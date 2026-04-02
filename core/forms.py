from django import forms
from .models import Empresa


class FormControlMixin:
    """Aplica a classe form-control do design system em todos os campos."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'form-control {existing}'.strip()


class EmpresaForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Empresa
        fields = [
            'descricao', 'cnpj', 'ativa',
            'ncad_swfast', 'ncad_cartoes', 'ncad_ifood',
            'ncad_mp', 'ncad_outros', 'integrado',
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'placeholder': 'Nome da empresa / loja'}),
            'cnpj':      forms.TextInput(attrs={'placeholder': '00.000.000/0000-00'}),
        }
        labels = {
            'descricao':    'Nome da Empresa / Loja',
            'cnpj':         'CNPJ',
            'ativa':        'Loja ativa',
            'ncad_swfast':  'Código SWFast (PDV)',
            'ncad_cartoes': 'Código Stone (Cartões)',
            'ncad_ifood':   'Código iFood',
            'ncad_mp':      'Código Mercado Pago',
            'ncad_outros':  'Código Outros',
            'integrado':    'Integrada com PDV',
        }
