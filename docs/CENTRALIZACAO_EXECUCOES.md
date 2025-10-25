# Centralização de Execuções: tasks unificado

## 📋 Resumo

Este documento descreve a centralização do sistema de execuções, unificando `councilor_executions` e `tasks` em uma única coleção.

**Data:** 2025-10-25
**Status:** ✅ Implementado

---

## 🎯 Objetivo

Eliminar a duplicação entre `tasks` e `councilor_executions`, centralizando todas as execuções de agentes (conselheiros ou não) na coleção `tasks`.

---

## 🔍 Problemas Identificados

### Antes da Centralização

**Duas coleções com propósitos sobrepostos:**

1. **`tasks`** (src/conductor)
   - Execuções gerais de agentes
   - Tracking de status (pending → processing → completed)
   - Suporte a instance_id e context

2. **`councilor_executions`** (conductor-gateway)
   - Execuções específicas de conselheiros
   - Análise de severidade (success/warning/error)
   - Tracking de estatísticas

**Problemas:**
- ❌ Duplicação de código e lógica
- ❌ Inconsistências entre os dois sistemas
- ❌ Dificuldade para análises unificadas
- ❌ Manutenção de dois schemas diferentes
- ❌ Impossibilidade de rastrear execuções de conselheiros com contexto (instance_id)

---

## ✅ Solução Implementada

### Nova Estrutura Unificada

**Coleção:** `tasks`

```python
{
    "_id": ObjectId,
    "agent_id": str,
    "provider": str,
    "prompt": str,
    "cwd": str,
    "timeout": int,
    "status": "pending|processing|completed|error",
    "instance_id": str,
    "context": {},
    "created_at": datetime,
    "updated_at": datetime,
    "started_at": datetime,
    "completed_at": datetime,
    "result": str,
    "exit_code": int,
    "duration": float,
    # 🆕 Campos específicos para conselheiros
    "is_councilor_execution": bool,
    "councilor_config": {
        "title": str,
        "task_name": str
    },
    "severity": "success|warning|error"
}
```

---

## 🛠️ Implementação

### 1. MongoTaskClient (src/conductor)

**Arquivo:** `src/conductor/src/core/services/mongo_task_client.py`

**Mudanças:**
- ✅ `submit_task()` aceita `is_councilor_execution` e `councilor_config`
- ✅ Novos métodos:
  - `analyze_severity(result: str) → str`
  - `update_task_severity(task_id, severity)`
  - `get_councilor_executions(agent_id, limit)`
  - `get_councilor_stats(agent_id)`
  - `ensure_councilor_indexes()`

### 2. CouncilorService (conductor-gateway)

**Arquivo:** `src/conductor-gateway/src/services/councilor_service.py`

**Mudanças:**
- ✅ Usa `tasks_collection` ao invés de `councilor_executions`
- ✅ `get_executions()` lê de tasks com filtro `is_councilor_execution=True`
- ✅ `get_latest_execution()` lê de tasks
- ✅ `_update_agent_stats()` calcula stats a partir de tasks
- ✅ `save_execution()` marcado como DEPRECATED

### 3. Índices MongoDB

**Novos índices criados:**
```javascript
// Índice composto para queries de conselheiros
db.tasks.createIndex({
    "agent_id": 1,
    "is_councilor_execution": 1,
    "created_at": -1
})

// Índice para severity
db.tasks.createIndex({"severity": 1})

// Índice para is_councilor_execution
db.tasks.createIndex({"is_councilor_execution": 1})
```

---

## 📦 Script de Migração

**Arquivo:** `migrate_councilor_executions.py`

**Uso:**
```bash
# Dry-run (sem modificar dados)
python migrate_councilor_executions.py --dry-run

# Migração real
python migrate_councilor_executions.py

# Com opções personalizadas
python migrate_councilor_executions.py --batch-size=50 --no-backup
```

**O que faz:**
1. ✅ Cria backup de `councilor_executions` → `councilor_executions_backup`
2. ✅ Migra documentos para `tasks` com mapeamento de campos
3. ✅ Cria índices necessários
4. ✅ Verifica duplicatas (não migra o que já existe)
5. ✅ Relatório detalhado de migração

---

## 🔄 Fluxo de Execução de Conselheiros

### Antes
```
CouncilorScheduler.execute_task()
    ↓
Agent execution
    ↓
CouncilorService.save_execution()
    ↓
councilor_executions collection
```

### Depois
```
CouncilorScheduler.execute_task()
    ↓
MongoTaskClient.submit_task(is_councilor_execution=True)
    ↓
Agent execution
    ↓
MongoTaskClient.update_task_severity()
    ↓
tasks collection
    ↓
CouncilorService._update_agent_stats()
```

---

## 📊 Benefícios

### ✅ Unificação
- Uma única fonte de verdade para todas as execuções
- Schema consistente em todo o sistema
- Queries mais simples e eficientes

### ✅ Contexto Completo
- Conselheiros agora têm `instance_id` e `context`
- Possibilita rastreamento por sessão/UI
- Integração com sistema de histórico

### ✅ Análise Unificada
- Relatórios podem incluir todas as execuções (conselheiro ou não)
- Métricas globais do sistema
- Debug mais fácil

### ✅ Manutenibilidade
- Menos código para manter
- Lógica centralizada
- Evolução mais fácil

---

## 🧪 Testes

### Verificar Migração
```python
from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client.conductor_state

# Contar execuções migradas
migrated = db.tasks.count_documents({"is_councilor_execution": True})
legacy = db.councilor_executions.count_documents({})

print(f"Execuções migradas: {migrated}")
print(f"Execuções legacy: {legacy}")

# Verificar primeira execução migrada
sample = db.tasks.find_one({"is_councilor_execution": True})
print(sample)
```

### Testar API
```bash
# Listar execuções de um conselheiro
curl http://localhost:8000/api/councilors/agent-123/councilor-reports

# Verificar relatório
curl http://localhost:8000/api/councilors/agent-123/councilor-reports?limit=5
```

---

## 🚀 Próximos Passos

### Fase 1: Validação (1-2 semanas)
1. ✅ Executar migração em ambiente de desenvolvimento
2. ✅ Validar dados migrados
3. ✅ Testar todas as funcionalidades do frontend
4. ✅ Verificar estatísticas de conselheiros
5. ✅ Confirmar que novos relatórios aparecem corretamente

### Fase 2: Produção
1. ✅ Executar migração em produção (com backup!)
2. ✅ Monitorar logs por 24-48h
3. ✅ Validar performance das queries

### Fase 3: Cleanup (após validação)
```bash
# Após validar que tudo funciona:
mongosh
> use conductor_state
> db.councilor_executions.drop()  # Remove coleção legacy
> db.councilor_executions_backup.drop()  # Remove backup (se quiser)
```

---

## ⚠️ Rollback

Se necessário reverter:

```python
from pymongo import MongoClient

client = MongoClient(MONGO_URI)
db = client.conductor_state

# Restaurar backup
if db.councilor_executions_backup.count_documents({}) > 0:
    # Limpar coleção atual
    db.councilor_executions.delete_many({})

    # Restaurar do backup
    docs = list(db.councilor_executions_backup.find())
    if docs:
        db.councilor_executions.insert_many(docs)
        print(f"✅ Restaurados {len(docs)} documentos")

# Remover execuções de conselheiros de tasks
db.tasks.delete_many({"is_councilor_execution": True})
```

---

## 📝 Referências

- **Arquivo de análise:** `/docs/analise-execucoes.md`
- **MongoTaskClient:** `src/conductor/src/core/services/mongo_task_client.py`
- **CouncilorService:** `src/conductor-gateway/src/services/councilor_service.py`
- **Script de migração:** `migrate_councilor_executions.py`

---

## 👥 Contato

Se tiver dúvidas sobre a centralização, consulte:
- Documentação técnica neste arquivo
- Código fonte com comentários detalhados
- Script de migração com logs verbosos
