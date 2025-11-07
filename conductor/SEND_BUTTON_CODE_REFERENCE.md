# Code Reference Guide - Send Button Implementation

## File Locations

```
conductor-web/
├── src/app/shared/conductor-chat/
│   ├── conductor-chat.component.ts          <- Main component with send button
│   ├── conductor-chat.component.ts (line 357-366)  <- Send button HTML
│   ├── conductor-chat.component.ts (line 1992)     <- sendMessage() method
│   ├── conductor-chat.component.ts (line 2054)     <- handleSendMessage() method
│   │
│   ├── components/
│   │   └── chat-input/
│   │       └── chat-input.component.ts      <- TipTap editor, captures input
│   │
│   └── services/
│       ├── message-handling.service.ts      <- Unifies send logic
│       ├── conductor-api.service.ts         <- Legacy API service
│       └── [other services...]
│
├── services/
│   └── agent.service.ts                     <- Executes agent, handles SSE
```

---

## Quick Code Snippets

### 1. Send Button HTML (conductor-chat.component.ts: 357-366)

```html
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

### 2. sendMessage() Method (conductor-chat.component.ts: 1992)

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

### 3. handleSendMessage() Method (conductor-chat.component.ts: 2054)

Key section - choosing between conversation vs legacy model:

```typescript
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
```

### 4. TipTap Editor Enter Key Handling (chat-input.component.ts: 309-314)

```typescript
handleKeyDown: (view, event) => {
  // Enter without Shift = send message
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    this.enterPressed.emit(); // Notify parent to send
    return true;
  }
  // Shift+Enter = new line (default behavior)
  return false;
},
```

### 5. AgentService - executeAgentViaSSE (agent.service.ts: 477-575)

Start execution request:

```typescript
const startUrl = `${this.baseUrl}/api/v1/stream-execute`;
console.log('🚀 [SSE] Starting streaming execution:', startUrl);

const startResponse = await fetch(startUrl, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    agent_id: agentId,
    instance_id: requestBody.instance_id,
    conversation_id: requestBody.conversation_id,
    screenplay_id: requestBody.document_id, // Use document_id as screenplay_id
    cwd: requestBody.cwd || '/app',
    ai_provider: requestBody.ai_provider || 'claude',
    context_mode: 'stateless',
    textEntries: [{
      uid: '1',
      content: inputText
    }]
  }),
});

if (!startResponse.ok) {
  throw new Error(`SSE start failed: ${startResponse.status} ${startResponse.statusText}`);
}

const { job_id } = await startResponse.json();
```

Stream connection:

```typescript
const streamUrl = `${this.baseUrl}/api/v1/stream/${job_id}`;
const eventSource = new EventSource(streamUrl);

eventSource.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    console.log('📡 [SSE] Event received:', data.event, data);

    switch (data.event) {
      case 'task_started':
        console.log('⏳ [SSE] Task started');
        break;
      case 'status_update':
        console.log('🔄 [SSE] Status update:', data.data?.message);
        break;
      case 'result':
        console.log('✅ [SSE] Result received');
        finalResult = data.data;
        break;
      case 'error':
        console.error('❌ [SSE] Error:', data.data?.error);
        eventSource.close();
        observer.error(new Error(data.data?.error || 'SSE execution failed'));
        break;
    }
  } catch (parseError) {
    console.error('❌ [SSE] Error parsing event:', parseError);
  }
};
```

### 6. MessageHandlingService Interface (message-handling.service.ts: 38-44)

```typescript
export interface MessageHandlingCallbacks {
  onProgressUpdate: (message: string, instanceId: string) => void;
  onStreamingUpdate: (chunk: string, instanceId: string) => void;
  onLoadingChange: (isLoading: boolean) => void;
  onMessagesUpdate: (messages: Message[]) => void;
  onConversationReload?: (conversationId: string) => void;
}
```

---

## Key Variables to Track

### In conductor-chat.component.ts

```typescript
// User input state
messageContent: string = '';

// Chat state
chatState: ChatState = {
  messages: [],
  isLoading: false,
  isConnected: false
};

// Active selections
activeAgentId: string = '';
selectedAgentDbId: string = '';
selectedAgentName: string = '';
selectedAgentEmoji: string = '';
activeAgentCwd: string = '';
activeConversationId: string | null = null;
activeScreenplayId: string | null = null;

// UI state
selectedProvider: string = '';  // AI provider selection
isRecording: boolean = false;   // Voice recording state
currentMode: ChatMode = 'ask';  // Ask or Agent mode
```

---

## Message Flow Summary

```
1. User types in TipTap Editor
   ↓
2. onUpdate event fires
   ↓
3. messageContentChanged emitted with trimmed markdown
   ↓
4. conductor-chat receives event, updates messageContent
   ↓
5. User clicks send button OR presses Enter
   ↓
6. sendMessage() called
   ↓
7. Validates message not empty and not loading
   ↓
8. handleSendMessage() called with message + provider
   ↓
9. Validations:
   - Input not blocked (CWD required)
   - Agent selected (ID + DbId)
   ↓
10. MessageParams object created with all context
   ↓
11. MessageHandlingCallbacks object created
   ↓
12. Feature flag check:
    - If useConversationModel: sendMessageWithConversationModel()
    - Else: sendMessageWithLegacyModel()
   ↓
13. MessageHandlingService executes agent via AgentService
   ↓
14. AgentService.executeAgent() called
   ↓
15. AgentService.executeAgentViaSSE() opens connections:
    - POST /api/v1/stream-execute (get job_id)
    - EventSource /api/v1/stream/{job_id} (stream events)
   ↓
16. SSE events processed, UI updated via callbacks
   ↓
17. Message history updated, loading state cleared
```

---

## Testing Checklist for Changes

When modifying send button behavior:

- [ ] Button click triggers sendMessage()
- [ ] Keyboard Enter key (without Shift) sends message
- [ ] Shift+Enter creates new line (doesn't send)
- [ ] Button disabled when message empty
- [ ] Button disabled while loading (shows hourglass)
- [ ] Editor clears after sending
- [ ] Message added to UI before backend response
- [ ] Loading state set during execution
- [ ] Error handling works for both model types
- [ ] Provider selection passes to backend
- [ ] CWD validation works
- [ ] Agent selection validation works
- [ ] Conversation reload callback fires (if using conversation model)
- [ ] Progress updates display in UI
- [ ] SSE connection established and closed properly
- [ ] Works with both conversation and legacy model enabled

---

## Environment Configuration

Feature flag for conversation model (from conductor-chat.component.ts):

```typescript
if (environment.features?.useConversationModel && this.activeConversationId && this.activeAgentId) {
  // Use new conversation model
}
```

This is defined in `environments/environment.ts` and controlled at build time.

---

## API Response Handling (agent.service.ts: 176-237)

The service handles various response formats from the backend:

```typescript
let resultText = '';

// Try different possible response formats from backend
if (typeof response.result === 'string' && response.result.trim().length > 0) {
  resultText = response.result;
} else if (typeof response === 'string' && response.trim().length > 0) {
  resultText = response;
} else if (response.ai_response && typeof response.ai_response === 'string') {
  resultText = response.ai_response;
} else if (response.data?.ai_response && typeof response.data.ai_response === 'string') {
  resultText = response.data.ai_response;
} else if (response.data?.result && typeof response.data.result === 'string') {
  resultText = response.data.result;
} else if (response.message && typeof response.message === 'string') {
  resultText = response.message;
} else if (response.output && typeof response.output === 'string') {
  resultText = response.output;
} else if (response.response && typeof response.response === 'string') {
  resultText = response.response;
} else if (response.result && typeof response.result === 'object') {
  // Handle nested objects...
}
```

This flexible approach allows the frontend to work with different backend response formats.

