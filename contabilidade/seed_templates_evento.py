"""
Script para criar templates de exemplo de eventos e regras contábeis.
Use: python manage.py shell < seed_templates_evento.py
"""

from contabilidade.models import TemplateEventoRegra, EventoTemplate, RegraTemplate, PartidaRegraTemplate

# Template para Restaurante Padrão
template = TemplateEventoRegra.objects.create(
    nome='Restaurante Padrão',
    descricao='Template básico para restaurantes com eventos de venda, pagamento e devolução.',
    ativo=True,
)

# Evento: VENDA_REALIZADA
evento_venda = EventoTemplate.objects.create(
    template=template,
    codigo='VENDA_REALIZADA',
    descricao='Venda de produtos/serviços realizada',
    modulo_origem='CAIXA',
)

# Regra para VENDA_REALIZADA
# Débito: Caixa | Crédito: Receita de Vendas
regra_venda = RegraTemplate.objects.create(
    template=template,
    evento=evento_venda,
    descricao='Débito Caixa - Crédito Receita',
    ativa=True,
)

# Partidas da regra de venda (comentadas - será necessário ajustar aos códigos da loja)
# PartidaRegraTemplate.objects.create(
#     regra=regra_venda,
#     tipo='D',
#     codigo_conta='1.1.1.01.0001',  # Caixa
#     ordem=1,
# )
# PartidaRegraTemplate.objects.create(
#     regra=regra_venda,
#     tipo='C',
#     codigo_conta='3.1.1.01.0001',  # Receita de Vendas
#     ordem=1,
# )

# Evento: PAGAMENTO_RECEBIDO
evento_pagamento = EventoTemplate.objects.create(
    template=template,
    codigo='PAGAMENTO_RECEBIDO',
    descricao='Recebimento de pagamento de cliente',
    modulo_origem='CAIXA',
)

# Regra para PAGAMENTO_RECEBIDO
regra_pagamento = RegraTemplate.objects.create(
    template=template,
    evento=evento_pagamento,
    descricao='Débito Caixa - Crédito Contas a Receber',
    ativa=True,
)

# Evento: DEVOLUÇÃO_REALIZADA
evento_devolucao = EventoTemplate.objects.create(
    template=template,
    codigo='DEVOLUCAO_REALIZADA',
    descricao='Devolução de produto/serviço pelo cliente',
    modulo_origem='CAIXA',
)

# Regra para DEVOLUÇÃO (estorno de venda)
regra_devolucao = RegraTemplate.objects.create(
    template=template,
    evento=evento_devolucao,
    descricao='Crédito Caixa - Débito Receita (reverso)',
    ativa=True,
)

print(f'✓ Template "{template.nome}" criado com sucesso!')
print(f'  - {template.eventos.count()} eventos')
print(f'  - {template.regras.count()} regras')
print(f'\n⚠️ Nota: As partidas das regras foram comentadas.')
print(f'   Importe o Plano de Contas primeiro, depois ajuste os códigos das contas.')
