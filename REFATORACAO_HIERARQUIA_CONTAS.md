# 📋 Refatoração: Hierarquia de Contas (Níveis 1-5)

## Objetivo
Padronizar a estrutura hierárquica do plano de contas com regras claras por nível:

| Nível | Exemplo | Formato | Tipo | Zero-padded |
|-------|---------|---------|------|---|
| 1 | `1` | 1 dígito | Sintética | ❌ |
| 2 | `1.1` | 2 dígitos | Sintética | ❌ |
| 3 | `1.1.1` | 3 dígitos | Sintética | ❌ |
| 4 | `1.1.1.02` | 2 dígitos | Sintética | ✅ |
| 5 | `1.1.1.02.0001` | 4 dígitos | **Analítica** | ✅ |

**Decisão arquitetural:** Manter dois modelos separados (ContaSintetica para níveis 1-4, ContaAnalitica para nível 5)

---

## 🔧 Mudanças Implementadas

### 1. `contabilidade/models.py`

#### ContaSintetica — Adicionado `clean()` para validação
```python
def clean(self):
    """Valida que contas sintéticas não podem ter nível superior a 4."""
    if self.nivel > 4:
        raise ValidationError(
            "Conta sintética não pode ter nível superior a 4. "
            "Contas de nível 5 devem ser criadas como contas analíticas."
        )
```

---

### 2. `contabilidade/forms.py`

#### ContaSinteticaForm — Adicionadas 2 validações

**`clean_nivel()`:** Bloqueia nível > 4
```python
def clean_nivel(self):
    """Valida que nível máximo para sintéticas é 4."""
    nivel = self.cleaned_data.get('nivel')
    if nivel and nivel > 4:
        raise forms.ValidationError(
            'Contas sintéticas podem ter no máximo nível 4. '
            'Para nível 5, crie uma conta analítica.'
        )
    return nivel
```

**`clean_codigo_classificacao()`:** Atualizado para validar formato por nível
- Nível 4: último segmento DEVE ter exatamente 2 dígitos zero-padded (`.02`, `.03`, ..., `.99`)
- Níveis 1-3: não permitir zeros à esquerda (nenhum zero-padding)
- Exemplo válido nível 4: `1.1.1.02` ✅
- Exemplo inválido nível 3: `1.1.01` ❌

#### ContaAnaliticaForm — Adicionadas 2 validações

**`clean()`:** Garante que analítica só é criada a partir de sintética nível 4
```python
def clean(self):
    """Valida que conta analítica só pode ser criada a partir de sintética nível 4."""
    cleaned_data = super().clean()
    conta_sintetica = cleaned_data.get('conta_sintetica')

    if conta_sintetica and conta_sintetica.nivel != 4:
        raise forms.ValidationError(
            'Contas analíticas só podem ser criadas a partir de contas sintéticas nível 4. '
            f'A conta selecionada é nível {conta_sintetica.nivel}.'
        )
    return cleaned_data
```

**`clean_codigo_classificacao()`:** Valida formato analítico
- Deve ter 5 segmentos: `X.X.X.XX.YYYY`
- Último segmento DEVE ter exatamente 4 dígitos zero-padded (`.0001`, `.0002`, ..., `.9999`)
- Código DEVE começar com código da sintética pai
- Exemplo: pai `1.1.1.02` → filho deve começar com `1.1.1.02.XXXX` ✅

---

### 3. `contabilidade/views.py`

#### conta_sintetica_criar — Lógica de proximo_codigo refatorada

**Novo comportamento:**
```
if pai.nivel >= 4:
    → Erro: "Contas sintéticas só vão até nível 4"
    → Redireciona para plano-contas

if proximo_nivel == 4:
    → Código será zero-padded: 1.1.1.01, 1.1.1.02, ...
    → Formato: f"{proximo_num:02d}"

else (nível 1-3):
    → Código simples: 1, 1.1, 1.1.1, ...
    → Formato: str(proximo_num)
```

**Exemplo de auto-preenchimento:**
```
Clica em: 1.1.1 (nível 3)
  ↓
Formulário abre para nível 4:
  • Código: 1.1.1.01 ← 2 dígitos zero-padded automaticamente
  • Tipo: (herdado do pai)
  • Nível: 4
  • Conta Pai: 1.1.1
```

#### conta_analitica_criar — Adicionada pré-validação e auto-preenchimento

**Novo comportamento:**
```
if sintetica.nivel != 4:
    → Erro: "Contas analíticas só podem ser criadas a partir de sintética nível 4"
    → Redireciona para plano-contas

if não há filhas:
    → proximo_codigo = f"{sintetica.codigo}.0001"

if há filhas:
    → Incrementa último segmento: {ultima_num} + 1
    → Formato zero-padded: f"{proximo_num:04d}"
```

**Exemplo de auto-preenchimento:**
```
Clica em: 1.1.1.02 (nível 4) → "+ Nova Analítica"
  ↓
Formulário abre para nível 5:
  • Código: 1.1.1.02.0001 ← 4 dígitos zero-padded automaticamente
  • Sintética Pai: 1.1.1.02 (pré-selecionada)
  → Campo é readonly (não pode editar)
```

---

### 4. `contabilidade/templates/plano_contas.html`

#### Botões condicionais baseado no nível

**Nível 1-3:** Mostra "+ Subconta" (criar sintética)
```django
{% if sintetica_selecionada.nivel < 4 %}
  <a class="btn btn--primary">+ Subconta</a>
{% endif %}
```

**Nível 4:** Mostra "+ Nova Analítica" (criar analítica)
```django
{% elif sintetica_selecionada.nivel == 4 %}
  <a class="btn btn--primary">+ Nova Analítica</a>
{% endif %}
```

#### Badges informativos por nível

**Nível 1-3:** Mostra contador de subcontas sintéticas
```
👶 2 subcontas ← Filhas sintéticas
```

**Nível 4:** Mostra contador de contas analíticas
```
📊 3 analíticas ← Filhas analíticas
⚠️ Sem analíticas ← Se não tem filhas
```

---

### 5. `contabilidade/templates/conta_sintetica_form.html`

#### Hints visuais de formato por nível

Quando criando nível 4 (pai é nível 3):
```
Formato nível 4: 2 dígitos zero-padded (ex: .01, .02)
```

Quando criando sem pai (nível 1):
```
Nível 1-3: 1, 1.1, 1.1.1 (simples)
Nível 4: 1.1.1.02 (2 dígitos zero-padded)
```

---

### 6. `contabilidade/templates/conta_analitica_form.html`

#### Pré-preenchimento e hints de formato

Quando criando analítica de sintética nível 4:
```
✓ Preenchido automaticamente: 1.1.1.02.0001
Código reduzido: 0001 (extraído automaticamente)
```

Quando editando (sem sintética pré-selecionada):
```
Formato: X.X.X.XX.YYYY
Ex: 1.1.1.02.0001 (últimos 4 dígitos = código reduzido)
```

#### Campo `codigo_reduzido` oculto/readonly

- **Na criação:** Campo fica hidden (será calculado automaticamente)
- **Na edição:** Campo fica readonly (mostra valor extraído dos últimos 4 dígitos)

---

## ✅ Validações Implementadas

### No Modelo (models.py)
- ❌ ContaSintetica.nivel não pode ser > 4

### No Formulário (forms.py)
- ❌ ContaSinteticaForm.nivel não pode ser > 4
- ❌ ContaSinteticaForm.codigo deve respeitar formato (nível 4 = 2 dígitos zero-padded)
- ❌ ContaAnaliticaForm.conta_sintetica deve ser nível 4
- ❌ ContaAnaliticaForm.codigo deve ter 4 dígitos no último segmento (zero-padded)
- ❌ ContaAnaliticaForm.codigo deve começar com código da sintética pai
- ❌ ContaAnaliticaForm.codigo_reduzido (calculado) deve ser único na loja

### Na View (views.py)
- ❌ conta_sintetica_criar bloqueia se pai.nivel >= 4
- ❌ conta_analitica_criar bloqueia se sintetica.nivel != 4

### Na Interface (templates)
- ❌ "+ Subconta" só aparece para níveis 1-3
- ❌ "+ Nova Analítica" só aparece para nível 4

---

## 🎯 Comportamento Esperado

### Cenário 1: Criar conta nível 2 (filha de nível 1)
```
Seleciona: 1 - ATIVO (nível 1)
Clica: + Subconta
  ↓
Formulário pré-preenchido:
  • Código: 1.2 (próximo número simples)
  • Nível: 2
  • Tipo: ATIVO (herdado)
  • Pai: 1 - ATIVO
  ✅ Usuário digita apenas Nome
```

### Cenário 2: Criar conta nível 4 (filha de nível 3)
```
Seleciona: 1.1.1 - Disponibilidades (nível 3)
Clica: + Subconta
  ↓
Formulário pré-preenchido:
  • Código: 1.1.1.01 ← ZERO-PADDED (2 dígitos)
  • Nível: 4
  • Tipo: ATIVO (herdado)
  • Pai: 1.1.1
  ✅ Usuário digita apenas Nome
```

### Cenário 3: Tentar criar conta nível 5 como sintética (BLOQUEADO)
```
Seleciona: 1.1.1.02 - Bancos (nível 4)
Clica: + Subconta
  ↓
❌ ERRO: "Contas sintéticas só vão até nível 4"
↓
Redireciona para plano-contas
```

### Cenário 4: Criar conta nível 5 (analítica)
```
Seleciona: 1.1.1.02 - Bancos (nível 4)
Clica: + Nova Analítica ← Novo botão!
  ↓
Formulário pré-preenchido:
  • Código: 1.1.1.02.0001 ← ZERO-PADDED (4 dígitos)
  • Código Reduzido: 0001 ← Extraído automaticamente dos últimos 4 dígitos
  • Sintética: 1.1.1.02 (readonly)
  ✅ Usuário digita: nome, natureza, natureza_saldo, etc
```

---

## 🧪 Como Testar

### Teste 1: Zero-padding nível 4
1. Vá para Cadastros → Plano de Contas
2. Selecione uma loja
3. Clique em uma conta nível 3 (ex: 1.1.1)
4. Clique "+ Subconta"
5. ✅ Campo código deve vir preenchido como `1.1.1.01` (com zero-padding)
6. Crie 3 subcontas rapidamente
7. ✅ Códigos devem ser: `1.1.1.01`, `1.1.1.02`, `1.1.1.03` (etc)

### Teste 2: Botões condicionais
1. Selecione conta nível 1, 2 ou 3
2. ✅ Deve ver "+ Subconta"
3. ❌ Não deve ver "+ Nova Analítica"
4. Selecione conta nível 4
5. ✅ Deve ver "+ Nova Analítica"
6. ❌ Não deve ver "+ Subconta"

### Teste 3: Bloqueio de nível 5 sintética
1. Selecione conta nível 4
2. Clique "+ Subconta"
3. ✅ Deve mostrar erro: "Contas sintéticas só vão até nível 4"

### Teste 4: Analítica zero-padding
1. Selecione conta nível 4
2. Clique "+ Nova Analítica"
3. ✅ Campo código deve vir preenchido como `{codigo_pai}.0001` (4 dígitos)
4. Crie 2 analíticas
5. ✅ Códigos devem ser: `{codigo_pai}.0001`, `{codigo_pai}.0002`

### Teste 5: Validação de código
1. Tente criar sintética nível 4 com código `1.1.1.1` (1 dígito)
2. ✅ Erro: "Último segmento deve ter exatamente 2 dígitos"
3. Tente criar analítica com código `1.1.1.02.1` (1 dígito)
4. ✅ Erro: "Último segmento deve ter exatamente 4 dígitos"

---

## 📝 Resumo das Mudanças

| Arquivo | O que mudou | Status |
|---------|-----------|--------|
| `models.py` | Adicionado `clean()` para validar nível ≤ 4 | ✅ |
| `forms.py` | ContaSinteticaForm: validação de nível e formato | ✅ |
| `forms.py` | ContaAnaliticaForm: validação de nível 4 e formato | ✅ |
| `forms.py` | ContaAnaliticaForm: campo codigo_reduzido hidden (criação) ou readonly (edição) | ✅ |
| `views.py` | conta_sintetica_criar: zero-padding nível 4 | ✅ |
| `views.py` | conta_analitica_criar: zero-padding + auto-calcula codigo_reduzido | ✅ |
| `plano_contas.html` | Botões condicionais + badges por nível | ✅ |
| `conta_sintetica_form.html` | Hints de formato | ✅ |
| `conta_analitica_form.html` | Pré-preenchimento + hints + codigo_reduzido auto | ✅ |

---

## 🚀 Próximos Passos (Opcional)

1. **Migração de dados:** Se há dados legados com formatação diferente
   - Criar script de migração/validação
   - Identificar contas que não seguem o novo padrão
   - Corrigir ou arquivar

2. **Importação de template:** Atualizar script `create_template_restaurante.py`
   - Gerar códigos com zero-padding correto
   - Validar estrutura antes de inserir

3. **Relatórios:** Atualizar exibição em DRE, Balanço, etc
   - Garantir que formatação é consistente
   - Adicionar filtros por nível se necessário

---

## ✨ Benefícios

- ✅ **Estrutura clara:** Regras de nível bem definidas
- ✅ **Prevenção de erros:** Validações impedem estruturas inválidas
- ✅ **UX melhorada:** Auto-preenchimento com zero-padding correto
- ✅ **Manutenibilidade:** Código mais previsível e documentado
- ✅ **Escalabilidade:** Pronto para futuros recursos (consolidação, drill-down)

**Versão:** 1.0
**Data:** 2026-04-01
**Status:** ✅ Implementado e testado
