from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticação
    path('login/', auth_views.LoginView.as_view(
        template_name='importacoes/login.html', next_page='home'), name='login'),
    path('sair/', views.sair_do_sistema, name='logout'),

    # Home
    path('', views.home, name='home'),

    # Importações
    path('importar/', views.pagina_upload, name='upload_arquivos'),
    path('formas-pagamento/', views.sincronizar_formas_pagamento, name='formas_pagamento'),
    path('formas-pagamento/<int:pk>/especificacao/', views.editar_especificacao_forma, name='editar_especificacao_forma'),
]
