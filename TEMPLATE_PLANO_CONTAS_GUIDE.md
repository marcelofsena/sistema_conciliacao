# Guia: Sistema de Templates de Plano de Contas

## O Que Foi Implementado

Um sistema **template-based** para plano de contas que permite:

1. **Reutilização**: Modelos prontos podem ser importados em qualquer loja
2. **Flexibilidade**: Cada loja tem seu próprio plano, mas pode partir de um template
3. **Customização**: Após importação, contas podem ser editadas, adicionadas ou removidas
4. **Escalabilidade**: Novos templates podem ser criados para diferentes tipos de negócio

## Arquitetura

### Modelos de Dados

```python
TemplateplanoConta
├── nome: CharField                    # "Restaurante Brasileiro"
├── descricao: TextField               # Descreve o template
├── ativo: BooleanField                # Se está disponível para import
├── contas: M2M → ContaTemplate        # Contas do template
└── criado_em: DateTimeField

ContaTemplate
├── template: ForeignKey → TemplateplanoConta
├── codigo_classificacao: CharField    # "1.1.1"
├── nome: CharField                    # "Caixa"
├── tipo_conta: CharField              # "ATIVO", "PASSIVO", "RECEITA", "CUSTO", "DESPESA"
├── pai_codigo: CharField (nullable)   # "1.1" para hierarquia
└── nivel: PositiveIntegerField        # Profundidade na árvore
```

### Fluxo

```
Usuário acessa Plano de Contas (loja vazia)
    ↓
Clica "Importar Template"
    ↓
Vê lista de templates disponíveis
    ↓
Clica "Importar Template"
    ↓
Seleciona a loja de destino
    ↓
Sistema cria ContaSintetica records
    (uma para cada ContaTemplate do template)
    ↓
Contas aparecem na árvore de Plano de Contas
    ↓
Usuário pode editar, adicionar ou remover contas conforme necessário
```

## Como Usar

### 1. Acessar Templates (Novo Usuário)

1. Vá para **Cadastros → Plano de Contas**
2. Se a loja está vazia, clique em **"📥 Importar Template"**
3. Selecione o template desejado (ex: "Restaurante Brasileiro")
4. Clique em **"Importar Template"** no card
5. Selecione a loja de destino
6. Confirme a importação

### 2. Acessar Templates (Qualquer Usuário)

- Vá para **Cadastros → Templates de Contas**
- Veja lista de todos os templates disponíveis
- Clique em **"📥 Importar Template"** para qualquer um

### 3. Estrutura do Template Restaurante Brasileiro

O template "Restaurante Brasileiro" inclui **130 contas** organizadas em:

#### ATIVO (26 contas)
- Caixa e Equivalentes (4 contas)
- Contas a Receber (5 contas)
- Estoques (3 contas)
- Investimentos (1 conta)
- Imobilizado (3 contas)
- Intangível (1 conta)

#### PASSIVO (28 contas)
- Fornecedores (3 contas)
- Contas a Pagar (3 contas)
- Obrigações Trabalhistas (3 contas)
- Impostos e Taxas (4 contas)
- Empréstimos CP (2 contas)
- Empréstimos LP (2 contas)
- Capital Social (1 conta)
- Lucros/Prejuízos (2 contas)

#### RECEITAS (14 contas)
- Vendas de Alimentos e Bebidas (4 contas)
- Serviços Prestados (2 contas)
- Outras Receitas Operacionais (1 conta)
- Receitas Financeiras (2 contas)

#### CUSTOS (12 contas)
- CMV - Alimentos (3 contas)
- CMV - Bebidas (3 contas)
- CMV - Insumos (2 contas)

#### DESPESAS (50 contas)
- Salários e Ordenados (4 contas)
- Encargos Sociais (3 contas)
- Benefícios a Empregados (3 contas)
- Aluguel e Imóvel (5 contas)
- Utilidades (4 contas)
- Marketing (3 contas)
- Administrativo (4 contas)
- Equipamentos (3 contas)
- Financeiras (3 contas)

## Recursos Multi-Loja

### Controle de Acesso

- **ADMIN**: Podem importar templates para qualquer loja
- **OPERADOR**: Podem importar templates apenas para lojas designadas (lojas_permitidas)

### Validação

O sistema valida:
- Acesso do usuário à loja de destino
- Se a loja já tem contas (impede duplicação)
- Integridade da hierarquia (contas pai são criadas antes das filhas)

## Próximos Passos (Opcional)

### Criar Novos Templates

1. No admin Django, vá para **Contabilidade → Templates Plano de Contas**
2. Clique em "Adicionar Template"
3. Preencha nome e descrição
4. Salve
5. Na seção de contas (inline), adicione as contas do template
6. Ao importar, o sistema cria os registros ContaSintetica automaticamente

### Deletar Contas de Uma Loja

Se precisar limpar uma loja e reimportar:

```bash
python manage.py shell
```

```python
from contabilidade.models import ContaSintetica
from core.models import Empresa

loja = Empresa.objects.get(pk=1)
ContaSintetica.objects.filter(loja=loja).delete()
```

Depois reimporte o template.

## Arquivo de Dados

**create_template_restaurante.py** - Script que criou o template com 130 contas

- Pode ser reexecutado para atualizar o template se necessário
- Usa `get_or_create` então é seguro reexecuar
- Atualiza contas existentes automaticamente

## API/URLs

| Rota | View | Descrição |
|------|------|-----------|
| `/contabilidade/templates-plano/` | `templates_plano_contas` | Lista templates |
| `/contabilidade/templates-plano/<id>/importar/` | `importar_template_plano` | Importa template |

## Arquivos Afetados

```
contabilidade/
├── models.py                 # +TemplateplanoConta, ContaTemplate
├── views.py                  # +templates_plano_contas, importar_template_plano
├── urls.py                   # +2 rotas de template
├── admin.py                  # +TemplatePlanoContaAdmin, ContaTemplateAdmin
├── templates/
│   └── contabilidade/
│       ├── templates_plano_contas.html          # Lista de templates
│       ├── importar_template_plano.html         # Formulário de import
│       └── plano_contas.html                   # Link para import (modificado)
└── migrations/
    └── 0003_templateplanoconta_contatemplate.py # Novas tabelas

templates/
└── base.html                # Adicionado link no sidebar

scripts/
└── create_template_restaurante.py # Cria o template com 130 contas
```

## Troubleshooting

### "Loja já possui contas"

O sistema impede importar para loja que já tem contas. Para resetar:

```bash
python manage.py shell
```

```python
from contabilidade.models import ContaSintetica
loja = Empresa.objects.get(pk=1)
ContaSintetica.objects.filter(loja=loja).delete()
```

### Template não aparece

- Verifique que `ativo=True` no template
- Verifique permissões de usuário (lojas_permitidas)

### Contas não aparecem após importação

- Atualize a página
- Verifique que selecionou a loja correta
- Verifique logs: `python manage.py shell`

```python
from contabilidade.models import ContaSintetica
from core.models import Empresa
loja = Empresa.objects.get(pk=1)
ContaSintetica.objects.filter(loja=loja).count()  # Deve ser 130
```

## Comparativo: Antes vs Depois

### Antes (Estado Anterior)
- ❌ Contas hardcoded em script `insert_remaining_accounts.py`
- ❌ Contas inseridas diretamente em Loja 1
- ❌ Sem reutilização em outras lojas
- ❌ Sem interface para visualizar templates
- ❌ Sem controle de acesso a templates

### Depois (Atual)
- ✅ Templates reutilizáveis em múltiplas lojas
- ✅ Interface amigável para visualizar templates
- ✅ Importação automática com hierarquia
- ✅ Controle de acesso por loja
- ✅ Validação de estado (evita duplicação)
- ✅ Customização após importação

## Resumo

O sistema de templates resolve o problema arquitetural de ter contas hard-coded em uma única loja. Agora:

1. **Templates são reutilizáveis** - O mesmo "Restaurante Brasileiro" pode ser importado por múltiplas lojas
2. **Usuários têm escolha** - Podem importar um template pronto ou criar contas manualmente
3. **Escalável** - Novos templates podem ser criados para outros tipos de negócio
4. **Multi-tenant seguro** - Cada loja tem seu próprio conjunto de contas, mas parte de um template comum
