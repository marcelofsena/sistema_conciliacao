from django.contrib import admin
from .models import Sangria, MovimentoCaixa, ConciliacaoCaixa


@admin.register(Sangria)
class SangriaAdmin(admin.ModelAdmin):
    list_display = ('codigo_loja', 'nr_abertura', 'vlrsanguia', 'sangriadescricao')
    search_fields = ('codigo_loja', 'nr_abertura')


@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ('codigo_loja', 'nr_abertura', 'dif_resumo',
                    'valor_dinheiro_envelope', 'tot_vend_resumo')
    search_fields = ('codigo_loja', 'nr_abertura')


@admin.register(ConciliacaoCaixa)
class ConciliacaoCaixaAdmin(admin.ModelAdmin):
    list_display = ('codigo_loja', 'nr_abertura', 'data_conciliacao', 'turno',
                    'status', 'diferenca_total', 'contabilizado')
    list_filter = ('status', 'contabilizado', 'turno')
    search_fields = ('codigo_loja', 'nr_abertura')
