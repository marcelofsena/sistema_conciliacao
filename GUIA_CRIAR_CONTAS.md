# 📝 Guia: Como Criar Novas Contas no Plano de Contas

Depois de importar um template, você pode criar novas contas facilmente. Aqui estão as formas disponíveis:

## 1️⃣ Criar Conta Sintética Raiz (Novo tipo)

### Via Topbar (mais rápido)
1. Vá para **Cadastros → Plano de Contas**
2. Selecione a loja
3. Clique no botão **"➕ Nova Sintética"** (no topo direito)
4. Preencha os dados:
   - **Código de Classificação**: `6` (número único)
   - **Nível**: `1` (é uma raiz)
   - **Nome**: ex. "INVESTIMENTOS"
   - **Tipo**: ATIVO, PASSIVO, RECEITA, CUSTO ou DESPESA
   - **Conta Pai**: deixe vazio (é raiz)
5. Clique **"💾 Salvar"**

### Via Sidebar (se plano está vazio)
1. No painel esquerdo, clique no botão **"+"** ao lado de "🌳 Contas Sintéticas"
2. Mesmo processo acima

---

## 2️⃣ Criar Subconta (Dentro de uma Conta Existente)

### Forma Rápida (Recomendada!)
1. Vá para **Cadastros → Plano de Contas**
2. Selecione a loja
3. **Clique no nome da conta pai** (ex: "ATIVO CIRCULANTE") na árvore
4. No painel direito, verá o card azul com a dica: **"💡 Quer adicionar uma nova conta no mesmo nível desta?"**
5. Clique em **"➕ Criar nova Sintética"**
6. O formulário abre **com a conta pai já pré-selecionada!** ✨
7. Preencha:
   - **Código**: ex. `1.1.4` (mantendo a hierarquia)
   - **Nível**: `3` (ou qual for apropriado)
   - **Nome**: ex. "Criptomoedas"
   - **Tipo**: ATIVO (herda do pai, mas pode mudar)
8. Clique **"💾 Salvar"**

### Forma Alternativa (Button "Subconta")
1. Na tela de Plano de Contas, selecione uma conta
2. Clique no botão **"+ Subconta"** (ao lado de "✏️ Editar")
3. Igual ao processo acima, mas pré-seleciona automaticamente

---

## 3️⃣ Criar Conta Analítica (Para Lançamentos)

### Quando Usar
Contas **analíticas** são onde você realmente faz os lançamentos contábeis. Criei uma para cada sintética depois de criar a hierarquia sintética.

### Como Criar
1. Vá para **Cadastros → Plano de Contas**
2. Selecione a loja
3. **Clique em uma Conta Sintética** (no painel esquerdo)
4. No painel direito, veja a tabela "📋 Contas Analíticas"
5. Clique **"➕ Nova analítica"** (se a tabela está vazia)
6. Preencha:
   - **Código reduzido**: ex. `1.1.1.1` ou `0001`
   - **Código de Classificação**: ex. `1.1.1.1` (igual ao da sintética)
   - **Nome**: ex. "Caixa Física"
   - **Natureza do Saldo**: DEVEDOR ou CREDOR
   - **Aceita Lançamento**: marque (caso contrário fica bloqueada)
7. Clique **"Criar conta"**

---

## 📊 Exemplo Completo: Adicionar "Criptomoedas"

Você importou o template e quer adicionar uma nova classe de ativo.

### Passo a Passo

**Passo 1**: Abra Plano de Contas e selecione a loja

**Passo 2**: Clique em "ATIVO" (na árvore)
- Vê no painel direito: "Código: 1, Tipo: ATIVO, Nível 1"

**Passo 3**: Clique no card azul "➕ Criar nova Sintética"

**Passo 4**: Preencha o formulário que abre:
```
Código de Classificação: 6
Nível: 1
Nome: CRIPTOMOEDAS
Tipo: ATIVO
Conta Pai: [vazio - é raiz no mesmo nível que ATIVO]
```
Salve.

**Passo 5**: Agora crie a subconta:
- Clique em "CRIPTOMOEDAS" (nova conta criada)
- Clique "➕ Criar nova Sintética"
- Preencha:
```
Código de Classificação: 6.1
Nível: 2
Nome: Bitcoin
Tipo: ATIVO
Conta Pai: CRIPTOMOEDAS (auto-selecionado!)
```
Salve.

**Passo 6**: Agora crie uma analítica:
- Com "Bitcoin" ainda selecionada
- Clique "➕ Nova analítica"
- Preencha:
```
Código Reduzido: 0001
Código de Classificação: 6.1
Nome: Carteira Fria - Empresa
Natureza: DEVEDOR
Aceita Lançamento: ✓ (marcado)
```
Salve.

**Pronto!** ✅ Agora você pode lançar valores em "Carteira Fria - Empresa"

---

## 💡 Dicas Importantes

### ✅ Faça Assim
- **Pense em hierarquia**: Sempre crie a sintética ANTES da analítica
- **Siga a numeração**: 1, 1.1, 1.1.1 (decimal, não arbitrário)
- **Mantenha o padrão**: Se o template usa "Caixa e Equivalentes", mantenha esse padrão para novas contas
- **Dê nomes descritivos**: "Caixa Física - Gerência" é melhor que "Caixa 1"

### ❌ Não Faça Assim
- Criar contas analíticas sem uma sintética pai
- Usar códigos duplicados (ex. duas contas "1.1")
- Mudar o tipo (ATIVO) de uma conta que já tem lançamentos
- Deletar uma conta pai que tem filhas (vai quebrar a hierarquia)

---

## 🎯 Estrutura Recomendada Pós-Importação

```
ATIVO (1)                           [Raiz - Nível 1]
├── ATIVO CIRCULANTE (1.1)          [Síntética - Nível 2]
│   ├── Caixa (1.1.1)               [Síntética - Nível 3]
│   │   ├── 0001: Caixa Física      [Analítica - onde lança]
│   │   └── 0002: Caixa Gerência    [Analítica - onde lança]
│   └── Banco (1.1.2)               [Síntética - Nível 3]
│       ├── 0003: Banco - Conta Corrente [Analítica]
│       └── 0004: Banco - Poupança  [Analítica]
└── ATIVO NÃO CIRCULANTE (1.2)     [Síntética - Nível 2]
    └── Imobilizado (1.2.1)         [Síntética - Nível 3]
        └── 0005: Móveis e Utensílios [Analítica]
```

---

## 🔄 Fluxo Visual

```
┌─────────────────────────────────────┐
│ Plano de Contas (com loja selecionada)
│                                     │
│ Sidebar (Esquerda)  │  Painel (Direita)
├─────────────────────┼────────────────┤
│ 🌳 Contas Sintéticas│                │
│ + (novo)            │ [Selecione]    │
│                     │                │
│ 1: ATIVO            │ (nada mostra)  │
│   1.1: CIRC         │                │
│   1.2: N.CIRC       │ Clique em 1.1  │
│ 2: PASSIVO          │      ↓         │
│   2.1: ...          │ ┌──────────────┤
│ 3: RECEITA          │ │ 1.1 -CIRC    │
│                     │ │ [✏️] [+Sub] │
│ ← Clique aqui       │ │              │
│   (em 1.1)          │ │ 💡 Quer...?  │
│                     │ │ [➕ Criar]   │
│                     │ │              │
│                     │ │ 📋 Analíticas│
│                     │ │ [➕ Nova] ◄─ Cria analítica
│                     │ └──────────────┤
│                     │                │
└─────────────────────┴────────────────┘
```

---

## ❓ Dúvidas Frequentes

### P: Posso editar uma conta depois de criada?
**R**: Sim! Clique em "✏️ Editar" na painel direito. Você pode mudar nome, código e tipo (evite mudar tipo se já tem lançamentos).

### P: Como deletar uma conta?
**R**: Ainda não há botão de deletar na interface. Se precisar, use o Django Admin:
```
http://localhost:8000/admin/contabilidade/contasintetica/
```

### P: Qual é a diferença entre Sintética e Analítica?
**R**:
- **Sintética**: Agrupa contas para relatórios (não usa em lançamentos diretos)
- **Analítica**: Usada nos lançamentos (é onde o dinheiro realmente vai)

### P: Posso deixar uma Sintética sem Analíticas?
**R**: Sim, mas você não conseguirá fazer lançamentos nela. Use apenas para agrupar.

### P: Como voltar para a lista de contas depois de editar?
**R**: Botão "Cancelar" no formulário ou clique em "Plano de Contas" no breadcrumb.

---

## 📈 Próximas Ações Recomendadas

Depois de importar e customizar o plano:

1. ✅ Importar template "Restaurante Brasileiro"
2. ✅ Criar contas analíticas para cada sintética (onde vai lançar)
3. ✅ Adicionar contas específicas da sua loja (ex. Criptomoedas, fornecedores específicos)
4. ⏭️ Configurar **Regras Contábeis** para eventos (vai para Contabilidade → Regras)
5. ⏭️ Criar **Períodos Contábeis** (vai para Contabilidade → Períodos)
6. ⏭️ Fazer primeiros **Lançamentos Contábeis** (vai para Contabilidade → Lançamentos)

---

## 🆘 Precisa de Ajuda?

Se não encontrar a opção de criar conta:
1. Verifique se **selecionou a loja** no seletor no topo
2. Verifique se tem **acesso à loja** (é ADMIN ou está em lojas_permitidas)
3. Verifique se o plano de contas **não está vazio** (importe um template primeiro)

Se ainda não funcionar, contate o suporte! 📞
