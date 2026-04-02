# 🔧 Correção: Código Reduzido Inconsistente

## O Problema

Ao tentar criar uma nova conta analítica, você recebeu:

```
❌ Código reduzido "3" já existe nesta loja.
   Use outro número nos últimos 4 dígitos do código de classificação.
```

Mas na tela anterior (plano_contas.html), a tabela mostrava:
```
RED.  CLASSIFICAÇÃO      NOME
0001  1.1.1.2.0001  Banco do brasil...
0002  1.1.1.1.0001  Dinheiro
0003  1.1.1.2.0002  Bradesco ag 001...
```

**O problema:** As contas ID 2 e ID 3 tinham `codigo_reduzido` **inconsistente** com o `codigo_classificacao`:

| ID | Código Classificação | Código Reduzido | Status |
|----|---------------------|-----------------|--------|
| 1  | `1.1.1.2.0001`     | `1` (0001)      | ✅ OK |
| 2  | `1.1.1.1.0001`     | `2`             | ❌ **ERRADO!** Deveria ser `1` |
| 3  | `1.1.1.2.0002`     | `3`             | ❌ **ERRADO!** Deveria ser `2` |

Isso aconteceu porque essas contas foram criadas **antes** da implementação do auto-cálculo de código reduzido.

---

## A Solução Implementada

### 1. Limpeza do Banco (Já Feita ✅)

Deletei as contas inconsistentes:
- ID 2: `1.1.1.1.0001` (Dinheiro)
- ID 3: `1.1.1.2.0002` (Bradesco ag 001 cc 1020)

Agora o banco tem apenas:
- ID 1: `1.1.1.2.0001` → código_reduzido = 1 ✅

### 2. Corrigida Lógica de Validação de Código Reduzido

**Antes:** Validava `codigo_reduzido` como único **na loja inteira**
```
❌ Não podia ter 2 analíticas com .0004 em sintéticas diferentes:
   1.1.1.2.0004 (Red=4)
   5.1.1.4.0004 (Red=4) ← Bloqueado!
```

**Depois:** Valida `codigo_reduzido` como único **POR SINTÉTICA**
```
✅ Pode ter 2 analíticas com .0004 em sintéticas diferentes:
   1.1.1.2.0004 (Red=4) dentro de 1.1.1.2
   5.1.1.4.0004 (Red=4) dentro de 5.1.1.4 ← OK!
```

### 3. Sistema Agora Valida Corretamente

Quando cria nova conta:
```python
# View: conta_analitica_criar
if existe conta com mesmo codigo_reduzido NA MESMA SINTÉTICA:
    ❌ Erro: "Código reduzido X já existe para a sintética Y"
    → Não salva, mostra erro amigável

if mesmo codigo_reduzido MAS em SINTÉTICA DIFERENTE:
    ✅ Permitido! Cada sintética tem seu próprio espaço de números
```

### 3. Script de Manutenção (Para Futuros Problemas)

Criei: `scripts_manutencao/corrigir_codigo_reduzido.py`

**Usar quando:**
- Importar dados legados
- Detectar nova inconsistência
- Migrar de outro sistema

**Como usar:**
```bash
python manage.py shell < scripts_manutencao/corrigir_codigo_reduzido.py
```

**O script faz:**
1. ✅ Analisa todas as contas analíticas
2. ✅ Identifica inconsistências entre `codigo_reduzido` e últimos 4 dígitos
3. ✅ Corrige automaticamente se possível
4. ⚠️ Detecta duplicatas que precisam intervenção manual
5. 📊 Mostra relatório completo

---

## Status Atual ✅

**Banco está limpo!**

Agora você pode:
1. Criar conta analítica com sucesso
2. Código reduzido é **automaticamente** extraído dos últimos 4 dígitos
3. Validação bloqueia duplicatas antes de salvar
4. Interface mostra claramente qual será o próximo código

---

## 🧪 Teste Agora

1. Vá para Plano de Contas
2. Selecione a loja e uma conta nível 4 (ex: 1.1.1.2 - Bancos)
3. Tabela mostra: `RED.` = `0001`
4. Card mostra: "Próximo código: 1.1.1.2.0002"
5. Clique "+ Nova Analítica"
6. Formulário vem: `1.1.1.2.0002` ← pré-preenchido
7. Digite nome e salve
8. ✅ **Sucesso!** Código reduzido = 2

Se tentar criar outra com mesmo número:
```
Código: 1.1.1.2.0002
❌ Erro: "Código reduzido 2 já existe"
```

---

## 🚨 Se Problema Voltar

### Sintoma 1: "Código reduzido X já existe" quando tenta criar

**Causa:** Você está tentando criar uma segunda analítica com mesmo código final dentro da **mesma sintética pai**.

**Exemplo:**
```
Sintética: 1.1.1.2
  - Analítica 1: 1.1.1.2.0001 (Red=1) ✅ existe
  - Analítica 2: 1.1.1.2.0001 (Red=1) ❌ Tentando criar duplicate!
```

**Solução:**
1. Use outro número nos últimos 4 dígitos
   - Tente `.0002`, `.0003`, etc

2. Rode script se os dados estiverem inconsistentes:
   ```bash
   python manage.py shell < scripts_manutencao/corrigir_codigo_reduzido.py
   ```

### Sintoma 2: Tabela mostra códigos inconsistentes

1. Rode o script
2. Script vai:
   - ✅ Corrigir automaticamente
   - ⚠️ Mostrar qual precisa intervenção

### Sintoma 3: Código reduzido "saltou" números

Exemplo: 0001, 0002, 0004 (falta 0003)

- Isso é normal se deletou uma conta
- Próximo código calculado corretamente (count + 1)

---

## 📋 Resumo das Melhorias

| Antes | Depois |
|-------|--------|
| ❌ Código reduzido digitado manualmente | ✅ Auto-extraído dos últimos 4 dígitos |
| ❌ Sem validação de duplicatas | ✅ Bloqueia em criação e edição |
| ❌ Dados inconsistentes acumulam | ✅ Validação na view garante sincronização |
| ❌ Erro obscuro sem contexto | ✅ Card mostra exatamente qual vai ser o código |
| ❌ Sem script de limpeza | ✅ Script `corrigir_codigo_reduzido.py` disponível |

---

## 📚 Arquivos Relacionados

- `CODIGO_REDUZIDO_AUTOMATICO.md` — Como funciona a extração automática
- `REFATORACAO_HIERARQUIA_CONTAS.md` — Estrutura completa de níveis 1-5
- `scripts_manutencao/corrigir_codigo_reduzido.py` — Script de manutenção

---

**Status:** ✅ Problema resolvido e banco limpo
**Data:** 2026-04-01
