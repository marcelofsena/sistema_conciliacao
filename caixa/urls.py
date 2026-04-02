from django.urls import path
from . import views

urlpatterns = [
    path('conferencia/', views.pagina_conferencia, name='conferencia_caixa'),
    path('conferencia/analitico/', views.exportar_analitico_excel, name='exportar_analitico'),
]
