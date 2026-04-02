"""
Core - Modelos base do sistema ERP Retaguarda.

Contém:
- Empresa/Loja: Cadastro multi-loja (SaaS) com separação via loja_id
- PerfilUsuario: Controle de acesso (ADMIN/OPERADOR)
- AuditoriaMixin: Mixin abstrato para rastreabilidade (quem/quando)
- RegistroAuditoria: Log de auditoria obrigatória (antes/depois)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ==========================================
# MIXIN DE AUDITORIA (ABSTRATO)
# ==========================================

class AuditoriaMixin(models.Model):
    """
    Mixin abstrato que adiciona campos de rastreabilidade a qualquer modelo.
    Conforme regra de negócio: "Quem fez, Quando".
    """
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    criado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_criados", verbose_name="Criado por"
    )
    atualizado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="%(class)s_atualizados", verbose_name="Atualizado por"
    )

    class Meta:
        abstract = True


# ==========================================
# EMPRESA / LOJA
# ==========================================

class Empresa(models.Model):
    """
    Cadastro de lojas/empresas do sistema multi-loja.
    Cada loja possui códigos de integração com sistemas externos
    (SWFast, Stone, iFood, Mercado Pago).
    """
    id_empresa = models.AutoField(primary_key=True)
    descricao = models.CharField(max_length=255, verbose_name="Descrição da Empresa")
    cnpj = models.CharField(max_length=18, blank=True, null=True, unique=True, verbose_name="CNPJ")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")

    # Códigos de integração com sistemas externos
    ncad_cartoes = models.IntegerField(default=0, verbose_name="Cad. Cartões (Stone)")
    ncad_ifood = models.IntegerField(default=0, verbose_name="Cad. iFood")
    ncad_mp = models.IntegerField(default=0, verbose_name="Cad. Mercado Pago")
    ncad_outros = models.IntegerField(default=0, verbose_name="Cad. Outros")
    ncad_swfast = models.IntegerField(default=0, verbose_name="Cad. SWFast (PDV)")

    OPCOES_INTEGRADO = [
        ('Sim', 'Sim'),
        ('Não', 'Não'),
    ]
    integrado = models.CharField(
        max_length=3, choices=OPCOES_INTEGRADO, default='Não',
        verbose_name="Integrado com PDV"
    )

    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    class Meta:
        db_table = 'tbl_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


# ==========================================
# PERFIL DE USUARIO (CONTROLE DE ACESSO)
# ==========================================

class PerfilUsuario(models.Model):
    """
    Controle de acesso multi-loja.
    ADMIN: vê todas as lojas.
    OPERADOR: vê apenas lojas vinculadas.
    """
    TIPO_ACESSO_CHOICES = [
        ('ADMIN', 'Administrador (Vê todas as lojas)'),
        ('OPERADOR', 'Operador (Vê apenas lojas permitidas)'),
    ]

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='perfil'
    )
    tipo_acesso = models.CharField(
        max_length=20, choices=TIPO_ACESSO_CHOICES, default='OPERADOR'
    )
    lojas_permitidas = models.ManyToManyField(
        Empresa, blank=True,
        verbose_name="Lojas Permitidas para este Operador"
    )

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_acesso_display()}"

    def get_lojas(self):
        """Retorna queryset de lojas acessíveis pelo usuário."""
        if self.tipo_acesso == 'ADMIN':
            return Empresa.objects.filter(ativa=True)
        return self.lojas_permitidas.filter(ativa=True)


def get_perfil_usuario(usuario):
    """
    Obtém ou cria o PerfilUsuario para um User.
    Se o usuário é superuser, cria com tipo_acesso ADMIN.
    Caso contrário, cria com tipo_acesso OPERADOR (padrão).
    """
    perfil, created = PerfilUsuario.objects.get_or_create(
        usuario=usuario,
        defaults={'tipo_acesso': 'ADMIN' if usuario.is_superuser else 'OPERADOR'}
    )
    return perfil


# ==========================================
# REGISTRO DE AUDITORIA
# ==========================================

class RegistroAuditoria(models.Model):
    """
    Log de auditoria obrigatória conforme regra de negócio:
    "Qualquer ajuste manual ou divergência exigirá registro de auditoria
    (Quem fez, Quando, Motivo, e snapshot do Antes/Depois)."

    Não é obrigatório se o usuário tem permissão específica.
    """
    TIPO_ACAO_CHOICES = [
        ('CRIACAO', 'Criação'),
        ('ALTERACAO', 'Alteração'),
        ('EXCLUSAO', 'Exclusão'),
        ('ESTORNO', 'Estorno'),
        ('AJUSTE', 'Ajuste Manual'),
        ('REABERTURA', 'Reabertura de Período'),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        verbose_name="Usuário"
    )
    loja = models.ForeignKey(
        Empresa, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Loja"
    )
    data_hora = models.DateTimeField(default=timezone.now, verbose_name="Data/Hora")
    tipo_acao = models.CharField(
        max_length=20, choices=TIPO_ACAO_CHOICES, verbose_name="Tipo de Ação"
    )
    modelo = models.CharField(max_length=100, verbose_name="Modelo/Tabela")
    objeto_id = models.CharField(max_length=100, verbose_name="ID do Objeto")
    motivo = models.TextField(blank=True, verbose_name="Motivo")
    snapshot_antes = models.JSONField(null=True, blank=True, verbose_name="Snapshot Antes")
    snapshot_depois = models.JSONField(null=True, blank=True, verbose_name="Snapshot Depois")

    class Meta:
        verbose_name = 'Registro de Auditoria'
        verbose_name_plural = 'Registros de Auditoria'
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['modelo', 'objeto_id']),
            models.Index(fields=['data_hora']),
            models.Index(fields=['usuario']),
        ]

    def __str__(self):
        return f"{self.tipo_acao} - {self.modelo}:{self.objeto_id} por {self.usuario} em {self.data_hora}"
