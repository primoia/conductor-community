# ✅ Checklist de Testes - Sistema de Conselheiros

> **Propósito:** Verificar que o sistema completo (Frontend + Backend) está funcionando corretamente

---

## 🚀 Pré-requisitos

- [ ] MongoDB rodando (`mongodb:27017`)
- [ ] Conductor Gateway rodando (`localhost:5006`)
- [ ] Conductor Web rodando (`localhost:4200`)
- [ ] Pelo menos 1 agente cadastrado no sistema

---

## 🔧 Testes de Backend (API)

### 1. Health Check

```bash
curl http://localhost:5006/health
```

**Esperado:** Status 200 OK

---

### 2. Listar Todos os Agentes

```bash
curl http://localhost:5006/api/agents
```

**Esperado:**
- Status 200
- JSON com lista de agentes
- Campo `is_councilor` presente em cada agente

---

### 3. Listar Apenas Conselheiros

```bash
curl http://localhost:5006/api/agents?is_councilor=true
```

**Esperado:**
- Status 200
- JSON com array vazio (se nenhum conselheiro ainda) ou lista de conselheiros

---

### 4. Promover Agente a Conselheiro

```bash
curl -X POST http://localhost:5006/api/agents/code_generator_agent/promote-councilor \
  -H "Content-Type: application/json" \
  -d '{
    "councilor_config": {
      "title": "Conselheiro de Teste",
      "schedule": {
        "type": "interval",
        "value": "5m",
        "enabled": true
      },
      "task": {
        "name": "Verificação de Teste",
        "prompt": "Liste os arquivos .ts do projeto",
        "output_format": "summary"
      },
      "notifications": {
        "on_success": false,
        "on_warning": true,
        "on_error": true,
        "channels": ["panel"]
      }
    },
    "customization": {
      "display_name": "Bot de Teste"
    }
  }'
```

**Esperado:**
- Status 200
- `success: true`
- `agent` com `is_councilor: true`
- `agent.councilor_config` preenchido
- `agent.customization.display_name: "Bot de Teste"`

**Verificar MongoDB:**
```bash
# Conectar ao MongoDB
mongosh mongodb://admin:<MONGO_PASSWORD>@localhost:27017/?authSource=admin

# Verificar agente
use conductor_state
db.agents.findOne({ agent_id: "code_generator_agent" })
```

---

### 5. Tentar Promover Novamente (Deve Falhar)

```bash
curl -X POST http://localhost:5006/api/agents/code_generator_agent/promote-councilor \
  -H "Content-Type: application/json" \
  -d '{ "councilor_config": { ... } }'
```

**Esperado:**
- Status 409 Conflict
- Mensagem: "already a councilor"

---

### 6. Atualizar Configuração

```bash
curl -X PATCH http://localhost:5006/api/agents/code_generator_agent/councilor-config \
  -H "Content-Type: application/json" \
  -d '{
    "task": {
      "name": "Nova Tarefa Atualizada",
      "prompt": "Novo prompt atualizado",
      "output_format": "detailed"
    }
  }'
```

**Esperado:**
- Status 200
- `success: true`
- `agent.councilor_config.task.name: "Nova Tarefa Atualizada"`

---

### 7. Pausar Schedule

```bash
curl -X PATCH http://localhost:5006/api/agents/code_generator_agent/councilor-schedule \
  -H "Content-Type: application/json" \
  -d '{ "enabled": false }'
```

**Esperado:**
- Status 200
- `schedule.enabled: false`

---

### 8. Retomar Schedule

```bash
curl -X PATCH http://localhost:5006/api/agents/code_generator_agent/councilor-schedule \
  -H "Content-Type: application/json" \
  -d '{ "enabled": true }'
```

**Esperado:**
- Status 200
- `schedule.enabled: true`

---

### 9. Salvar Execução Manual

```bash
curl -X POST http://localhost:5006/api/agents/councilors/executions \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "exec_test_001",
    "councilor_id": "code_generator_agent",
    "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "status": "completed",
    "severity": "warning",
    "output": "Encontrados 3 arquivos grandes:\n1. file1.ts (800 linhas)\n2. file2.ts (650 linhas)\n3. file3.ts (900 linhas)",
    "duration_ms": 2500
  }'
```

**Esperado:**
- Status 201 Created
- `success: true`
- `execution` com todos os dados salvos

**Verificar MongoDB:**
```bash
mongosh mongodb://admin:<MONGO_PASSWORD>@localhost:27017/?authSource=admin

use conductor_state
db.councilor_executions.findOne({ execution_id: "exec_test_001" })
```

**Verificar Stats Atualizadas:**
```bash
db.agents.findOne(
  { agent_id: "code_generator_agent" },
  { stats: 1 }
)
```

**Esperado:**
- `stats.total_executions: 1`
- `stats.success_rate: 0.0` (pois foi warning, não success)

---

### 10. Salvar Segunda Execução (Success)

```bash
curl -X POST http://localhost:5006/api/agents/councilors/executions \
  -H "Content-Type: application/json" \
  -d '{
    "execution_id": "exec_test_002",
    "councilor_id": "code_generator_agent",
    "started_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "completed_at": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
    "status": "completed",
    "severity": "success",
    "output": "Nenhum problema encontrado!",
    "duration_ms": 1200
  }'
```

**Verificar Stats:**
```bash
db.agents.findOne(
  { agent_id: "code_generator_agent" },
  { stats: 1 }
)
```

**Esperado:**
- `stats.total_executions: 2`
- `stats.success_rate: 50.0` (1 success de 2 total)

---

### 11. Buscar Relatório

```bash
curl http://localhost:5006/api/agents/code_generator_agent/councilor-reports?limit=5
```

**Esperado:**
- Status 200
- `councilor_id: "code_generator_agent"`
- `councilor_name: "Bot de Teste"`
- `recent_executions: [ ... ]` (2 execuções)
- `total_executions: 2`
- `success_rate: 50.0`

---

### 12. Buscar Última Execução

```bash
curl http://localhost:5006/api/agents/code_generator_agent/councilor-reports/latest
```

**Esperado:**
- Status 200
- Dados da última execução (exec_test_002)

---

### 13. Demover Conselheiro

```bash
curl -X DELETE http://localhost:5006/api/agents/code_generator_agent/demote-councilor
```

**Esperado:**
- Status 200
- `success: true`
- `agent.is_councilor: false`
- `agent.councilor_config` removido

**Verificar MongoDB:**
```bash
db.agents.findOne({ agent_id: "code_generator_agent" })
```

**Esperado:**
- `is_councilor: false`
- `councilor_config` não existe
- `stats` preservadas

---

## 🎨 Testes de Frontend

### 1. Abrir Dashboard de Conselheiros

1. Abra o Conductor Web (`http://localhost:4200`)
2. Clique no botão "🏛️ Conselho"

**Esperado:**
- Modal/dashboard abre
- Se não houver conselheiros: mensagem "Nenhum conselheiro ativo"
- Botão "⭐ Promover Primeiro Conselheiro" visível

---

### 2. Promover Agente via UI

1. Clique em "⭐ Promover Novo Conselheiro"
2. Modal de promoção abre
3. Preencher formulário:
   - Nome: "Silva"
   - Título: "Conselheiro de Arquitetura"
   - Template: Selecionar "Verificar Arquivos Monolíticos"
   - Periodicidade: "30m"
   - Notificações: ✅ Alertas e Erros
4. Clicar "⭐ Promover"

**Esperado:**
- Request POST enviado para `/api/agents/.../promote-councilor`
- Sucesso retornado
- Modal fecha
- Dashboard atualiza mostrando o novo conselheiro

---

### 3. Verificar Conselheiro no Dashboard

**Esperado no card:**
- Avatar com emoji
- Badge de status (✅)
- Nome: "Silva"
- Cargo: "Conselheiro de Arquitetura"
- Tarefa: "Verificar Arquivos Monolíticos"
- Última execução: "Nunca executado" (se novo)
- Próxima execução: "daqui a 30m"
- Estatísticas: 0 execuções, 0% sucesso

**Botões disponíveis:**
- 📋 Ver Último Relatório
- ⚙️ Editar Configuração
- ⏸️ Pausar
- 🗑️ Remover do Conselho (na parte inferior)

---

### 4. Verificar Coroa no AgentGame

1. Abrir AgentGame (se disponível na UI)
2. Localizar o agente promovido

**Esperado:**
- Coroa dourada 👑 acima do agente
- Borda dourada ao redor do círculo
- Efeito de brilho (shadow glow)

---

### 5. Pausar Conselheiro

1. No dashboard, clicar "⏸️ Pausar"

**Esperado:**
- Request PATCH enviado para `/api/agents/.../councilor-schedule`
- Status visual muda para "Pausado"
- Badge muda para ⏸️
- Botão muda para "▶️ Retomar"
- Próxima execução mostra "Pausado"

---

### 6. Retomar Conselheiro

1. Clicar "▶️ Retomar"

**Esperado:**
- Request PATCH enviado
- Status volta para "Ativo"
- Badge volta para ✅
- Botão volta para "⏸️ Pausar"

---

### 7. Simular Execução (Scheduler Funcionando)

**Pré-requisito:** CouncilorSchedulerService inicializado

1. Aguardar o intervalo configurado (ex: 30 minutos)
   - OU reduzir para 1 minuto para teste rápido

**Esperado:**
- Frontend scheduler executa o agente
- Resultado salvo via POST `/api/agents/councilors/executions`
- Evento aparece no painel de gamificação:
  - "🏗️ Silva: Verificar Arquivos Monolíticos - [resultado]"
- Dashboard atualiza estatísticas automaticamente

---

### 8. Ver Último Relatório

1. Após uma execução, clicar "📋 Ver Último Relatório"

**Esperado:**
- Modal abre com relatório detalhado
- Mostra execução mais recente
- Output do agente exibido

---

### 9. Editar Configuração

1. Clicar "⚙️ Editar Configuração"

**Esperado:**
- Modal de edição abre (similar ao de promoção)
- Campos preenchidos com valores atuais
- Permite modificar tarefa, periodicidade, notificações

---

### 10. Demover Conselheiro

1. Clicar "Remover do Conselho"
2. Confirmar no diálogo

**Esperado:**
- Request DELETE enviado
- Conselheiro removido da lista
- Se era o último, volta para estado "empty"
- Coroa desaparece do AgentGame

---

## 🔄 Teste de Integração Completa

### Cenário: Ciclo de Vida Completo

1. **Promover agente** via UI → Backend salva → MongoDB atualizado
2. **Scheduler inicia** → Task agendada (setInterval)
3. **Execução automática** → AgentService executa → Resultado analisado
4. **Salvar resultado** → POST /executions → MongoDB salva
5. **Atualizar stats** → MongoDB atualiza `stats` do agente
6. **Notificar** → Evento adicionado ao painel de gamificação
7. **Usuário visualiza** → Dashboard mostra execução recente
8. **Pausar** → Task cancelada (clearInterval)
9. **Demover** → Conselheiro removido do sistema

**Checklist:**
- [ ] Promoção funcionou
- [ ] Scheduler agendou task
- [ ] Execução aconteceu automaticamente
- [ ] Resultado foi salvo no MongoDB
- [ ] Stats foram atualizadas
- [ ] Evento apareceu no painel
- [ ] Dashboard mostrou execução
- [ ] Pause funcionou
- [ ] Demoção funcionou

---

## 📊 Verificações MongoDB

### Índices Criados

```bash
mongosh mongodb://admin:<MONGO_PASSWORD>@localhost:27017/?authSource=admin

use conductor_state

# Verificar índices da collection agents
db.agents.getIndexes()
```

**Esperado:**
```javascript
[
  { "_id": 1 },
  { "agent_id": 1 },        // unique
  { "is_councilor": 1 }     // novo
]
```

### Índices de Execuções

```bash
db.councilor_executions.getIndexes()
```

**Esperado:**
```javascript
[
  { "_id": 1 },
  { "execution_id": 1 },    // unique
  { "councilor_id": 1 },
  { "councilor_id": 1, "started_at": -1 }  // compound
]
```

---

## 🐛 Troubleshooting

### Erro: "CouncilorService not available"

**Solução:**
- Verificar que o router foi incluído no `app.py`
- Verificar que o MongoDB está rodando
- Reiniciar o conductor-gateway

### Erro: "Agent not found"

**Solução:**
- Verificar que o `agent_id` está correto
- Listar agentes disponíveis: `GET /api/agents`

### Scheduler não executa

**Solução:**
- Verificar se `CouncilorSchedulerService.initialize()` foi chamado
- Verificar se `schedule.enabled = true`
- Verificar console do navegador para erros
- Reduzir intervalo para 1 minuto para teste rápido

### Coroa não aparece

**Solução:**
- Verificar se `agent.isCouncilor = true` no AgentGame
- Verificar se método `loadCouncilorIds()` está sendo chamado
- Verificar se endpoint `/api/agents?is_councilor=true` retorna o agente

---

## ✅ Checklist Final

### Backend
- [ ] Servidor iniciado sem erros
- [ ] Índices MongoDB criados
- [ ] Endpoint `/health` responde
- [ ] Endpoint de listar agentes funciona
- [ ] Endpoint de promover funciona
- [ ] Endpoint de pausar/retomar funciona
- [ ] Endpoint de salvar execução funciona
- [ ] Endpoint de buscar relatório funciona
- [ ] Endpoint de demover funciona
- [ ] Validações de erro funcionam (404, 409, 400)

### Frontend
- [ ] Dashboard abre corretamente
- [ ] Modal de promoção funciona
- [ ] Formulário de promoção valida corretamente
- [ ] Promoção via UI funciona
- [ ] Dashboard lista conselheiros
- [ ] Botões de ação funcionam
- [ ] Coroa aparece no AgentGame
- [ ] Scheduler executa tarefas
- [ ] Eventos aparecem no painel
- [ ] Pause/resume funciona

### Integração
- [ ] Frontend → Backend → MongoDB (ciclo completo)
- [ ] Scheduler frontend → Backend API
- [ ] Execuções salvas → Stats atualizadas
- [ ] Eventos → Painel de gamificação
- [ ] Promoção → Visual no AgentGame

---

**Se todos os checkboxes estiverem marcados: 🎉 Sistema funcionando perfeitamente!**
