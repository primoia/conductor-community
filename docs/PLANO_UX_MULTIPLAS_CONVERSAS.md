# Plano UX: Múltiplas Conversas Paralelas

**Data:** 2025-11-02
**Status:** Proposto

## 1. Visão Geral

Permitir que o usuário gerencie **múltiplas conversas paralelas**, onde cada conversa pode ter múltiplos agentes colaborando.

### Objetivos de UX:
- ✅ Criar N conversas simultâneas (botão "+")
- ✅ Alternar entre conversas ativas
- ✅ Trocar agente ANTES de enviar mensagem (dropdown)
- ✅ Ver histórico completo de cada conversa
- ✅ Deletar conversas antigas

---

## 2. Arquitetura de UI Proposta

```
┌─────────────────────────────────────────────────────────┐
│                    SCREENPLAY EDITOR                     │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌──────────────┐  ┌──────────────────────────────────────┐
│ CONVERSAS    │  │ CHAT ATIVA                           │
│              │  │                                      │
│ [+ Nova]     │  │ 📝 Conversa 1                       │
│              │  │ Agente: [🤖 Agente A ▼]             │
│ 📝 Conv 1 ✓  │  │                                      │
│ 💼 Conv 2    │  │ ┌────────────────────────────────┐  │
│ 🔧 Conv 3    │  │ │ User: Olá!                    │  │
│              │  │ │ 🤖 A: Como posso ajudar?      │  │
│ [Delete]     │  │ │ User: Mude para Agente B      │  │
│              │  │ │ 👨 B: Olá, vi o contexto...   │  │
└──────────────┘  │ └────────────────────────────────┘  │
                  │                                      │
                  │ [Input de mensagem]           [Send] │
                  └──────────────────────────────────────┘
```

---

## 3. Componentes Necessários

### 3.1. ConversationListComponent (NOVO)

**Localização:** `src/app/shared/conversation-list/`

**Responsabilidades:**
- Listar todas as conversas do usuário
- Botão "+" para criar nova conversa
- Selecionar conversa ativa
- Deletar conversa
- Mostrar preview (título, última mensagem, contagem)

**Interface:**
```typescript
interface ConversationListItem {
  conversation_id: string;
  title: string;
  last_message_preview?: string;
  message_count: number;
  participant_emojis: string[];  // ["🤖", "👨", "🔧"]
  updated_at: Date;
  is_active: boolean;
}
```

**Template:**
```html
<div class="conversation-list">
  <button class="new-conversation-btn" (click)="createNewConversation()">
    + Nova Conversa
  </button>

  <div class="conversation-items">
    <div
      *ngFor="let conv of conversations"
      class="conversation-item"
      [class.active]="conv.is_active"
      (click)="selectConversation(conv.conversation_id)">

      <div class="conversation-title">{{ conv.title }}</div>
      <div class="conversation-preview">{{ conv.last_message_preview }}</div>
      <div class="conversation-meta">
        <span class="participants">{{ conv.participant_emojis.join(' ') }}</span>
        <span class="count">{{ conv.message_count }} msgs</span>
      </div>

      <button
        class="delete-btn"
        (click)="deleteConversation($event, conv.conversation_id)">
        🗑️
      </button>
    </div>
  </div>
</div>
```

---

### 3.2. AgentSelectorComponent (NOVO)

**Localização:** `src/app/shared/agent-selector/`

**Responsabilidades:**
- Dropdown para selecionar agente ANTES de enviar mensagem
- Mostrar agente ativo atual
- Listar agentes disponíveis no dock

**Template:**
```html
<div class="agent-selector">
  <label>Agente ativo:</label>
  <select
    [(ngModel)]="selectedAgentId"
    (change)="onAgentChange($event)"
    class="agent-dropdown">

    <option
      *ngFor="let agent of availableAgents"
      [value]="agent.id">
      {{ agent.emoji }} {{ agent.name }}
    </option>
  </select>
</div>
```

---

### 3.3. Modificações no ConductorChatComponent

**Adicionar:**
```typescript
// Múltiplas conversas
private conversations: Map<string, Conversation> = new Map();
private conversationList: ConversationSummary[] = [];

// Métodos
loadConversationList(): void {
  this.conversationService.listConversations().subscribe({
    next: (list) => {
      this.conversationList = list;
    }
  });
}

createNewConversation(): void {
  this.conversationService.createConversation({
    title: `Nova Conversa ${Date.now()}`
  }).subscribe({
    next: (response) => {
      this.activeConversationId = response.conversation_id;
      this.loadConversationList();
      this.loadConversation(response.conversation_id);
    }
  });
}

switchConversation(conversationId: string): void {
  this.activeConversationId = conversationId;
  this.loadConversation(conversationId);
}

deleteConversation(conversationId: string): void {
  this.conversationService.deleteConversation(conversationId).subscribe({
    next: () => {
      this.loadConversationList();
      // Se deletou a conversa ativa, selecionar outra
      if (this.activeConversationId === conversationId) {
        this.activeConversationId = null;
        this.chatState.messages = [];
      }
    }
  });
}

// Trocar agente SEM recarregar (só atualiza o selected)
changeActiveAgent(agentId: string): void {
  const agent = this.contextualAgents.find(a => a.id === agentId);
  if (!agent) return;

  this.activeAgentId = agent.id;
  this.selectedAgentDbId = agent.agent_id;
  this.selectedAgentName = agent.definition.title;
  this.selectedAgentEmoji = agent.emoji;

  // NÃO recarrega histórico - apenas troca o agente para próxima mensagem
  console.log('🔄 Agente selecionado para próxima mensagem:', agent.definition.title);
}
```

---

## 4. Fluxo de Uso (UX Completa)

### Cenário 1: Criar Nova Conversa

```
1. Usuário clica em [+ Nova Conversa]
   ↓
2. Backend cria: conversation_id = "conv-xyz"
   ↓
3. Frontend:
   - Adiciona à lista de conversas
   - Marca como ativa
   - Limpa área de chat
   ↓
4. Usuário seleciona agente no dropdown: 🤖 Agente A
   ↓
5. Usuário envia: "Olá!"
   ↓
6. Mensagem salva em conversations.conv-xyz
```

---

### Cenário 2: Alternar Entre Conversas

```
Usuário está em: Conversa 1 (Python help)
         ↓
Clica em: Conversa 2 (Code review)
         ↓
Frontend:
  - Salva estado de Conversa 1 (sem enviar nada)
  - Carrega histórico de Conversa 2
  - Exibe mensagens da Conversa 2
         ↓
Usuário continua trabalhando na Conversa 2
```

---

### Cenário 3: Trocar Agente ANTES de Mensagem

```
Conversa ativa: conv-123
Histórico:
  - User: "Ajude com Python"
  - 🤖 Agente A: "Claro! Use..."
         ↓
Usuário muda dropdown: [👨 Agente B]
         ↓
Frontend atualiza: selectedAgentDbId = "agente-b"
(NÃO chama backend ainda - só marca localmente)
         ↓
Usuário digita: "E sobre testes?"
         ↓
Clica [Enviar]
         ↓
handleSendMessage():
  - Envia mensagem usando agente-b
  - Salva em conversations.conv-123
  - Agente B vê TODO o histórico
```

---

## 5. Endpoints Backend (já existem!)

Todos os endpoints necessários já foram implementados:

```
✅ POST   /api/conversations              (criar conversa)
✅ GET    /api/conversations              (listar conversas)
✅ GET    /api/conversations/:id          (obter conversa)
✅ POST   /api/conversations/:id/messages (adicionar mensagem)
✅ PUT    /api/conversations/:id/active-agent (trocar agente)
✅ DELETE /api/conversations/:id          (deletar conversa)
```

---

## 6. Layout Responsivo

### Desktop (>1200px)
```
┌────────────┬──────────────────────────┐
│ Conversas  │  Chat                    │
│ (300px)    │  (flex)                  │
└────────────┴──────────────────────────┘
```

### Mobile (<768px)
```
┌──────────────────────────────────────┐
│ [≡ Conversas] Chat - Conversa 1      │
├──────────────────────────────────────┤
│                                      │
│  [Mensagens...]                      │
│                                      │
└──────────────────────────────────────┘

Modal quando clica [≡]:
┌──────────────────┐
│ Conversas        │
│ [+ Nova]         │
│ • Conv 1         │
│ • Conv 2         │
└──────────────────┘
```

---

## 7. Priorização

### Fase 1 (MVP - 4h):
- [ ] ConversationListComponent básico
- [ ] Botão "+" criar conversa
- [ ] Listar conversas
- [ ] Selecionar conversa ativa

### Fase 2 (Seletor de Agente - 2h):
- [ ] AgentSelectorComponent (dropdown)
- [ ] Trocar agente sem recarregar histórico
- [ ] Mostrar agente ativo no header

### Fase 3 (Refinamentos - 2h):
- [ ] Deletar conversa
- [ ] Renomear conversa
- [ ] Preview de última mensagem
- [ ] Contador de mensagens

---

## 8. Estado Final

Com esta implementação, o usuário poderá:

✅ Ter 10+ conversas paralelas
✅ Alternar entre elas instantaneamente
✅ Escolher qual agente responde ANTES de enviar
✅ Ver histórico completo e unificado
✅ Deletar conversas antigas
✅ Múltiplos agentes colaborando na mesma conversa

**Resultado:** UX profissional e produtiva! 🚀
