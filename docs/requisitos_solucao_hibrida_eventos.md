# Análise de Viabilidade: Solução Híbrida de Eventos
## Histórico via MongoDB Tasks + Tempo Real via WebSocket

## 📋 Visão Geral

Este documento analisa a **viabilidade técnica** de implementar uma solução híbrida para resolver o problema de perda de dados no editor-footer ao recarregar a página. A proposta combina:

1. **Carga inicial de histórico**: Buscar últimas N execuções da coleção `tasks` do MongoDB ao inicializar página
2. **Atualizações em tempo real**: Receber novos eventos via WebSocket conforme agentes executam
3. **Deduplicação inteligente**: Evitar eventos duplicados entre histórico e real-time

---

## 🎯 Problema a Resolver

**Situação Atual**:
- Eventos de gamificação são armazenados APENAS em memória (BehaviorSubject)
- Ao dar reload (F5), todos os eventos são perdidos
- Usuário perde contexto visual de execuções recentes

**Proposta do Usuário**:
> "Se ao dar reload na página, fosse trazido em forma de lista uma quantidade X de eventos da coleção task, então adicionados com sockets para eventos novos?"

**Resposta**: ✅ **TOTALMENTE VIÁVEL** - A infraestrutura já existe!

---

## 🏗️ Infraestrutura Existente

### 1. Coleção `tasks` do MongoDB

**Banco de dados**: `conductor_state`
**Coleção**: `tasks`
**Localização**: `mongo_task_client.py:65-84`

**Estrutura do Documento**:

```python
{
    # Identificação
    "_id": ObjectId,                    # ID único do MongoDB
    "task_id": str,                     # ID da execução (ex: "exec_quality_agent_1730000000000")
    "agent_id": str,                    # ID do agente
    "instance_id": str,                 # ID da instância para isolamento

    # Execução
    "provider": str,                    # "claude", "gemini", etc.
    "prompt": str,                      # Prompt XML completo
    "cwd": str,                         # Diretório de trabalho
    "timeout": int,                     # Timeout em segundos

    # Status e Timestamps
    "status": str,                      # "pending" | "processing" | "completed" | "error"
    "created_at": datetime,             # ⭐ Timestamp de criação (INDEXADO)
    "updated_at": datetime,             # Última atualização
    "started_at": datetime,             # Início da execução
    "completed_at": datetime,           # ⭐ Fim da execução (INDEXADO)

    # Resultados
    "result": str,                      # Output do agente
    "exit_code": int,                   # Código de saída
    "duration": float,                  # ⭐ Duração em segundos
    "error": str,                       # Mensagem de erro (se houver)

    # Conselheiros (Gamificação)
    "is_councilor_execution": bool,     # ⭐ Flag para identificar conselheiros (INDEXADO)
    "severity": str,                    # ⭐ "success" | "warning" | "error" (INDEXADO)
    "councilor_config": {               # Configuração específica de conselheiro
        "task_name": str,               # Nome da tarefa
        "display_name": str             # Nome de exibição (ex: "Dra. Testa")
    }
}
```

**Indexes Relevantes** (`app.py:241-257`):
- `(agent_id, created_at)`: Para queries por agente específico
- `(is_councilor_execution, created_at)`: Para filtrar conselheiros
- `severity`: Para filtrar por severidade

---

### 2. Endpoints REST Existentes

#### A. `GET /api/tasks` (`app.py:1644-1711`)

**Funcionalidade Completa**:

```http
GET /api/tasks?status=completed&limit=50&sort=-completed_at
```

**Parâmetros**:
- `status`: `"processing"` | `"completed"` | `"error"` (opcional, aceita múltiplos)
- `agent_id`: Filtrar por agente específico (opcional)
- `limit`: Quantidade máxima (1-500, padrão 100)
- `offset`: Paginação (padrão 0)
- `sort`: Campo de ordenação (prefixo `-` para decrescente, padrão `-created_at`)

**Resposta**:
```json
{
    "success": true,
    "count": 50,
    "total": 1234,
    "tasks": [
        {
            "_id": "673a1234567890abcdef1234",
            "task_id": "exec_quality_agent_1730000000000",
            "agent_id": "quality_agent",
            "status": "completed",
            "created_at": "2025-11-05T10:30:00Z",
            "completed_at": "2025-11-05T10:30:03Z",
            "duration": 3.45,
            "result": "Análise de qualidade concluída...",
            "is_councilor_execution": false
        }
        // ... mais 49 tasks
    ]
}
```

**Exemplo de Query para Carregar Histórico**:
```typescript
// Buscar últimas 50 execuções concluídas/com erro
const response = await fetch(
    '/api/tasks?status=completed&status=error&limit=50&sort=-completed_at'
);
const { tasks } = await response.json();
```

---

#### B. `GET /api/tasks/processing` (`app.py:1713-1773`)

**Funcionalidade**: Atalho para `GET /api/tasks?status=processing`

**Uso**: Monitorar execuções em andamento

---

### 3. Sistema WebSocket para Tempo Real

#### A. Endpoint WebSocket (`app.py:600-670`)

**Conexão**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/gamification');
```

**Manager**: `GamificationConnectionManager` (`websocket.py:20-131`)

**Fluxo de Conexão**:
1. Cliente conecta ao WebSocket
2. Recebe `client_id` único
3. Pode subscrever a tipos específicos de eventos (padrão: `"all"`)
4. Recebe eventos em tempo real conforme ocorrem

---

#### B. Eventos Emitidos

**1. Eventos de Agente Regular** (`app.py:802-856`):

```json
// Início da execução
{
    "type": "agent_execution_started",
    "data": {
        "agent_id": "quality_agent",
        "agent_name": "Quality Analyzer",
        "agent_emoji": "🔍",
        "instance_id": "instance-123",
        "execution_id": "exec_quality_agent_1730000000000",
        "started_at": "2025-11-05T10:30:00",
        "level": "debug"
    },
    "timestamp": 1730000000.123
}

// Conclusão da execução
{
    "type": "agent_execution_completed",
    "data": {
        "agent_id": "quality_agent",
        "agent_name": "Quality Analyzer",
        "agent_emoji": "🔍",
        "execution_id": "exec_quality_agent_1730000000000",
        "status": "completed",
        "started_at": "2025-11-05T10:30:00",
        "completed_at": "2025-11-05T10:30:03",
        "duration_ms": 3450
    },
    "timestamp": 1730000003.123
}
```

**2. Eventos de Conselheiro** (`councilor_scheduler.py:212-282`):

```json
// Início
{
    "type": "councilor_started",
    "data": {
        "councilor_id": "quality_councilor",
        "task_name": "Verificar Cobertura de Testes",
        "display_name": "Dra. Testa",
        "execution_id": "exec_quality_councilor_1730000000000",
        "started_at": "2025-11-05T10:30:00"
    },
    "timestamp": 1730000000.123
}

// Conclusão com sucesso
{
    "type": "councilor_completed",
    "data": {
        "councilor_id": "quality_councilor",
        "task_name": "Verificar Cobertura de Testes",
        "display_name": "Dra. Testa",
        "execution_id": "exec_quality_councilor_1730000000000",
        "status": "completed",
        "severity": "warning",  // ⭐ Analisado do resultado
        "started_at": "2025-11-05T10:30:00",
        "completed_at": "2025-11-05T10:30:03",
        "duration_ms": 3450
    },
    "timestamp": 1730000003.123
}

// Conclusão com erro
{
    "type": "councilor_error",
    "data": {
        "councilor_id": "quality_councilor",
        "task_name": "Verificar Cobertura de Testes",
        "display_name": "Dra. Testa",
        "execution_id": "exec_quality_councilor_1730000000000",
        "status": "error",
        "severity": "error",
        "error_message": "Falha ao executar análise...",
        "started_at": "2025-11-05T10:30:00",
        "completed_at": "2025-11-05T10:30:03",
        "duration_ms": 3450
    },
    "timestamp": 1730000003.123
}
```

---

### 4. Serviço de Conselheiros

**Localização**: `councilor_service.py:357-496`

**Método Relevante**: `get_executions(councilor_id, limit)` (linhas 357-404)

```python
async def get_executions(
    self,
    councilor_id: str,
    limit: Optional[int] = 10
) -> List[Dict]:
    """
    Busca execuções recentes de um conselheiro específico.

    Faz query na coleção tasks com:
    - Filtro: agent_id = councilor_id AND is_councilor_execution = True
    - Ordenação: created_at descendente
    - Limite: N mais recentes
    """
    pass
```

**Transformação de Dados** (linhas 378-392):

```python
# Mapeia documento de task para formato de execução
{
    "execution_id": task["_id"],
    "councilor_id": task["agent_id"],
    "started_at": task["created_at"],
    "completed_at": task["completed_at"],
    "status": task["status"],
    "severity": task["severity"],  # ⭐ Já analisado e armazenado
    "output": task["result"],
    "error": task["result"] if status == "error" else None,
    "duration_ms": int(task["duration"] * 1000)
}
```

---

## 🔄 Proposta de Implementação

### Arquitetura da Solução Híbrida

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Angular)                        │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ GamificationEventsService                            │    │
│  │                                                       │    │
│  │  ┌─────────────────┐  ┌─────────────────┐          │    │
│  │  │ Histórico       │  │ Real-Time       │          │    │
│  │  │ (REST API)      │  │ (WebSocket)     │          │    │
│  │  └────────┬────────┘  └────────┬────────┘          │    │
│  │           │                     │                    │    │
│  │           ├─────────────────────┤                    │    │
│  │           ▼                     ▼                    │    │
│  │  ┌──────────────────────────────────────┐           │    │
│  │  │ eventsSubject (BehaviorSubject)      │           │    │
│  │  │                                       │           │    │
│  │  │ - Merge de eventos históricos e RT   │           │    │
│  │  │ - Deduplicação por execution_id      │           │    │
│  │  │ - Ordenação por timestamp            │           │    │
│  │  │ - Limite de 50 eventos em memória    │           │    │
│  │  └──────────────────────────────────────┘           │    │
│  │           │                                          │    │
│  │           ▼                                          │    │
│  │  ┌──────────────────────────────────────┐           │    │
│  │  │ events$ (Observable)                 │           │    │
│  │  └──────────────────────────────────────┘           │    │
│  └────────────────────┬────────────────────────────────┘    │
│                       │                                      │
│                       ▼                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ EventTickerComponent                                 │    │
│  │ - Exibe eventos no footer                           │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                        ▲            ▲
                        │            │
        ┌───────────────┘            └───────────────┐
        │                                             │
        │ REST                                   WebSocket
        │                                             │
┌───────┴──────────────────────────────────────────┴──────────┐
│              BACKEND (FastAPI + MongoDB)                     │
│                                                               │
│  ┌─────────────────────────┐  ┌──────────────────────────┐  │
│  │ GET /api/tasks/events   │  │ WS /ws/gamification      │  │
│  │ (Novo endpoint)         │  │ (Já existe)              │  │
│  │                         │  │                          │  │
│  │ - Query últimas N tasks │  │ - Emite eventos em RT    │  │
│  │ - Transforma para       │  │ - Broadcast para clientes│  │
│  │   formato de evento     │  │                          │  │
│  └────────┬────────────────┘  └──────────┬───────────────┘  │
│           │                               │                  │
│           ▼                               ▼                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MongoDB: conductor_state.tasks                       │   │
│  │                                                       │   │
│  │ - Persistência permanente                            │   │
│  │ - Indexes para queries eficientes                    │   │
│  │ - Severity já analisada (conselheiros)               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

### Fase 1: Backend - Criar Endpoint de Histórico

**Arquivo**: `conductor-gateway/src/api/app.py`

**Novo Endpoint**:

```python
@app.get("/api/tasks/events")
async def get_task_events(
    limit: int = Query(50, ge=1, le=200, description="Quantidade de eventos"),
    since: Optional[datetime] = Query(None, description="Data/hora inicial (UTC)"),
    until: Optional[datetime] = Query(None, description="Data/hora final (UTC)"),
    agent_id: Optional[str] = Query(None, description="Filtrar por agente"),
    include_processing: bool = Query(False, description="Incluir tarefas em processamento")
):
    """
    Retorna histórico de execuções formatado como eventos de gamificação.

    Utilizado para carregar eventos históricos ao inicializar a página,
    permitindo que o usuário veja o que aconteceu antes do reload.

    Retorna eventos no mesmo formato que o WebSocket /ws/gamification,
    garantindo compatibilidade com o frontend.
    """
    try:
        # Construir filtro de query
        query_filter = {}

        # Filtrar status (excluir "pending", incluir "processing" se solicitado)
        if include_processing:
            query_filter["status"] = {"$in": ["processing", "completed", "error"]}
        else:
            query_filter["status"] = {"$in": ["completed", "error"]}

        # Filtrar por data (se especificado)
        if since or until:
            date_filter = {}
            if since:
                date_filter["$gte"] = since
            if until:
                date_filter["$lte"] = until
            query_filter["completed_at"] = date_filter

        # Filtrar por agente (se especificado)
        if agent_id:
            query_filter["agent_id"] = agent_id

        # Buscar tasks do MongoDB
        tasks_cursor = mongo_task_client.tasks_collection.find(query_filter)\
            .sort("completed_at", -1)\
            .limit(limit)

        tasks = await tasks_cursor.to_list(length=limit)

        # Transformar tasks em eventos de gamificação
        events = []
        for task in tasks:
            # Obter metadados do agente (emoji, nome)
            agent = await mongo_client.agents.find_one({"_id": task["agent_id"]})
            agent_name = agent.get("name", task["agent_id"]) if agent else task["agent_id"]
            agent_emoji = agent.get("emoji", "🤖") if agent else "🤖"

            # Identificar se é conselheiro
            is_councilor = task.get("is_councilor_execution", False)

            # Montar estrutura de evento
            if is_councilor:
                # Evento de conselheiro (mais rico em informações)
                event_type = "councilor_completed" if task["status"] == "completed" else "councilor_error"
                councilor_config = task.get("councilor_config", {})

                event = {
                    "type": event_type,
                    "data": {
                        "councilor_id": task["agent_id"],
                        "task_name": councilor_config.get("task_name", "Tarefa do Conselheiro"),
                        "display_name": councilor_config.get("display_name", agent_name),
                        "execution_id": task.get("task_id") or str(task["_id"]),
                        "status": task["status"],
                        "severity": task.get("severity", "success"),
                        "started_at": task["created_at"].isoformat() if task.get("created_at") else None,
                        "completed_at": task["completed_at"].isoformat() if task.get("completed_at") else None,
                        "duration_ms": int(task["duration"] * 1000) if task.get("duration") else None,
                        "summary": task.get("result", "")[:200] if task.get("result") else None
                    },
                    "timestamp": task["completed_at"].timestamp() if task.get("completed_at") else time.time()
                }

                # Adicionar erro se houver
                if task["status"] == "error":
                    event["data"]["error_message"] = task.get("error") or task.get("result", "Erro desconhecido")

            else:
                # Evento de agente regular
                event_type = "agent_execution_completed"

                event = {
                    "type": event_type,
                    "data": {
                        "agent_id": task["agent_id"],
                        "agent_name": agent_name,
                        "agent_emoji": agent_emoji,
                        "execution_id": task.get("task_id") or str(task["_id"]),
                        "status": task["status"],
                        "started_at": task["created_at"].isoformat() if task.get("created_at") else None,
                        "completed_at": task["completed_at"].isoformat() if task.get("completed_at") else None,
                        "duration_ms": int(task["duration"] * 1000) if task.get("duration") else None,
                        "level": "debug"  # Eventos regulares são nível debug
                    },
                    "timestamp": task["completed_at"].timestamp() if task.get("completed_at") else time.time()
                }

            events.append(event)

        return {
            "success": True,
            "events": events,
            "count": len(events)
        }

    except Exception as e:
        logger.error(f"Erro ao buscar eventos históricos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar eventos: {str(e)}")
```

**Exemplo de Uso**:

```bash
# Últimas 50 execuções
GET /api/tasks/events?limit=50

# Execuções das últimas 24 horas
GET /api/tasks/events?since=2025-11-04T10:00:00Z&limit=100

# Execuções de um agente específico
GET /api/tasks/events?agent_id=quality_agent&limit=20

# Incluir execuções em andamento
GET /api/tasks/events?include_processing=true&limit=30
```

---

### Fase 2: Frontend - Modificar GamificationEventsService

**Arquivo**: `conductor-web/src/app/services/gamification-events.service.ts`

**Mudanças Necessárias**:

#### A. Adicionar Método de Carregamento Histórico

```typescript
// Adicionar após linha 100 (aproximadamente)

/**
 * Carrega eventos históricos do backend ao inicializar o serviço.
 * Chamado automaticamente no ngOnInit ou manualmente após reload.
 */
private async loadHistoricalEvents(): Promise<void> {
  try {
    // Verificar se já carregou nesta sessão (evitar duplicatas em navegação interna)
    const sessionKey = 'gamification_events_loaded';
    if (sessionStorage.getItem(sessionKey) === 'true') {
      console.log('[GamificationEvents] Histórico já carregado nesta sessão, pulando...');
      return;
    }

    console.log('[GamificationEvents] Carregando eventos históricos...');

    // Buscar últimas 50 execuções do backend
    const response = await fetch('/api/tasks/events?limit=50');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const historicalEvents: GamificationEvent[] = data.events || [];

    console.log(`[GamificationEvents] ${historicalEvents.length} eventos históricos recuperados`);

    // Adicionar eventos históricos ao subject (em ordem cronológica reversa)
    // Eles já vêm ordenados do backend (mais recente primeiro)
    const currentEvents = this.eventsSubject.value;

    // Mesclar, removendo duplicatas por execution_id
    const mergedEvents = this.deduplicateEvents([...historicalEvents, ...currentEvents]);

    // Limitar ao máximo de eventos
    const boundedEvents = mergedEvents.length > this.maxEvents
      ? mergedEvents.slice(mergedEvents.length - this.maxEvents)
      : mergedEvents;

    // Atualizar subject
    this.eventsSubject.next(boundedEvents);

    // Marcar como carregado na sessão
    sessionStorage.setItem(sessionKey, 'true');

    console.log(`[GamificationEvents] Estado final: ${boundedEvents.length} eventos no histórico`);

  } catch (error) {
    console.error('[GamificationEvents] Erro ao carregar histórico:', error);
    // Não bloquear aplicação se histórico falhar
    // WebSocket ainda funcionará normalmente para novos eventos
  }
}

/**
 * Remove eventos duplicados com base no execution_id.
 * Mantém sempre a versão mais recente (com mais informações).
 */
private deduplicateEvents(events: GamificationEvent[]): GamificationEvent[] {
  const seen = new Map<string, GamificationEvent>();

  for (const event of events) {
    const executionId = event.data.execution_id;

    if (!executionId) {
      // Evento sem ID, manter (pode ser erro ou evento especial)
      seen.set(`fallback_${event.timestamp}`, event);
      continue;
    }

    const existing = seen.get(executionId);

    if (!existing) {
      // Primeiro evento com esse ID
      seen.set(executionId, event);
    } else {
      // Já existe, manter o mais completo (completed > started)
      if (event.type.includes('completed') || event.type.includes('error')) {
        seen.set(executionId, event); // Substituir por versão finalizada
      }
      // Se já existe completed e chegou started, ignorar started
    }
  }

  // Retornar eventos únicos, ordenados por timestamp
  return Array.from(seen.values()).sort((a, b) => a.timestamp - b.timestamp);
}
```

#### B. Modificar Constructor para Carregar Histórico

```typescript
// Modificar constructor (aproximadamente linha 40)

constructor(
  private agentMetricsService: AgentMetricsService,
  private agentPersonalizationService: AgentPersonalizationService,
  private websocketService: GamificationWebSocketService
) {
  // 1. Conectar WebSocket para eventos em tempo real
  this.websocketService.connect();

  // 2. Inscrever-se em eventos WebSocket
  this.websocketService.events$.subscribe({
    next: (event) => this.handleWebSocketEvent(event),
    error: (err) => console.error('[GamificationEvents] WebSocket error:', err)
  });

  // 3. Carregar eventos históricos do MongoDB (NOVO)
  this.loadHistoricalEvents().catch(err => {
    console.error('[GamificationEvents] Falha ao carregar histórico:', err);
  });

  // 4. Fallback: derivar eventos de métricas se WebSocket falhar (mantido)
  this.agentMetricsService.metrics$
    .pipe(
      filter(() => !this.websocketService.isConnected()),
      debounceTime(1000)
    )
    .subscribe({
      next: (metrics) => this.deriveExecutionEvents(metrics),
      error: (err) => console.error('[GamificationEvents] Metrics error:', err)
    });
}
```

#### C. Modificar `pushEvent` para Evitar Duplicatas

```typescript
// Modificar método pushEvent (aproximadamente linha 67)

pushEvent(event: GamificationEvent): void {
  const currentList = this.eventsSubject.value;

  // Verificar se evento já existe (por execution_id)
  const executionId = event.data.execution_id;
  if (executionId) {
    const isDuplicate = currentList.some(
      existing => existing.data.execution_id === executionId
    );

    if (isDuplicate) {
      console.log(`[GamificationEvents] Evento duplicado ignorado: ${executionId}`);
      return; // Não adicionar evento duplicado
    }
  }

  // Adicionar novo evento
  const updatedList = [...currentList, event];

  // Limitar ao máximo de eventos (remover mais antigos)
  const boundedList = updatedList.length > this.maxEvents
    ? updatedList.slice(updatedList.length - this.maxEvents)
    : updatedList;

  this.eventsSubject.next(boundedList);

  console.log(`[GamificationEvents] Novo evento adicionado. Total: ${boundedList.length}`);
}
```

---

### Fase 3: Fluxo Completo da Solução

#### Cenário 1: Primeiro Acesso (Sem Histórico Local)

```
1. Usuário abre aplicação
   └─> Angular inicializa GamificationEventsService

2. Constructor executa
   ├─> WebSocket.connect() → Conecta WS /ws/gamification
   ├─> websocketService.events$.subscribe() → Ouve eventos RT
   └─> loadHistoricalEvents() → Busca histórico do MongoDB

3. loadHistoricalEvents() executa
   ├─> Verifica sessionStorage['gamification_events_loaded']
   │   └─> Não existe (primeiro acesso)
   ├─> fetch('/api/tasks/events?limit=50')
   │   └─> Backend retorna últimas 50 execuções formatadas
   ├─> deduplicateEvents([...histórico, ...atual])
   │   └─> Mescla e remove duplicatas
   ├─> eventsSubject.next(mergedEvents)
   │   └─> Emite eventos para componentes
   └─> sessionStorage.setItem('gamification_events_loaded', 'true')

4. EventTickerComponent recebe eventos
   └─> Exibe histórico no footer ✅

5. Usuário usa aplicação normalmente
   └─> Novos eventos chegam via WebSocket em tempo real
       └─> pushEvent() verifica duplicatas e adiciona
```

#### Cenário 2: Reload da Página (F5)

```
1. Usuário pressiona F5
   └─> Navegador destroi contexto JavaScript
       └─> sessionStorage é MANTIDO (diferente de localStorage)
       └─> eventsSubject é DESTRUÍDO (memória liberada)

2. Angular reinicializa GamificationEventsService
   └─> eventsSubject = new BehaviorSubject([]) // Vazio

3. Constructor executa (mesmo fluxo do Cenário 1)
   ├─> WebSocket reconecta
   ├─> loadHistoricalEvents() executa
   │   ├─> Verifica sessionStorage['gamification_events_loaded']
   │   │   └─> ❌ Existe = 'true' (ainda está na mesma sessão)
   │   └─> ⚠️ PROBLEMA: Pula carregamento de histórico!

4. Resultado: Footer fica VAZIO até novo evento chegar ❌
```

**⚠️ Ajuste Necessário**: Usar `localStorage` ou limpar flag ao detectar reload

**Solução Refinada**:

```typescript
// Opção A: Usar localStorage (persiste entre abas/janelas)
const storageKey = 'gamification_events_loaded_timestamp';
const lastLoaded = localStorage.getItem(storageKey);
const now = Date.now();

// Recarregar se nunca carregou OU última carga foi há mais de 5 minutos
if (!lastLoaded || (now - parseInt(lastLoaded)) > 5 * 60 * 1000) {
  await this.loadHistoricalEvents();
  localStorage.setItem(storageKey, now.toString());
}

// Opção B: Sempre carregar (mais simples, overhead mínimo)
// Remove lógica de sessionStorage completamente
```

**Recomendação**: **Opção B** - Sempre carregar histórico ao inicializar.

- Custo: ~100ms de latência inicial (query simples no MongoDB)
- Benefício: Garantia de sempre ter dados
- Deduplicação previne qualquer duplicata

#### Cenário 3: Nova Execução de Agente (Tempo Real)

```
1. Backend processa tarefa de agente
   └─> Agente finaliza execução

2. Gateway emite evento WebSocket (app.py:841)
   └─> gamification_manager.broadcast_event({
       "type": "agent_execution_completed",
       "data": {...},
       "timestamp": 1730000003.123
   })

3. Frontend recebe via WebSocket
   └─> GamificationWebSocketService.events$ emite evento

4. GamificationEventsService recebe
   └─> handleWebSocketEvent(event)
       └─> pushEvent(event)
           ├─> Verifica duplicata por execution_id
           │   └─> Não existe (evento novo)
           └─> Adiciona ao eventsSubject

5. EventTickerComponent atualiza UI
   └─> Novo evento aparece instantaneamente no footer ✅
```

---

## 🎯 Análise de Gaps e Melhorias

### Gap 1: Severidade Apenas em Conselheiros ⚠️

**Problema**: Tasks regulares (não-conselheiros) não têm campo `severity` analisado.

**Impacto**:
- Eventos de agentes regulares não podem ser filtrados por severidade
- UI não pode exibir cores/ícones baseados em severidade

**Opção A - Análise Simples no Backend**:

```python
# Em mongo_task_client.py, após salvar resultado

def analyze_severity(result: str, exit_code: int) -> str:
    """Análise básica de severidade baseada em exit code e keywords."""
    if exit_code != 0:
        return "error"

    # Análise por keywords no resultado
    result_lower = result.lower()
    error_keywords = ["error", "failed", "exception", "crash"]
    warning_keywords = ["warning", "deprecated", "missing"]

    if any(kw in result_lower for kw in error_keywords):
        return "error"
    if any(kw in result_lower for kw in warning_keywords):
        return "warning"

    return "success"

# Chamar após conclusão da task
severity = self.analyze_severity(result, exit_code)
self.tasks_collection.update_one(
    {"_id": task_id},
    {"$set": {"severity": severity}}
)
```

**Opção B - Análise no Frontend (Mais Simples)**:

```typescript
// No novo endpoint /api/tasks/events, adicionar lógica

function inferSeverity(task: Task): string {
  // Se já tem severity (conselheiros), usar
  if (task.severity) return task.severity;

  // Inferir baseado em status
  if (task.status === "error") return "error";
  if (task.exit_code !== 0) return "error";

  return "success";
}
```

**Recomendação**: **Opção B** - Inferir no endpoint `/api/tasks/events`.
- Não modifica fluxo de execução de tasks
- Mantém compatibilidade com tasks antigas
- Fácil de ajustar lógica sem reprocessar dados

---

### Gap 2: Metadados de Agente Não Denormalizados 📦

**Problema**: Tasks só armazenam `agent_id`, não emoji/nome/cor.

**Impacto**:
- Endpoint `/api/tasks/events` precisa fazer JOIN com coleção `agents`
- Latência adicional por query extra

**Solução Proposta no Código Acima**: JOIN assíncrono dentro do loop.

**Otimização Adicional (Fase 2)**:

```python
# Buscar todos os agentes uma única vez antes do loop
agent_ids = list(set(task["agent_id"] for task in tasks))
agents_cursor = mongo_client.agents.find({"_id": {"$in": agent_ids}})
agents_map = {agent["_id"]: agent for agent in await agents_cursor.to_list(length=None)}

# No loop, fazer lookup no dict
for task in tasks:
    agent = agents_map.get(task["agent_id"], {})
    agent_name = agent.get("name", task["agent_id"])
    agent_emoji = agent.get("emoji", "🤖")
```

**Benefício**: Uma única query ao invés de N queries.

---

### Gap 3: Sem Filtro de Data no Endpoint Atual ⏰

**Problema**: Endpoint `GET /api/tasks` não tem parâmetros `since`/`until`.

**Solução**: Já incluído na proposta de `/api/tasks/events`:

```python
since: Optional[datetime] = Query(None)
until: Optional[datetime] = Query(None)
```

**Uso**:
```bash
# Últimas 24 horas
GET /api/tasks/events?since=2025-11-04T10:00:00Z

# Intervalo específico
GET /api/tasks/events?since=2025-11-01T00:00:00Z&until=2025-11-05T23:59:59Z
```

---

## 📊 Estimativa de Esforço

### Backend (Conductor-Gateway)

| Tarefa | Esforço | Complexidade |
|--------|---------|--------------|
| Criar endpoint `/api/tasks/events` | 3-4h | Média |
| Otimizar query com JOIN de agentes | 1h | Baixa |
| Adicionar testes unitários | 2h | Baixa |
| Testes de integração | 1h | Baixa |
| **Total Backend** | **7-8h** | **Média** |

### Frontend (Conductor-Web)

| Tarefa | Esforço | Complexidade |
|--------|---------|--------------|
| Adicionar `loadHistoricalEvents()` | 2h | Baixa |
| Implementar `deduplicateEvents()` | 1h | Baixa |
| Modificar `pushEvent()` para duplicatas | 1h | Baixa |
| Ajustar lógica de inicialização | 1h | Baixa |
| Testes manuais e ajustes | 2h | Baixa |
| **Total Frontend** | **7h** | **Baixa** |

### Testes e Refinamento

| Tarefa | Esforço | Complexidade |
|--------|---------|--------------|
| Testes end-to-end | 2h | Média |
| Validação de performance | 1h | Baixa |
| Ajustes de UX | 1h | Baixa |
| **Total Testes** | **4h** | **Baixa** |

### **TOTAL GERAL: 18-19 horas** ⏱️

---

## 🚀 Plano de Implementação

### Sprint 1: Backend Foundation (1-2 dias)

**Dia 1**:
- ✅ Criar endpoint `/api/tasks/events` em `app.py`
- ✅ Implementar query básica (sem JOIN ainda)
- ✅ Testar manualmente com Postman/curl

**Dia 2**:
- ✅ Adicionar JOIN com coleção `agents`
- ✅ Otimizar query (bulk lookup de agentes)
- ✅ Adicionar filtros `since`/`until`
- ✅ Escrever testes unitários

### Sprint 2: Frontend Integration (2-3 dias)

**Dia 1**:
- ✅ Implementar `loadHistoricalEvents()` no service
- ✅ Adicionar `deduplicateEvents()` utility
- ✅ Testar carregamento isolado (mock de API)

**Dia 2**:
- ✅ Modificar `pushEvent()` para evitar duplicatas
- ✅ Ajustar constructor para carregar histórico
- ✅ Testar integração WebSocket + REST

**Dia 3**:
- ✅ Testes end-to-end (reload, navegação, novos eventos)
- ✅ Validação de performance (timing, latência)
- ✅ Ajustes de UX (loading states, error handling)

### Sprint 3: Polishing (1 dia)

- ✅ Code review
- ✅ Documentação técnica
- ✅ Atualizar README/CHANGELOG
- ✅ Deploy para staging

---

## 🎓 Conceitos-Chave da Solução

### 1. Dual-Source Pattern

A solução implementa duas fontes de dados complementares:

- **Fonte Primária (REST API)**: Histórico persistente, carregado uma vez na inicialização
- **Fonte Secundária (WebSocket)**: Eventos em tempo real, stream contínuo

**Vantagens**:
- Baixa latência (WebSocket)
- Resiliência (dados não são perdidos)
- Sincronização eventual (deduplicação garante consistência)

### 2. Event Deduplication

Sistema usa `execution_id` como chave única para evitar duplicatas:

```typescript
// Cenário: Evento histórico e evento RT do mesmo execution
const historicalEvent = {
  type: "agent_execution_completed",
  data: { execution_id: "exec_123", ... }
};

const realtimeEvent = {
  type: "agent_execution_completed",
  data: { execution_id: "exec_123", ... } // Mesmo ID!
};

// deduplicateEvents() mantém apenas um (mais recente)
```

### 3. Session vs Storage Persistence

| Tipo | Escopo | Duração | Uso |
|------|--------|---------|-----|
| **sessionStorage** | Aba/Janela | Até fechar aba | ❌ Não adequado (perdido no F5 em algumas implementações) |
| **localStorage** | Global | Indefinido | ✅ Ideal para flag de cache |
| **Memória (RAM)** | Processo | Até reload | ❌ Problema atual |

**Solução Adotada**: Sempre carregar histórico ao inicializar (sem flag de cache).

### 4. Backward Compatibility

A solução mantém compatibilidade com:
- ✅ Tasks antigas sem `severity` (inferido no endpoint)
- ✅ Tasks sem `councilor_config` (tratadas como agente regular)
- ✅ Clients que não usam novo endpoint (WebSocket funciona normalmente)

---

## 📈 Benefícios da Solução

### Para o Usuário

1. **Contexto Preservado**: Ao recarregar página, vê o que aconteceu antes
2. **Histórico Confiável**: Dados não são mais perdidos
3. **UX Consistente**: Footer sempre mostra informações relevantes
4. **Debug Facilitado**: Pode revisar execuções anteriores

### Para o Sistema

1. **Resiliência**: Não depende apenas de memória volátil
2. **Escalabilidade**: MongoDB já está indexado para queries eficientes
3. **Observabilidade**: Histórico persistente facilita análise de problemas
4. **Extensibilidade**: Novo endpoint pode ser usado para outras features (relatórios, dashboards)

### Para Desenvolvimento

1. **Manutenibilidade**: Separação clara entre histórico e real-time
2. **Testabilidade**: Endpoint REST pode ser testado isoladamente
3. **Monitoramento**: Logs detalhados facilitam troubleshooting

---

## ⚠️ Considerações e Trade-offs

### Performance

**Query de Histórico**:
- Carga: ~50 tasks + JOIN com ~10 agentes únicos
- Tempo estimado: 50-100ms (MongoDB com indexes)
- Impacto: Adiciona <100ms ao carregamento inicial da página
- Mitigação: Query é assíncrona, não bloqueia renderização

**WebSocket**:
- Carga: Mantida constante (não afeta)
- Latência: <10ms (inalterada)

### Consistência

**Eventual Consistency**:
- Histórico é snapshot no momento da query
- WebSocket traz atualizações subsequentes
- Deduplicação garante que não há conflitos

**Edge Case - Race Condition**:
```
T0: Task finaliza no backend
T1: Frontend faz query de histórico (task não incluída ainda)
T2: Task é salva no MongoDB
T3: WebSocket emite evento (task é recebida via RT)

Resultado: ✅ OK - Task aparece via WebSocket
Não há perda de dados
```

### Escalabilidade

**Limite de Eventos em Memória**:
- Atual: 50 eventos
- Com histórico: 50 eventos (mantido)
- Rotação: Eventos mais antigos são descartados da memória

**MongoDB Storage**:
- Crescimento: ~5KB por task (aproximadamente)
- 10.000 tasks/dia = ~50MB/dia
- Recomendação: TTL index para arquivar tasks antigas (ex: 90 dias)

---

## 🔍 Exemplo de Resposta do Novo Endpoint

```http
GET /api/tasks/events?limit=5
```

```json
{
  "success": true,
  "count": 5,
  "events": [
    {
      "type": "councilor_completed",
      "data": {
        "councilor_id": "quality_councilor",
        "task_name": "Verificar Cobertura de Testes",
        "display_name": "Dra. Testa",
        "execution_id": "exec_quality_councilor_1730512345000",
        "status": "completed",
        "severity": "warning",
        "started_at": "2025-11-05T15:30:00Z",
        "completed_at": "2025-11-05T15:30:03Z",
        "duration_ms": 3450,
        "summary": "Análise concluída. Cobertura de testes está em 72% (meta: 80%)..."
      },
      "timestamp": 1730512403.123
    },
    {
      "type": "agent_execution_completed",
      "data": {
        "agent_id": "performance_agent",
        "agent_name": "Performance Analyzer",
        "agent_emoji": "🚀",
        "execution_id": "exec_performance_agent_1730512200000",
        "status": "completed",
        "started_at": "2025-11-05T15:25:00Z",
        "completed_at": "2025-11-05T15:25:05Z",
        "duration_ms": 5000,
        "level": "debug"
      },
      "timestamp": 1730512305.456
    },
    {
      "type": "agent_execution_completed",
      "data": {
        "agent_id": "security_agent",
        "agent_name": "Security Scanner",
        "agent_emoji": "🔒",
        "execution_id": "exec_security_agent_1730512000000",
        "status": "error",
        "started_at": "2025-11-05T15:20:00Z",
        "completed_at": "2025-11-05T15:20:10Z",
        "duration_ms": 10000,
        "level": "debug"
      },
      "timestamp": 1730512010.789
    }
  ]
}
```

---

## 🎯 Conclusão

### ✅ Viabilidade: ALTA

A solução proposta é **totalmente viável** e **tecnicamente sólida**:

1. **Infraestrutura Existente**: Coleção `tasks` já armazena todos os dados necessários
2. **Indexes Adequados**: MongoDB possui indexes para queries eficientes
3. **WebSocket Funcional**: Sistema de tempo real já está operacional
4. **Esforço Razoável**: 18-19 horas de desenvolvimento (~2-3 dias)
5. **Baixo Risco**: Não quebra funcionalidades existentes (additive change)

### 🎯 Recomendações Finais

**PRIORIDADE ALTA**:
1. ✅ Implementar endpoint `/api/tasks/events`
2. ✅ Adicionar `loadHistoricalEvents()` no frontend
3. ✅ Implementar deduplicação de eventos

**PRIORIDADE MÉDIA**:
4. ⚠️ Otimizar JOIN de agentes (bulk lookup)
5. ⚠️ Adicionar filtros de data (`since`/`until`)
6. ⚠️ Inferir `severity` para tasks regulares

**PRIORIDADE BAIXA**:
7. 📌 TTL index para arquivamento de tasks antigas
8. 📌 Dashboard de métricas agregadas
9. 📌 Export de eventos (CSV/JSON)

### 🚀 Próximos Passos

1. **Revisar proposta com time de desenvolvimento**
2. **Aprovar escopo e estimativa**
3. **Criar tasks no backlog**
4. **Iniciar Sprint 1: Backend Foundation**

---

## 📚 Referências

**Arquivos Analisados**:
- `conductor/src/core/services/mongo_task_client.py:12-293`
- `conductor-gateway/src/api/app.py:600-856, 1644-1773`
- `conductor-gateway/src/api/websocket.py:20-131`
- `conductor-gateway/src/services/councilor_service.py:357-496`
- `conductor-gateway/src/services/councilor_scheduler.py:189-329`
- `conductor-web/src/app/services/gamification-events.service.ts:25-100`

**Documentação Técnica**:
- MongoDB Indexes: https://www.mongodb.com/docs/manual/indexes/
- WebSocket API: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- RxJS BehaviorSubject: https://rxjs.dev/api/index/class/BehaviorSubject

---

**Documento gerado em**: 2025-11-05
**Versão**: 1.0.0
**Autor**: Claude (Requirements Engineer)
**Status**: ✅ Análise Completa - Aguardando Aprovação para Implementação
