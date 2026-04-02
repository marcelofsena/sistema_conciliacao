"""
Script para injetar dados de Plano de Contas padrão para Restaurantes Brasileiros.
Mostra previamente os dados antes de inserir no banco.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_caixa.settings')
django.setup()

from contabilidade.models import ContaSintetica, TipoConta
from core.models import Empresa

# Plano de Contas Padrão para Restaurantes
# Formato: (codigo_string, nivel, nome, tipo, pai_codigo_string)
PLANO_CONTAS = [
    # ATIVO
    ("1", 1, "ATIVO", "ATIVO", None),
    ("1.1", 2, "ATIVO CIRCULANTE", "ATIVO", "1"),
    ("1.1.1", 3, "Disponibilidades", "ATIVO", "1.1"),
    ("1.1.1.1", 4, "Caixa", "ATIVO", "1.1.1"),
    ("1.1.1.2", 4, "Bancos - Conta Corrente", "ATIVO", "1.1.1"),
    ("1.1.1.3", 4, "Bancos - Conta Poupança", "ATIVO", "1.1.1"),
    ("1.1.2", 3, "Contas a Receber", "ATIVO", "1.1"),
    ("1.1.2.1", 4, "Clientes", "ATIVO", "1.1.2"),
    ("1.1.2.2", 4, "Cartão de Crédito a Receber", "ATIVO", "1.1.2"),
    ("1.1.3", 3, "Estoques", "ATIVO", "1.1"),
    ("1.1.3.1", 4, "Estoque de Alimentos", "ATIVO", "1.1.3"),
    ("1.1.3.2", 4, "Estoque de Bebidas", "ATIVO", "1.1.3"),
    ("1.1.3.3", 4, "Estoque de Insumos", "ATIVO", "1.1.3"),
    ("1.1.4", 3, "Adiantamentos e Outras Contas", "ATIVO", "1.1"),
    ("1.1.4.1", 4, "Adiantamentos a Fornecedores", "ATIVO", "1.1.4"),
    ("1.1.4.2", 4, "Adiantamentos a Empregados", "ATIVO", "1.1.4"),
    ("1.2", 2, "ATIVO NÃO CIRCULANTE", "ATIVO", "1"),
    ("1.2.1", 3, "Imobilizado", "ATIVO", "1.2"),
    ("1.2.1.1", 4, "Móveis e Utensílios", "ATIVO", "1.2.1"),
    ("1.2.1.2", 4, "Equipamentos de Cozinha", "ATIVO", "1.2.1"),
    ("1.2.1.3", 4, "Computadores e Periféricos", "ATIVO", "1.2.1"),
    ("1.2.1.4", 4, "Veículos", "ATIVO", "1.2.1"),
    ("1.2.1.5", 4, "Imóvel (se próprio)", "ATIVO", "1.2.1"),
    ("1.2.2", 3, "Depreciação Acumulada", "ATIVO", "1.2"),
    ("1.2.2.1", 4, "Deprec. Móveis e Utensílios", "ATIVO", "1.2.2"),
    ("1.2.2.2", 4, "Deprec. Equipamentos de Cozinha", "ATIVO", "1.2.2"),

    # PASSIVO
    (2, 1, "PASSIVO", "PASSIVO", None),
    (2.1, 2, "PASSIVO CIRCULANTE", "PASSIVO", 2),
    (2.1.1, 3, "Fornecedores", "PASSIVO", 2.1),
    (2.1.1.1, 4, "Fornecedores de Alimentos", "PASSIVO", 2.1.1),
    (2.1.1.2, 4, "Fornecedores de Bebidas", "PASSIVO", 2.1.1),
    (2.1.1.3, 4, "Fornecedores de Insumos", "PASSIVO", 2.1.1),
    (2.1.2, 3, "Contas a Pagar", "PASSIVO", 2.1),
    (2.1.2.1, 4, "Aluguel a Pagar", "PASSIVO", 2.1.2),
    (2.1.2.2, 4, "Água e Energia a Pagar", "PASSIVO", 2.1.2),
    (2.1.2.3, 4, "Telefone e Internet a Pagar", "PASSIVO", 2.1.2),
    (2.1.3, 3, "Obrigações Trabalhistas", "PASSIVO", 2.1),
    (2.1.3.1, 4, "Salários a Pagar", "PASSIVO", 2.1.3),
    (2.1.3.2, 4, "FGTS a Pagar", "PASSIVO", 2.1.3),
    (2.1.3.3, 4, "INSS a Pagar", "PASSIVO", 2.1.3),
    (2.1.4, 3, "Impostos e Taxas", "PASSIVO", 2.1),
    (2.1.4.1, 4, "ICMS a Pagar", "PASSIVO", 2.1.4),
    (2.1.4.2, 4, "ISS a Pagar", "PASSIVO", 2.1.4),
    (2.1.4.3, 4, "PIS/PASEP a Pagar", "PASSIVO", 2.1.4),
    (2.1.4.4, 4, "Imposto de Renda a Pagar", "PASSIVO", 2.1.4),
    (2.1.5, 3, "Empréstimos Curto Prazo", "PASSIVO", 2.1),
    (2.1.5.1, 4, "Empréstimos Bancários CP", "PASSIVO", 2.1.5),
    (2.1.5.2, 4, "Financiamentos CP", "PASSIVO", 2.1.5),
    (2.2, 2, "PASSIVO NÃO CIRCULANTE", "PASSIVO", 2),
    (2.2.1, 3, "Empréstimos Longo Prazo", "PASSIVO", 2.2),
    (2.2.1.1, 4, "Empréstimos Bancários LP", "PASSIVO", 2.2.1),
    (2.2.1.2, 4, "Financiamentos LP", "PASSIVO", 2.2.1),
    (2.3, 2, "PATRIMÔNIO LÍQUIDO", "PASSIVO", 2),
    (2.3.1, 3, "Capital Social", "PASSIVO", 2.3),
    (2.3.1.1, 4, "Capital Integralizado", "PASSIVO", 2.3.1),
    (2.3.2, 3, "Lucros/Prejuízos Acumulados", "PASSIVO", 2.3),
    (2.3.2.1, 4, "Lucros Acumulados", "PASSIVO", 2.3.2),
    (2.3.2.2, 4, "Prejuízos Acumulados", "PASSIVO", 2.3.2),

    # RECEITAS
    (3, 1, "RECEITAS", "RECEITA", None),
    (3.1, 2, "RECEITA OPERACIONAL", "RECEITA", 3),
    (3.1.1, 3, "Vendas de Alimentos e Bebidas", "RECEITA", 3.1),
    (3.1.1.1, 4, "Vendas de Refeições", "RECEITA", 3.1.1),
    (3.1.1.2, 4, "Vendas de Bebidas", "RECEITA", 3.1.1),
    (3.1.1.3, 4, "Vendas de Lanches", "RECEITA", 3.1.1),
    (3.1.1.4, 4, "Vendas de Sobremesas", "RECEITA", 3.1.1),
    (3.1.2, 3, "Serviços Prestados", "RECEITA", 3.1),
    (3.1.2.1, 4, "Taxa de Serviço", "RECEITA", 3.1.2),
    (3.1.2.2, 4, "Eventos e Festas", "RECEITA", 3.1.2),
    (3.1.3, 3, "Outras Receitas Operacionais", "RECEITA", 3.1),
    (3.1.3.1, 4, "Devoluções de Vendas", "RECEITA", 3.1.3),
    (3.2, 2, "RECEITA NÃO OPERACIONAL", "RECEITA", 3),
    (3.2.1, 3, "Receitas Financeiras", "RECEITA", 3.2),
    (3.2.1.1, 4, "Juros Recebidos", "RECEITA", 3.2.1),
    (3.2.1.2, 4, "Descontos Obtidos", "RECEITA", 3.2.1),

    # CUSTOS
    (4, 1, "CUSTO DAS MERCADORIAS VENDIDAS", "CUSTO", None),
    (4.1, 2, "CUSTOS DIRETOS", "CUSTO", 4),
    (4.1.1, 3, "CMV - Alimentos", "CUSTO", 4.1),
    (4.1.1.1, 4, "CMV - Proteínas", "CUSTO", 4.1.1),
    (4.1.1.2, 4, "CMV - Vegetais e Frutas", "CUSTO", 4.1.1),
    (4.1.1.3, 4, "CMV - Grãos e Cereais", "CUSTO", 4.1.1),
    (4.1.2, 3, "CMV - Bebidas", "CUSTO", 4.1),
    (4.1.2.1, 4, "CMV - Refrigerantes", "CUSTO", 4.1.2),
    (4.1.2.2, 4, "CMV - Bebidas Alcólicas", "CUSTO", 4.1.2),
    (4.1.2.3, 4, "CMV - Café/Chá", "CUSTO", 4.1.2),
    (4.1.3, 3, "CMV - Insumos", "CUSTO", 4.1),
    (4.1.3.1, 4, "CMV - Embalagens", "CUSTO", 4.1.3),
    (4.1.3.2, 4, "CMV - Descartáveis", "CUSTO", 4.1.3),

    # DESPESAS
    (5, 1, "DESPESAS OPERACIONAIS", "DESPESA", None),
    (5.1, 2, "DESPESAS COM PESSOAL", "DESPESA", 5),
    (5.1.1, 3, "Salários e Ordenados", "DESPESA", 5.1),
    (5.1.1.1, 4, "Salários - Gerenciamento", "DESPESA", 5.1.1),
    (5.1.1.2, 4, "Salários - Cozinha", "DESPESA", 5.1.1),
    (5.1.1.3, 4, "Salários - Atendimento", "DESPESA", 5.1.1),
    (5.1.1.4, 4, "Salários - Limpeza", "DESPESA", 5.1.1),
    (5.1.2, 3, "Encargos Sociais", "DESPESA", 5.1),
    (5.1.2.1, 4, "FGTS", "DESPESA", 5.1.2),
    (5.1.2.2, 4, "INSS Patronal", "DESPESA", 5.1.2),
    (5.1.2.3, 4, "Seguro de Acidente", "DESPESA", 5.1.2),
    (5.1.3, 3, "Benefícios a Empregados", "DESPESA", 5.1),
    (5.1.3.1, 4, "Vale Refeição", "DESPESA", 5.1.3),
    (5.1.3.2, 4, "Vale Transporte", "DESPESA", 5.1.3),
    (5.1.3.3, 4, "Convênio Médico", "DESPESA", 5.1.3),
    (5.2, 2, "DESPESAS COM IMÓVEL", "DESPESA", 5),
    (5.2.1, 3, "Aluguel do Estabelecimento", "DESPESA", 5.2),
    (5.2.2, 3, "Condomínio", "DESPESA", 5.2),
    (5.2.3, 3, "IPTU", "DESPESA", 5.2),
    (5.2.4, 3, "Manutenção do Imóvel", "DESPESA", 5.2),
    (5.2.5, 3, "Limpeza e Higiene", "DESPESA", 5.2),
    (5.3, 2, "DESPESAS COM UTILIDADES", "DESPESA", 5),
    (5.3.1, 3, "Energia Elétrica", "DESPESA", 5.3),
    (5.3.2, 3, "Água e Esgoto", "DESPESA", 5.3),
    (5.3.3, 3, "Gás", "DESPESA", 5.3),
    (5.3.4, 3, "Telefone e Internet", "DESPESA", 5.3),
    (5.4, 2, "DESPESAS COM MARKETING", "DESPESA", 5),
    (5.4.1, 3, "Publicidade e Propaganda", "DESPESA", 5.4),
    (5.4.2, 3, "Redes Sociais e Digital", "DESPESA", 5.4),
    (5.4.3, 3, "Promoções e Descontos", "DESPESA", 5.4),
    (5.5, 2, "DESPESAS COM ADMINISTRATIVO", "DESPESA", 5),
    (5.5.1, 3, "Materiais de Escritório", "DESPESA", 5.5),
    (5.5.2, 3, "Serviços Contábeis e Jurídicos", "DESPESA", 5.5),
    (5.5.3, 3, "Seguros", "DESPESA", 5.5),
    (5.5.4, 3, "Taxas e Licenças", "DESPESA", 5.5),
    (5.6, 2, "DESPESAS COM EQUIPAMENTOS", "DESPESA", 5),
    (5.6.1, 3, "Manutenção de Equipamentos", "DESPESA", 5.6),
    (5.6.2, 3, "Reposição de Utensílios", "DESPESA", 5.6),
    (5.6.3, 3, "Softwares e Sistemas", "DESPESA", 5.6),
    (5.7, 2, "DESPESAS FINANCEIRAS", "DESPESA", 5),
    (5.7.1, 3, "Juros Pagos", "DESPESA", 5.7),
    (5.7.2, 3, "Multas e Juros", "DESPESA", 5.7),
    (5.7.3, 3, "Tarifas Bancárias", "DESPESA", 5.7),
]


def preview_plano_contas():
    """Mostra previa do plano de contas antes de inserir."""
    print("\n" + "=" * 120)
    print("PLANO DE CONTAS PADRÃO PARA RESTAURANTES BRASILEIROS".center(120))
    print("=" * 120)

    # Agrupar por tipo
    por_tipo = {}
    for codigo, nivel, nome, tipo, pai in PLANO_CONTAS:
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append((codigo, nivel, nome, tipo, pai))

    ordem = ["ATIVO", "PASSIVO", "RECEITA", "CUSTO", "DESPESA"]
    total = 0

    for tipo in ordem:
        if tipo in por_tipo:
            contas = por_tipo[tipo]
            print(f"\n{'█ ' * 60}")
            print(f"  {tipo:<20} ({len(contas):>3} contas)")
            print(f"{'█ ' * 60}")

            for codigo, nivel, nome, _, pai in contas:
                total += 1
                indent = "    " * (nivel - 1)
                cod_str = f"{codigo:>6.1f}"
                pai_info = f"← {pai}" if pai else "[RAIZ]"
                print(f"{indent}{cod_str} | {nome:<48} {pai_info:>12}")

    print("\n" + "=" * 120)
    print(f"TOTAL DE CONTAS: {total}".center(120))
    print("=" * 120 + "\n")

    return por_tipo, total


def inserir_plano_contas(loja_id=1, confirmar=False):
    """Insere o plano de contas no banco."""

    if not confirmar:
        print("AVISO: Use confirmar=True para inserir os dados.")
        return

    try:
        loja = Empresa.objects.get(id_empresa=loja_id)
    except Empresa.DoesNotExist:
        print(f"ERRO: Loja com ID {loja_id} não encontrada.")
        return

    print(f"Inserindo plano de contas para: {loja.descricao}")
    print()

    # Mapa para rastrear contas criadas
    contas_criadas = {}

    inserted = 0
    updated = 0

    for codigo, nivel, nome, tipo, pai_codigo in PLANO_CONTAS:
        # Obter tipo de conta
        tipo_obj = TipoConta.objects.get(codigo=tipo)

        # Obter conta pai
        conta_pai = None
        if pai_codigo:
            if pai_codigo in contas_criadas:
                conta_pai = contas_criadas[pai_codigo]
            else:
                try:
                    conta_pai = ContaSintetica.objects.get(
                        loja=loja,
                        codigo_classificacao=str(pai_codigo)
                    )
                except ContaSintetica.DoesNotExist:
                    print(f"  AVISO: Conta pai {pai_codigo} não encontrada para {nome}")

        # Criar ou atualizar
        obj, created = ContaSintetica.objects.get_or_create(
            loja=loja,
            codigo_classificacao=str(codigo),
            defaults={
                'nome': nome,
                'tipo_conta': tipo_obj,
                'conta_pai': conta_pai,
                'nivel': nivel,
            }
        )

        contas_criadas[codigo] = obj

        if created:
            inserted += 1
            status = "CRIADA"
        else:
            updated += 1
            status = "EXISTENTE"
            # Atualizar dados se necessário
            obj.nome = nome
            obj.tipo_conta = tipo_obj
            obj.conta_pai = conta_pai
            obj.nivel = nivel
            obj.save()

        if created or updated <= 5:  # Mostrar apenas primeiras atualizações
            print(f"  [{status:>9}] {str(codigo):>6} - {nome}")

    print()
    print("=" * 120)
    print(f"Inserção Concluída: {inserted} novas contas, {updated} atualizadas".center(120))
    print("=" * 120 + "\n")


if __name__ == '__main__':
    import sys

    # Mostrar preview
    por_tipo, total = preview_plano_contas()

    # Perguntar se quer inserir
    if len(sys.argv) > 1 and sys.argv[1] == '--inserir':
        resposta = input("Deseja inserir este plano de contas? (s/n): ").lower()
        if resposta == 's':
            loja_id = input("ID da loja (padrão: 1): ").strip() or 1
            try:
                inserir_plano_contas(int(loja_id), confirmar=True)
            except ValueError:
                print("ID de loja inválido.")
        else:
            print("Inserção cancelada.")
    else:
        print("Para inserir os dados, execute:")
        print("  python seed_plano_contas.py --inserir")
