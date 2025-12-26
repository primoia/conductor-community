# Requisitos de Estado da URL - Conductor

Este documento define todos os fluxos de navegação e comportamentos esperados para sincronização de estado via URL.

## Parâmetros da URL

```
http://localhost:8080/screenplay?screenplayId=XXX&conversationId=YYY&instanceId=ZZZ
```

| Parâmetro | Descrição |
|-----------|-----------|
| `screenplayId` | ID do roteiro ativo |
| `conversationId` | ID da conversa ativa |
| `instanceId` | ID do agente instanciado selecionado |

---

## ARQUITETURA: Persistência de Estado

### Problema Atual
- Estado salvo no `localStorage` do navegador
- Funciona apenas no mesmo navegador/máquina
- Ao trocar de navegador ou máquina, estado se perde

### Solução: Salvar Estado no MongoDB

O estado deve ser persistido no MongoDB via endpoint da API, vinculado ao usuário.

### Modelo de Dados

```typescript
// DOIS NÍVEIS DE ESTADO:

// 1. Estado do ROTEIRO: última conversa ativa
// Collection: screenplay_states
// Índice único: { user_id: 1, screenplay_id: 1 }
interface ScreenplayState {
  _id: ObjectId;
  user_id: string;
  screenplay_id: string;
  conversation_id: string | null;  // Última conversa ativa no roteiro
  created_at: Date;
  updated_at: Date;
}

// 2. Estado da CONVERSA: último agente ativo
// Collection: conversation_states
// Índice único: { user_id: 1, screenplay_id: 1, conversation_id: 1 }
interface ConversationState {
  _id: ObjectId;
  user_id: string;
  screenplay_id: string;
  conversation_id: string;
  instance_id: string | null;  // Último agente ativo na conversa
  created_at: Date;
  updated_at: Date;
}
```

### Endpoint da API

```
GET  /api/navigation                                        → Último roteiro + conversa + agente
GET  /api/navigation?screenplay_id=xxx                      → Conversa + agente do roteiro
GET  /api/navigation?screenplay_id=xxx&conversation_id=yyy  → Agente da conversa
GET  /api/navigation/last                                   → Último roteiro + conversa
PUT  /api/navigation                                        → Salva estado (ambas collections)
DELETE /api/navigation?screenplay_id=xxx                    → Limpa roteiro + conversas
DELETE /api/navigation?screenplay_id=xxx&conversation_id=yyy → Limpa conversa
```

**Request Body (PUT):**
```json
{
  "screenplay_id": "xxx",       // Obrigatório
  "conversation_id": "yyy",     // Salvo em screenplay_states E conversation_states
  "instance_id": "zzz"          // Salvo em conversation_states (se conversation_id fornecido)
}
```

**Response (GET/PUT):**
```json
{
  "screenplay_id": "xxx",
  "conversation_id": "yyy",
  "instance_id": "zzz",
  "updated_at": "2024-12-26T12:00:00Z"
}
```

**Response (GET /last):**
```json
{
  "screenplay_id": "xxx",
  "conversation_id": "yyy",
  "updated_at": "2024-12-26T12:00:00Z"
}
```

### Ordem de Operações (Todos os Fluxos)

```
┌─────────────────────────────────────────────────────────────────┐
│ QUALQUER MUDANÇA DE ESTADO (Fluxo 1, 2 ou 3)                   │
│                                                                 │
│ 1. SALVAR NO MONGO (prioridade máxima)                         │
│    └── PUT /api/v1/navigation-state                            │
│                                                                 │
│ 2. ATUALIZAR URL                                               │
│    └── Montar URL com parâmetros atualizados                   │
│                                                                 │
│ 3. CARREGAR DADOS (se necessário)                              │
│    ├── Roteiro                                                 │
│    ├── Conversas                                               │
│    ├── Histórico de mensagens                                  │
│    └── Agente instanciado                                      │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo de Inicialização (Página Carrega)

```
┌─────────────────────────────────────────────────────────────────┐
│ PÁGINA CARREGA                                                  │
│                                                                 │
│ 1. VERIFICAR URL                                               │
│    └── URL tem parâmetros? (screenplayId, etc.)                │
│                                                                 │
│ 2. SE URL TEM PARÂMETROS                                       │
│    ├── Usar parâmetros da URL                                  │
│    └── Salvar no MongoDB (sincronizar)                         │
│                                                                 │
│ 3. SE URL NÃO TEM PARÂMETROS                                   │
│    ├── GET /api/v1/navigation-state                            │
│    ├── Usar estado do MongoDB                                  │
│    └── Atualizar URL com parâmetros                            │
│                                                                 │
│ 4. CARREGAR DADOS                                              │
│    └── (Fluxo 1 normal)                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Prioridade de Fontes

| Prioridade | Fonte | Quando Usar |
|------------|-------|-------------|
| 1 | URL | Se URL tem parâmetros (link compartilhado, reload) |
| 2 | MongoDB | Se URL não tem parâmetros (acesso direto) |
| 3 | Último/Default | Se nem URL nem MongoDB tem estado |

### Componentes a Criar/Modificar

| Componente | Ação |
|------------|------|
| `navigation-state.service.ts` | **CRIAR** - Service Angular para gerenciar estado |
| `conductor/src/api/navigation.py` | **CRIAR** - Endpoint FastAPI |
| `conductor/src/models/navigation.py` | **CRIAR** - Modelo Pydantic |
| `screenplay-interactive.ts` | **MODIFICAR** - Usar novo service |

---

## CONSIDERAÇÕES: Concorrência

### Solução: Fila de Envio

Para cliques rápidos, usar fila que processa PUT sequencialmente:

```typescript
class NavigationStateQueue {
  private queue: NavigationState[] = [];
  private isProcessing = false;

  enqueue(state: NavigationState): void {
    this.queue.push(state);
    this.processNext();
  }

  private async processNext(): Promise<void> {
    if (this.isProcessing || this.queue.length === 0) return;

    this.isProcessing = true;
    const state = this.queue.shift()!;

    try {
      await this.http.put('/api/v1/navigation-state', state);
    } finally {
      this.isProcessing = false;
      this.processNext(); // processa próximo da fila
    }
  }
}
```

### Regras

| # | Regra | Descrição |
|---|-------|-----------|
| C.1 | Fila FIFO | Primeiro a entrar, primeiro a processar |
| C.2 | Um PUT por vez | Aguarda resposta antes de enviar próximo |
| C.3 | Múltiplas abas | Cada aba opera independente; último clique sobrescreve MongoDB |
| C.4 | Falha de rede | Se PUT falhar, tentar novamente ou descartar (definir política) |

---

## FLUXO 1: Carregar/Trocar Roteiro

### Gatilhos (Formas de Acionar)
1. **Clicar no roteiro** em `class="screenplay-tree"` (árvore de roteiros)
2. **Reload da página** (Ctrl+R / F5)
3. **Copiar URL e colar em outra aba** do navegador
4. **Clicar em evento** com `class="news-article expanded status-completed clickable"`
5. **Botão Abrir** `class="toolbar-btn open-btn"` → trocar ou importar roteiro via gerenciador

### Comportamento Esperado (Cascata)

```
┌─────────────────────────────────────────────────────────────────┐
│ ROTEIRO                                                         │
│ ├── Carrega roteiro pelo screenplayId (URL ou clique)          │
│ └── Atualiza URL com screenplayId                               │
│                                                                  │
│     ┌─────────────────────────────────────────────────────────┐ │
│     │ CONVERSAS                                               │ │
│     │ ├── Recarrega lista de conversas do roteiro             │ │
│     │ ├── Se URL tem conversationId → seleciona essa conversa │ │
│     │ └── Senão → seleciona a última conversa                 │ │
│     │                                                         │ │
│     │     ┌─────────────────────────────────────────────────┐ │ │
│     │     │ HISTÓRICO DE MENSAGENS                          │ │ │
│     │     │ └── Recarrega mensagens da conversa selecionada │ │ │
│     │     └─────────────────────────────────────────────────┘ │ │
│     │                                                         │ │
│     │     ┌─────────────────────────────────────────────────┐ │ │
│     │     │ AGENTE INSTANCIADO                              │ │ │
│     │     │ ├── Se URL tem instanceId → seleciona esse      │ │ │
│     │     │ └── Senão → seleciona o último da conversa      │ │ │
│     │     └─────────────────────────────────────────────────┘ │ │
│     └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Regras do Fluxo 1

| # | Regra | Descrição |
|---|-------|-----------|
| 1.1 | Prioridade da URL | Se `screenplayId` vem da URL, usar esse valor. Caso contrário, usar o ID do roteiro clicado. |
| 1.2 | Carregar conversas | Após carregar roteiro, sempre recarregar lista de conversas desse roteiro. |
| 1.3 | Seleção de conversa | Se `conversationId` está na URL e existe no roteiro → selecionar. Senão → selecionar última conversa. |
| 1.4 | Carregar histórico | Após selecionar conversa, carregar histórico de mensagens dessa conversa. |
| 1.5 | Seleção de agente | Se `instanceId` está na URL e pertence à conversa → selecionar. Senão → selecionar último agente da conversa. |
| 1.6 | Atualizar URL | Ao final do fluxo, URL deve refletir o estado atual (screenplayId, conversationId, instanceId). |
| 1.7 | Não sobrescrever URL prematuramente | Não atualizar URL parcialmente durante o carregamento - atualizar apenas quando estado final estiver definido. |

### Componentes Envolvidos

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| ScreenplayInteractive | `screenplay-interactive.ts` | Orquestra o fluxo, gerencia estado global |
| ScreenplayTree | `screenplay-tree.component.ts` | Emite evento de seleção de roteiro |
| ConductorChat | `conductor-chat.component.ts` | Gerencia conversas e chat |
| EventTicker | `event-ticker.component.ts` | Emite evento de clique em notícia |

---

## FLUXO 2: Trocar Conversa

### Gatilhos (Formas de Acionar)
1. **Clicar em conversa** diferente na lista de conversas (trocar de K para L)

### Contexto
- O roteiro já está carregado (não muda)
- Apenas a conversa muda dentro do mesmo roteiro

### Comportamento Esperado

```
┌─────────────────────────────────────────────────────────────────┐
│ CONVERSA (clique para trocar de K → L)                         │
│ ├── Atualiza URL com novo conversationId                       │
│ ├── Carrega histórico de mensagens da conversa L               │
│ │                                                               │
│ └── AGENTE INSTANCIADO                                         │
│     ├── Se conversa L tem agente selecionado → manter          │
│     └── Senão → selecionar último agente da conversa L         │
│                                                                 │
│ └── Atualiza URL com instanceId do agente selecionado          │
└─────────────────────────────────────────────────────────────────┘
```

### Regras do Fluxo 2

| # | Regra | Descrição |
|---|-------|-----------|
| 2.1 | Roteiro não muda | O `screenplayId` permanece o mesmo na URL. |
| 2.2 | Atualizar conversationId | URL deve refletir a nova conversa selecionada. |
| 2.3 | Carregar histórico | Recarregar mensagens da nova conversa no chat. |
| 2.4 | Seleção de agente | Se a nova conversa não tem agente selecionado, selecionar o último agente dessa conversa. |
| 2.5 | Atualizar instanceId | URL deve refletir o agente instanciado da nova conversa. |
| 2.6 | Conversa sem agentes | Se a conversa não tem agentes, `instanceId` deve ser removido da URL. |

### Componentes Envolvidos

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| ConductorChat | `conductor-chat.component.ts` | Emite evento de troca de conversa, carrega histórico |
| ScreenplayInteractive | `screenplay-interactive.ts` | Recebe evento, atualiza URL, seleciona agente |

---

## FLUXO 3: Clicar no Agente Instanciado

### Gatilhos (Formas de Acionar)
1. **Clicar em agente instanciado** no dock de agentes

### Contexto
- O roteiro já está carregado (não muda)
- A conversa já está selecionada (não muda)
- Apenas o agente instanciado muda

### Comportamento Esperado

```
┌─────────────────────────────────────────────────────────────────┐
│ AGENTE INSTANCIADO (clique para selecionar)                    │
│ ├── Atualiza URL com novo instanceId                           │
│ ├── Marca agente como ativo visualmente (class="active")       │
│ └── NÃO recarrega histórico de mensagens                       │
└─────────────────────────────────────────────────────────────────┘
```

### Regras do Fluxo 3

| # | Regra | Descrição |
|---|-------|-----------|
| 3.1 | Roteiro não muda | O `screenplayId` permanece o mesmo na URL. |
| 3.2 | Conversa não muda | O `conversationId` permanece o mesmo na URL. |
| 3.3 | Atualizar instanceId | URL deve refletir o novo agente instanciado selecionado. |
| 3.4 | Não recarregar histórico | O histórico de mensagens já está carregado, não recarregar. |
| 3.5 | Feedback visual | Agente clicado deve receber `class="active"` no dock. |

### Componentes Envolvidos

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| ConductorChat | `conductor-chat.component.ts` | Renderiza dock de agentes, emite evento de clique |
| ScreenplayInteractive | `screenplay-interactive.ts` | Recebe evento, atualiza URL e estado |

---

## FLUXO 4: (Aguardando definição)

*Próximo fluxo a ser documentado...*

---

## Histórico de Alterações

| Data | Descrição |
|------|-----------|
| 2024-12-26 | Documento criado. Fluxo 1 documentado. |
