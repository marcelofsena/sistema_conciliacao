from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from decimal import Decimal
import datetime

from .models import ContaReceber, ContaPagar
from .forms import (
    ContaReceberForm, RegistrarRecebimentoForm,
    ContaPagarForm, RegistrarPagamentoForm,
)
from core.models import Empresa


# ==========================================
# HELPERS
# ==========================================

def _totais_receber(qs):
    return {
        'total_aberto':   qs.filter(status__in=['ABERTO', 'PARCIAL']).aggregate(s=Sum('saldo'))['s'] or Decimal('0'),
        'total_recebido': qs.filter(status='RECEBIDO').aggregate(s=Sum('valor_recebido'))['s'] or Decimal('0'),
        'count_vencido':  qs.filter(status__in=['ABERTO', 'PARCIAL'], data_vencimento__lt=datetime.date.today()).count(),
    }

def _totais_pagar(qs):
    return {
        'total_aberto':  qs.filter(status__in=['ABERTO', 'PARCIAL']).aggregate(s=Sum('saldo'))['s'] or Decimal('0'),
        'total_pago':    qs.filter(status='PAGO').aggregate(s=Sum('valor_pago'))['s'] or Decimal('0'),
        'count_vencido': qs.filter(status__in=['ABERTO', 'PARCIAL'], data_vencimento__lt=datetime.date.today()).count(),
    }


# ==========================================
# CONTAS A RECEBER
# ==========================================

@login_required(login_url='login')
def contas_receber(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.GET.get('loja')
    status_filtro = request.GET.get('status', '')
    origem_filtro = request.GET.get('origem', '')
    loja = None
    titulos = []
    totais = {}

    if loja_id:
        loja = get_object_or_404(Empresa, pk=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        qs = ContaReceber.objects.filter(loja=loja).order_by('data_vencimento')
        totais = _totais_receber(qs)

        if status_filtro:
            qs = qs.filter(status=status_filtro)
        if origem_filtro:
            qs = qs.filter(origem=origem_filtro)
        titulos = qs

    return render(request, 'financeiro/contas_receber.html', {
        'lojas':          lojas,
        'loja':           loja,
        'titulos':        titulos,
        'totais':         totais,
        'status_filtro':  status_filtro,
        'origem_filtro':  origem_filtro,
        'status_choices': ContaReceber.STATUS_CHOICES,
        'origem_choices': ContaReceber.ORIGEM_CHOICES,
        'hoje':           datetime.date.today(),
    })


@login_required(login_url='login')
def conta_receber_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids) if loja_id else None
    form = ContaReceberForm(request.POST or None, loja=loja)
    if request.method == 'POST' and form.is_valid():
        cr = form.save(commit=False)
        cr.origem = 'MANUAL'
        cr.save()
        messages.success(request, f'Título "{cr.descricao}" criado.')
        return redirect('/financeiro/contas-receber/')
    return render(request, 'financeiro/conta_receber_form.html', {
        'form':   form,
        'loja':   loja,
        'titulo': 'Nova Conta a Receber',
        'acao':   'Criar título',
    })


@login_required(login_url='login')
def conta_receber_editar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    cr = get_object_or_404(ContaReceber, pk=pk, loja__id_empresa__in=lojas_ids)
    form = ContaReceberForm(request.POST or None, instance=cr, loja=cr.loja)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{cr.descricao}" atualizado.')
        return redirect('/financeiro/contas-receber/')
    return render(request, 'financeiro/conta_receber_form.html', {
        'form':   form,
        'cr':     cr,
        'loja':   cr.loja,
        'titulo': f'Editar — {cr.descricao}',
        'acao':   'Salvar alterações',
    })


@login_required(login_url='login')
def registrar_recebimento(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    cr = get_object_or_404(ContaReceber, pk=pk, loja__id_empresa__in=lojas_ids)

    if cr.status == 'RECEBIDO':
        messages.warning(request, 'Este título já foi totalmente recebido.')
        return redirect('/financeiro/contas-receber/')

    if cr.status == 'CANCELADO':
        messages.error(request, 'Título cancelado não pode ser baixado.')
        return redirect('/financeiro/contas-receber/')

    form = RegistrarRecebimentoForm(request.POST or None, saldo_restante=cr.saldo)

    if request.method == 'POST' and form.is_valid():
        cr.valor_recebido += form.cleaned_data['valor_recebido']
        cr.data_recebimento = form.cleaned_data['data_recebimento']
        obs = form.cleaned_data.get('observacoes', '').strip()
        if obs:
            cr.observacoes = (cr.observacoes + '\n' + obs).strip() if cr.observacoes else obs
        cr.save()  # save() recalcula saldo e status automaticamente
        messages.success(
            request,
            f'Recebimento de R$ {form.cleaned_data["valor_recebido"]:.2f} registrado. '
            f'Saldo restante: R$ {cr.saldo:.2f}.'
        )
        return redirect('/financeiro/contas-receber/')

    return render(request, 'financeiro/registrar_recebimento.html', {
        'form': form,
        'cr':   cr,
    })


@login_required(login_url='login')
def cancelar_conta_receber(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    if request.method == 'POST':
        cr = get_object_or_404(ContaReceber, pk=pk, loja__id_empresa__in=lojas_ids)
        if cr.status not in ('RECEBIDO', 'CANCELADO'):
            cr.status = 'CANCELADO'
            cr.save(update_fields=['status'])
            messages.success(request, f'Título "{cr.descricao}" cancelado.')
        else:
            messages.warning(request, 'Não é possível cancelar este título.')
    return redirect('/financeiro/contas-receber/')


# ==========================================
# CONTAS A PAGAR
# ==========================================

@login_required(login_url='login')
def contas_pagar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.GET.get('loja')
    status_filtro = request.GET.get('status', '')
    origem_filtro = request.GET.get('origem', '')
    loja = None
    titulos = []
    totais = {}

    if loja_id:
        loja = get_object_or_404(Empresa, pk=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        qs = ContaPagar.objects.filter(loja=loja).order_by('data_vencimento')
        totais = _totais_pagar(qs)

        if status_filtro:
            qs = qs.filter(status=status_filtro)
        if origem_filtro:
            qs = qs.filter(origem=origem_filtro)
        titulos = qs

    return render(request, 'financeiro/contas_pagar.html', {
        'lojas':          lojas,
        'loja':           loja,
        'titulos':        titulos,
        'totais':         totais,
        'status_filtro':  status_filtro,
        'origem_filtro':  origem_filtro,
        'status_choices': ContaPagar.STATUS_CHOICES,
        'origem_choices': ContaPagar.ORIGEM_CHOICES,
        'hoje':           datetime.date.today(),
    })


@login_required(login_url='login')
def conta_pagar_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids) if loja_id else None
    form = ContaPagarForm(request.POST or None, loja=loja)
    if request.method == 'POST' and form.is_valid():
        cp = form.save()
        messages.success(request, f'Título "{cp.descricao}" criado.')
        return redirect('/financeiro/contas-pagar/')
    return render(request, 'financeiro/conta_pagar_form.html', {
        'form':   form,
        'loja':   loja,
        'titulo': 'Nova Conta a Pagar',
        'acao':   'Criar título',
    })


@login_required(login_url='login')
def conta_pagar_editar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    cp = get_object_or_404(ContaPagar, pk=pk, loja__id_empresa__in=lojas_ids)
    form = ContaPagarForm(request.POST or None, instance=cp, loja=cp.loja)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{cp.descricao}" atualizado.')
        return redirect('/financeiro/contas-pagar/')
    return render(request, 'financeiro/conta_pagar_form.html', {
        'form':   form,
        'cp':     cp,
        'loja':   cp.loja,
        'titulo': f'Editar — {cp.descricao}',
        'acao':   'Salvar alterações',
    })


@login_required(login_url='login')
def registrar_pagamento(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    cp = get_object_or_404(ContaPagar, pk=pk, loja__id_empresa__in=lojas_ids)

    if cp.status == 'PAGO':
        messages.warning(request, 'Este título já foi totalmente pago.')
        return redirect('/financeiro/contas-pagar/')

    if cp.status == 'CANCELADO':
        messages.error(request, 'Título cancelado não pode ser baixado.')
        return redirect('/financeiro/contas-pagar/')

    form = RegistrarPagamentoForm(request.POST or None, saldo_restante=cp.saldo)

    if request.method == 'POST' and form.is_valid():
        cp.valor_pago += form.cleaned_data['valor_pago']
        cp.data_pagamento = form.cleaned_data['data_pagamento']
        obs = form.cleaned_data.get('observacoes', '').strip()
        if obs:
            cp.observacoes = (cp.observacoes + '\n' + obs).strip() if cp.observacoes else obs
        cp.save()
        messages.success(
            request,
            f'Pagamento de R$ {form.cleaned_data["valor_pago"]:.2f} registrado. '
            f'Saldo restante: R$ {cp.saldo:.2f}.'
        )
        return redirect('/financeiro/contas-pagar/')

    return render(request, 'financeiro/registrar_pagamento.html', {
        'form': form,
        'cp':   cp,
    })


@login_required(login_url='login')
def cancelar_conta_pagar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    if request.method == 'POST':
        cp = get_object_or_404(ContaPagar, pk=pk, loja__id_empresa__in=lojas_ids)
        if cp.status not in ('PAGO', 'CANCELADO'):
            cp.status = 'CANCELADO'
            cp.save(update_fields=['status'])
            messages.success(request, f'Título "{cp.descricao}" cancelado.')
        else:
            messages.warning(request, 'Não é possível cancelar este título.')
    return redirect('/financeiro/contas-pagar/')
