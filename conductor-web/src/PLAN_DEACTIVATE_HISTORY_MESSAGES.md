# Plano de Implementação: Inativar Mensagens do Histórico
## Projeto: conductor-web (Frontend Angular)

---

## 📋 Objetivo

Implementar a interface de usuário para permitir que usuários inativem mensagens do histórico do chat, com feedback visual imediato (update otimista) e sincronização assíncrona com o backend.

---

## 🎯 Escopo desta Implementação

### ✅ In Scope
- Adicionar campos `isDeleted?: boolean` e `_historyId?: string` ao modelo `Message`
- Criar botão 🗑️ para inativar mensagens (ao lado do botão de copiar 📋)
- Implementar método `deactivateMessage()` em `ChatMessagesComponent`
- Implementar método `onMessageDeactivated()` em `ConductorChatComponent` com update otimista
- Mapear `_id` e `isDeleted` do backend ao carregar histórico
- Adicionar estilos CSS para feedback visual (botão, mensagem inativa)

### ❌ Out of Scope
- Lógica de filtragem do prompt (responsabilidade do `conductor`)
- Endpoints de API (responsabilidade do `conductor-gateway`)
- Testes automatizados
- Deploy ou build do projeto

---

## 📦 Arquivos a Modificar

### 1. `src/app/shared/conductor-chat/models/chat.models.ts`
**Mudança**: Adicionar campos `isDeleted` e `_historyId` à interface `Message`

**ANTES**:
```typescript
export interface Message {
  id: string;
  content: string;
  type: 'user' | 'bot' | 'system';
  timestamp: Date;
  isStreaming?: boolean;
}
```

**DEPOIS**:
```typescript
export interface Message {
  id: string;
  content: string;
  type: 'user' | 'bot' | 'system';
  timestamp: Date;
  isStreaming?: boolean;
  isDeleted?: boolean;    // ← NOVO: undefined = não deletado, false = não deletado, true = deletado
  _historyId?: string;    // ← NOVO: ID do documento no MongoDB para updates
}
```

---

### 2. `src/app/shared/conductor-chat/components/chat-messages/chat-messages.component.ts`

#### **Mudança 2.1: Template HTML - Adicionar botão de inativar**

**ANTES** (trecho relevante):
```html
<div class="bot-message">
  <div class="message-actions">
    <button class="copy-btn" ...>
      📋
      <span class="checkmark" *ngIf="copiedMessageId === message.id">✅</span>
    </button>
  </div>
  <strong>Conductor:</strong>
  <div [innerHTML]="formatMessage(message.content)"></div>
</div>
```

**DEPOIS**:
```html
<div class="bot-message" [class.inactive]="message.isDeleted === true">
  <div class="message-actions">
    <!-- Botão de copiar (existente) -->
    <button
      class="copy-btn"
      (click)="copyToClipboard(message)"
      [title]="copiedMessageId === message.id ? 'Copiado!' : 'Copiar para área de transferência'">
      📋
      <span class="checkmark" *ngIf="copiedMessageId === message.id">✅</span>
    </button>

    <!-- 🆕 NOVO: Botão de inativar -->
    <button
      class="deactivate-btn"
      (click)="deactivateMessage(message)"
      [disabled]="message.isDeleted === true"
      [title]="message.isDeleted === true ? 'Mensagem deletada' : 'Deletar mensagem (não incluir no prompt)'">
      <span *ngIf="message.isDeleted === true">❌</span>
      <span *ngIf="message.isDeleted !== true">🗑️</span>
    </button>
  </div>
  <strong>Conductor:</strong>
  <div [innerHTML]="formatMessage(message.content)"></div>
</div>
```

#### **Mudança 2.2: TypeScript - Adicionar método `deactivateMessage()`**

**ANTES** (parte relevante da classe):
```typescript
@Component({
  selector: 'app-chat-messages',
  standalone: true,
  imports: [CommonModule],
  template: `...`,
  styles: [`...`]
})
export class ChatMessagesComponent implements AfterViewChecked {
  @Input() messages: Message[] = [];
  @Input() isLoading: boolean = false;
  @Input() progressMessage: Message | null = null;
  @Input() streamingMessage: Message | null = null;
  @Input() autoScroll: boolean = true;

  @ViewChild('messagesContainer') messagesContainer?: ElementRef;

  private shouldScrollToBottom = false;
  copiedMessageId: string | null = null;

  constructor(private sanitizer: DomSanitizer) {}

  // ... métodos existentes (formatMessage, copyToClipboard, etc.)
}
```

**DEPOIS**:
```typescript
@Component({
  selector: 'app-chat-messages',
  standalone: true,
  imports: [CommonModule],
  template: `...`,
  styles: [`...`]
})
export class ChatMessagesComponent implements AfterViewChecked {
  @Input() messages: Message[] = [];
  @Input() isLoading: boolean = false;
  @Input() progressMessage: Message | null = null;
  @Input() streamingMessage: Message | null = null;
  @Input() autoScroll: boolean = true;

  @ViewChild('messagesContainer') messagesContainer?: ElementRef;

  // 🆕 NOVO: EventEmitter para inativar mensagem
  @Output() messageDeactivated = new EventEmitter<Message>();

  private shouldScrollToBottom = false;
  copiedMessageId: string | null = null;

  constructor(private sanitizer: DomSanitizer) {}

  // ... métodos existentes ...

  // 🆕 NOVO: Método para inativar mensagem
  deactivateMessage(message: Message): void {
    if (!message || !message._historyId) {
      console.warn('⚠️ [CHAT_MESSAGES] Mensagem não tem _historyId, não pode ser inativada');
      return;
    }

    console.log('🗑️ [CHAT_MESSAGES] Inativando mensagem:', message.id, message._historyId);

    // Emite evento para componente pai tratar
    this.messageDeactivated.emit(message);
  }
}
```

**Import necessário** (adicionar no topo do arquivo):
```typescript
import { Component, Input, ElementRef, ViewChild, AfterViewChecked, Output, EventEmitter } from '@angular/core';
```

#### **Mudança 2.3: Estilos CSS - Adicionar `.deactivate-btn` e `.message.inactive`**

**ADICIONAR aos estilos existentes**:
```css
/* 🆕 NOVO: Estilo do botão de inativar */
.deactivate-btn {
  position: absolute;
  top: 8px;
  right: 36px; /* Ao lado do copy-btn */
  background: #fff3e0;
  border: 1px solid #ffb74d;
  color: #e65100;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease, background 0.2s ease;
}

.deactivate-btn:hover:not(:disabled) {
  background: #ffe0b2;
}

.deactivate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #ffccbc;
}

.bot-message:hover .deactivate-btn {
  opacity: 1;
}

/* 🆕 NOVO: Estilo de mensagem inativa */
.message.inactive {
  opacity: 0.5;
  text-decoration: line-through;
  background: #f5f5f5;
}
```

---

### 3. `src/app/shared/conductor-chat/conductor-chat.component.ts`

#### **Mudança 3.1: Template HTML - Binding do evento `messageDeactivated`**

**ANTES** (trecho relevante):
```html
<app-chat-messages
  [messages]="chatState.messages"
  [isLoading]="chatState.isLoading"
  [progressMessage]="progressMessage"
  [streamingMessage]="streamingMessage"
  [autoScroll]="config.autoScroll"
/>
```

**DEPOIS**:
```html
<app-chat-messages
  [messages]="chatState.messages"
  [isLoading]="chatState.isLoading"
  [progressMessage]="progressMessage"
  [streamingMessage]="streamingMessage"
  [autoScroll]="config.autoScroll"
  (messageDeactivated)="onMessageDeactivated($event)"
/>
```

#### **Mudança 3.2: TypeScript - Adicionar método `onMessageDeactivated()`**

**Localização**: Adicionar método próximo aos outros handlers de eventos (ex: `sendMessage()`, `clearChat()`, etc.)

**Código a adicionar**:
```typescript
/**
 * Handle message deactivation request
 * @param message - The message to deactivate
 */
async onMessageDeactivated(message: Message): Promise<void> {
  if (!message._historyId) {
    console.error('❌ [CHAT] Não é possível inativar: mensagem sem _historyId');
    return;
  }

  console.log('🗑️ [CHAT] Inativando mensagem do histórico:', message._historyId);

  try {
    // 1. Atualização otimista na UI (instant feedback)
    const instanceId = this.activeAgentId;
    if (instanceId) {
      const history = this.chatHistories.get(instanceId);
      if (history) {
        const updatedHistory = history.map(msg => {
          if (msg.id === message.id) {
            return { ...msg, isDeleted: true };
          }
          return msg;
        });
        this.chatHistories.set(instanceId, updatedHistory);
        this.chatState.messages = updatedHistory;
      }
    }

    // 2. Chamada assíncrona ao backend (não bloqueia UI)
    const response = await fetch(`/api/agents/history/${message._historyId}/deactivate`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Falha ao inativar mensagem: ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ [CHAT] Mensagem inativada no backend:', result);

  } catch (error) {
    console.error('❌ [CHAT] Erro ao inativar mensagem:', error);

    // 3. Rollback otimista em caso de erro
    const instanceId = this.activeAgentId;
    if (instanceId) {
      const history = this.chatHistories.get(instanceId);
      if (history) {
        const revertedHistory = history.map(msg => {
          if (msg.id === message.id) {
            return { ...msg, isDeleted: false };
          }
          return msg;
        });
        this.chatHistories.set(instanceId, revertedHistory);
        this.chatState.messages = revertedHistory;
      }
    }

    alert('Erro ao inativar mensagem. Tente novamente.');
  }
}
```

#### **Mudança 3.3: TypeScript - Mapear `_id` e `isDeleted` ao carregar histórico**

**Localização**: Método `loadContextForAgent()` (linha ~1912)

**ANTES** (trecho relevante):
```typescript
context.history.forEach((record: any, index: number) => {
  // Add user message if present
  if (record.user_input && record.user_input.trim().length > 0) {
    historyMessages.push({
      id: `history-user-${index}`,
      content: record.user_input,
      type: 'user',
      timestamp: new Date(record.timestamp * 1000 || record.createdAt)
    });
  }

  // Add AI response if present
  if (record.ai_response) {
    let aiContent = record.ai_response;
    if (typeof aiContent === 'object') {
      aiContent = JSON.stringify(aiContent, null, 2);
    }
    if (aiContent.trim().length > 0) {
      historyMessages.push({
        id: `history-bot-${index}`,
        content: aiContent,
        type: 'bot',
        timestamp: new Date(record.timestamp * 1000 || record.createdAt)
      });
    }
  }
});
```

**DEPOIS**:
```typescript
context.history.forEach((record: any, index: number) => {
  // 🔍 IMPORTANTE: Capturar _id do MongoDB para permitir inativação
  const historyId = record._id || null;
  const isDeleted = record.isDeleted === true;  // Retrocompatibilidade

  // Add user message if present
  if (record.user_input && record.user_input.trim().length > 0) {
    historyMessages.push({
      id: `history-user-${index}`,
      content: record.user_input,
      type: 'user',
      timestamp: new Date(record.timestamp * 1000 || record.createdAt),
      isDeleted: isDeleted,      // 🆕 NOVO
      _historyId: historyId      // 🆕 NOVO
    });
  }

  // Add AI response if present
  if (record.ai_response) {
    let aiContent = record.ai_response;
    if (typeof aiContent === 'object') {
      aiContent = JSON.stringify(aiContent, null, 2);
    }
    if (aiContent.trim().length > 0) {
      historyMessages.push({
        id: `history-bot-${index}`,
        content: aiContent,
        type: 'bot',
        timestamp: new Date(record.timestamp * 1000 || record.createdAt),
        isDeleted: isDeleted,      // 🆕 NOVO
        _historyId: historyId      // 🆕 NOVO
      });
    }
  }
});
```

---

## 🔄 Fluxo de Dados

### Fluxo 1: Carregar Histórico
```
1. ConductorChatComponent.loadContextForAgent()
   ↓
2. fetch('/api/agents/context/{instance_id}')
   ↓
3. Backend retorna: {history: [{_id, user_input, ai_response, isDeleted, ...}], ...}
   ↓
4. Mapeia para Message[]: {id, content, type, timestamp, isDeleted, _historyId}
   ↓
5. ChatMessagesComponent renderiza lista (mensagens inativas aparecem riscadas/opacas)
```

### Fluxo 2: Inativar Mensagem
```
1. Usuário clica no botão 🗑️
   ↓
2. ChatMessagesComponent.deactivateMessage(message)
   ↓
3. Emite evento: messageDeactivated.emit(message)
   ↓
4. ConductorChatComponent.onMessageDeactivated(message)
   ↓
5. Update otimista: message.isDeleted = true (UI muda instantaneamente)
   ↓
6. fetch('/api/agents/history/{_historyId}/deactivate', {method: 'PATCH'})
   ↓
7a. Sucesso: mantém UI
7b. Erro: rollback (message.isDeleted = false) + alert
```

---

## 📝 Regras de Negócio Implementadas

### RN1: Update Otimista
- **O que**: UI atualiza imediatamente ao clicar no botão, antes da resposta do backend
- **Onde**: `ConductorChatComponent.onMessageDeactivated()`
- **Rollback**: Se API retornar erro, reverte mudança na UI

### RN2: Feedback Visual
- **O que**: Mensagens inativadas aparecem com opacidade reduzida e riscadas
- **Onde**: CSS `.message.inactive`
- **Como**: Aplicar classe `[class.inactive]="message.isDeleted === true"`

### RN3: Validação de `_historyId`
- **O que**: Apenas mensagens com `_historyId` podem ser inativadas
- **Onde**: `ChatMessagesComponent.deactivateMessage()`
- **Segurança**: Previne tentativas de inativar mensagens sem ID do MongoDB

### RN4: Retrocompatibilidade
- **O que**: Mensagens antigas (sem `isDeleted`) devem funcionar normalmente
- **Onde**: `loadContextForAgent()` - mapeamento do histórico
- **Como**: `const isDeleted = record.isDeleted === true;` (undefined/false = não deletado)

---

## ✅ Critérios de Sucesso

1. ✅ Botão 🗑️ aparece ao lado de 📋 quando hover sobre mensagem do bot
2. ✅ Clicar no botão muda a aparência da mensagem instantaneamente (opaca, riscada)
3. ✅ Botão fica desabilitado após clicar (mostra ❌ em vez de 🗑️)
4. ✅ Se API retornar sucesso, mensagem permanece inativa
5. ✅ Se API retornar erro, mensagem volta ao estado original + alerta
6. ✅ Histórico carregado do backend mapeia `_id` e `isDeleted` corretamente
7. ✅ Mensagens antigas (sem `isDeleted`) não quebram a UI

---

## 🔗 Dependências

### Upstream (bloqueia este trabalho)
- **conductor-gateway**: Endpoint `PATCH /api/agents/history/{id}/deactivate` deve existir
- **conductor-gateway**: Endpoint `GET /api/agents/context/{instance_id}` deve retornar `_id` e `isDeleted`

### Downstream (depende deste trabalho)
- Nenhuma (este é o último componente da cadeia)

---

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Mensagem sem `_historyId` | Alto | Validação no `deactivateMessage()` com `console.warn()` |
| Erro de rede (API offline) | Médio | Try/catch + rollback otimista + alert |
| Mensagens antigas sem `isDeleted` | Baixo | Fallback: `record.isDeleted === true` (undefined = false) |
| Estilos CSS conflitantes | Baixo | Usar classes específicas (`.deactivate-btn`, `.message.inactive`) |

---

## 🚀 Ordem de Implementação Sugerida

1. **Passo 1**: Modificar `chat.models.ts` (adicionar campos à interface `Message`)
2. **Passo 2**: Modificar `conductor-chat.component.ts` - método `loadContextForAgent()` (mapear `_id` e `isDeleted`)
3. **Passo 3**: Adicionar método `onMessageDeactivated()` em `conductor-chat.component.ts`
4. **Passo 4**: Adicionar binding `(messageDeactivated)="..."` no template do `ConductorChatComponent`
5. **Passo 5**: Adicionar método `deactivateMessage()` em `chat-messages.component.ts`
6. **Passo 6**: Adicionar botão 🗑️ no template de `ChatMessagesComponent`
7. **Passo 7**: Adicionar estilos CSS (`.deactivate-btn`, `.message.inactive`)
8. **Passo 8**: Testar manualmente no navegador

---

## 🧪 Validação Manual

### Teste 1: Carregar histórico com `_id`
1. Abrir DevTools → Network
2. Carregar um agente no chat
3. Verificar resposta de `/api/agents/context/{instance_id}`
4. Confirmar que cada item do histórico tem `_id` (string) e `isDeleted` (boolean)

### Teste 2: Inativar mensagem
1. Passar mouse sobre mensagem do bot
2. Botão 🗑️ deve aparecer (opacity: 0 → 1)
3. Clicar no botão
4. Mensagem deve ficar opaca e riscada instantaneamente
5. Botão deve mudar para ❌ e ficar desabilitado
6. Verificar no Network que `PATCH /api/agents/history/{id}/deactivate` foi enviado

### Teste 3: Rollback em caso de erro
1. Desligar backend (ou modificar URL do endpoint para causar erro 404)
2. Clicar no botão de inativar
3. Mensagem deve voltar ao estado original após ~1 segundo
4. Alerta deve aparecer: "Erro ao inativar mensagem. Tente novamente."

### Teste 4: Mensagem não reaparece em novo prompt
1. Inativar uma mensagem
2. Enviar nova mensagem no chat
3. Verificar no backend/logs que a mensagem inativa NÃO foi incluída no prompt

---

## 📚 Referências

- **Screenplay completo**: `requisitos_inativar_mensagens_chat.md`
- **Código atual**:
  - `src/app/shared/conductor-chat/conductor-chat.component.ts:1-2507`
  - `src/app/shared/conductor-chat/components/chat-messages/chat-messages.component.ts:1-317`
  - `src/app/shared/conductor-chat/models/chat.models.ts`

---

## 🎯 Estimativa de Esforço

- **Complexidade**: Média-Alta
- **Tempo estimado**: 2-3 horas
- **Arquivos modificados**: 3
- **Linhas de código**: ~80 linhas adicionadas/modificadas (código + HTML + CSS)

---

**Plano criado em**: 2025-11-01
**Projeto**: conductor-web (Frontend Angular)
**Saga**: Inativar Mensagens do Histórico do Chat
