# Funcionalidade: Conversas (Conversations)

## 📋 Visão Geral

O sistema de **Conversas** é o núcleo de interação do Conductor, permitindo que usuários mantenham diálogos organizados com múltiplos agentes de IA especializados. Uma conversa representa um contexto compartilhado e persistente onde diferentes agentes podem colaborar sequencialmente, mantendo o histórico unificado de todas as interações.

A funcionalidade foi projetada para evoluir o Conductor de uma simples ferramenta de "chat com IA" para uma plataforma de "resolução de problemas colaborativa", onde especialistas artificiais trabalham em conjunto para alcançar objetivos complexos.

**Contexto arquitetural:**
- Um **Roteiro (Screenplay)** pode ter **N Conversas**
- Cada **Conversa** pode ter **N Agentes** participantes
- Cada **Conversa** mantém um histórico unificado de mensagens
- As mensagens preservam a identidade do agente que as gerou

## 🎯 Requisitos Identificados

### Requisitos Funcionais

**RF1: Criar nova conversa**
- O sistema deve permitir criar uma nova conversa, opcionalmente vinculada a um roteiro específico
- A conversa deve receber um título automático baseado na data/hora de criação ou um título customizado
- Uma conversa pode ser iniciada com um agente ativo já definido

**RF2: Listar conversas existentes**
- O sistema deve exibir todas as conversas do usuário ordenadas por data de atualização (mais recentes primeiro)
- Cada item da lista deve mostrar: título, número de mensagens, número de participantes (agentes) e última atualização
- As conversas podem ser filtradas por roteiro específico quando aplicável

**RF3: Selecionar conversa ativa**
- O usuário deve poder alternar entre diferentes conversas
- Ao selecionar uma conversa, todo seu histórico de mensagens deve ser carregado e exibido
- A conversa selecionada deve ser destacada visualmente na lista

**RF4: Adicionar mensagens à conversa**
- O sistema deve permitir adicionar mensagens do usuário e respostas dos agentes ao histórico
- Cada mensagem deve registrar: conteúdo, tipo (user/bot), timestamp e agente (para mensagens de bot)
- As mensagens devem ser persistidas em tempo real

**RF5: Trocar agente ativo**
- O usuário deve poder trocar o agente que responderá à próxima mensagem
- Ao trocar de agente, o histórico completo da conversa deve permanecer acessível ao novo agente
- O agente deve ser adicionado automaticamente à lista de participantes se ainda não estiver presente

**RF6: Deletar conversa**
- O usuário deve poder deletar uma conversa e todo seu histórico
- O sistema deve solicitar confirmação antes de deletar
- Após deletar, se a conversa estava ativa, o estado deve ser resetado

**RF7: Vincular conversa a roteiro**
- Conversas devem poder ser associadas a um roteiro específico
- O vínculo permite organizar conversas por contexto de trabalho
- Conversas vinculadas a roteiros podem ser filtradas na listagem

**RF8: Identificar participantes**
- O sistema deve manter registro de todos os agentes que participaram da conversa
- Cada agente participante deve ter: agent_id, instance_id, nome e emoji
- A lista de participantes deve ser exibida no resumo da conversa

### Requisitos Não-Funcionais

**RNF1: Persistência e consistência**
- Todas as conversas e mensagens devem ser persistidas no MongoDB
- O histórico deve ser mantido íntegro mesmo em caso de falhas
- Índices devem ser criados para otimizar consultas por conversation_id, updated_at e screenplay_id

**RNF2: Performance**
- A listagem de conversas deve ser paginada (padrão: 20 por página)
- Mensagens devem ser carregadas de forma eficiente, suportando limite opcional
- As operações de leitura devem ser otimizadas para não impactar a UX

**RNF3: Escalabilidade**
- A arquitetura deve suportar múltiplas conversas simultâneas
- O modelo de dados deve permitir crescimento do histórico sem degradação
- Operações devem ser atômicas para evitar race conditions

**RNF4: Rastreabilidade**
- Todas as operações devem gerar logs estruturados
- Cada mensagem deve ter identificador único (UUID)
- Timestamps devem ser registrados em formato ISO 8601 (UTC)

## 🔄 Fluxo do Processo

### Criação de Nova Conversa

1. **Início**: O usuário clica no botão "+" na interface de conversas ou inicia uma interação quando nenhuma conversa está ativa
2. **Validação**: O sistema verifica se há um agente disponível e opcionalmente um roteiro selecionado
3. **Criação**:
   - Frontend chama `conversationService.createConversation()` com título opcional, agente ativo e screenplay_id
   - Backend gera um UUID único como conversation_id
   - Cria documento na collection `conversations` com metadados iniciais
   - Retorna o conversation_id ao frontend
4. **Ativação**: A nova conversa se torna a conversa ativa no componente de chat
5. **Atualização**: A lista de conversas é recarregada para exibir a nova entrada

### Envio de Mensagem

1. **Entrada do usuário**: Usuário digita mensagem no editor de chat e pressiona enviar
2. **Validação**: Sistema verifica se há uma conversa ativa e um agente selecionado
3. **Persistência da mensagem do usuário**:
   - Frontend chama `conversationService.addMessage()` com user_input
   - Backend adiciona mensagem tipo "user" ao array messages
   - Atualiza campo updated_at da conversa
4. **Execução do agente**:
   - Sistema recupera todo o histórico da conversa
   - Formata histórico para envio ao agente ativo
   - Executa agente com contexto completo
5. **Persistência da resposta**:
   - Frontend chama novamente `addMessage()` com agent_response e agent_info
   - Backend adiciona mensagem tipo "bot" com metadados do agente
   - Adiciona agente aos participantes se necessário
6. **Atualização da UI**: Mensagens são exibidas em tempo real no chat

### Alternância de Agente

1. **Seleção**: Usuário clica em um agente diferente no dock lateral
2. **Definição do agente ativo**:
   - Frontend chama `conversationService.setActiveAgent()` passando agent_info
   - Backend atualiza campo active_agent na conversa
   - Backend registra o novo agente nos participantes se necessário
3. **Recarregamento de contexto**:
   - Sistema busca a conversa atualizada
   - Histórico completo é mantido intacto
   - Interface visual atualiza indicador de agente ativo
4. **Resultado**: Próxima mensagem será processada pelo novo agente, mas com acesso a todo histórico anterior

### Alternância de Conversa

1. **Seleção**: Usuário clica em uma conversa diferente na lista lateral
2. **Carregamento**:
   - Frontend chama `conversationService.getConversation(conversation_id)`
   - Backend retorna conversa completa com mensagens, participantes e agente ativo
3. **Renderização**:
   - Histórico de mensagens é convertido para formato do componente
   - Cada mensagem de bot exibe nome e emoji do agente que a gerou
   - Interface atualiza para refletir agente ativo da conversa
4. **Estado**: A nova conversa se torna a conversa ativa para próximas interações

### Deleção de Conversa

1. **Ação**: Usuário clica no ícone de lixeira em uma conversa
2. **Confirmação**: Sistema exibe diálogo pedindo confirmação
3. **Execução**:
   - Frontend chama `conversationService.deleteConversation(conversation_id)`
   - Backend remove documento da collection conversations
4. **Limpeza de estado**:
   - Se a conversa deletada estava ativa, activeConversationId é resetado para null
   - Lista de conversas é recarregada
   - Interface volta ao estado inicial

## 🏗️ Componentes Principais

### Frontend (Angular)

**ConversationListComponent** (`src/app/shared/conversation-list/conversation-list.component.ts`)
- **Responsabilidade**: Exibir lista de conversas e permitir navegação entre elas
- **Funcionalidades**:
  - Renderiza conversas com título, metadados (número de agentes e mensagens) e data de atualização
  - Destaca visualmente a conversa ativa
  - Permite criar nova conversa via botão "+"
  - Permite deletar conversa com confirmação
  - Formata datas de forma humanizada (ex: "5m atrás", "2h atrás")
- **Inputs**: `activeConversationId`, `screenplayId` (para filtrar)
- **Outputs**: `conversationSelected`, `conversationCreated`, `conversationDeleted`

**ConversationService** (`src/app/services/conversation.service.ts`)
- **Responsabilidade**: Comunicar com API de conversas via HTTP
- **Métodos principais**:
  - `createConversation(request)`: Criar nova conversa
  - `getConversation(conversationId)`: Obter conversa completa
  - `listConversations(limit, skip, screenplay_id?)`: Listar conversas com paginação
  - `addMessage(conversationId, request)`: Adicionar mensagem
  - `setActiveAgent(conversationId, request)`: Trocar agente ativo
  - `deleteConversation(conversationId)`: Deletar conversa
  - `getConversationMessages(conversationId, limit?)`: Obter apenas mensagens
- **Interfaces exportadas**: `Conversation`, `ConversationSummary`, `Message`, `AgentInfo`

**ConductorChatComponent** (`src/app/shared/conductor-chat/conductor-chat.component.ts`)
- **Responsabilidade**: Componente principal de chat que orquestra conversas
- **Integração com conversas**:
  - Mantém referência à conversa ativa via `activeConversationId`
  - Gerencia estado de mensagens e participantes
  - Coordena criação, seleção e deleção de conversas
  - Integra-se com ConversationListComponent via ViewChild
- **Métodos relacionados a conversas**:
  - `loadContextWithConversationModel()`: Carrega contexto usando novo modelo
  - `handleSendMessageWithConversationModel()`: Envia mensagem usando novo modelo
  - `onCreateNewConversation()`: Cria nova conversa via UI
  - `onSelectConversation()`: Alterna entre conversas
  - `onDeleteConversation()`: Remove conversa
  - `refreshConversationList()`: Atualiza lista de conversas
- **Feature flag**: Funcionalidade controlada por `environment.features.useConversationModel`

### Backend (Python)

**ConversationService** (`src/conductor/src/core/services/conversation_service.py`)
- **Responsabilidade**: Camada de serviço para gerenciar conversas no MongoDB
- **Métodos principais**:
  - `create_conversation(title?, active_agent?, screenplay_id?)`: Cria nova conversa com UUID
  - `get_conversation_by_id(conversation_id)`: Busca conversa completa
  - `add_message(conversation_id, user_input?, agent_response?, agent_info?)`: Adiciona mensagem(s)
  - `set_active_agent(conversation_id, agent_info)`: Define agente ativo
  - `_add_participant(conversation_id, agent_info)`: Adiciona agente aos participantes (interno)
  - `get_conversation_messages(conversation_id, limit?)`: Retorna apenas mensagens
  - `list_conversations(limit, skip, screenplay_id?)`: Lista conversas com filtros
  - `delete_conversation(conversation_id)`: Remove conversa
- **Métodos legacy**: `get_conversation_history_legacy()` e `append_to_conversation_legacy()` (mantidos temporariamente para compatibilidade)
- **Otimizações**: Cria índices no MongoDB para conversation_id, participants.agent_id, updated_at e screenplay_id

**Conversations Router** (`src/conductor/src/api/routes/conversations.py`)
- **Responsabilidade**: Endpoints FastAPI para operações de conversas
- **Endpoints**:
  - `POST /conversations/`: Criar conversa
  - `GET /conversations/{conversation_id}`: Obter conversa
  - `POST /conversations/{conversation_id}/messages`: Adicionar mensagem
  - `PUT /conversations/{conversation_id}/active-agent`: Trocar agente ativo
  - `GET /conversations/`: Listar conversas (com paginação e filtro por screenplay_id)
  - `DELETE /conversations/{conversation_id}`: Deletar conversa
  - `GET /conversations/{conversation_id}/messages`: Obter mensagens
  - `POST /conversations/migrate-screenplays`: Endpoint de migração para normalizar roteiros antigos
- **Modelos Pydantic**: Define contratos de request/response (CreateConversationRequest, ConversationDetail, ConversationSummary, etc.)

**Gateway Router** (`src/conductor-gateway/src/api/routers/conversations.py`)
- **Responsabilidade**: Proxy transparente para os endpoints de conversas
- **Função**: Encaminha todas as requisições de `/api/conversations/*` para o serviço conductor backend
- **Implementação**: Usa função genérica `proxy_request()` para fazer forward de requests mantendo headers, body e query params

## 🔗 Relacionamentos e Dependências

### Fluxo de Dados: Frontend → Gateway → Backend → MongoDB

1. **Frontend → Gateway**:
   - ConversationService faz requisições HTTP para `${environment.apiUrl}/conversations/*`
   - Envia dados em JSON (CreateConversationRequest, AddMessageRequest, etc.)

2. **Gateway → Conductor API**:
   - Gateway recebe requisições em `/api/conversations/*`
   - Faz proxy transparente para `${CONDUCTOR_URL}/conversations/*`
   - Mantém headers originais e passa query params

3. **Conductor API → ConversationService**:
   - Rotas FastAPI validam request com Pydantic
   - Instanciam ConversationService e chamam métodos apropriados
   - Retornam responses padronizados

4. **ConversationService → MongoDB**:
   - Conecta na collection `conversations`
   - Executa operações CRUD usando PyMongo
   - Garante atomicidade com operações como `$push`, `$set`, `$inc`

### Dependência de Roteiros (Screenplays)

- Conversas podem ser criadas **sem vínculo** com roteiro (screenplay_id = null)
- Conversas vinculadas a roteiros permitem organização contextual
- Um roteiro pode ter múltiplas conversas independentes
- Filtro por screenplay_id permite listar apenas conversas de um roteiro específico
- Endpoint de migração garante que roteiros antigos tenham pelo menos uma conversa default

### Dependência de Agentes (Agent Instances)

- Conversas dependem de agentes para gerar respostas
- Cada agente participante é identificado por: `agent_id` (DB), `instance_id`, `name`, `emoji`
- O campo `active_agent` indica qual agente responderá à próxima mensagem
- O array `participants` mantém histórico de todos agentes que já interagiram
- Ao executar um agente, o sistema busca a conversa e formata o histórico para contexto

### Estado no Frontend

- ConductorChatComponent mantém `activeConversationId` como fonte de verdade
- ConversationListComponent recebe activeConversationId como Input para destacar visualmente
- Ao alternar agentes no dock, o sistema atualiza `active_agent` mas mantém `activeConversationId`
- Ao alternar conversas, todo o estado de mensagens é recarregado

## 💡 Regras de Negócio Identificadas

**RN1: Unicidade de conversation_id**
- Cada conversa deve ter um UUID único globalmente
- _Implementação_: MongoDB index único em `conversation_id` + geração via `uuid.uuid4()`

**RN2: Histórico unificado**
- Todas as mensagens de uma conversa ficam no mesmo array `messages`
- Mensagens de bot incluem metadados do agente que as gerou
- _Implementação_: Array `messages` no documento da conversa com campo `agent` em mensagens tipo "bot"

**RN3: Participantes automáticos**
- Ao adicionar uma mensagem de bot, o agente é automaticamente incluído nos participantes se ainda não estiver
- _Implementação_: Método `_add_participant()` verifica duplicatas antes de adicionar

**RN4: Ordenação por recência**
- Conversas devem ser listadas da mais recente para a mais antiga
- O campo `updated_at` é atualizado toda vez que uma mensagem é adicionada ou agente é trocado
- _Implementação_: Listagem usa `.sort("updated_at", -1)` no MongoDB

**RN5: Título automático**
- Se não fornecido, o título da conversa é gerado no formato "Conversa YYYY-MM-DD HH:MM"
- _Implementação_: `conversation_service.py` linha 98: `datetime.utcnow().strftime('%Y-%m-%d %H:%M')`

**RN6: Soft deletion**
- Atualmente conversas são deletadas permanentemente (hard delete)
- _Implementação_: `delete_one()` remove documento do MongoDB

**RN7: Paginação padrão**
- Listagem de conversas retorna no máximo 20 por padrão (configurável)
- _Implementação_: Parâmetro `limit` com valor default 20 e máximo 100 na API

**RN8: Feature flag controlada**
- O sistema pode operar nos dois modelos (antigo instance_id e novo conversation_id)
- _Implementação_: `environment.features.useConversationModel` no Angular determina qual lógica usar

**RN9: Compatibilidade legacy**
- ConversationService mantém métodos para o modelo antigo durante período de transição
- _Implementação_: Métodos `*_legacy` que acessam collection `agent_conversations`

**RN10: Timestamps UTC**
- Todas as datas/horas são armazenadas em formato ISO 8601 no timezone UTC
- _Implementação_: `datetime.utcnow().isoformat()` em todos os registros de timestamp

## 🎓 Conceitos-Chave

### Conversa vs. Histórico de Agente

**Modelo Antigo (instance_id)**:
- Cada agente tinha seu próprio histórico isolado em `agent_conversations`
- Trocar de agente significava perder o contexto anterior
- Não havia forma de múltiplos agentes colaborarem em um mesmo problema

**Modelo Novo (conversation_id)**:
- Uma conversa é uma entidade independente que pode ter múltiplos agentes
- O histórico é compartilhado entre todos os participantes
- Trocar de agente mantém o contexto completo
- Permite colaboração real entre agentes especialistas

### Agente Ativo vs. Participantes

- **Agente Ativo** (`active_agent`): O agente que responderá à próxima mensagem do usuário
- **Participantes** (`participants`): Lista de todos os agentes que já contribuíram na conversa
- Um agente pode estar nos participantes mas não ser o ativo no momento

### Mensagens Tipadas

Cada mensagem possui um campo `type`:
- **"user"**: Mensagem enviada pelo usuário humano (não possui campo `agent`)
- **"bot"**: Mensagem gerada por um agente de IA (possui campo `agent` com metadados)

### Feature Flag

`environment.features.useConversationModel`:
- Booleano que controla qual modelo de conversas usar
- Permite rollout gradual e rollback rápido se necessário
- Quando `true`: usa novo modelo com conversation_id
- Quando `false`: usa modelo legacy com instance_id

### Filtro por Roteiro

Conversas podem ser filtradas por `screenplay_id`:
- Permite organizar conversas por contexto de projeto/trabalho
- Útil quando usuário está trabalhando em múltiplos roteiros simultaneamente
- Implementado como query parameter opcional em `GET /conversations/`

## 📌 Observações

### Migração de Dados

O sistema inclui scripts de migração para converter históricos antigos:
- `normalize_tasks_add_conversation_id.py`: Adiciona campo conversation_id em tasks
- `migrate_histories_to_conversations.py`: Migra agent_conversations → conversations
- Endpoint `POST /conversations/migrate-screenplays`: Normaliza roteiros antigos

### Estado de Implementação

**Implementado (✅)**:
- Collection conversations no MongoDB
- ConversationService completo no backend
- Endpoints de API no conductor e proxy no gateway
- ConversationService Angular no frontend
- ConversationListComponent com UI completa
- Integração no ConductorChatComponent
- Feature flag funcional

**Próximos passos sugeridos (📋)**:
- Melhorias de UX: filtro de mensagens por agente
- Mensagens-resumo (milestones) recolhíveis
- Recolhimento automático de blocos de código/log
- Diferenciação visual mais forte entre agentes
- Busca de conversas por conteúdo
- Exportar conversa completa (PDF, Markdown)

### Arquivos de Referência

Para aprofundamento técnico:
- `docs/PLANO_REFATORACAO_CONVERSATION_ID.md`: Plano original detalhado
- `docs/IMPLEMENTACAO_CONVERSATION_ID.md`: Documentação técnica completa
- `docs/README_CONVERSATION_ID.md`: Guia navegacional da documentação
- `docs/GUIA_APLICACAO_PATCH_FRONTEND.md`: Como aplicar mudanças no frontend
- `docs/CHECKLIST_VALIDACAO.md`: Como validar a implementação

### Modelo de Dados - Collection `conversations`

```javascript
{
  "_id": ObjectId("..."),
  "conversation_id": "uuid-v4",             // Identificador único global
  "title": "Conversa 2025-11-02 10:30",    // Título da conversa
  "created_at": "2025-11-02T10:30:00Z",    // Timestamp de criação (ISO 8601 UTC)
  "updated_at": "2025-11-02T11:45:00Z",    // Timestamp da última atualização
  "screenplay_id": "screenplay-uuid",       // ID do roteiro (opcional, pode ser null)
  "active_agent": {                         // Agente que responderá próxima mensagem
    "agent_id": "agent-db-id",
    "instance_id": "instance-uuid",
    "name": "Code Expert",
    "emoji": "💻"
  },
  "participants": [                         // Lista de todos agentes que participaram
    {
      "agent_id": "agent-db-id",
      "instance_id": "instance-uuid",
      "name": "Code Expert",
      "emoji": "💻"
    },
    {
      "agent_id": "agent-db-id-2",
      "instance_id": "instance-uuid-2",
      "name": "Database Specialist",
      "emoji": "🗄️"
    }
  ],
  "messages": [                             // Array unificado de mensagens
    {
      "id": "msg-uuid-1",
      "type": "user",
      "content": "Como faço para otimizar esta query?",
      "timestamp": "2025-11-02T10:31:00Z"
    },
    {
      "id": "msg-uuid-2",
      "type": "bot",
      "content": "Vou analisar a query. Primeiro...",
      "timestamp": "2025-11-02T10:31:15Z",
      "agent": {                             // Presente apenas em mensagens de bot
        "agent_id": "agent-db-id",
        "instance_id": "instance-uuid",
        "name": "Code Expert",
        "emoji": "💻"
      }
    },
    {
      "id": "msg-uuid-3",
      "type": "user",
      "content": "E quanto ao índice do MongoDB?",
      "timestamp": "2025-11-02T11:40:00Z"
    },
    {
      "id": "msg-uuid-4",
      "type": "bot",
      "content": "Recomendo criar índices compostos...",
      "timestamp": "2025-11-02T11:45:00Z",
      "agent": {
        "agent_id": "agent-db-id-2",
        "instance_id": "instance-uuid-2",
        "name": "Database Specialist",
        "emoji": "🗄️"
      }
    }
  ]
}
```

**Índices criados:**
- `conversation_id` (unique): Chave primária
- `participants.agent_id`: Buscar conversas por participante
- `updated_at`: Ordenação por recência
- `screenplay_id`: Filtrar conversas por roteiro

---

**Documento criado em:** 2025-11-02
**Versão:** 1.0
**Autor:** Engenheiro de Requisitos (Claude)
**Propósito:** Contextualizar futuras interações sobre a funcionalidade de Conversas no Conductor
