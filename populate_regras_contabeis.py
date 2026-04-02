#!/usr/bin/env python
"""
Script para popular as Regras Contábeis dos 13 eventos de restaurante.
Mapeia cada TipoEvento para RegraContabil com partidas (débitos + créditos).

Baseado em EVENTOS_RESTAURANTE.md usando contas analiticas da Empresa Modelo.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_caixa.settings')
django.setup()

from contabilidade.models import TipoEvento, RegraContabil, PartidaRegra, ContaAnalitica
from core.models import Empresa
from django.db import transaction

# Mapa de códigos de contas usando as contas analiticas que existem
REGRAS_EVENTOS = {
    'FOLHA_PAGAMENTO_MENSAL': {
        'descricao': 'Folha de pagamento mensal com retenções',
        'partidas': [
            ('D', '5.1.1.1.0001', 1, 'Salários - Gerenciamento'),
            ('C', '2.1.3.1.0001', 2, 'Salários a Pagar'),
            ('C', '2.1.3.2.0001', 3, 'FGTS a Pagar'),
            ('C', '2.1.3.3.0001', 4, 'INSS a Pagar'),
        ]
    },
    'COMPRA_ALIMENTOS_BEBIDAS': {
        'descricao': 'Compra a prazo ou à vista de alimentos e bebidas',
        'partidas': [
            ('D', '1.1.3.1.0001', 1, 'Estoque - Alimentos'),
            ('D', '1.1.3.2.0001', 2, 'Estoque - Bebidas'),
            ('D', '1.1.3.3.0001', 3, 'Estoque - Insumos'),
            ('C', '1.1.1.1.0001', 4, 'Caixa'),
            ('C', '2.1.1.1.0001', 5, 'Fornecedores de Alimentos'),
        ]
    },
    'VENDA_REFEICOES': {
        'descricao': 'Venda diária de refeições',
        'partidas': [
            ('D', '1.1.1.1.0001', 1, 'Caixa'),
            ('D', '1.1.2.3.0001', 2, 'Clientes - Cartoes de Credito'),
            ('D', '1.1.2.2.0001', 3, 'Clientes - Pessoa Juridica'),
            ('D', '1.1.2.1.0001', 4, 'Clientes - Consumidor Final'),
            ('D', '4.1.1.1.0001', 5, 'CMV - Proteinas'),
            ('C', '3.1.1.1.0001', 6, 'Vendas de Refeicoes'),
            ('C', '1.1.3.1.0001', 7, 'Estoque - Alimentos'),
        ]
    },
    'DESPESA_MATERIAL_CONSUMO': {
        'descricao': 'Materiais consumíveis (limpeza, embalagem)',
        'partidas': [
            ('D', '5.5.1.0001', 1, 'Materiais de Escritorio'),
            ('D', '5.2.5.0001', 2, 'Limpeza e Higiene'),
            ('D', '4.1.3.2.0001', 3, 'CMV - Descartaveis'),
            ('C', '1.1.1.2.0001', 4, 'Banco - Conta Corrente'),
        ]
    },
    'COMPRA_EQUIPAMENTO_KICHEN': {
        'descricao': 'Aquisição de equipamento para cozinha',
        'partidas': [
            ('D', '1.2.2.2.0001', 1, 'Equipamentos'),
            ('D', '1.2.2.2.0001', 2, 'Equipamentos (Frete)'),
            ('C', '1.1.1.2.0001', 3, 'Banco - Conta Corrente'),
            ('C', '2.2.1.2.0001', 4, 'Financiamentos LP'),
        ]
    },
    'DESPESA_ALUGUEL_LOCACAO': {
        'descricao': 'Aluguel mensal do espaço',
        'partidas': [
            ('D', '5.2.1.0001', 1, 'Aluguel do Estabelecimento'),
            ('D', '2.1.4.2.0001', 2, 'ISS a Pagar'),
            ('C', '1.1.1.2.0001', 3, 'Banco - Conta Corrente'),
        ]
    },
    'DESPESA_UTILIDADES': {
        'descricao': 'Contas de energia, água e gás',
        'partidas': [
            ('D', '5.3.1.0001', 1, 'Energia Eletrica'),
            ('D', '5.3.2.0001', 2, 'Agua e Esgoto'),
            ('D', '5.3.3.0001', 3, 'Gas'),
            ('D', '2.1.4.1.0001', 4, 'ICMS a Pagar'),
            ('C', '1.1.1.2.0001', 5, 'Banco - Conta Corrente'),
            ('C', '2.1.2.2.0001', 6, 'Agua e Energia a Pagar'),
        ]
    },
    'DEPRECIACAO_MENSAL': {
        'descricao': 'Depreciação mensal de equipamentos',
        'partidas': [
            ('D', '5.6.1.0001', 1, 'Manutencao de Equipamentos'),
            ('C', '1.2.2.3.0001', 2, 'Depreciacoes Acumuladas'),
        ]
    },
    'DESPESA_BENEFICIOS_FUNCIONARIOS': {
        'descricao': 'Vale Refeição e Vale Transporte',
        'partidas': [
            ('D', '5.1.3.1.0001', 1, 'Vale Refeicao'),
            ('D', '5.1.3.2.0001', 2, 'Vale Transporte'),
            ('C', '2.1.3.1.0001', 3, 'Salários a Pagar'),
            ('C', '1.1.1.2.0001', 4, 'Banco - Conta Corrente'),
        ]
    },
    'DEVOLUCAO_CLIENTE': {
        'descricao': 'Devolução de cliente (redução de venda)',
        'partidas': [
            ('D', '3.1.3.1.0001', 1, 'Devolucoes de Vendas'),
            ('D', '1.1.3.1.0001', 2, 'Estoque - Alimentos'),
            ('C', '1.1.1.1.0001', 3, 'Caixa'),
            ('C', '4.1.1.1.0001', 4, 'CMV - Proteinas'),
        ]
    },
    'APLICACAO_FUNDO_RENDA_FIXA': {
        'descricao': 'Aplicação em investimento (CDB, etc)',
        'partidas': [
            ('D', '1.1.1.3.0001', 1, 'Banco - Aplicacoes'),
            ('D', '5.7.1.0001', 2, 'Juros Pagos'),
            ('C', '1.1.1.2.0001', 3, 'Banco - Conta Corrente'),
        ]
    },
    'RECEITA_JUROS_APLICACAO': {
        'descricao': 'Recebimento de juros de investimento',
        'partidas': [
            ('D', '1.1.1.2.0001', 1, 'Banco - Conta Corrente'),
            ('D', '2.1.4.4.0001', 2, 'Imposto de Renda a Pagar'),
            ('C', '3.2.1.1.0001', 3, 'Juros Recebidos'),
        ]
    },
    'PAGAMENTO_FORNECEDOR': {
        'descricao': 'Liquidação de compra a prazo',
        'partidas': [
            ('D', '2.1.1.1.0001', 1, 'Fornecedores de Alimentos'),
            ('C', '1.1.1.2.0001', 2, 'Banco - Conta Corrente'),
            ('C', '3.2.1.2.0001', 3, 'Descontos Obtidos'),
        ]
    },
}


def popular_regras_contabeis():
    """Popula as regras contábeis para todos os eventos de restaurante"""

    print("\n" + "="*70)
    print("POPULANDO REGRAS CONTABEIS DOS EVENTOS DE RESTAURANTE")
    print("="*70 + "\n")

    # Buscar Empresa Modelo
    try:
        empresa_modelo = Empresa.objects.get(id_empresa=4)
        print(f"[OK] Empresa Modelo encontrada: {empresa_modelo.descricao}")
    except Empresa.DoesNotExist:
        print("[ERRO] Empresa Modelo (ID=4) nao encontrada!")
        return

    print(f"[OK] {ContaAnalitica.objects.filter(loja=empresa_modelo).count()} contas analiticas disponiveis\n")

    criadas = 0
    erro_conta = 0
    evento_sem_regra = 0

    with transaction.atomic():
        for codigo_evento, regra_data in REGRAS_EVENTOS.items():
            print(f"[PROCESSANDO] {codigo_evento}")

            # Buscar tipo de evento
            try:
                tipo_evento = TipoEvento.objects.get(codigo=codigo_evento)
            except TipoEvento.DoesNotExist:
                print(f"  [ERRO] Evento {codigo_evento} nao existe\n")
                evento_sem_regra += 1
                continue

            # Criar regra contábil
            regra, criada = RegraContabil.objects.get_or_create(
                loja=empresa_modelo,
                tipo_evento=tipo_evento,
                descricao=regra_data['descricao'],
                defaults={'ativa': True}
            )

            if criada:
                print(f"  [CRIADA] Regra para {codigo_evento}")
            else:
                print(f"  [EXISTE] Regra já criada")
                # Limpar partidas antigas
                regra.partidas.all().delete()

            # Criar partidas
            partidas_criadas = 0
            for tipo, codigo_conta, ordem, descricao in regra_data['partidas']:
                try:
                    # Buscar conta analítica
                    conta = ContaAnalitica.objects.get(
                        loja=empresa_modelo,
                        codigo_classificacao=codigo_conta
                    )

                    # Criar partida (usar get_or_create para evitar duplicatas)
                    PartidaRegra.objects.get_or_create(
                        regra=regra,
                        tipo=tipo,
                        conta=conta,
                        defaults={'ordem': ordem}
                    )
                    partidas_criadas += 1

                except ContaAnalitica.DoesNotExist:
                    print(f"    [AVISO] Conta {codigo_conta} nao encontrada para {tipo}")
                    erro_conta += 1

            print(f"  [{partidas_criadas} partidas criadas]\n")
            criadas += 1

    print("="*70)
    print(f"RESUMO:")
    print(f"  Regras criadas: {criadas}")
    print(f"  Eventos sem regra: {evento_sem_regra}")
    print(f"  Contas nao encontradas: {erro_conta}")
    print("="*70 + "\n")

    # Listar regras criadas
    print("Regras Contabeis Criadas:")
    print("-"*70)
    regras = RegraContabil.objects.filter(loja=empresa_modelo).select_related('tipo_evento').order_by('tipo_evento__modulo_origem', 'tipo_evento__codigo')
    for i, regra in enumerate(regras, 1):
        partidas_count = regra.partidas.count()
        debitos_count = regra.partidas.filter(tipo='D').count()
        creditos_count = regra.partidas.filter(tipo='C').count()
        print(f"{i:2d}. {regra.tipo_evento.codigo:40s} | {debitos_count} D + {creditos_count} C = {partidas_count} partidas")

    print(f"\nTotal: {regras.count()} regras")


if __name__ == '__main__':
    popular_regras_contabeis()
