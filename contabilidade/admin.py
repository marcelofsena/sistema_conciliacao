from django.contrib import admin
from .models import (
    TipoConta, ContaSintetica, ContaAnalitica, TipoEvento, RegraContabil, PartidaRegra,
    EventoOperacional, LancamentoContabil, PartidaLancamento,
    PeriodoContabil, ModeloRelatorio, EstruturaRelatorio, ComposicaoEstrutura,
    TemplateplanoConta, ContaTemplate,
    TemplateEventoRegra, EventoTemplate, RegraTemplate, PartidaRegraTemplate
)


# ==========================================
# TIPOS DE CONTAS (CONFIGURÁVEL)
# ==========================================

@admin.register(TipoConta)
class TipoContaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'natureza', 'ordem', 'ativo')
    list_filter = ('ativo', 'natureza')
    list_editable = ('natureza', 'ordem', 'ativo')
    ordering = ('ordem', 'codigo')


# ==========================================
# PLANO DE CONTAS
# ==========================================

@admin.register(ContaSintetica)
class ContaSinteticaAdmin(admin.ModelAdmin):
    list_display = ('codigo_classificacao', 'nome', 'tipo_conta', 'nivel', 'conta_pai', 'loja', 'eh_modelo')
    list_filter = ('tipo_conta', 'loja', 'nivel', 'eh_modelo')
    list_editable = ('eh_modelo',)
    search_fields = ('codigo_classificacao', 'nome')


@admin.register(ContaAnalitica)
class ContaAnaliticaAdmin(admin.ModelAdmin):
    list_display = ('codigo_reduzido', 'codigo_classificacao', 'nome',
                    'conta_sintetica', 'natureza_saldo', 'aceita_lancamento', 'loja', 'eh_modelo')
    list_filter = ('natureza_saldo', 'aceita_lancamento', 'loja', 'eh_modelo')
    list_editable = ('eh_modelo',)
    search_fields = ('codigo_reduzido', 'codigo_classificacao', 'nome')


# ==========================================
# EVENTOS E REGRAS
# ==========================================

@admin.register(TipoEvento)
class TipoEventoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'modulo_origem', 'ativo', 'eh_modelo')
    list_filter = ('modulo_origem', 'ativo', 'eh_modelo')
    list_editable = ('eh_modelo',)


class PartidaRegraInline(admin.TabularInline):
    model = PartidaRegra
    extra = 2
    fields = ('tipo', 'conta', 'ordem')


@admin.register(RegraContabil)
class RegraContabilAdmin(admin.ModelAdmin):
    list_display = ('tipo_evento', 'descricao', 'ativa', 'loja', 'eh_modelo')
    list_filter = ('tipo_evento', 'ativa', 'loja', 'eh_modelo')
    list_editable = ('eh_modelo',)
    inlines = [PartidaRegraInline]


@admin.register(PartidaRegra)
class PartidaRegraAdmin(admin.ModelAdmin):
    list_display = ('regra', 'tipo', 'conta', 'ordem')
    list_filter = ('tipo', 'regra__tipo_evento')
    ordering = ('regra', 'ordem')


@admin.register(EventoOperacional)
class EventoOperacionalAdmin(admin.ModelAdmin):
    list_display = ('tipo_evento', 'data_evento', 'valor', 'status', 'loja')
    list_filter = ('status', 'tipo_evento', 'loja')
    readonly_fields = ('criado_em',)


# ==========================================
# LANÇAMENTOS
# ==========================================

class PartidaInline(admin.TabularInline):
    model = PartidaLancamento
    extra = 2


@admin.register(LancamentoContabil)
class LancamentoContabilAdmin(admin.ModelAdmin):
    list_display = ('numero', 'data_lancamento', 'historico', 'tipo', 'loja')
    list_filter = ('tipo', 'loja', 'data_lancamento')
    search_fields = ('numero', 'historico')
    inlines = [PartidaInline]
    readonly_fields = ('data_registro',)


# ==========================================
# PERÍODOS
# ==========================================

@admin.register(PeriodoContabil)
class PeriodoContabilAdmin(admin.ModelAdmin):
    list_display = ('ano', 'mes', 'status', 'loja', 'data_fechamento', 'fechado_por')
    list_filter = ('status', 'loja', 'ano')


# ==========================================
# RELATÓRIOS CONTÁBEIS
# ==========================================

class EstruturaInline(admin.TabularInline):
    model = EstruturaRelatorio
    extra = 1


class ComposicaoInline(admin.TabularInline):
    model = ComposicaoEstrutura
    extra = 1


@admin.register(ModeloRelatorio)
class ModeloRelatorioAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'tipo', 'loja', 'ativo')
    list_filter = ('tipo', 'loja')
    inlines = [EstruturaInline]


@admin.register(EstruturaRelatorio)
class EstruturaRelatorioAdmin(admin.ModelAdmin):
    list_display = ('posicao', 'descricao', 'tipo_calculo', 'operacao', 'modelo')
    list_filter = ('tipo_calculo', 'modelo')
    inlines = [ComposicaoInline]


# ==========================================
# TEMPLATES DE PLANO DE CONTAS
# ==========================================

class ContaTemplateInline(admin.TabularInline):
    model = ContaTemplate
    extra = 1
    fields = ('codigo_classificacao', 'nome', 'tipo_conta', 'pai_codigo', 'nivel')


@admin.register(TemplateplanoConta)
class TemplatePlanoContaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    list_filter = ('ativo', 'criado_em')
    inlines = [ContaTemplateInline]


@admin.register(ContaTemplate)
class ContaTemplateAdmin(admin.ModelAdmin):
    list_display = ('codigo_classificacao', 'nome', 'tipo_conta', 'template', 'nivel')
    list_filter = ('template', 'tipo_conta', 'nivel')
    search_fields = ('codigo_classificacao', 'nome')


# ==========================================
# TEMPLATES DE EVENTOS E REGRAS
# ==========================================

class PartidaRegraTemplateInline(admin.TabularInline):
    model = PartidaRegraTemplate
    extra = 1
    fields = ('tipo', 'codigo_conta', 'ordem')


class RegraTemplateInline(admin.TabularInline):
    model = RegraTemplate
    extra = 1
    fields = ('evento', 'descricao', 'ativa')
    inlines = [PartidaRegraTemplateInline]


class EventoTemplateInline(admin.TabularInline):
    model = EventoTemplate
    extra = 1
    fields = ('codigo', 'descricao', 'modulo_origem')


@admin.register(TemplateEventoRegra)
class TemplateEventoRegraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo', 'criado_em')
    list_filter = ('ativo', 'criado_em')
    inlines = [EventoTemplateInline]


@admin.register(EventoTemplate)
class EventoTemplateAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'modulo_origem', 'template')
    list_filter = ('modulo_origem', 'template')
    search_fields = ('codigo', 'descricao')


@admin.register(RegraTemplate)
class RegraTemplateAdmin(admin.ModelAdmin):
    list_display = ('evento', 'descricao', 'ativa', 'template')
    list_filter = ('ativa', 'template', 'evento__template')
    inlines = [PartidaRegraTemplateInline]


@admin.register(PartidaRegraTemplate)
class PartidaRegraTemplateAdmin(admin.ModelAdmin):
    list_display = ('regra', 'tipo', 'codigo_conta', 'ordem')
    list_filter = ('tipo', 'regra__template')
    ordering = ('regra', 'ordem')
