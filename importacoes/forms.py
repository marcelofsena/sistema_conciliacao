from django import forms
from .models import Empresa


# Novo formulário para cadastrar a Empresa
class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        # Agora listamos todos os campos novos
        fields = ['descricao', 'ncad_cartoes', 'ncad_ifood', 'ncad_mp', 'ncad_outros', 'ncad_swfast', 'integrado'] 
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control'}),
            'ncad_cartoes': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_ifood': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_mp': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_outros': forms.NumberInput(attrs={'class': 'form-control'}),
            'ncad_swfast': forms.NumberInput(attrs={'class': 'form-control'}),
            'integrado': forms.Select(attrs={'class': 'form-control'}),
        }

class UploadArquivoForm(forms.Form):
    # As opções que vão aparecer na tela
    OPCOES = [
        ('swfast', 'SWFast - Vendas (CSV)'),
        ('swfast_abertura', 'SWFast - Aberturas/Fechamentos (CSV)'), # <--- NOVA OPÇÃO AQUI
        ('stone', 'Stone (CSV)'),
        ('ifood', 'iFood (Excel)'),
    ]
    tipo_arquivo = forms.ChoiceField(choices=OPCOES, label="Qual sistema você quer importar?")
    arquivo = forms.FileField(label="Selecione a planilha")