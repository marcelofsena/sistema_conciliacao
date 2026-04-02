"""
Financeiro - Gestão de Contas a Receber e Contas a Pagar.

Conforme regra de negócio (seção 3.2):

Contas a Receber (Fase 1):
- "Alimentado 100% de forma automática pelos eventos de Vendas e Conciliação"
- "Terá opção de inclusão manual com tipificação
  (ex: parcelamento de vales/empréstimos a funcionários)"

Contas a Pagar (Fase 2):
- "Gestão de obrigações com opção de importar dados externos
  (ex: lotes de folhas de pagamento)"

Conciliação Bancária (Fase 2):
- "Cruzamento de extratos de múltiplos bancos com as baixas
  do Contas a Pagar/Receber"
- "Extratos bancários importados de planilhas ou arquivos CSV"
"""

from django.db import models
from django.contrib.auth.models import User
from core.models import AuditoriaMixin, Empresa


# ==========================================
# CONTAS A RECEBER (FASE 1)
# ==========================================

class ContaReceber(AuditoriaMixin):
    """
    Título a receber, alimentado automaticamente pelos eventos de vendas
    e conciliação de caixa, com opção de inclusão manual.
    """
    ORIGEM_CHOICES = [
        ('VENDA', 'Venda (Automático)'),
        ('CONCILIACAO', 'Conciliação de Caixa (Automático)'),
        ('MANUAL', 'Inclusão Manual'),
    ]

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('PARCIAL', 'Parcialmente Recebido'),
        ('RECEBIDO', 'Recebido'),
        ('CANCELADO', 'Cancelado'),
    ]

    TIPO_MANUAL_CHOICES = [
        ('VALE', 'Parcelamento de Vale'),
        ('EMPRESTIMO', 'Empréstimo a Funcionário'),
        ('OUTROS', 'Outros'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="contas_receber"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    valor_original = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valor Original"
    )
    valor_recebido = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.0, verbose_name="Valor Recebido"
    )
    saldo = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Saldo"
    )
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_recebimento = models.DateField(
        null=True, blank=True, verbose_name="Data de Recebimento"
    )
    origem = models.CharField(
        max_length=20, choices=ORIGEM_CHOICES, default='VENDA'
    )
    tipo_manual = models.CharField(
        max_length=20, choices=TIPO_MANUAL_CHOICES, blank=True,
        verbose_name="Tipo (para inclusões manuais)"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='ABERTO'
    )
    referencia_evento = models.CharField(
        max_length=255, blank=True,
        verbose_name="Referência do Evento",
        help_text="ID do evento que gerou este título"
    )
    forma_pagamento = models.CharField(
        max_length=100, blank=True, verbose_name="Forma de Pagamento"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['status', 'data_vencimento']),
            models.Index(fields=['loja', 'status']),
        ]

    def __str__(self):
        return f"CR: {self.descricao} - R$ {self.saldo} ({self.status})"

    def save(self, *args, **kwargs):
        self.saldo = self.valor_original - self.valor_recebido
        if self.saldo <= 0:
            self.status = 'RECEBIDO'
        elif self.valor_recebido > 0:
            self.status = 'PARCIAL'
        super().save(*args, **kwargs)


# ==========================================
# CONTAS A PAGAR (FASE 2)
# ==========================================

class ContaPagar(AuditoriaMixin):
    """
    Título a pagar. Gestão de obrigações com opção
    de importar dados externos (folha de pagamento, etc).
    """
    ORIGEM_CHOICES = [
        ('COMPRA', 'Compra/Fornecedor'),
        ('FOLHA', 'Folha de Pagamento (Importada)'),
        ('IMPOSTO', 'Imposto/Taxa'),
        ('MANUAL', 'Inclusão Manual'),
    ]

    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('PARCIAL', 'Parcialmente Pago'),
        ('PAGO', 'Pago'),
        ('CANCELADO', 'Cancelado'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="contas_pagar"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    fornecedor = models.CharField(max_length=255, blank=True, verbose_name="Fornecedor")
    valor_original = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valor Original"
    )
    valor_pago = models.DecimalField(
        max_digits=15, decimal_places=2, default=0.0, verbose_name="Valor Pago"
    )
    saldo = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Saldo"
    )
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(
        null=True, blank=True, verbose_name="Data de Pagamento"
    )
    origem = models.CharField(
        max_length=20, choices=ORIGEM_CHOICES, default='MANUAL'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='ABERTO'
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['-data_vencimento']
        indexes = [
            models.Index(fields=['status', 'data_vencimento']),
            models.Index(fields=['loja', 'status']),
        ]

    def __str__(self):
        return f"CP: {self.descricao} - R$ {self.saldo} ({self.status})"

    def save(self, *args, **kwargs):
        self.saldo = self.valor_original - self.valor_pago
        if self.saldo <= 0:
            self.status = 'PAGO'
        elif self.valor_pago > 0:
            self.status = 'PARCIAL'
        super().save(*args, **kwargs)


# ==========================================
# CONCILIAÇÃO BANCÁRIA (FASE 2)
# ==========================================

class ExtratoBancario(AuditoriaMixin):
    """
    Registro de extrato bancário importado (CSV/planilha).
    Usado para conciliação bancária com Contas a Pagar/Receber.
    """
    TIPO_CHOICES = [
        ('C', 'Crédito (Entrada)'),
        ('D', 'Débito (Saída)'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="extratos"
    )
    banco = models.CharField(max_length=100, verbose_name="Banco")
    agencia = models.CharField(max_length=20, blank=True, verbose_name="Agência")
    conta = models.CharField(max_length=30, blank=True, verbose_name="Conta")
    data_movimento = models.DateField(verbose_name="Data do Movimento")
    descricao = models.CharField(max_length=500, verbose_name="Descrição/Histórico")
    valor = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="Valor")
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, verbose_name="Tipo")
    conciliado = models.BooleanField(default=False, verbose_name="Conciliado")
    conta_receber = models.ForeignKey(
        ContaReceber, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Conta a Receber Vinculada"
    )
    conta_pagar = models.ForeignKey(
        ContaPagar, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Conta a Pagar Vinculada"
    )

    class Meta:
        verbose_name = 'Extrato Bancário'
        verbose_name_plural = 'Extratos Bancários'
        ordering = ['-data_movimento']

    def __str__(self):
        return f"{self.banco} - {self.data_movimento} - {self.tipo} R$ {self.valor}"
