from django import forms
from django.forms import inlineformset_factory
from django.utils.html import format_html
from .models import (
    ContaSintetica, ContaAnalitica, TipoEvento, RegraContabil, PartidaRegra,
    PeriodoContabil, LancamentoContabil
)
from core.models import Empresa


class ContaPaiSelect(forms.Select):
    """
    Widget customizado para exibir contas com indentação hierárquica.
    Mostra: "  1.1 - ATIVO CIRCULANTE" com espaços de indentação.
    """
    def __init__(self, attrs=None, choices=(), loja=None):
        super().__init__(attrs, choices)
        self.loja = loja

    def optgroups(self, name, value, attrs=None):
        """Renderiza as opções com indentação visual."""
        from .models import ContaSintetica

        groups = []
        has_selected = False

        # Opção "Nenhuma (raiz)"
        selected = (value is None or value == '')
        groups.append(
            (None, [
                self.create_option(name, '', '— Nenhuma (raiz) —', selected, 0)
            ], 0)
        )

        if self.loja:
            # Buscar todas as contas da loja
            contas = ContaSintetica.objects.filter(
                loja=self.loja
            ).order_by('codigo_classificacao').select_related('conta_pai')

            # Calcular profundidade para cada conta
            profundidades = {}
            def calc_prof(conta):
                if conta.pk in profundidades:
                    return profundidades[conta.pk]
                if conta.conta_pai is None:
                    prof = 0
                else:
                    prof = 1 + calc_prof(conta.conta_pai)
                profundidades[conta.pk] = prof
                return prof

            for conta in contas:
                prof = calc_prof(conta)
                indent = '&nbsp;&nbsp;' * prof  # 2 espaços por nível
                label = format_html(
                    '{}&bull; {}',
                    format_html(indent),
                    f"{conta.codigo_classificacao} - {conta.nome}"
                )
                selected = str(conta.pk) == str(value)
                groups.append(
                    (None, [
                        self.create_option(name, conta.pk, label, selected, 0)
                    ], 0)
                )

        return groups


class FormControlMixin:
    """Aplica a classe form-control do design system em todos os campos."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'form-control {existing}'.strip()


class ContaSinteticaForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = ContaSintetica
        fields = ['loja', 'codigo_classificacao', 'nome', 'tipo_conta', 'conta_pai', 'nivel']
        widgets = {
            'codigo_classificacao': forms.TextInput(attrs={'placeholder': 'Ex: 1, 1.1, 1.1.1'}),
            'nome':  forms.TextInput(attrs={'placeholder': 'Ex: ATIVO CIRCULANTE'}),
            'nivel': forms.NumberInput(attrs={'min': 1, 'max': 6}),
            'conta_pai': ContaPaiSelect(),  # Widget customizado com indentação
        }
        labels = {
            'loja':                 'Loja',
            'codigo_classificacao': 'Código de Classificação',
            'nome':                 'Nome da Conta',
            'tipo_conta':           'Tipo',
            'conta_pai':            'Conta Pai (hierarquia)',
            'nivel':                'Nível Hierárquico',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loja = loja
        if loja:
            self.fields['conta_pai'].queryset = ContaSintetica.objects.filter(
                loja=loja
            ).order_by('codigo_classificacao')
            # Usar widget customizado com loja
            self.fields['conta_pai'].widget = ContaPaiSelect(loja=loja)
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()
        self.fields['conta_pai'].required = False

    def clean_nivel(self):
        """Valida que nível máximo para sintéticas é 4."""
        nivel = self.cleaned_data.get('nivel')
        if nivel and nivel > 4:
            raise forms.ValidationError(
                'Contas sintéticas podem ter no máximo nível 4. '
                'Para nível 5, crie uma conta analítica.'
            )
        return nivel

    def clean_codigo_classificacao(self):
        codigo = self.cleaned_data.get('codigo_classificacao', '').strip()
        loja = self.loja or self.cleaned_data.get('loja')
        nivel = self.cleaned_data.get('nivel')

        if not codigo:
            raise forms.ValidationError('Código é obrigatório.')

        # Validar formato do código baseado no nível
        if nivel:
            partes = codigo.split('.')

            # Se nível 4, o último segmento deve ter 2 dígitos (zero-padded)
            if nivel == 4:
                if len(partes) < 4:
                    raise forms.ValidationError(
                        'Código de nível 4 deve ter 4 segmentos. Ex: 1.1.1.02'
                    )
                ultimo = partes[-1]
                if not ultimo.isdigit() or len(ultimo) != 2:
                    raise forms.ValidationError(
                        'Último segmento do nível 4 deve ter exatamente 2 dígitos zero-padded. Ex: .01, .02, ..., .99'
                    )
            # Níveis 1-3 não devem ter zeros à esquerda
            elif nivel < 4:
                for i, parte in enumerate(partes[:nivel]):
                    if parte.isdigit() and parte.startswith('0') and len(parte) > 1:
                        raise forms.ValidationError(
                            f'Segmentos dos níveis 1-3 não devem ter zeros à esquerda. '
                            f'Segmento {i+1} inválido: "{parte}"'
                        )

        # Validar se código já existe nesta loja (exceto se estamos editando)
        queryset = ContaSintetica.objects.filter(
            loja=loja,
            codigo_classificacao=codigo
        )

        # Se é edição, excluir o próprio objeto
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                f'Este código "{codigo}" já existe nesta loja. '
                'Use um código diferente ou edite a conta existente.'
            )

        return codigo


class ContaAnaliticaForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = ContaAnalitica
        fields = [
            'loja', 'codigo_reduzido', 'codigo_classificacao', 'nome',
            'conta_sintetica', 'natureza_saldo', 'aceita_lancamento',
            'data_bloqueio', 'centro_custo',
        ]
        widgets = {
            'codigo_classificacao': forms.TextInput(attrs={'placeholder': 'Ex: 1110001'}),
            'nome':  forms.TextInput(attrs={'placeholder': 'Ex: Caixa Central'}),
            'data_bloqueio': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'loja':                 'Loja',
            'codigo_reduzido':      'Código Reduzido',
            'codigo_classificacao': 'Código de Classificação',
            'nome':                 'Nome da Conta',
            'conta_sintetica':      'Conta Sintética (Grupo)',
            'natureza_saldo':       'Natureza do Saldo',
            'aceita_lancamento':    'Aceita Lançamentos',
            'data_bloqueio':        'Data de Bloqueio',
            'centro_custo':         'Exige Centro de Custo',
        }

    def __init__(self, *args, loja=None, sintetica=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.loja = loja
        self.sintetica = sintetica
        if loja:
            self.fields['conta_sintetica'].queryset = ContaSintetica.objects.filter(
                loja=loja
            ).order_by('codigo_classificacao')
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()
        if sintetica:
            self.fields['conta_sintetica'].initial = sintetica
        self.fields['data_bloqueio'].required = False

        # Código reduzido é auto-calculado a partir do código de classificação
        # Mostrar apenas para referência, não editável
        if self.instance and self.instance.pk:
            # Em edição, mostrar o código reduzido atual (readonly)
            self.fields['codigo_reduzido'].widget.attrs['readonly'] = True
            self.fields['codigo_reduzido'].help_text = 'Extraído automaticamente dos últimos 4 dígitos do código de classificação'
            self.fields['codigo_reduzido'].required = True
        else:
            # Em criação, ocultar (será calculado) e não obrigatório
            self.fields['codigo_reduzido'].widget = forms.HiddenInput()
            self.fields['codigo_reduzido'].required = False

    def clean(self):
        """Valida que conta analítica só pode ser criada a partir de sintética nível 4."""
        cleaned_data = super().clean()
        conta_sintetica = cleaned_data.get('conta_sintetica')

        if conta_sintetica and conta_sintetica.nivel != 4:
            raise forms.ValidationError(
                'Contas analíticas só podem ser criadas a partir de contas sintéticas nível 4. '
                f'A conta selecionada é nível {conta_sintetica.nivel}.'
            )

        return cleaned_data

    def clean_codigo_classificacao(self):
        """Valida formato do código analítico e unicidade."""
        codigo = self.cleaned_data.get('codigo_classificacao', '').strip()
        conta_sintetica = self.cleaned_data.get('conta_sintetica')
        loja = self.loja or self.cleaned_data.get('loja')

        if not codigo:
            raise forms.ValidationError('Código é obrigatório.')

        # Validar formato: deve ter 4 dígitos zero-padded no último segmento
        partes = codigo.split('.')
        if len(partes) < 5:
            raise forms.ValidationError(
                'Código analítico deve ter 5 segmentos. Ex: 1.1.1.02.0001'
            )

        ultimo = partes[-1]
        if not ultimo.isdigit() or len(ultimo) != 4:
            raise forms.ValidationError(
                'Último segmento da analítica deve ter exatamente 4 dígitos zero-padded. Ex: .0001, .0002, ..., .9999'
            )

        # Validar que começa com código da sintética pai
        if conta_sintetica:
            if not codigo.startswith(conta_sintetica.codigo_classificacao + '.'):
                raise forms.ValidationError(
                    f'Código analítico deve começar com o código da sintética pai: {conta_sintetica.codigo_classificacao}.XXXX'
                )

        # Validar se código já existe nesta loja (exceto se estamos editando)
        queryset = ContaAnalitica.objects.filter(
            loja=loja,
            codigo_classificacao=codigo
        )

        # Se é edição, excluir o próprio objeto
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                f'Este código "{codigo}" já existe nesta loja. '
                'Use um código diferente ou edite a conta existente.'
            )

        # NOTA: Validação de código_reduzido é feita na view APÓS salvar
        # Aqui apenas validamos o formato do código de classificação
        # A unicidade do código_reduzido será validada quando o objeto for criado

        return codigo


class TipoEventoForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = TipoEvento
        fields = ['codigo', 'descricao', 'modulo_origem', 'ativo']
        widgets = {
            'codigo':        forms.TextInput(attrs={'placeholder': 'Ex: VENDA_REALIZADA', 'style': 'text-transform:uppercase'}),
            'descricao':     forms.TextInput(attrs={'placeholder': 'Descrição legível do evento'}),
            'modulo_origem': forms.TextInput(attrs={'placeholder': 'Ex: CAIXA, ESTOQUE, FINANCEIRO'}),
        }
        labels = {
            'codigo':        'Código do Evento',
            'descricao':     'Descrição',
            'modulo_origem': 'Módulo de Origem',
            'ativo':         'Evento Ativo',
        }


class RegraContabilForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = RegraContabil
        fields = ['loja', 'tipo_evento', 'descricao', 'ativa']
        widgets = {
            'descricao': forms.TextInput(attrs={'placeholder': 'Ex: Receita de Vendas — Caixa'}),
        }
        labels = {
            'loja':          'Loja',
            'tipo_evento':   'Tipo de Evento',
            'descricao':     'Descrição da Regra',
            'ativa':         'Regra Ativa',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loja:
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()


class PartidaRegraForm(forms.ModelForm):
    class Meta:
        model = PartidaRegra
        fields = ['tipo', 'conta', 'ordem']
        widgets = {
            'tipo':  forms.Select(attrs={'class': 'form-control'}),
            'conta': forms.Select(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }
        labels = {
            'tipo':  'Tipo (D/C)',
            'conta': 'Conta Analítica',
            'ordem': 'Ordem',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loja:
            analiticas = ContaAnalitica.objects.filter(
                loja=loja, aceita_lancamento=True
            ).order_by('codigo_classificacao')
            self.fields['conta'].queryset = analiticas


class LancamentoContabilForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = LancamentoContabil
        fields = ['loja', 'data_lancamento', 'historico', 'tipo', 'lancamento_referencia']
        widgets = {
            'data_lancamento':      forms.DateInput(attrs={'type': 'date'}),
            'historico':            forms.TextInput(attrs={'placeholder': 'Descrição do lançamento…'}),
            'lancamento_referencia': forms.HiddenInput(),
        }
        labels = {
            'loja':                  'Loja',
            'data_lancamento':       'Data do Lançamento',
            'historico':             'Histórico',
            'tipo':                  'Tipo',
            'lancamento_referencia': 'Lançamento de Referência',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loja:
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()
            # Filtra referências da mesma loja
            self.fields['lancamento_referencia'].queryset = (
                LancamentoContabil.objects.filter(loja=loja)
            )
        self.fields['lancamento_referencia'].required = False


class PeriodoContabilForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = PeriodoContabil
        fields = ['loja', 'ano', 'mes']
        widgets = {
            'ano': forms.NumberInput(attrs={'min': 2020, 'max': 2099, 'placeholder': '2025'}),
            'mes': forms.NumberInput(attrs={'min': 1, 'max': 12, 'placeholder': '1–12'}),
        }
        labels = {
            'loja': 'Loja',
            'ano':  'Ano',
            'mes':  'Mês',
        }

    def __init__(self, *args, loja=None, **kwargs):
        super().__init__(*args, **kwargs)
        if loja:
            self.fields['loja'].initial = loja
            self.fields['loja'].widget = forms.HiddenInput()


# Formset para gerenciar múltiplas partidas de uma regra
class PartidaRegraFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, loja=None, **kwargs):
        self.loja = loja
        super().__init__(*args, **kwargs)

        # Filtrar contas por loja em cada formulário
        for form in self.forms:
            if loja:
                analiticas = ContaAnalitica.objects.filter(
                    loja=loja, aceita_lancamento=True
                ).order_by('codigo_classificacao')
                form.fields['conta'].queryset = analiticas

    def clean(self):
        """Validação customizada do formset."""
        super().clean()

        if any(self.errors):
            return

        # Validar que há pelo menos um débito e um crédito (apenas forms não vazios)
        debitos = sum(1 for form in self.forms
                     if form.cleaned_data.get('tipo') == 'D'
                     and form.cleaned_data.get('conta')
                     and not form.cleaned_data.get('DELETE', False))
        creditos = sum(1 for form in self.forms
                      if form.cleaned_data.get('tipo') == 'C'
                      and form.cleaned_data.get('conta')
                      and not form.cleaned_data.get('DELETE', False))

        if debitos == 0:
            raise forms.ValidationError('Deve haver pelo menos um débito.')
        if creditos == 0:
            raise forms.ValidationError('Deve haver pelo menos um crédito.')


PartidaRegraInlineFormSet = inlineformset_factory(
    RegraContabil,
    PartidaRegra,
    form=PartidaRegraForm,
    formset=PartidaRegraFormSet,
    extra=5,  # Inicialmente 5 linhas vazias (usuário pode adicionar mais)
    min_num=2,  # Mínimo 2 partidas (1D + 1C)
    validate_min=True,
)
