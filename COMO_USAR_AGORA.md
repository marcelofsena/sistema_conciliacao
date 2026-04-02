# 🎉 Como Criar Contas - Versão Melhorada

## Problema Identificado e Resolvido

**O que você disse:**
> "Clico em Salvar mas nada acontece"

**Causa:**
Você provavelmente estava tentando criar um conta com um **código que já existia**, e o formulário volta para corrigir, mas sem mensagem clara.

**Solução Implementada:**
✅ Agora o sistema mostra **mensagem de erro clara**
✅ Sugere o **próximo código automaticamente**
✅ Valida o código **antes de salvar**

---

## ✨ O Que Mudou

### Antes ❌
1. Clica em "+ Subconta"
2. Formulário abre (código em branco)
3. Digita um código qualquer
4. Clica "Salvar"
5. Nada acontece (erro silencioso)
6. Sem saber por que...

### Depois ✅
1. Clica em "+ Subconta"
2. Formulário abre com **card azul com sugestão**:
   ```
   💡 Sugestão: 1.1.4
   ```
3. Preenche com o código sugerido (ou outro único)
4. Clica "Salvar"
5. Se houver erro, mostra **mensagem clara em vermelho**
6. Se sucesso, volta com **mensagem verde de sucesso**

---

## 🚀 Como Usar Agora

### Criar Subconta (Forma Rápida)

**Exemplo: Adicionar "Dólar" sob "ATIVO CIRCULANTE"**

1. Vá para **Cadastros → Plano de Contas**
2. Selecione a loja
3. Clique em **"ATIVO CIRCULANTE"** (1.1) na árvore
4. Clique em **"+ Subconta"** (botão azul escuro, lado direito)
5. Formulário abre. Vê o card azul:
   ```
   💡 Sugestão: 1.1.5
   Conta Pai: [já preenchido] ATIVO CIRCULANTE
   Nível: [deixar 3]
   ```
6. Preencha:
   - **Código de Classificação**: `1.1.5` (ou use a sugestão)
   - **Nome da Conta**: `Dólar`
   - **Tipo**: `ATIVO` (herda automaticamente)
7. Clique **"💾 Salvar"**
8. ✅ Volta para Plano de Contas
9. ✅ "Dólar" aparece na árvore sob "ATIVO CIRCULANTE"

---

## 📝 Regras Importantes

### ✅ Código Correto
```
1, 1.1, 1.1.1, 1.1.1.1
```
Apenas números e pontos. Nada mais!

### ❌ Erros Comuns
```
"1 1 1"        ← espaços
"1,1,1"        ← vírgulas
"1A"           ← letras
"1.1."         ← ponto final
```

### 💡 O Nível Deve Bater
```
Código 1      → Nível 1
Código 1.1    → Nível 2
Código 1.1.1  → Nível 3
```

Conte os números separados por ponto!

---

## 🎯 Fluxos Disponíveis

### 1. Criar Conta Raiz (novo tipo)
```
Topbar "➕ Nova Sintética"
  → Preenche código "6"
  → Preenche nome "CRIPTOMOEDAS"
  → Seleciona tipo "ATIVO"
  → Nível "1"
  → Salva
```

### 2. Criar Subconta (recomendado!)
```
Clica na conta pai na árvore
  → Botão "+ Subconta" aparece
  → Clica "+ Subconta"
  → Vê sugestão de código 💡
  → Preenche nome
  → Salva ✅
```

### 3. Criar Conta Analítica
```
Seleciona uma sintética
  → Clica "➕ Nova analítica"
  → Preenche dados
  → Salva (pronto para lançamentos!)
```

---

## ❌ Se der erro ao salvar

### "Este código já existe nesta loja"
```
Solução: Use outro código
Exemplo: Se sugeriu 1.1.5, use 1.1.5 e não 1.1.4
```

### "Este campo é obrigatório"
```
Solução: Preencha CÓDIGO, NOME e TIPO
Deixe Conta Pai vazio se é raiz
```

### "Nível deve ser número"
```
Solução: Digite um número (1, 2, 3, etc.)
Corresponda ao número de pontos no código
```

### Nada acontece ao clicar Salvar
```
1. Atualize a página (F5)
2. Tente novamente
3. Verifique se há erro em vermelho
4. Leia a mensagem cuidadosamente
```

---

## 🔍 Como Verificar se a Conta Foi Criada

1. ✅ Volta automaticamente para Plano de Contas
2. ✅ Mostra mensagem verde "Conta sintética criada com sucesso!"
3. ✅ Conta aparece na árvore (esquerda) com o código

Se não aparecer:
1. Atualize a página (F5)
2. Verifique que **selecionou a loja correta**
3. Se ainda não aparece, vá ao **Django Admin**:
   ```
   http://localhost:8000/admin/contabilidade/contasintetica/
   Procure pelo código que criou
   ```

---

## 💡 Dicas de Eficiência

### Use as Sugestões
- Sistema sugere o **próximo código automaticamente** ✨
- Clique "Sugestão" e não precisa digitar
- Evita erros de duplicação

### Organize Antes
- Pense na hierarquia antes
- Exemplo:
  ```
  6: CRIPTOMOEDAS (raiz)
    6.1: Bitcoin (filha)
    6.2: Ethereum (filha)
    6.3: Stablecoin (filha)
  ```

### Crie Analíticas Depois
1. Crie a árvore de sintéticas
2. Depois crie as analíticas (para lançamentos)
3. Assim fica organizado

---

## 📚 Estrutura Recomendada

```
1: ATIVO (raiz)
├── 1.1: ATIVO CIRCULANTE
│   ├── 1.1.1: Caixa
│   │   └── 0001: Caixa Física [ANALÍTICA]
│   ├── 1.1.2: Banco
│   │   ├── 0002: Conta Corrente [ANALÍTICA]
│   │   └── 0003: Poupança [ANALÍTICA]
│   └── 1.1.3: Estoques
│       └── 0004: Estoque Geral [ANALÍTICA]
└── 1.2: ATIVO NÃO CIRCULANTE
    └── 1.2.1: Imobilizado
        └── 0005: Móveis e Utensílios [ANALÍTICA]
```

---

## ✅ Próximos Passos

Depois de criar as contas sintéticas:

1. ✅ Crie contas **analíticas** (para lançamentos reais)
2. ⏭️ Configure **Regras Contábeis** (Contabilidade → Regras)
3. ⏭️ Crie **Períodos Contábeis** (Contabilidade → Períodos)
4. ⏭️ Faça primeiros **Lançamentos** (Contabilidade → Lançamentos)

---

## 🎬 Tente Agora!

1. Abra: **Cadastros → Plano de Contas**
2. Selecione loja
3. Clique em uma conta
4. Clique "+ Subconta"
5. Veja a **sugestão de código**
6. Preencha **Nome**
7. Clique **"💾 Salvar"**
8. ✅ Pronto!

**Qualquer problema, leia `TROUBLESHOOTING_CONTAS.md`!** 📖
