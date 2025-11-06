# Relatório de Análise - Coleção Tasks no MongoDB

## Resumo Executivo

O conductor-gateway implementa uma coleção MongoDB chamada `tasks` que armazena tanto execuções de agentes regulares quanto execuções de agentes promovidos a "conselheiros". A coleção é gerenciada por dois serviços principais:
1. **MongoTaskClient** - para criação e gerenciamento básico
2. **CouncilorBackendScheduler** - para execuções periódicas agendadas de conselheiros

---

## 1. ESTRUTURA/SCHEMA DA COLEÇÃO `tasks`

### Localização da Coleção
- **Banco de dados**: `conductor_state` (definido em MongoTaskClient)
- **Coleção**: `tasks`
- **Inicializado em**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/app.py` (linhas 242-257)

### Estrutura Completa do Documento

```javascript
{
  _id: ObjectId,                          // ID MongoDB automático
  
  // CAMPOS BÁSICOS
  "task_id": string,                      // ID único da tarefa (gerado como exec_{agent_id}_{timestamp_ms})
  "agent_id": string,                     // ID do agente responsável
  "provider": string,                     // "claude" ou "gemini"
  "prompt": string,                       // Prompt XML completo (persona + playbook + history + user_input)
  "cwd": string,                          // Current working directory
  "timeout": number,                      // Timeout em segundos
  "instance_id": string,                  // ID da instância para separação de contextos
  "conversation_id": string,              // ID da conversa para contexto
  
  // CAMPOS DE STATUS
  "status": string,                       // "pending" | "processing" | "completed" | "error"
  "exit_code": number | null,             // Código de saída (0 = sucesso)
  "result": string,                       // Output/resultado da execução
  "error": string | null,                 // Mensagem de erro (se aplicável)
  "duration": number,                     // Duração em segundos
  
  // CAMPOS RELACIONADOS A SEVERIDADE
  "severity": string,                     // "success" | "warning" | "error" (para conselheiros)
  
  // CAMPOS RELACIONADOS A CONSELHEIROS
  "is_councilor_execution": boolean,      // Flag para identificar execuções de conselheiros
  "councilor_config": {                   // Configuração do conselheiro (se aplicável)
    "task_name": string,                  // Nome da tarefa do conselheiro
    "display_name": string                // Nome de exibição customizado
  } | null,
  
  // CAMPOS DE CONTEXTO
  "context": object,                      // Objeto de contexto para metadados adicionais
  
  // TIMESTAMPS
  "created_at": datetime,                 // Data/hora de criação (UTC)
  "updated_at": datetime,                 // Data/hora de última atualização (UTC)
  "started_at": datetime | null,          // Data/hora de início (para conselheiros)
  "completed_at": datetime | null,        // Data/hora de conclusão (para conselheiros)
}
```

### Tipos de Valores para `severity`
- **"success"**: Execução bem-sucedida sem alertas
- **"warning"**: Execução concluída mas com potenciais problemas (keywords: "alerta", "atenção", "warning", "aviso", "vulnerab", "deprecated")
- **"error"**: Erro crítico na execução (keywords: "crítico", "erro", "falha", "critical", "error", "fail", "exception")

---

## 2. ONDE E COMO AS TASKS SÃO CRIADAS/INSERIDAS

### A. MongoTaskClient.submit_task() - Método Principal

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor/src/core/services/mongo_task_client.py`

**Método**: `submit_task()` (linhas 29-89)

```python
def submit_task(
    self,
    agent_id: str,
    cwd: str,
    timeout: int = 600,
    provider: str = "claude",
    prompt: str = None,
    instance_id: str = None,
    is_councilor_execution: bool = False,
    councilor_config: dict = None,
    conversation_id: str = None
) -> str:
    """Insere nova tarefa e retorna seu ID"""
```

**Fluxo de Inserção**:
1. Cria documento com estrutura padrão
2. Define `status: "pending"` inicialmente
3. Define `severity: None` (será preenchido após execução)
4. Insere com `collection.insert_one(task_document)`
5. Retorna task_id (string do ObjectId inserido)

### B. CouncilorBackendScheduler._execute_councilor_task() - Inserções Agendadas

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/services/councilor_scheduler.py`

**Método**: `_execute_councilor_task()` (linhas 189-328)

**Dois pontos de inserção**:

**1. Sucesso (linhas 241-257)**:
```python
await self.tasks_collection.insert_one({
    "task_id": execution_id,
    "agent_id": agent_id,
    "instance_id": f"councilor_{agent_id}_{int(start_time.timestamp() * 1000)}",
    "is_councilor_execution": True,
    "councilor_config": {
        "task_name": task_name,
        "display_name": display_name
    },
    "status": "completed",
    "severity": severity,  # Analisado por _analyze_severity()
    "result": output,
    "error": None,
    "created_at": start_time,
    "completed_at": end_time,
    "duration": (end_time - start_time).total_seconds()
})
```

**2. Erro (linhas 292-308)**:
```python
await self.tasks_collection.insert_one({
    "task_id": execution_id,
    "agent_id": agent_id,
    "instance_id": f"councilor_{agent_id}_{..}",
    "is_councilor_execution": True,
    "councilor_config": {...},
    "status": "error",
    "severity": "error",
    "result": None,
    "error": str(e),
    "created_at": start_time,
    "completed_at": end_time,
    "duration": (end_time - start_time).total_seconds()
})
```

---

## 3. CAMPOS EXISTENTES NA COLEÇÃO

### Campos Obrigatórios (sempre presentes)
1. `_id` - ObjectId (MongoDB)
2. `agent_id` - string
3. `status` - string ("pending", "processing", "completed", "error")
4. `created_at` - datetime
5. `updated_at` - datetime (ou `completed_at`)
6. `is_councilor_execution` - boolean

### Campos Opcionais (dependem do contexto)
1. `provider` - string ("claude", "gemini")
2. `prompt` - string (pode ser None para conselheiros)
3. `cwd` - string (diretório de trabalho)
4. `timeout` - number (em segundos)
5. `instance_id` - string
6. `conversation_id` - string
7. `context` - object (metadados)
8. `result` - string (output da execução)
9. `error` - string | null (mensagem de erro)
10. `exit_code` - number | null
11. `duration` - number (em segundos)
12. `severity` - string | null ("success", "warning", "error")
13. `councilor_config` - object | null
14. `task_id` - string (ID único para rastreamento)
15. `started_at` - datetime | null
16. `completed_at` - datetime | null

---

## 4. ENDPOINTS EXISTENTES PARA LISTAR TASKS

### A. GET /api/tasks - Listagem Genérica

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/app.py`

**Linhas**: 1644-1711

**Query Parameters**:
- `status` (optional): Filtrar por status ("processing", "completed", "error")
- `agent_id` (optional): Filtrar por agent_id
- `limit` (default: 100, max: 500): Número máximo de resultados
- `offset` (default: 0): Paginação
- `sort` (default: "-created_at"): Campo para ordenação (prefixo "-" para descendente)

**Resposta**:
```json
{
  "success": boolean,
  "count": number,
  "total": number,
  "tasks": [
    {... task documents ...}
  ]
}
```

**Exemplos de Uso**:
```bash
# Listar todas as tasks
GET /api/tasks

# Listar apenas tasks em processamento
GET /api/tasks?status=processing

# Filtrar por agente específico
GET /api/tasks?agent_id=ReadmeResume_Agent

# Com paginação
GET /api/tasks?limit=10&offset=20

# Ordenar por outro campo
GET /api/tasks?sort=created_at
```

### B. GET /api/tasks/processing - Endpoint Dedicado para Processing

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/app.py`

**Linhas**: 1713-1773

**Query Parameters**:
- `limit` (default: 100, max: 500)
- `offset` (default: 0)
- `sort` (default: "-created_at")

**Funcionalidade**: Convenience endpoint equivalente a `GET /api/tasks?status=processing`

**Resposta**: Mesmo formato do `/api/tasks`

---

## 5. INTEGRAÇÃO COM CONSELHEIROS (Councilors)

### A. Flag `is_councilor_execution`

**Propósito**: Diferenciar execuções de conselheiros de execuções de agentes regulares

**Valores**:
- `true`: Execução de um agente promovido a conselheiro
- `false` ou não presente: Execução de agente regular

**Uso em Queries**:
```python
# No CouncilorService (linhas 369-372)
cursor = self.tasks_collection.find({
    "agent_id": councilor_id,
    "is_councilor_execution": True
}).sort("created_at", -1).limit(limit)
```

### B. Campo `severity`

**Valores Possíveis**:
- **"success"**: Execução bem-sucedida
- **"warning"**: Execução com alertas detectados
- **"error"**: Execução com erros

**Análise Automática** via `_analyze_severity()`:

```python
# CouncilorBackendScheduler (linhas 330-361)
def _analyze_severity(self, output: str) -> str:
    error_keywords = [
        'crítico', 'erro', 'falha', 'failed', 'error',
        'critical', 'fatal', 'exception'
    ]
    if any(keyword in lower_output for keyword in error_keywords):
        return 'error'
    
    warning_keywords = [
        'alerta', 'atenção', 'warning', 'aviso',
        'vulnerab', 'deprecated', 'caution'
    ]
    if any(keyword in lower_output for keyword in warning_keywords):
        return 'warning'
    
    return 'success'
```

### C. Campo `councilor_config`

**Estrutura**:
```json
{
  "task_name": string,        // Nome da tarefa do conselheiro
  "display_name": string      // Nome customizado para exibição
}
```

**Preenchido em**: CouncilorBackendScheduler ao executar tarefa de conselheiro

### D. Agendamento de Conselheiros

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/services/councilor_scheduler.py`

**Fluxo**:
1. Carrega conselheiros ativos com `is_councilor: True` e `councilor_config.schedule.enabled: True`
2. Cria triggers (interval ou cron) usando APScheduler
3. Em cada execução, insere documento na coleção `tasks` com `is_councilor_execution: True`
4. Atualiza estatísticas do agente baseado em severidade

### E. Endpoints Relacionados a Conselheiros

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/routers/councilor.py`

**Endpoints**:
- `GET /api/councilors` - Listar agentes/conselheiros
- `POST /api/councilors/{agent_id}/promote-councilor` - Promover a conselheiro
- `DELETE /api/councilors/{agent_id}/demote-councilor` - Remover status
- `PATCH /api/councilors/{agent_id}/councilor-config` - Atualizar configuração
- `PATCH /api/councilors/{agent_id}/councilor-schedule` - Pausar/retomar
- `POST /api/councilors/councilors/executions` - Salvar resultado de execução
- `GET /api/councilors/{agent_id}/councilor-reports` - Gerar relatório
- `GET /api/councilors/{agent_id}/councilor-reports/latest` - Última execução

---

## 6. ÍNDICES MONGODB

### Índices Criados Automaticamente

**Arquivo**: `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/app.py` (linhas 241-257)

```python
# Índice único em task_id
tasks_collection.create_index("task_id", unique=True, sparse=True)

# Índice composto para queries de agentes/datas
tasks_collection.create_index([("agent_id", 1), ("created_at", -1)])

# Índice para identificar execuções de conselheiros
tasks_collection.create_index("is_councilor_execution")

# Índice composto para conselheiros
tasks_collection.create_index([
    ("is_councilor_execution", 1),
    ("created_at", -1)
])

# Índice para severidade
tasks_collection.create_index("severity")
```

**Índices adicionais no MongoTaskClient** (linhas 282-289):
```python
self.collection.create_index([
    ("agent_id", 1),
    ("is_councilor_execution", 1),
    ("created_at", -1)
])
self.collection.create_index("severity")
```

---

## 7. ARQUIVOS RELEVANTES - CAMINHO COMPLETO

| Arquivo | Propósito |
|---------|-----------|
| `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor/src/core/services/mongo_task_client.py` | Classe principal para criar/gerenciar tasks |
| `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/services/councilor_scheduler.py` | Agendador de conselheiros com inserções automáticas |
| `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/services/councilor_service.py` | Lógica de negócio para conselheiros (queries) |
| `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/routers/councilor.py` | Endpoints REST para conselheiros |
| `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/api/app.py` | Endpoints genéricos de tasks + setup de índices |
| `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-gateway/src/models/councilor.py` | Modelos Pydantic para conselheiros |

---

## 8. CICLO DE VIDA DE UMA TASK

### Para Agentes Regulares
1. **Submissão**: `MongoTaskClient.submit_task()` → status = "pending"
2. **Processamento**: Status atualizado para "processing" (por serviço executor)
3. **Conclusão**: Status = "completed" ou "error", result preenchido
4. **Análise**: `update_task_severity()` analisa output e define severity

### Para Conselheiros (Agentes Promovidos)
1. **Agendamento**: `CouncilorBackendScheduler.schedule_councilor()` configura trigger
2. **Execução Periódica**: Trigger dispara `_execute_councilor_task()`
3. **Execução da IA**: `conductor_client.execute_agent()` executa agente
4. **Inserção**: Documento inserido na tasks com `is_councilor_execution: true`
5. **Análise**: `_analyze_severity()` determina severity do output
6. **Stats**: `_update_agent_stats()` atualiza estatísticas do agente
7. **Events**: Broadcast via WebSocket de eventos ("councilor_started", "councilor_completed", "councilor_error")

---

## 9. CAMPOS ESPECÍFICOS DE CONSELHEIROS

Quando uma task é inserida com `is_councilor_execution: true`:

```json
{
  "is_councilor_execution": true,
  "severity": "success|warning|error",  // Analisado automaticamente
  "councilor_config": {
    "task_name": "Verificar Qualidade",
    "display_name": "Dra. Testa"
  },
  "started_at": datetime,               // Registrado
  "completed_at": datetime,             // Registrado
  "status": "completed|error",          // Definido imediatamente
  "instance_id": "councilor_AgentID_Timestamp"  // Formato especial
}
```

---

## 10. EXEMPLO DE DOCUMENTO COMPLETO

### Execução de Conselheiro (Sucesso)
```json
{
  "_id": ObjectId("6731234567890abcdef12345"),
  "task_id": "exec_QualityAssurance_1700000000000",
  "agent_id": "QualityAssurance",
  "provider": null,
  "prompt": null,
  "cwd": null,
  "timeout": 600,
  "instance_id": "councilor_QualityAssurance_1700000000000",
  "conversation_id": null,
  "status": "completed",
  "exit_code": null,
  "result": "Análise completa: cobertura de testes em 85%, sem vulnerabilidades críticas.",
  "error": null,
  "duration": 45.23,
  "severity": "success",
  "is_councilor_execution": true,
  "councilor_config": {
    "task_name": "Verificar Qualidade",
    "display_name": "Dra. Testa"
  },
  "context": {},
  "created_at": ISODate("2024-11-06T10:30:00Z"),
  "updated_at": ISODate("2024-11-06T10:30:45Z"),
  "started_at": ISODate("2024-11-06T10:30:00Z"),
  "completed_at": ISODate("2024-11-06T10:30:45Z")
}
```

### Execução de Agente Regular
```json
{
  "_id": ObjectId("6731234567890abcdef12346"),
  "task_id": "task_123abc",
  "agent_id": "AnalysisAgent",
  "provider": "claude",
  "prompt": "<?xml>...</xml>",  // Prompt XML completo
  "cwd": "/home/user/project",
  "timeout": 600,
  "instance_id": "instance_user_12345",
  "conversation_id": "conv_789xyz",
  "status": "completed",
  "exit_code": 0,
  "result": "Análise concluída com sucesso",
  "error": null,
  "duration": 23.15,
  "severity": "success",
  "is_councilor_execution": false,
  "councilor_config": null,
  "context": {"key": "value"},
  "created_at": ISODate("2024-11-06T10:25:00Z"),
  "updated_at": ISODate("2024-11-06T10:25:23Z"),
  "started_at": null,
  "completed_at": null
}
```

