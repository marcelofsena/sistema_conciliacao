from django.contrib import admin
from .models import Empresa, VendaSWFast, TransacaoStone, PedidoIFood, FormaPagamento, Sangria, MovimentoCaixa, PerfilUsuario
# Configuração para a tabela Empresa ficar bonita no painel

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_acesso')
    # O filter_horizontal cria aquela caixinha bonita de "passar de um lado pro outro" no painel admin
    filter_horizontal = ('lojas_permitidas',)
    
@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    # Quais colunas vão aparecer na listagem
    list_display = ('id_empresa', 'descricao', 'ncad_ifood', 'integrado')
    # Adiciona uma barra de pesquisa
    search_fields = ('descricao', 'ncad_ifood')
    # Adiciona um filtro lateral
    list_filter = ('integrado',)

# Já vamos registrar as planilhas importadas para você ver os dados por lá também!
admin.site.register(VendaSWFast)
admin.site.register(TransacaoStone)
admin.site.register(PedidoIFood)

@admin.register(FormaPagamento)
class FormaPagamentoAdmin(admin.ModelAdmin):
    # Adicionamos codigo_loja e aplicativo na tela
    list_display = ('forma_pagamento', 'aplicativo', 'codigo_loja', 'especific_form_pgto')
    search_fields = ('forma_pagamento', 'especific_form_pgto', 'codigo_loja')

@admin.register(Sangria)
class SangriaAdmin(admin.ModelAdmin):
    list_display = ('codigo_loja', 'nr_abertura', 'vlrsanguia', 'sangriadescricao')
    search_fields = ('codigo_loja', 'nr_abertura')

@admin.register(MovimentoCaixa)
class MovimentoCaixaAdmin(admin.ModelAdmin):
    list_display = ('codigo_loja', 'nr_abertura', 'dif_resumo', 'valor_dinheiro_envelope')
    search_fields = ('codigo_loja', 'nr_abertura')