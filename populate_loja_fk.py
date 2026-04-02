"""
Script para preencher loja_id em modelos que usam codigo_loja.

Fase 3 da migração híbrida:
- VendaSWFast: ~11010 registros
- Sangria, MovimentoCaixa, ConciliacaoCaixa: registros existentes

Uso: python manage.py shell < populate_loja_fk.py
"""

from importacoes.models import VendaSWFast
from caixa.models import Sangria, MovimentoCaixa, ConciliacaoCaixa
from core.models import Empresa

print("=" * 70)
print("INICIANDO POPULAÇÃO DE loja_id")
print("=" * 70)

# ========================================
# 1. VendaSWFast
# ========================================
print("\n[1/4] VendaSWFast")
print("-" * 70)

vendas_sem_loja = VendaSWFast.objects.filter(loja__isnull=True)
total_vendas = vendas_sem_loja.count()

if total_vendas == 0:
    print("✓ Nenhuma venda sem loja_id. Já está preenchido!")
else:
    print(f"Encontradas {total_vendas} vendas para preencher...")

    codigo_loja_set = set(vendas_sem_loja.values_list('codigo_loja', flat=True))
    print(f"Códigos SWFast únicos: {sorted(codigo_loja_set)}")

    atualizadas = 0
    nao_encontradas = set()

    for codigo_loja in codigo_loja_set:
        if not codigo_loja:
            continue

        empresa = Empresa.objects.filter(ncad_swfast=codigo_loja).first()

        if not empresa:
            nao_encontradas.add(codigo_loja)
            continue

        # Atualiza todas as vendas com este codigo_loja
        qty = VendaSWFast.objects.filter(codigo_loja=codigo_loja, loja__isnull=True).update(loja=empresa)
        atualizadas += qty
        print(f"  ✓ Código {codigo_loja} → Empresa {empresa.descricao} ({qty} vendas)")

    print(f"\n✓ Total atualizado: {atualizadas} vendas")

    if nao_encontradas:
        print(f"\n⚠️  Códigos SWFast não encontrados em Empresa.ncad_swfast:")
        for codigo in sorted(nao_encontradas):
            print(f"   - {codigo}")


# ========================================
# 2. Sangria
# ========================================
print("\n[2/4] Sangria")
print("-" * 70)

sangrias_sem_loja = Sangria.objects.filter(loja__isnull=True)
total_sangrias = sangrias_sem_loja.count()

if total_sangrias == 0:
    print("✓ Nenhuma sangria sem loja_id. Já está preenchido!")
else:
    print(f"Encontradas {total_sangrias} sangrias para preencher...")

    codigo_loja_set = set(sangrias_sem_loja.values_list('codigo_loja', flat=True))

    atualizadas = 0
    nao_encontradas = set()

    for codigo_loja in codigo_loja_set:
        if not codigo_loja:
            continue

        empresa = Empresa.objects.filter(ncad_swfast=codigo_loja).first()

        if not empresa:
            nao_encontradas.add(codigo_loja)
            continue

        qty = Sangria.objects.filter(codigo_loja=codigo_loja, loja__isnull=True).update(loja=empresa)
        atualizadas += qty
        print(f"  ✓ Código {codigo_loja} → Empresa {empresa.descricao} ({qty} sangrias)")

    print(f"\n✓ Total atualizado: {atualizadas} sangrias")

    if nao_encontradas:
        print(f"\n⚠️  Códigos não encontrados: {sorted(nao_encontradas)}")


# ========================================
# 3. MovimentoCaixa
# ========================================
print("\n[3/4] MovimentoCaixa")
print("-" * 70)

movimentos_sem_loja = MovimentoCaixa.objects.filter(loja__isnull=True)
total_movimentos = movimentos_sem_loja.count()

if total_movimentos == 0:
    print("✓ Nenhum movimento sem loja_id. Já está preenchido!")
else:
    print(f"Encontrados {total_movimentos} movimentos para preencher...")

    codigo_loja_set = set(movimentos_sem_loja.values_list('codigo_loja', flat=True))

    atualizadas = 0
    nao_encontradas = set()

    for codigo_loja in codigo_loja_set:
        if not codigo_loja:
            continue

        empresa = Empresa.objects.filter(ncad_swfast=codigo_loja).first()

        if not empresa:
            nao_encontradas.add(codigo_loja)
            continue

        qty = MovimentoCaixa.objects.filter(codigo_loja=codigo_loja, loja__isnull=True).update(loja=empresa)
        atualizadas += qty
        print(f"  ✓ Código {codigo_loja} → Empresa {empresa.descricao} ({qty} movimentos)")

    print(f"\n✓ Total atualizado: {atualizadas} movimentos")

    if nao_encontradas:
        print(f"\n⚠️  Códigos não encontrados: {sorted(nao_encontradas)}")


# ========================================
# 4. ConciliacaoCaixa
# ========================================
print("\n[4/4] ConciliacaoCaixa")
print("-" * 70)

conciliações_sem_loja = ConciliacaoCaixa.objects.filter(loja__isnull=True)
total_conciliações = conciliações_sem_loja.count()

if total_conciliações == 0:
    print("✓ Nenhuma conciliação sem loja_id. Já está preenchido!")
else:
    print(f"Encontradas {total_conciliações} conciliações para preencher...")

    codigo_loja_set = set(conciliações_sem_loja.values_list('codigo_loja', flat=True))

    atualizadas = 0
    nao_encontradas = set()

    for codigo_loja in codigo_loja_set:
        if not codigo_loja:
            continue

        empresa = Empresa.objects.filter(ncad_swfast=codigo_loja).first()

        if not empresa:
            nao_encontradas.add(codigo_loja)
            continue

        qty = ConciliacaoCaixa.objects.filter(codigo_loja=codigo_loja, loja__isnull=True).update(loja=empresa)
        atualizadas += qty
        print(f"  ✓ Código {codigo_loja} → Empresa {empresa.descricao} ({qty} conciliações)")

    print(f"\n✓ Total atualizado: {atualizadas} conciliações")

    if nao_encontradas:
        print(f"\n⚠️  Códigos não encontrados: {sorted(nao_encontradas)}")


# ========================================
# RESUMO FINAL
# ========================================
print("\n" + "=" * 70)
print("RESUMO FINAL")
print("=" * 70)

vendas_preenchidas = VendaSWFast.objects.filter(loja__isnull=False).count()
sangrias_preenchidas = Sangria.objects.filter(loja__isnull=False).count()
movimentos_preenchidos = MovimentoCaixa.objects.filter(loja__isnull=False).count()
conciliações_preenchidas = ConciliacaoCaixa.objects.filter(loja__isnull=False).count()

print(f"✓ VendaSWFast: {vendas_preenchidas} registros com loja_id")
print(f"✓ Sangria: {sangrias_preenchidas} registros com loja_id")
print(f"✓ MovimentoCaixa: {movimentos_preenchidos} registros com loja_id")
print(f"✓ ConciliacaoCaixa: {conciliações_preenchidas} registros com loja_id")

print("\n✅ Script concluído com sucesso!")
print("=" * 70)
