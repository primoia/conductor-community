# Plano de Implementação: Inativar Mensagens do Histórico
## Projeto: conductor-gateway (API Gateway)

---

## 📋 Objetivo

Criar endpoints de API para permitir que o frontend inative mensagens do histórico e obtenha os IDs necessários para essa operação. Este projeto atua como ponte entre o frontend (conductor-web) e o backend (conductor).

---

## 🎯 Escopo desta Implementação

### ✅ In Scope
- Criar endpoint `PATCH /api/agents/history/{history_id}/deactivate` para inativar mensagens
- Modificar endpoint `GET /api/agents/context/{instance_id}` para retornar `_id` e `isDeleted`
- Atualizar função `mongo_to_dict()` para não remover o campo `_id`
- Garantir retrocompatibilidade com mensagens antigas

### ❌ Out of Scope
- Lógica de filtragem do prompt (responsabilidade do `conductor`)
- Interface de usuário (responsabilidade do `conductor-web`)
- Testes automatizados
- Deploy ou configuração de containers

---

## 📦 Arquivos a Modificar

### 1. `src/api/app.py` - Novo Endpoint `PATCH /deactivate`
**Localização**: Adicionar novo endpoint (sugestão: próximo aos outros endpoints de agentes, linha ~1800)

**Código a adicionar**:
```python
@app.patch("/api/agents/history/{history_id}/deactivate")
async def deactivate_history_entry(history_id: str):
    """
    Inativa (soft delete) uma entrada do histórico.

    Args:
        history_id: UUID do documento na collection 'history'

    Returns:
        {"success": true, "message": "History entry deactivated"}
    """
    logger.info(f"🗑️ [GATEWAY] Inativando mensagem do histórico: {history_id}")

    if mongo_db is None:
        raise HTTPException(status_code=503, detail="MongoDB connection not available")

    try:
        history_collection = mongo_db["history"]

        # Atualizar documento, definindo isDeleted=true
        result = history_collection.update_one(
            {"_id": history_id},
            {"$set": {"isDeleted": True, "deletedAt": datetime.utcnow()}}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"History entry '{history_id}' not found"
            )

        logger.info(f"✅ [GATEWAY] Mensagem {history_id} inativada com sucesso")

        return {
            "success": True,
            "message": "History entry deactivated",
            "history_id": history_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [GATEWAY] Erro ao inativar mensagem: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Imports necessários** (adicionar se não existir):
```python
from datetime import datetime
```

---

### 2. `src/api/app.py` - Modificar Endpoint `GET /api/agents/context/{instance_id}`
**Linha afetada**: ~1673 (método `get_agent_context`)

**Mudança**: Retornar `_id` e `isDeleted` no histórico, sem removê-los.

**ANTES** (linha ~1690):
```python
# 3. Fetch history for the instance
history_collection = mongo_db["history"]
history_cursor = history_collection.find({"instance_id": instance_id}).sort("timestamp", 1)
history = [mongo_to_dict(dict(item)) for item in history_cursor]
```

**DEPOIS**:
```python
# 3. Fetch history for the instance
history_collection = mongo_db["history"]
history_cursor = history_collection.find({"instance_id": instance_id}).sort("timestamp", 1)

# 🔍 IMPORTANTE: NÃO remover _id, pois frontend precisa para inativar
history = []
for item in history_cursor:
    doc = dict(item)

    # Converter ObjectId para string se necessário
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])

    # Garantir retrocompatibilidade: se não tiver 'isDeleted', assume False
    if "isDeleted" not in doc:
        doc["isDeleted"] = False

    history.append(doc)
```

---

### 3. `src/api/app.py` - Modificar função `mongo_to_dict()`
**Linha afetada**: Localizar função `mongo_to_dict()` (provavelmente próximo ao início do arquivo)

**Mudança**: Manter campo `_id` em vez de removê-lo.

**ANTES** (exemplo típico):
```python
def mongo_to_dict(item: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    # Remove _id field (comum em implementações antigas)
    if "_id" in item:
        del item["_id"]

    # Convert datetime objects to ISO format strings
    for key, value in item.items():
        if hasattr(value, "isoformat"):
            item[key] = value.isoformat()

    return item
```

**DEPOIS**:
```python
def mongo_to_dict(item: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    # ✅ MANTER _id (não remover) - convertê-lo para string
    if "_id" in item and hasattr(item["_id"], "__str__"):
        item["_id"] = str(item["_id"])

    # Convert datetime objects to ISO format strings
    for key, value in item.items():
        if hasattr(value, "isoformat"):  # datetime, date, or time object
            item[key] = value.isoformat()

    return item
```

**NOTA**: Se a função `mongo_to_dict()` não existir, você pode pular esta etapa - a modificação no endpoint de contexto já cobre a conversão.

---

## 🔄 Fluxo de Dados

### Fluxo 1: Carregar Histórico (Frontend pede contexto)
```
Frontend → GET /api/agents/context/{instance_id}
         ↓
Gateway: get_agent_context()
         ↓
MongoDB: find({"instance_id": ...})
         ↓
Gateway: Converte _id para string, adiciona isDeleted=false (se ausente)
         ↓
Frontend ← {persona, procedure, history: [{_id, user_input, ai_response, isDeleted, ...}], cwd}
```

### Fluxo 2: Inativar Mensagem (Frontend clica 🗑️)
```
Frontend → PATCH /api/agents/history/{history_id}/deactivate
         ↓
Gateway: deactivate_history_entry()
         ↓
MongoDB: update_one({"_id": history_id}, {$set: {isDeleted: true, deletedAt: ...}})
         ↓
Frontend ← {success: true, message: "...", history_id: "..."}
```

---

## 📝 Regras de Negócio Implementadas

### RN1: Soft Delete (Inativação)
- **O que**: Mensagens não são excluídas fisicamente, apenas marcadas como `isDeleted: true`
- **Onde**: Endpoint `PATCH /deactivate`
- **Auditoria**: Campo `deletedAt` registra quando foi inativada

### RN2: Retrocompatibilidade no Retorno de Histórico
- **O que**: Mensagens antigas (sem `isDeleted`) devem ter campo adicionado como `false`
- **Onde**: Endpoint `GET /context/{instance_id}`
- **Como**: `if "isDeleted" not in doc: doc["isDeleted"] = False`

### RN3: Retornar `_id` para o Frontend
- **O que**: Frontend precisa do `_id` do MongoDB para fazer a inativação
- **Onde**: Endpoint `GET /context/{instance_id}`
- **Como**: Converter ObjectId para string: `doc["_id"] = str(doc["_id"])`

---

## ✅ Critérios de Sucesso

1. ✅ Endpoint `PATCH /api/agents/history/{id}/deactivate` retorna `{success: true}` quando bem-sucedido
2. ✅ Endpoint retorna `404` se `history_id` não existir
3. ✅ Documento no MongoDB tem `isDeleted: true` e `deletedAt` após inativação
4. ✅ Endpoint `GET /api/agents/context/{instance_id}` retorna campo `_id` (string)
5. ✅ Endpoint adiciona `isDeleted: false` para mensagens antigas que não têm o campo
6. ✅ Logs indicam sucesso/falha das operações

---

## 🔗 Dependências

### Upstream (bloqueia este trabalho)
- **conductor**: Schema MongoDB com campo `isDeleted` (pode ser implementado em paralelo)

### Downstream (depende deste trabalho)
- **conductor-web**: Frontend precisa deste endpoint para inativar mensagens

---

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| `_id` não é string (é ObjectId) | Alto | Converter explicitamente: `str(doc["_id"])` |
| Mensagens antigas sem `isDeleted` | Médio | Adicionar campo com valor `false` no retorno |
| Erro de conexão MongoDB | Alto | `if mongo_db is None: raise HTTPException(503)` |
| Concorrência (duas requisições inativando mesma msg) | Baixo | MongoDB `update_one` é idempotente |

---

## 🚀 Ordem de Implementação Sugerida

1. **Passo 1**: Modificar `mongo_to_dict()` para não remover `_id` (se a função existir)
2. **Passo 2**: Modificar endpoint `GET /api/agents/context/{instance_id}` para retornar `_id` e `isDeleted`
3. **Passo 3**: Criar endpoint `PATCH /api/agents/history/{history_id}/deactivate`
4. **Passo 4**: Validar manualmente com cURL:
   ```bash
   # 1. Obter contexto e pegar um _id
   curl http://localhost:8001/api/agents/context/{instance_id}

   # 2. Inativar mensagem
   curl -X PATCH http://localhost:8001/api/agents/history/{_id}/deactivate

   # 3. Verificar no MongoDB que isDeleted=true
   ```

---

## 📚 Referências

- **Screenplay completo**: `requisitos_inativar_mensagens_chat.md`
- **Código atual**:
  - `src/api/app.py:1673-1755` (endpoint de contexto)

---

## 🎯 Estimativa de Esforço

- **Complexidade**: Média
- **Tempo estimado**: 2-3 horas
- **Arquivos modificados**: 1 (`app.py`)
- **Linhas de código**: ~60 linhas adicionadas/modificadas

---

## 🧪 Validação Manual (Opcional)

### Teste 1: Obter contexto com `_id`
```bash
curl http://localhost:8001/api/agents/context/abc-123-instance-id | jq '.history[0]._id'
# Esperado: "673fa1c2d8e9f2a1b3c4d5e6" (string)
```

### Teste 2: Inativar mensagem
```bash
curl -X PATCH http://localhost:8001/api/agents/history/673fa1c2d8e9f2a1b3c4d5e6/deactivate
# Esperado: {"success": true, "message": "History entry deactivated", "history_id": "..."}
```

### Teste 3: Verificar no MongoDB
```bash
mongosh
> use conductor
> db.history.findOne({_id: "673fa1c2d8e9f2a1b3c4d5e6"})
# Esperado: { ..., isDeleted: true, deletedAt: ISODate("...") }
```

---

**Plano criado em**: 2025-11-01
**Projeto**: conductor-gateway (API Gateway)
**Saga**: Inativar Mensagens do Histórico do Chat
