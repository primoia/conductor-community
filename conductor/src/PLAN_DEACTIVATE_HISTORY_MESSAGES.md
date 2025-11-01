# Plano de Implementação: Inativar Mensagens do Histórico
## Projeto: conductor (Backend Core)

---

## 📋 Objetivo

Implementar a base de dados e lógica de filtragem para permitir que mensagens do histórico do chat sejam marcadas como inativas (`isDeleted: true`) e não sejam incluídas no prompt enviado para a LLM.

---

## 🎯 Escopo desta Implementação

### ✅ In Scope
- Adicionar suporte ao campo `isDeleted` no schema do MongoDB (collection `history`)
- Modificar `MongoStateRepository` para salvar novas mensagens com `isDeleted: False`
- Implementar filtro no `PromptEngine` para excluir mensagens inativas do prompt
- Garantir retrocompatibilidade com mensagens antigas (sem o campo `isDeleted`)

### ❌ Out of Scope
- Endpoints de API (responsabilidade do `conductor-gateway`)
- Interface de usuário (responsabilidade do `conductor-web`)
- Testes automatizados
- Deploy ou configuração de containers

---

## 📦 Arquivos a Modificar

### 1. `src/infrastructure/storage/mongo_repository.py`
**Linha afetada**: ~153 (método `append_to_history`)

**Mudança**: Adicionar campo `isDeleted: False` ao salvar novas entradas no histórico.

**ANTES**:
```python
doc = dict(history_entry)  # Copia o dict
doc["agent_id"] = agent_id
doc["createdAt"] = datetime.utcnow()

if instance_id:
    doc["instance_id"] = instance_id
```

**DEPOIS**:
```python
doc = dict(history_entry)  # Copia o dict
doc["agent_id"] = agent_id
doc["createdAt"] = datetime.utcnow()

# 🆕 NOVO: Definir isDeleted=false por padrão
doc["isDeleted"] = False

if instance_id:
    doc["instance_id"] = instance_id
```

---

### 2. `src/core/prompt_engine.py`
**Linhas afetadas**: ~503 (método `_format_history_xml`) e ~414 (método `_format_history`)

#### **Mudança 2.1: Filtro em `_format_history_xml()`**

**ANTES** (linha ~503):
```python
def _format_history_xml(self, history: List[Dict[str, Any]]) -> str:
    """Formata o histórico da conversa como uma série de tags XML."""
    if not history:
        return ""

    MAX_HISTORY_TURNS = 100
    recent_history = (
        history[-MAX_HISTORY_TURNS:]
        if len(history) > MAX_HISTORY_TURNS
        else history
    )

    # ... resto do código
```

**DEPOIS**:
```python
def _format_history_xml(self, history: List[Dict[str, Any]]) -> str:
    """Formata o histórico da conversa como uma série de tags XML."""
    if not history:
        return ""

    # 🔍 NOVO: Filtrar mensagens não deletadas
    # Retrocompatibilidade: se não tiver campo 'isDeleted', assume False
    active_history = [
        turn for turn in history
        if not turn.get("isDeleted", False)  # Inclui se isDeleted=False ou campo ausente
    ]

    logger.info(f"📊 [PROMPT_ENGINE] Histórico filtrado: {len(history)} total, {len(active_history)} não deletadas")

    if not active_history:
        return ""

    MAX_HISTORY_TURNS = 100
    recent_history = (
        active_history[-MAX_HISTORY_TURNS:]
        if len(active_history) > MAX_HISTORY_TURNS
        else active_history
    )

    # ... resto do código continua igual
```

#### **Mudança 2.2: Filtro em `_format_history()` (formato texto)**

**ANTES** (linha ~414):
```python
def _format_history(self, history: List[Dict[str, Any]]) -> str:
    """Formata o histórico da conversa como texto."""
    if not history:
        return ""

    MAX_HISTORY_TURNS = 100
    recent_history = (
        history[-MAX_HISTORY_TURNS:]
        if len(history) > MAX_HISTORY_TURNS
        else history
    )

    # ... resto do código
```

**DEPOIS**:
```python
def _format_history(self, history: List[Dict[str, Any]]) -> str:
    """Formata o histórico da conversa como texto."""
    if not history:
        return ""

    # 🔍 NOVO: Filtrar mensagens não deletadas
    active_history = [
        turn for turn in history
        if not turn.get("isDeleted", False)
    ]

    logger.info(f"📊 [PROMPT_ENGINE] Histórico filtrado (texto): {len(history)} total, {len(active_history)} ativas")

    if not active_history:
        return ""

    MAX_HISTORY_TURNS = 100
    recent_history = (
        active_history[-MAX_HISTORY_TURNS:]
        if len(active_history) > MAX_HISTORY_TURNS
        else active_history
    )

    # ... resto do código continua igual
```

---

## 🔍 Schema MongoDB (Documentação)

### Collection: `history`

**ANTES (implícito)**:
```javascript
{
  "_id": "uuid-v4",
  "agent_id": "performance-agent",
  "instance_id": "uuid-da-instancia",
  "user_input": "Analise o código",
  "ai_response": "Aqui está a análise...",
  "timestamp": 1234567890,
  "createdAt": ISODate("2025-11-01T...")
}
```

**DEPOIS (explícito)**:
```javascript
{
  "_id": "uuid-v4",
  "agent_id": "performance-agent",
  "instance_id": "uuid-da-instancia",
  "user_input": "Analise o código",
  "ai_response": "Aqui está a análise...",
  "timestamp": 1234567890,
  "createdAt": ISODate("2025-11-01T..."),
  "isDeleted": false  // ← NOVO CAMPO (default: false)
}
```

**Nota**: Não é necessária migração de dados. Mensagens antigas (sem o campo) serão tratadas como `isDeleted: False` pelo filtro.

---

## 📝 Regras de Negócio Implementadas

### RN1: Filtro de Mensagens Ativas no Prompt
- **O que**: Ao construir o prompt (XML ou texto), incluir apenas mensagens com `isDeleted: False`
- **Onde**: `prompt_engine.py` (métodos `_format_history_xml()` e `_format_history()`)
- **Como**: List comprehension com `turn.get("isDeleted", False)`

### RN2: Retrocompatibilidade
- **O que**: Mensagens antigas sem o campo `isDeleted` devem funcionar normalmente
- **Como**: Usar `turn.get("isDeleted", False)` - se não existir, assume `False` (ativa)

### RN3: Salvamento Padrão
- **O que**: Novas mensagens devem ser salvas com `isDeleted: False`
- **Onde**: `mongo_repository.py` (método `append_to_history()`)

---

## ✅ Critérios de Sucesso

1. ✅ Novas mensagens salvas no MongoDB têm campo `isDeleted: False`
2. ✅ Mensagens com `isDeleted: True` são excluídas do prompt XML
3. ✅ Mensagens com `isDeleted: True` são excluídas do prompt texto
4. ✅ Mensagens antigas (sem campo `isDeleted`) continuam aparecendo no prompt
5. ✅ Logs indicam quantas mensagens foram filtradas

---

## 🔗 Dependências

### Upstream (bloqueia este trabalho)
- Nenhuma

### Downstream (depende deste trabalho)
- **conductor-gateway**: API endpoint para inativar mensagens (precisa que o schema esteja pronto)
- **conductor-web**: UI para inativar mensagens (precisa que o filtro esteja funcionando)

---

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Mensagens antigas sem `isDeleted` | Médio | Fallback `.get("isDeleted", False)` |
| Performance com históricos grandes | Baixo | Filtro é O(n), mas já existe limite de 100 mensagens |
| Logs excessivos em produção | Baixo | Usar `logger.debug()` em vez de `logger.info()` se necessário |

---

## 🚀 Ordem de Implementação Sugerida

1. **Passo 1**: Modificar `mongo_repository.py` (adicionar campo `isDeleted: False`)
2. **Passo 2**: Modificar `prompt_engine.py` - método `_format_history_xml()`
3. **Passo 3**: Modificar `prompt_engine.py` - método `_format_history()`
4. **Passo 4**: Validar manualmente (inserir documento com `isDeleted: True` no Mongo e verificar que não aparece no prompt)

---

## 📚 Referências

- **Screenplay completo**: `requisitos_inativar_mensagens_chat.md`
- **Código atual**:
  - `src/core/prompt_engine.py:1-713`
  - `src/infrastructure/storage/mongo_repository.py:1-253`

---

## 🎯 Estimativa de Esforço

- **Complexidade**: Baixa
- **Tempo estimado**: 1-2 horas
- **Arquivos modificados**: 2
- **Linhas de código**: ~15 linhas adicionadas/modificadas

---

**Plano criado em**: 2025-11-01
**Projeto**: conductor (Backend Core)
**Saga**: Inativar Mensagens do Histórico do Chat
