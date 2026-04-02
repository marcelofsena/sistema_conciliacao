from django.urls import path
from . import views

urlpatterns = [
    # Contas a Receber
    path('contas-receber/',                         views.contas_receber,           name='contas_receber'),
    path('contas-receber/nova/',                    views.conta_receber_criar,      name='conta_receber_criar'),
    path('contas-receber/<int:pk>/editar/',          views.conta_receber_editar,     name='conta_receber_editar'),
    path('contas-receber/<int:pk>/receber/',         views.registrar_recebimento,    name='registrar_recebimento'),
    path('contas-receber/<int:pk>/cancelar/',        views.cancelar_conta_receber,   name='cancelar_conta_receber'),

    # Contas a Pagar
    path('contas-pagar/',                           views.contas_pagar,             name='contas_pagar'),
    path('contas-pagar/nova/',                      views.conta_pagar_criar,        name='conta_pagar_criar'),
    path('contas-pagar/<int:pk>/editar/',            views.conta_pagar_editar,       name='conta_pagar_editar'),
    path('contas-pagar/<int:pk>/pagar/',             views.registrar_pagamento,      name='registrar_pagamento'),
    path('contas-pagar/<int:pk>/cancelar/',          views.cancelar_conta_pagar,     name='cancelar_conta_pagar'),
]
