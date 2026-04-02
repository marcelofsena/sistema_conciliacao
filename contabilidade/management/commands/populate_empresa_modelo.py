"""
Comando Django para popular Empresa Modelo com plano de contas do template.

Uso: python manage.py populate_empresa_modelo
"""

from django.core.management.base import BaseCommand
from contabilidade.models import (
    TemplateplanoConta, ContaTemplate, ContaSintetica, ContaAnalitica, TipoConta
)
from core.models import Empresa


class Command(BaseCommand):
    help = 'Popula Empresa Modelo (ID=4) com plano de contas do template'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("POPULANDO EMPRESA MODELO COM PLANO DE CONTAS")
        self.stdout.write("=" * 70)

        # Busca dados
        try:
            empresa_modelo = Empresa.objects.get(id_empresa=4)
            template = TemplateplanoConta.objects.get(nome='Restaurante Brasileiro')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao buscar dados: {e}"))
            return

        self.stdout.write(f"\n[1] Validacao inicial:")
        self.stdout.write(f"  Empresa: {empresa_modelo.descricao} (ID={empresa_modelo.id_empresa})")
        self.stdout.write(f"  Template: {template.nome}")

        # Verifica se ja foi preenchido
        contas_existentes = ContaSintetica.objects.filter(loja=empresa_modelo).count()
        if contas_existentes > 0:
            self.stdout.write(f"  [AVISO] Empresa ja tem {contas_existentes} contas!")
            self.stdout.write("  Removendo contas existentes...")
            ContaSintetica.objects.filter(loja=empresa_modelo).delete()

        # Mapeamento de tipos
        tipo_map = {
            'ATIVO': TipoConta.objects.get(codigo='ATIVO'),
            'PASSIVO': TipoConta.objects.get(codigo='PASSIVO'),
            'RECEITA': TipoConta.objects.get(codigo='RECEITA'),
            'CUSTO': TipoConta.objects.get(codigo='CUSTO'),
            'DESPESA': TipoConta.objects.get(codigo='DESPESA'),
        }

        # Copia contas
        self.stdout.write(f"\n[2] Copiando contas do template:")
        self.stdout.write("-" * 70)

        contas_template = ContaTemplate.objects.filter(template=template).order_by('codigo_classificacao')
        mapa_contas = {}

        self.stdout.write(f"  Total de contas no template: {contas_template.count()}")

        criadas = 0
        for ct in contas_template:
            conta_pai = None
            if ct.pai_codigo:
                if ct.pai_codigo in mapa_contas:
                    conta_pai = mapa_contas[ct.pai_codigo]
                else:
                    conta_pai = ContaSintetica.objects.filter(
                        loja=empresa_modelo,
                        codigo_classificacao=ct.pai_codigo
                    ).first()

            tipo_conta_obj = tipo_map.get(ct.tipo_conta)
            if not tipo_conta_obj:
                self.stdout.write(f"  [ERRO] Tipo '{ct.tipo_conta}' nao encontrado")
                continue

            cs, c = ContaSintetica.objects.get_or_create(
                loja=empresa_modelo,
                codigo_classificacao=ct.codigo_classificacao,
                defaults={
                    'nome': ct.nome,
                    'tipo_conta': tipo_conta_obj,
                    'nivel': ct.nivel,
                    'conta_pai': conta_pai,
                    'eh_modelo': True,
                }
            )

            if c:
                criadas += 1
                if criadas <= 10 or criadas % 20 == 0:
                    self.stdout.write(f"  [OK] {ct.codigo_classificacao} - {ct.nome}")

            mapa_contas[ct.codigo_classificacao] = cs

        self.stdout.write(f"  Total criadas: {criadas}")

        # Cria contas analiticas
        self.stdout.write(f"\n[3] Criando contas analiticas:")
        self.stdout.write("-" * 70)

        contas_sinteticas = ContaSintetica.objects.filter(loja=empresa_modelo)
        contador = 0

        for cs in contas_sinteticas:
            tem_filhas = ContaSintetica.objects.filter(conta_pai=cs).exists()

            if not tem_filhas:
                ca, c = ContaAnalitica.objects.get_or_create(
                    loja=empresa_modelo,
                    codigo_reduzido=1,
                    conta_sintetica=cs,
                    defaults={
                        'codigo_classificacao': f"{cs.codigo_classificacao}.0001",
                        'nome': cs.nome,
                        'natureza_saldo': 'DEVEDOR' if cs.tipo_conta.codigo in ['ATIVO', 'DESPESA'] else 'CREDOR',
                        'aceita_lancamento': True,
                        'eh_modelo': True,
                    }
                )
                if c:
                    contador += 1

        self.stdout.write(f"  Criadas {contador} contas analiticas")

        # Resumo
        self.stdout.write(f"\n[4] RESUMO FINAL:")
        self.stdout.write("=" * 70)

        cs_criadas = ContaSintetica.objects.filter(loja=empresa_modelo).count()
        ca_criadas = ContaAnalitica.objects.filter(loja=empresa_modelo).count()

        self.stdout.write(self.style.SUCCESS(f"[OK] Contas Sinteticas criadas: {cs_criadas}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Contas Analiticas criadas: {ca_criadas}"))
        self.stdout.write(self.style.SUCCESS(f"[OK] Empresa Modelo pronta para ser copiada!"))

        self.stdout.write(f"\nProximo passo:")
        self.stdout.write(f"  Quando usuario clicar 'Importar Plano de Contas'")
        self.stdout.write(f"  Sistema vai buscar em Empresa Modelo (eh_modelo=True)")
        self.stdout.write(f"  E copiar para a nova loja do usuario")

        self.stdout.write("\n" + "=" * 70)
