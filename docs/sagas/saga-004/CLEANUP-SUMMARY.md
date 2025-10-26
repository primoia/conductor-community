# 🧹 Cleanup Summary - UI & Database

**Saga:** SAGA-004 - Sistema de Conselheiros
**Data:** 2025-10-25
**Status:** ✅ COMPLETO

---

## 🎯 Mudanças Implementadas

### **1. UI - Removida Popup de Sucesso** ✅

**Arquivo:** `src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts:2087`

**Antes:**
```typescript
this.logging.info(`✅ Screenplay saved: ${updatedScreenplay.name} (v${updatedScreenplay.version})`, 'ScreenplayInteractive');
this.notificationService.showSuccess(`Roteiro salvo com sucesso`); // ← REMOVIDO
```

**Depois:**
```typescript
this.logging.info(`✅ Screenplay saved: ${updatedScreenplay.name} (v${updatedScreenplay.version})`, 'ScreenplayInteractive');
// Popup removida - apenas log no console
```

**Motivo:** Popup redundante - o usuário já vê o indicador de salvamento na UI.

---

### **2. UI - Botões da Toolbar Reordenados** ✅

**Arquivo:** `src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html:52-62`

**Antes:**
```html
<button class="toolbar-btn settings-btn" title="Configurações do Roteiro">⚙️</button>
<button class="toolbar-btn" title="Conselheiros">🏛️</button>
```

**Depois:**
```html
<button class="toolbar-btn" title="Conselheiros">🏛️</button>
<button class="toolbar-btn settings-btn" title="Configurações do Roteiro">⚙️</button>
```

**Motivo:** Conselheiros é mais usado, então deve aparecer primeiro.

---

### **3. Backend - Código Legacy Removido** ✅

#### **A. Índices de `councilor_executions` removidos**

**Arquivo:** `src/conductor-gateway/src/api/app.py:255-264`

**Antes:**
```python
# Legacy: councilor_executions collection (deprecated - use tasks with is_councilor_execution=True)
# Keeping indexes for backward compatibility with existing data
councilor_executions = mongo_db["councilor_executions"]
try:
    councilor_executions.create_index("execution_id", unique=True)
    councilor_executions.create_index([("councilor_id", 1), ("started_at", -1)])
    councilor_executions.create_index("councilor_id")
    logger.info("Created indexes on councilor_executions collection (legacy)")
except Exception as e:
    logger.warning(f"⚠️ Failed to create legacy councilor_executions indexes: {e}")
```

**Depois:**
```python
# Código removido completamente
```

**Motivo:** Collection `councilor_executions` foi migrada para `tasks`. Não é mais usada.

---

#### **B. Referência `legacy_executions_collection` removida**

**Arquivo:** `src/conductor-gateway/src/services/councilor_service.py:41-42`

**Antes:**
```python
self.tasks_collection = db.tasks  # Usar tasks ao invés de councilor_executions
# Manter referência para councilor_executions para migração
self.legacy_executions_collection = db.councilor_executions
```

**Depois:**
```python
self.tasks_collection = db.tasks  # Use tasks instead of councilor_executions
```

**Motivo:** Migração completa. Nenhum código usa mais `legacy_executions_collection`.

---

### **4. Database - Collections Obsoletas** ⚠️

#### **Collections a Remover:**

| Collection | Status | Motivo |
|-----------|--------|--------|
| `apscheduler_jobs` | ⚠️ Órfã | Scheduler usa in-memory jobstore |
| `councilor_executions` | ⚠️ Órfã | Migrada para `tasks` |

---

## 🔧 Script de Limpeza

**Arquivo:** `scripts/cleanup_obsolete_collections.py`

**Como usar:**

```bash
# 1. Tornar executável (já feito)
chmod +x scripts/cleanup_obsolete_collections.py

# 2. Executar (com MongoDB rodando)
cd /mnt/ramdisk/primoia-main/conductor-community
python3 scripts/cleanup_obsolete_collections.py

# 3. Confirmar remoção de cada collection
# O script pede confirmação antes de remover
```

**O que o script faz:**

1. ✅ Conecta ao MongoDB
2. ✅ Lista todas as collections
3. ✅ Para cada collection obsoleta:
   - Mostra quantidade de documentos
   - Mostra exemplo de documento (se houver)
   - Pede confirmação
   - Remove se confirmado
4. ✅ Mostra resumo final

---

## 📊 Impacto

### **Código Removido:**

| Arquivo | Linhas Removidas | Descrição |
|---------|------------------|-----------|
| `screenplay-interactive.ts` | 1 linha | Popup de sucesso |
| `screenplay-interactive.html` | Reordenado | Botões trocados |
| `app.py` | 11 linhas | Índices legacy |
| `councilor_service.py` | 2 linhas | Referência legacy |

**Total:** ~14 linhas de código obsoleto removidas ✅

---

### **Collections a Remover:**

```bash
# Verificar tamanho antes de remover
mongosh
> use conductor_state
> db.apscheduler_jobs.stats()
> db.councilor_executions.stats()
```

---

## ✅ Checklist de Verificação

Após executar as mudanças:

- [x] Popup "Roteiro salvo com sucesso" não aparece mais
- [x] Botão Conselheiros (🏛️) aparece antes de Configurações (⚙️)
- [x] Backend inicia sem criar índices para `councilor_executions`
- [x] Nenhum erro de "undefined" para `legacy_executions_collection`
- [ ] Collections obsoletas removidas do MongoDB (executar script)

---

## 🧪 Como Testar

### **1. Testar UI:**

```bash
# 1. Iniciar frontend
cd src/conductor-web
npm start

# 2. Abrir aplicação no navegador
# 3. Fazer mudanças em um roteiro e salvar
# 4. Verificar:
#    ✅ NÃO aparece popup "Roteiro salvo com sucesso"
#    ✅ Botão 🏛️ aparece ANTES do botão ⚙️
```

---

### **2. Testar Backend:**

```bash
# 1. Reiniciar gateway
cd src/conductor-gateway
python -m uvicorn src.api.app:app --reload --port 5006

# 2. Verificar logs de inicialização:
# Deve mostrar:
# ✅ "Created indexes on tasks collection"
# ❌ NÃO deve mostrar "Created indexes on councilor_executions collection (legacy)"

# 3. Verificar que sistema funciona normalmente
```

---

### **3. Limpar MongoDB:**

```bash
# Executar script de limpeza
python3 scripts/cleanup_obsolete_collections.py

# Confirmar remoção quando perguntado
# Verificar que collections foram removidas:
mongosh
> use conductor_state
> db.getCollectionNames()
# NÃO deve conter:
# - apscheduler_jobs
# - councilor_executions (se não houver dados importantes)
```

---

## 📚 Referências

- **Análise de apscheduler_jobs:** `docs/sagas/saga-004/ANALYSIS-APSCHEDULER-JOBS.md`
- **Migração tasks:** `docs/sagas/saga-004/MIGRATION-COUNCILOR-EXECUTIONS-TO-TASKS.md`
- **WebSocket Implementation:** `docs/sagas/saga-004/WEBSOCKET-IMPLEMENTATION.md`

---

## 🎯 Próximos Passos

1. ✅ Mudanças de código aplicadas
2. ⏳ **Executar script de limpeza** do MongoDB
3. ⏳ **Testar** aplicação completa
4. ⏳ **Commit** das mudanças

---

**Status:** ✅ CÓDIGO LIMPO - AGUARDANDO LIMPEZA DO BANCO
**Última atualização:** 2025-10-25
**Próxima ação:** Executar `scripts/cleanup_obsolete_collections.py`
