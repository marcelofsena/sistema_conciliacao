from django.db import models
from django.contrib.auth.models import User

# ==========================================
# CONTROLE DE ACESSO E SAAS
# ==========================================
class PerfilUsuario(models.Model):
    TIPO_ACESSO_CHOICES = [
        ('ADMIN', 'Administrador (Vê todas as lojas)'),
        ('OPERADOR', 'Operador (Vê apenas lojas permitidas)'),
    ]
    
    # Liga este perfil a um usuário oficial do Django
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo_acesso = models.CharField(max_length=20, choices=TIPO_ACESSO_CHOICES, default='OPERADOR')
    
    # Cria a relação: Um usuário pode ter várias lojas, e uma loja pode ter vários usuários
    lojas_permitidas = models.ManyToManyField('Empresa', blank=True, verbose_name="Lojas Permitidas para este Operador")

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_acesso_display()}"

class Empresa(models.Model):
    id_empresa = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=255, verbose_name="Descrição da Empresa")
    ncad_cartoes = models.IntegerField(default=0, verbose_name="Cad. Cartões")
    ncad_ifood = models.IntegerField(default=0, verbose_name="Cad. iFood")
    ncad_mp = models.IntegerField(default=0, verbose_name="Cad. Mercado Pago")
    ncad_outros = models.IntegerField(default=0, verbose_name="Cad. Outros")
    ncad_swfast = models.IntegerField(default=0, verbose_name="Cad. SWFast")
    
    OPCOES_INTEGRADO = [
        ('Sim', 'Sim'),
        ('Não', 'Não'),
    ]
    integrado = models.CharField(max_length=3, choices=OPCOES_INTEGRADO, default='Não')

    class Meta:
        # Isso força o Django a dar o nome exato da sua tabela antiga
        db_table = 'tbl_empresa' 

    def __str__(self):
        return self.descricao
    
class VendaSWFast(models.Model):
    venda = models.CharField(max_length=100, blank=True, null=True)
    forma_pagamento = models.CharField(max_length=100)
    aplicativo = models.CharField(max_length=100, blank=True, null=True)
    operador = models.CharField(max_length=100, blank=True, null=True)
    data_hora_transacao = models.DateTimeField(blank=True, null=True)
    id_pedido_externo = models.CharField(max_length=100, blank=True, null=True)
    codigo_loja = models.CharField(max_length=50, blank=True, null=True)
    chave_composta = models.CharField(max_length=255, unique=True)
    valor_pagamento = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    nr_abertura = models.CharField(max_length=50, blank=True, null=True)
    dthr_abert_cx = models.DateTimeField(null=True, blank=True)
    dthr_encerr_cx = models.DateTimeField(null=True, blank=True)
    conciliado = models.CharField(max_length=10, default='não')

class TransacaoStone(models.Model):
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

class PedidoIFood(models.Model):
    id_pedido = models.CharField(max_length=255, primary_key=True)
    nr_pedido = models.CharField(max_length=100, blank=True, null=True)
    data = models.DateTimeField(blank=True, null=True)
    restaurante = models.CharField(max_length=255, blank=True, null=True)
    id_restaurante = models.CharField(max_length=100, blank=True, null=True)
    valor_itens = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    total_pedido = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    vlr_pedido_sw = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    
    # NOVAS COLUNAS ADICIONADAS AQUI:
    formas_pagamento = models.CharField(max_length=255, blank=True, null=True)
    incentivo_ifood = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    origem_cancelamento = models.CharField(max_length=255, blank=True, null=True)
    status_pedido = models.CharField(max_length=100, null=True, blank=True, default='CONCLUIDO')
    conciliado = models.CharField(max_length=10, default='não')

    def __str__(self):
        return f"iFood: {self.nr_pedido} - R$ {self.total_pedido}"

# ==========================================
# NOVAS TABELAS DE CONFIGURAÇÃO E CAIXA
# ==========================================

class FormaPagamento(models.Model):
    forma_pagamento = models.CharField(max_length=100, verbose_name="Forma de Pagamento")
    especific_form_pgto = models.CharField(max_length=100, blank=True, null=True, verbose_name="Especificação (Resumo)")
    
    # NOVOS CAMPOS AQUI
    codigo_loja = models.CharField(max_length=50, blank=True, null=True, verbose_name="Código da Loja")
    aplicativo = models.CharField(max_length=100, blank=True, null=True, verbose_name="Aplicativo")

    class Meta:
        db_table = 'tbl_formapagamento'
        # Garante que a combinação exata não se repita
        unique_together = (('forma_pagamento', 'codigo_loja', 'aplicativo'),)
        verbose_name = 'Forma de Pagamento'
        verbose_name_plural = 'Formas de Pagamento'

    def __str__(self):
        return f"{self.forma_pagamento} ({self.aplicativo}) - Loja {self.codigo_loja}"


class Sangria(models.Model):
    codigo_loja = models.CharField(max_length=50)
    nr_abertura = models.CharField(max_length=50)
    vlrsanguia = models.DecimalField(max_digits=15, decimal_places=2, default=0.0, verbose_name="Valor da Sangria")
    sangriadescricao = models.TextField(verbose_name="Descrição da Sangria")

    class Meta:
        db_table = 'tbl_sangria'
        verbose_name = 'Sangria'
        verbose_name_plural = 'Sangrias'

    def __str__(self):
        return f"Loja: {self.codigo_loja} | Abertura: {self.nr_abertura} - R$ {self.vlrsanguia}"


class MovimentoCaixa(models.Model):
    codigo_loja = models.CharField(max_length=50)
    nr_abertura = models.CharField(max_length=50)
    suprim_inicial_cx = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    total_trocos_recebidos = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    sld_caixa_prox_turno = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    valor_dinheiro_envelope = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    pagto_tx_entr_pix_escrit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    dif_cont_sld_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    dif_resumo = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    tot_vend_resumo = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)

    class Meta:
        db_table = 'tbl_movcaixa'
        # Define que a combinação de Loja e Abertura não pode se repetir (sua chave primária composta)
        unique_together = (('codigo_loja', 'nr_abertura'),) 
        verbose_name = 'Movimento de Caixa'
        verbose_name_plural = 'Movimentos de Caixa'

    def __str__(self):
        return f"Movimento - Loja: {self.codigo_loja} | Abertura: {self.nr_abertura}"