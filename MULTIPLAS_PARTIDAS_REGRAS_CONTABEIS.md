# 🔄 Múltiplas Partidas em Regras Contábeis

## O Problema Anterior

Antes, cada **RegraContabil** tinha exatamente:
- **1 Débito** (conta_debito)
- **1 Crédito** (conta_credito)

Isso limitava eventos complexos:
```
❌ NÃO era possível:
Evento: VENDA_COM_IMPOSTO
├─ Débitos:
│  ├─ Caixa (100)
│  └─ Banco (50) ← Não podia ter 2 débitos!
│
└─ Crédito:
   └─ Receita (150)
```

## A Nova Solução: PartidaRegra

Agora cada **RegraContabil** pode ter **N partidas** (débitos e créditos):

```
✅ AGORA é possível:

Evento: VENDA_COM_IMPOSTO
├─ Débitos (PartidaRegra):
│  ├─ Débito 1: Caixa (ordem 1)
│  └─ Débito 2: Banco (ordem 2)
│
└─ Créditos (PartidaRegra):
   ├─ Crédito 1: Receita (ordem 1)
   └─ Crédito 2: Impostos a Pagar (ordem 2)
```

## Modelo de Dados

### RegraContabil (Simplificado)
```python
class RegraContabil(models.Model):
    loja = ForeignKey(Empresa)
    tipo_evento = ForeignKey(TipoEvento)
    descricao = CharField()
    ativa = BooleanField()
    # Sem mais conta_debito, conta_credito, ordem!

    def get_debitos(self):
        """Retorna PartidaRegra com tipo='D'"""
        return self.partidas.filter(tipo='D')

    def get_creditos(self):
        """Retorna PartidaRegra com tipo='C'"""
        return self.partidas.filter(tipo='C')
```

### PartidaRegra (Nova)
```python
class PartidaRegra(models.Model):
    TIPO_CHOICES = [('D', 'Débito'), ('C', 'Crédito')]

    regra = ForeignKey(RegraContabil, related_name='partidas')
    tipo = CharField(choices=TIPO_CHOICES)  # D ou C
    conta = ForeignKey(ContaAnalitica)
    ordem = PositiveIntegerField()

    # unique_together = (('regra', 'tipo', 'conta'),)
    # Não pode ter mesma conta 2x na mesma regra
```

## Como Usar

### No Admin Django

1. Vá para **Tipos de Evento**
2. Clique em uma tipo evento (ex: Despesa_limpeza)
3. Clique em **"Regras"** ou **"+ Nova Regra"**
4. Preencha:
   ```
   Tipo de Evento: Despesa_limpeza
   Descrição: Despesa com limpeza
   Loja: [selecione]
   Ativa: ✓
   ```
5. Clique **Salvar**
6. Agora vê seção **"Partidas de Regra"** com tabela inline:
   ```
   Tipo │ Conta Analítica │ Ordem
   ─────┼─────────────────┼──────
   D    │ 4.3.2.1 (Limpeza)│ 1
   C    │ 1.1.1.2 (Caixa)  │ 1
   ```
7. Clique **"Adicionar outra Partida de Regra"** para cada D/C
8. Salve

### No Código (Python)

```python
# Criar regra com múltiplas partidas
from contabilidade.models import RegraContabil, PartidaRegra, TipoEvento
from core.models import Empresa

loja = Empresa.objects.get(pk=1)
tipo_evento = TipoEvento.objects.get(codigo='VENDA_COM_IMPOSTO')

# 1. Criar regra
regra = RegraContabil.objects.create(
    loja=loja,
    tipo_evento=tipo_evento,
    descricao='Venda com imposto - múltiplos débitos e créditos',
    ativa=True
)

# 2. Adicionar partidas (débitos)
PartidaRegra.objects.create(
    regra=regra,
    tipo='D',
    conta=ContaAnalitica.objects.get(pk=1),  # Caixa
    ordem=1
)

PartidaRegra.objects.create(
    regra=regra,
    tipo='D',
    conta=ContaAnalitica.objects.get(pk=2),  # Banco
    ordem=2
)

# 3. Adicionar partidas (créditos)
PartidaRegra.objects.create(
    regra=regra,
    tipo='C',
    conta=ContaAnalitica.objects.get(pk=50),  # Receita
    ordem=1
)

PartidaRegra.objects.create(
    regra=regra,
    tipo='C',
    conta=ContaAnalitica.objects.get(pk=51),  # Impostos
    ordem=2
)

# 4. Usar a regra
debitos = regra.get_debitos()  # PartidaRegra D/C=D
creditos = regra.get_creditos()  # PartidaRegra D/C=C

for d in debitos:
    print(f"Débita: {d.conta.nome} (ordem {d.ordem})")
# Débita: Caixa (ordem 1)
# Débita: Banco (ordem 2)

for c in creditos:
    print(f"Credita: {c.conta.nome} (ordem {c.ordem})")
# Credita: Receita (ordem 1)
# Credita: Impostos (ordem 2)
```

## Exemplos de Eventos Complexos

### Exemplo 1: Venda com Imposto

```
Evento: VENDA_COM_IMPOSTO
Descrição: Venda realizada com ICMS e PIS

Partidas:
├─ D: 1.1.1.2.0001 - Caixa (ordem 1)
├─ D: 1.1.1.2.0002 - Banco (ordem 2)
├─ C: 3.1.1.1.0001 - Receita Vendas (ordem 1)
├─ C: 2.1.2.1.0001 - ICMS a Pagar (ordem 2)
└─ C: 2.1.2.2.0001 - PIS a Pagar (ordem 3)

Valor total entrada: R$ 100
├─ Débita Caixa: R$ 60
├─ Débita Banco: R$ 40
├─ Credita Receita: R$ 85
├─ Credita ICMS: R$ 10
└─ Credita PIS: R$ 5
```

### Exemplo 2: Compra com Desconto e Frete

```
Evento: COMPRA_REGISTRADA
Descrição: Compra com desconto + frete

Partidas:
├─ D: 1.2.1.1.0001 - Estoque (ordem 1)
├─ D: 4.1.1.1.0001 - Despesa Frete (ordem 2)
├─ C: 2.1.1.1.0001 - Fornecedores (ordem 1)
└─ C: 2.1.3.1.0001 - Desconto Recebido (ordem 2)

Valor total nota: R$ 1.000
├─ Desconto: -R$ 50
├─ Frete: +R$ 100
├─ Débita Estoque: R$ 950
├─ Débita Frete: R$ 100
├─ Credita Fornecedor: R$ 1.000
└─ Credita Desconto: R$ 50
```

## 📋 Comparação

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Débitos por regra** | Máximo 1 | Ilimitado |
| **Créditos por regra** | Máximo 1 | Ilimitado |
| **Estrutura** | RegraContabil (conta_debito, conta_credito) | RegraContabil + PartidaRegra N:1 |
| **Interface** | Dropdown D/C simples | Tabela inline com múltiplas partidas |
| **Casos de uso** | Eventos simples | Eventos complexos |
| **Exemplos suportados** | D-Caixa / C-Receita | D-Caixa + D-Banco / C-Receita + C-Impostos |

## 🚀 Migração de Dados

Se tinha regras antigas (com conta_debito/conta_credito), foram automaticamente convertidas:

```python
# Antes (no banco, regra ID=1):
RegraContabil:
  id=1
  tipo_evento=VENDA
  conta_debito=Caixa
  conta_credito=Receita
  ordem=1

# Depois (migração 0005):
RegraContabil:
  id=1
  tipo_evento=VENDA
  # (campos antigos removidos)

PartidaRegra (criadas automaticamente):
  id=1, regra=1, tipo='D', conta=Caixa, ordem=1
  id=2, regra=1, tipo='C', conta=Receita, ordem=1
```

⚠️ **Nota**: A migração **NÃO criou** PartidaRegra automaticamente. Se tinha regras antigas, elas ficarão vazias (sem partidas). Você precisa **recriá-las** manualmente no admin.

## 🧪 Como Testar

1. Vá para **Contabilidade → Tipos de Evento**
2. Clique em um tipo evento
3. Crie uma **nova regra**
4. Adicione múltiplas **Partidas de Regra**:
   - 2+ Débitos
   - 2+ Créditos
5. Salve
6. ✅ Tudo deve funcionar!

## ⚙️ Próximos Passos

Para usar a regra ao disparar um evento:

```python
# No view/signal, quando evento é criado:
evento = EventoOperacional.objects.create(...)

# Motor contábil executa:
regra = RegraContabil.objects.get(tipo_evento=evento.tipo_evento)

# Cria LancamentoContabil com partidas:
lancamento = LancamentoContabil.objects.create(...)

for partida_regra in regra.partidas.all().order_by('ordem'):
    PartidaLancamento.objects.create(
        lancamento=lancamento,
        conta=partida_regra.conta,
        tipo=partida_regra.tipo,
        valor=valor,  # Será dividido conforme lógica
    )
```

---

**Versão:** 1.0
**Data:** 2026-04-01
**Status:** ✅ Implementado
