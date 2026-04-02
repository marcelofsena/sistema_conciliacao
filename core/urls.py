from django.urls import path
from . import views

urlpatterns = [
    path('selecionar-loja/',                 views.selecionar_loja,      name='selecionar_loja'),
    path('trocar-loja/',                     views.trocar_loja,          name='trocar_loja'),
    path('empresas/',                       views.empresas_lista,       name='empresas_lista'),
    path('empresas/nova/',                  views.empresa_criar,        name='empresa_criar'),
    path('empresas/<int:pk>/editar/',       views.empresa_editar,       name='empresa_editar'),
    path('empresas/<int:pk>/toggle/',       views.empresa_toggle_ativa, name='empresa_toggle'),
]
