"""
Script de manutenção: Corrigir código_reduzido das contas analíticas

Este script sincroniza o campo codigo_reduzido com os últimos 4 dígitos
do campo codigo_classificacao.

Usar quando:
- Importar dados legados
- Detectar inconsistências no banco
- Migrar de um sistema antigo

Uso:
  python manage.py shell < scripts_manutencao/corrigir_codigo_reduzido.py
"""

from contabilidade.models import ContaAnalitica
from django.db.models import Count

print("=" * 70)
print("ANÁLISE: Código Reduzido vs Código de Classificação")
print("=" * 70)

# 1. Encontrar inconsistências
inconsistentes = []
for conta in ContaAnalitica.objects.all():
    if conta.codigo_classificacao:
        ultimos_4 = conta.codigo_classificacao.split('.')[-1]
        try:
            codigo_correto = int(ultimos_4)
            if conta.codigo_reduzido != codigo_correto:
                inconsistentes.append({
                    'id': conta.id,
                    'loja': conta.loja_id,
                    'codigo_atual': conta.codigo_reduzido,
                    'codigo_correto': codigo_correto,
                    'classificacao': conta.codigo_classificacao,
                    'nome': conta.nome,
                })
        except ValueError:
            print(f"⚠️  ID {conta.id}: Não conseguiu extrair código de {conta.codigo_classificacao}")

print(f"\n📊 Encontradas {len(inconsistentes)} inconsistência(s)\n")

if inconsistentes:
    print("INCONSISTÊNCIAS ENCONTRADAS:")
    print("-" * 70)
    for item in inconsistentes:
        print(f"ID: {item['id']:3} | Loja: {item['loja']} | Código: {item['classificacao']}")
        print(f"  Atual: {item['codigo_atual']:4} → Deveria ser: {item['codigo_correto']:4} | {item['nome']}")

    # 2. Corrigir
    print("\n" + "=" * 70)
    print("CORRIGINDO...")
    print("=" * 70)

    for item in inconsistentes:
        conta = ContaAnalitica.objects.get(id=item['id'])
        conta.codigo_reduzido = item['codigo_correto']
        try:
            conta.save()
            print(f"✅ ID {item['id']}: Corrigido {item['codigo_atual']} → {item['codigo_correto']}")
        except Exception as e:
            print(f"❌ ID {item['id']}: Erro ao corrigir - {str(e)}")

    print("\n" + "=" * 70)
    print(f"✅ Processo concluído! {len(inconsistentes)} conta(s) corrigida(s).")
    print("=" * 70)
else:
    print("✅ Nenhuma inconsistência encontrada! Tudo OK.")
    print("=" * 70)

# 3. Verificar duplicatas (agora por sintética, não por loja inteira)
print("\n" + "=" * 70)
print("VERIFICANDO DUPLICATAS...")
print("=" * 70)

duplicatas = ContaAnalitica.objects.values('loja_id', 'conta_sintetica_id', 'codigo_reduzido').annotate(
    count=Count('id')
).filter(count__gt=1)

if duplicatas.exists():
    print(f"\n⚠️  ENCONTRADAS {duplicatas.count()} DUPLICATA(S)!\n")
    for dup in duplicatas:
        contas = ContaAnalitica.objects.filter(
            loja_id=dup['loja_id'],
            conta_sintetica_id=dup['conta_sintetica_id'],
            codigo_reduzido=dup['codigo_reduzido']
        ).order_by('id')
        print(f"Loja {dup['loja_id']}, Sintética {dup['conta_sintetica_id']}, Código Reduzido {dup['codigo_reduzido']} ({dup['count']} contas):")
        for c in contas:
            print(f"  - ID {c.id}: {c.codigo_classificacao} | {c.nome}")
    print("\n⚠️  Ação recomendada: Deletar uma das duplicatas ou renomear o código")
else:
    print("✅ Nenhuma duplicata encontrada!")

print("=" * 70)
