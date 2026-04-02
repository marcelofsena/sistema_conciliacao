"""
Middleware para garantir que todo usuário autenticado possui um PerfilUsuario
e que uma loja está sempre selecionada na sessão.
"""

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from .models import get_perfil_usuario, Empresa


class EnsureUserPerfilMiddleware(MiddlewareMixin):
    """
    Cria automaticamente um PerfilUsuario para usuários autenticados que não possuem um.
    Isso previne RelatedObjectDoesNotExist quando o perfil não foi criado manualmente.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                _ = request.user.perfil
            except:
                # Usuário não tem perfil, criar automaticamente
                get_perfil_usuario(request.user)
        return None


class LojaSessionMiddleware(MiddlewareMixin):
    """
    Middleware para garantir que a sessão de loja sempre exista.
    Se o usuário não tiver uma loja selecionada, redireciona para o seletor.
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        # URLs que NÃO precisam de loja selecionada
        self.urls_sem_loja = [
            '/admin/',
            '/login/',
            '/logout/',
            '/accounts/',
            '/selecionar-loja/',
            '/static/',
            '/media/',
            '/trocar-loja/',
        ]

    def process_request(self, request):
        # Verificar se é URL que não precisa de loja
        if any(request.path.startswith(url) for url in self.urls_sem_loja):
            return None

        # Se usuário não autenticado, deixa passar (será redirecionado ao login)
        if not request.user.is_authenticated:
            return None

        # Verificar se usuário tem lojas vinculadas
        lojas = request.user.perfil.get_lojas()
        if lojas.count() == 0:
            # Usuário sem lojas vinculadas
            return None

        # Verificar se existe loja_id na sessão
        loja_id = request.session.get('loja_id')

        if not loja_id:
            # Loja não foi selecionada ainda
            if lojas.count() == 1:
                # Auto-seleciona loja única
                request.session['loja_id'] = lojas.first().id_empresa
                request.session['loja_nome'] = lojas.first().descricao
            else:
                # Múltiplas lojas - redireciona ao seletor
                return redirect('selecionar_loja')
        else:
            # Validar se loja_id ainda é válida (usuário continua vinculado)
            if not lojas.filter(id_empresa=loja_id).exists():
                # Loja foi desvinculada - redirecionar ao seletor
                del request.session['loja_id']
                if 'loja_nome' in request.session:
                    del request.session['loja_nome']
                if lojas.count() == 1:
                    request.session['loja_id'] = lojas.first().id_empresa
                    request.session['loja_nome'] = lojas.first().descricao
                else:
                    return redirect('selecionar_loja')

        # Adicionar loja ao request para fácil acesso
        try:
            request.loja = Empresa.objects.get(id_empresa=request.session.get('loja_id'))
        except Empresa.DoesNotExist:
            pass

        return None
