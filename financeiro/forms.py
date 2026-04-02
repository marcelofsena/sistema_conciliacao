from django import forms
from .models import ContaReceber, ContaPagar
from core.models import Empresa

import datetime


class FormControlMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'form-control {existing}'.strip()


# ==========================================
# CONTAS A RECEBER
# ==========================================

class ContaReceberForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = ContaReceber
        fields = [
            'loja', 'descricao', 'tipo_manual', 'valor_original',
            'data_emissao', 'data_vencimento', 'forma_pagamento', 'observacoes',
        ]
        widgets = {
            'descricao':       forms.TextInput(attrs={'placeholder': 'Ex: Vale funcionário João - Parcela 1/3'}),
            'valor_original':  forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0,00'}),
            'data_emissao':    forms.DateInput(attrs={'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'forma_pagamento': forms.TextInput(attrs={'placeholder': 'Ex: Desconto em folha, Dinheiro…'}),
            'observacoes':     forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observações adicionais…'}),
        }
        labels = {
            'loja':           'Loja',
            'descricao':      'Descrição',
            'tipo_manual':    'Tipo',
            'valor_original': 'Valor (R$)',
            'data_emissao':   'Data de Emissão',
            'data_vencimento':'Data de Vencimento',
            'forma_pagamento':'Forma de Pagamento',
            'observacoes':    'Observações',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loja:
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()
        # Inclusão manual sempre fixa a origem
        self.fields['tipo_manual'].required = True
        # Data de emissão padrão hoje
        if not self.instance.pk:
            self.fields['data_emissao'].initial = datetime.date.today()


class RegistrarRecebimentoForm(FormControlMixin, forms.Form):
    valor_recebido = forms.DecimalField(
        label='Valor a Receber (R$)',
        max_digits=15, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0,00'}),
    )
    data_recebimento = forms.DateField(
        label='Data do Recebimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    observacoes = forms.CharField(
        label='Observações', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Opcional…'}),
    )

    def __init__(self, *args, saldo_restante=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.saldo_restante = saldo_restante
        if not self.data.get('data_recebimento'):
            self.fields['data_recebimento'].initial = datetime.date.today()

    def clean_valor_recebido(self):
        v = self.cleaned_data['valor_recebido']
        if self.saldo_restante is not None and v > self.saldo_restante:
            raise forms.ValidationError(
                f'Valor informado (R$ {v:.2f}) excede o saldo em aberto (R$ {self.saldo_restante:.2f}).'
            )
        return v


# ==========================================
# CONTAS A PAGAR
# ==========================================

class ContaPagarForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = ContaPagar
        fields = [
            'loja', 'descricao', 'fornecedor', 'origem', 'valor_original',
            'data_emissao', 'data_vencimento', 'observacoes',
        ]
        widgets = {
            'descricao':       forms.TextInput(attrs={'placeholder': 'Ex: Aluguel março/2025'}),
            'fornecedor':      forms.TextInput(attrs={'placeholder': 'Nome do fornecedor ou credor'}),
            'valor_original':  forms.NumberInput(attrs={'step': '0.01', 'min': '0.01', 'placeholder': '0,00'}),
            'data_emissao':    forms.DateInput(attrs={'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'type': 'date'}),
            'observacoes':     forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observações adicionais…'}),
        }
        labels = {
            'loja':           'Loja',
            'descricao':      'Descrição',
            'fornecedor':     'Fornecedor / Credor',
            'origem':         'Origem',
            'valor_original': 'Valor (R$)',
            'data_emissao':   'Data de Emissão',
            'data_vencimento':'Data de Vencimento',
            'observacoes':    'Observações',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loja:
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()
        if not self.instance.pk:
            self.fields['data_emissao'].initial = datetime.date.today()


class RegistrarPagamentoForm(FormControlMixin, forms.Form):
    valor_pago = forms.DecimalField(
        label='Valor a Pagar (R$)',
        max_digits=15, decimal_places=2, min_value=0.01,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': '0,00'}),
    )
    data_pagamento = forms.DateField(
        label='Data do Pagamento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    observacoes = forms.CharField(
        label='Observações', required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Opcional…'}),
    )

    def __init__(self, *args, saldo_restante=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.saldo_restante = saldo_restante
        if not self.data.get('data_pagamento'):
            self.fields['data_pagamento'].initial = datetime.date.today()

    def clean_valor_pago(self):
        v = self.cleaned_data['valor_pago']
        if self.saldo_restante is not None and v > self.saldo_restante:
            raise forms.ValidationError(
                f'Valor informado (R$ {v:.2f}) excede o saldo em aberto (R$ {self.saldo_restante:.2f}).'
            )
        return v
