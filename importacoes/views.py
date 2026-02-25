import sqlite3
import pandas as pd
import re
import unidecode
import io
from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from .forms import UploadArquivoForm
from .models import VendaSWFast, TransacaoStone, PedidoIFood, Empresa, FormaPagamento
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def home(request):
    return render(request, 'importacoes/index.html')


# ==========================================
# 🛡️ FUNÇÕES AUXILIARES DE LIMPEZA (BLINDADAS)
# ==========================================

def limpar_valor(valor):
    """Converte valores monetários do Excel (com ponto ou vírgula) para float perfeito."""
    if pd.isna(valor) or valor == '':
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    
    valor_str = str(valor).strip()
    # Verifica se já é padrão americano (ex: 1250.50)
    if '.' in valor_str and ',' not in valor_str:
        try: return float(valor_str)
        except: pass
        
    # Padrão Brasileiro (ex: 1.250,50)
    valor_str = valor_str.replace('.', '')    # Tira o ponto de milhar
    valor_str = valor_str.replace(',', '.')   # Troca a vírgula por ponto decimal
    valor_str = re.sub(r"[^\d.-]", "", valor_str) # Tira R$ e espaços
    try:
        return float(valor_str)
    except:
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
# 📤 VIEW DE UPLOAD DE ARQUIVOS
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

                    df.loc[df["FormaPagamento"].str.contains("IFOOD ONLINE", na=False, case=False), "FormaPagamento"] = "IFOOD"
                    df.loc[df["FormaPagamento"].str.contains("IFOOD VOUCHER", na=False, case=False), "FormaPagamento"] = "IFOOD"
                    
                    col_venda = "Venda" if "Venda" in df.columns else "IdPedidoExterno"
                    df["ChaveComposta"] = (
                        df["FormaPagamento"].astype(str) + "-" + 
                        df[col_venda].astype(str) + "-" + 
                        df["ValorPagamento"].astype(str) + "-" +
                        df["DataHoraTransacao"].astype(str)
                    )

                    campos_agrupamento = ["FormaPagamento", "Aplicativo", "Operador", "DataHoraTransacao", 
                                          "IdPedidoExterno", "CodigoLoja", "ChaveComposta", "NrAbertura"]
                    if "Venda" in df.columns: campos_agrupamento.append("Venda")
                        
                    df = df.groupby(campos_agrupamento, dropna=False, as_index=False).agg({"ValorPagamento": "sum"})

                    contador = 0
                    for _, row in df.iterrows():
                        data_transacao = row['DataHoraTransacao'] if pd.notna(row['DataHoraTransacao']) else None
                        VendaSWFast.objects.update_or_create(
                            chave_composta=row['ChaveComposta'],
                            defaults={
                                'venda': str(row.get('Venda', '')),
                                'forma_pagamento': str(row.get('FormaPagamento', '')),
                                'aplicativo': str(row.get('Aplicativo', '')),
                                'operador': str(row.get('Operador', '')),
                                'data_hora_transacao': data_transacao,
                                'id_pedido_externo': str(row.get('IdPedidoExterno', '')),
                                'codigo_loja': str(row.get('CodigoLoja', '')),
                                'valor_pagamento': row.get('ValorPagamento', 0.0),
                                'nr_abertura': str(row.get('NrAbertura', '')),
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

                    for i in range(len(df_csv)-1):
                        if df_csv.loc[i, 'CodigoLoja'] == df_csv.loc[i+1, 'CodigoLoja']:
                            fechamento_anterior = df_csv.loc[i+1, 'DataHoraFechamento']
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

                        chave_turno = f"TURNO-{cod_loja}-{nr_abert}"
                        VendaSWFast.objects.update_or_create(
                            chave_composta=chave_turno,
                            defaults={
                                'codigo_loja': cod_loja, 'nr_abertura': nr_abert,
                                'dthr_abert_cx': dt_abert, 'dthr_encerr_cx': dt_fech,
                                'forma_pagamento': 'ABERTURA_CAIXA', 'venda': 'INFO_TURNO', 'valor_pagamento': 0.0,
                            }
                        )
                        VendaSWFast.objects.filter(codigo_loja=cod_loja, nr_abertura=nr_abert).exclude(chave_composta=chave_turno).update(
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
                    df.rename(columns={"N_DE_PARCELAS": "QTD_DE_PARCELAS", "VALOR_LIQUIDO": "VALOR_LÍQUIDO", "DESCONTO_DE_ANTECIPACAO": "DESCONTO_DE_ANTECIPAÇÃO"}, inplace=True)
                    df["DATA_DA_VENDA"] = pd.to_datetime(df.get("DATA_DA_VENDA"), dayfirst=True, errors="coerce")

                    contador = 0
                    for _, row in df.iterrows():
                        stone_id = str(row.get('STONE_ID', ''))
                        if stone_id == 'nan' or stone_id == '': continue
                        
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
                        "ID COMPLETO DO PEDIDO": "ID DO PEDIDO", "ID CURTO DO PEDIDO": "N° PEDIDO",
                        "DATA E HORA DO PEDIDO": "DATA", "NOME DA LOJA": "RESTAURANTE", "ID DA LOJA": "ID DO RESTAURANTE",
                        "TAXA DE ENTREGA PAGA PELO CLIENTE (R$)": "TAXA DE ENTREGA", "VALOR DOS ITENS (R$)": "VALOR DOS ITENS",
                        "INCENTIVO PROMOCIONAL DO IFOOD (R$)": "INCENTIVO PROMOCIONAL DO IFOOD",
                        "INCENTIVO PROMOCIONAL DA LOJA (R$)": "INCENTIVO PROMOCIONAL DA LOJA",
                        "TAXA DE SERVIÇO (R$)": "TAXA DE SERVIÇO", "VALOR LIQUIDO (R$)": "TOTAL DO PARCEIRO", 
                        "TOTAL PAGO PELO CLIENTE (R$)": "TOTAL DO PEDIDO", "FORMA DE PAGAMENTO": "FORMAS DE PAGAMENTO"
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

                    contador = 0
                    for _, row in df.iterrows():
                        id_pedido = str(row.get('ID DO PEDIDO', '')).strip()
                        if id_pedido == 'nan' or id_pedido == '': continue
                            
                        data_pedido = row['DATA'] if pd.notna(row['DATA']) else None
                        
                        # Tratamento seguro de strings para evitar "nan"
                        formas_pgto = row.get('FORMAS DE PAGAMENTO')
                        origem_canc = row.get('ORIGEM DO CANCELAMENTO')

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
# 🔄 VIEW DE SINCRONIZAÇÃO DE PAGAMENTOS
# ==========================================
@login_required(login_url='login')
def sincronizar_formas_pagamento(request):
    if request.method == 'POST':
        try:
            # Pega todas as combinações reais que vieram das vendas importadas
            combinacoes_swfast = VendaSWFast.objects.exclude(
                forma_pagamento__isnull=True
            ).exclude(
                forma_pagamento=''
            ).values('forma_pagamento', 'codigo_loja', 'aplicativo').distinct()

            novas_insercoes = 0

            for combo in combinacoes_swfast:
                forma = str(combo.get('forma_pagamento', '')).strip()
                loja = str(combo.get('codigo_loja', '')).strip()
                app = str(combo.get('aplicativo', '')).strip()

                # 1. Verifica se ESSA exata combinação (Forma + Loja + App) já existe
                existe = FormaPagamento.objects.filter(
                    forma_pagamento=forma,
                    codigo_loja=loja,
                    aplicativo=app
                ).exists()

                if not existe:
                    # 2. PROCURA UMA "COLA" (uma configuração que você já preencheu antes para essa mesma forma, 
                    # mesmo que seja de outra loja ou da época que a loja ficava em branco)
                    referencia = FormaPagamento.objects.filter(
                        forma_pagamento=forma,
                        aplicativo=app
                    ).exclude(especific_form_pgto='').first()

                    # 3. Se achou, copia o grupo (ex: 'CARTAO'). Se não achou, deixa em branco para você preencher.
                    especificacao_herdada = referencia.especific_form_pgto if referencia else ''

                    # Cria o registro novo já com a configuração copiada!
                    FormaPagamento.objects.create(
                        forma_pagamento=forma,
                        codigo_loja=loja,
                        aplicativo=app,
                        especific_form_pgto=especificacao_herdada
                    )
                    novas_insercoes += 1

            if novas_insercoes > 0:
                messages.success(request, f"Sucesso! {novas_insercoes} configurações de loja sincronizadas automaticamente.")
            else:
                messages.info(request, "Todas as formas de pagamento e lojas já estão perfeitamente sincronizadas.")
                
        except Exception as e:
            messages.error(request, f"Erro ao sincronizar: {e}")
            
        return redirect('formas_pagamento')

    # A ordenação aqui ajuda a agrupar visualmente por loja na tela
    formas = FormaPagamento.objects.all().order_by('codigo_loja', 'forma_pagamento')
    return render(request, 'importacoes/formas_pagamento.html', {'formas': formas})

# ==========================================
# 📊 VIEW E LÓGICA DA CONFERÊNCIA
# ==========================================
DB_PATH = "db.sqlite3"

def carregar_lojas(usuario):
    """Carrega apenas as lojas que o usuário logado tem permissão para ver"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT codigo_loja FROM importacoes_vendaswfast WHERE codigo_loja IS NOT NULL ORDER BY codigo_loja")
        lojas_importadas = [str(row[0]) for row in cursor.fetchall()]
        conn.close()

        # Se for um SuperUsuário (você) ou tiver perfil ADMIN, vê todas as lojas importadas
        if usuario.is_superuser or (hasattr(usuario, 'perfil') and usuario.perfil.tipo_acesso == 'ADMIN'):
            return lojas_importadas
        
        # Se for OPERADOR, cruza as lojas importadas com as que ele tem permissão
        elif hasattr(usuario, 'perfil') and usuario.perfil.tipo_acesso == 'OPERADOR':
            # Pega os IDs das lojas permitidas cadastradas na tabela Empresa
            permitidas = [str(emp.ncad_swfast) for emp in usuario.perfil.lojas_permitidas.all()]
            # Devolve apenas as lojas que estão importadas E que ele tem permissão
            return [loja for loja in lojas_importadas if loja in permitidas]
        
        # Se não tiver perfil configurado, por segurança, não vê nenhuma
        return []

    except Exception as e:
        print(f"Erro ao carregar lojas: {e}")
        return []

def carregar_aberturas(codigo_loja):
    if not codigo_loja: return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # O CAST garante que a ordem numérica seja exata (ex: 3624 antes do 3625)
        cursor.execute("""
            SELECT DISTINCT nr_abertura 
            FROM importacoes_vendaswfast 
            WHERE codigo_loja = ? AND nr_abertura IS NOT NULL
            ORDER BY CAST(nr_abertura AS INTEGER)
        """, (codigo_loja,))
        aberturas = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        return aberturas
    except Exception as e:
        print(f"Erro ao carregar aberturas: {e}")
        return []

def buscar_dados_conferencia(codigo_loja, nr_abertura, incluir_dinheiro=False):
    conn = sqlite3.connect(DB_PATH)
    
    query = """
        SELECT
            fp.especific_form_pgto AS RESUMO,
            SUM(sw.valor_pagamento) AS rel_swfast,

            CASE
                WHEN fp.especific_form_pgto = 'CARTAO' THEN COALESCE((
                    SELECT SUM(c.valor_bruto) FROM importacoes_transacaostone c
                    WHERE c.data_venda BETWEEN 
                        (SELECT DATETIME(MIN(sw2.dthr_abert_cx), '+1 hour') FROM importacoes_vendaswfast sw2 WHERE sw2.codigo_loja = ? AND sw2.nr_abertura = ?)
                        AND (SELECT DATETIME(MAX(sw3.dthr_encerr_cx), '+1 hour') FROM importacoes_vendaswfast sw3 WHERE sw3.codigo_loja = ? AND sw3.nr_abertura = ?)
                    AND c.stonecode = emp.ncad_cartoes
                ), 0) - COALESCE((
                    SELECT SUM(i.total_pedido) FROM importacoes_pedidoifood i
                    WHERE LOWER(TRIM(i.id_pedido)) IN (
                        SELECT LOWER(TRIM(sw4.id_pedido_externo)) FROM importacoes_vendaswfast sw4
                        WHERE LOWER(sw4.aplicativo) = 'ifood' AND sw4.codigo_loja = ? AND sw4.nr_abertura = ?
                    ) AND i.id_restaurante = emp.ncad_ifood
                ), 0)

                WHEN fp.especific_form_pgto = 'PIX' THEN 0 /* PIX MERCADO PAGO */

                WHEN fp.especific_form_pgto = 'IFOOD' THEN COALESCE((
                    SELECT SUM(i.vlr_pedido_sw) FROM importacoes_pedidoifood i
                    WHERE LOWER(TRIM(i.id_pedido)) IN (
                        SELECT LOWER(TRIM(sw5.id_pedido_externo)) FROM importacoes_vendaswfast sw5
                        WHERE LOWER(sw5.aplicativo) = 'ifood' AND sw5.codigo_loja = ? AND sw5.nr_abertura = ?
                    ) AND LOWER(TRIM(i.formas_pagamento)) NOT IN ('dinheiro') 
                      AND i.id_restaurante = emp.ncad_ifood
                      AND LOWER(TRIM(i.formas_pagamento)) NOT LIKE '%entrega%'
                ), 0)

                WHEN fp.especific_form_pgto = 'DINHEIRO' THEN COALESCE((
                    SELECT mov.valor_dinheiro_envelope FROM tbl_movcaixa mov WHERE mov.codigo_loja = ? AND mov.nr_abertura = ?
                ), 0)
                ELSE 0
            END AS Rel_importados

        FROM importacoes_vendaswfast sw
        LEFT JOIN tbl_formapagamento fp 
            ON LOWER(TRIM(sw.forma_pagamento)) = LOWER(TRIM(fp.forma_pagamento))
            AND sw.codigo_loja = fp.codigo_loja
            AND LOWER(TRIM(sw.aplicativo)) = LOWER(TRIM(fp.aplicativo))
        LEFT JOIN tbl_empresa emp ON emp.ncad_swfast = sw.codigo_loja
        WHERE sw.codigo_loja = ? AND sw.nr_abertura = ?
    """
    if not incluir_dinheiro: query += " AND UPPER(TRIM(sw.forma_pagamento)) != 'DINHEIRO'"
    query += " GROUP BY fp.especific_form_pgto"

    params = [codigo_loja, nr_abertura, codigo_loja, nr_abertura, codigo_loja, nr_abertura, codigo_loja, nr_abertura, codigo_loja, nr_abertura, codigo_loja, nr_abertura]

    query_cancelados = """
        SELECT i.nr_pedido, i.data, i.formas_pagamento, i.total_pedido FROM importacoes_pedidoifood i
        WHERE LOWER(TRIM(i.id_pedido)) IN (
            SELECT LOWER(TRIM(sw.id_pedido_externo)) FROM importacoes_vendaswfast sw
            WHERE LOWER(sw.aplicativo) = 'ifood' AND sw.codigo_loja = ? AND sw.nr_abertura = ?
        ) AND i.origem_cancelamento != ''
    """

    query_incentivo = """       
        SELECT SUM(i.incentivo_ifood) FROM importacoes_pedidoifood i
        WHERE LOWER(TRIM(i.id_pedido)) IN (
            SELECT LOWER(TRIM(sw.id_pedido_externo)) FROM importacoes_vendaswfast sw
            WHERE LOWER(sw.aplicativo) = 'ifood' AND sw.codigo_loja = ? AND sw.nr_abertura = ?
        ) AND LOWER(TRIM(i.formas_pagamento)) = 'dinheiro'
    """

    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        df = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
        
        cursor.execute(query_cancelados, [codigo_loja, nr_abertura])
        df_cancelados = pd.DataFrame(cursor.fetchall(), columns=[col[0] for col in cursor.description])
        
        cursor.execute(query_incentivo, [codigo_loja, nr_abertura])
        res_incentivo = cursor.fetchone()
        valor_incentivo = res_incentivo[0] if res_incentivo and res_incentivo[0] else 0.0
    except Exception as e:
        print(f"Erro SQL: {e}")
        df, df_cancelados, valor_incentivo = pd.DataFrame(), pd.DataFrame(), 0.0
    finally:
        conn.close()

    return df, df_cancelados, valor_incentivo

@login_required(login_url='login')
def pagina_conferencia(request):
    context = {'lojas': carregar_lojas(request.user), 'codigo_loja_selecionada': None, 'nr_abertura_selecionada': None, 'aberturas': [], 'resultados': None}
    
    if request.method == 'GET' and 'codigo_loja' in request.GET:
        codigo_loja = request.GET.get('codigo_loja')
        nr_abertura = request.GET.get('nr_abertura')
        context['codigo_loja_selecionada'] = codigo_loja
        context['aberturas'] = carregar_aberturas(codigo_loja)
        
        if nr_abertura:
            context['nr_abertura_selecionada'] = nr_abertura
            # ==========================================
            # NOVA LÓGICA: Buscar a data do caixa
            # ==========================================
            primeira_venda = VendaSWFast.objects.filter(
                codigo_loja=codigo_loja, 
                nr_abertura=nr_abertura, 
                data_hora_transacao__isnull=False
            ).order_by('data_hora_transacao').first()
            
            if primeira_venda and primeira_venda.data_hora_transacao:
                context['data_caixa_selecionada'] = primeira_venda.data_hora_transacao.strftime('%d/%m/%Y')
            # ==========================================
            df_res, df_canc, val_inc = buscar_dados_conferencia(codigo_loja, nr_abertura, request.GET.get('incluir_dinheiro') == 'on')
            
            if not df_res.empty:
                df_res = pd.concat([df_res, pd.DataFrame({"RESUMO": ["INCENTIVO IFOOD A RECEBER DINHEIRO"], "rel_swfast": [0.0], "Rel_importados": [val_inc]})], ignore_index=True)
                df_res["Rel_importados"] = pd.to_numeric(df_res["Rel_importados"], errors='coerce').fillna(0)
                df_res["rel_swfast"] = pd.to_numeric(df_res["rel_swfast"], errors='coerce').fillna(0)
                
                # CORREÇÃO AQUI: Nome da coluna alterado para 'diferenca' (sem ç e minúsculo)
                df_res["diferenca"] = df_res["Rel_importados"] - df_res["rel_swfast"]
                
                # Atualizando o Subtotal com o novo nome
                df_res = pd.concat([df_res, pd.DataFrame({
                    "RESUMO": ["SUBTOTAL"], 
                    "Rel_importados": [df_res["Rel_importados"].sum()], 
                    "rel_swfast": [df_res["rel_swfast"].sum()], 
                    "diferenca": [df_res["diferenca"].sum()]
                })], ignore_index=True)
                
                context['resultados'] = df_res.fillna('').to_dict('records')
                context['cancelados'] = df_canc.to_dict('records')

    return render(request, 'importacoes/conferencia.html', context)

# ==========================================
# 📥 EXPORTAÇÃO DO RELATÓRIO ANALÍTICO
# ==========================================
@login_required(login_url='login')
def exportar_analitico_excel(request):
    codigo_loja = request.GET.get('codigo_loja')
    nr_abertura = request.GET.get('nr_abertura')

    if not codigo_loja or not nr_abertura:
        messages.error(request, "Parâmetros inválidos para o relatório analítico.")
        return redirect('conferencia_caixa')

    conn = sqlite3.connect(DB_PATH)

    # 1. Analítico iFood (Linha a Linha) - Agrupando pagamentos e espelhando o Sintético
    query_ifood = """
        SELECT
            sw.data_hora_transacao AS "Data SWFast",
            sw.venda AS "Nº Venda SWFast",
            sw.id_pedido_externo AS "ID Pedido iFood",
            MAX(sw.forma_pagamento) AS "Forma Pgto SWFast",
            SUM(sw.valor_pagamento) AS "Valor SWFast",
            COALESCE(i.vlr_pedido_sw, 0) AS "iFood Repasse",
            COALESCE(i.incentivo_ifood, 0) AS "iFood Incentivo",
            COALESCE(i.vlr_pedido_sw, 0) AS "Total iFood (Conciliação)",
            (COALESCE(i.vlr_pedido_sw, 0) - SUM(sw.valor_pagamento)) AS "Diferença"
        FROM importacoes_vendaswfast sw
        LEFT JOIN importacoes_pedidoifood i ON LOWER(TRIM(sw.id_pedido_externo)) = LOWER(TRIM(i.id_pedido))
        WHERE sw.codigo_loja = ? AND sw.nr_abertura = ? AND LOWER(sw.aplicativo) = 'ifood'
        GROUP BY 
            sw.data_hora_transacao, sw.venda, sw.id_pedido_externo, i.vlr_pedido_sw, i.incentivo_ifood
        ORDER BY sw.data_hora_transacao
    """
    df_ifood = pd.read_sql(query_ifood, conn, params=[codigo_loja, nr_abertura])

    # 2. Analítico Cartões no SWFast
    query_cartoes_sw = """
        SELECT
            sw.data_hora_transacao AS "Data SWFast",
            sw.venda AS "Nº Venda",
            sw.forma_pagamento AS "Forma Pgto SWFast",
            sw.valor_pagamento AS "Valor Registrado no Caixa"
        FROM importacoes_vendaswfast sw
        LEFT JOIN tbl_formapagamento fp 
            ON LOWER(TRIM(sw.forma_pagamento)) = LOWER(TRIM(fp.forma_pagamento))
            AND sw.codigo_loja = fp.codigo_loja
            AND LOWER(TRIM(sw.aplicativo)) = LOWER(TRIM(fp.aplicativo))
        WHERE sw.codigo_loja = ? AND sw.nr_abertura = ? AND fp.especific_form_pgto = 'CARTAO'
        ORDER BY sw.data_hora_transacao
    """
    df_cartoes_sw = pd.read_sql(query_cartoes_sw, conn, params=[codigo_loja, nr_abertura])

    # 3. Analítico Cartões na Stone (Intervalo de Horário do Caixa)
    query_stone = """
        SELECT
            c.data_venda AS "Data Venda Stone",
            c.bandeira AS "Bandeira",
            c.produto AS "Produto",
            c.qtd_parcelas AS "Parcelas",
            c.valor_bruto AS "Valor Bruto",
            c.desconto_mdr AS "Taxa MDR",
            c.valor_liquido AS "Valor Líquido"
        FROM importacoes_transacaostone c
        JOIN tbl_empresa emp ON c.stonecode = emp.ncad_cartoes
        WHERE emp.ncad_swfast = ?
        AND c.data_venda BETWEEN 
            (SELECT DATETIME(MIN(sw2.dthr_abert_cx), '+1 hour') FROM importacoes_vendaswfast sw2 WHERE sw2.codigo_loja = ? AND sw2.nr_abertura = ?)
            AND 
            (SELECT DATETIME(MAX(sw3.dthr_encerr_cx), '+1 hour') FROM importacoes_vendaswfast sw3 WHERE sw3.codigo_loja = ? AND sw3.nr_abertura = ?)
        ORDER BY c.data_venda
    """
    df_stone = pd.read_sql(query_stone, conn, params=[codigo_loja, codigo_loja, nr_abertura, codigo_loja, nr_abertura])

    # ==========================================
    # 4. NOVO: iFood NÃO Integrado (Furo de Caixa)
    # ==========================================
    query_nao_integrado = """
        SELECT
            i.data AS "Data no iFood",
            i.id_pedido AS "ID Pedido iFood",
            COALESCE(i.vlr_pedido_sw, 0) AS "iFood Repasse",
            COALESCE(i.incentivo_ifood, 0) AS "iFood Incentivo",
            (COALESCE(i.vlr_pedido_sw, 0) + COALESCE(i.incentivo_ifood, 0)) AS "Valor Total Oculto do Caixa"
        FROM importacoes_pedidoifood i
        WHERE i.data BETWEEN 
            (SELECT DATETIME(MIN(sw.dthr_abert_cx)) FROM importacoes_vendaswfast sw WHERE sw.codigo_loja = ? AND sw.nr_abertura = ?)
            AND 
            (SELECT DATETIME(MAX(sw.dthr_encerr_cx)) FROM importacoes_vendaswfast sw WHERE sw.codigo_loja = ? AND sw.nr_abertura = ?)
        AND LOWER(TRIM(i.id_pedido)) NOT IN (
            SELECT LOWER(TRIM(sw2.id_pedido_externo))
            FROM importacoes_vendaswfast sw2
            WHERE sw2.id_pedido_externo IS NOT NULL AND sw2.id_pedido_externo != ''
        )
        ORDER BY i.data
    """
    # Nota: Assumi que o nome da sua coluna de data na tabela do iFood é 'data_pedido'. 
    # Se for diferente no seu models.py, é só trocar ali no 'i.data_pedido'.
    df_nao_integrado = pd.read_sql(query_nao_integrado, conn, params=[codigo_loja, nr_abertura, codigo_loja, nr_abertura])

    conn.close()

    # Gerar o arquivo Excel com a nova aba
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_ifood.to_excel(writer, sheet_name='Analítico iFood (Integrados)', index=False)
        df_nao_integrado.to_excel(writer, sheet_name='iFood NÃO Integrado (Furos)', index=False) # <--- NOVA ABA
        df_cartoes_sw.to_excel(writer, sheet_name='Cartões Passados no Caixa', index=False)
        df_stone.to_excel(writer, sheet_name='Transações Reais Stone', index=False)

    output.seek(0)
    
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    nome_arquivo = f'Analitico_Caixa_{codigo_loja}_Turno_{nr_abertura}.xlsx'
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
    
    return response
# ==========================================
# VIEW DE LOGOUT CUSTOMIZADA
# ==========================================
def sair_do_sistema(request):
    logout(request) # Destrói a sessão do usuário na hora
    return redirect('login') # Joga ele de volta para a tela de login