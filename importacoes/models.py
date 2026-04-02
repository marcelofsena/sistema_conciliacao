"""
Importações - Camada de padronização e importação de dados externos.

Conforme regra de negócio (seção 3.3):
- Importação iFood, Bancos e Cartões via planilhas/CSV
- Normalizador de Dados: camada intermediária que padroniza nomenclaturas
  (Ex: "MASTERCARD DÉBITO" do iFood e "MAESTRO" da maquininha
  viram uma nomenclatura única interna)

Modelos:
- VendaSWFast: Transações do PDV (SWFast)
- TransacaoStone: Transações de cartão (Stone)
- PedidoIFood: Pedidos do iFood
- FormaPagamento: Normalizador/De-Para de formas de pagamento (específica por loja)
"""

from django.db import models
from core.models import Empresa


# ==========================================
# DADOS IMPORTADOS DO PDV (SWFAST)
# ==========================================

class VendaSWFast(models.Model):
    """Transação de venda importada do sistema PDV SWFast."""
    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True,
        related_name='vendas_swfast',
        verbose_name='Loja',
        help_text='Referência para a Empresa. Será preenchido gradualmente a partir do codigo_loja'
    )
    venda = models.CharField(max_length=100, blank=True, null=True)
    forma_pagamento = models.CharField(max_length=100)
    aplicativo = models.CharField(max_length=100, blank=True, null=True)
    operador = models.CharField(max_length=100, blank=True, null=True)
    data_hora_transacao = models.DateTimeField(blank=True, null=True)
    id_pedido_externo = models.CharField(max_length=100, blank=True, null=True)
    codigo_loja = models.CharField(max_length=50, blank=True, null=True, help_text='Código SWFast da loja (para auditoria)')
    chave_composta = models.CharField(max_length=255, unique=True)
    valor_pagamento = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    nr_abertura = models.CharField(max_length=50, blank=True, null=True)
    dthr_abert_cx = models.DateTimeField(null=True, blank=True)
    dthr_encerr_cx = models.DateTimeField(null=True, blank=True)
    conciliado = models.CharField(max_length=10, default='não')

    class Meta:
        verbose_name = 'Venda SWFast'
        verbose_name_plural = 'Vendas SWFast'

    def __str__(self):
        return f"Venda {self.venda} - {self.forma_pagamento} - R$ {self.valor_pagamento}"

    def get_loja(self):
        """
        Retorna a Empresa associada. Se loja_id está preenchido, usa direto.
        Caso contrário, tenta buscar por codigo_loja → ncad_swfast.
        Método temporário durante migração (será removido depois).
        """
        if self.loja:
            return self.loja
        if self.codigo_loja:
            return Empresa.objects.filter(ncad_swfast=self.codigo_loja).first()
        return None


# ==========================================
# DADOS IMPORTADOS DE CARTÕES (STONE)
# ==========================================

class TransacaoStone(models.Model):
    """Transação de cartão importada da adquirente Stone."""
    stonecode = models.CharField(max_length=100, blank=True, null=True)
    data_venda = models.DateTimeField(blank=True, null=True)
    bandeira = models.CharField(max_length=50, blank=True, null=True)
    produto = models.CharField(max_length=100, blank=True, null=True)
    stone_id = models.CharField(max_length=100, blank=True, null=True)
    qtd_parcelas = models.IntegerField(default=1)
    valor_bruto = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    valor_liquido = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    desconto_mdr = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    desconto_antecipacao = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    documento = models.BigIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Transação Stone'
        verbose_name_plural = 'Transações Stone'

    def __str__(self):
        return f"Stone {self.stone_id} - {self.bandeira} - R$ {self.valor_bruto}"


# ==========================================
# DADOS IMPORTADOS DO IFOOD
# ==========================================

class PedidoIFood(models.Model):
    """Pedido importado do iFood (portal do restaurante)."""
    id_pedido = models.CharField(max_length=255, primary_key=True)
    nr_pedido = models.CharField(max_length=100, blank=True, null=True)
    data = models.DateTimeField(blank=True, null=True)
    restaurante = models.CharField(max_length=255, blank=True, null=True)
    id_restaurante = models.CharField(max_length=100, blank=True, null=True)
    valor_itens = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    total_pedido = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    vlr_pedido_sw = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    formas_pagamento = models.CharField(max_length=255, blank=True, null=True)
    incentivo_ifood = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    origem_cancelamento = models.CharField(max_length=255, blank=True, null=True)
    status_pedido = models.CharField(max_length=100, null=True, blank=True, default='CONCLUIDO')
    conciliado = models.CharField(max_length=10, default='não')

    class Meta:
        verbose_name = 'Pedido iFood'
        verbose_name_plural = 'Pedidos iFood'

    def __str__(self):
        return f"iFood: {self.nr_pedido} - R$ {self.total_pedido}"


# ==========================================
# NORMALIZADOR DE FORMAS DE PAGAMENTO
# ==========================================

class FormaPagamento(models.Model):
    """
    Normalizador/De-Para de formas de pagamento.

    Conforme regra de negócio (seção 3.3 - Normalizador de Dados):
    "Camada intermediária que padroniza os nomes
    (Ex: 'MASTERCARD DÉBITO' do iFood e 'MAESTRO' da maquininha
    viram uma nomenclatura única interna)."

    especific_form_pgto é a nomenclatura interna unificada
    (ex: CARTAO, DINHEIRO, IFOOD ONLINE, PIX).

    Cada forma de pagamento é específica por loja, evitando duplicação
    quando um usuário é adicionado a múltiplas lojas.
    """
    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="formas_pagamento",
        null=True, blank=True  # Nullable durante transição
    )
    forma_pagamento = models.CharField(max_length=100, verbose_name="Forma de Pagamento (Original)")
    especific_form_pgto = models.CharField(
        max_length=100, blank=True, null=True,
        verbose_name="Especificação Interna (Resumo)"
    )
    aplicativo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Aplicativo/Origem")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        db_table = 'tbl_formapagamento'
        unique_together = (('loja', 'forma_pagamento', 'aplicativo'),)
        verbose_name = 'Forma de Pagamento'
        verbose_name_plural = 'Formas de Pagamento'
        ordering = ['loja', 'aplicativo', 'forma_pagamento']

    def __str__(self):
        return f"{self.forma_pagamento} ({self.aplicativo}) - {self.loja.descricao}"
