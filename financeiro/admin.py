from django.contrib import admin
from .models import ContaReceber, ContaPagar, ExtratoBancario


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor_original', 'valor_recebido', 'saldo',
                    'data_vencimento', 'origem', 'status', 'loja')
    list_filter = ('status', 'origem', 'loja')
    search_fields = ('descricao', 'referencia_evento')
    date_hierarchy = 'data_vencimento'


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'fornecedor', 'valor_original', 'valor_pago',
                    'saldo', 'data_vencimento', 'origem', 'status', 'loja')
    list_filter = ('status', 'origem', 'loja')
    search_fields = ('descricao', 'fornecedor')
    date_hierarchy = 'data_vencimento'


@admin.register(ExtratoBancario)
class ExtratoBancarioAdmin(admin.ModelAdmin):
    list_display = ('banco', 'data_movimento', 'descricao', 'tipo', 'valor',
                    'conciliado', 'loja')
    list_filter = ('banco', 'tipo', 'conciliado', 'loja')
    search_fields = ('descricao', 'banco')
    date_hierarchy = 'data_movimento'
