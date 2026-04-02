from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.exceptions import ValidationError

import json
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal

from .models import (
    ContaSintetica, ContaAnalitica,
    TipoEvento, RegraContabil, PartidaRegra,
    PeriodoContabil, EventoOperacional,
    LancamentoContabil, PartidaLancamento,
    ModeloRelatorio, TemplateplanoConta, ContaTemplate, TipoConta,
    TemplateEventoRegra, EventoTemplate, RegraTemplate, PartidaRegraTemplate,
)
from .forms import (
    ContaSinteticaForm, ContaAnaliticaForm,
    TipoEventoForm, RegraContabilForm, PeriodoContabilForm,
    LancamentoContabilForm, PartidaRegraInlineFormSet,
)
from core.models import Empresa


# ==========================================
# PLANO DE CONTAS
# ==========================================

def _calcular_profundidade_arvore(conta, cache_profundidade=None):
    """
    Calcula a profundidade real de uma conta na árvore (contando ancestrais).
    Isso garante que a indentação visual corresponde à hierarquia real.
    """
    if cache_profundidade is None:
        cache_profundidade = {}

    if conta.pk in cache_profundidade:
        return cache_profundidade[conta.pk]

    if conta.conta_pai is None:
        profundidade = 0
    else:
        profundidade = 1 + _calcular_profundidade_arvore(conta.conta_pai, cache_profundidade)

    cache_profundidade[conta.pk] = profundidade
    return profundidade


@login_required(login_url='login')
def plano_contas(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')
    loja_id = request.session.get('loja_id')
    sintetica_id = request.GET.get('sintetica')

    loja = None
    arvore = []
    sintetica_selecionada = None
    contas_analiticas = []

    if loja_id:
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        arvore_qs = ContaSintetica.objects.filter(
            loja=loja
        ).order_by('codigo_classificacao')

        # Adicionar profundidade real da árvore para cada conta
        # Isso garante indentação visual correta
        cache_profundidade = {}
        arvore = []
        for conta in arvore_qs:
            profundidade_real = _calcular_profundidade_arvore(conta, cache_profundidade)
            conta.profundidade_arvore = profundidade_real
            arvore.append(conta)

        if sintetica_id:
            sintetica_selecionada = get_object_or_404(
                ContaSintetica, pk=sintetica_id, loja=loja
            )
            contas_analiticas = ContaAnalitica.objects.filter(
                conta_sintetica=sintetica_selecionada
            ).order_by('codigo_classificacao')

    return render(request, 'contabilidade/plano_contas.html', {
        'lojas':                 lojas,
        'loja':                  loja,
        'arvore':                arvore,
        'sintetica_selecionada': sintetica_selecionada,
        'contas_analiticas':     contas_analiticas,
    })


@login_required(login_url='login')
def importar_plano_contas(request):
    """
    View para importar plano de contas da Empresa Modelo.

    Importa automaticamente para a loja selecionada na sessao.
    """
    # Obtem a loja selecionada na sessao
    loja_id = request.session.get('loja_id')

    # Valida se loja foi selecionada
    if not loja_id:
        messages.error(request, 'Selecione uma loja primeiro.')
        return redirect('plano_contas')

    # Valida acesso do usuario a loja
    lojas_user = request.user.perfil.get_lojas()
    loja = get_object_or_404(
        Empresa,
        id_empresa=loja_id,
        id_empresa__in=lojas_user.values_list('id_empresa', flat=True)
    )

    # Nao permite importar para Empresa Modelo
    if loja.id_empresa == 4:
        messages.error(request, 'Nao pode importar para a Empresa Modelo!')
        return redirect('plano_contas')

    # GET: Mostra pagina de confirmacao
    if request.method == 'GET':
        # Verifica se loja ja tem plano
        contas_existentes = ContaSintetica.objects.filter(loja=loja).count()

        return render(request, 'contabilidade/importar_plano_contas.html', {
            'loja': loja,
            'contas_existentes': contas_existentes,
        })

    # POST: Executa importacao
    elif request.method == 'POST':
        try:
            # Busca Empresa Modelo
            empresa_modelo = Empresa.objects.get(id_empresa=4)

            # Valida que modelo tem contas
            contas_modelo = ContaSintetica.objects.filter(
                loja=empresa_modelo,
                eh_modelo=True
            )
            if not contas_modelo.exists():
                raise ValueError('Empresa Modelo nao tem contas para importar!')

            # Deleta contas existentes (se houver)
            contas_existentes = ContaSintetica.objects.filter(loja=loja)
            if contas_existentes.exists():
                contas_existentes.delete()

            # =========== IMPORTAR CONTAS SINTETICAS ===========
            mapa_contas = {}
            criadas_sinteticas = 0

            for conta_modelo in contas_modelo.order_by('codigo_classificacao'):
                # Busca conta pai na nova loja (se houver)
                conta_pai = None
                if conta_modelo.conta_pai:
                    conta_pai_id = mapa_contas.get(conta_modelo.conta_pai.id)
                    if conta_pai_id:
                        conta_pai = ContaSintetica.objects.get(id=conta_pai_id)

                # Cria conta na nova loja
                nova_conta = ContaSintetica.objects.create(
                    loja=loja,
                    codigo_classificacao=conta_modelo.codigo_classificacao,
                    nome=conta_modelo.nome,
                    tipo_conta=conta_modelo.tipo_conta,
                    nivel=conta_modelo.nivel,
                    conta_pai=conta_pai,
                    eh_modelo=False,
                )

                mapa_contas[conta_modelo.id] = nova_conta.id
                criadas_sinteticas += 1

            # =========== IMPORTAR CONTAS ANALITICAS ===========
            contas_analiticas_modelo = ContaAnalitica.objects.filter(
                loja=empresa_modelo,
                eh_modelo=True
            )

            criadas_analiticas = 0

            for ca_modelo in contas_analiticas_modelo:
                # Busca conta sintetica correspondente na nova loja
                try:
                    nova_conta_sintetica = ContaSintetica.objects.get(
                        loja=loja,
                        codigo_classificacao=ca_modelo.conta_sintetica.codigo_classificacao
                    )
                except ContaSintetica.DoesNotExist:
                    continue

                # Cria conta analitica na nova loja
                ContaAnalitica.objects.create(
                    loja=loja,
                    codigo_reduzido=ca_modelo.codigo_reduzido,
                    codigo_classificacao=ca_modelo.codigo_classificacao,
                    nome=ca_modelo.nome,
                    natureza_saldo=ca_modelo.natureza_saldo,
                    aceita_lancamento=ca_modelo.aceita_lancamento,
                    conta_sintetica=nova_conta_sintetica,
                    eh_modelo=False,
                )
                criadas_analiticas += 1

            # Sucesso!
            messages.success(
                request,
                f'Plano de contas importado com sucesso! '
                f'{criadas_sinteticas} contas sinteticas e {criadas_analiticas} analiticas.'
            )
            return redirect('plano_contas')

        except Exception as e:
            messages.error(request, f'Erro ao importar: {str(e)}')
            return redirect('plano_contas')


@login_required(login_url='login')
def conta_sintetica_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    pai_id = request.GET.get('pai') or request.POST.get('conta_pai')

    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids) if loja_id else None
    pai = get_object_or_404(ContaSintetica, pk=pai_id, loja__id_empresa__in=lojas_ids) if pai_id else None

    form = ContaSinteticaForm(request.POST or None, loja=loja)

    # Pré-preencher campos automaticamente se há conta pai
    proximo_codigo = None
    if pai and not request.POST:
        # Se pai está no nível 4, não pode criar subconta sintética (apenas analítica)
        if pai.nivel >= 4:
            messages.error(request,
                f'Contas sintéticas só vão até nível 4. '
                f'Para criar nível 5, use "Nova Analítica" a partir de uma conta nível 4.'
            )
            return redirect('/contabilidade/plano-contas/')

        # Buscar filhas do pai para sugerir o próximo número
        filhas = ContaSintetica.objects.filter(
            loja=loja, conta_pai=pai
        ).order_by('-codigo_classificacao')

        proximo_nivel = pai.nivel + 1

        if filhas.exists():
            ultima = filhas.first().codigo_classificacao
            partes = ultima.split('.')
            try:
                ultimo_num = int(partes[-1])
                proximo_num = ultimo_num + 1

                # Se vai ser nível 4 (próximo), usar zero-padding de 2 dígitos
                if proximo_nivel == 4:
                    partes[-1] = f"{proximo_num:02d}"
                else:
                    partes[-1] = str(proximo_num)

                proximo_codigo = '.'.join(partes)
            except (ValueError, IndexError):
                proximo_codigo = None
        else:
            # Nenhuma filha, sugerir primeira filha
            if proximo_nivel == 4:
                # Nível 4 usa zero-padding de 2 dígitos
                proximo_codigo = f"{pai.codigo_classificacao}.01"
            else:
                proximo_codigo = f"{pai.codigo_classificacao}.1"

        # PRÉ-PREENCHER TODOS OS CAMPOS AUTOMATICAMENTE
        form.initial['conta_pai'] = pai
        form.initial['codigo_classificacao'] = proximo_codigo
        form.initial['tipo_conta'] = pai.tipo_conta.codigo  # Herdar tipo do pai
        form.initial['nivel'] = proximo_nivel  # Nível é pai + 1

        # DESABILITAR CAMPOS QUE NÃO PRECISAM SER EDITADOS (usando readonly para preservar no POST)
        # Campos readonly são enviados no formulário, diferente de disabled
        form.fields['codigo_classificacao'].widget.attrs['readonly'] = True
        form.fields['codigo_classificacao'].widget.attrs.setdefault('class', '')
        form.fields['codigo_classificacao'].widget.attrs['class'] += ' readonly'

        form.fields['nivel'].widget.attrs['readonly'] = True
        form.fields['nivel'].widget.attrs.setdefault('class', '')
        form.fields['nivel'].widget.attrs['class'] += ' readonly'

        # Para conta_pai e tipo_conta (select), usar disabled + hidden input com valor
        form.fields['conta_pai'].widget.attrs['disabled'] = True
        form.fields['tipo_conta'].widget.attrs['disabled'] = True

    if request.method == 'POST' and form.is_valid():
        try:
            form.save()
            messages.success(request, 'Conta sintética criada com sucesso!')
            return redirect('/contabilidade/plano-contas/')
        except Exception as e:
            # Se houver erro, mostrar mensagem amigável
            if 'unique constraint' in str(e).lower() or 'codigo_classificacao' in str(e):
                messages.error(request, f'Erro: Este código ({form.cleaned_data.get("codigo_classificacao")}) já existe nesta loja. Use outro código.')
            else:
                messages.error(request, f'Erro ao criar conta: {str(e)}')

    return render(request, 'contabilidade/conta_sintetica_form.html', {
        'form':             form,
        'loja':             loja,
        'pai':              pai,
        'proximo_codigo':   proximo_codigo,
        'titulo':           'Nova Conta Sintética',
        'acao':             'Criar conta',
    })


@login_required(login_url='login')
def conta_sintetica_editar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    conta = get_object_or_404(ContaSintetica, pk=pk, loja__id_empresa__in=lojas_ids)
    form = ContaSinteticaForm(request.POST or None, instance=conta, loja=conta.loja)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{conta.nome}" atualizada.')
        return redirect('/contabilidade/plano-contas/')
    return render(request, 'contabilidade/conta_sintetica_form.html', {
        'form':   form,
        'conta':  conta,
        'loja':   conta.loja,
        'titulo': f'Editar — {conta.codigo_classificacao} {conta.nome}',
        'acao':   'Salvar alterações',
    })


@login_required(login_url='login')
def conta_analitica_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id   = request.session.get('loja_id')
    sint_id   = request.GET.get('sintetica') or request.POST.get('conta_sintetica')
    loja      = get_object_or_404(Empresa, pk=loja_id, id_empresa__in=lojas_ids) if loja_id else None
    sintetica = get_object_or_404(ContaSintetica, pk=sint_id, loja__id_empresa__in=lojas_ids) if sint_id else None

    # Validar que sintética é nível 4
    if sintetica and sintetica.nivel != 4:
        messages.error(request,
            f'Contas analíticas só podem ser criadas a partir de contas sintéticas nível 4. '
            f'A conta selecionada é nível {sintetica.nivel}.'
        )
        return redirect(f'/contabilidade/plano-contas/')

    form = ContaAnaliticaForm(request.POST or None, loja=loja, sintetica=sintetica)

    # Pré-calcular próximo código analítico
    proximo_codigo_analitico = None
    if sintetica and not request.POST:
        filhas = ContaAnalitica.objects.filter(
            loja=loja, conta_sintetica=sintetica
        ).order_by('-codigo_classificacao')

        if filhas.exists():
            ultima = filhas.first().codigo_classificacao
            partes = ultima.split('.')
            try:
                ultimo_num = int(partes[-1])
                proximo_num = ultimo_num + 1
                partes[-1] = f"{proximo_num:04d}"
                proximo_codigo_analitico = '.'.join(partes)
            except (ValueError, IndexError):
                proximo_codigo_analitico = None
        else:
            # Primeira analítica desta sintética
            proximo_codigo_analitico = f"{sintetica.codigo_classificacao}.0001"

        # Pré-preencher campos
        form.initial['codigo_classificacao'] = proximo_codigo_analitico
        form.fields['codigo_classificacao'].widget.attrs['readonly'] = True
        form.fields['codigo_classificacao'].widget.attrs.setdefault('class', '')
        form.fields['codigo_classificacao'].widget.attrs['class'] += ' readonly'

    if request.method == 'POST' and form.is_valid():
        # Extrair código reduzido dos últimos 4 dígitos do código de classificação
        conta = form.instance
        if conta.codigo_classificacao:
            # Pega os últimos 4 dígitos (formato analítico: X.X.X.XX.YYYY)
            ultimos_digitos = conta.codigo_classificacao.split('.')[-1]
            try:
                codigo_reduzido = int(ultimos_digitos)
                conta.codigo_reduzido = codigo_reduzido

                # Validar unicidade do código reduzido APENAS DENTRO DA MESMA SINTÉTICA
                # Diferentes sintéticas podem ter mesmo código reduzido (ex: 1.1.1.2.0001 e 5.1.1.4.0001)
                existe = ContaAnalitica.objects.filter(
                    loja=loja,
                    conta_sintetica=conta.conta_sintetica,
                    codigo_reduzido=codigo_reduzido
                )
                if conta.pk:
                    existe = existe.exclude(pk=conta.pk)

                if existe.exists():
                    messages.error(request,
                        f'Código reduzido "{codigo_reduzido}" já existe para a sintética '
                        f'{conta.conta_sintetica.codigo_classificacao}. '
                        f'Use outro número nos últimos 4 dígitos.'
                    )
                    return render(request, 'contabilidade/conta_analitica_form.html', {
                        'form':      form,
                        'loja':      loja,
                        'sintetica': sintetica,
                        'proximo_codigo_analitico': None,
                        'titulo':    'Nova Conta Analítica',
                        'acao':      'Criar conta',
                    })

            except ValueError:
                messages.error(request, 'Erro ao extrair código reduzido dos últimos 4 dígitos.')
                return render(request, 'contabilidade/conta_analitica_form.html', {
                    'form':      form,
                    'loja':      loja,
                    'sintetica': sintetica,
                    'proximo_codigo_analitico': None,
                    'titulo':    'Nova Conta Analítica',
                    'acao':      'Criar conta',
                })

        form.save()
        messages.success(request, 'Conta analítica criada.')
        url = f'/contabilidade/plano-contas/&sintetica={sint_id}'
        return redirect(url)
    return render(request, 'contabilidade/conta_analitica_form.html', {
        'form':      form,
        'loja':      loja,
        'sintetica': sintetica,
        'proximo_codigo_analitico': proximo_codigo_analitico,
        'titulo':    'Nova Conta Analítica',
        'acao':      'Criar conta',
    })


@login_required(login_url='login')
def conta_analitica_editar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    conta = get_object_or_404(ContaAnalitica, pk=pk, loja__id_empresa__in=lojas_ids)
    form = ContaAnaliticaForm(request.POST or None, instance=conta, loja=conta.loja)
    if request.method == 'POST' and form.is_valid():
        # Em edição, validar se o código reduzido é único (pode ter mudado o código)
        conta_atualizada = form.instance
        if conta_atualizada.codigo_classificacao:
            ultimos_digitos = conta_atualizada.codigo_classificacao.split('.')[-1]
            try:
                codigo_reduzido = int(ultimos_digitos)
                # Validar unicidade APENAS DENTRO DA MESMA SINTÉTICA
                existe = ContaAnalitica.objects.filter(
                    loja=conta_atualizada.loja,
                    conta_sintetica=conta_atualizada.conta_sintetica,
                    codigo_reduzido=codigo_reduzido
                ).exclude(pk=conta_atualizada.pk)

                if existe.exists():
                    messages.error(request,
                        f'Código reduzido "{codigo_reduzido}" já existe para a sintética '
                        f'{conta_atualizada.conta_sintetica.codigo_classificacao}. '
                        f'Use outro número nos últimos 4 dígitos.'
                    )
                    return render(request, 'contabilidade/conta_analitica_form.html', {
                        'form':      form,
                        'conta':     conta,
                        'loja':      conta.loja,
                        'sintetica': conta.conta_sintetica,
                        'titulo':    f'Editar — {conta.codigo_reduzido} {conta.nome}',
                        'acao':      'Salvar alterações',
                    })
                conta_atualizada.codigo_reduzido = codigo_reduzido
            except ValueError:
                pass

        form.save()
        messages.success(request, f'"{conta.nome}" atualizada.')
        return redirect(
            f'/contabilidade/plano-contas/'
            f'&sintetica={conta.conta_sintetica_id}'
        )
    return render(request, 'contabilidade/conta_analitica_form.html', {
        'form':      form,
        'conta':     conta,
        'loja':      conta.loja,
        'sintetica': conta.conta_sintetica,
        'titulo':    f'Editar — {conta.codigo_reduzido} {conta.nome}',
        'acao':      'Salvar alterações',
    })


# ==========================================
# TIPOS DE EVENTO
# ==========================================

@login_required(login_url='login')
def tipos_evento(request):
    eventos = TipoEvento.objects.all().order_by('modulo_origem', 'codigo')
    return render(request, 'contabilidade/tipos_evento.html', {
        'eventos': eventos,
    })


@login_required(login_url='login')
def tipo_evento_criar(request):
    form = TipoEventoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de evento criado.')
        return redirect('tipos_evento')
    return render(request, 'contabilidade/tipo_evento_form.html', {
        'form':   form,
        'titulo': 'Novo Tipo de Evento',
        'acao':   'Criar',
    })


@login_required(login_url='login')
def tipo_evento_editar(request, pk):
    evento = get_object_or_404(TipoEvento, pk=pk)
    form = TipoEventoForm(request.POST or None, instance=evento)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{evento.codigo}" atualizado.')
        return redirect('tipos_evento')
    return render(request, 'contabilidade/tipo_evento_form.html', {
        'form':   form,
        'evento': evento,
        'titulo': f'Editar — {evento.codigo}',
        'acao':   'Salvar',
    })


@login_required(login_url='login')
def tipo_evento_toggle(request, pk):
    if request.method == 'POST':
        evento = get_object_or_404(TipoEvento, pk=pk)
        evento.ativo = not evento.ativo
        evento.save(update_fields=['ativo'])
        status = 'ativado' if evento.ativo else 'desativado'
        messages.success(request, f'"{evento.codigo}" {status}.')
    return redirect('tipos_evento')


# ==========================================
# REGRAS CONTÁBEIS
# ==========================================

@login_required(login_url='login')
def regras_contabeis(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.session.get('loja_id')
    loja = None
    regras = []

    if loja_id:
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        regras = (
            RegraContabil.objects
            .filter(loja=loja)
            .select_related('tipo_evento')
            .prefetch_related('partidas')
            .order_by('tipo_evento__codigo')
        )

    return render(request, 'contabilidade/regras_contabeis.html', {
        'lojas':  lojas,
        'loja':   loja,
        'regras': regras,
    })


@login_required(login_url='login')
@login_required(login_url='login')
def regra_contabil_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids) if loja_id else None

    if request.method == 'POST':
        form = RegraContabilForm(request.POST, loja=loja)
        formset = PartidaRegraInlineFormSet(request.POST, instance=None, loja=loja)

        if form.is_valid() and formset.is_valid():
            # Salvar regra primeiro
            regra = form.save()
            # Vincular partidas à regra
            formset.instance = regra
            formset.save()
            messages.success(request, 'Regra contábil criada com sucesso.')
            return redirect(f'/contabilidade/regras/')
    else:
        form = RegraContabilForm(loja=loja)
        formset = PartidaRegraInlineFormSet(instance=None, loja=loja)

    return render(request, 'contabilidade/regra_contabil_form.html', {
        'form':    form,
        'formset': formset,
        'loja':    loja,
        'titulo':  'Nova Regra Contábil',
        'acao':    'Criar regra',
    })


@login_required(login_url='login')
def regra_contabil_editar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    regra = get_object_or_404(RegraContabil, pk=pk, loja__id_empresa__in=lojas_ids)

    if request.method == 'POST':
        form = RegraContabilForm(request.POST, instance=regra, loja=regra.loja)
        formset = PartidaRegraInlineFormSet(request.POST, instance=regra, loja=regra.loja)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Regra atualizada com sucesso.')
            return redirect(f'/contabilidade/regras/')
    else:
        form = RegraContabilForm(instance=regra, loja=regra.loja)
        formset = PartidaRegraInlineFormSet(instance=regra, loja=regra.loja)

    return render(request, 'contabilidade/regra_contabil_form.html', {
        'form':    form,
        'formset': formset,
        'regra':   regra,
        'loja':    regra.loja,
        'titulo':  f'Editar Regra — {regra.tipo_evento.codigo}',
        'acao':    'Salvar alterações',
    })


@login_required(login_url='login')
def regra_contabil_toggle(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    if request.method == 'POST':
        regra = get_object_or_404(RegraContabil, pk=pk, loja__id_empresa__in=lojas_ids)
        regra.ativa = not regra.ativa
        regra.save(update_fields=['ativa'])
        status = 'ativada' if regra.ativa else 'desativada'
        messages.success(request, f'Regra {status}.')
    return redirect(f'/contabilidade/regras/')


# ==========================================
# PERÍODOS CONTÁBEIS
# ==========================================

@login_required(login_url='login')
def periodos_contabeis(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.session.get('loja_id')
    loja = None
    periodos = []

    if loja_id:
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        periodos = PeriodoContabil.objects.filter(loja=loja).order_by('-ano', '-mes')

    return render(request, 'contabilidade/periodos_contabeis.html', {
        'lojas':   lojas,
        'loja':    loja,
        'periodos': periodos,
    })


@login_required(login_url='login')
def periodo_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids) if loja_id else None
    form = PeriodoContabilForm(request.POST or None, loja=loja)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Período criado.')
        url = f'/contabilidade/periodos/' if loja_id else '/contabilidade/periodos/'
        return redirect(url)
    return render(request, 'contabilidade/periodo_form.html', {
        'form':   form,
        'loja':   loja,
        'titulo': 'Abrir Novo Período',
        'acao':   'Criar período',
    })


@login_required(login_url='login')
def periodo_fechar(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    if request.method == 'POST':
        periodo = get_object_or_404(PeriodoContabil, pk=pk, loja__id_empresa__in=lojas_ids)
        if periodo.status == 'ABERTO' or periodo.status == 'REABERTO':
            periodo.status = 'FECHADO'
            periodo.data_fechamento = timezone.now()
            periodo.fechado_por = request.user
            periodo.save(update_fields=['status', 'data_fechamento', 'fechado_por'])
            messages.success(request, f'Período {periodo.mes:02d}/{periodo.ano} fechado.')
        else:
            messages.warning(request, 'Período já está fechado.')
    return redirect(f'/contabilidade/periodos/')


@login_required(login_url='login')
def periodo_reabrir(request, pk):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    if request.method == 'POST':
        periodo = get_object_or_404(PeriodoContabil, pk=pk, loja__id_empresa__in=lojas_ids)
        motivo = request.POST.get('motivo', '').strip()
        if periodo.status == 'FECHADO':
            periodo.status = 'REABERTO'
            periodo.data_reabertura = timezone.now()
            periodo.reaberto_por = request.user
            periodo.motivo_reabertura = motivo
            periodo.save(update_fields=[
                'status', 'data_reabertura', 'reaberto_por', 'motivo_reabertura'
            ])
            messages.success(request, f'Período {periodo.mes:02d}/{periodo.ano} reaberto.')
        else:
            messages.warning(request, 'Apenas períodos fechados podem ser reabertos.')
    return redirect(f'/contabilidade/periodos/')


# ==========================================
# EVENTOS OPERACIONAIS (leitura)
# ==========================================

@login_required(login_url='login')
def eventos_operacionais(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.session.get('loja_id')
    status_filtro = request.GET.get('status', '')
    loja = None
    eventos = []

    if loja_id:
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        qs = EventoOperacional.objects.filter(loja=loja).select_related('tipo_evento')
        if status_filtro:
            qs = qs.filter(status=status_filtro)
        eventos = qs.order_by('-data_evento')[:200]

    return render(request, 'contabilidade/eventos_operacionais.html', {
        'lojas':         lojas,
        'loja':          loja,
        'eventos':       eventos,
        'status_filtro': status_filtro,
        'status_choices': EventoOperacional.STATUS_CHOICES,
    })


# ==========================================
# LANÇAMENTOS CONTÁBEIS
# ==========================================

@login_required(login_url='login')
def lancamentos(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.session.get('loja_id')
    periodo_id = request.GET.get('periodo')
    tipo_filtro = request.GET.get('tipo', '')
    loja = None
    periodos = []
    periodo_sel = None
    lancamentos_qs = []

    if loja_id:
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        periodos = PeriodoContabil.objects.filter(loja=loja).order_by('-ano', '-mes')

        if periodo_id:
            periodo_sel = get_object_or_404(PeriodoContabil, pk=periodo_id, loja=loja)
            qs = (
                LancamentoContabil.objects
                .filter(loja=loja, periodo=periodo_sel)
                .select_related('usuario', 'evento__tipo_evento')
                .prefetch_related('partidas__conta')
            )
            if tipo_filtro:
                qs = qs.filter(tipo=tipo_filtro)
            lancamentos_qs = qs.order_by('-data_lancamento', '-numero')

            # Calcular valor total de cada lançamento (soma dos débitos)
            for lancamento in lancamentos_qs:
                total = lancamento.partidas.filter(tipo='D').aggregate(total=Sum('valor'))['total'] or Decimal('0')
                lancamento.valor_total = total

    return render(request, 'contabilidade/lancamentos.html', {
        'lojas':        lojas,
        'loja':         loja,
        'periodos':     periodos,
        'periodo_sel':  periodo_sel,
        'lancamentos':  lancamentos_qs,
        'tipo_filtro':  tipo_filtro,
        'tipo_choices': LancamentoContabil.TIPO_CHOICES,
    })


@login_required(login_url='login')
def lancamento_criar(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids) if loja_id else None

    # Contas analíticas da loja para o select das partidas
    contas = []
    if loja:
        contas = list(
            ContaAnalitica.objects
            .filter(loja=loja, aceita_lancamento=True)
            .order_by('codigo_classificacao')
            .values('id', 'codigo_reduzido', 'codigo_classificacao', 'nome', 'centro_custo')
        )

    # Pré-preenchimento para estorno
    ref_id = request.GET.get('ref')
    lanc_ref = None
    partidas_iniciais = []
    if ref_id and loja:
        lanc_ref = LancamentoContabil.objects.filter(pk=ref_id, loja=loja).first()
        if lanc_ref:
            # Inverte D↔C para o estorno
            for p in lanc_ref.partidas.select_related('conta').all():
                partidas_iniciais.append({
                    'conta_id': p.conta_id,
                    'tipo': 'C' if p.tipo == 'D' else 'D',
                    'valor': str(p.valor),
                    'historico': f'Estorno: {p.historico_complementar or lanc_ref.historico}',
                    'centro_custo': p.centro_custo,
                })

    initial = {}
    if lanc_ref:
        initial['tipo'] = 'ESTORNO'
        initial['historico'] = f'Estorno do lançamento #{lanc_ref.numero} — {lanc_ref.historico}'
        initial['lancamento_referencia'] = lanc_ref.pk

    form = LancamentoContabilForm(request.POST or None, loja=loja, initial=initial)

    if request.method == 'POST' and form.is_valid():
        # Coleta as partidas do POST
        contas_ids  = request.POST.getlist('partida_conta')
        tipos_dc    = request.POST.getlist('partida_tipo')
        valores     = request.POST.getlist('partida_valor')
        historicos  = request.POST.getlist('partida_historico')
        centros     = request.POST.getlist('partida_centro_custo')

        # Valida: mínimo 2 partidas
        partidas_data = []
        erros = []
        for i, (cid, tdc, val, hist, cc) in enumerate(
                zip(contas_ids, tipos_dc, valores, historicos, centros), start=1):
            if not cid or not tdc or not val:
                continue
            try:
                v = Decimal(val.replace(',', '.'))
                if v <= 0:
                    raise ValueError
            except (ValueError, Exception):
                erros.append(f'Partida {i}: valor inválido.')
                continue
            partidas_data.append({
                'conta_id': int(cid),
                'tipo': tdc,
                'valor': v,
                'historico_complementar': hist,
                'centro_custo': cc,
            })

        if len(partidas_data) < 2:
            erros.append('O lançamento precisa de no mínimo 2 partidas.')

        total_d = sum(p['valor'] for p in partidas_data if p['tipo'] == 'D')
        total_c = sum(p['valor'] for p in partidas_data if p['tipo'] == 'C')
        if not erros and total_d != total_c:
            erros.append(
                f'Débitos (R$ {total_d:.2f}) ≠ Créditos (R$ {total_c:.2f}). '
                'O lançamento deve ser equilibrado.'
            )

        if erros:
            for e in erros:
                messages.error(request, e)
        else:
            with transaction.atomic():
                # Próximo número da loja
                ultimo = (
                    LancamentoContabil.objects
                    .filter(loja=loja)
                    .order_by('-numero')
                    .values_list('numero', flat=True)
                    .first()
                ) or 0

                # Determina o período contábil pela data informada
                data_lanc = form.cleaned_data['data_lancamento']
                periodo = PeriodoContabil.objects.filter(
                    loja=loja, ano=data_lanc.year, mes=data_lanc.month,
                    status__in=['ABERTO', 'REABERTO']
                ).first()
                if not periodo:
                    messages.error(
                        request,
                        f'Não existe período contábil aberto para '
                        f'{data_lanc.month:02d}/{data_lanc.year}.'
                    )
                else:
                    lanc = form.save(commit=False)
                    lanc.numero = ultimo + 1
                    lanc.usuario = request.user
                    lanc.periodo = periodo
                    lanc.save()

                    for p in partidas_data:
                        PartidaLancamento.objects.create(
                            lancamento=lanc,
                            conta_id=p['conta_id'],
                            tipo=p['tipo'],
                            valor=p['valor'],
                            historico_complementar=p['historico_complementar'],
                            centro_custo=p['centro_custo'],
                        )

                    messages.success(
                        request,
                        f'Lançamento #{lanc.numero} criado com {len(partidas_data)} partidas.'
                    )
                    return redirect(
                        f'/contabilidade/lancamentos/'
                        f'&periodo={periodo.pk}'
                    )

    titulo = f'Estorno — Lanç. #{lanc_ref.numero}' if lanc_ref else 'Novo Lançamento Manual'
    return render(request, 'contabilidade/lancamento_form.html', {
        'form':             form,
        'loja':             loja,
        'contas':           contas,
        'contas_json':      json.dumps(contas),
        'partidas_iniciais': json.dumps(partidas_iniciais),
        'titulo':           titulo,
        'acao':             'Registrar Lançamento',
    })


@login_required(login_url='login')
def lancamento_detalhe(request, pk):
    lanc = get_object_or_404(
        LancamentoContabil.objects
        .select_related('loja', 'usuario', 'periodo', 'evento__tipo_evento', 'lancamento_referencia')
        .prefetch_related('partidas__conta'),
        pk=pk
    )
    total_d = lanc.partidas.filter(tipo='D').aggregate(s=Sum('valor'))['s'] or Decimal('0')
    total_c = lanc.partidas.filter(tipo='C').aggregate(s=Sum('valor'))['s'] or Decimal('0')
    return render(request, 'contabilidade/lancamento_detalhe.html', {
        'lanc':    lanc,
        'total_d': total_d,
        'total_c': total_c,
    })


# ==========================================
# RELATÓRIOS CONTÁBEIS (DRE / DFC)
# ==========================================

def _calcular_saldo_estrutura(estrutura, periodos_ids):
    """
    Retorna o saldo líquido de uma estrutura com tipo_calculo=1
    (vinculada a contas analíticas) para um conjunto de períodos.
    Débitos aumentam contas de Ativo/Despesa, Créditos aumentam Passivo/Receita.
    A operação (4=+, 5=-, 6==, 7=+/-) determina o sinal na linha do relatório.
    """
    contas_ids = list(
        estrutura.composicoes.values_list('conta_analitica_id', flat=True)
    )
    if not contas_ids:
        return Decimal('0')

    from django.db.models import Sum as _Sum
    partidas = PartidaLancamento.objects.filter(
        lancamento__periodo_id__in=periodos_ids,
        conta_id__in=contas_ids,
    )
    total_d = partidas.filter(tipo='D').aggregate(s=_Sum('valor'))['s'] or Decimal('0')
    total_c = partidas.filter(tipo='C').aggregate(s=_Sum('valor'))['s'] or Decimal('0')

    # Saldo bruto = D - C (positivo = devedor, negativo = credor)
    saldo = total_d - total_c

    # Aplica operação do modelo
    if estrutura.operacao == 5:   # Negativo
        return -saldo
    return saldo                  # Positivo, Igual, (+/-)


@login_required(login_url='login')
def relatorios_contabeis(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas = request.user.perfil.get_lojas().order_by('descricao')

    loja_id = request.session.get('loja_id')
    modelo_id = request.GET.get('modelo')
    ano = request.GET.get('ano', '')
    mes_ini = request.GET.get('mes_ini', '')
    mes_fim = request.GET.get('mes_fim', '')

    loja = None
    modelos = []
    modelo_sel = None
    linhas = []
    total_resultado = Decimal('0')
    periodos_selecionados = []
    erro = None

    if loja_id:
        loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True))
        modelos = ModeloRelatorio.objects.filter(loja=loja, ativo=True).order_by('tipo', 'descricao')

    if loja and modelo_id:
        modelo_sel = get_object_or_404(ModeloRelatorio, pk=modelo_id, loja=loja)

        # Filtra períodos pelo intervalo informado
        periodos_qs = PeriodoContabil.objects.filter(loja=loja)
        if ano:
            periodos_qs = periodos_qs.filter(ano=ano)
        if mes_ini:
            periodos_qs = periodos_qs.filter(mes__gte=mes_ini)
        if mes_fim:
            periodos_qs = periodos_qs.filter(mes__lte=mes_fim)
        periodos_selecionados = list(periodos_qs.values_list('id', flat=True))

        if not periodos_selecionados:
            erro = 'Nenhum período contábil encontrado para os filtros informados.'
        else:
            estruturas = (
                modelo_sel.estruturas
                .prefetch_related('composicoes__conta_analitica')
                .order_by('posicao')
            )

            # Mapa de saldos calculados por posição (para linhas sintéticas somarem filhas)
            saldos_por_posicao = {}

            for est in estruturas:
                if est.tipo_calculo == 1:
                    # Vinculada a contas analíticas — calcula direto
                    saldo = _calcular_saldo_estrutura(est, periodos_selecionados)
                elif est.tipo_calculo == 0:
                    # Sintética — soma todas as linhas filhas cujo posicao começa com esta posicao
                    saldo = sum(
                        v for pos, v in saldos_por_posicao.items()
                        if pos.startswith(est.posicao + '.') or pos == est.posicao
                    )
                elif est.tipo_calculo == 2:
                    # Resultado — soma de todas as filhas diretas até aqui
                    saldo = sum(saldos_por_posicao.values())
                else:
                    saldo = Decimal('0')

                saldos_por_posicao[est.posicao] = saldo
                nivel = est.posicao.count('.') + 1

                linhas.append({
                    'posicao':      est.posicao,
                    'descricao':    est.descricao,
                    'tipo_calculo': est.tipo_calculo,
                    'operacao':     est.operacao,
                    'saldo':        saldo,
                    'nivel':        nivel,
                    'is_resultado': est.tipo_calculo == 2,
                    'is_sintetica': est.tipo_calculo == 0,
                })

            # Resultado final = última linha de tipo Resultado (tipo_calculo=2)
            resultados = [l for l in linhas if l['is_resultado']]
            if resultados:
                total_resultado = resultados[-1]['saldo']

    anos_disponiveis = []
    if loja:
        anos_disponiveis = (
            PeriodoContabil.objects
            .filter(loja=loja)
            .values_list('ano', flat=True)
            .distinct()
            .order_by('-ano')
        )

    return render(request, 'contabilidade/relatorios_contabeis.html', {
        'lojas':                lojas,
        'loja':                 loja,
        'modelos':              modelos,
        'modelo_sel':           modelo_sel,
        'linhas':               linhas,
        'total_resultado':      total_resultado,
        'periodos_selecionados': periodos_selecionados,
        'anos_disponiveis':     anos_disponiveis,
        'ano':                  ano,
        'mes_ini':              mes_ini,
        'mes_fim':              mes_fim,
        'erro':                 erro,
        'meses': [
            (1,'Jan'),(2,'Fev'),(3,'Mar'),(4,'Abr'),
            (5,'Mai'),(6,'Jun'),(7,'Jul'),(8,'Ago'),
            (9,'Set'),(10,'Out'),(11,'Nov'),(12,'Dez'),
        ],
    })


# ==========================================
# TEMPLATES DE PLANO DE CONTAS
# ==========================================

@login_required(login_url='login')
def templates_plano_contas(request):
    """Lista templates disponíveis para importação."""
    templates = TemplateplanoConta.objects.filter(ativo=True).prefetch_related('contas')

    context = {
        'templates': templates,
        'titulo': 'Templates - Plano de Contas',
    }
    return render(request, 'contabilidade/templates_plano_contas.html', context)


@login_required(login_url='login')
def importar_template_plano(request, template_id):
    """Importa um template de plano de contas para a loja selecionada."""
    lojas = request.user.perfil.get_lojas().order_by('descricao')
    template = get_object_or_404(TemplateplanoConta, pk=template_id, ativo=True)

    if request.method == 'POST':
        loja_id = request.POST.get('loja_id')
        loja = get_object_or_404(
            Empresa, pk=loja_id, id_empresa__in=lojas.values_list('id_empresa', flat=True)
        )

        # Verificar se loja já tem contas
        contas_existentes = ContaSintetica.objects.filter(loja=loja).count()
        if contas_existentes > 0:
            messages.warning(
                request,
                f'A loja {loja.descricao} já possui {contas_existentes} contas. '
                'Primeiro exporte as contas existentes (se necessário) ou crie uma nova loja.'
            )
            return redirect('importar_template_plano', template_id=template_id)

        # Importar contas do template
        with transaction.atomic():
            contas_criadas_map = {}  # Mapear codigo_classificacao → ContaSintetica
            contas_importadas = 0

            for conta_template in template.contas.all().order_by('codigo_classificacao'):
                # Obter tipo_conta
                tipo_obj = TipoConta.objects.get(codigo=conta_template.tipo_conta)

                # Obter conta pai se existir
                pai = None
                if conta_template.pai_codigo:
                    if conta_template.pai_codigo in contas_criadas_map:
                        pai = contas_criadas_map[conta_template.pai_codigo]
                    else:
                        try:
                            pai = ContaSintetica.objects.get(
                                loja=loja,
                                codigo_classificacao=conta_template.pai_codigo
                            )
                        except ContaSintetica.DoesNotExist:
                            pass

                # Criar conta sintetica
                conta_obj = ContaSintetica.objects.create(
                    loja=loja,
                    codigo_classificacao=conta_template.codigo_classificacao,
                    nome=conta_template.nome,
                    tipo_conta=tipo_obj,
                    conta_pai=pai,
                    nivel=conta_template.nivel,
                )
                contas_criadas_map[conta_template.codigo_classificacao] = conta_obj
                contas_importadas += 1

        messages.success(
            request,
            f'Template "{template.nome}" importado com sucesso! '
            f'{contas_importadas} contas criadas para {loja.descricao}.'
        )
        return redirect('plano_contas')

    context = {
        'template': template,
        'lojas': lojas,
        'titulo': f'Importar Template - {template.nome}',
    }
    return render(request, 'contabilidade/importar_template_plano.html', context)


@login_required(login_url='login')
def templates_evento_regra(request):
    """Lista todos os templates de eventos e regras disponíveis."""
    lojas_user = request.user.perfil.get_lojas()
    templates = TemplateEventoRegra.objects.filter(ativo=True).order_by('nome')

    return render(request, 'contabilidade/templates_evento_regra.html', {
        'lojas': lojas_user,
        'templates': templates,
    })


@login_required(login_url='login')
def importar_template_evento_regra(request, template_id):
    """Importa eventos e regras contábeis de um template para uma loja."""
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    template = get_object_or_404(TemplateEventoRegra, pk=template_id, ativo=True)
    loja_id = request.GET.get('loja') or request.POST.get('loja')
    loja = None
    erro_plano_contas = False

    if loja_id:
        try:
            loja = get_object_or_404(Empresa, id_empresa=int(loja_id), id_empresa__in=lojas_ids)
        except (ValueError, TypeError):
            loja = None

    # Validar se a loja tem plano de contas
    if loja:
        contas_existentes = ContaAnalitica.objects.filter(loja=loja).count()
        if contas_existentes == 0:
            erro_plano_contas = True
            if request.method == 'POST':
                messages.error(
                    request,
                    '❌ Plano de Contas não encontrado!\n\n'
                    'É necessário importar o Plano de Contas ANTES de importar eventos e regras.\n\n'
                    'Acesse: Configuração → Templates de Contas → Importar para essa loja.'
                )

    if request.method == 'POST' and loja and not erro_plano_contas:
        try:
            with transaction.atomic():
                eventos_importados = 0
                regras_importadas = 0
                erros_contas = []

                # Importar eventos
                for evento_template in template.eventos.all():
                    # Verificar se evento já existe
                    evento_obj, criado = TipoEvento.objects.get_or_create(
                        codigo=evento_template.codigo,
                        defaults={
                            'descricao': evento_template.descricao,
                            'modulo_origem': evento_template.modulo_origem,
                            'ativo': True,
                        }
                    )
                    if criado:
                        eventos_importados += 1

                    # Importar regras para este evento
                    for regra_template in evento_template.regras.all():
                        # Verificar se regra já existe
                        regra_obj, criado = RegraContabil.objects.get_or_create(
                            loja=loja,
                            tipo_evento=evento_obj,
                            descricao=regra_template.descricao,
                            defaults={'ativa': regra_template.ativa}
                        )

                        if criado or True:  # Sempre recriar partidas para garantir sincronização
                            # Limpar partidas existentes
                            regra_obj.partidas.all().delete()

                            # Importar partidas
                            for partida_template in regra_template.partidas.all():
                                # Resolver conta analítica pelo código de classificação
                                try:
                                    conta = ContaAnalitica.objects.get(
                                        loja=loja,
                                        codigo_classificacao=partida_template.codigo_conta
                                    )
                                    PartidaRegra.objects.create(
                                        regra=regra_obj,
                                        tipo=partida_template.tipo,
                                        conta=conta,
                                        ordem=partida_template.ordem,
                                    )
                                except ContaAnalitica.DoesNotExist:
                                    erros_contas.append(
                                        f'Conta {partida_template.codigo_conta} não encontrada na loja'
                                    )

                        if criado:
                            regras_importadas += 1

            # Mensagem de sucesso
            msg = f'Template "{template.nome}" importado com sucesso! '
            msg += f'{eventos_importados} evento(s) e {regras_importadas} regra(s) criadas.'
            if erros_contas:
                msg += f'\n⚠️ {len(erros_contas)} conta(s) não encontrada(s). '
                msg += 'Certifique-se de que o Plano de Contas foi importado primeiro.'
            messages.success(request, msg)
            return redirect('regras_contabeis')

        except Exception as e:
            messages.error(request, f'Erro ao importar template: {str(e)}')

    context = {
        'template': template,
        'lojas': lojas_user,
        'loja': loja,
        'erro_plano_contas': erro_plano_contas,
        'titulo': f'Importar Template de Eventos e Regras - {template.nome}',
    }
    return render(request, 'contabilidade/importar_template_evento_regra.html', context)


# ==========================================
# SIMULAÇÃO DE LANÇAMENTOS
# ==========================================

@login_required(login_url='login')
def simular_lancamento(request):
    """
    Tela para simular lançamentos contábeis baseados em eventos e regras.
    Permite informar valor(es) e aplica automaticamente as partidas conforme regra.
    Suporta estorno (inverte débitos e créditos).
    """
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    tipo_evento_id = request.GET.get('tipo_evento') or request.POST.get('tipo_evento')

    # Converter para int se houver valor
    if tipo_evento_id:
        try:
            tipo_evento_id = int(tipo_evento_id)
        except (ValueError, TypeError):
            tipo_evento_id = None

    loja = None
    tipos_evento = []
    regra = None
    partidas_debito = []
    partidas_credito = []
    preview_lancamento = None

    if loja_id:
        try:
            loja = get_object_or_404(Empresa, pk=int(loja_id), id_empresa__in=lojas_ids)
            tipos_evento = TipoEvento.objects.filter(ativo=True).order_by('codigo')
        except (ValueError, TypeError):
            loja = None

    # Se evento foi selecionado (GET ou POST), carrega as partidas
    if tipo_evento_id and loja:
        tipo_evento = get_object_or_404(TipoEvento, pk=tipo_evento_id, ativo=True)
        try:
            regra = RegraContabil.objects.get(tipo_evento=tipo_evento, loja=loja, ativa=True)
            partidas_debito = list(regra.partidas.filter(tipo='D').order_by('ordem'))
            partidas_credito = list(regra.partidas.filter(tipo='C').order_by('ordem'))
        except RegraContabil.DoesNotExist:
            messages.warning(request, f'Nenhuma regra ativa para o evento "{tipo_evento.codigo}" nesta loja.')

    if request.method == 'POST':
        data_lancamento = request.POST.get('data_lancamento')
        eh_estorno = request.POST.get('eh_estorno') == 'on'

        if tipo_evento_id and data_lancamento and loja and regra and partidas_debito and partidas_credito:
            tipo_evento = regra.tipo_evento

            # Se há apenas 1 débito e 1 crédito, pode haver um único valor
            if len(partidas_debito) == 1 and len(partidas_credito) == 1:
                valor_total = request.POST.get('valor_unico')
                if valor_total:
                    valor_total = Decimal(valor_total)
                    preview_lancamento = {
                        'data': data_lancamento,
                        'tipo_evento': tipo_evento.codigo,
                        'eh_estorno': eh_estorno,
                        'partidas': [],
                    }

                    # Adicionar partidas ao preview
                    partida_d = partidas_debito[0]
                    partida_c = partidas_credito[0]

                    if eh_estorno:
                        # Inverte: débito vira crédito, crédito vira débito
                        preview_lancamento['partidas'].append({
                            'tipo': 'C',
                            'conta': partida_d.conta,
                            'valor': valor_total,
                            'partida_regra_id': partida_d.id,
                        })
                        preview_lancamento['partidas'].append({
                            'tipo': 'D',
                            'conta': partida_c.conta,
                            'valor': valor_total,
                            'partida_regra_id': partida_c.id,
                        })
                    else:
                        preview_lancamento['partidas'].append({
                            'tipo': 'D',
                            'conta': partida_d.conta,
                            'valor': valor_total,
                            'partida_regra_id': partida_d.id,
                        })
                        preview_lancamento['partidas'].append({
                            'tipo': 'C',
                            'conta': partida_c.conta,
                            'valor': valor_total,
                            'partida_regra_id': partida_c.id,
                        })
            else:
                # Múltiplos débitos ou créditos
                preview_lancamento = {
                    'data': data_lancamento,
                    'tipo_evento': tipo_evento.codigo,
                    'eh_estorno': eh_estorno,
                    'partidas': [],
                }

                soma_debito = Decimal('0')
                soma_credito = Decimal('0')

                # Processar débitos
                for partida_d in partidas_debito:
                    valor_str = request.POST.get(f'valor_debito_{partida_d.id}')
                    if valor_str:
                        valor = Decimal(valor_str)
                        if eh_estorno:
                            # Se estorno, débito vira crédito
                            preview_lancamento['partidas'].append({
                                'tipo': 'C',
                                'conta': partida_d.conta,
                                'valor': valor,
                                'partida_regra_id': partida_d.id,
                            })
                            soma_credito += valor
                        else:
                            preview_lancamento['partidas'].append({
                                'tipo': 'D',
                                'conta': partida_d.conta,
                                'valor': valor,
                                'partida_regra_id': partida_d.id,
                            })
                            soma_debito += valor

                # Processar créditos
                for partida_c in partidas_credito:
                    valor_str = request.POST.get(f'valor_credito_{partida_c.id}')
                    if valor_str:
                        valor = Decimal(valor_str)
                        if eh_estorno:
                            # Se estorno, crédito vira débito
                            preview_lancamento['partidas'].append({
                                'tipo': 'D',
                                'conta': partida_c.conta,
                                'valor': valor,
                                'partida_regra_id': partida_c.id,
                            })
                            soma_debito += valor
                        else:
                            preview_lancamento['partidas'].append({
                                'tipo': 'C',
                                'conta': partida_c.conta,
                                'valor': valor,
                                'partida_regra_id': partida_c.id,
                            })
                            soma_credito += valor

                # Validar que débitos = créditos
                if soma_debito != soma_credito:
                    messages.error(
                        request,
                        f'Débitos (R$ {soma_debito}) e Créditos (R$ {soma_credito}) não conferem!'
                    )
                    preview_lancamento = None

    return render(request, 'contabilidade/simular_lancamento.html', {
        'lojas': lojas_user,
        'loja': loja,
        'tipos_evento': tipos_evento,
        'regra': regra,
        'partidas_debito': partidas_debito,
        'partidas_credito': partidas_credito,
        'preview_lancamento': preview_lancamento,
        'Decimal': Decimal,
    })


@login_required(login_url='login')
def confirmar_lancamento_simulado(request):
    """
    Confirma e salva um lançamento simulado no banco de dados.
    Recebe os dados do preview em POST e cria o LancamentoContabil com suas PartidaLancamento.
    """
    if request.method != 'POST':
        return redirect('simular_lancamento')

    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    regra_id = request.POST.get('regra_id')
    data_lancamento_str = request.POST.get('data_lancamento')
    eh_estorno = request.POST.get('eh_estorno') == 'on'

    loja = get_object_or_404(Empresa, id_empresa=loja_id, id_empresa__in=lojas_ids)
    regra = get_object_or_404(RegraContabil, pk=regra_id, loja=loja, ativa=True)

    # Converter data
    from datetime import datetime
    data_lancamento = datetime.strptime(data_lancamento_str, '%Y-%m-%d').date()

    # Obter período contábil
    periodo = get_object_or_404(
        PeriodoContabil,
        loja=loja,
        ano=data_lancamento.year,
        mes=data_lancamento.month,
        status__in=['ABERTO', 'REABERTO']
    )

    with transaction.atomic():
        try:
            # Gerar próximo número de lançamento
            ultimo_lancamento = LancamentoContabil.objects.filter(
                loja=loja
            ).order_by('-numero').first()
            proximo_numero = (ultimo_lancamento.numero if ultimo_lancamento else 0) + 1

            # Criar lançamento
            lancamento = LancamentoContabil.objects.create(
                loja=loja,
                numero=proximo_numero,
                data_lancamento=data_lancamento,
                historico=f"Simulado: {regra.tipo_evento.codigo}" + (" (ESTORNO)" if eh_estorno else ""),
                tipo='ESTORNO' if eh_estorno else 'NORMAL',
                evento=None,  # Não associado a evento operacional
                usuario=request.user,
                periodo=periodo,
            )

            # Coletar partidas do POST
            partidas_a_salvar = []

            # Procurar por TODOS os campos de valor no POST (débito e crédito)
            # Isso funciona independentemente se é estorno ou não
            all_partidas = regra.partidas.order_by('ordem')

            for partida_regra in all_partidas:
                # Procurar pelos campos com o ID da partida da regra
                valor_debito = request.POST.get(f'valor_debito_{partida_regra.id}')
                valor_credito = request.POST.get(f'valor_credito_{partida_regra.id}')

                if valor_debito:
                    valor = Decimal(valor_debito)
                    partidas_a_salvar.append({
                        'lancamento': lancamento,
                        'conta': partida_regra.conta,
                        'tipo': 'D',
                        'valor': valor,
                    })

                if valor_credito:
                    valor = Decimal(valor_credito)
                    partidas_a_salvar.append({
                        'lancamento': lancamento,
                        'conta': partida_regra.conta,
                        'tipo': 'C',
                        'valor': valor,
                    })

            # Validar saldo conforme natureza da conta
            saldos_por_conta = {}
            for partida_data in partidas_a_salvar:
                conta = partida_data['conta']
                if conta.id not in saldos_por_conta:
                    # Buscar saldo atual da conta
                    partidas_existentes = PartidaLancamento.objects.filter(conta=conta)
                    debitos = partidas_existentes.filter(tipo='D').aggregate(total=Sum('valor'))['total'] or Decimal('0')
                    creditos = partidas_existentes.filter(tipo='C').aggregate(total=Sum('valor'))['total'] or Decimal('0')
                    saldos_por_conta[conta.id] = {'debitos': debitos, 'creditos': creditos, 'conta': conta}

                # Atualizar saldo com a nova partida
                if partida_data['tipo'] == 'D':
                    saldos_por_conta[conta.id]['debitos'] += partida_data['valor']
                else:
                    saldos_por_conta[conta.id]['creditos'] += partida_data['valor']

            # Verificar naturaleza de cada conta
            erros_natureza = []
            for conta_id, saldo_info in saldos_por_conta.items():
                conta = saldo_info['conta']
                saldo_liquido = saldo_info['debitos'] - saldo_info['creditos']
                natureza = conta.conta_sintetica.tipo_conta.natureza

                # Validar conforme a natureza
                if natureza == 'DEVEDORA' and saldo_liquido < 0:
                    erros_natureza.append(
                        f'Conta "{conta.nome}" ({conta.codigo_classificacao}) tem natureza Devedora '
                        f'mas o saldo ficaria Credor: R$ {abs(saldo_liquido):.2f}'
                    )
                elif natureza == 'CREDORA' and saldo_liquido > 0:
                    erros_natureza.append(
                        f'Conta "{conta.nome}" ({conta.codigo_classificacao}) tem natureza Credora '
                        f'mas o saldo ficaria Devedor: R$ {saldo_liquido:.2f}'
                    )

            if erros_natureza:
                # Rollback da transaction automático por exceção
                raise ValidationError(
                    'Lançamento violaria natureza das contas:\n' + '\n'.join(erros_natureza)
                )

            # Salvar todas as partidas
            for partida_data in partidas_a_salvar:
                PartidaLancamento.objects.create(**partida_data)

            messages.success(
                request,
                f'✓ Lançamento #{lancamento.numero} contabilizado com sucesso em {data_lancamento}.'
            )
            return redirect(f'/contabilidade/simular-lancamento/?tipo_evento={regra.tipo_evento.id}')

        except ValidationError as e:
            # Erro de validação de natureza - mostrar mensagem e permitir edição
            # Não deleta o lançamento porque está em transaction.atomic() que rollback automaticamente

            # Reconstituir preview_lancamento a partir das partidas_a_salvar
            # Necessário para manter preview visível e permitir edição
            # Mapeia (conta_id, tipo) -> partida_regra_id para reconstruir os hidden inputs
            partidas_regra_map = {}
            for partida_regra in regra.partidas.all():
                key = (partida_regra.conta.id, partida_regra.tipo)
                partidas_regra_map[key] = partida_regra.id

            preview_lancamento = {
                'data': data_lancamento_str,
                'tipo_evento': regra.tipo_evento.codigo,
                'eh_estorno': eh_estorno,
                'partidas': [],
                'erro_natureza': True,  # Flag para renderizar mensagem de erro na template
            }
            for partida_data in partidas_a_salvar:
                conta = partida_data['conta']
                tipo = partida_data['tipo']
                key = (conta.id, tipo)
                preview_lancamento['partidas'].append({
                    'conta': conta,
                    'tipo': tipo,
                    'valor': partida_data['valor'],
                    'partida_regra_id': partidas_regra_map.get(key),
                })
            # Não redireciona, mantém o preview para edição
            tipos_evento = TipoEvento.objects.all().order_by('codigo')
            return render(request, 'contabilidade/simular_lancamento.html', {
                'loja': loja,
                'tipos_evento': tipos_evento,
                'regra': regra,
                'preview_lancamento': preview_lancamento,
            })
        except PeriodoContabil.DoesNotExist:
            messages.error(
                request,
                f'Período {data_lancamento.month}/{data_lancamento.year} não existe ou está fechado para esta loja.'
            )
            return redirect('simular_lancamento')
        except Exception as e:
            messages.error(request, f'Erro ao salvar lançamento: {str(e)}')
            return redirect('simular_lancamento')


# ==========================================
# RELATÓRIOS (DRE SIMPLIFICADO)
# ==========================================

@login_required(login_url='login')
def gerar_dre(request):
    """
    Gera DRE (Demonstração do Resultado do Exercício) simplificado.
    Agrupa lançamentos por conta analítica e calcula o resultado.
    """
    lojas_user = request.user.perfil.get_lojas()
    lojas_ids = lojas_user.values_list('id_empresa', flat=True)

    loja_id = request.session.get('loja_id')
    periodo_id = request.GET.get('periodo')

    loja = None
    periodo = None
    dre_data = None
    lojas_list = list(lojas_user)
    periodos_list = []

    if loja_id:
        loja = get_object_or_404(Empresa, pk=loja_id, id_empresa__in=lojas_ids)
        periodos_list = PeriodoContabil.objects.filter(loja=loja).order_by('-ano', '-mes')

        if periodo_id:
            periodo = get_object_or_404(PeriodoContabil, pk=periodo_id, loja=loja)

            # Buscar todos os lançamentos do período
            lancamentos = LancamentoContabil.objects.filter(
                loja=loja,
                periodo=periodo
            ).prefetch_related('partidas__conta__conta_sintetica')

            # Agrupar por conta analítica
            contas_dados = {}
            for lancamento in lancamentos:
                for partida in lancamento.partidas.all():
                    conta = partida.conta
                    if conta.id not in contas_dados:
                        contas_dados[conta.id] = {
                            'conta': conta,
                            'tipo_conta_codigo': conta.conta_sintetica.tipo_conta.codigo,
                            'debitos': Decimal('0'),
                            'creditos': Decimal('0'),
                        }

                    if partida.tipo == 'D':
                        contas_dados[conta.id]['debitos'] += partida.valor
                    else:  # 'C'
                        contas_dados[conta.id]['creditos'] += partida.valor

            # Separar por tipo de conta
            receitas = []
            despesas = []
            outros = []

            for conta_id, dados in contas_dados.items():
                tipo_conta_codigo = dados['tipo_conta_codigo']

                # Calcular saldo conforme o tipo de conta
                if tipo_conta_codigo == 'RECEITA':
                    # RECEITA: crédito positivo, débito negativo
                    saldo = dados['creditos'] - dados['debitos']
                elif tipo_conta_codigo == 'DESPESA':
                    # DESPESA: débito positivo, crédito negativo
                    saldo = dados['debitos'] - dados['creditos']
                else:
                    # ATIVO/PASSIVO: débito positivo, crédito negativo
                    saldo = dados['debitos'] - dados['creditos']

                item = {
                    'conta': dados['conta'],
                    'tipo_conta': tipo_conta_codigo,
                    'debitos': dados['debitos'],
                    'creditos': dados['creditos'],
                    'saldo': saldo,
                }

                if tipo_conta_codigo == 'RECEITA':
                    receitas.append(item)
                elif tipo_conta_codigo == 'DESPESA':
                    despesas.append(item)
                else:
                    outros.append(item)

            # Ordenar por código
            receitas.sort(key=lambda x: x['conta'].codigo_classificacao)
            despesas.sort(key=lambda x: x['conta'].codigo_classificacao)

            # Calcular totais usando saldos
            total_receitas = sum(r['saldo'] for r in receitas)
            total_despesas = sum(d['saldo'] for d in despesas)
            resultado = total_receitas - total_despesas

            dre_data = {
                'receitas': receitas,
                'total_receitas': total_receitas,
                'despesas': despesas,
                'total_despesas': total_despesas,
                'resultado': resultado,
                'periodo': f"{periodo.mes:02d}/{periodo.ano}",
            }

    return render(request, 'contabilidade/gerar_dre.html', {
        'lojas': lojas_list,
        'loja': loja,
        'periodos': periodos_list,
        'periodo': periodo,
        'dre_data': dre_data,
    })


# ==========================================
# IMPORTAÇÃO DE EVENTOS DA EMPRESA MODELO
# ==========================================

@login_required(login_url='login')
def importar_eventos_modelo(request):
    """
    Importa os 13 eventos padrão de restaurante para a loja do usuário.
    Eventos já estão populados em TipoEvento com eh_modelo=True.
    """
    lojas_user = request.user.perfil.get_lojas()
    loja_id = request.session.get('loja_id')
    loja = None
    eventos_existentes = 0

    if loja_id:
        try:
            loja = get_object_or_404(
                Empresa,
                id_empresa=int(loja_id),
                id_empresa__in=lojas_user.values_list('id_empresa', flat=True)
            )
        except (ValueError, TypeError):
            messages.error(request, 'Loja inválida')
            return redirect('eventos_operacionais')

    if request.method == 'GET' and loja:
        # Contar eventos já existentes
        eventos_existentes = TipoEvento.objects.filter(
            codigo__in=[
                'FOLHA_PAGAMENTO_MENSAL',
                'COMPRA_ALIMENTOS_BEBIDAS',
                'VENDA_REFEICOES',
                'DESPESA_MATERIAL_CONSUMO',
                'COMPRA_EQUIPAMENTO_KICHEN',
                'DESPESA_ALUGUEL_LOCACAO',
                'DESPESA_UTILIDADES',
                'DEPRECIACAO_MENSAL',
                'DESPESA_BENEFICIOS_FUNCIONARIOS',
                'DEVOLUCAO_CLIENTE',
                'APLICACAO_FUNDO_RENDA_FIXA',
                'RECEITA_JUROS_APLICACAO',
                'PAGAMENTO_FORNECEDOR',
            ]
        ).count()

    if request.method == 'POST' and loja:
        try:
            with transaction.atomic():
                # Buscar todos os eventos modelo
                eventos_modelo = TipoEvento.objects.filter(eh_modelo=True)
                importados = 0
                duplicados = 0

                for evento in eventos_modelo:
                    # Verificar se já existe na loja
                    tipo_evento_existe = TipoEvento.objects.filter(
                        codigo=evento.codigo
                    ).exists()

                    if tipo_evento_existe:
                        duplicados += 1
                    else:
                        # Criar novo tipo de evento
                        TipoEvento.objects.create(
                            codigo=evento.codigo,
                            descricao=evento.descricao,
                            modulo_origem=evento.modulo_origem,
                            ativo=True,
                            eh_modelo=False,  # Não é modelo, é instância
                        )
                        importados += 1

                messages.success(
                    request,
                    f'✅ Eventos importados com sucesso!\n'
                    f'{importados} novos eventos criados\n'
                    f'{duplicados} eventos já existiam'
                )
        except Exception as e:
            messages.error(
                request,
                f'❌ Erro ao importar eventos: {str(e)}'
            )

        return redirect('eventos_operacionais')

    return render(request, 'contabilidade/importar_eventos_modelo.html', {
        'loja': loja,
        'eventos_existentes': eventos_existentes,
        'total_eventos': 13,
    })
