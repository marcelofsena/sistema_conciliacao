from django.contrib import admin
from .models import VendaSWFast, TransacaoStone, PedidoIFood, FormaPagamento


@admin.register(VendaSWFast)
class VendaSWFastAdmin(admin.ModelAdmin):
    list_display = ('venda', 'forma_pagamento', 'aplicativo', 'valor_pagamento',
                    'codigo_loja', 'nr_abertura', 'data_hora_transacao', 'conciliado')
    list_filter = ('codigo_loja', 'aplicativo', 'conciliado')
    search_fields = ('venda', 'id_pedido_externo', 'chave_composta')


@admin.register(TransacaoStone)
class TransacaoStoneAdmin(admin.ModelAdmin):
    list_display = ('stone_id', 'stonecode', 'bandeira', 'produto',
                    'valor_bruto', 'valor_liquido', 'data_venda')
    list_filter = ('bandeira', 'produto')
    search_fields = ('stone_id', 'stonecode')


@admin.register(PedidoIFood)
class PedidoIFoodAdmin(admin.ModelAdmin):
    list_display = ('id_pedido', 'nr_pedido', 'restaurante', 'total_pedido',
                    'status_pedido', 'formas_pagamento', 'data')
    list_filter = ('status_pedido', 'id_restaurante')
    search_fields = ('id_pedido', 'nr_pedido')


@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    list_display = ('forma_pagamento', 'aplicativo', 'loja', 'especific_form_pgto', 'ativo')
    search_fields = ('forma_pagamento', 'especific_form_pgto', 'loja__descricao')
    list_filter = ('loja', 'aplicativo', 'especific_form_pgto', 'ativo')
    list_editable = ('ativo',)
    ordering = ('loja', 'aplicativo', 'forma_pagamento')
