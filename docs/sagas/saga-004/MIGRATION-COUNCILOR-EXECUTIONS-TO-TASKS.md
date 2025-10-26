# 🔄 Migration: councilor_executions → tasks

**Saga:** SAGA-004 - Sistema de Conselheiros
**Data:** 2025-10-25
**Status:** ✅ COMPLETO

---

## 🎯 Objetivo

Eliminar redundância entre as collections `councilor_executions` e `tasks`, consolidando todas as execuções na collection `tasks` com a flag `is_councilor_execution=True`.

---

## ❌ Problema: Redundância

### **Antes:**

Tínhamos **DUAS collections** para armazenar execuções:

#### 1. `councilor_executions` (específica para conselheiros)
```javascript
{
  "execution_id": "exec_security-audit_1234567890",
  "councilor_id": "security-audit",
  "started_at": ISODate("2025-10-25T10:00:00Z"),
  "completed_at": ISODate("2025-10-25T10:05:00Z"),
  "duration_ms": 300000,
  "status": "completed",
  "severity": "warning",
  "output": "...",
  "error": null,
  "created_at": ISODate("2025-10-25T10:00:00Z")
}
```

#### 2. `tasks` (para todas as execuções)
```javascript
{
  "task_id": "task_123",
  "agent_id": "code-analyzer",
  "instance_id": "instance-abc",
  "status": "completed",
  "result": "...",
  "created_at": ISODate("2025-10-25T10:00:00Z"),
  "completed_at": ISODate("2025-10-25T10:02:00Z")
}
```

### **Problemas:**
- ❌ Dados duplicados
- ❌ Duas fontes de verdade
- ❌ Manutenção duplicada de indexes
- ❌ Queries fragmentadas (buscar em duas collections)
- ❌ Inconsistência de schema

---

## ✅ Solução: Collection Unificada

### **Depois:**

**UMA collection** `tasks` para TODAS as execuções (agentes normais + conselheiros):

```javascript
// Execução de agente normal
{
  "task_id": "task_123",
  "agent_id": "code-analyzer",
  "instance_id": "instance-abc",
  "is_councilor_execution": false,  // ← Flag
  "status": "completed",
  "result": "...",
  "created_at": ISODate("2025-10-25T10:00:00Z"),
  "completed_at": ISODate("2025-10-25T10:02:00Z"),
  "duration": 120
}

// Execução de conselheiro
{
  "task_id": "exec_security-audit_1234567890",
  "agent_id": "security-audit",
  "instance_id": "councilor_security-audit_1234567890",
  "is_councilor_execution": true,  // ← Flag que identifica conselheiro
  "councilor_config": {
    "task_name": "Security Audit",
    "display_name": "🔒 Auditor de Segurança"
  },
  "status": "completed",
  "severity": "warning",
  "result": "...",
  "error": null,
  "created_at": ISODate("2025-10-25T10:00:00Z"),
  "completed_at": ISODate("2025-10-25T10:05:00Z"),
  "duration": 300
}
```

### **Benefícios:**
- ✅ Uma única fonte de verdade
- ✅ Schema consistente
- ✅ Queries unificadas
- ✅ Fácil filtrar: `{is_councilor_execution: true}`
- ✅ Menos código para manter

---

## 🔧 Mudanças Implementadas

### **1. CouncilorScheduler (`councilor_scheduler.py`)** ✅

**Antes:**
```python
self.executions_collection = db.councilor_executions

# Salvar execução
await self.executions_collection.insert_one({
    "execution_id": execution_id,
    "councilor_id": agent_id,
    "started_at": start_time,
    ...
})
```

**Depois:**
```python
self.tasks_collection = db.tasks  # ← Mudança

# Salvar execução
await self.tasks_collection.insert_one({
    "task_id": execution_id,
    "agent_id": agent_id,
    "instance_id": f"councilor_{agent_id}_{timestamp}",
    "is_councilor_execution": True,  # ← Flag
    "councilor_config": {
        "task_name": task_name,
        "display_name": display_name
    },
    "status": "completed",
    "severity": severity,
    "result": output,
    "created_at": start_time,
    "completed_at": end_time,
    "duration": (end_time - start_time).total_seconds()
})
```

---

### **2. Indexes (`app.py`)** ✅

**Antes:**
```python
# Indexes apenas para councilor_executions
councilor_executions = mongo_db["councilor_executions"]
councilor_executions.create_index("execution_id", unique=True)
councilor_executions.create_index([("councilor_id", 1), ("started_at", -1)])
```

**Depois:**
```python
# Indexes para tasks (inclui conselheiros)
tasks_collection = mongo_db["tasks"]
tasks_collection.create_index("task_id", unique=True)
tasks_collection.create_index([("agent_id", 1), ("created_at", -1)])
tasks_collection.create_index("is_councilor_execution")  # ← Novo index
tasks_collection.create_index([("is_councilor_execution", 1), ("created_at", -1)])

# Legacy indexes (mantidos para compatibilidade com dados antigos)
councilor_executions = mongo_db["councilor_executions"]
try:
    councilor_executions.create_index("execution_id", unique=True)
    # ...
    logger.info("Created indexes on councilor_executions collection (legacy)")
except Exception as e:
    logger.warning(f"⚠️ Failed to create legacy indexes: {e}")
```

---

### **3. CouncilorService (`councilor_service.py`)** ✅

**Já estava correto:**
```python
class CouncilorService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.tasks_collection = db.tasks  # ✅ Usa tasks
        # Manter referência para councilor_executions para migração
        self.legacy_executions_collection = db.councilor_executions  # Para compat.
```

---

## 📊 Queries de Migração

### **Buscar execuções de conselheiros:**

**Antes:**
```javascript
// Precisava buscar em duas collections
db.councilor_executions.find({ "councilor_id": "security-audit" })
```

**Depois:**
```javascript
// Uma única query
db.tasks.find({
  "is_councilor_execution": true,
  "agent_id": "security-audit"
})
```

### **Buscar TODAS as execuções de um agente:**

**Antes:**
```javascript
// Precisava unir resultados de duas collections
const normalTasks = db.tasks.find({ "agent_id": "security-audit" })
const councilorTasks = db.councilor_executions.find({ "councilor_id": "security-audit" })
// Merge manual...
```

**Depois:**
```javascript
// Uma única query
db.tasks.find({ "agent_id": "security-audit" })
```

### **Buscar execuções recentes de conselheiros:**

```javascript
db.tasks.find({
  "is_councilor_execution": true
}).sort({ "created_at": -1 }).limit(10)
```

---

## 🔄 Migração de Dados Existentes (Opcional)

Se houver dados antigos em `councilor_executions`, você pode migrá-los para `tasks`:

```javascript
// MongoDB migration script
db.councilor_executions.find().forEach(function(doc) {
  db.tasks.insert({
    task_id: doc.execution_id,
    agent_id: doc.councilor_id,
    instance_id: "councilor_" + doc.councilor_id + "_" + doc.started_at.getTime(),
    is_councilor_execution: true,
    councilor_config: {
      task_name: doc.councilor_id,  // Adjust as needed
      display_name: doc.councilor_id
    },
    status: doc.status,
    severity: doc.severity,
    result: doc.output,
    error: doc.error,
    created_at: doc.started_at,
    completed_at: doc.completed_at,
    duration: doc.duration_ms ? doc.duration_ms / 1000 : null
  });
});

// Verificar migração
print("Total em councilor_executions:", db.councilor_executions.count());
print("Total migrado para tasks:", db.tasks.count({ is_councilor_execution: true }));

// Após verificação, você pode remover councilor_executions (OPCIONAL)
// db.councilor_executions.drop();
```

---

## 📝 Schema da Collection `tasks`

```javascript
{
  // Identificação
  "task_id": String,           // ID único da task
  "agent_id": String,          // ID do agente que executou
  "instance_id": String,       // ID da instância (para isolamento)

  // Flag de conselheiro
  "is_councilor_execution": Boolean,  // true para conselheiros, false/undefined para normais

  // Config específica de conselheiro (apenas se is_councilor_execution=true)
  "councilor_config": {
    "task_name": String,       // Nome da task do conselheiro
    "display_name": String     // Nome de exibição customizado
  },

  // Status e resultado
  "status": String,            // "completed", "error", "processing"
  "severity": String,          // "success", "warning", "error"
  "result": String,            // Output da execução
  "error": String,             // Mensagem de erro (se houver)

  // Timestamps
  "created_at": ISODate,       // Quando iniciou
  "completed_at": ISODate,     // Quando completou
  "duration": Number           // Duração em segundos
}
```

---

## 🧪 Como Testar

### **1. Verificar que conselheiros salvam em tasks:**

```bash
# 1. Executar um conselheiro (aguardar schedule ou forçar)
# 2. Verificar no MongoDB:

mongosh
> use conductor_state
> db.tasks.find({ "is_councilor_execution": true }).sort({ created_at: -1 }).limit(1).pretty()
```

Você deve ver:
```javascript
{
  _id: ObjectId("..."),
  task_id: "exec_security-audit_...",
  agent_id: "security-audit",
  is_councilor_execution: true,
  councilor_config: {
    task_name: "Security Audit",
    display_name: "🔒 Auditor de Segurança"
  },
  status: "completed",
  severity: "success",
  ...
}
```

### **2. Verificar que não salva mais em councilor_executions:**

```bash
> db.councilor_executions.find().sort({ created_at: -1 }).limit(1)
```

Deve mostrar apenas dados antigos (se houver), mas não novos registros.

---

## ✅ Checklist de Migração

- [x] Atualizar `CouncilorScheduler` para usar `tasks_collection`
- [x] Adicionar flag `is_councilor_execution=True` ao salvar
- [x] Criar indexes para `is_councilor_execution`
- [x] Marcar `councilor_executions` como legacy
- [x] Manter backward compatibility com dados antigos
- [x] Atualizar documentação

---

## 📚 Referências

- **Pendência Original:** `docs/sagas/saga-004/PENDENCIA-REFATORACAO-EVENTOS-BACKEND.md`
- **WebSocket Implementation:** `docs/sagas/saga-004/WEBSOCKET-IMPLEMENTATION.md`
- **Arquivo Principal:** `src/conductor-gateway/src/services/councilor_scheduler.py`

---

**Status:** ✅ COMPLETO
**Última atualização:** 2025-10-25
