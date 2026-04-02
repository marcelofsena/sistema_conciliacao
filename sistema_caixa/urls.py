from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('importacoes.urls')),      # Home, Login, Upload, Formas Pagamento
    path('', include('caixa.urls')),            # Conferência e Exportação Analítica
    path('', include('core.urls')),             # Empresas / Lojas
    path('contabilidade/', include('contabilidade.urls')),
    path('financeiro/', include('financeiro.urls')),
]
