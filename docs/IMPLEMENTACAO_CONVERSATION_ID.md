# Implementação: Refatoração de instance_id para conversation_id

**Data:** 2025-11-01
**Autor:** Claude Code Assistant
**Status:** ✅ Fase 1-3 Completas, Fase 2 Parcial (aguardando integração frontend)
**Ref:** PLANO_REFATORACAO_CONVERSATION_ID.md

---

## 📋 Visão Geral

Este documento descreve a implementação completa do novo modelo de conversas globais, migrando de um sistema baseado em `instance_id` (históricos isolados por agente) para `conversation_id` (conversas compartilhadas entre múltiplos agentes).

---

## 🎯 Objetivos Alcançados

- ✅ Habilitar colaboração de múltiplos agentes em uma única conversa
- ✅ Manter histórico unificado e compartilhado
- ✅ Criar arquitetura escalável e desacoplada
- ✅ Manter compatibilidade com sistema legado (via feature flag)

---

## 📦 Componentes Implementados

### 1. Script de Normalização de Tasks

**Arquivo:** `src/conductor/scripts/normalize_tasks_add_conversation_id.py`

**Funcionalidade:**
- Adiciona campo `conversation_id` na collection `tasks`
- Mapeia cada `instance_id` único para um `conversation_id`
- Tasks sem `instance_id` recebem `conversation_id` único
- Cria índice para otimização

**Como executar:**

```bash
# Dry run (simulação)
python src/conductor/scripts/normalize_tasks_add_conversation_id.py --dry-run

# Execução real
python src/conductor/scripts/normalize_tasks_add_conversation_id.py

# Verificar apenas
python src/conductor/scripts/normalize_tasks_add_conversation_id.py --verify-only
```

**Saída esperada:**
```
✅ Conectado ao MongoDB: conductor_state
📦 Criando backup: tasks_backup_20251101_123456
🔍 Analisando tasks existentes...
📊 Encontrados 127 instance_ids únicos
✅ Normalização concluída com sucesso!
```

---

### 2. ConversationService Refatorado (Backend)

**Arquivo:** `src/conductor/src/core/services/conversation_service.py`

**Mudanças principais:**
- ✅ Nova collection `conversations` (modelo global)
- ✅ Métodos novos:
  - `create_conversation()` - Criar conversa
  - `get_conversation_by_id()` - Buscar conversa
  - `add_message()` - Adicionar mensagens
  - `set_active_agent()` - Trocar agente ativo
  - `list_conversations()` - Listar conversas
  - `delete_conversation()` - Deletar conversa
- ✅ Métodos legados (compatibilidade):
  - `get_conversation_history_legacy()`
  - `append_to_conversation_legacy()`

**Estrutura de dados (novo modelo):**

```python
{
  "conversation_id": "uuid-v4",
  "title": "Conversa sobre Feature X",
  "created_at": "2025-11-01T10:00:00Z",
  "updated_at": "2025-11-01T10:30:00Z",
  "active_agent": {
    "agent_id": "RequirementsEngineer_Agent",
    "instance_id": "uuid-instance",
    "name": "Requirements Engineer",
    "emoji": "📋"
  },
  "participants": [
    {
      "agent_id": "RequirementsEngineer_Agent",
      "instance_id": "uuid-1",
      "name": "Requirements Engineer",
      "emoji": "📋"
    },
    {
      "agent_id": "Executor_Agent",
      "instance_id": "uuid-2",
      "name": "Executor",
      "emoji": "⚡"
    }
  ],
  "messages": [
    {
      "id": "msg-uuid-1",
      "type": "user",
      "content": "Analise os requisitos do sistema X",
      "timestamp": "2025-11-01T10:00:00Z"
    },
    {
      "id": "msg-uuid-2",
      "type": "bot",
      "content": "Sistema X possui 5 requisitos principais...",
      "timestamp": "2025-11-01T10:05:00Z",
      "agent": {
        "agent_id": "RequirementsEngineer_Agent",
        "instance_id": "uuid-1",
        "name": "Requirements Engineer",
        "emoji": "📋"
      }
    }
  ]
}
```

---

### 3. Endpoints de API (Backend)

**Arquivo:** `src/conductor/src/api/routes/conversations.py`

**Rotas implementadas:**

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/conversations/` | Criar nova conversa |
| GET | `/conversations/{id}` | Obter conversa completa |
| POST | `/conversations/{id}/messages` | Adicionar mensagem |
| PUT | `/conversations/{id}/active-agent` | Alterar agente ativo |
| GET | `/conversations/` | Listar conversas |
| DELETE | `/conversations/{id}` | Deletar conversa |
| GET | `/conversations/{id}/messages` | Obter apenas mensagens |

**Exemplo de uso:**

```bash
# Criar conversa
curl -X POST http://localhost:8000/conversations/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Discussão sobre Feature Y",
    "active_agent": {
      "agent_id": "RequirementsEngineer_Agent",
      "instance_id": "uuid-1",
      "name": "Requirements Engineer",
      "emoji": "📋"
    }
  }'

# Adicionar mensagem
curl -X POST http://localhost:8000/conversations/{conversation_id}/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Analise requisitos",
    "agent_response": "Identificados 3 requisitos...",
    "agent_info": {
      "agent_id": "RequirementsEngineer_Agent",
      "instance_id": "uuid-1",
      "name": "Requirements Engineer",
      "emoji": "📋"
    }
  }'
```

---

### 4. Gateway Proxy (Backend)

**Arquivo:** `src/conductor-gateway/src/api/routers/conversations.py`

**Funcionalidade:**
- Proxy transparente para o serviço conductor
- Encaminha requisições de `/api/conversations` para conductor backend
- Tratamento de erros e timeouts

**Configuração no `app.py`:**
```python
from src.api.routers.conversations import router as conversations_router

app.include_router(conversations_router)
```

---

### 5. ConversationService (Frontend Angular)

**Arquivo:** `src/conductor-web/src/app/services/conversation.service.ts`

**Métodos implementados:**

```typescript
class ConversationService {
  createConversation(request): Observable<{conversation_id, title, created_at}>
  getConversation(conversationId): Observable<Conversation>
  addMessage(conversationId, request): Observable<{success, message}>
  setActiveAgent(conversationId, request): Observable<{success, message}>
  listConversations(limit?, skip?): Observable<{total, conversations}>
  deleteConversation(conversationId): Observable<{success, message}>
  getConversationMessages(conversationId, limit?): Observable<{messages}>
}
```

**Interfaces TypeScript:**

```typescript
interface AgentInfo {
  agent_id: string;
  instance_id: string;
  name: string;
  emoji?: string;
}

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: string;
  agent?: AgentInfo;
}

interface Conversation {
  conversation_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  active_agent?: AgentInfo;
  participants: AgentInfo[];
  messages: Message[];
}
```

---

### 6. Feature Flag

**Arquivos:**
- `src/conductor-web/src/environments/environment.ts`
- `src/conductor-web/src/environments/environment.development.ts`
- `src/conductor-web/src/environments/environment.prod.ts`

**Configuração:**

```typescript
export const environment = {
  production: false,
  apiUrl: '/api',

  features: {
    // true = novo modelo (conversation_id)
    // false = modelo legado (instance_id)
    useConversationModel: true
  }
};
```

**Como usar no código:**

```typescript
import { environment } from '../../environments/environment';

if (environment.features.useConversationModel) {
  // Usar novo modelo de conversas
  this.conversationService.getConversation(conversationId).subscribe(...);
} else {
  // Usar modelo legado
  this.agentService.getAgentContext(instanceId).subscribe(...);
}
```

---

### 7. Script de Migração de Dados

**Arquivo:** `src/conductor/scripts/migrate_histories_to_conversations.py`

**Funcionalidade:**
- Migra dados de `agent_conversations` → `conversations`
- Converte formato `{role, content}` → `{type, content, agent}`
- Constrói mapa `instance_id` → `agent_id` usando collection `tasks`
- Gera `conversation_id` único para cada `instance_id`

**Como executar:**

```bash
# Dry run (simulação)
python src/conductor/scripts/migrate_histories_to_conversations.py --dry-run

# Execução real
python src/conductor/scripts/migrate_histories_to_conversations.py

# Verificar migração
python src/conductor/scripts/migrate_histories_to_conversations.py --verify-only
```

**Saída esperada:**
```
📦 Criando backup: agent_conversations_backup_20251101_123456
🔍 Construindo mapa instance_id → agent_id...
✅ Mapa construído com 85 entradas
📊 Encontradas 127 conversas para migrar
✅ Migrada: uuid-1 → conv-uuid-1 (24 mensagens)
✅ Migrada: uuid-2 → conv-uuid-2 (12 mensagens)
...
✅ Migração concluída: 127/127 conversas migradas
```

---

## 🚀 Roteiro de Implantação

### Passo 1: Normalizar Tasks (Preparação)

```bash
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor

# 1. Dry run para verificar
python scripts/normalize_tasks_add_conversation_id.py --dry-run

# 2. Executar normalização
python scripts/normalize_tasks_add_conversation_id.py

# 3. Verificar resultado
python scripts/normalize_tasks_add_conversation_id.py --verify-only
```

### Passo 2: Migrar Históricos

```bash
# 1. Dry run da migração
python scripts/migrate_histories_to_conversations.py --dry-run

# 2. Executar migração
python scripts/migrate_histories_to_conversations.py

# 3. Verificar resultado
python scripts/migrate_histories_to_conversations.py --verify-only
```

### Passo 3: Reiniciar Serviços

```bash
# Reiniciar conductor backend
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor
# (comando de restart depende do ambiente)

# Reiniciar conductor-gateway
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor-gateway
# (comando de restart depende do ambiente)

# Rebuild frontend
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor-web
npm run build
```

### Passo 4: Testar APIs

```bash
# Criar conversa teste
curl -X POST http://localhost:5006/api/conversations/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Teste de Conversa",
    "active_agent": {
      "agent_id": "test_agent",
      "instance_id": "test-instance",
      "name": "Test Agent",
      "emoji": "🧪"
    }
  }'

# Listar conversas
curl http://localhost:5006/api/conversations/
```

### Passo 5: Integração Frontend (Pendente)

**Tarefas restantes:**

1. **Refatorar `conductor-chat.component.ts`:**
   - Remover `chatHistories: Map<string, Message[]>`
   - Adicionar `activeConversationId: string`
   - Usar `ConversationService` em vez de `AgentService`
   - Implementar lógica condicional com feature flag

2. **Ajustar UI:**
   - Exibir nome/emoji do agente em mensagens de bot
   - Adicionar indicador visual de múltiplos participantes
   - (Opcional) Lista de conversas recentes no sidebar

---

## 🧪 Testes

### Backend

```bash
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor

# Testar ConversationService
pytest tests/core/services/test_conversation_service.py -v

# Testar rotas de API
pytest tests/api/test_conversations_routes.py -v
```

### Frontend

```bash
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor-web

# Testar serviço
ng test --include='**/conversation.service.spec.ts'

# Testar componente (após refatoração)
ng test --include='**/conductor-chat.component.spec.ts'
```

---

## 📊 Comparação: Antes vs. Depois

### Modelo Antigo (instance_id)

```
AgentA (instance_id: uuid-A)
├─ Msg 1: User: "Analise requisitos"
├─ Msg 2: Agent: "Requisitos identificados..."
└─ [Histórico isolado em agent_conversations]

AgentB (instance_id: uuid-B)
└─ [Histórico vazio - não vê mensagens de AgentA]
```

### Modelo Novo (conversation_id)

```
Conversation (conversation_id: conv-uuid-1)
├─ Participantes: [AgentA, AgentB]
├─ Agente Ativo: AgentB
├─ Msg 1: User: "Analise requisitos"
├─ Msg 2: AgentA: "Requisitos identificados..."
├─ Msg 3: User: "Execute requisitos"
└─ Msg 4: AgentB: "Executando..." ✅ VÊ TODO O HISTÓRICO
```

---

## 🔧 Troubleshooting

### Problema: "Conversa não encontrada"

**Causa:** conversation_id inválido ou não migrado

**Solução:**
```bash
# Verificar se conversa existe
mongo conductor_state --eval 'db.conversations.find({conversation_id: "uuid"})'

# Verificar migração
python scripts/migrate_histories_to_conversations.py --verify-only
```

### Problema: "Agent info missing"

**Causa:** Mensagens antigas sem metadados de agente

**Solução:** Re-executar migração com mapa atualizado de agent_id

### Problema: "Feature flag não funciona"

**Causa:** Ambiente não foi rebuilded após mudança

**Solução:**
```bash
cd src/conductor-web
npm run build
# ou
ng serve --configuration=development
```

---

## 📝 Próximos Passos

### Fase 2 (Frontend) - PENDENTE

- [ ] Refatorar `conductor-chat.component.ts`
- [ ] Ajustar UI para exibir múltiplos agentes
- [ ] Testes E2E do fluxo completo

### Fase 4 (Limpeza) - APÓS VALIDAÇÃO

- [ ] Remover métodos legados do `ConversationService`
- [ ] Remover feature flag `useConversationModel`
- [ ] Arquivar collection `agent_conversations`
- [ ] Remover código comentado

---

## 📚 Referências

- [PLANO_REFATORACAO_CONVERSATION_ID.md](../PLANO_REFATORACAO_CONVERSATION_ID.md) - Plano original
- [analise_troca_agente_com_historico.md](../src/conductor-web/docs/analise_troca_agente_com_historico.md) - Análise prévia

---

**Última atualização:** 2025-11-01
**Autores:** Claude Code Assistant, Gemini (plano original)
