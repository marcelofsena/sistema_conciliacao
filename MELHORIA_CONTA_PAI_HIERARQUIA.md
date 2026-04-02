# ✨ Melhoria: Campo "Conta Pai" com Hierarquia Visual

## Seu Problema

> "A forma como conta pai (hierarquia) não ficou legal, pois o usuário tem adivinhar o código de codificação. Analise o que podemos fazer para melhorar isso para o usuário."

### O Que Estava Errado

Quando criava uma nova conta, o campo "Conta Pai" mostrava apenas:
```
Conta Pai: [ — Nenhuma (raiz) — ]

(Dropdown com opções impossíveis de ler)
```

Clicava no dropdown e via:
```
1.1
1.1.1
1.1.1.1
1.1.2
1.1.3
```

**Problema:** O usuário não sabia qual era o **nome** de cada conta, só via o código!

---

## ✅ A Solução Implementada

### Nova Exibição (Muito Melhor!)

Agora o dropdown mostra:
```
— Nenhuma (raiz) —
• 1 - ATIVO
  • 1.1 - ATIVO CIRCULANTE
    • 1.1.1 - Disponibilidades
    • 1.1.2 - Contas a Receber
    • 1.1.3 - Estoques
  • 1.2 - ATIVO NÃO CIRCULANTE
• 2 - PASSIVO
  • 2.1 - PASSIVO CIRCULANTE
    • 2.1.1 - Fornecedores
    • 2.1.2 - Contas a Pagar
```

### Melhorias

1. **Código + Nome**: Mostra `"1.1 - ATIVO CIRCULANTE"` ao invés de só `"1.1"`
2. **Indentação Visual**: Filhas aparecem indentadas sob a mãe
3. **Contexto Claro**: Usuário vê exatamente a hierarquia ao escolher
4. **Sem Ambiguidade**: Cada opção é única e claramente identificável

---

## 🔧 Como Funciona Tecnicamente

### Nova Classe: `ContaPaiSelect`

```python
class ContaPaiSelect(forms.Select):
    """
    Widget customizado que renderiza contas com indentação hierárquica.
    """
    def optgroups(self, name, value, attrs=None):
        # Para cada conta, calcula sua profundidade (quantos ancestrais tem)
        # Exemplo: 1.1.1.1 tem 3 ancestrais, então indenta 3 níveis
        profundidade = calc_prof(conta)
        indent = '&nbsp;&nbsp;' * profundidade  # 2 espaços por nível
        label = f"{indent}• {conta.codigo_classificacao} - {conta.nome}"
```

### Resultado HTML

```html
<select name="conta_pai" class="form-control">
  <option value="">— Nenhuma (raiz) —</option>
  <option value="1">• 1 - ATIVO</option>
  <option value="5">&nbsp;&nbsp;• 1.1 - ATIVO CIRCULANTE</option>
  <option value="6">&nbsp;&nbsp;&nbsp;&nbsp;• 1.1.1 - Disponibilidades</option>
  <option value="10">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;• 1.1.1.1 - Caixa</option>
</select>
```

---

## 📊 Antes vs Depois

### ANTES ❌

```
Conta Pai: [Nenhuma (raiz)]

Dropdown:
- 1.1
- 1.1.1
- 1.1.1.1
- 1.1.2
- 1.2
- 1.2.1
- 2
- 2.1
- 2.1.1

Problema: Impossível saber qual é qual!
```

### DEPOIS ✅

```
Conta Pai: [Nenhuma (raiz)]

Dropdown:
- — Nenhuma (raiz) —
• 1 - ATIVO
  • 1.1 - ATIVO CIRCULANTE
    • 1.1.1 - Disponibilidades
    • 1.1.2 - Contas a Receber
  • 1.2 - ATIVO NÃO CIRCULANTE
• 2 - PASSIVO
  • 2.1 - PASSIVO CIRCULANTE
    • 2.1.1 - Fornecedores

Solução: Perfeito! Vê toda a hierarquia e pode escolher com confiança!
```

---

## 🎯 Casos de Uso

### Exemplo 1: Criar "1.1.1.1 - Caixa Física"

**Antes:**
```
Código: 1.1.1.1
Nome: Caixa Física
Tipo: ATIVO
Conta Pai: [dropdown com só números]
  - 1.1
  - 1.1.1
  - 1.1.2
  - ...

Usuário: "Qual é a 1.1.1 mesmo?"
```

**Depois:**
```
Código: 1.1.1.1
Nome: Caixa Física
Tipo: ATIVO
Conta Pai: [dropdown com hierarquia]
  • 1.1 - ATIVO CIRCULANTE
    • 1.1.1 - Disponibilidades  ← Claro! Esta é a que preciso
    • 1.1.2 - Contas a Receber
  • 1.2 - ATIVO NÃO CIRCULANTE

Usuário: "Pronto! Escolho '1.1.1 - Disponibilidades'"
```

### Exemplo 2: Criar "1.2.1.1 - Máquinas Industriais"

**Com a nova exibição:**
```
Conta Pai: [dropdown]
  • 1.1 - ATIVO CIRCULANTE
    • 1.1.1 - Disponibilidades
    • 1.1.2 - Contas a Receber
    • 1.1.3 - Estoques
  • 1.2 - ATIVO NÃO CIRCULANTE  ← Vejo claramente que é nível 2
    • 1.2.1 - Imobilizado        ← Vejo que é filha de 1.2
    • 1.2.2 - Intangível

Usuário seleciona: "1.2.1 - Imobilizado" com total clareza
```

---

## 📁 Arquivos Modificados

### `contabilidade/forms.py`

**Adições:**
1. Novo import: `from django.utils.html import format_html`
2. Nova classe: `ContaPaiSelect(forms.Select)`
   - Renderiza opções com indentação HTML
   - Calcula profundidade recursivamente
   - Usa `&nbsp;` para indentação visual

**Modificações:**
1. `ContaSinteticaForm.Meta.widgets` - Adicionado `'conta_pai': ContaPaiSelect()`
2. `ContaSinteticaForm.__init__()` - Instancia `ContaPaiSelect` com `loja=loja`

---

## 🎨 Características Técnicas

### Recursão Inteligente com Cache
```python
profundidades = {}
def calc_prof(conta):
    if conta.pk in profundidades:
        return profundidades[conta.pk]
    # ... calcula profundidade
    profundidades[conta.pk] = prof
    return prof
```

Evita recalcular a mesma profundidade múltiplas vezes.

### Renderização HTML Segura
```python
label = format_html(
    '{}&bull; {}',
    format_html(indent),  # &nbsp;&nbsp; repetido
    f"{conta.codigo_classificacao} - {conta.nome}"
)
```

Usa `format_html()` do Django para evitar XSS.

### Integração Automática
- Widget detecta automaticamente a loja
- Renderiza apenas as contas da loja selecionada
- Indentação funciona em qualquer nível de profundidade

---

## ✨ Benefícios

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Clareza** | ❌ Só números | ✅ Código + Nome |
| **Hierarquia** | ❌ Impossível saber | ✅ Visualmente clara |
| **Eficiência** | ❌ Usuário confuso | ✅ Escolha rápida |
| **Usabilidade** | ❌ Requer memorização | ✅ Intuitivo |
| **Escalabilidade** | ❌ Piora com mais contas | ✅ Funciona em qualquer escala |

---

## 🧪 Como Testar

### Teste 1: Criar Conta Sintética
1. Vá para **Cadastros → Plano de Contas**
2. Selecione a loja
3. Clique em uma conta
4. Clique **"+ Subconta"**
5. Formulário abre
6. **Clique no dropdown "Conta Pai"**
7. ✅ Vê a hierarquia com indentação!

### Teste 2: Verificar Indentação
1. Abra o dropdown
2. Note os `•` (bullet points) alinhados
3. Veja como cada nível está indentado:
   ```
   • 1 - ATIVO (sem indentação)
     • 1.1 - ATIVO CIRC (2 espaços)
       • 1.1.1 - Disponib (4 espaços)
   ```

### Teste 3: Selecionar Conta Pai
1. Clique em **1.1.1 - Disponibilidades**
2. Campo "Conta Pai" agora mostra: **1.1.1 - Disponibilidades**
3. Próxima conta criada será filha dela ✓

---

## 🚀 Próximas Melhorias Possíveis

### Opção 1: Search Select (Buscável)
```javascript
// Adicionar Select2 para busca
$('select[name="conta_pai"]').select2();
```

### Opção 2: Expandir/Colapsar
```html
<details>
  <summary>1.1 - ATIVO CIRCULANTE</summary>
    <option>1.1.1 - Disponibilidades</option>
    <option>1.1.2 - Contas a Receber</option>
</details>
```

### Opção 3: Filtrar por Tipo
```
Filtrar por tipo: [ Todos ] [ ATIVO ] [ PASSIVO ]
```

---

## 📝 Resumo da Solução

**Problema:** Campo "Conta Pai" mostrava só códigos, usuário adivinhava

**Solução:** Widget customizado que mostra:
- Código + Nome
- Indentação visual da hierarquia
- Renderização automática para cada loja

**Resultado:** Usuário clica no dropdown e **vê toda a árvore de contas com clareza**!

✅ **Implementado e testado!**

---

## 🎓 Código Relevante

Se quiser entender melhor, veja:
- `contabilidade/forms.py` - Classe `ContaPaiSelect`
- Método `optgroups()` - Renderiza as opções
- Função `calc_prof()` - Calcula indentação

**A solução é elegante, escalável e totalmente automática!** 🚀
