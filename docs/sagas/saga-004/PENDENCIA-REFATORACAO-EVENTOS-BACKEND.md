# 📋 PENDÊNCIA: Refatoração de Eventos e Scheduler de Conselheiros

**Saga:** SAGA-004 - Sistema de Conselheiros
**Data:** 2025-10-25
**Status:** 🟡 PENDENTE
**Prioridade:** ALTA

---

## 🎯 Objetivo

Unificar e melhorar o sistema de execução e notificação de conselheiros, migrando de um modelo híbrido (frontend + backend) para um modelo centralizado no backend com eventos em tempo real.

---

## 🔍 Situação Atual

### **Problema Identificado**

Existem **DUAS implementações** de scheduler de conselheiros:

#### 1️⃣ **Frontend Scheduler** (Client-Side)
- **Arquivo:** `src/conductor-web/src/app/services/councilor-scheduler.service.ts`
- **Execução:** No navegador usando `setInterval()`
- **Persistência:** ❌ Não salva resultados
- **Notificações:** ✅ Eventos UI em tempo real
- **Problema:**
  - Só funciona com navegador aberto
  - Não sobrevive a refresh da página
  - Execuções não são rastreadas em `tasks`

#### 2️⃣ **Backend Scheduler** (Server-Side)
- **Arquivo:** `src/conductor-gateway/src/services/councilor_scheduler.py`
- **Execução:** No servidor usando APScheduler
- **Persistência:** ⚠️ Parcial (usa collection legacy)
- **Notificações:** ❌ Não notifica frontend em tempo real
- **Problema:**
  - ❌ Não usa `MongoTaskClient` (tasks collection)
  - ❌ Não calcula `severity`
  - ❌ Não emite eventos para o frontend

### **Eventos do Rodapé**

**Sistema Atual:**
```
Backend executa agente
    ↓
Salva em councilor_executions (legacy)
    ↓
Frontend polling de /api/agents/metrics (30s)
    ↓
GamificationEventsService deriva eventos localmente
    ↓
Mostra no rodapé
```

**Problemas:**
- ⏱️ Latência de até 30 segundos
- 🔄 Eventos são derivados, não diretos
- 📊 Dados indiretos (via metrics, não executions)
- ❌ Não usa tasks collection centralizada

---

## 💡 Solução Proposta

### **Arquitetura Target**

```
Backend Scheduler (APScheduler)
    ↓
MongoTaskClient.submit_task(is_councilor_execution=True)
    ↓
Task executada e salva em tasks collection
    ↓
CouncilorService calcula stats
    ↓
SSE stream notifica frontend em tempo real
    ↓
GamificationEventsService recebe eventos diretos
    ↓
Mostra no rodapé instantaneamente
```

### **Benefícios**

✅ **Execuções Persistentes**
- Sobrevivem a fechamento do navegador
- Histórico completo em `tasks`
- Rastreamento unificado

✅ **Eventos em Tempo Real**
- Server-Sent Events (SSE)
- Latência < 1 segundo
- Dados diretos do backend

✅ **Scheduler Profissional**
- APScheduler robusto
- Retry automático
- Logs centralizados

✅ **Centralização**
- Uma única fonte de verdade
- Menos código para manter
- Consistência garantida

---

## 🛠️ Plano de Implementação

### **Fase 1: Backend - Integração com tasks** (4-6 horas)

#### 1.1 Modificar `CouncilorBackendScheduler`

**Arquivo:** `src/conductor-gateway/src/services/councilor_scheduler.py`

**Mudanças:**
```python
from src.core.services.mongo_task_client import MongoTaskClient

class CouncilorBackendScheduler:
    def __init__(self):
        self.task_client = MongoTaskClient()
        self.scheduler = AsyncIOScheduler()
        # ...

    async def execute_task(self, councilor: dict):
        """Executa tarefa de conselheiro via tasks collection"""
        agent_id = councilor["agent_id"]
        config = councilor["councilor_config"]

        logger.info(f"🏛️ Executando conselheiro: {agent_id}")

        # 1. Submeter task
        task_id = self.task_client.submit_task(
            agent_id=agent_id,
            cwd=councilor.get("cwd", os.getcwd()),
            provider=councilor.get("provider", "claude"),
            prompt=config["task"]["prompt"],
            instance_id=f"councilor_{agent_id}_{int(time.time())}",
            is_councilor_execution=True,
            councilor_config={
                "title": config["title"],
                "task_name": config["task"]["name"]
            }
        )

        logger.info(f"📤 Task submetida: {task_id}")

        # 2. Aguardar resultado (polling)
        try:
            result = self.task_client.get_task_result(
                task_id,
                poll_interval=2.0,
                timeout=config.get("timeout", 600)
            )

            # 3. Analisar severity
            severity = self.task_client.analyze_severity(result["result"])
            self.task_client.update_task_severity(task_id, severity)

            logger.info(f"✅ Task concluída: {task_id} - Severity: {severity}")

            # 4. Stats são atualizados automaticamente por CouncilorService

            return {
                "success": True,
                "task_id": task_id,
                "severity": severity
            }

        except TimeoutError:
            logger.error(f"⏰ Timeout executando task {task_id}")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"❌ Erro executando task: {e}")
            return {"success": False, "error": str(e)}
```

**Checklist:**
- [ ] Importar `MongoTaskClient`
- [ ] Adicionar inicialização de `task_client`
- [ ] Refatorar `execute_task()` para usar `submit_task()`
- [ ] Implementar tratamento de timeout
- [ ] Adicionar logs detalhados
- [ ] Remover código legacy de `councilor_executions`

---

#### 1.2 Criar Endpoint SSE para Eventos

**Arquivo:** `src/conductor-gateway/src/api/routers/councilor.py`

**Novo endpoint:**
```python
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

@router.get("/events/stream")
async def stream_councilor_events(
    request: Request,
    service: CouncilorService = Depends(get_councilor_service)
):
    """
    Server-Sent Events stream para execuções de conselheiros em tempo real

    Stream format:
    event: councilor_execution
    data: {"execution_id": "...", "councilor_id": "...", "severity": "success", ...}

    event: councilor_started
    data: {"councilor_id": "...", "task_name": "..."}

    event: councilor_completed
    data: {"councilor_id": "...", "severity": "success", "duration_ms": 1234}
    """

    async def event_generator():
        last_execution_id = None

        while True:
            # Verificar se cliente desconectou
            if await request.is_disconnected():
                logger.info("🔌 Cliente desconectado do SSE stream")
                break

            try:
                # Buscar execuções recentes da tasks collection
                cursor = service.tasks_collection.find({
                    "is_councilor_execution": True
                }).sort("created_at", -1).limit(10)

                executions = await cursor.to_list(length=10)

                for exec_doc in executions:
                    exec_id = str(exec_doc["_id"])

                    # Enviar apenas novas execuções
                    if exec_id != last_execution_id:
                        # Mapear para formato do evento
                        event_data = {
                            "execution_id": exec_id,
                            "councilor_id": exec_doc["agent_id"],
                            "task_name": exec_doc.get("councilor_config", {}).get("task_name", "Unknown"),
                            "status": exec_doc["status"],
                            "severity": exec_doc.get("severity", "info"),
                            "started_at": exec_doc.get("created_at").isoformat() if exec_doc.get("created_at") else None,
                            "completed_at": exec_doc.get("completed_at").isoformat() if exec_doc.get("completed_at") else None,
                            "duration_ms": int(exec_doc.get("duration", 0) * 1000) if exec_doc.get("duration") else None
                        }

                        yield {
                            "event": "councilor_execution",
                            "data": json.dumps(event_data)
                        }

                        last_execution_id = exec_id

                # Heartbeat a cada 30s para manter conexão
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.utcnow().isoformat()})
                }

            except Exception as e:
                logger.error(f"❌ Erro no SSE stream: {e}")
                yield {
                    "event": "error",
                    "data": json.dumps({"error": str(e)})
                }

            # Poll a cada 5 segundos
            await asyncio.sleep(5)

    return EventSourceResponse(event_generator())
```

**Dependências necessárias:**
```bash
pip install sse-starlette
```

**Checklist:**
- [ ] Instalar `sse-starlette`
- [ ] Criar endpoint `/events/stream`
- [ ] Implementar event generator
- [ ] Adicionar heartbeat para manter conexão
- [ ] Testar com `curl -N http://localhost:8000/api/councilors/events/stream`

---

### **Fase 2: Frontend - Consumir SSE** (2-3 horas)

#### 2.1 Atualizar `GamificationEventsService`

**Arquivo:** `src/conductor-web/src/app/services/gamification-events.service.ts`

**Adicionar método SSE:**
```typescript
private eventSource?: EventSource;

/**
 * Conecta ao stream SSE de eventos de conselheiros
 */
connectToCouncilorEvents(): void {
  if (this.eventSource) {
    this.eventSource.close();
  }

  console.log('🔌 Conectando ao SSE stream de conselheiros...');

  this.eventSource = new EventSource('/api/councilors/events/stream');

  this.eventSource.addEventListener('councilor_execution', (event) => {
    const execution = JSON.parse(event.data);

    console.log('📨 Evento de execução recebido:', execution);

    // Criar evento de gamificação
    const emoji = this.getSeverityEmoji(execution.severity);
    const title = `${emoji} ${execution.task_name} - ${this.getSeverityLabel(execution.severity)}`;

    this.pushEvent({
      id: execution.execution_id,
      title: title,
      severity: execution.severity as GamificationSeverity,
      timestamp: Date.now(),
      meta: {
        councilorId: execution.councilor_id,
        executionId: execution.execution_id,
        taskName: execution.task_name,
        durationMs: execution.duration_ms
      },
      category: execution.severity === 'error' ? 'critical' : 'analysis'
    });
  });

  this.eventSource.addEventListener('heartbeat', () => {
    console.log('💓 SSE heartbeat');
  });

  this.eventSource.addEventListener('error', (error) => {
    console.error('❌ Erro no SSE stream:', error);

    // Reconectar após 5 segundos
    setTimeout(() => {
      console.log('🔄 Reconectando ao SSE stream...');
      this.connectToCouncilorEvents();
    }, 5000);
  });

  this.eventSource.onopen = () => {
    console.log('✅ SSE stream conectado');
  };
}

private getSeverityEmoji(severity: string): string {
  switch (severity) {
    case 'error': return '🔥';
    case 'warning': return '⚠️';
    case 'success': return '✅';
    default: return 'ℹ️';
  }
}

private getSeverityLabel(severity: string): string {
  switch (severity) {
    case 'error': return 'Erro';
    case 'warning': return 'Alerta';
    case 'success': return 'Sucesso';
    default: return 'Info';
  }
}

/**
 * Desconecta do SSE stream
 */
disconnectFromCouncilorEvents(): void {
  if (this.eventSource) {
    this.eventSource.close();
    this.eventSource = undefined;
    console.log('🔌 SSE stream desconectado');
  }
}
```

**No constructor, iniciar conexão:**
```typescript
constructor(
  private readonly metricsService: AgentMetricsService,
  private readonly personalization: AgentPersonalizationService,
) {
  // Código existente...

  // 🆕 Conectar ao SSE stream
  this.connectToCouncilorEvents();
}
```

**Checklist:**
- [ ] Adicionar método `connectToCouncilorEvents()`
- [ ] Implementar handlers de eventos SSE
- [ ] Adicionar reconexão automática
- [ ] Adicionar método `disconnectFromCouncilorEvents()`
- [ ] Chamar `connectToCouncilorEvents()` no constructor

---

#### 2.2 Simplificar `CouncilorSchedulerService` (Opcional)

**Opção A: Remover scheduler frontend completamente**
- Remove `scheduleTask()`, `executeTask()`, etc.
- Mantém apenas `getActiveCouncilors()` para visualização
- Backend fica responsável por 100% das execuções

**Opção B: Manter como fallback**
- Adicionar flag `enable_frontend_scheduler` (default: false)
- Usar apenas em desenvolvimento
- Produção usa apenas backend

**Recomendação:** **Opção A** para simplificar

**Checklist:**
- [ ] Decidir entre Opção A ou B
- [ ] Se Opção A: remover código de scheduling
- [ ] Se Opção B: adicionar flag de configuração
- [ ] Atualizar documentação

---

### **Fase 3: Testing e Validação** (2-3 horas)

#### 3.1 Testes Backend

**Cenários:**
1. ✅ Scheduler inicia e carrega conselheiros
2. ✅ Task é submetida com `is_councilor_execution=True`
3. ✅ Task é executada e resultado salvo em `tasks`
4. ✅ Severity é calculada corretamente
5. ✅ Stats do agente são atualizados
6. ✅ SSE stream emite eventos

**Comandos:**
```bash
# 1. Iniciar backend
cd src/conductor-gateway
python -m uvicorn src.api.app:app --reload

# 2. Monitorar logs
tail -f logs/councilor_scheduler.log

# 3. Testar SSE stream
curl -N http://localhost:8000/api/councilors/events/stream

# 4. Verificar tasks no MongoDB
mongosh
> use conductor_state
> db.tasks.find({"is_councilor_execution": true}).sort({created_at: -1}).limit(5).pretty()
```

**Checklist:**
- [ ] Backend scheduler inicializa sem erros
- [ ] Tasks são criadas em `tasks` collection
- [ ] Severity é calculada
- [ ] Stats são atualizados
- [ ] SSE stream funciona

---

#### 3.2 Testes Frontend

**Cenários:**
1. ✅ SSE conecta ao iniciar aplicação
2. ✅ Eventos aparecem no rodapé em tempo real
3. ✅ Reconexão funciona após perda de conexão
4. ✅ Dashboard mostra execuções recentes
5. ✅ KPIs são atualizados

**Comandos:**
```bash
# 1. Iniciar frontend
cd src/conductor-web
npm start

# 2. Abrir DevTools e verificar:
# - Console: mensagens de SSE
# - Network: conexão SSE ativa
# - Application: EventSource em uso
```

**Checklist:**
- [ ] SSE conecta automaticamente
- [ ] Eventos aparecem no rodapé < 5s após execução
- [ ] Reconexão funciona
- [ ] Dashboard mostra dados corretos
- [ ] Sem erros no console

---

### **Fase 4: Documentação e Cleanup** (1-2 horas)

#### 4.1 Atualizar Documentação

**Arquivos:**
- [ ] `CENTRALIZACAO_EXECUCOES.md` - Adicionar seção sobre SSE
- [ ] `IMPLEMENTACAO-CONSELHEIROS.md` - Atualizar fluxo de execução
- [ ] `README.md` - Adicionar nota sobre eventos em tempo real

#### 4.2 Remover Código Legacy

**Arquivos a limpar:**
- [ ] Remover métodos de scheduling de `councilor-scheduler.service.ts` (se Opção A)
- [ ] Adicionar comentários de deprecation em código legacy
- [ ] Atualizar testes unitários

---

## 📊 Métricas de Sucesso

### **Performance**
- ⏱️ Latência de eventos: < 5 segundos (vs 30s atual)
- 💾 Persistência: 100% das execuções em `tasks`
- 🔄 Uptime do scheduler: > 99%

### **Funcionalidade**
- ✅ Execuções sobrevivem a fechamento do navegador
- ✅ Eventos em tempo real no rodapé
- ✅ Dashboard mostra dados precisos
- ✅ Stats atualizados automaticamente

### **Código**
- 📉 Redução de código: ~30% (remoção de scheduler frontend)
- 🎯 Centralização: 1 fonte de verdade (tasks)
- 🧹 Cleanup: 0 referências a `councilor_executions`

---

## ⚠️ Riscos e Mitigações

### **Risco 1: SSE pode desconectar**
**Mitigação:**
- Implementar reconexão automática
- Manter polling de fallback a cada 30s
- Adicionar heartbeat no stream

### **Risco 2: Overhead de SSE em múltiplos clientes**
**Mitigação:**
- Usar Redis Pub/Sub para escalar
- Implementar rate limiting
- Adicionar cache de eventos

### **Risco 3: Breaking changes para usuários**
**Mitigação:**
- Manter compatibilidade com API existente
- Fazer deploy gradual (feature flag)
- Comunicar mudanças claramente

---

## 🎯 Próximos Passos

1. ✅ **Aprovar plano** - Review com time
2. 🟡 **Implementar Fase 1** - Backend + SSE
3. 🟡 **Implementar Fase 2** - Frontend
4. 🟡 **Testing completo** - QA
5. 🟡 **Deploy em staging** - Validação
6. 🟡 **Deploy em produção** - Rollout gradual

---

## 📚 Referências

- **Análise original:** `/docs/CENTRALIZACAO_EXECUCOES.md`
- **Implementação atual:**
  - Backend: `src/conductor-gateway/src/services/councilor_scheduler.py`
  - Frontend: `src/conductor-web/src/app/services/councilor-scheduler.service.ts`
- **SSE Documentation:** https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- **APScheduler:** https://apscheduler.readthedocs.io/

---

## 👥 Responsáveis

**Backend:**
- Integração com MongoTaskClient
- Implementação de SSE endpoint
- Testes de scheduler

**Frontend:**
- Consumo de SSE
- Atualização de eventos
- Testes de UI

**DevOps:**
- Deploy de SSE em produção
- Monitoramento de performance
- Escalabilidade

---

**Status:** 🟡 PENDENTE
**Última atualização:** 2025-10-25
**Próxima revisão:** A ser agendada
