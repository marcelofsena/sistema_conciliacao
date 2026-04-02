from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Empresa
from .forms import EmpresaForm


@login_required(login_url='login')
def selecionar_loja(request):
    """
    Tela para selecionar a loja com a qual o usuário vai trabalhar.
    Se o usuário tiver apenas 1 loja, é auto-selecionada.
    """
    lojas = request.user.perfil.get_lojas()

    # Se tem apenas uma loja, auto-seleciona
    if lojas.count() == 1:
        request.session['loja_id'] = lojas.first().id_empresa
        request.session['loja_nome'] = lojas.first().descricao
        return redirect('home')

    # Se POST, usuário escolheu uma loja
    if request.method == 'POST':
        loja_id = request.POST.get('loja_id')
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        request.session['loja_id'] = loja.id_empresa
        request.session['loja_nome'] = loja.descricao
        messages.success(request, f'Você está trabalhando em: {loja.descricao}')
        return redirect('home')

    return render(request, 'core/selecionar_loja.html', {
        'lojas': lojas,
    })


@login_required(login_url='login')
def trocar_loja(request):
    """
    Endpoint para trocar a loja na sessão.
    """
    loja_id = request.GET.get('id') or request.POST.get('id')

    if not loja_id:
        messages.error(request, 'Loja não especificada.')
        return redirect('home')

    lojas = request.user.perfil.get_lojas()
    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))

    request.session['loja_id'] = loja.id_empresa
    request.session['loja_nome'] = loja.descricao
    messages.success(request, f'Loja alterada para: {loja.descricao}')

    # Redirecionar para a página anterior ou home
    next_url = request.GET.get('next') or request.POST.get('next')
    return redirect(next_url or 'home')


@login_required(login_url='login')
def empresas_lista(request):
    empresas = Empresa.objects.all().order_by('descricao')
    return render(request, 'core/empresas_lista.html', {'empresas': empresas})


@login_required(login_url='login')
def empresa_criar(request):
    form = EmpresaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Empresa cadastrada com sucesso.')
        return redirect('empresas_lista')
    return render(request, 'core/empresa_form.html', {
        'form': form,
        'titulo': 'Nova Empresa',
        'acao': 'Cadastrar',
    })


@login_required(login_url='login')
def empresa_editar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    form = EmpresaForm(request.POST or None, instance=empresa)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{empresa.descricao}" atualizada com sucesso.')
        return redirect('empresas_lista')
    return render(request, 'core/empresa_form.html', {
        'form': form,
        'empresa': empresa,
        'titulo': f'Editar — {empresa.descricao}',
        'acao': 'Salvar alterações',
    })


@login_required(login_url='login')
def empresa_toggle_ativa(request, pk):
    if request.method == 'POST':
        empresa = get_object_or_404(Empresa, pk=pk)
        empresa.ativa = not empresa.ativa
        empresa.save(update_fields=['ativa'])
        estado = 'ativada' if empresa.ativa else 'desativada'
        messages.success(request, f'"{empresa.descricao}" {estado}.')
    return redirect('empresas_lista')
