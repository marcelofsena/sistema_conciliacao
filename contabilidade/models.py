"""
Contabilidade - Motor Contábil Orientado a Eventos.

Conforme regra de negócio:
- "O Motor Contábil é a fonte inquestionável da verdade financeira"
- "Lançamentos não podem ser apagados ou adulterados"
- "Ajustes via lançamentos de correção"
- "Meses fechados são bloqueados, com possibilidade de reabertura para estornos"

Referência PDFs Blue:
- Plano de Contas com contas Sintéticas (árvore) e Analíticas (folha)
- Estrutura hierárquica com mínimo 4 níveis
- DRE/DFC/DOAR com modelos flexíveis (estrutura + composição)
- Rotina de fechamento mensal com apuração de resultado
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from core.models import AuditoriaMixin, Empresa


# ==========================================
# TEMPLATES DE PLANO DE CONTAS
# ==========================================

class TemplateplanoConta(models.Model):
    """
    Template reutilizável de plano de contas.
    Permite que novos usuários importem um plano pronto ou criem do zero.
    """
    nome = models.CharField(
        max_length=100, verbose_name="Nome do Template",
        help_text="Ex: Restaurante Brasileiro, Pequeno Comercio, etc"
    )
    descricao = models.TextField(
        verbose_name="Descrição",
        blank=True,
        help_text="Descrição do template e quando usar"
    )
    ativo = models.BooleanField(
        default=True, verbose_name="Ativo"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Template Plano de Contas'
        verbose_name_plural = 'Templates Plano de Contas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ContaTemplate(models.Model):
    """
    Contas que fazem parte de um template.
    Podem ser importadas para qualquer loja.
    """
    template = models.ForeignKey(
        TemplateplanoConta, on_delete=models.CASCADE,
        related_name='contas', verbose_name="Template"
    )
    codigo_classificacao = models.CharField(
        max_length=20, verbose_name="Código de Classificação"
    )
    nome = models.CharField(max_length=255, verbose_name="Nome da Conta")
    tipo_conta = models.CharField(
        max_length=20, verbose_name="Tipo de Conta",
        choices=[
            ('ATIVO', 'Ativo'),
            ('PASSIVO', 'Passivo'),
            ('RECEITA', 'Receita'),
            ('CUSTO', 'Custo'),
            ('DESPESA', 'Despesa'),
        ]
    )
    pai_codigo = models.CharField(
        max_length=20, null=True, blank=True,
        verbose_name="Código da Conta Pai",
        help_text="Deixe vazio se for conta raiz"
    )
    nivel = models.PositiveIntegerField(
        default=1, verbose_name="Nível Hierárquico"
    )

    class Meta:
        verbose_name = 'Conta Template'
        verbose_name_plural = 'Contas Template'
        unique_together = (('template', 'codigo_classificacao'),)
        ordering = ['codigo_classificacao']

    def __str__(self):
        return f"{self.codigo_classificacao} - {self.nome}"


# ==========================================
# TEMPLATES DE EVENTOS E REGRAS CONTÁBEIS
# ==========================================

class TemplateEventoRegra(models.Model):
    """
    Template reutilizável de eventos e suas regras contábeis.
    Permite importar eventos com regras pré-configuradas para qualquer loja.
    """
    nome = models.CharField(
        max_length=100, verbose_name="Nome do Template",
        help_text="Ex: Restaurante Padrão, Lanchonete, Padaria"
    )
    descricao = models.TextField(
        verbose_name="Descrição",
        blank=True,
        help_text="Descrição do template e quando usar"
    )
    ativo = models.BooleanField(
        default=True, verbose_name="Ativo"
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Template Evento/Regra'
        verbose_name_plural = 'Templates Evento/Regra'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class EventoTemplate(models.Model):
    """
    Tipo de evento que faz parte de um template.
    Pode ser importado para qualquer loja.
    """
    template = models.ForeignKey(
        TemplateEventoRegra, on_delete=models.CASCADE,
        related_name='eventos', verbose_name="Template"
    )
    codigo = models.CharField(
        max_length=50, verbose_name="Código do Evento",
        help_text="Ex: VENDA_REALIZADA, PAGAMENTO_RECEBIDO"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    modulo_origem = models.CharField(
        max_length=50, verbose_name="Módulo de Origem",
        help_text="Ex: CAIXA, ESTOQUE, FINANCEIRO"
    )

    class Meta:
        verbose_name = 'Evento Template'
        verbose_name_plural = 'Eventos Template'
        unique_together = (('template', 'codigo'),)
        ordering = ['modulo_origem', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class RegraTemplate(models.Model):
    """
    Regra contábil que faz parte de um template.
    Mapeia um evento para débitos e créditos de contas analíticas.
    """
    template = models.ForeignKey(
        TemplateEventoRegra, on_delete=models.CASCADE,
        related_name='regras', verbose_name="Template"
    )
    evento = models.ForeignKey(
        EventoTemplate, on_delete=models.CASCADE,
        related_name='regras', verbose_name="Evento"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição da Regra")
    ativa = models.BooleanField(default=True, verbose_name="Regra Ativa")

    class Meta:
        verbose_name = 'Regra Template'
        verbose_name_plural = 'Regras Template'
        ordering = ['evento', '-ativa']

    def __str__(self):
        return f"{self.evento.codigo} - {self.descricao}"


class PartidaRegraTemplate(models.Model):
    """
    Partida individual de uma regra template.
    Identifica a conta por código de classificação (será resolvida na importação).
    """
    TIPO_CHOICES = [
        ('D', 'Débito'),
        ('C', 'Crédito'),
    ]

    regra = models.ForeignKey(
        RegraTemplate, on_delete=models.CASCADE,
        related_name='partidas', verbose_name="Regra"
    )
    tipo = models.CharField(
        max_length=1, choices=TIPO_CHOICES,
        verbose_name="Tipo", help_text="Débito (D) ou Crédito (C)"
    )
    codigo_conta = models.CharField(
        max_length=30, verbose_name="Código de Classificação da Conta",
        help_text="Ex: 1.1.1.02.0001 (será resolvido na importação)"
    )
    ordem = models.PositiveIntegerField(
        default=1, verbose_name="Ordem de Execução"
    )

    class Meta:
        verbose_name = 'Partida Regra Template'
        verbose_name_plural = 'Partidas Regra Template'
        ordering = ['regra', 'ordem']
        unique_together = (('regra', 'tipo', 'codigo_conta'),)

    def __str__(self):
        return f"{self.regra} - {self.get_tipo_display()} - {self.codigo_conta}"


# ==========================================
# TIPOS DE CONTAS (CONFIGURÁVEL)
# ==========================================

class TipoConta(models.Model):
    """
    Tipos de contas sintéticas configuráveis pelo administrador.
    Substituem o TIPO_CONTA_CHOICES hardcoded.
    """
    NATUREZA_CHOICES = [
        ('DEVEDORA', 'Devedora (Saldo Devedor)'),
        ('CREDORA', 'Credora (Saldo Credor)'),
        ('MISTA', 'Mista (Saldo Devedor ou Credor)'),
    ]

    codigo = models.CharField(
        max_length=20, unique=True, primary_key=True,
        verbose_name="Código"
    )
    descricao = models.CharField(
        max_length=100, verbose_name="Descrição"
    )
    natureza = models.CharField(
        max_length=20, choices=NATUREZA_CHOICES, default='DEVEDORA',
        verbose_name="Natureza da Conta",
        help_text="Define se a conta pode ter saldo devedor, credor ou ambos"
    )
    ordem = models.PositiveIntegerField(
        default=0, verbose_name="Ordem de Exibição"
    )
    ativo = models.BooleanField(
        default=True, verbose_name="Ativo"
    )

    class Meta:
        verbose_name = 'Tipo de Conta'
        verbose_name_plural = 'Tipos de Conta'
        ordering = ['ordem', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


# ==========================================
# PLANO DE CONTAS
# ==========================================

class ContaSintetica(AuditoriaMixin):
    """
    Conta Sintética (agrupadora) - forma a árvore hierárquica do plano de contas.
    Conforme PDF Blue: árvore do lado esquerdo com Ativo, Passivo, Receitas, Despesas.
    Numeração hierárquica por grupo (ex: 1, 1.1, 1.1.1).
    """

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="contas_sinteticas"
    )
    codigo_classificacao = models.CharField(
        max_length=20, verbose_name="Código de Classificação",
        help_text="Numeração hierárquica. Ex: 1, 1.1, 1.1.1"
    )
    nome = models.CharField(max_length=255, verbose_name="Nome da Conta")
    tipo_conta = models.ForeignKey(
        TipoConta, on_delete=models.PROTECT,
        verbose_name="Tipo de Conta", related_name="contas_sinteticas"
    )
    conta_pai = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='filhas', verbose_name="Conta Pai"
    )
    nivel = models.PositiveIntegerField(default=1, verbose_name="Nível Hierárquico")
    eh_modelo = models.BooleanField(
        default=False, verbose_name="É Modelo?",
        help_text="Marque para incluir essa conta nos templates de importação"
    )

    class Meta:
        verbose_name = 'Conta Sintética'
        verbose_name_plural = 'Contas Sintéticas'
        unique_together = (('loja', 'codigo_classificacao'),)
        ordering = ['codigo_classificacao']

    def __str__(self):
        return f"{self.codigo_classificacao} - {self.nome}"

    def clean(self):
        """Valida que contas sintéticas não podem ter nível superior a 4."""
        from django.core.exceptions import ValidationError
        if self.nivel > 4:
            raise ValidationError(
                "Conta sintética não pode ter nível superior a 4. "
                "Contas de nível 5 devem ser criadas como contas analíticas."
            )


class ContaAnalitica(AuditoriaMixin):
    """
    Conta Analítica (folha) - onde os lançamentos contábeis são efetivamente realizados.
    Conforme PDF Blue: lado direito da tela, com código reduzido e classificação fiscal.

    Controle automático de saldo (devedor/credor ou ambos) conforme regra de negócio.
    """
    NATUREZA_SALDO_CHOICES = [
        ('DEVEDOR', 'Devedor'),
        ('CREDOR', 'Credor'),
        ('AMBOS', 'Devedor e Credor'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="contas_analiticas"
    )
    codigo_reduzido = models.PositiveIntegerField(verbose_name="Código Reduzido")
    codigo_classificacao = models.CharField(
        max_length=30, verbose_name="Código de Classificação",
        help_text="Ex: 1110001, 3110001"
    )
    nome = models.CharField(max_length=255, verbose_name="Nome da Conta")
    conta_sintetica = models.ForeignKey(
        ContaSintetica, on_delete=models.CASCADE,
        related_name='contas_analiticas', verbose_name="Conta Sintética (Grupo)"
    )
    natureza_saldo = models.CharField(
        max_length=10, choices=NATUREZA_SALDO_CHOICES, default='DEVEDOR',
        verbose_name="Natureza do Saldo"
    )
    aceita_lancamento = models.BooleanField(default=True, verbose_name="Aceita Lançamentos")
    data_bloqueio = models.DateField(
        null=True, blank=True, verbose_name="Data de Bloqueio",
        help_text="Não aceita lançamentos com data anterior a esta"
    )
    centro_custo = models.BooleanField(
        default=False, verbose_name="Exige Centro de Custo"
    )
    eh_modelo = models.BooleanField(
        default=False, verbose_name="É Modelo?",
        help_text="Marque para incluir essa conta nos templates de importação"
    )

    class Meta:
        verbose_name = 'Conta Analítica'
        verbose_name_plural = 'Contas Analíticas'
        unique_together = (('loja', 'conta_sintetica', 'codigo_reduzido'),)
        ordering = ['codigo_classificacao']

    def __str__(self):
        return f"{self.codigo_reduzido} - {self.codigo_classificacao} - {self.nome}"


# ==========================================
# EVENTOS OPERACIONAIS (EVENT-DRIVEN)
# ==========================================

class TipoEvento(models.Model):
    """
    Catálogo de tipos de eventos operacionais que o sistema pode gerar.
    Conforme regra: "Uma ação no PDV ou no Estoque gera um evento
    (ex: VENDA_REALIZADA), e os módulos financeiros 'escutam' esse evento."
    """
    codigo = models.CharField(
        max_length=50, unique=True, verbose_name="Código do Evento",
        help_text="Ex: VENDA_REALIZADA, PAGAMENTO_RECEBIDO, COMPRA_REGISTRADA"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição")
    modulo_origem = models.CharField(
        max_length=50, verbose_name="Módulo de Origem",
        help_text="Ex: CAIXA, ESTOQUE, FINANCEIRO"
    )
    ativo = models.BooleanField(default=True)
    eh_modelo = models.BooleanField(
        default=False, verbose_name="É Modelo?",
        help_text="Marque para incluir esse evento nos templates de importação"
    )

    class Meta:
        verbose_name = 'Tipo de Evento'
        verbose_name_plural = 'Tipos de Evento'
        ordering = ['modulo_origem', 'codigo']

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class RegraContabil(models.Model):
    """
    Motor de Regras: mapeamento de Evento -> Débitos e Créditos.
    Conforme regra: "Tela para de/para (Mapeamento de qual Evento Operacional
    gera quais Débitos e Créditos no plano de contas)."

    Suporta MÚLTIPLAS partidas (N débitos + M créditos).
    Exemplo: VENDA_REALIZADA pode ter:
      - Débitos: Caixa (100) + Banco (50)
      - Créditos: Receita (120) + Impostos (30)
    """
    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="regras_contabeis"
    )
    tipo_evento = models.ForeignKey(
        TipoEvento, on_delete=models.CASCADE,
        related_name='regras', verbose_name="Tipo de Evento"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição da Regra")
    ativa = models.BooleanField(default=True, verbose_name="Regra Ativa")
    eh_modelo = models.BooleanField(
        default=False, verbose_name="É Modelo?",
        help_text="Marque para incluir essa regra nos templates de importação"
    )

    class Meta:
        verbose_name = 'Regra Contábil'
        verbose_name_plural = 'Regras Contábeis'
        ordering = ['tipo_evento', '-ativa']

    def __str__(self):
        return f"{self.tipo_evento.codigo} - {self.descricao}"

    def get_debitos(self):
        """Retorna todas as contas a debitar desta regra"""
        return self.partidas.filter(tipo='D').select_related('conta')

    def get_creditos(self):
        """Retorna todas as contas a creditar desta regra"""
        return self.partidas.filter(tipo='C').select_related('conta')


class PartidaRegra(models.Model):
    """
    Partida individual de uma regra contábil.
    Uma regra pode ter múltiplas partidas (débitos e créditos).
    """
    TIPO_CHOICES = [
        ('D', 'Débito'),
        ('C', 'Crédito'),
    ]

    regra = models.ForeignKey(
        RegraContabil, on_delete=models.CASCADE,
        related_name='partidas', verbose_name="Regra Contábil"
    )
    tipo = models.CharField(
        max_length=1, choices=TIPO_CHOICES,
        verbose_name="Tipo", help_text="Débito (D) ou Crédito (C)"
    )
    conta = models.ForeignKey(
        ContaAnalitica, on_delete=models.PROTECT,
        verbose_name="Conta Analítica"
    )
    ordem = models.PositiveIntegerField(
        default=1, verbose_name="Ordem de Execução"
    )

    class Meta:
        verbose_name = 'Partida de Regra'
        verbose_name_plural = 'Partidas de Regra'
        ordering = ['regra', 'ordem']
        unique_together = (('regra', 'tipo', 'conta'),)

    def __str__(self):
        tipo_display = "Débito" if self.tipo == 'D' else "Crédito"
        return f"{tipo_display}: {self.conta.codigo_classificacao} - {self.conta.nome}"


# ==========================================
# EVENTO OPERACIONAL (INSTÂNCIA)
# ==========================================

class EventoOperacional(models.Model):
    """
    Registro de um evento operacional ocorrido no sistema.
    Cada evento gera automaticamente os lançamentos contábeis
    conforme as regras configuradas.
    """
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente de Contabilização'),
        ('CONTABILIZADO', 'Contabilizado'),
        ('ERRO', 'Erro na Contabilização'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="eventos"
    )
    tipo_evento = models.ForeignKey(
        TipoEvento, on_delete=models.PROTECT,
        verbose_name="Tipo de Evento"
    )
    data_evento = models.DateTimeField(verbose_name="Data/Hora do Evento")
    valor = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valor do Evento"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='PENDENTE'
    )
    referencia_id = models.CharField(
        max_length=255, blank=True, verbose_name="ID de Referência",
        help_text="ID do objeto que originou o evento (venda, pedido, etc.)"
    )
    referencia_modelo = models.CharField(
        max_length=100, blank=True, verbose_name="Modelo de Referência",
        help_text="Nome do modelo que originou o evento"
    )
    dados_extras = models.JSONField(
        null=True, blank=True, verbose_name="Dados Extras",
        help_text="Informações adicionais do evento em JSON"
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    erro_mensagem = models.TextField(blank=True, verbose_name="Mensagem de Erro")

    class Meta:
        verbose_name = 'Evento Operacional'
        verbose_name_plural = 'Eventos Operacionais'
        ordering = ['-data_evento']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['tipo_evento', 'data_evento']),
            models.Index(fields=['loja', 'data_evento']),
        ]

    def __str__(self):
        return f"{self.tipo_evento.codigo} - R$ {self.valor} ({self.status})"


# ==========================================
# LANÇAMENTOS CONTÁBEIS (PARTIDAS DOBRADAS)
# ==========================================

class LancamentoContabil(models.Model):
    """
    Lançamento contábil IMUTÁVEL em partidas dobradas.

    Conforme regra de negócio:
    - "Lançamentos não podem ser apagados ou adulterados"
    - "Ajustes dentro de um mês aberto são feitos via lançamentos de correção"

    Cada lançamento possui uma ou mais partidas (débitos e créditos)
    que devem somar zero (princípio das partidas dobradas).
    """
    TIPO_CHOICES = [
        ('NORMAL', 'Normal'),
        ('CORRECAO', 'Correção/Ajuste'),
        ('ESTORNO', 'Estorno'),
        ('FECHAMENTO', 'Fechamento de Período'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="lancamentos"
    )
    numero = models.PositiveIntegerField(verbose_name="Número do Lançamento")
    data_lancamento = models.DateField(verbose_name="Data do Lançamento")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registro")
    historico = models.CharField(max_length=500, verbose_name="Histórico")
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default='NORMAL'
    )
    evento = models.ForeignKey(
        EventoOperacional, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='lancamentos', verbose_name="Evento de Origem"
    )
    lancamento_referencia = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='correcoes', verbose_name="Lançamento de Referência",
        help_text="Para estornos e correções, aponta ao lançamento original"
    )
    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name="Usuário Responsável"
    )
    periodo = models.ForeignKey(
        'PeriodoContabil', on_delete=models.PROTECT,
        verbose_name="Período Contábil"
    )

    class Meta:
        verbose_name = 'Lançamento Contábil'
        verbose_name_plural = 'Lançamentos Contábeis'
        unique_together = (('loja', 'numero'),)
        ordering = ['-data_lancamento', '-numero']

    def __str__(self):
        return f"Lanc. {self.numero} - {self.data_lancamento} - {self.historico[:50]}"


class PartidaLancamento(models.Model):
    """
    Partida individual de um lançamento contábil.
    Cada lançamento tem no mínimo 2 partidas (1 débito + 1 crédito).
    A soma dos débitos deve ser igual à soma dos créditos.
    """
    TIPO_CHOICES = [
        ('D', 'Débito'),
        ('C', 'Crédito'),
    ]

    lancamento = models.ForeignKey(
        LancamentoContabil, on_delete=models.CASCADE,
        related_name='partidas', verbose_name="Lançamento"
    )
    conta = models.ForeignKey(
        ContaAnalitica, on_delete=models.PROTECT,
        related_name='partidas', verbose_name="Conta Analítica"
    )
    tipo = models.CharField(max_length=1, choices=TIPO_CHOICES, verbose_name="D/C")
    valor = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name="Valor"
    )
    historico_complementar = models.CharField(
        max_length=255, blank=True, verbose_name="Histórico Complementar"
    )
    centro_custo = models.CharField(
        max_length=50, blank=True, verbose_name="Centro de Custo"
    )

    class Meta:
        verbose_name = 'Partida de Lançamento'
        verbose_name_plural = 'Partidas de Lançamento'

    def __str__(self):
        return f"{self.tipo} - {self.conta.codigo_reduzido} - R$ {self.valor}"


# ==========================================
# CONTROLE DE PERÍODOS
# ==========================================

class PeriodoContabil(models.Model):
    """
    Controle de períodos contábeis (meses).

    Conforme regra:
    - "Meses fechados são bloqueados sistemicamente"
    - "Há possibilidade de abertura para estornos parciais ou lançamentos complementares"

    Conforme PDF Blue - Rotina de Fechamento:
    - Apuração CMV, ICMS, PIS/COFINS
    - Encerramento de contas de resultado
    - Transferência para Lucros/Prejuízos Acumulados
    """
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('FECHADO', 'Fechado'),
        ('REABERTO', 'Reaberto para Ajustes'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="periodos"
    )
    ano = models.PositiveIntegerField(verbose_name="Ano")
    mes = models.PositiveIntegerField(verbose_name="Mês")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='ABERTO'
    )
    data_fechamento = models.DateTimeField(
        null=True, blank=True, verbose_name="Data/Hora do Fechamento"
    )
    fechado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='periodos_fechados', verbose_name="Fechado por"
    )
    data_reabertura = models.DateTimeField(
        null=True, blank=True, verbose_name="Data/Hora da Reabertura"
    )
    reaberto_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='periodos_reabertos', verbose_name="Reaberto por"
    )
    motivo_reabertura = models.TextField(
        blank=True, verbose_name="Motivo da Reabertura"
    )

    class Meta:
        verbose_name = 'Período Contábil'
        verbose_name_plural = 'Períodos Contábeis'
        unique_together = (('loja', 'ano', 'mes'),)
        ordering = ['-ano', '-mes']

    def __str__(self):
        return f"{self.mes:02d}/{self.ano} - {self.get_status_display()}"

    def clean(self):
        if self.mes < 1 or self.mes > 12:
            raise ValidationError({'mes': 'Mês deve ser entre 1 e 12.'})


# ==========================================
# MODELOS DE RELATÓRIOS CONTÁBEIS (DRE/DFC/DOAR)
# ==========================================

class ModeloRelatorio(models.Model):
    """
    Modelo de relatório contábil flexível.
    Conforme PDF Blue: "Sua estrutura de montagem não é fixa,
    possibilitando que a empresa monte qualquer relatório."

    Tipos: DRE (Demonstração do Resultado do Exercício),
           DFC (Demonstração do Fluxo de Caixa),
           DOAR (Demonstração das Origens e Aplicações de Recursos).
    """
    TIPO_CHOICES = [
        ('DRE', 'Demonstração do Resultado do Exercício'),
        ('DFC_DOAR', 'DFC / DOAR'),
    ]

    loja = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        verbose_name="Loja", related_name="modelos_relatorio"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição do Relatório")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, verbose_name="Tipo")
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Modelo de Relatório Contábil'
        verbose_name_plural = 'Modelos de Relatórios Contábeis'

    def __str__(self):
        return f"{self.descricao} ({self.tipo})"


class EstruturaRelatorio(models.Model):
    """
    Estrutura (esqueleto) do relatório contábil.
    Conforme PDF Blue:
    - Posição hierárquica (001, 001.001, 001.001.001 - até 3 níveis)
    - Tipo de cálculo: Sintética, Vinculada a Analíticas, Resultado, Manual, Grupo DFC
    - Operação: Positivo(+), Negativo(-), Igual(=), (+/-)
    """
    CALCULO_CHOICES = [
        (0, 'Sintética (Soma das contas)'),
        (1, 'Vinculada a Contas Analíticas'),
        (2, 'Resultado de Operações'),
        (3, 'Valor Informado Manualmente'),
        (4, 'Grupo de Contas DFC/DOAR'),
    ]

    OPERACAO_CHOICES = [
        (4, 'Positivo (+)'),
        (5, 'Negativo (-)'),
        (6, 'Igual (=)'),
        (7, '(+/-)'),
    ]

    modelo = models.ForeignKey(
        ModeloRelatorio, on_delete=models.CASCADE,
        related_name='estruturas', verbose_name="Modelo"
    )
    posicao = models.CharField(
        max_length=20, verbose_name="Posição",
        help_text="Posição hierárquica. Ex: 001, 001.001"
    )
    descricao = models.CharField(max_length=255, verbose_name="Descrição da Estrutura")
    tipo_calculo = models.IntegerField(
        choices=CALCULO_CHOICES, default=0, verbose_name="Tipo de Cálculo"
    )
    operacao = models.IntegerField(
        choices=OPERACAO_CHOICES, default=4, verbose_name="Operação"
    )

    class Meta:
        verbose_name = 'Estrutura de Relatório'
        verbose_name_plural = 'Estruturas de Relatório'
        ordering = ['posicao']
        unique_together = (('modelo', 'posicao'),)

    def __str__(self):
        return f"{self.posicao} - {self.descricao}"


class ComposicaoEstrutura(models.Model):
    """
    Composição: vincula contas analíticas a uma estrutura do relatório.
    Conforme PDF Blue: "Na composição serão informadas as contas
    de acordo com cada estrutura definida."
    """
    estrutura = models.ForeignKey(
        EstruturaRelatorio, on_delete=models.CASCADE,
        related_name='composicoes', verbose_name="Estrutura"
    )
    conta_analitica = models.ForeignKey(
        ContaAnalitica, on_delete=models.CASCADE,
        verbose_name="Conta Analítica"
    )

    class Meta:
        verbose_name = 'Composição de Estrutura'
        verbose_name_plural = 'Composições de Estrutura'
        unique_together = (('estrutura', 'conta_analitica'),)

    def __str__(self):
        return f"{self.estrutura.posicao} <- {self.conta_analitica}"
