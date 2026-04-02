from django.urls import path
from . import views

urlpatterns = [
    # Plano de Contas
    path('plano-contas/',                          views.plano_contas,             name='plano_contas'),
    path('plano-contas/importar/',                 views.importar_plano_contas,    name='importar_plano_contas'),
    path('plano-contas/sintetica/nova/',            views.conta_sintetica_criar,    name='sintetica_criar'),
    path('plano-contas/sintetica/<int:pk>/editar/', views.conta_sintetica_editar,   name='sintetica_editar'),
    path('plano-contas/analitica/nova/',            views.conta_analitica_criar,    name='analitica_criar'),
    path('plano-contas/analitica/<int:pk>/editar/', views.conta_analitica_editar,   name='analitica_editar'),

    # Templates de Plano de Contas
    path('templates-plano/',                       views.templates_plano_contas,   name='templates_plano_contas'),
    path('templates-plano/<int:template_id>/importar/', views.importar_template_plano, name='importar_template_plano'),

    # Templates de Eventos e Regras
    path('templates-evento-regra/',                    views.templates_evento_regra,   name='templates_evento_regra'),
    path('templates-evento-regra/<int:template_id>/importar/', views.importar_template_evento_regra, name='importar_template_evento_regra'),

    # Tipos de Evento
    path('tipos-evento/',                       views.tipos_evento,         name='tipos_evento'),
    path('tipos-evento/novo/',                  views.tipo_evento_criar,    name='tipo_evento_criar'),
    path('tipos-evento/<int:pk>/editar/',        views.tipo_evento_editar,   name='tipo_evento_editar'),
    path('tipos-evento/<int:pk>/toggle/',        views.tipo_evento_toggle,   name='tipo_evento_toggle'),
    path('eventos-modelo/importar/',            views.importar_eventos_modelo, name='importar_eventos_modelo'),

    # Regras Contábeis
    path('regras/',                             views.regras_contabeis,       name='regras_contabeis'),
    path('regras/nova/',                        views.regra_contabil_criar,   name='regra_contabil_criar'),
    path('regras/<int:pk>/editar/',              views.regra_contabil_editar,  name='regra_contabil_editar'),
    path('regras/<int:pk>/toggle/',              views.regra_contabil_toggle,  name='regra_contabil_toggle'),

    # Períodos Contábeis
    path('periodos/',                           views.periodos_contabeis,  name='periodos_contabeis'),
    path('periodos/novo/',                      views.periodo_criar,        name='periodo_criar'),
    path('periodos/<int:pk>/fechar/',            views.periodo_fechar,       name='periodo_fechar'),
    path('periodos/<int:pk>/reabrir/',           views.periodo_reabrir,      name='periodo_reabrir'),

    # Eventos Operacionais
    path('eventos/',                            views.eventos_operacionais, name='eventos_operacionais'),

    # Lançamentos Contábeis
    path('lancamentos/',                        views.lancamentos,           name='lancamentos'),
    path('lancamentos/novo/',                   views.lancamento_criar,      name='lancamento_criar'),
    path('lancamentos/<int:pk>/',               views.lancamento_detalhe,    name='lancamento_detalhe'),

    # Simulação de Lançamentos
    path('simular-lancamento/',                 views.simular_lancamento,    name='simular_lancamento'),
    path('confirmar-lancamento/',               views.confirmar_lancamento_simulado, name='confirmar_lancamento'),

    # Relatórios
    path('gerar-dre/',                          views.gerar_dre,             name='gerar_dre'),
    path('relatorios/',                         views.relatorios_contabeis,  name='relatorios_contabeis'),
]
