"""
Importações - Views de upload de arquivos e sincronização de pagamentos.

Responsabilidades:
- Upload e processamento de CSVs (SWFast, Stone) e Excel (iFood)
- Sincronização automática de formas de pagamento (Normalizador)
"""

import pandas as pd
import re
import unidecode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from datetime import datetime

from .forms import UploadArquivoForm
from .models import VendaSWFast, TransacaoStone, PedidoIFood, FormaPagamento
from core.models import Empresa


@login_required(login_url='login')
def home(request):
    from core.models import Empresa
    from .models import VendaSWFast, PedidoIFood, FormaPagamento
    from contabilidade.models import LancamentoContabil, PeriodoContabil, EventoOperacional
    from financeiro.models import ContaReceber, ContaPagar
    from django.db.models import Sum
    from decimal import Decimal
    import datetime

    hoje = datetime.date.today()

    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()

    # ── Operacional ──────────────────────────────────────
    total_lojas  = lojas_user.count()
    total_vendas = VendaSWFast.objects.filter(loja__in=lojas_user).count() if lojas_user.exists() else 0
    # PedidoIFood usa id_restaurante (ncad_ifood), não codigo_loja
    codigos_ifood = list(
        lojas_user.values_list('ncad_ifood', flat=True)
        .filter(ncad_ifood__gt=0)
    )
    codigos_ifood_str = [str(c) for c in codigos_ifood]
    total_pedidos = PedidoIFood.objects.filter(id_restaurante__in=codigos_ifood_str).count() if codigos_ifood_str else 0
    formas_sem_config = (
        FormaPagamento.objects.filter(loja__in=lojas_user, especific_form_pgto__isnull=True).count()
        + FormaPagamento.objects.filter(loja__in=lojas_user, especific_form_pgto='').count()
    ) if lojas_user.exists() else 0

    # ── Contabilidade ─────────────────────────────────────
    if lojas_user.exists():
        periodos_abertos  = PeriodoContabil.objects.filter(status__in=['ABERTO', 'REABERTO'], loja__in=lojas_user).count()
        lancamentos_mes   = LancamentoContabil.objects.filter(
            data_lancamento__year=hoje.year,
            data_lancamento__month=hoje.month,
            loja__in=lojas_user
        ).count()
        eventos_pendentes = EventoOperacional.objects.filter(status='PENDENTE', loja__in=lojas_user).count()
        eventos_erro      = EventoOperacional.objects.filter(status='ERRO', loja__in=lojas_user).count()
    else:
        periodos_abertos = lancamentos_mes = eventos_pendentes = eventos_erro = 0

    # ── Financeiro ────────────────────────────────────────
    if lojas_user.exists():
        cr_aberto = (
            ContaReceber.objects
            .filter(status__in=['ABERTO', 'PARCIAL'], loja__in=lojas_user)
            .aggregate(s=Sum('saldo'))['s'] or Decimal('0')
        )
        cp_aberto = (
            ContaPagar.objects
            .filter(status__in=['ABERTO', 'PARCIAL'], loja__in=lojas_user)
            .aggregate(s=Sum('saldo'))['s'] or Decimal('0')
        )
        cr_vencido = ContaReceber.objects.filter(
            status__in=['ABERTO', 'PARCIAL'], data_vencimento__lt=hoje, loja__in=lojas_user
        ).count()
        cp_vencido = ContaPagar.objects.filter(
            status__in=['ABERTO', 'PARCIAL'], data_vencimento__lt=hoje, loja__in=lojas_user
        ).count()
    else:
        cr_aberto = cp_aberto = Decimal('0')
        cr_vencido = cp_vencido = 0

    # ── Alertas ───────────────────────────────────────────
    alertas = []
    if formas_sem_config:
        alertas.append({
            'tipo': 'warning',
            'msg': f'{formas_sem_config} forma(s) de pagamento sem configuração.',
            'link': 'formas_pagamento', 'link_label': 'Configurar →'
        })
    if eventos_erro:
        alertas.append({
            'tipo': 'error',
            'msg': f'{eventos_erro} evento(s) operacional(ais) com erro de contabilização.',
            'link': 'eventos_operacionais', 'link_label': 'Ver eventos →'
        })
    if cr_vencido:
        alertas.append({
            'tipo': 'warning',
            'msg': f'{cr_vencido} título(s) a receber vencido(s).',
            'link': 'contas_receber', 'link_label': 'Ver contas →'
        })
    if cp_vencido:
        alertas.append({
            'tipo': 'error',
            'msg': f'{cp_vencido} título(s) a pagar vencido(s).',
            'link': 'contas_pagar', 'link_label': 'Ver contas →'
        })

    context = {
        # operacional
        'total_lojas':       total_lojas,
        'total_vendas':      total_vendas,
        'total_pedidos':     total_pedidos,
        'formas_sem_config': formas_sem_config,
        # contabilidade
        'periodos_abertos':  periodos_abertos,
        'lancamentos_mes':   lancamentos_mes,
        'eventos_pendentes': eventos_pendentes,
        'eventos_erro':      eventos_erro,
        # financeiro
        'cr_aberto':         cr_aberto,
        'cp_aberto':         cp_aberto,
        'cr_vencido':        cr_vencido,
        'cp_vencido':        cp_vencido,
        # alertas
        'alertas':           alertas,
        'hoje':              hoje,
    }
    return render(request, 'importacoes/index.html', context)


# ==========================================
# FUNÇÕES AUXILIARES DE LIMPEZA
# ==========================================

def limpar_valor(valor):
    """Converte valores monetários do Excel (com ponto ou vírgula) para float."""
    if pd.isna(valor) or valor == '':
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)

    valor_str = str(valor).strip()
    if '.' in valor_str and ',' not in valor_str:
        try:
            return float(valor_str)
        except ValueError:
            pass

    valor_str = valor_str.replace('.', '')
    valor_str = valor_str.replace(',', '.')
    valor_str = re.sub(r"[^\d.-]", "", valor_str)
    try:
        return float(valor_str)
    except ValueError:
        return 0.0


def limpar_numero(valor):
    """Garante que IDs sejam apenas números, removendo '.0' do Pandas."""
    if pd.isna(valor):
        return ""
    val_str = str(valor).strip()
    if val_str.endswith('.0'):
        val_str = val_str[:-2]
    return re.sub(r"\D", "", val_str)


# ==========================================
# VIEW DE UPLOAD DE ARQUIVOS
# ==========================================

@login_required(login_url='login')
def pagina_upload(request):
    if request.method == 'POST':
        form = UploadArquivoForm(request.POST, request.FILES)
        if form.is_valid():
            tipo = form.cleaned_data['tipo_arquivo']
            arquivo = request.FILES['arquivo']

            try:
                # ----------------------------------------------------
                # 1. SWFAST (VENDAS)
                # ----------------------------------------------------
                if tipo == 'swfast':
                    df = pd.read_csv(arquivo, delimiter=",", parse_dates=["DataHoraTransacao"], dayfirst=True)
                    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                    df["ValorPagamento"] = df["ValorPagamento"].apply(limpar_valor)
                    df["CodigoLoja"] = df["CodigoLoja"].apply(limpar_numero)
                    df["NrAbertura"] = df["NrAbertura"].apply(limpar_numero) if "NrAbertura" in df.columns else ""

                    col_venda = "Venda" if "Venda" in df.columns else "IdPedidoExterno"
                    df["ChaveComposta"] = (
                        df["FormaPagamento"].astype(str) + "-" +
                        df[col_venda].astype(str) + "-" +
                        df["ValorPagamento"].astype(str) + "-" +
                        df["DataHoraTransacao"].astype(str)
                    )

                    campos_agrupamento = ["FormaPagamento", "Aplicativo", "Operador", "DataHoraTransacao",
                                          "IdPedidoExterno", "CodigoLoja", "ChaveComposta", "NrAbertura"]
                    if "Venda" in df.columns:
                        campos_agrupamento.append("Venda")

                    df = df.groupby(campos_agrupamento, dropna=False, as_index=False).agg({"ValorPagamento": "sum"})

                    contador = 0
                    for _, row in df.iterrows():
                        app = str(row.get('Aplicativo', '')).strip()
                        id_ext = str(row.get('IdPedidoExterno', '')).strip()
                        venda = str(row.get('Venda', '')).strip() if 'Venda' in df.columns else id_ext
                        forma_pgto = str(row.get('FormaPagamento', '')).strip()
                        operador = str(row.get('Operador', '')).strip()

                        # Busca a Empresa pelo codigo_loja (ncad_swfast)
                        codigo_loja = row['CodigoLoja']
                        empresa = Empresa.objects.filter(ncad_swfast=codigo_loja).first()

                        VendaSWFast.objects.update_or_create(
                            chave_composta=row['ChaveComposta'],
                            defaults={
                                'loja': empresa,
                                'codigo_loja': codigo_loja,
                                'nr_abertura': row['NrAbertura'],
                                'forma_pagamento': forma_pgto if forma_pgto.lower() != 'nan' else '',
                                'aplicativo': app if app.lower() != 'nan' else '',
                                'operador': operador if operador.lower() != 'nan' else '',
                                'data_hora_transacao': row['DataHoraTransacao'] if pd.notna(row['DataHoraTransacao']) else None,
                                'id_pedido_externo': id_ext if id_ext.lower() != 'nan' else '',
                                'venda': venda if venda.lower() != 'nan' else '',
                                'valor_pagamento': row['ValorPagamento']
                            }
                        )
                        contador += 1
                    messages.success(request, f"Sucesso! {contador} vendas do SWFast importadas.")

                # ----------------------------------------------------
                # 2. SWFAST (ABERTURA/FECHAMENTO)
                # ----------------------------------------------------
                elif tipo == 'swfast_abertura':
                    df_csv = pd.read_csv(arquivo, parse_dates=['DataHoraAbertura', 'DataHoraFechamento'], dayfirst=True)
                    df_csv.sort_values(by=['CodigoLoja', 'NrAbertura'], ascending=False, inplace=True)
                    df_csv.reset_index(drop=True, inplace=True)

                    for i in range(len(df_csv) - 1):
                        if df_csv.loc[i, 'CodigoLoja'] == df_csv.loc[i + 1, 'CodigoLoja']:
                            fechamento_anterior = df_csv.loc[i + 1, 'DataHoraFechamento']
                            if pd.notna(fechamento_anterior):
                                df_csv.loc[i, 'DataHoraAbertura'] = fechamento_anterior + pd.Timedelta(seconds=30)

                    for i, row in df_csv.iterrows():
                        if pd.isna(row['DataHoraAbertura']) or pd.isna(row['DataHoraFechamento']):
                            fech = row['DataHoraFechamento'] if pd.notna(row['DataHoraFechamento']) else datetime.now()
                            hora_base = 6 if 6 <= fech.hour < 18 else 18
                            abertura_simulada = fech.replace(hour=hora_base, minute=0, second=0)
                            df_csv.at[i, 'DataHoraAbertura'] = abertura_simulada
                            df_csv.at[i, 'DataHoraFechamento'] = abertura_simulada + pd.Timedelta(hours=12)

                    contador = 0
                    for _, row in df_csv.iterrows():
                        cod_loja = limpar_numero(row['CodigoLoja'])
                        nr_abert = limpar_numero(row['NrAbertura'])
                        dt_abert = row['DataHoraAbertura'] if pd.notna(row['DataHoraAbertura']) else None
                        dt_fech = row['DataHoraFechamento'] if pd.notna(row['DataHoraFechamento']) else None

                        # Busca a Empresa pelo codigo_loja (ncad_swfast)
                        empresa = Empresa.objects.filter(ncad_swfast=cod_loja).first()

                        chave_turno = f"TURNO-{cod_loja}-{nr_abert}"
                        VendaSWFast.objects.update_or_create(
                            chave_composta=chave_turno,
                            defaults={
                                'loja': empresa,
                                'codigo_loja': cod_loja, 'nr_abertura': nr_abert,
                                'dthr_abert_cx': dt_abert, 'dthr_encerr_cx': dt_fech,
                                'forma_pagamento': 'ABERTURA_CAIXA', 'venda': 'INFO_TURNO', 'valor_pagamento': 0.0,
                            }
                        )
                        VendaSWFast.objects.filter(
                            codigo_loja=cod_loja, nr_abertura=nr_abert
                        ).exclude(chave_composta=chave_turno).update(
                            dthr_abert_cx=dt_abert, dthr_encerr_cx=dt_fech
                        )
                        contador += 1
                    messages.success(request, f"Sucesso! {contador} turnos processados.")

                # ----------------------------------------------------
                # 3. STONE (CSV)
                # ----------------------------------------------------
                elif tipo == 'stone':
                    df = pd.read_csv(arquivo, delimiter=",")
                    df.columns = [unidecode.unidecode(col).strip().upper().replace(" ", "_") for col in df.columns]
                    df.rename(columns={
                        "N_DE_PARCELAS": "QTD_DE_PARCELAS",
                        "VALOR_LIQUIDO": "VALOR_LÍQUIDO",
                        "DESCONTO_DE_ANTECIPACAO": "DESCONTO_DE_ANTECIPAÇÃO"
                    }, inplace=True)
                    df["DATA_DA_VENDA"] = pd.to_datetime(df.get("DATA_DA_VENDA"), dayfirst=True, errors="coerce")

                    contador = 0
                    for _, row in df.iterrows():
                        stone_id = str(row.get('STONE_ID', ''))
                        if stone_id == 'nan' or stone_id == '':
                            continue

                        data_venda = row['DATA_DA_VENDA'] if pd.notna(row['DATA_DA_VENDA']) else None
                        TransacaoStone.objects.update_or_create(
                            stone_id=stone_id,
                            defaults={
                                'stonecode': limpar_numero(row.get('STONECODE', '')),
                                'data_venda': data_venda,
                                'bandeira': str(row.get('BANDEIRA', '')),
                                'produto': str(row.get('PRODUTO', '')),
                                'qtd_parcelas': int(row.get('QTD_DE_PARCELAS', 1) if pd.notna(row.get('QTD_DE_PARCELAS')) else 1),
                                'valor_bruto': limpar_valor(row.get('VALOR_BRUTO', 0)),
                                'valor_liquido': limpar_valor(row.get('VALOR_LÍQUIDO', 0)),
                                'desconto_mdr': limpar_valor(row.get('DESCONTO_DE_MDR', 0)),
                                'desconto_antecipacao': limpar_valor(row.get('DESCONTO_DE_ANTECIPAÇÃO', 0)),
                                'documento': row.get('DOCUMENTO') if pd.notna(row.get('DOCUMENTO')) else None,
                            }
                        )
                        contador += 1
                    messages.success(request, f"Sucesso! {contador} transações da Stone importadas.")

                # ----------------------------------------------------
                # 4. IFOOD (EXCEL)
                # ----------------------------------------------------
                elif tipo == 'ifood':
                    df = pd.read_excel(arquivo)
                    mapeamento = {
                        "ID COMPLETO DO PEDIDO": "ID DO PEDIDO",
                        "ID CURTO DO PEDIDO": "N° PEDIDO",
                        "DATA E HORA DO PEDIDO": "DATA",
                        "NOME DA LOJA": "RESTAURANTE",
                        "ID DA LOJA": "ID DO RESTAURANTE",
                        "TAXA DE ENTREGA PAGA PELO CLIENTE (R$)": "TAXA DE ENTREGA",
                        "VALOR DOS ITENS (R$)": "VALOR DOS ITENS",
                        "INCENTIVO PROMOCIONAL DO IFOOD (R$)": "INCENTIVO PROMOCIONAL DO IFOOD",
                        "INCENTIVO PROMOCIONAL DA LOJA (R$)": "INCENTIVO PROMOCIONAL DA LOJA",
                        "TAXA DE SERVIÇO (R$)": "TAXA DE SERVIÇO",
                        "VALOR LIQUIDO (R$)": "TOTAL DO PARCEIRO",
                        "TOTAL PAGO PELO CLIENTE (R$)": "TOTAL DO PEDIDO",
                        "FORMA DE PAGAMENTO": "FORMAS DE PAGAMENTO"
                    }
                    df.rename(columns=mapeamento, inplace=True)
                    df["DATA"] = pd.to_datetime(df.get("DATA"), errors='coerce')

                    empresas_db = Empresa.objects.values_list('ncad_ifood', 'integrado')
                    empresas_dict = {str(ncad): integrado for ncad, integrado in empresas_db if ncad}

                    def calcular_vlr_pedido(linha, dict_empresas):
                        id_rest = limpar_numero(linha.get("ID DO RESTAURANTE", ""))
                        integrado = dict_empresas.get(id_rest, "Não")
                        vlr_itens = limpar_valor(linha.get("VALOR DOS ITENS", 0))
                        incentivo_loja = limpar_valor(linha.get("INCENTIVO PROMOCIONAL DA LOJA", 0))
                        taxa_entrega = limpar_valor(linha.get("TAXA DE ENTREGA", 0))
                        return (vlr_itens - incentivo_loja + taxa_entrega) if integrado == "Sim" else (vlr_itens - incentivo_loja)

                    coluna_status = None
                    for col in df.columns:
                        if 'STATUS' in str(col).upper():
                            coluna_status = col
                            break

                    contador = 0
                    for _, row in df.iterrows():
                        id_pedido = str(row.get('ID DO PEDIDO', '')).strip()
                        if id_pedido == 'nan' or id_pedido == '':
                            continue

                        data_pedido = row['DATA'] if pd.notna(row['DATA']) else None
                        formas_pgto = row.get('FORMAS DE PAGAMENTO')
                        origem_canc = row.get('ORIGEM DO CANCELAMENTO')

                        status_pedido = 'CONCLUIDO'
                        if coluna_status:
                            status_bruto = str(row.get(coluna_status, '')).strip().upper()
                            if status_bruto != 'NAN' and status_bruto != '':
                                status_pedido = status_bruto
                        if 'CANCELAD' in status_pedido:
                            status_pedido = 'CANCELADO'

                        PedidoIFood.objects.update_or_create(
                            id_pedido=id_pedido,
                            defaults={
                                'nr_pedido': str(row.get('N° PEDIDO', '')),
                                'data': data_pedido,
                                'restaurante': str(row.get('RESTAURANTE', '')),
                                'id_restaurante': limpar_numero(row.get('ID DO RESTAURANTE', '')),
                                'valor_itens': limpar_valor(row.get('VALOR DOS ITENS', 0)),
                                'total_pedido': limpar_valor(row.get('TOTAL DO PEDIDO', 0)),
                                'vlr_pedido_sw': calcular_vlr_pedido(row, empresas_dict),
                                'formas_pagamento': str(formas_pgto) if pd.notna(formas_pgto) else '',
                                'incentivo_ifood': limpar_valor(row.get('INCENTIVO PROMOCIONAL DO IFOOD', 0)),
                                'origem_cancelamento': str(origem_canc) if pd.notna(origem_canc) else '',
                                'status_pedido': status_pedido,
                            }
                        )
                        contador += 1
                    messages.success(request, f"Sucesso! {contador} pedidos do iFood importados.")

            except Exception as e:
                messages.error(request, f"Erro ao processar: {e}")
    else:
        form = UploadArquivoForm()
    return render(request, 'importacoes/upload.html', {'form': form})


# ==========================================
# SINCRONIZAÇÃO DE FORMAS DE PAGAMENTO
# ==========================================

@login_required(login_url='login')
def sincronizar_formas_pagamento(request):
    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()

    if request.method == 'POST':
        try:
            combinacoes_swfast = VendaSWFast.objects.filter(
                loja__in=lojas_user
            ).exclude(
                forma_pagamento__isnull=True
            ).exclude(
                forma_pagamento=''
            ).values('forma_pagamento', 'codigo_loja', 'aplicativo').distinct()

            novas_insercoes = 0

            for combo in combinacoes_swfast:
                forma = str(combo.get('forma_pagamento', '')).strip()
                loja = str(combo.get('codigo_loja', '')).strip()
                app = str(combo.get('aplicativo', '')).strip()

                # Get the Empresa object for this loja code
                empresa_obj = Empresa.objects.filter(ncad_swfast=loja).first()
                if not empresa_obj:
                    continue

                existe = FormaPagamento.objects.filter(
                    forma_pagamento=forma, loja=empresa_obj, aplicativo=app
                ).exists()

                if not existe:
                    referencia = FormaPagamento.objects.filter(
                        forma_pagamento=forma, aplicativo=app
                    ).exclude(especific_form_pgto='').first()

                    especificacao_herdada = referencia.especific_form_pgto if referencia else ''

                    FormaPagamento.objects.create(
                        forma_pagamento=forma, loja=empresa_obj,
                        aplicativo=app, especific_form_pgto=especificacao_herdada
                    )
                    novas_insercoes += 1

            if novas_insercoes > 0:
                messages.success(request, f"Sucesso! {novas_insercoes} configurações sincronizadas.")
            else:
                messages.info(request, "Todas as formas de pagamento já estão sincronizadas.")

        except Exception as e:
            messages.error(request, f"Erro ao sincronizar: {e}")

        return redirect('formas_pagamento')

    formas = FormaPagamento.objects.filter(loja__in=lojas_user).order_by('loja', 'forma_pagamento')
    return render(request, 'importacoes/formas_pagamento.html', {'formas': formas})


@login_required(login_url='login')
def editar_especificacao_forma(request, pk):
    """AJAX endpoint para editar especificação de forma de pagamento."""
    from django.http import JsonResponse

    # ── Filtro de acesso multi-loja ──────────────────────
    lojas_user = request.user.perfil.get_lojas()

    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        forma = get_object_or_404(FormaPagamento, pk=pk, loja__in=lojas_user)
        nova_especificacao = request.POST.get('especific_form_pgto', '').strip()

        forma.especific_form_pgto = nova_especificacao
        forma.save(update_fields=['especific_form_pgto'])

        return JsonResponse({
            'status': 'success',
            'message': f'Especificação salva: "{nova_especificacao or "vazio"}"',
            'especific_form_pgto': forma.especific_form_pgto,
        })

    return JsonResponse({'status': 'error', 'message': 'Requisição inválida.'}, status=400)


# ==========================================
# LOGOUT
# ==========================================

def sair_do_sistema(request):
    logout(request)
    return redirect('login')
