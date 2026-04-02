"""
Caixa - Conferência e Conciliação de Caixa.

Conforme regra de negócio (seção 3.4):
- Módulo para os caixas fecharem seus turnos e a retaguarda auditar
- Suporte a restaurantes 24h (múltiplos turnos)
- Tela de Conciliação por Turno: painel comparativo PDV vs plataformas
- Drill-down de Diferenças: links clicáveis nas divergências
- Contas de Valores em Trânsito para diferenças entre turnos
- Botão de contabilização de valores em trânsito para ajuste do saldo
"""

from django.db import models
from core.models import AuditoriaMixin, Empresa


# ==========================================
# SANGRIA (RETIRADA DE DINHEIRO DO CAIXA)
# ==========================================

class Sangria(models.Model):
    """Registro de sangria (retirada) de dinheiro do caixa."""
    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True,
        related_name='sangrias',
        verbose_name='Loja',
        help_text='Referência para a Empresa. Será preenchido gradualmente a partir do codigo_loja'
    )
    codigo_loja = models.CharField(max_length=50, help_text='Código SWFast da loja (para auditoria)')
    nr_abertura = models.CharField(max_length=50)
    vlrsanguia = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.0,
        verbose_name="Valor da Sangria"
    )
    sangriadescricao = models.TextField(verbose_name="Descrição da Sangria")

    class Meta:
        db_table = 'tbl_sangria'
        verbose_name = 'Sangria'
        verbose_name_plural = 'Sangrias'

    def __str__(self):
        return f"Loja: {self.codigo_loja} | Abertura: {self.nr_abertura} - R$ {self.vlrsanguia}"

    def get_loja(self):
        """Método temporário durante migração."""
        if self.loja:
            return self.loja
        if self.codigo_loja:
            return Empresa.objects.filter(ncad_swfast=self.codigo_loja).first()
        return None


# ==========================================
# MOVIMENTO DE CAIXA (ABERTURA/FECHAMENTO)
# ==========================================

class MovimentoCaixa(models.Model):
    """
    Registro de movimento diário do caixa.
    Contém suprimento inicial, trocos, envelope de dinheiro e diferenças.
    """
    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True,
        related_name='movimentos_caixa',
        verbose_name='Loja',
        help_text='Referência para a Empresa. Será preenchido gradualmente a partir do codigo_loja'
    )
    codigo_loja = models.CharField(max_length=50, help_text='Código SWFast da loja (para auditoria)')
    nr_abertura = models.CharField(max_length=50)
    suprim_inicial_cx = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                            verbose_name="Suprimento Inicial")
    total_trocos_recebidos = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                                  verbose_name="Total Trocos Recebidos")
    sld_caixa_prox_turno = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                                verbose_name="Saldo p/ Próximo Turno")
    valor_dinheiro_envelope = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                                   verbose_name="Valor Dinheiro Envelope")
    pagto_tx_entr_pix_escrit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                                    verbose_name="Pgto Taxa/Entrega/PIX/Escritório")
    dif_cont_sld_inicial = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                                verbose_name="Dif. Contagem Saldo Inicial")
    dif_resumo = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                      verbose_name="Diferença Resumo")
    tot_vend_resumo = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                           verbose_name="Total Vendas Resumo")

    class Meta:
        db_table = 'tbl_movcaixa'
        unique_together = (('codigo_loja', 'nr_abertura'),)
        verbose_name = 'Movimento de Caixa'
        verbose_name_plural = 'Movimentos de Caixa'

    def __str__(self):
        return f"Movimento - Loja: {self.codigo_loja} | Abertura: {self.nr_abertura}"

    def get_loja(self):
        """Método temporário durante migração."""
        if self.loja:
            return self.loja
        if self.codigo_loja:
            return Empresa.objects.filter(ncad_swfast=self.codigo_loja).first()
        return None


# ==========================================
# CONCILIAÇÃO DE CAIXA (RESULTADO)
# ==========================================

class ConciliacaoCaixa(AuditoriaMixin):
    """
    Resultado da conciliação de um turno de caixa.
    Registra o status e diferenças encontradas após conferência.

    Conforme regra:
    - "O sistema não permitirá 'forçar' o fechamento de caixa"
    - "Diferenças temporais tratadas via Contas de Valores em Trânsito"
    - "Nas telas de conciliação deve haver um botão que faça
      contabilização de valores em trânsito para ajuste do saldo"
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Conferência'),
        ('CONFERIDO', 'Conferido - Sem Divergência'),
        ('DIVERGENTE', 'Conferido - Com Divergência'),
        ('AJUSTADO', 'Ajustado via Valores em Trânsito'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE, null=True, blank=True,
        related_name='conciliacoes_caixa',
        verbose_name='Loja',
        help_text='Referência para a Empresa. Será preenchido gradualmente a partir do codigo_loja'
    )
    codigo_loja = models.CharField(max_length=50, verbose_name="Código da Loja", help_text='Código SWFast da loja (para auditoria)')
    nr_abertura = models.CharField(max_length=50, verbose_name="Nº Abertura")
    data_conciliacao = models.DateField(verbose_name="Data da Conciliação")
    turno = models.CharField(max_length=10, verbose_name="Turno (Dia/Noite)")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDENTE'
    )
    total_pdv = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                     verbose_name="Total PDV (SWFast)")
    total_importados = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                            verbose_name="Total Importados (Stone/iFood)")
    diferenca_total = models.DecimalField(max_digits=15, decimal_places=2, default=0.0,
                                           verbose_name="Diferença Total")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    contabilizado = models.BooleanField(
        default=False, verbose_name="Contabilizado",
        help_text="Se os valores em trânsito foram contabilizados"
    )

    class Meta:
        verbose_name = 'Conciliação de Caixa'
        verbose_name_plural = 'Conciliações de Caixa'
        unique_together = (('codigo_loja', 'nr_abertura'),)
        ordering = ['-data_conciliacao']

    def __str__(self):
        return f"Conciliação Loja {self.codigo_loja} - Cx {self.nr_abertura} ({self.status})"

    def get_loja(self):
        """Método temporário durante migração."""
        if self.loja:
            return self.loja
        if self.codigo_loja:
            return Empresa.objects.filter(ncad_swfast=self.codigo_loja).first()
        return None
