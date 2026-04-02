from django import forms
from core.models import Empresa


class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['descricao', 'cnpj', 'ncad_cartoes', 'ncad_ifood', 'ncad_mp',
                  'ncad_outros', 'ncad_swfast', 'integrado']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'ncad_cartoes': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_ifood': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_mp': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_outros': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_swfast': forms.NumberInput(attrs={'class': 'form-control'}),
            'integrado': forms.Select(attrs={'class': 'form-control'}),
        }


class UploadArquivoForm(forms.Form):
    OPCOES = [
        ('swfast', 'SWFast - Vendas (CSV)'),
        ('swfast_abertura', 'SWFast - Aberturas/Fechamentos (CSV)'),
        ('stone', 'Stone (CSV)'),
        ('ifood', 'iFood (Excel)'),
    ]
    tipo_arquivo = forms.ChoiceField(choices=OPCOES, label="Qual sistema você quer importar?")
    arquivo = forms.FileField(label="Selecione a planilha")
