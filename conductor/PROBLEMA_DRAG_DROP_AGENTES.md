# 🐛 Problema: Drag & Drop de Agentes não Persiste no MongoDB

**Data:** 2025-11-05
**Status:** 🔴 Bug Identificado
**Componentes Afetados:** Frontend (Angular) + Backend (Gateway API)

---

## 📋 Resumo do Problema

O sistema de drag & drop de agentes no dock lateral está funcionando **parcialmente**:

- ✅ **Funciona:** Arrastar e soltar agentes reordena visualmente
- ✅ **Funciona:** Chamada ao endpoint `/api/agents/instances/reorder` é feita
- ❌ **Falha:** O campo `display_order` NÃO está sendo salvo no MongoDB
- ❌ **Falha:** Ao recarregar a página (F5), a ordem volta ao original

---

## 🔍 Contexto Técnico

### Arquitetura do Sistema

```
Frontend (Angular)
  └─> conductor-chat.component.ts (Dock de agentes)
       └─> onAgentDrop() → emite evento
            └─> screenplay-interactive.ts
                 └─> onAgentOrderChanged()
                      ├─> Atualiza contextualAgents[] local
                      ├─> Atualiza display_order no Map agentInstances
                      └─> saveAgentOrder()
                           └─> fetch('/api/agents/instances/reorder')

Backend (Gateway FastAPI)
  └─> conductor-gateway/src/api/app.py
       └─> @app.patch("/api/agents/instances/reorder")
            └─> Recebe: {"order_updates": [{instance_id, display_order}]}
            └─> Atualiza MongoDB: agent_instances.update_one()
```

---

## 🎯 Fluxo Atual (Com Problema)

### 1. **Frontend: Drag & Drop** ✅ Funciona

**Arquivo:** `conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts:3151-3166`

```typescript
onAgentDrop(event: CdkDragDrop<any[]>): void {
  if (event.previousIndex === event.currentIndex) return;

  console.log(`🔄 [AGENT-DRAG-DROP] Movendo agente de ${event.previousIndex} para ${event.currentIndex}`);

  const reorderedAgents = [...this.contextualAgents];
  moveItemInArray(reorderedAgents, event.previousIndex, event.currentIndex);

  // Emite evento para o pai
  this.agentOrderChanged.emit(reorderedAgents);
}
```

**Status:** ✅ Este código funciona corretamente

---

### 2. **Frontend: Recebe Reordenação e Atualiza Localmente** ✅ Funciona

**Arquivo:** `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts:3339-3367`

```typescript
public onAgentOrderChanged(reorderedAgents: any[]): void {
  this.logging.info('🔄 [AGENT-ORDER-CHANGED] Nova ordem de agentes recebida', 'ScreenplayInteractive', {
    count: reorderedAgents.length
  });

  // Atualizar array local
  this.contextualAgents = reorderedAgents;

  // 🔥 IMPORTANTE: Atualizar display_order no Map de instâncias IMEDIATAMENTE
  reorderedAgents.forEach((agent, index) => {
    const instance = this.agentInstances.get(agent.id);
    if (instance) {
      (instance as any).display_order = index;
      this.logging.debug(`📍 [AGENT-ORDER] Updated display_order=${index} for agent ${agent.id}`, 'ScreenplayInteractive');
    }
  });

  // Preparar updates para o backend
  const orderUpdates = reorderedAgents.map((agent, index) => ({
    instance_id: agent.id,
    display_order: index
  }));

  this.logging.info('💾 [AGENT-ORDER] Salvando ordem no MongoDB', 'ScreenplayInteractive', orderUpdates);

  // Chamar endpoint para atualizar ordem
  this.saveAgentOrder(orderUpdates);
}
```

**Status:** ✅ Este código funciona corretamente

---

### 3. **Frontend: Envia para Backend** ✅ Funciona

**Arquivo:** `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts:3369-3384`

```typescript
private saveAgentOrder(orderUpdates: Array<{ instance_id: string; display_order: number }>): void {
  const baseUrl = this.agentService['baseUrl'] || '';

  fetch(`${baseUrl}/api/agents/instances/reorder`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_updates: orderUpdates })
  })
    .then(response => {
      if (response.ok) {
        this.logging.info('✅ [AGENT-ORDER] Ordem salva com sucesso', 'ScreenplayInteractive');
      } else {
        this.logging.warn('⚠️ [AGENT-ORDER] Falha ao salvar ordem:', 'ScreenplayInteractive', response.status);
        this.updateAgentDockLists();
      }
    })
    .catch(error => {
      this.logging.error('❌ [AGENT-ORDER] Erro ao salvar ordem:', error, 'ScreenplayInteractive');
      this.updateAgentDockLists();
    });
}
```

**Status:** ✅ A requisição é enviada corretamente

**Exemplo de Payload:**
```json
{
  "order_updates": [
    {"instance_id": "instance-1730824000000-abc", "display_order": 0},
    {"instance_id": "instance-1730824001000-def", "display_order": 1},
    {"instance_id": "instance-1730824002000-ghi", "display_order": 2}
  ]
}
```

---

### 4. **Backend: Recebe e Processa** ⚠️ **PROBLEMA AQUI**

**Arquivo:** `conductor-gateway/src/api/app.py:1445-1515`

```python
@app.patch("/api/agents/instances/reorder")
async def reorder_agent_instances(payload: dict[str, Any]):
    """
    🔥 NOVO: Atualiza a ordem de exibição dos agentes no dock.
    """
    if mongo_db is None:
        raise HTTPException(status_code=503, detail="MongoDB connection not available")

    try:
        order_updates = payload.get("order_updates", [])

        if not order_updates or not isinstance(order_updates, list):
            raise HTTPException(
                status_code=400,
                detail="Campo 'order_updates' é obrigatório e deve ser uma lista"
            )

        logger.info(f"🔄 [REORDER] Atualizando ordem de {len(order_updates)} agentes")

        agent_instances = mongo_db["agent_instances"]
        updated_count = 0

        for update in order_updates:
            instance_id = update.get("instance_id")
            display_order = update.get("display_order")

            if not instance_id or display_order is None:
                logger.warning(f"⚠️ [REORDER] Update inválido ignorado: {update}")
                continue

            result = agent_instances.update_one(
                {"instance_id": instance_id},
                {
                    "$set": {
                        "display_order": display_order,
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )

            if result.matched_count > 0:
                updated_count += 1

        logger.info(f"✅ [REORDER] Ordem atualizada para {updated_count}/{len(order_updates)} agentes")

        return {
            "success": True,
            "message": f"Ordem atualizada para {updated_count} agentes",
            "updated_count": updated_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [REORDER] Erro ao atualizar ordem dos agentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Status:** ⚠️ O código **parece** correto, mas o `display_order` não está sendo salvo no MongoDB

---

### 5. **Frontend: Carregamento no Reload** ✅ Funciona

**Arquivo:** `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts:3256-3275`

```typescript
.sort((a, b) => {
  // 🔥 NOVO: Ordenar por display_order se disponível, senão por data de criação
  const aOrder = (a as any).display_order;
  const bOrder = (b as any).display_order;

  // Se ambos têm display_order, usar isso
  if (aOrder !== undefined && bOrder !== undefined) {
    return aOrder - bOrder;
  }

  // Se apenas um tem display_order, ele vem primeiro
  if (aOrder !== undefined) return -1;
  if (bOrder !== undefined) return 1;

  // Caso contrário, ordenar por data de criação (mais antigo primeiro)
  const dateA = a.config?.createdAt ? new Date(a.config.createdAt).getTime() : 0;
  const dateB = b.config?.createdAt ? new Date(b.config.createdAt).getTime() : 0;
  return dateA - dateB;
});
```

**Status:** ✅ O código de ordenação está correto e usa `display_order` quando disponível

---

## 🔍 Investigação Necessária

### Possíveis Causas

#### 1. **Query do MongoDB não encontra documentos**
```python
result = agent_instances.update_one(
    {"instance_id": instance_id},  # ⚠️ Pode não estar encontrando?
    {"$set": {"display_order": display_order}}
)
```

**Verificar:**
- O campo no MongoDB é `instance_id` ou `_id`?
- O valor de `instance_id` está correto (exemplo: `"instance-1730824000000-abc"`)?
- Há filtros adicionais (como `isDeleted`, `conversation_id`) que impedem o match?

#### 2. **Endpoint retorna sucesso mas não salva**
```python
if result.matched_count > 0:
    updated_count += 1  # ⚠️ Isso está sendo incrementado?
```

**Verificar:**
- O log `✅ [REORDER] Ordem atualizada para X/Y agentes` mostra quantos foram atualizados?
- `matched_count` é > 0?
- `modified_count` é > 0?

#### 3. **Permissões do MongoDB**
- O usuário do MongoDB tem permissão de `update` na coleção `agent_instances`?
- Há índices ou restrições que impedem o update?

#### 4. **Concorrência / Race Condition**
- Outro processo está sobrescrevendo o campo?
- O `display_order` está sendo removido por outro update?

---

## 📊 Dados para Diagnóstico

### Logs Esperados no Console (Browser)

Ao arrastar um agente, deve aparecer:
```
🔄 [AGENT-DRAG-DROP] Movendo agente de 0 para 2
🔄 [AGENT-ORDER-CHANGED] Nova ordem de agentes recebida {count: 3}
📍 [AGENT-ORDER] Updated display_order=0 for agent instance-xxx
📍 [AGENT-ORDER] Updated display_order=1 for agent instance-yyy
📍 [AGENT-ORDER] Updated display_order=2 for agent instance-zzz
💾 [AGENT-ORDER] Salvando ordem no MongoDB [{instance_id: "instance-xxx", display_order: 0}, ...]
✅ [AGENT-ORDER] Ordem salva com sucesso
```

### Logs Esperados no Backend (Gateway)

```
🔄 [REORDER] Atualizando ordem de 3 agentes
✅ [REORDER] Ordem atualizada para 3/3 agentes
```

### Verificação no MongoDB

```javascript
// No mongosh
use conductor
db.agent_instances.find({display_order: {$exists: true}}).pretty()

// Deve retornar documentos com:
{
  "_id": ObjectId("..."),
  "instance_id": "instance-1730824000000-abc",
  "display_order": 0,  // ⚠️ Este campo deve existir
  "agent_id": "AgentName",
  "conversation_id": "conv-xxx",
  "created_at": "2025-11-05T...",
  "updated_at": "2025-11-05T..."  // ⚠️ Deve ter sido atualizado
}
```

**Verificação específica:**
```javascript
// Contar quantos agentes têm display_order
db.agent_instances.countDocuments({display_order: {$exists: true}})

// Ver um exemplo completo
db.agent_instances.findOne({display_order: {$exists: true}})

// Ver todos os instance_id
db.agent_instances.find({}, {instance_id: 1, display_order: 1, _id: 0}).pretty()
```

---

## 🧪 Testes de Diagnóstico

### 1. Verificar se o endpoint está sendo chamado

**No DevTools (Network tab):**
- Procurar requisição `PATCH /api/agents/instances/reorder`
- Verificar:
  - Status Code: deve ser `200 OK`
  - Request Payload: deve conter `order_updates` com `instance_id` e `display_order`
  - Response: deve conter `{"success": true, "updated_count": N}`

### 2. Verificar logs do backend

**No terminal do Gateway:**
```bash
docker-compose logs -f gateway | grep REORDER
```

Deve mostrar:
```
gateway_1  | 🔄 [REORDER] Atualizando ordem de 3 agentes
gateway_1  | ✅ [REORDER] Ordem atualizada para 3/3 agentes
```

### 3. Testar endpoint diretamente

```bash
curl -X PATCH http://localhost:5006/api/agents/instances/reorder \
  -H "Content-Type: application/json" \
  -d '{
    "order_updates": [
      {"instance_id": "instance-1730824000000-abc", "display_order": 0},
      {"instance_id": "instance-1730824001000-def", "display_order": 1}
    ]
  }'
```

Verificar:
- Response: `{"success": true, "updated_count": 2}`
- MongoDB: `db.agent_instances.find({instance_id: {$in: ["instance-1730824000000-abc", "instance-1730824001000-def"]}}).pretty()`

---

## 🎯 Comparação com Conversas (Funciona)

O drag & drop de **conversas** funciona perfeitamente. Comparação:

| Aspecto | Conversas ✅ | Agentes ❌ |
|---------|-------------|-----------|
| **Endpoint** | `/api/conversations/reorder` | `/api/agents/instances/reorder` |
| **Coleção** | `conversations` | `agent_instances` |
| **Campo ID** | `conversation_id` | `instance_id` |
| **Campo Ordem** | `display_order` | `display_order` |
| **Frontend** | conversation-list.component.ts | conductor-chat.component.ts → screenplay-interactive.ts |
| **Salvamento** | ✅ Funciona | ❌ Não salva |

**Código de Conversas que funciona:**

```python
# conductor/src/core/services/conversation_service.py:471-510
def update_conversation_order(self, order_updates: List[Dict[str, Any]]) -> int:
    updated_count = 0

    for update in order_updates:
        conversation_id = update.get("conversation_id")
        display_order = update.get("display_order")

        if not conversation_id or display_order is None:
            logger.warning(f"⚠️ Update inválido ignorado: {update}")
            continue

        result = self.conversations.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "display_order": display_order,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        )

        if result.matched_count > 0:
            updated_count += 1

    logger.info(f"✅ Ordem atualizada para {updated_count}/{len(order_updates)} conversas")
    return updated_count
```

**Diferença chave:** As conversas usam um **serviço dedicado** (`conversation_service.py`) que acessa diretamente a coleção MongoDB. Os agentes usam o **endpoint direto** no `app.py`.

---

## 🔑 Próximos Passos para Resolução

1. **Adicionar logs detalhados no backend:**
   ```python
   logger.info(f"🔍 [DEBUG] Tentando atualizar: {instance_id}")
   logger.info(f"🔍 [DEBUG] Match count: {result.matched_count}")
   logger.info(f"🔍 [DEBUG] Modified count: {result.modified_count}")
   ```

2. **Verificar estrutura real do MongoDB:**
   ```javascript
   db.agent_instances.findOne()  // Ver estrutura completa
   ```

3. **Comparar com endpoint GET:**
   ```python
   # app.py:1232 - Endpoint GET funciona
   # Como ele busca? Por qual campo?
   doc = agent_instances.find_one({"instance_id": instance_id, "isDeleted": {"$ne": True}})
   ```

4. **Testar update manual no MongoDB:**
   ```javascript
   db.agent_instances.updateOne(
     {"instance_id": "instance-1730824000000-abc"},
     {"$set": {"display_order": 999}}
   )
   ```

---

## 📝 Informações Adicionais

### Estrutura Esperada do Documento no MongoDB

```javascript
{
  "_id": ObjectId("672a1234567890abcdef1234"),
  "instance_id": "instance-1730824000000-abc123",
  "agent_id": "ScreenplayAssistant_Agent",
  "conversation_id": "conv-1730824000000-xyz",
  "screenplay_id": "672a1234567890abcdef5678",
  "emoji": "🤖",
  "definition": {
    "title": "Assistente de Roteiro",
    "description": "...",
    "unicode": "1f916"
  },
  "position": {"x": 100, "y": 100},
  "status": "pending",
  "created_at": "2025-11-05T12:00:00.000Z",
  "updated_at": "2025-11-05T12:00:00.000Z",
  "display_order": 0,  // ⚠️ Este campo deve ser salvo
  "is_system_default": false,
  "is_hidden": false,
  "isDeleted": false
}
```

### Versões do Sistema

- Angular: 20.3.0
- Angular CDK: 20.2.11
- FastAPI: (verificar versão no requirements.txt)
- PyMongo: (verificar versão no requirements.txt)
- MongoDB: (verificar versão do container)

---

## 🔗 Arquivos Relacionados

### Frontend
- `conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts` (linhas 3151-3166)
- `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts` (linhas 3339-3384)
- `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts` (linhas 3256-3275)

### Backend
- `conductor-gateway/src/api/app.py` (linhas 1445-1515)
- `conductor/src/core/services/conversation_service.py` (linhas 471-510) - **Referência de código que funciona**

### Configuração
- `conductor-web/package.json` (linha 26: @angular/cdk)
- `docker-compose.yml` (configuração do MongoDB)

---

**Última atualização:** 2025-11-05
**Criado por:** Claude Code
**Ticket:** DRAG-DROP-AGENTS-001
