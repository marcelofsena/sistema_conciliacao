#!/usr/bin/env python
"""
Script para criar contas analíticas faltantes na Empresa Modelo.
Cria uma conta analítica para cada conta sintética que não tem.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_caixa.settings')
django.setup()

from contabilidade.models import ContaSintetica, ContaAnalitica
from core.models import Empresa

def criar_contas_analiticas_faltantes():
    """Cria contas analíticas para contas sintéticas sem análise"""

    print("\n" + "="*70)
    print("CRIANDO CONTAS ANALITICAS FALTANTES NA EMPRESA MODELO")
    print("="*70 + "\n")

    empresa_modelo = Empresa.objects.get(id_empresa=4)
    print(f"[OK] Empresa Modelo: {empresa_modelo.descricao}\n")

    contas_sinteticas = ContaSintetica.objects.filter(loja=empresa_modelo).order_by('codigo_classificacao')
    criadas = 0
    ja_existem = 0

    for conta_sintetica in contas_sinteticas:
        # Verificar se já existe conta analítica
        tem_analítica = ContaAnalitica.objects.filter(
            loja=empresa_modelo,
            conta_sintetica=conta_sintetica
        ).exists()

        if not tem_analítica:
            # Criar conta analítica
            codigo_reduzido = ContaAnalitica.objects.filter(
                loja=empresa_modelo
            ).aggregate(max_codigo=__import__('django.db.models', fromlist=['Max'])('Max')('codigo_reduzido'))['max_codigo'] or 0
            codigo_reduzido += 1

            try:
                ContaAnalitica.objects.create(
                    loja=empresa_modelo,
                    codigo_reduzido=codigo_reduzido,
                    codigo_classificacao=f"{conta_sintetica.codigo_classificacao}.0001",
                    nome=conta_sintetica.nome,
                    conta_sintetica=conta_sintetica,
                    natureza_saldo='DEVEDOR' if conta_sintetica.tipo_conta.codigo in ['ATIVO', 'CUSTO', 'DESPESA'] else 'CREDOR',
                    aceita_lancamento=True,
                )
                print(f"[CRIADA] {conta_sintetica.codigo_classificacao} - {conta_sintetica.nome}")
                criadas += 1
            except Exception as e:
                print(f"[ERRO] {conta_sintetica.codigo_classificacao}: {str(e)}")
        else:
            ja_existem += 1

    print(f"\n{'='*70}")
    print(f"RESUMO: {criadas} contas criadas, {ja_existem} já existem")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    criar_contas_analiticas_faltantes()
