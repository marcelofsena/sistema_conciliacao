#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para inserir as 82 contas restantes do plano de contas.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_caixa.settings')
django.setup()

from contabilidade.models import ContaSintetica, TipoConta
from core.models import Empresa

# Lista com as 82 contas restantes
contas_restantes = [
    # PASSIVO (28 contas)
    ("2", "PASSIVO", "PASSIVO", None),
    ("2.1", "PASSIVO CIRCULANTE", "PASSIVO", "2"),
    ("2.1.1", "Fornecedores", "PASSIVO", "2.1"),
    ("2.1.1.1", "Fornecedores de Alimentos", "PASSIVO", "2.1.1"),
    ("2.1.1.2", "Fornecedores de Bebidas", "PASSIVO", "2.1.1"),
    ("2.1.1.3", "Fornecedores de Insumos", "PASSIVO", "2.1.1"),
    ("2.1.2", "Contas a Pagar", "PASSIVO", "2.1"),
    ("2.1.2.1", "Aluguel a Pagar", "PASSIVO", "2.1.2"),
    ("2.1.2.2", "Agua e Energia a Pagar", "PASSIVO", "2.1.2"),
    ("2.1.2.3", "Telefone e Internet a Pagar", "PASSIVO", "2.1.2"),
    ("2.1.3", "Obrigacoes Trabalhistas", "PASSIVO", "2.1"),
    ("2.1.3.1", "Salarios a Pagar", "PASSIVO", "2.1.3"),
    ("2.1.3.2", "FGTS a Pagar", "PASSIVO", "2.1.3"),
    ("2.1.3.3", "INSS a Pagar", "PASSIVO", "2.1.3"),
    ("2.1.4", "Impostos e Taxas a Pagar", "PASSIVO", "2.1"),
    ("2.1.4.1", "ICMS a Pagar", "PASSIVO", "2.1.4"),
    ("2.1.4.2", "ISS a Pagar", "PASSIVO", "2.1.4"),
    ("2.1.4.3", "PIS/PASEP a Pagar", "PASSIVO", "2.1.4"),
    ("2.1.4.4", "Imposto de Renda a Pagar", "PASSIVO", "2.1.4"),
    ("2.1.5", "Emprestimos Curto Prazo", "PASSIVO", "2.1"),
    ("2.1.5.1", "Emprestimos Bancarios CP", "PASSIVO", "2.1.5"),
    ("2.1.5.2", "Financiamentos CP", "PASSIVO", "2.1.5"),
    ("2.2", "PASSIVO NAO CIRCULANTE", "PASSIVO", "2"),
    ("2.2.1", "Emprestimos Longo Prazo", "PASSIVO", "2.2"),
    ("2.2.1.1", "Emprestimos Bancarios LP", "PASSIVO", "2.2.1"),
    ("2.2.1.2", "Financiamentos LP", "PASSIVO", "2.2.1"),
    ("2.3", "PATRIMONIO LIQUIDO", "PASSIVO", "2"),
    ("2.3.1", "Capital Social", "PASSIVO", "2.3"),
    ("2.3.1.1", "Capital Integralizado", "PASSIVO", "2.3.1"),
    ("2.3.2", "Lucros/Prejuizos Acumulados", "PASSIVO", "2.3"),
    ("2.3.2.1", "Lucros Acumulados", "PASSIVO", "2.3.2"),
    ("2.3.2.2", "Prejuizos Acumulados", "PASSIVO", "2.3.2"),

    # RECEITAS (14 contas)
    ("3", "RECEITAS", "RECEITA", None),
    ("3.1", "RECEITA OPERACIONAL", "RECEITA", "3"),
    ("3.1.1", "Vendas de Alimentos e Bebidas", "RECEITA", "3.1"),
    ("3.1.1.1", "Vendas de Refeicoes", "RECEITA", "3.1.1"),
    ("3.1.1.2", "Vendas de Bebidas", "RECEITA", "3.1.1"),
    ("3.1.1.3", "Vendas de Lanches", "RECEITA", "3.1.1"),
    ("3.1.1.4", "Vendas de Sobremesas", "RECEITA", "3.1.1"),
    ("3.1.2", "Servicos Prestados", "RECEITA", "3.1"),
    ("3.1.2.1", "Taxa de Servico", "RECEITA", "3.1.2"),
    ("3.1.2.2", "Eventos e Festas", "RECEITA", "3.1.2"),
    ("3.1.3", "Outras Receitas Operacionais", "RECEITA", "3.1"),
    ("3.1.3.1", "Devolucoes de Vendas", "RECEITA", "3.1.3"),
    ("3.2", "RECEITA NAO OPERACIONAL", "RECEITA", "3"),
    ("3.2.1", "Receitas Financeiras", "RECEITA", "3.2"),
    ("3.2.1.1", "Juros Recebidos", "RECEITA", "3.2.1"),
    ("3.2.1.2", "Descontos Obtidos", "RECEITA", "3.2.1"),

    # CUSTOS (12 contas)
    ("4", "CUSTO DAS MERCADORIAS VENDIDAS", "CUSTO", None),
    ("4.1", "CUSTOS DIRETOS", "CUSTO", "4"),
    ("4.1.1", "CMV - Alimentos", "CUSTO", "4.1"),
    ("4.1.1.1", "CMV - Proteinas", "CUSTO", "4.1.1"),
    ("4.1.1.2", "CMV - Vegetais e Frutas", "CUSTO", "4.1.1"),
    ("4.1.1.3", "CMV - Graos e Cereais", "CUSTO", "4.1.1"),
    ("4.1.2", "CMV - Bebidas", "CUSTO", "4.1"),
    ("4.1.2.1", "CMV - Refrigerantes", "CUSTO", "4.1.2"),
    ("4.1.2.2", "CMV - Bebidas Alcoolicas", "CUSTO", "4.1.2"),
    ("4.1.2.3", "CMV - Cafe/Cha", "CUSTO", "4.1.2"),
    ("4.1.3", "CMV - Insumos", "CUSTO", "4.1"),
    ("4.1.3.1", "CMV - Embalagens", "CUSTO", "4.1.3"),
    ("4.1.3.2", "CMV - Descartaveis", "CUSTO", "4.1.3"),

    # DESPESAS OPERACIONAIS (28 contas)
    ("5", "DESPESAS OPERACIONAIS", "DESPESA", None),
    ("5.1", "DESPESAS COM PESSOAL", "DESPESA", "5"),
    ("5.1.1", "Salarios e Ordenados", "DESPESA", "5.1"),
    ("5.1.1.1", "Salarios - Gerenciamento", "DESPESA", "5.1.1"),
    ("5.1.1.2", "Salarios - Cozinha", "DESPESA", "5.1.1"),
    ("5.1.1.3", "Salarios - Atendimento", "DESPESA", "5.1.1"),
    ("5.1.1.4", "Salarios - Limpeza", "DESPESA", "5.1.1"),
    ("5.1.2", "Encargos Sociais", "DESPESA", "5.1"),
    ("5.1.2.1", "FGTS", "DESPESA", "5.1.2"),
    ("5.1.2.2", "INSS Patronal", "DESPESA", "5.1.2"),
    ("5.1.2.3", "Seguro de Acidente de Trabalho", "DESPESA", "5.1.2"),
    ("5.1.3", "Beneficios a Empregados", "DESPESA", "5.1"),
    ("5.1.3.1", "Vale Refeicao", "DESPESA", "5.1.3"),
    ("5.1.3.2", "Vale Transporte", "DESPESA", "5.1.3"),
    ("5.1.3.3", "Convenio Medico", "DESPESA", "5.1.3"),
    ("5.2", "DESPESAS COM IMOVEL", "DESPESA", "5"),
    ("5.2.1", "Aluguel do Estabelecimento", "DESPESA", "5.2"),
    ("5.2.2", "Condominio", "DESPESA", "5.2"),
    ("5.2.3", "IPTU", "DESPESA", "5.2"),
    ("5.2.4", "Manutencao do Imovel", "DESPESA", "5.2"),
    ("5.2.5", "Limpeza e Higiene", "DESPESA", "5.2"),
    ("5.3", "DESPESAS COM UTILIDADES", "DESPESA", "5"),
    ("5.3.1", "Energia Eletrica", "DESPESA", "5.3"),
    ("5.3.2", "Agua e Esgoto", "DESPESA", "5.3"),
    ("5.3.3", "Gas", "DESPESA", "5.3"),
    ("5.3.4", "Telefone e Internet", "DESPESA", "5.3"),
    ("5.4", "DESPESAS COM MARKETING", "DESPESA", "5"),
    ("5.4.1", "Publicidade e Propaganda", "DESPESA", "5.4"),
    ("5.4.2", "Redes Sociais e Digital", "DESPESA", "5.4"),
    ("5.4.3", "Promocoes e Descontos", "DESPESA", "5.4"),
    ("5.5", "DESPESAS COM ADMINISTRATIVO", "DESPESA", "5"),
    ("5.5.1", "Materiais de Escritorio", "DESPESA", "5.5"),
    ("5.5.2", "Servicos Contabeis e Juridicos", "DESPESA", "5.5"),
    ("5.5.3", "Seguros", "DESPESA", "5.5"),
    ("5.5.4", "Taxas e Licencas", "DESPESA", "5.5"),
    ("5.6", "DESPESAS COM EQUIPAMENTOS", "DESPESA", "5"),
    ("5.6.1", "Manutencao de Equipamentos", "DESPESA", "5.6"),
    ("5.6.2", "Reposicao de Utensilio", "DESPESA", "5.6"),
    ("5.6.3", "Softwares e Sistemas", "DESPESA", "5.6"),
    ("5.7", "DESPESAS FINANCEIRAS", "DESPESA", "5"),
    ("5.7.1", "Juros Pagos", "DESPESA", "5.7"),
    ("5.7.2", "Multas e Juros de Mora", "DESPESA", "5.7"),
    ("5.7.3", "Tarifas Bancarias", "DESPESA", "5.7"),
]

def main():
    loja = Empresa.objects.get(id_empresa=1)
    contas_criadas = {}

    # Recuperar contas ja criadas
    for conta in ContaSintetica.objects.filter(loja=loja):
        contas_criadas[conta.codigo_classificacao] = conta

    inseridas = 0
    print("Inserindo contas restantes...\n")

    for codigo, nome, tipo, pai_codigo in contas_restantes:
        tipo_obj = TipoConta.objects.get(codigo=tipo)
        nivel = len(codigo.split('.'))

        pai = None
        if pai_codigo:
            if pai_codigo in contas_criadas:
                pai = contas_criadas[pai_codigo]
            else:
                try:
                    pai = ContaSintetica.objects.get(loja=loja, codigo_classificacao=pai_codigo)
                    contas_criadas[pai_codigo] = pai
                except ContaSintetica.DoesNotExist:
                    print(f"AVISO: Conta pai {pai_codigo} nao encontrada para {nome}")

        obj, created = ContaSintetica.objects.get_or_create(
            loja=loja,
            codigo_classificacao=codigo,
            defaults={
                'nome': nome,
                'tipo_conta': tipo_obj,
                'conta_pai': pai,
                'nivel': nivel,
            }
        )

        contas_criadas[codigo] = obj

        if created:
            inseridas += 1
            tipo_abrev = tipo[:3]
            print(f"OK | {codigo:>10} | {nome:<48} | {tipo_abrev}")

    total = ContaSintetica.objects.filter(loja=loja).count()
    print(f"\n{'='*90}")
    print(f"INSERCAO COMPLETA!")
    print(f"  Contas criadas neste lote: {inseridas}")
    print(f"  Total no banco agora: {total}")
    print(f"  PLANO DE CONTAS COMPLETO PARA RESTAURANTES")
    print(f"{'='*90}")

if __name__ == '__main__':
    main()
