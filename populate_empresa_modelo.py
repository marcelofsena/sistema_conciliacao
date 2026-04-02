"""
Script para popular Empresa Modelo (ID=4) com plano de contas do template.

Cópia estruturada:
1. ContaTemplate → ContaSintetica (com eh_modelo=True)
2. Cria hierarquia corretamente (conta_pai)
3. Depois cria ContaAnalitica para cada ContaSintetica folha
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_caixa.settings')
django.setup()

from contabilidade.models import (
    TemplateplanoConta, ContaTemplate, ContaSintetica, ContaAnalitica, TipoConta
)
from django.core.management import call_command
from core.models import Empresa
from django.contrib.auth.models import User

print("\n" + "=" * 70)
print("POPULANDO EMPRESA MODELO COM PLANO DE CONTAS")
print("=" * 70)

# 1. Busca Empresa Modelo e Template
empresa_modelo = Empresa.objects.get(id_empresa=4)
template = TemplateplanoConta.objects.get(nome='Restaurante Brasileiro')

print(f"\n[1] Validacao inicial:")
print(f"  Empresa: {empresa_modelo.descricao} (ID={empresa_modelo.id_empresa})")
print(f"  Template: {template.nome}")

# Verifica se já foi preenchido
contas_existentes = ContaSintetica.objects.filter(loja=empresa_modelo).count()
if contas_existentes > 0:
    print(f"\n  [AVISO] Empresa Modelo ja tem {contas_existentes} contas!")
    resposta = input("  Deseja continuar e recriar? (s/n): ").strip().lower()
    if resposta != 's':
        print("  Operacao cancelada.")
        exit(1)
    # Remove as existentes
    ContaSintetica.objects.filter(loja=empresa_modelo).delete()
    print(f"  Contas removidas. Continuando...")

# 2. Copia ContasTemplate → ContaSintetica
print(f"\n[2] Copiando contas do template:")
print("-" * 70)

# Primeiro, mapeamento de tipo_conta (string no template → TipoConta no banco)
tipo_map = {
    'ATIVO': TipoConta.objects.get(codigo='ATIVO'),
    'PASSIVO': TipoConta.objects.get(codigo='PASSIVO'),
    'RECEITA': TipoConta.objects.get(codigo='RECEITA'),
    'CUSTO': TipoConta.objects.get(codigo='CUSTO'),
    'DESPESA': TipoConta.objects.get(codigo='DESPESA'),
}

contas_template = ContaTemplate.objects.filter(template=template).order_by('codigo_classificacao')
mapa_contas = {}  # Mapeia codigo_template → ContaSintetica criada

print(f"  Total de contas no template: {contas_template.count()}")

for ct in contas_template:
    # Busca ou cria conta pai se necessário
    conta_pai = None
    if ct.pai_codigo:
        # Procura no mapa de contas já criadas
        if ct.pai_codigo in mapa_contas:
            conta_pai = mapa_contas[ct.pai_codigo]
        else:
            # Procura no banco
            conta_pai = ContaSintetica.objects.filter(
                loja=empresa_modelo,
                codigo_classificacao=ct.pai_codigo
            ).first()

    # Converte string tipo_conta para TipoConta object
    tipo_conta_obj = tipo_map.get(ct.tipo_conta)
    if not tipo_conta_obj:
        print(f"  ✗ Tipo de conta '{ct.tipo_conta}' não encontrado. Pulando {ct.codigo_classificacao}")
        continue

    # Cria ContaSintetica
    cs, criada = ContaSintetica.objects.get_or_create(
        loja=empresa_modelo,
        codigo_classificacao=ct.codigo_classificacao,
        defaults={
            'nome': ct.nome,
            'tipo_conta': tipo_conta_obj,
            'nivel': ct.nivel,
            'conta_pai': conta_pai,
            'eh_modelo': True,  # ← IMPORTANTE: marca como modelo
        }
    )

    # Armazena no mapa para referência futura
    mapa_contas[ct.codigo_classificacao] = cs

    if criada:
        print(f"  [OK] {ct.codigo_classificacao} - {ct.nome}")
    else:
        print(f"  [EX] {ct.codigo_classificacao} - {ct.nome} (ja existia)")

# 3. Cria ContasAnaliticas para as contas folha
print(f"\n[3] Criando contas analíticas para contas folha:")
print("-" * 70)

contas_sinteticas = ContaSintetica.objects.filter(loja=empresa_modelo)
contador_analiticas = 0

for cs in contas_sinteticas:
    # Verifica se é uma conta folha (não tem filhas)
    tem_filhas = ContaSintetica.objects.filter(conta_pai=cs).exists()

    if not tem_filhas:
        # Cria uma conta analítica padrão
        ca, criada = ContaAnalitica.objects.get_or_create(
            loja=empresa_modelo,
            codigo_reduzido=1,  # Código simplificado
            conta_sintetica=cs,
            defaults={
                'codigo_classificacao': f"{cs.codigo_classificacao}.0001",
                'nome': cs.nome,
                'natureza_saldo': 'DEVEDOR' if cs.tipo_conta in ['ATIVO', 'DESPESA'] else 'CREDOR',
                'aceita_lancamento': True,
                'eh_modelo': True,  # ← IMPORTANTE: marca como modelo
            }
        )
        if criada:
            contador_analiticas += 1

print(f"  Criadas {contador_analiticas} contas analíticas")

# 4. Resumo final
print(f"\n[4] RESUMO FINAL:")
print("=" * 70)

cs_criadas = ContaSintetica.objects.filter(loja=empresa_modelo).count()
ca_criadas = ContaAnalitica.objects.filter(loja=empresa_modelo).count()

print(f"[OK] Contas Sinteticas criadas: {cs_criadas}")
print(f"[OK] Contas Analiticas criadas: {ca_criadas}")
print(f"[OK] Empresa Modelo pronta para ser copiada!")

print(f"\nProximo passo:")
print(f"  - Quando usuário clicar 'Importar Plano de Contas'")
print(f"  - Sistema vai buscar em Empresa Modelo (eh_modelo=True)")
print(f"  - E copiar para a nova loja do usuário")

print("\n" + "=" * 70)
print("Script concluído com sucesso!")
print("=" * 70)
EOF
