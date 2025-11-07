# Send Button Implementation Analysis - conductor-web

## Overview
The send button in conductor-web is the primary mechanism for submitting messages to the agent execution system. This document provides a comprehensive breakdown of the current implementation.

---

## 1. COMPONENT FILE: conductor-chat.component.ts

**File Path:** `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts`

### HTML Template (Embedded in Component)
Located at lines 357-366:

```html
<!-- Send button -->
<button
  class="icon-button send-button"
  (click)="sendMessage()"
  [disabled]="chatState.isLoading || isEditorEmpty()"
  [title]="chatState.isLoading ? 'Enviando...' : 'Enviar mensagem'"
>
  <span *ngIf="!chatState.isLoading">⬆️</span>
  <span *ngIf="chatState.isLoading">⏳</span>
</button>
```

**Button Behavior:**
- **Click Handler:** `sendMessage()` method
- **Disabled State:** Button is disabled when:
  - `chatState.isLoading` is true (message is being processed)
  - `isEditorEmpty()` returns true (no text entered)
- **Dynamic Icon:** Shows ⬆️ (up arrow) when ready, ⏳ (hourglass) when loading
- **Dynamic Title:** Shows "Enviando..." (Sending...) when loading, "Enviar mensagem" (Send message) when ready

### Location in Template
The button is located in the **chat footer** (`chat-footer` class), in the `controls-row` div alongside:
- Provider dropdown selector
- Microphone button for speech input
- Mode toggle button (Ask/Agent modes)

---

## 2. CLICK HANDLER METHOD: sendMessage()

**Location:** Lines 1992-2009

```typescript
sendMessage(): void {
  if (!this.messageContent.trim() || this.chatState.isLoading) return;

  const data = {
    message: this.messageContent.trim(),
    provider: this.selectedProvider || undefined
  };

  this.handleSendMessage(data);

  // Clear editor after sending
  if (this.chatInputComponent) {
    this.chatInputComponent.clearEditor();
  }

  // Reset messageContent
  this.messageContent = '';
}
```

**What it does:**
1. Validates that message content is not empty and chat is not loading
2. Creates a data object with:
   - `message`: The trimmed user input
   - `provider`: The selected AI provider (claude, gemini, cursor-agent, or undefined for default)
3. Calls `handleSendMessage(data)` to process the message
4. Clears the editor component and resets the messageContent property

---

## 3. MESSAGE HANDLER: handleSendMessage()

**Location:** Lines 2054-2149

```typescript
handleSendMessage(data: {message: string, provider?: string}): void {
  if (!data.message.trim() || this.chatState.isLoading) return;

  if (this.isInputBlocked()) {
    console.warn('⚠️ [CHAT] Bloqueado: defina o diretório de trabalho primeiro');
    return;
  }

  this.forceSaveScreenplayIfNeeded();

  // Validar que temos as informações necessárias
  if (!this.activeAgentId || !this.selectedAgentDbId) {
    console.error('❌ [CHAT] Agente não selecionado ou sem ID');
    return;
  }

  // Criar mensagem do usuário
  const userMessage: Message = {
    id: Date.now().toString(),
    content: data.message.trim(),
    type: 'user',
    timestamp: new Date()
  };

  // Preparar parâmetros para o serviço
  const params: MessageParams = {
    message: data.message,
    provider: data.provider,
    conversationId: this.activeConversationId || undefined,
    agentId: this.activeAgentId,
    agentDbId: this.selectedAgentDbId,
    agentName: this.selectedAgentName || 'Unknown',
    agentEmoji: this.selectedAgentEmoji || '🤖',
    cwd: this.activeAgentCwd || undefined,
    screenplayId: this.activeScreenplayId || undefined,
    instanceId: this.activeAgentId
  };

  // Preparar callbacks
  const callbacks: MessageHandlingCallbacks = {
    onProgressUpdate: (message: string, instanceId: string) => {
      if (message) {
        this.addProgressMessage(message, instanceId);
      } else {
        this.progressMessages.set(instanceId, null);
      }
    },
    onStreamingUpdate: (chunk: string, instanceId: string) => {
      this.appendToStreamingMessage(chunk, instanceId);
    },
    onLoadingChange: (isLoading: boolean) => {
      this.chatState.isLoading = isLoading;
    },
    onMessagesUpdate: (messages: Message[]) => {
      this.chatState.messages = messages;
    },
    onConversationReload: (conversationId: string) => {
      this.loadConversation(conversationId);
    }
  };

  // 🔥 NOVO MODELO: Usar conversas globais
  if (environment.features?.useConversationModel && this.activeConversationId && this.activeAgentId) {
    // Adicionar mensagem à UI imediatamente
    this.chatState.messages = [...this.chatState.messages.filter(msg =>
      !msg.id.startsWith('empty-')
    ), userMessage];

    this.messageHandlingService.sendMessageWithConversationModel(params, callbacks).subscribe({
      next: (result) => {
        console.log('✅ [CHAT] Mensagem processada com sucesso');
      },
      error: (error) => {
        console.error('❌ [CHAT] Erro ao processar mensagem:', error);
        this.handleError(error, this.activeAgentId);
      }
    });
    return;
  }

  // 🔄 MODELO LEGADO: Código original
  this.messageHandlingService.sendMessageWithLegacyModel(
    params,
    this.chatState.messages,
    this.chatHistories,
    callbacks
  ).subscribe({
    next: (result) => {
      console.log('✅ [CHAT] Mensagem processada com sucesso (legado)');
    },
    error: (error) => {
      console.error('❌ [CHAT] Erro ao processar mensagem:', error);
      this.handleError(error, this.activeAgentId);
    }
  });
}
```

**Key Validations:**
1. Message is not empty and loading not in progress
2. Input is not blocked (requires working directory to be set)
3. Agent is selected (both instance ID and DB ID required)

**Two Execution Paths:**
1. **Conversation Model (NEW):** Used when `environment.features?.useConversationModel` is enabled
   - Uses global conversations stored in backend
   - Calls `messageHandlingService.sendMessageWithConversationModel()`

2. **Legacy Model:** Falls back to original implementation
   - Uses local message history per agent
   - Calls `messageHandlingService.sendMessageWithLegacyModel()`

---

## 4. USER INPUT CAPTURE

**Current Implementation:** Two mechanisms capture user input

### A. Chat Input Component (TipTap Editor)

**File:** `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`

**How it works:**
- Uses TipTap editor (rich text editing library) with ProseMirror
- Supports:
  - Rich text formatting (bold, italic, code, etc.)
  - Markdown syntax
  - Code blocks with syntax highlighting
  - Task lists
  - Paste handling (converts HTML to Markdown)

**Key Events:**
- `onUpdate` event emits content changes to parent component
- `handleKeyDown` intercepts keyboard:
  - **Enter (without Shift):** Emits `enterPressed` event (triggers send)
  - **Shift+Enter:** Adds new line

**Content Flow:**
```
TipTap Editor
  ↓ (onUpdate event)
messageContentChanged event emitted
  ↓ (received by conductor-chat)
onMessageContentChanged() method updates this.messageContent
  ↓ (enterPressed event on Enter key)
sendMessage() called
```

### B. Message Content Binding

In conductor-chat.component.ts:

```typescript
@ViewChild('chatInputComponent') chatInputComponent!: ChatInputComponent;

onMessageContentChanged(content: string): void {
  this.messageContent = content;
}
```

The component listens to `messageContentChanged` event from ChatInputComponent and updates `this.messageContent`.

---

## 5. SERVICE FILE: MessageHandlingService

**File Path:** `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-web/src/app/shared/conductor-chat/services/message-handling.service.ts`

This service unifies message sending logic for both conversation and legacy models.

### Methods:

#### sendMessageWithConversationModel()
- Adds user message to backend conversation
- Executes agent asynchronously
- Saves agent response back to backend
- Handles streaming and progress updates

#### sendMessageWithLegacyModel()
- Updates local message history
- Executes agent
- Updates UI with responses
- Maintains separate message history per agent instance

**Callbacks Used:**
```typescript
interface MessageHandlingCallbacks {
  onProgressUpdate: (message: string, instanceId: string) => void;
  onStreamingUpdate: (chunk: string, instanceId: string) => void;
  onLoadingChange: (isLoading: boolean) => void;
  onMessagesUpdate: (messages: Message[]) => void;
  onConversationReload?: (conversationId: string) => void;
}
```

---

## 6. API SERVICE: ConductorApiService (Legacy)

**File Path:** `/mnt/ramdisk/primoia-main/conductor-community/conductor/conductor-web/src/app/shared/conductor-chat/services/conductor-api.service.ts`

Note: This appears to be a legacy service. The current implementation uses AgentService instead.

**Method:** `sendMessage()`
- Uses EventSource for Server-Sent Events (SSE)
- Endpoint: `/api/v1/stream-execute` (start) and `/api/v1/stream/${job_id}` (stream)

---

## 7. CURRENT API ENDPOINTS

### Primary Endpoint: Agent Execution

**Service:** AgentService (agent.service.ts)

**Start Execution:**
```
POST /api/v1/stream-execute
```

**Request Body:**
```json
{
  "agent_id": "string",
  "instance_id": "string",
  "conversation_id": "string (optional)",
  "screenplay_id": "string (optional)",
  "cwd": "string (default: /app)",
  "ai_provider": "string (default: claude)",
  "context_mode": "stateless",
  "textEntries": [
    {
      "uid": "1",
      "content": "user message text"
    }
  ]
}
```

**Stream Connection:**
```
GET /api/v1/stream/{job_id}
```
Uses EventSource for Server-Sent Events

**Available Parameters:**
- `agent_id`: ID of the agent to execute (required)
- `instance_id`: Instance identifier for this execution (required)
- `conversation_id`: Global conversation context (optional)
- `screenplay_id`: Document/screenplay context (optional)
- `cwd`: Working directory for agent execution (default: /app)
- `ai_provider`: AI provider to use (claude, gemini, cursor-agent, etc.)
- `context_mode`: How to handle context (stateless)
- `textEntries`: Array of text inputs (typically just the user message)

---

## 8. DATA FLOW DIAGRAM

```
User clicks Send Button (⬆️)
         ↓
    sendMessage()
         ↓
   Validate inputs
         ↓
   handleSendMessage()
         ↓
Create MessageParams object ─→ Collect:
                               - message content
                               - provider
                               - agentId
                               - agentDbId
                               - conversationId
                               - cwd
                               - screenplayId
         ↓
   Check feature flag
    /          \
   /            \
NEW MODEL    LEGACY MODEL
(Conversation) (Local History)
   |                |
   v                v
messageHandling messageHandling
Service.send     Service.send
WithConversation WithLegacy
Model()          Model()
   |                |
   +----+----+----+
        |
        v
   AgentService
   .executeAgent()
        |
        v
executeAgentViaSSE()
        |
   POST /api/v1/stream-execute
        |
   Get job_id
        |
   GET /api/v1/stream/{job_id}
        |
   Receive SSE events
        |
   Update UI callbacks
        |
   Complete/Error
```

---

## 9. KEY PROPERTIES & STATE

### From conductor-chat.component.ts

```typescript
// User input
messageContent: string = '';  // Current message being typed

// Editor reference
@ViewChild('chatInputComponent') chatInputComponent!: ChatInputComponent;

// Chat state
chatState: ChatState = {
  messages: [],
  isLoading: false,
  isConnected: false
};

// Agent info
activeAgentId: string = '';                // Instance ID
selectedAgentDbId: string = '';            // Database agent ID
selectedAgentName: string = '';            // Display name
selectedAgentEmoji: string = '';           // Emoji icon
activeAgentCwd: string = '';               // Working directory
activeConversationId: string | null = null;
activeScreenplayId: string | null = null;

// Provider selection
selectedProvider: string = '';  // AI provider (claude, gemini, etc.)
```

---

## 10. VALIDATION CHECKS

**Before message is sent:**

1. **Message content check:**
   ```typescript
   if (!this.messageContent.trim() || this.chatState.isLoading) return;
   ```

2. **Input blocking check** (requires working directory):
   ```typescript
   if (this.isInputBlocked()) return;
   ```

3. **Agent selection check:**
   ```typescript
   if (!this.activeAgentId || !this.selectedAgentDbId) {
     console.error('❌ [CHAT] Agente não selecionado ou sem ID');
     return;
   }
   ```

4. **Editor empty check** (button disable):
   ```typescript
   [disabled]="chatState.isLoading || isEditorEmpty()"
   ```

---

## 11. KEYBOARD SHORTCUTS

From chat-input.component.ts (handleKeyDown):

- **Enter** (without Shift): Sends message
- **Shift+Enter**: Adds new line in editor

---

## 12. SUMMARY TABLE

| Component | File | Key Function | Role |
|-----------|------|--------------|------|
| **conductor-chat** | conductor-chat.component.ts | sendMessage(), handleSendMessage() | Main orchestrator |
| **chat-input** | chat-input.component.ts | - | Rich text editor, captures input |
| **MessageHandlingService** | message-handling.service.ts | sendMessageWithConversationModel(), sendMessageWithLegacyModel() | Unifies send logic |
| **AgentService** | agent.service.ts | executeAgent(), executeAgentViaSSE() | Executes agent, handles SSE |
| **ConductorApiService** | conductor-api.service.ts | sendMessage() | Legacy API calls (not used currently) |

---

## 13. CURRENT LIMITATIONS & NOTES

1. **Two models:** Code supports both conversation model (new) and legacy model (old) - this can be simplified
2. **Direct fetch:** Uses native `fetch()` with EventSource instead of HttpClient - might not use Angular interceptors
3. **Manual error handling:** Error handling is manual in services - could use centralized error handler
4. **Message format:** Uses simple text entries array, future versions might need attachment support
5. **No optimistic updates:** Messages appear after backend confirmation (conversation model)

---

## Change Preparation Notes

When preparing changes to the send button, consider:

1. **Button click handler:** `sendMessage()` at line 1992
2. **Message validation:** Before `handleSendMessage()` is called
3. **Input capture source:** TipTap editor component (chat-input.component.ts)
4. **API endpoint:** `/api/v1/stream-execute` POST request
5. **Streaming response:** Handled via EventSource, not HTTP polling
6. **Loading state:** `chatState.isLoading` controls UI appearance
7. **Error callbacks:** `onLoadingChange`, `onProgressUpdate` for feedback
8. **Both code paths:** Must test with both conversation model and legacy model enabled

