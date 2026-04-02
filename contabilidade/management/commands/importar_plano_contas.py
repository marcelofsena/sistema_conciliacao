"""
Command Django para importar plano de contas da Empresa Modelo.

Uso:
  python manage.py importar_plano_contas --loja-id 2
  python manage.py importar_plano_contas --loja-id 3 --force

Opções:
  --loja-id: ID da empresa para importar (obrigatório)
  --force: Sobrescrever plano existente
"""

from django.core.management.base import BaseCommand, CommandError
from contabilidade.models import ContaSintetica, ContaAnalitica, TipoConta
from core.models import Empresa


class Command(BaseCommand):
    help = 'Importa plano de contas da Empresa Modelo para uma nova loja'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loja-id',
            type=int,
            required=True,
            help='ID da empresa (id_empresa) para importar o plano de contas'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescrever plano de contas existente'
        )

    def handle(self, *args, **options):
        loja_id = options['loja_id']
        force = options.get('force', False)

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("IMPORTANDO PLANO DE CONTAS")
        self.stdout.write("=" * 70)

        # =========================================
        # 1. VALIDACOES INICIAIS
        # =========================================
        self.stdout.write(f"\n[1] Validacoes iniciais:")
        self.stdout.write("-" * 70)

        # Busca empresa modelo
        try:
            empresa_modelo = Empresa.objects.get(id_empresa=4)
            self.stdout.write(f"  [OK] Empresa Modelo encontrada: {empresa_modelo.descricao}")
        except Empresa.DoesNotExist:
            raise CommandError("Empresa Modelo (ID=4) nao encontrada!")

        # Busca loja destino
        try:
            loja_destino = Empresa.objects.get(id_empresa=loja_id)
            self.stdout.write(f"  [OK] Loja destino encontrada: {loja_destino.descricao}")
        except Empresa.DoesNotExist:
            raise CommandError(f"Loja com ID={loja_id} nao encontrada!")

        # Valida que nao sao a mesma
        if loja_id == 4:
            raise CommandError("Nao pode importar para a Empresa Modelo!")

        # Verifica se ja tem plano de contas
        contas_existentes = ContaSintetica.objects.filter(loja=loja_destino).count()
        if contas_existentes > 0:
            self.stdout.write(f"  [AVISO] Loja ja tem {contas_existentes} contas!")
            if not force:
                raise CommandError(
                    "Use --force para sobrescrever. "
                    "Isso deletara todas as contas existentes!"
                )
            self.stdout.write("  Deletando contas existentes...")
            ContaSintetica.objects.filter(loja=loja_destino).delete()
            self.stdout.write("  Contas deletadas.")

        # Verifica se modelo tem contas
        contas_modelo = ContaSintetica.objects.filter(
            loja=empresa_modelo,
            eh_modelo=True
        )
        if not contas_modelo.exists():
            raise CommandError("Empresa Modelo nao tem contas para importar!")
        self.stdout.write(f"  [OK] Empresa Modelo tem {contas_modelo.count()} contas")

        # =========================================
        # 2. IMPORTAR CONTAS SINTETICAS
        # =========================================
        self.stdout.write(f"\n[2] Importando contas sinteticas:")
        self.stdout.write("-" * 70)

        mapa_contas = {}  # modelo_id -> nova_conta
        criadas = 0

        for conta_modelo in contas_modelo.order_by('codigo_classificacao'):
            # Busca conta pai na nova loja (se houver)
            conta_pai = None
            if conta_modelo.conta_pai:
                conta_pai_id = mapa_contas.get(conta_modelo.conta_pai.id)
                if conta_pai_id:
                    conta_pai = ContaSintetica.objects.get(id=conta_pai_id)

            # Cria conta na nova loja
            nova_conta = ContaSintetica.objects.create(
                loja=loja_destino,
                codigo_classificacao=conta_modelo.codigo_classificacao,
                nome=conta_modelo.nome,
                tipo_conta=conta_modelo.tipo_conta,
                nivel=conta_modelo.nivel,
                conta_pai=conta_pai,
                eh_modelo=False,  # Copia, nao modelo
            )

            # Armazena para referencia
            mapa_contas[conta_modelo.id] = nova_conta.id
            criadas += 1

            # Mostrar progresso a cada 20 contas
            if criadas <= 10 or criadas % 20 == 0:
                self.stdout.write(
                    f"  {criadas:3d}. {conta_modelo.codigo_classificacao} - {conta_modelo.nome}"
                )

        self.stdout.write(f"  Total: {criadas} contas sinteticas criadas")

        # =========================================
        # 3. IMPORTAR CONTAS ANALITICAS
        # =========================================
        self.stdout.write(f"\n[3] Importando contas analiticas:")
        self.stdout.write("-" * 70)

        contas_analiticas_modelo = ContaAnalitica.objects.filter(
            loja=empresa_modelo,
            eh_modelo=True
        )

        criadas_analiticas = 0

        for ca_modelo in contas_analiticas_modelo:
            # Busca conta sintetica correspondente na nova loja
            try:
                nova_conta_sintetica = ContaSintetica.objects.get(
                    loja=loja_destino,
                    codigo_classificacao=ca_modelo.conta_sintetica.codigo_classificacao
                )
            except ContaSintetica.DoesNotExist:
                self.stdout.write(
                    f"  [AVISO] Conta sintetica {ca_modelo.conta_sintetica.codigo_classificacao} nao encontrada"
                )
                continue

            # Cria conta analitica na nova loja
            ContaAnalitica.objects.create(
                loja=loja_destino,
                codigo_reduzido=ca_modelo.codigo_reduzido,
                codigo_classificacao=ca_modelo.codigo_classificacao,
                nome=ca_modelo.nome,
                natureza_saldo=ca_modelo.natureza_saldo,
                aceita_lancamento=ca_modelo.aceita_lancamento,
                conta_sintetica=nova_conta_sintetica,
                eh_modelo=False,
            )
            criadas_analiticas += 1

        self.stdout.write(f"  Total: {criadas_analiticas} contas analiticas criadas")

        # =========================================
        # 4. RESUMO FINAL
        # =========================================
        self.stdout.write(f"\n[4] RESUMO FINAL:")
        self.stdout.write("=" * 70)

        cs_final = ContaSintetica.objects.filter(loja=loja_destino).count()
        ca_final = ContaAnalitica.objects.filter(loja=loja_destino).count()

        self.stdout.write(self.style.SUCCESS(
            f"[OK] Plano de contas importado com sucesso para {loja_destino.descricao}!"
        ))
        self.stdout.write(self.style.SUCCESS(f"     Contas sinteticas: {cs_final}"))
        self.stdout.write(self.style.SUCCESS(f"     Contas analiticas: {ca_final}"))

        self.stdout.write("\n" + "=" * 70)
