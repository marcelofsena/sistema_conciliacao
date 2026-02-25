from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Rotas de Autenticação
    path('login/', auth_views.LoginView.as_view(template_name='importacoes/login.html', next_page='home'), name='login'),
    path('sair/', views.sair_do_sistema, name='logout'),
    path('', views.home, name='home'), # <--- NOVA ROTA INICIAL
    path('importar/', views.pagina_upload, name='upload_arquivos'),
    path('conferencia/', views.pagina_conferencia, name='conferencia_caixa'),
    path('formas-pagamento/', views.sincronizar_formas_pagamento, name='formas_pagamento'),
    path('conferencia/analitico/', views.exportar_analitico_excel, name='exportar_analitico'),
    # O "next_page='home'" faz com que ele volte para a tela inicial após sair
    
]