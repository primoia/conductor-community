# 🔍 Análise: Collection `apscheduler_jobs`

**Saga:** SAGA-004 - Sistema de Conselheiros
**Data:** 2025-10-25
**Status:** ⚠️ COLLECTION ÓRFÃ - PODE SER REMOVIDA

---

## 🎯 Objetivo da Análise

Verificar se a collection `apscheduler_jobs` está sendo utilizada e determinar se pode ser removida do MongoDB.

---

## 📊 Situação Atual

### **1. O Que É `apscheduler_jobs`?**

A collection `apscheduler_jobs` é criada automaticamente pelo **APScheduler** quando você configura um **MongoDBJobStore** para persistir jobs agendados no MongoDB.

```python
# Exemplo de configuração que CRIARIA essa collection
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.mongodb import MongoDBJobStore

jobstores = {
    'default': MongoDBJobStore(database='conductor_state', collection='apscheduler_jobs')
}

scheduler = AsyncIOScheduler(jobstores=jobstores)
```

---

### **2. Implementação Atual do CouncilorScheduler**

**Arquivo:** `src/conductor-gateway/src/services/councilor_scheduler.py:48-52`

```python
# Configure APScheduler with in-memory job store
# Note: MongoDB jobstore doesn't work with async objects like ConductorClient
# Jobs are recreated from MongoDB agents collection on startup, so we don't lose them
self.scheduler = AsyncIOScheduler(timezone='UTC')
```

**Análise:**
- ✅ Usa **jobstore in-memory** (padrão do APScheduler)
- ❌ **NÃO** usa MongoDBJobStore
- ✅ Jobs são **recriados** a partir da collection `agents` na inicialização
- ✅ Comentário explica que MongoDB jobstore não funciona com objetos async

---

### **3. Como os Jobs São Persistidos Atualmente?**

#### **A. Jobs Agendados (Configuração):**

**Persistido em:** `db.agents` collection

```javascript
// Exemplo de conselheiro na collection agents
{
  "agent_id": "security-audit",
  "is_councilor": true,
  "councilor_config": {
    "schedule": {
      "enabled": true,
      "type": "interval",
      "value": "30m"
    },
    "task": {
      "name": "Security Audit",
      "prompt": "Analyze security..."
    }
  }
}
```

**Processo:**
1. Servidor inicia → `CouncilorScheduler.start()`
2. `load_councilors()` busca todos os agentes com `is_councilor=true`
3. Para cada conselheiro, cria job no APScheduler in-memory
4. Jobs são executados conforme schedule

**Código:** `councilor_scheduler.py:70-92`

---

#### **B. Execuções (Resultados):**

**Persistido em:** `db.tasks` collection

```javascript
// Exemplo de execução de conselheiro
{
  "task_id": "exec_security-audit_1730000000000",
  "agent_id": "security-audit",
  "is_councilor_execution": true,
  "status": "completed",
  "severity": "warning",
  "result": "...",
  "created_at": ISODate("2025-10-25T10:00:00Z"),
  "completed_at": ISODate("2025-10-25T10:05:00Z")
}
```

**Código:** `councilor_scheduler.py:240-256`

---

### **4. Por Que `apscheduler_jobs` Não É Mais Usada?**

**Motivo técnico:** MongoDB jobstore não suporta objetos async (como `ConductorClient`)

**Trecho do comentário no código:**
```python
# Note: MongoDB jobstore doesn't work with async objects like ConductorClient
```

**Solução adotada:**
- Jobs são **in-memory** (não persistidos no MongoDB)
- Configuração dos jobs vem de `agents` collection
- Na inicialização, jobs são **recriados automaticamente**

**Vantagens:**
- ✅ Funciona com objetos async
- ✅ Simples e eficaz
- ✅ Não perde jobs (recria da source of truth: `agents`)

---

## 🗑️ Conclusão: `apscheduler_jobs` Está Órfã

### **Evidências:**

1. ❌ **Nenhuma referência no código atual**
   ```bash
   $ grep -r "apscheduler_jobs" src/conductor-gateway/src/
   # Nenhum resultado
   ```

2. ❌ **Scheduler usa jobstore in-memory**
   ```python
   self.scheduler = AsyncIOScheduler(timezone='UTC')  # Sem MongoDBJobStore
   ```

3. ❌ **Não há índices criados para essa collection**
   ```python
   # Em app.py, criamos índices para:
   # - agents
   # - tasks
   # - agent_instances
   # - history
   # - councilor_executions (legacy)
   # MAS NÃO para apscheduler_jobs
   ```

4. ✅ **Sistema funciona sem ela**
   - Jobs são recriados de `agents` collection
   - Execuções salvas em `tasks` collection

---

## 📋 Recomendação: REMOVER

### **Opção 1: Remover Definitivamente** ⭐ **RECOMENDADO**

```javascript
// MongoDB shell
use conductor_state

// Verificar se existe
db.apscheduler_jobs.countDocuments()

// Verificar conteúdo (se houver)
db.apscheduler_jobs.find().pretty()

// Fazer backup (opcional)
mongodump --db conductor_state --collection apscheduler_jobs --out backup_apscheduler_jobs

// Remover collection
db.apscheduler_jobs.drop()
```

**Justificativa:**
- Collection não é mais usada
- Nenhum código depende dela
- Sistema funciona perfeitamente sem ela

---

### **Opção 2: Renomear como Legacy (Conservador)**

```javascript
// Renomear para indicar que é legacy
db.apscheduler_jobs.renameCollection("_legacy_apscheduler_jobs")
```

**Justificativa:**
- Mantém dados históricos se houver
- Pode ser removida depois de confirmação

---

## 📊 Comparação: Antes vs Depois

| Aspecto | Antiga Implementação (MongoDB jobstore) | Atual (In-memory + agents) |
|---------|----------------------------------------|---------------------------|
| **Jobs persistidos** | `apscheduler_jobs` collection | `agents` collection (config) |
| **Execuções** | ❓ Provavelmente `councilor_executions` | `tasks` collection |
| **Async support** | ❌ Não funciona | ✅ Funciona |
| **Recriação de jobs** | Automática (APScheduler) | Manual (`load_councilors()`) |
| **Complexidade** | Alta (2 systems) | Baixa (1 source of truth) |

---

## 🧪 Como Verificar

### **1. Verificar se a collection existe:**

```bash
mongosh
> use conductor_state
> db.getCollectionNames().filter(c => c.includes('apscheduler'))

# Deve mostrar algo como:
# [ 'apscheduler_jobs' ]
```

### **2. Verificar conteúdo:**

```javascript
> db.apscheduler_jobs.countDocuments()
// Se retornar 0 ou error: collection está vazia/não existe

> db.apscheduler_jobs.find().limit(5).pretty()
// Ver o que tem dentro (se houver)
```

### **3. Verificar se algum código usa:**

```bash
cd /mnt/ramdisk/primoia-main/conductor-community
grep -r "apscheduler_jobs" src/conductor-gateway/src/
grep -r "MongoDBJobStore" src/conductor-gateway/src/

# Deve retornar: nenhum resultado (ou apenas nos arquivos da lib apscheduler)
```

---

## ✅ Checklist de Remoção

Antes de remover, verificar:

- [ ] Collection `apscheduler_jobs` existe no MongoDB?
- [ ] Contém dados importantes? (provavelmente não)
- [ ] Algum código referencia essa collection? (não, já verificamos)
- [ ] Sistema está funcionando sem ela? (sim)
- [ ] Backup foi feito? (se quiser segurança extra)

**Se todas as respostas indicam que é seguro:**

- [ ] Executar `db.apscheduler_jobs.drop()`
- [ ] Verificar que sistema continua funcionando
- [ ] Atualizar documentação

---

## 📚 Referências

- **APScheduler Docs:** https://apscheduler.readthedocs.io/en/stable/
- **MongoDBJobStore:** https://apscheduler.readthedocs.io/en/stable/modules/jobstores/mongodb.html
- **Código Atual:** `src/conductor-gateway/src/services/councilor_scheduler.py:48-52`
- **Migração Tasks:** `docs/sagas/saga-004/MIGRATION-COUNCILOR-EXECUTIONS-TO-TASKS.md`

---

## 🎯 Resumo Executivo

**Collection:** `apscheduler_jobs`

**Status:** ⚠️ **ÓRFÃ** - Não está sendo usada pelo código atual

**Motivo:** Sistema migrou de MongoDB jobstore para in-memory jobstore devido a incompatibilidade com objetos async

**Fonte de verdade atual:**
- **Jobs (config):** `agents` collection
- **Execuções (results):** `tasks` collection

**Recomendação:** 🗑️ **REMOVER** - Collection não é mais necessária

**Risco:** 🟢 **BAIXO** - Nenhum código depende dela

---

**Status:** ✅ ANÁLISE COMPLETA
**Última atualização:** 2025-10-25
**Ação recomendada:** Remover collection `apscheduler_jobs`
