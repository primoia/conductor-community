# Plano de Refatoração: De `instance_id` para `conversation_id`

**Autor:** Gemini
**Data:** 2025-11-01
**Status:** Proposto

## 1. Visão Geral e Objetivos

Este documento descreve o plano para refatorar o núcleo do sistema de chat do Conductor, migrando de um modelo de controle de histórico centrado no `instance_id` de cada agente para um modelo centrado em um `conversation_id` global.

**Objetivos de Negócio:**
- Habilitar a colaboração de múltiplos agentes especialistas em uma única linha de raciocínio.
- Manter um histórico de auditoria completo e unificado para tarefas complexas.
- Evoluir a plataforma de uma ferramenta de "chat com IA" para uma de "resolução de problemas colaborativa".

**Objetivos Técnicos:**
- Desacoplar o histórico de mensagens da instância do agente.
- Criar uma arquitetura de dados mais limpa, robusta e escalável.
- Simplificar o gerenciamento de estado no frontend.
- Estabelecer uma base para futuras funcionalidades de UX (filtros, resumos, etc.).

---

## 2. Arquitetura Proposta

A nova arquitetura se baseia em uma nova entidade no banco de dados: `conversations`.

- **Coleção `conversations` (MongoDB):**
  - `_id`: `conversation_id` (UUID)
  - `title`: Título da conversa.
  - `created_at`, `updated_at`: Timestamps.
  - `active_agent`: Metadados do agente selecionado para a próxima resposta.
  - `participants`: Lista de agentes que já participaram da conversa.
  - `messages`: **Array único** contendo todas as mensagens (de usuários e de bots).
    - Cada mensagem de bot contém um objeto `agent` para identificar seu autor.

- **Novos Endpoints de API (via Gateway):**
  - `POST /api/conversations`: Cria uma nova conversa.
  - `GET /api/conversations/{id}`: Obtém o histórico completo de uma conversa.
  - `POST /api/conversations/{id}/messages`: Envia uma nova mensagem para a conversa, especificando o agente executor.
  - `PUT /api/conversations/{id}/active-agent`: Altera o agente ativo para a próxima resposta.

---

## 3. Fases da Implementação

A implementação será dividida em 4 fases para mitigar riscos e permitir testes incrementais.

- **Fase 1: Fundação do Backend.** Construir o novo modelo e as APIs no `conductor` e `conductor-gateway`, mantendo as APIs antigas funcionando em paralelo.
- **Fase 2: Integração do Frontend.** Refatorar o `conductor-web` para usar as novas APIs. A nova lógica pode ser ativada via feature flag.
- **Fase 3: Migração de Dados.** Criar e executar um script para migrar os históricos existentes da coleção `agent_history` para a nova coleção `conversations`.
- **Fase 4: Limpeza e Deprecação.** Após a validação completa do novo sistema, remover as APIs, código e coleções de banco de dados legadas.

---

## 4. Detalhamento das Tarefas por Projeto

### Fase 1: Fundação do Backend

####  проект `conductor`
1.  **Modelo de Dados:**
    -   Definir o novo schema para a coleção `conversations` no MongoDB.
2.  **Camada de Serviço (`ConversationService`):**
    -   Criar `src/core/services/conversation_service.py`.
    -   Implementar a classe `ConversationService` com os métodos:
        -   `create_conversation(...)`
        -   `get_conversation_by_id(...)`
        -   `add_message(conversation_id, user_input, agent_instance_id, ...)`
        -   `set_active_agent(conversation_id, agent_instance_id, ...)`
3.  **Modificação do Core:**
    -   Ajustar a função `execute_agent` para que ela receba o histórico de mensagens como um parâmetro, em vez de buscá-lo no banco de dados. A lógica de carregar a persona do agente via `PromptEngine` continua a mesma.
4.  **Camada de API:**
    -   Criar um novo arquivo de rotas: `src/api/routes/conversations.py`.
    -   Implementar os endpoints FastAPI que utilizam o `ConversationService`.

#### проект `conductor-gateway`
1.  **Roteamento:**
    -   Adicionar as novas rotas (`/api/conversations/...`) ao gateway.
    -   Configurar o proxy para encaminhar as requisições para os novos endpoints do serviço `conductor`.

### Fase 2: Integração do Frontend

#### проект `conductor-web`
1.  **Feature Flag:**
    -   Implementar uma feature flag (ex: `useConversationModel`) no `environment.ts` para permitir alternar entre a lógica antiga e a nova durante o desenvolvimento.
2.  **Camada de Serviço:**
    -   Criar `src/app/services/conversation.service.ts`.
    -   Implementar os métodos para chamar os novos endpoints: `getConversation`, `createConversation`, `sendMessage`, etc.
3.  **Refatoração do Componente de Chat:**
    -   Em `conductor-chat.component.ts`:
        -   Remover a dependência do mapa `chatHistories`.
        -   Gerenciar um estado mais simples: `activeConversationId` e `messages: Message[]`.
        -   Adaptar os métodos `loadContext...` e `handleSendMessage` para usar o novo `ConversationService`.
        -   A lógica de troca de agente (`onDockAgentClick`) agora chamará `conversationService.setActiveAgent` e **não** recarregará mais o histórico.
4.  **Ajustes de UI:**
    -   Garantir que cada mensagem de bot exiba o nome e emoji do agente que a gerou, usando os dados do campo `message.agent`.

### Fase 3: Migração de Dados

1.  **Script de Migração:**
    -   Criar um script em Python (`scripts/migrate_histories_to_conversations.py`) no projeto `conductor`.
    -   **Lógica:**
        1.  Iterar sobre todos os `instance_id` distintos na coleção `agent_history`.
        2.  Para cada `instance_id`, criar um novo documento na coleção `conversations`.
        3.  Copiar e transformar as mensagens do formato antigo para o novo array `messages`.
        4.  Preencher os metadados da nova conversa (título, `created_at`, etc.).
        5.  Marcar o histórico antigo como migrado.

### Fase 4: Limpeza e Deprecação

1.  **Backend (`conductor` e `gateway`):**
    -   Remover os endpoints legados relacionados a `getAgentContext`.
    -   Remover a lógica antiga de busca de histórico dentro de `execute_agent`.
    -   Arquivar ou remover a coleção `agent_history` do MongoDB.
2.  **Frontend (`conductor-web`):**
    -   Remover a feature flag `useConversationModel`.
    -   Remover o código legado do `conductor-chat.component.ts` (gerenciamento do `chatHistories`).
    -   Remover métodos não utilizados do `agent.service.ts`.

---

## 5. Estratégia de Testes

1.  **Testes Unitários (Backend):**
    -   Testar todos os métodos do `ConversationService` de forma isolada.
2.  **Testes de API (Backend/Gateway):**
    -   Criar testes de integração para os novos endpoints `/api/conversations`.
3.  **Testes de Componente (Frontend):**
    -   Testar a nova lógica do `conductor-chat.component` com um `ConversationService` mockado.
4.  **Testes End-to-End (E2E):**
    -   Criar um cenário de teste completo:
        1.  Usuário inicia uma conversa.
        2.  Envia mensagem para o Agente A.
        3.  Troca para o Agente B.
        4.  Envia mensagem para o Agente B, que deve ter o contexto da mensagem do Agente A.
        5.  Recarrega a página e verifica se o histórico persiste corretamente.

---

## 6. Melhorias Futuras (Pós-Lançamento)

Após a estabilização da nova arquitetura, podemos implementar as seguintes melhorias de UX para gerenciar a "poluição" do histórico:

-   **Filtro de Mensagens por Agente.**
-   **Mensagens-Resumo (Milestones) recolhíveis.**
-   **Recolhimento automático de blocos de código/log.**
-   **Diferenciação visual mais forte entre mensagens de agentes diferentes.**
