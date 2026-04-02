#!/usr/bin/env python
"""
Script para popular os 13 eventos da Empresa Modelo com base em EVENTOS_RESTAURANTE.md

Eventos a importar:
1. FOLHA_PAGAMENTO_MENSAL
2. COMPRA_ALIMENTOS_BEBIDAS
3. VENDA_REFEICOES
4. DESPESA_MATERIAL_CONSUMO
5. COMPRA_EQUIPAMENTO_KICHEN
6. DESPESA_ALUGUEL_LOCACAO
7. DESPESA_UTILIDADES
8. DEPRECIACAO_MENSAL
9. DESPESA_BENEFICIOS_FUNCIONARIOS
10. DEVOLUCAO_CLIENTE
11. APLICACAO_FUNDO_RENDA_FIXA
12. RECEITA_JUROS_APLICACAO
13. PAGAMENTO_FORNECEDOR
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_caixa.settings')
django.setup()

from contabilidade.models import TipoEvento

# Definir eventos conforme EVENTOS_RESTAURANTE.md
EVENTOS_RESTAURANTE = [
    {
        'codigo': 'FOLHA_PAGAMENTO_MENSAL',
        'descricao': 'Lançamento mensal de folha de pagamento com retenções',
        'modulo_origem': 'RH',
        'eh_modelo': True,
    },
    {
        'codigo': 'COMPRA_ALIMENTOS_BEBIDAS',
        'descricao': 'Compra a prazo ou à vista de alimentos e bebidas para cozinha',
        'modulo_origem': 'COMPRAS',
        'eh_modelo': True,
    },
    {
        'codigo': 'VENDA_REFEICOES',
        'descricao': 'Venda diária de refeições (entrada de receita)',
        'modulo_origem': 'VENDAS',
        'eh_modelo': True,
    },
    {
        'codigo': 'DESPESA_MATERIAL_CONSUMO',
        'descricao': 'Compra de materiais consumíveis (limpeza, embalagem, etc)',
        'modulo_origem': 'DESPESAS',
        'eh_modelo': True,
    },
    {
        'codigo': 'COMPRA_EQUIPAMENTO_KICHEN',
        'descricao': 'Aquisição de equipamento para cozinha (fogão, forno, etc)',
        'modulo_origem': 'IMOBILIZADO',
        'eh_modelo': True,
    },
    {
        'codigo': 'DESPESA_ALUGUEL_LOCACAO',
        'descricao': 'Pagamento mensal de aluguel do espaço',
        'modulo_origem': 'DESPESAS',
        'eh_modelo': True,
    },
    {
        'codigo': 'DESPESA_UTILIDADES',
        'descricao': 'Pagamento de contas de energia, água e gás',
        'modulo_origem': 'DESPESAS',
        'eh_modelo': True,
    },
    {
        'codigo': 'DEPRECIACAO_MENSAL',
        'descricao': 'Registro mensal de depreciação de equipamentos',
        'modulo_origem': 'AJUSTES',
        'eh_modelo': True,
    },
    {
        'codigo': 'DESPESA_BENEFICIOS_FUNCIONARIOS',
        'descricao': 'Lançamento de benefícios retidos e fornecidos aos funcionários',
        'modulo_origem': 'RH',
        'eh_modelo': True,
    },
    {
        'codigo': 'DEVOLUCAO_CLIENTE',
        'descricao': 'Recebimento de devolução de cliente (redução de venda)',
        'modulo_origem': 'VENDAS',
        'eh_modelo': True,
    },
    {
        'codigo': 'APLICACAO_FUNDO_RENDA_FIXA',
        'descricao': 'Aplicação de sobra de caixa em investimento',
        'modulo_origem': 'FINANCEIRA',
        'eh_modelo': True,
    },
    {
        'codigo': 'RECEITA_JUROS_APLICACAO',
        'descricao': 'Recebimento de juros de investimento',
        'modulo_origem': 'FINANCEIRA',
        'eh_modelo': True,
    },
    {
        'codigo': 'PAGAMENTO_FORNECEDOR',
        'descricao': 'Liquidação de compra a prazo registrada anteriormente',
        'modulo_origem': 'COMPRAS',
        'eh_modelo': True,
    },
]


def popular_eventos():
    """Popula os 13 eventos na Empresa Modelo"""

    criados = 0
    duplicados = 0

    print("\n" + "="*60)
    print("POPULANDO EVENTOS DA EMPRESA MODELO")
    print("="*60 + "\n")

    for evento_data in EVENTOS_RESTAURANTE:
        codigo = evento_data['codigo']

        # Verificar se já existe
        evento_existe = TipoEvento.objects.filter(codigo=codigo).exists()

        if evento_existe:
            print(f"[EXISTE] {codigo}")
            duplicados += 1
        else:
            TipoEvento.objects.create(**evento_data)
            print(f"[CRIADO] {codigo}")
            criados += 1

    print("\n" + "="*60)
    print(f"RESUMO: {criados} criados, {duplicados} já existiam")
    print("="*60 + "\n")

    # Listar todos os eventos marcados com eh_modelo=True
    print("\nEventos Marcados como Modelo:")
    print("-"*60)
    eventos_modelo = TipoEvento.objects.filter(eh_modelo=True).order_by('modulo_origem', 'codigo')
    for i, evento in enumerate(eventos_modelo, 1):
        print(f"{i:2d}. {evento.codigo:40s} | {evento.modulo_origem:15s}")

    print(f"\nTotal: {eventos_modelo.count()} eventos de modelo")


if __name__ == '__main__':
    popular_eventos()
