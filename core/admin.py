from django.contrib import admin
from .models import Empresa, PerfilUsuario, RegistroAuditoria


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('id_empresa', 'descricao', 'cnpj', 'ncad_swfast', 'ncad_ifood', 'ncad_cartoes', 'integrado', 'ativa')
    search_fields = ('descricao', 'cnpj', 'ncad_ifood')
    list_filter = ('integrado', 'ativa')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo_acesso')
    filter_horizontal = ('lojas_permitidas',)


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'usuario', 'tipo_acao', 'modelo', 'objeto_id', 'loja')
    list_filter = ('tipo_acao', 'modelo')
    search_fields = ('modelo', 'objeto_id', 'motivo')
    readonly_fields = ('usuario', 'data_hora', 'tipo_acao', 'modelo', 'objeto_id',
                       'motivo', 'snapshot_antes', 'snapshot_depois', 'loja')
