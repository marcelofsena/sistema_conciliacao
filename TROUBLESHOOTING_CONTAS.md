# 🔧 Troubleshooting: Problemas ao Criar Contas Sintéticas

## ❌ "Clico em Salvar mas nada acontece"

Esse problema geralmente significa que o **formulário tem erros de validação** mas você não está vendo a mensagem. Aqui estão as causas mais comuns:

---

## 1️⃣ Código Duplicado (Mais Comum!)

### ❌ Erro
```
Você tenta criar uma conta com código "1.1.1"
Mas já existe outra conta com o mesmo código na loja
```

### ✅ Solução
**O sistema agora mostra a sugestão automática!**

Quando você clica em "+ Subconta" de uma conta, o formulário abre com um card azul:

```
💡 Sugestão: 1.1.4
```

Use exatamente esse código ou customize (1.1.5, 1.1.6, etc.)

### 📋 Verificar Códigos Existentes
1. Na tela de Plano de Contas, veja a árvore esquerda
2. Clique em cada conta para ver seu código no painel direito
3. Não use os códigos que já existem

---

## 2️⃣ Código em Formato Inválido

### ❌ Erros Comuns
```
Código: "1 1 1"        ❌ (com espaços)
Código: "1.1.1."       ❌ (ponto no final)
Código: "1a1"          ❌ (com letras)
Código: "1,1,1"        ❌ (com vírgula)
```

### ✅ Formato Correto
```
1              ✅ (raiz)
1.1            ✅ (filho)
1.1.1          ✅ (neto)
1.1.1.1        ✅ (bisneto)
```

Use **apenas números e pontos**. Nada mais!

---

## 3️⃣ Nível Incorreto

### ❌ Erro
```
Código: "1.1.1"  (3 níveis)
Nível: 1         ❌ (deveria ser 3!)
```

### ✅ Forma Correta
O nível deve corresponder ao número de "pontos" no código:
```
1       → Nível 1 (raiz)
1.1     → Nível 2
1.1.1   → Nível 3
1.1.1.1 → Nível 4
```

**Dica**: Conte os números separados por ponto!

---

## 4️⃣ Campos Vazios

### ❌ Campos Obrigatórios
Todos estes **devem** ser preenchidos:
- ✋ Código de Classificação
- ✋ Nome da Conta
- ✋ Tipo (ATIVO, PASSIVO, RECEITA, CUSTO, DESPESA)
- ✋ Nível Hierárquico

### ✅ Campos Opcionais
Estes podem ficar vazios:
- ✓ Conta Pai (deixe vazio se é raiz)

---

## 5️⃣ Tipo de Conta Não Encontrado

### ❌ Erro
```
Tipo: [vazio]  ❌ Selecione um tipo!
```

### ✅ Solução
Clique em "Tipo" e selecione um:
- ATIVO
- PASSIVO
- RECEITA
- CUSTO
- DESPESA

Se não aparecer nenhuma opção, o tipo pode não estar criado no admin.

---

## 🎯 Passo a Passo: Criar Conta Corretamente

### Cenário: Adicionar "Bitcoin" em "ATIVO CIRCULANTE"

**Passo 1**: Abra Plano de Contas
```
Cadastros → Plano de Contas → Selecione a loja
```

**Passo 2**: Na árvore, clique em "ATIVO CIRCULANTE" (1.1)
```
Vê no painel direito:
  Código: 1.1
  Tipo: ATIVO
  Nível: 2
  Conta Pai: ATIVO
```

**Passo 3**: Clique em "+ Subconta"
```
Formulário abre com:
  Conta Pai: ✅ [pré-selecionado] ATIVO CIRCULANTE
  Sugestão de Código: 💡 1.1.4
```

**Passo 4**: Preencha os campos
```
Código de Classificação: 1.1.4        ← Use a sugestão!
Nome da Conta:           Bitcoin       ← Nome descritivo
Tipo:                    ATIVO         ← Herda do pai
Nível:                   3             ← Sempre 3 para neto
Conta Pai:               [já preenchido]
```

**Passo 5**: Clique em "💾 Salvar"
```
✅ Mensagem: "Conta sintética criada com sucesso!"
✅ Volta para Plano de Contas
✅ Bitcoin aparece na árvore sob ATIVO CIRCULANTE
```

---

## 🔍 Verificar se a Conta Foi Criada

### Se o formulário retornar com erro:
1. **Leia a mensagem vermelha** (agora é mais clara!)
2. **Corrija o problema** apontado
3. **Tente novamente**

### Se a mensagem desaparecer mas nada acontece:
1. Aguarde 2-3 segundos (pode estar salvando)
2. Atualize a página (F5)
3. Verifique se a conta aparece na árvore

### Se a conta não aparece na árvore:
1. Verifique que selecionou a **loja correta** no seletor
2. Atualize a página (F5)
3. Se ainda não aparecer, verifique no admin Django:
   ```
   http://localhost:8000/admin/contabilidade/contasintetica/
   ```

---

## 📋 Checklist Antes de Salvar

- [ ] Código é **numérico com pontos** apenas (ex: 1.1.1)
- [ ] Código não é **duplicado** na loja
- [ ] **Nível** corresponde ao número de números no código
- [ ] **Nome** não está vazio
- [ ] **Tipo** está selecionado (ATIVO, PASSIVO, etc.)
- [ ] Se criando **subconta**, Conta Pai está pré-selecionado

---

## 💬 Mensagens de Erro Explicadas

### "Este código '1.1.1' já existe nesta loja"
```
Causa: Você tentou criar uma conta com código que já existe
Solução: Use outro código (ex: 1.1.4, 1.1.5)
```

### "Código é obrigatório"
```
Causa: Deixou o campo de código vazio
Solução: Preencha com código válido (ex: 1.1.1)
```

### "Este campo é obrigatório"
```
Causa: Deixou algum campo obrigatório vazio
Solução: Preencha NOME, TIPO e NÍVEL
```

---

## 🆘 Se Nada Funcionar

### Passos de Emergência:

**Passo 1**: Limpe o cache do navegador
```
Ctrl + Shift + Delete → Apague "Cookies and Cached Images"
```

**Passo 2**: Tente em outro navegador (Chrome, Firefox, Edge)

**Passo 3**: Verifique a console do navegador (F12)
```
Abra: F12 → Aba "Console"
Procure por mensagens vermelhas (erro)
Copie a mensagem e compartilhe
```

**Passo 4**: Verifique logs do servidor
```
bash
python manage.py runserver > debug.log 2>&1
```
Procure por erros no arquivo `debug.log`

---

## 📞 Antes de Chamar Suporte

Tenha pronto:
1. Screenshot do formulário preenchido
2. Screenshot da mensagem de erro (se houver)
3. O código exato que tentou usar
4. Qual é a conta pai (se criando subconta)
5. Qual é a loja selecionada

---

## ✅ Resumo das Melhorias Recentes

O sistema agora:
- ✅ Sugere automaticamente o **próximo código** válido
- ✅ Valida se código é **duplicado** (aviso claro)
- ✅ Valida se código é **válido** (formato correto)
- ✅ **Pré-seleciona** conta pai ao criar subconta
- ✅ **Feedback claro** em caso de erro

**Tente novamente agora e veja se funciona!** 🎉
