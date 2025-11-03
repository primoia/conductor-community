# Funcionalidade de Conversas e Relacionamento com Screenplay

## 📋 Visão Geral

A funcionalidade de conversas implementa um modelo de **conversas globais** onde múltiplos agentes podem participar de uma mesma linha de raciocínio. Cada conversa está vinculada a um **screenplay** (roteiro), que fornece o contexto narrativo para os agentes.

**Contexto do Problema Reportado:**
- Screenplay ID: `69076492ef4831565adae786`
- Conversa: "Roteiro 11:02"
- Agente instanciado: `instance-1762106538195-l43bafuhv`
- **Problema:** Histórico do chat não está vazio quando deveria estar
- **Causa raiz:** Faltam filtros `isDeleted` em queries críticas

---

## 🎯 Requisitos Identificados

### Requisitos Funcionais

**RF1: Gerenciar Conversas Independentes**
- O sistema deve permitir criar conversas independentes de agentes específicos
- Cada conversa possui um `conversation_id` único (UUID)
- Uma conversa pode ter múltiplos agentes participantes

**RF2: Vincular Conversas a Screenplays**
- Cada conversa deve estar vinculada a um screenplay através do campo `screenplay_id`
- O screenplay fornece o contexto narrativo (conteúdo markdown) para os agentes
- Quando um screenplay é deletado (soft delete), suas conversas devem continuar acessíveis mas sem contexto

**RF3: Filtrar Recursos Deletados (Soft Delete)**
- O sistema deve respeitar a flag `isDeleted` em todas as queries
- Screenplays deletados não devem ser carregados no contexto dos prompts
- Agent instances órfãos (vinculados a screenplays deletados) devem ser identificados

**RF4: Carregar Contexto de Screenplay nos Prompts**
- O `PromptEngine` deve carregar o conteúdo textual do screenplay
- O texto do screenplay deve ser incluído no prompt enviado ao LLM
- Apenas screenplays **ativos** (não deletados) devem ser carregados

**RF5: Limpar Instâncias Órfãs**
- O sistema deve identificar agent instances sem screenplay válido
- Deve haver ferramentas para limpar instances órfãs automaticamente

### Requisitos Não-Funcionais

**RNF1: Integridade de Dados**
- Todas as queries devem filtrar recursos com `isDeleted = true`
- Queries devem ser consistentes em todo o sistema

**RNF2: Performance**
- Queries devem usar índices apropriados (`screenplay_id`, `conversation_id`)
- Histórico de mensagens deve ser paginado para evitar sobrecarga

---

## 🔄 Fluxo do Processo

### 1. Criação de Conversa

**Início:** Usuário cria uma nova conversa a partir de um screenplay

1. Frontend chama `POST /conversations/` com `screenplay_id` e `title`
2. `ConversationService.create_conversation()` gera um `conversation_id` único
3. Documento é criado na collection `conversations` com:
   - `conversation_id` (UUID)
   - `screenplay_id` (vínculo com roteiro)
   - `title`, `created_at`, `updated_at`
   - `participants` (lista vazia inicialmente)
   - `messages` (lista vazia)

**Finalização:** Conversa criada e vinculada ao screenplay

---

### 2. Envio de Mensagem em uma Conversa

**Início:** Usuário envia mensagem para um agente em uma conversa

1. Frontend chama `POST /conversations/{conversation_id}/messages`
2. `ConversationService.add_message()` adiciona mensagens do tipo `user` e `bot`
3. Se for resposta de agente, adiciona metadados do agente (`agent_id`, `instance_id`, `name`, `emoji`)
4. Agente é adicionado à lista de `participants` se ainda não estiver presente

**Finalização:** Mensagens armazenadas no histórico da conversa

---

### 3. Carregamento de Contexto do Screenplay pelo PromptEngine

**Início:** Agente precisa processar uma mensagem

1. `PromptEngine.__init__()` recebe `instance_id`
2. `PromptEngine.load_context()` chama `_load_screenplay_context()`
3. **Query 1:** Busca `agent_instances.find_one({"instance_id": instance_id})` para obter `screenplay_id`
4. **Query 2 (PROBLEMA):** Busca `screenplays.find_one({"_id": ObjectId(screenplay_id)})`
   - ❌ **FALTA FILTRO:** `{"isDeleted": {"$ne": True}}`
5. Se screenplay encontrado, carrega campo `content` (texto markdown)
6. Texto do screenplay é incluído no prompt XML/texto enviado ao LLM

**Finalização:** Prompt construído com contexto do screenplay

**⚠️ PROBLEMA IDENTIFICADO:**
- A query na linha `prompt_engine.py:349` **não filtra screenplays deletados**
- Isso faz com que agentes carreguem contexto de roteiros que foram deletados pelo usuário
- **Impacto:** Agentes podem usar informações desatualizadas ou inválidas

---

### 4. Limpeza de Instâncias Órfãs

**Início:** Script de limpeza é executado

1. `cleanup_orphan_instances.py` busca todas as agent_instances
2. **Query (PROBLEMA):** Busca todos os screenplays válidos com `screenplays.find({}, {'id': 1})`
   - ❌ **FALTA FILTRO:** `{"isDeleted": {"$ne": True}}`
3. Compara `screenplay_id` de cada instance com lista de screenplays válidos
4. Identifica instances órfãs (sem screenplay ou screenplay inexistente)
5. Remove instances órfãs se não for modo dry-run

**Finalização:** Instances órfãs deletadas

**⚠️ PROBLEMA IDENTIFICADO:**
- A query na linha `cleanup_orphan_instances.py:51` **inclui screenplays deletados**
- Isso faz com que instances vinculadas a screenplays deletados **não sejam identificadas como órfãs**
- **Impacto:** Instances ficam no banco sem screenplay válido, consumindo recursos

---

## 🏗️ Componentes Principais

### Backend (Python)

#### 1. **ConversationService** (`src/core/services/conversation_service.py`)
- **Responsabilidade:** CRUD de conversas globais
- **Métodos principais:**
  - `create_conversation()`: Cria nova conversa vinculada a screenplay
  - `get_conversation_by_id()`: Busca conversa por UUID
  - `add_message()`: Adiciona mensagens (user/bot) ao histórico
  - `set_active_agent()`: Define agente ativo para próxima resposta
  - `list_conversations()`: Lista conversas com filtro por `screenplay_id`
- **Collection MongoDB:** `conversations`
- **Índices criados:** `conversation_id` (unique), `participants.agent_id`, `updated_at`, `screenplay_id`

#### 2. **PromptEngine** (`src/core/prompt_engine.py`)
- **Responsabilidade:** Carregar contexto completo do agente e construir prompts
- **Métodos principais:**
  - `load_context()`: Carrega definition, persona, playbook e **screenplay**
  - `_load_screenplay_context()`: Busca screenplay vinculado à instance (⚠️ **SEM FILTRO isDeleted**)
  - `build_xml_prompt()`: Constrói prompt XML com contexto do screenplay
- **⚠️ PROBLEMA:** Linha 349 não filtra `isDeleted`

#### 3. **Conversas API** (`src/api/routes/conversations.py`)
- **Responsabilidade:** Endpoints REST para conversas
- **Endpoints:**
  - `POST /conversations/` - Criar conversa
  - `GET /conversations/{id}` - Obter conversa completa
  - `GET /conversations/` - Listar conversas (filtro por screenplay_id)
  - `POST /conversations/{id}/messages` - Adicionar mensagem
  - `PUT /conversations/{id}/active-agent` - Alterar agente ativo
  - `DELETE /conversations/{id}` - Deletar conversa
  - `POST /conversations/migrate-screenplays` - Migração de dados

#### 4. **Cleanup Tool** (`src/conductor-gateway/src/tools/cleanup_orphan_instances.py`)
- **Responsabilidade:** Identificar e remover agent_instances órfãos
- **⚠️ PROBLEMA:** Linha 51 não filtra screenplays deletados ao buscar IDs válidos

---

### Frontend (Angular)

*Nota: Análise focada no backend conforme solicitado. Frontend interage via APIs REST.*

---

## 🔗 Relacionamentos e Dependências

### Modelo de Dados

```
┌─────────────────────────┐
│   screenplays           │
│  ───────────────────    │
│  _id: ObjectId          │◄────┐
│  name: string           │     │
│  content: string        │     │ screenplay_id
│  isDeleted: boolean     │     │
│  created_at: datetime   │     │
└─────────────────────────┘     │
                                │
                                │
┌─────────────────────────┐     │
│   conversations         │     │
│  ───────────────────    │     │
│  conversation_id: UUID  │     │
│  title: string          │     │
│  screenplay_id: str ────┼─────┘
│  messages: array        │
│  participants: array    │
│  active_agent: object   │
└─────────────────────────┘
         ▲
         │ conversation_id
         │
┌─────────────────────────┐
│   agent_instances       │
│  ───────────────────    │
│  instance_id: string    │
│  agent_id: string       │
│  screenplay_id: str ────┼────► (vincula a screenplay)
│  conversation_id: UUID  │
└─────────────────────────┘
```

### Dependências de Query

**PromptEngine → screenplays:**
```python
# src/core/prompt_engine.py:349
screenplay_doc = db.screenplays.find_one({"_id": ObjectId(screenplay_id)})
# ❌ FALTA: {"_id": ObjectId(screenplay_id), "isDeleted": {"$ne": True}}
```

**Cleanup Tool → screenplays:**
```python
# cleanup_orphan_instances.py:51
for screenplay in screenplays.find({}, {'id': 1, '_id': 0}):
# ❌ FALTA: screenplays.find({"isDeleted": {"$ne": True}}, {'id': 1, '_id': 0})
```

**Conversas API → screenplays:**
- Relação através do campo `screenplay_id`
- Conversas podem ser filtradas por screenplay
- ✅ Não há problema nas queries de conversas

---

## 💡 Regras de Negócio Identificadas

### Regra 1: Soft Delete de Screenplays
**Descrição:** Screenplays não são deletados fisicamente, apenas marcados com `isDeleted = true`

**Implementação:**
- Campo `isDeleted` na collection `screenplays` (padrão `false`)
- Modelo Pydantic `ScreenplayUpdate` suporta atualizar `isDeleted`
- **⚠️ PROBLEMA:** Queries não filtram este campo consistentemente

### Regra 2: Contexto de Screenplay no Prompt
**Descrição:** O texto markdown do screenplay deve ser incluído no prompt do agente para fornecer contexto narrativo

**Implementação:**
- `PromptEngine._load_screenplay_context()` busca campo `content` do screenplay
- Conteúdo é incluído na tag `<screenplay>` no prompt XML
- **⚠️ PROBLEMA:** Screenplays deletados são carregados incorretamente

### Regra 3: Conversas Vinculadas a Screenplays
**Descrição:** Toda conversa deve estar vinculada a um screenplay válido

**Implementação:**
- Campo `screenplay_id` na collection `conversations`
- Índice criado para performance: `conversations.screenplay_id`
- Endpoint de listagem suporta filtro por `screenplay_id`

### Regra 4: Instâncias Órfãs Devem Ser Limpas
**Descrição:** Agent instances sem screenplay válido devem ser identificados e removidos

**Implementação:**
- Script `cleanup_orphan_instances.py` compara instances com screenplays válidos
- **⚠️ PROBLEMA:** Não considera screenplays deletados como inválidos

### Regra 5: Histórico de Mensagens Não Deve Incluir Deletadas
**Descrição:** Mensagens marcadas com `isDeleted` não devem aparecer no histórico

**Implementação:**
- ✅ `PromptEngine._format_history()` filtra mensagens deletadas (linha 424)
- ✅ `PromptEngine._format_history_xml()` filtra mensagens deletadas (linha 514)

---

## 🎓 Conceitos-Chave

### Conversation (Conversa)
Uma **conversa global** é uma linha de raciocínio compartilhada entre múltiplos agentes. Diferente do modelo antigo onde cada instância de agente tinha seu próprio histórico isolado, agora múltiplos agentes podem colaborar na mesma conversa.

**Campos principais:**
- `conversation_id`: UUID único
- `screenplay_id`: Vínculo com roteiro
- `messages`: Histórico de mensagens (user/bot)
- `participants`: Lista de agentes que participaram

### Screenplay (Roteiro)
Um **screenplay** é um documento markdown que define o contexto narrativo para os agentes. Ele contém instruções, cenários, objetivos e informações que devem ser carregadas no prompt.

**Campos principais:**
- `_id`: ObjectId do MongoDB
- `name`: Nome do roteiro
- `content`: Texto markdown completo
- `isDeleted`: Flag de soft delete

### Agent Instance (Instância de Agente)
Uma **instância de agente** é uma "execução" específica de um agente. Cada instância está vinculada a um screenplay e a uma conversa.

**Campos principais:**
- `instance_id`: ID único da instância
- `agent_id`: ID do agente (definition)
- `screenplay_id`: Vínculo com roteiro
- `conversation_id`: Vínculo com conversa

### Soft Delete
**Soft delete** é uma técnica onde recursos não são removidos fisicamente do banco de dados, mas marcados como deletados através de uma flag (`isDeleted = true`). Isso permite:
- Recuperação de dados
- Auditoria
- Cascata de deleção controlada

---

## 📌 Observações e Recomendações

### 🔴 PROBLEMA CRÍTICO 1: PromptEngine Carrega Screenplays Deletados

**Arquivo:** `src/conductor/src/core/prompt_engine.py:349`

**Código atual:**
```python
screenplay_doc = db.screenplays.find_one({"_id": ObjectId(screenplay_id)})
```

**Código correto:**
```python
screenplay_doc = db.screenplays.find_one({
    "_id": ObjectId(screenplay_id),
    "isDeleted": {"$ne": True}
})
```

**Impacto:**
- Agentes carregam contexto de screenplays que foram deletados pelo usuário
- Pode causar confusão, comportamento inesperado e uso de informações desatualizadas
- No caso reportado, isso pode estar causando o histórico não-vazio

**Prioridade:** 🔴 ALTA

---

### 🔴 PROBLEMA CRÍTICO 2: Cleanup Não Identifica Instâncias de Screenplays Deletados

**Arquivo:** `src/conductor-gateway/src/tools/cleanup_orphan_instances.py:51`

**Código atual:**
```python
for screenplay in screenplays.find({}, {'id': 1, '_id': 0}):
    valid_screenplay_ids.add(screenplay.get('id'))
```

**Código correto:**
```python
for screenplay in screenplays.find({"isDeleted": {"$ne": True}}, {'id': 1, '_id': 0}):
    valid_screenplay_ids.add(screenplay.get('id'))
```

**Impacto:**
- Instâncias vinculadas a screenplays deletados não são identificadas como órfãs
- Consumo desnecessário de recursos no banco de dados
- Possível confusão ao listar instâncias ativas

**Prioridade:** 🔴 ALTA

---

### 🟡 OBSERVAÇÃO 3: Relação Conversation ↔ Screenplay É Unidirecional

**Situação atual:**
- Conversations têm `screenplay_id` (conversation → screenplay)
- Screenplays **não sabem** quais conversas estão vinculadas a eles

**Implicação:**
- Quando um screenplay é deletado, não há cascata automática para conversas
- Conversas continuam existindo com `screenplay_id` de um screenplay deletado
- Isso pode ser intencional (manter histórico) ou um problema (dados órfãos)

**Recomendação:**
- Se conversas devem ser deletadas junto com screenplay: implementar cascata de soft delete
- Se conversas devem ser preservadas: documentar claramente este comportamento

**Prioridade:** 🟡 MÉDIA

---

### 🟢 PONTO POSITIVO: Filtro de Mensagens Deletadas

**Arquivo:** `src/conductor/src/core/prompt_engine.py:424` e `514`

O `PromptEngine` corretamente filtra mensagens marcadas como deletadas antes de construir o histórico:

```python
active_history = [turn for turn in history if not turn.get("isDeleted", False)]
```

Isso garante que mensagens deletadas não apareçam no contexto do LLM.

---

### 🔵 SUGESTÃO: Índice Composto para Performance

**Problema potencial:**
Queries que filtram por `screenplay_id` E `isDeleted` podem se beneficiar de índice composto.

**Recomendação:**
```python
db.screenplays.create_index([("screenplay_id", 1), ("isDeleted", 1)])
```

**Prioridade:** 🔵 BAIXA (otimização futura)

---

## ✅ Checklist de Correções

Para resolver o problema reportado:

- [ ] **Corrigir `prompt_engine.py:349`**: Adicionar filtro `isDeleted: {$ne: True}`
- [ ] **Corrigir `cleanup_orphan_instances.py:51`**: Adicionar filtro `isDeleted: {$ne: True}`
- [ ] **Testar cenário reportado:**
  - [ ] Criar screenplay
  - [ ] Criar conversa vinculada ao screenplay
  - [ ] Instanciar agente na conversa
  - [ ] Deletar screenplay (soft delete)
  - [ ] Verificar que histórico fica vazio
  - [ ] Verificar que cleanup identifica instance como órfã
- [ ] **Adicionar testes unitários** para garantir que queries filtram `isDeleted`
- [ ] **Documentar comportamento** de conversas quando screenplay é deletado

---

## 📚 Arquivos Relevantes

| Arquivo | Linha | Descrição |
|---------|-------|-----------|
| `src/conductor/src/core/prompt_engine.py` | 349 | ❌ Query sem filtro isDeleted |
| `src/conductor-gateway/src/tools/cleanup_orphan_instances.py` | 51 | ❌ Query sem filtro isDeleted |
| `src/core/services/conversation_service.py` | - | ✅ Serviço de conversas (OK) |
| `src/api/routes/conversations.py` | - | ✅ API de conversas (OK) |
| `src/conductor-gateway/src/models/screenplay.py` | 136 | ✅ Modelo define isDeleted |

---

## 🔍 Diagnóstico do Problema Reportado

### Cenário:
- Screenplay: `69076492ef4831565adae786`
- Conversa: "Roteiro 11:02"
- Agente: `instance-1762106538195-l43bafuhv`
- **Expectativa:** Histórico vazio (agente recém-criado)
- **Realidade:** Histórico não vazio

### Possíveis Causas:

1. **Screenplay foi deletado (soft delete)** mas ainda está sendo carregado pelo `PromptEngine`
   - Verificar: `db.screenplays.find_one({"_id": ObjectId("69076492ef4831565adae786")})` → campo `isDeleted`

2. **Conversas antigas não foram migradas corretamente**
   - Verificar: `db.conversations.find({"screenplay_id": "69076492ef4831565adae786"})`
   - Pode haver múltiplas conversas para o mesmo screenplay

3. **Agent instance está vinculado à conversa errada**
   - Verificar: `db.agent_instances.find_one({"instance_id": "instance-1762106538195-l43bafuhv"})` → campo `conversation_id`

### Próximos Passos:

1. Executar queries de diagnóstico para confirmar causa
2. Aplicar correções nos dois arquivos identificados
3. Rodar script de cleanup para identificar órfãos
4. Testar novamente o cenário

---

**Documento gerado em:** 2025-11-02
**Versão:** 1.0
