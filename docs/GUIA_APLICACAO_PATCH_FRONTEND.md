# Guia de Aplicação: Patch Frontend para Conversas Globais

**Data:** 2025-11-01
**Ref:** PLANO_REFATORACAO_CONVERSATION_ID.md - Fase 2

---

## 📋 Visão Geral

Este guia descreve como aplicar as mudanças no `conductor-chat.component.ts` para suportar o novo modelo de conversas globais mantendo compatibilidade com o modelo legado via feature flag.

---

## 🎯 Arquivos Afetados

1. **src/app/shared/conductor-chat/conductor-chat.component.ts** - Componente principal
2. **src/app/shared/conductor-chat/components/chat-messages/chat-messages.component.html** - Template de mensagens
3. **src/app/shared/conductor-chat/components/chat-messages/chat-messages.component.ts** - Componente de mensagens
4. **src/app/shared/conductor-chat/conductor-chat.component.html** (embutido no TS) - Template

---

## 🔧 Passo 1: Adicionar Imports

**Arquivo:** `conductor-chat.component.ts`

**Localização:** Após os imports existentes (linha ~15)

```typescript
// 🔥 NOVO: Imports para modelo de conversas
import { environment } from '../../../environments/environment';
import {
  ConversationService,
  Conversation,
  AgentInfo as ConvAgentInfo,
  Message as ConvMessage
} from '../../services/conversation.service';
```

---

## 🔧 Passo 2: Adicionar Propriedades

**Arquivo:** `conductor-chat.component.ts`

**Localização:** Após a linha 1382 (`private chatHistories: Map<string, Message[]> = new Map();`)

```typescript
// 🔥 NOVO MODELO: Conversas globais
private activeConversationId: string | null = null;  // ID da conversa ativa
private conversationParticipants: ConvAgentInfo[] = [];  // Participantes
```

---

## 🔧 Passo 3: Modificar Constructor

**Arquivo:** `conductor-chat.component.ts`

**Localização:** Linha ~1402

**ANTES:**
```typescript
constructor(
  private apiService: ConductorApiService,
  private screenplayService: ScreenplayService,
  private agentService: AgentService,
  private agentExecutionService: AgentExecutionService,
  private personaEditService: PersonaEditService,
  private speechService: SpeechRecognitionService
) { }
```

**DEPOIS:**
```typescript
constructor(
  private apiService: ConductorApiService,
  private screenplayService: ScreenplayService,
  private agentService: AgentService,
  private agentExecutionService: AgentExecutionService,
  private personaEditService: PersonaEditService,
  private speechService: SpeechRecognitionService,
  private conversationService: ConversationService  // 🔥 NOVO
) { }
```

---

## 🔧 Passo 4: Refatorar loadContextForAgent()

**Arquivo:** `conductor-chat.component.ts`

**Localização:** Linha ~1913

**Estratégia:** Adicionar lógica condicional no início do método e extrair código legado para método separado.

```typescript
loadContextForAgent(instanceId: string, agentName?: string, agentEmoji?: string, agentDbId?: string, cwd?: string, screenplayId?: string): void {
  console.log('📥 [CHAT] loadContextForAgent chamado');
  console.log('   - Feature Flag useConversationModel:', environment.features?.useConversationModel);

  this.activeAgentId = instanceId;
  this.selectedAgentDbId = agentDbId || null;
  this.selectedAgentName = agentName || null;
  this.selectedAgentEmoji = agentEmoji || null;
  this.activeScreenplayId = screenplayId || null;
  this.chatState.isLoading = true;

  // 🔥 NOVO MODELO
  if (environment.features?.useConversationModel) {
    this.loadContextWithConversationModel(instanceId, agentName, agentEmoji, agentDbId, cwd, screenplayId);
    return;
  }

  // 🔄 MODELO LEGADO (código original)
  this.loadContextWithLegacyModel(instanceId, cwd);
}
```

**Adicionar novos métodos** (ver arquivo patch completo em `conductor-chat-conversation-refactor.PATCH.md`):
- `loadContextWithConversationModel()`
- `loadConversation()`
- `loadContextWithLegacyModel()`
- `loadAgentMetadata()`

---

## 🔧 Passo 5: Refatorar handleSendMessage()

**Arquivo:** `conductor-chat.component.ts`

**Localização:** Linha ~1531

```typescript
handleSendMessage(data: {message: string, provider?: string}): void {
  if (!data.message.trim() || this.chatState.isLoading) return;
  if (this.isInputBlocked()) return;

  this.forceSaveScreenplayIfNeeded();

  const userMessage: Message = {
    id: Date.now().toString(),
    content: data.message.trim(),
    type: 'user',
    timestamp: new Date()
  };

  // 🔥 NOVO MODELO
  if (environment.features?.useConversationModel && this.activeConversationId && this.activeAgentId) {
    this.handleSendMessageWithConversationModel(data, userMessage);
    return;
  }

  // 🔄 MODELO LEGADO
  this.handleSendMessageWithLegacyModel(data, userMessage);
}
```

**Adicionar novos métodos** (ver arquivo patch):
- `handleSendMessageWithConversationModel()`
- `handleSendMessageWithLegacyModel()`

---

## 🔧 Passo 6: Ajustar Template para Exibir Agente em Mensagens

**Arquivo:** `chat-messages.component.html`

**Localização:** Template de mensagem de bot

**ANTES:**
```html
<div class="message bot">
  <div class="message-content">{{ message.content }}</div>
</div>
```

**DEPOIS:**
```html
<div class="message bot">
  <!-- 🔥 NOVO: Exibir info do agente -->
  <div class="message-agent-info" *ngIf="message.agent">
    <span class="agent-emoji">{{ message.agent.emoji }}</span>
    <span class="agent-name">{{ message.agent.name }}</span>
  </div>
  <div class="message-content">{{ message.content }}</div>
</div>
```

---

## 🔧 Passo 7: Adicionar Estilos CSS

**Arquivo:** `chat-messages.component.ts` (ou arquivo de estilos)

```css
.message-agent-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 0;
  font-size: 0.85em;
  color: #666;
  margin-bottom: 4px;
}

.message-agent-info .agent-emoji {
  font-size: 1.2em;
}

.message-agent-info .agent-name {
  font-weight: 600;
}

/* Diferenciação visual entre agentes */
.message.bot:has(.message-agent-info) {
  border-left: 3px solid #667eea;
  padding-left: 12px;
}
```

---

## 🔧 Passo 8: Atualizar Interface Message

**Arquivo:** `models/chat.models.ts`

**ANTES:**
```typescript
export interface Message {
  id: string;
  content: string;
  type: 'user' | 'bot' | 'system';
  timestamp: Date;
  _historyId?: string;
  isDeleted?: boolean;
}
```

**DEPOIS:**
```typescript
export interface Message {
  id: string;
  content: string;
  type: 'user' | 'bot' | 'system';
  timestamp: Date;
  _historyId?: string;
  isDeleted?: boolean;

  // 🔥 NOVO: Informações do agente (para modelo de conversas)
  agent?: {
    agent_id: string;
    instance_id: string;
    name: string;
    emoji?: string;
  };
}
```

---

## ✅ Checklist de Aplicação

- [ ] Adicionar imports
- [ ] Adicionar propriedades na classe
- [ ] Modificar constructor
- [ ] Adicionar método `loadContextWithConversationModel()`
- [ ] Adicionar método `loadConversation()`
- [ ] Adicionar método `loadContextWithLegacyModel()`
- [ ] Adicionar método `loadAgentMetadata()`
- [ ] Refatorar método `handleSendMessage()`
- [ ] Adicionar método `handleSendMessageWithConversationModel()`
- [ ] Adicionar método `handleSendMessageWithLegacyModel()`
- [ ] Atualizar template de mensagens (exibir agente)
- [ ] Adicionar estilos CSS
- [ ] Atualizar interface `Message`
- [ ] Testar com feature flag `true`
- [ ] Testar com feature flag `false`

---

## 🧪 Testes

### Teste 1: Modelo Novo (feature flag = true)

```typescript
// environment.ts
features: {
  useConversationModel: true
}
```

**Cenário:**
1. Selecionar agente A
2. Enviar mensagem "Olá"
3. Aguardar resposta
4. Selecionar agente B (mesmo screenplay)
5. Enviar mensagem "Continue"
6. **Verificar:** Agente B vê histórico completo incluindo mensagens do Agente A

### Teste 2: Modelo Legado (feature flag = false)

```typescript
// environment.ts
features: {
  useConversationModel: false
}
```

**Cenário:**
1. Selecionar agente A
2. Enviar mensagem "Olá"
3. Selecionar agente B
4. **Verificar:** Agente B NÃO vê mensagens do Agente A (comportamento atual)

### Teste 3: UI - Exibição de Agente

**Verificar:**
- Mensagens de bot exibem emoji e nome do agente
- Diferenciação visual entre mensagens de agentes diferentes
- Ícones/badges de participantes da conversa

---

## 🐛 Troubleshooting

### Erro: "Cannot find module 'ConversationService'"

**Solução:** Verificar import do serviço:
```typescript
import { ConversationService } from '../../services/conversation.service';
```

### Erro: "Property 'agent' does not exist on type 'Message'"

**Solução:** Atualizar interface `Message` em `chat.models.ts`

### UI não mostra nome do agente

**Solução:** Verificar se:
1. Template foi atualizado com `*ngIf="message.agent"`
2. Backend está retornando campo `agent` nas mensagens
3. CSS foi adicionado corretamente

---

## 📚 Arquivos de Referência

- **Patch completo:** `conductor-chat-conversation-refactor.PATCH.md`
- **Documentação:** `IMPLEMENTACAO_CONVERSATION_ID.md`
- **Plano original:** `PLANO_REFATORACAO_CONVERSATION_ID.md`

---

**Última atualização:** 2025-11-01
**Status:** Pronto para aplicação
