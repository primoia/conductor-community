# 🔗 Fase 2: Frontend - Integração com AgentService

## 📋 Metadados
- **ID**: fase-02
- **Título**: Frontend - Integração com AgentService
- **Executor**: Agente Frontend
- **Dependências**: Fase 1 (UI do seletor deve estar implementada)
- **Status**: Pendente

## 🎯 Objetivo
Integrar o seletor de provider implementado na Fase 1 com o fluxo de envio de mensagem, propagando o provider selecionado através do evento `messageSent` até o `AgentService.executeAgent()`, que enviará ao backend.

## 📍 Contexto
Atualmente, o fluxo de envio é:
1. Usuário clica no botão de envio → `ChatInputComponent.sendMessage()`
2. `ChatInputComponent` emite evento `messageSent` (apenas string da mensagem)
3. `ConductorChatComponent` recebe evento → chama `AgentService.executeAgent()`
4. `AgentService` faz POST para `/api/agents/{id}/execute` (sem `ai_provider`)

Precisamos modificar esse fluxo para incluir o `ai_provider` selecionado.

## 📁 Arquivos a Modificar

### 1. `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`
**Modificações**:
- Alterar tipo do `@Output() messageSent`
- Modificar método `sendMessage()` para emitir objeto `{message, provider}`

### 2. `src/conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts`
**Modificações**:
- Atualizar assinatura de `handleSendMessage()` para receber objeto
- Passar `provider` para `AgentService.executeAgent()`

### 3. `src/conductor-web/src/app/services/agent.service.ts`
**Modificações**:
- Adicionar parâmetro `aiProvider?: string` em `executeAgent()`
- Incluir `ai_provider` no body do POST se fornecido

## 🔧 Tarefas Detalhadas

### ✅ Tarefa 2.1: Modificar Output `messageSent` no ChatInputComponent

**Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`

**Localização**: Procurar por `@Output() messageSent`

**Código Atual**:
```typescript
@Output() messageSent = new EventEmitter<string>();
```

**Código Modificado**:
```typescript
@Output() messageSent = new EventEmitter<{message: string, provider?: string}>();
```

**Justificativa**: Agora o evento emitirá um objeto com a mensagem e o provider selecionado (opcional).

---

### ✅ Tarefa 2.2: Modificar Método `sendMessage()` no ChatInputComponent

**Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`

**Localização**: Procurar método `sendMessage()` (aproximadamente linha 245-254)

**Código Atual**:
```typescript
sendMessage(): void {
  if (this.message.trim() && !this.isLoading) {
    this.messageSent.emit(this.message);  // Emite apenas string
    this.message = '';
    this.adjustTextareaHeight();
  }
}
```

**Código Modificado**:
```typescript
sendMessage(): void {
  if (this.message.trim() && !this.isLoading) {
    // Emite objeto com mensagem e provider (se selecionado)
    this.messageSent.emit({
      message: this.message,
      provider: this.selectedProvider || undefined  // undefined se vazio
    });
    this.message = '';
    this.adjustTextareaHeight();
    // Nota: NÃO limpar selectedProvider - manter seleção para próxima mensagem
  }
}
```

**Justificativa**:
- Envia `provider` como `undefined` (não string vazia) quando não selecionado
- Mantém `selectedProvider` após envio para reutilizar seleção

---

### ✅ Tarefa 2.3: Atualizar `handleSendMessage()` no ConductorChatComponent

**Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts`

**Localização**: Procurar método `handleSendMessage`

**Código Atual** (aproximadamente):
```typescript
handleSendMessage(message: string): void {
  // Validações...

  this.agentService.executeAgent(
    this.selectedAgentId!,
    message,
    this.activeInstanceId,
    this.currentCwd,
    this.screenplayId
  ).subscribe(/* ... */);
}
```

**Código Modificado**:
```typescript
handleSendMessage(data: {message: string, provider?: string}): void {
  // Validações existentes continuam iguais...

  this.agentService.executeAgent(
    this.selectedAgentId!,
    data.message,              // Usar data.message ao invés de message
    this.activeInstanceId,
    this.currentCwd,
    this.screenplayId,
    data.provider              // NOVO PARÂMETRO
  ).subscribe(/* ... */);
}
```

**Importante**: Ajustar também todas as referências a `message` dentro do método para `data.message`.

---

### ✅ Tarefa 2.4: Adicionar Parâmetro `aiProvider` no AgentService

**Arquivo**: `src/conductor-web/src/app/services/agent.service.ts`

**Localização**: Procurar método `executeAgent`

**Código Atual** (aproximadamente linha 66-79):
```typescript
executeAgent(
  agentId: string,
  inputText: string,
  instanceId?: string,
  cwd?: string,
  documentId?: string
): Observable<any> {
  const url = `${this.baseUrl}/api/agents/${agentId}/execute`;
  const body = {
    input_text: inputText,
    instance_id: instanceId,
    cwd: cwd,
    screenplay_id: documentId
  };
  // NÃO ENVIA ai_provider atualmente
  return this.http.post<any>(url, body);
}
```

**Código Modificado**:
```typescript
executeAgent(
  agentId: string,
  inputText: string,
  instanceId?: string,
  cwd?: string,
  documentId?: string,
  aiProvider?: string        // NOVO PARÂMETRO
): Observable<any> {
  const url = `${this.baseUrl}/api/agents/${agentId}/execute`;

  const body: any = {
    input_text: inputText,
    instance_id: instanceId,
    cwd: cwd,
    screenplay_id: documentId
  };

  // Adicionar ai_provider ao body apenas se fornecido
  if (aiProvider) {
    body.ai_provider = aiProvider;
  }

  return this.http.post<any>(url, body);
}
```

**Justificativa**:
- Adiciona `ai_provider` ao payload apenas quando presente
- Compatível com backend que já espera este campo (opcional)

---

## ✅ Checklist de Validação

Após implementação, verificar:

- [ ] **Tipo do Event**: `messageSent` emite `{message: string, provider?: string}`
- [ ] **Método sendMessage**: Emite objeto com `message` e `provider`
- [ ] **Provider Selecionado**: Quando dropdown = "Claude", `provider = "claude"`
- [ ] **Provider Padrão**: Quando dropdown = "Padrão", `provider = undefined`
- [ ] **ConductorChatComponent**: Recebe objeto e passa `provider` corretamente
- [ ] **AgentService**: Método `executeAgent()` aceita novo parâmetro
- [ ] **Payload HTTP**: POST inclui `ai_provider` apenas quando selecionado
- [ ] **Console**: Verificar payload no DevTools Network tab
- [ ] **Build**: Aplicação compila sem erros TypeScript
- [ ] **Runtime**: Nenhum erro no console do navegador

## 🧪 Teste Manual

Para validar o fluxo completo:

1. **Abrir DevTools** → aba Network
2. **Selecionar Provider** = "Claude" no dropdown
3. **Enviar mensagem** no chat
4. **Verificar Request** no Network tab:
   ```json
   {
     "input_text": "sua mensagem aqui",
     "instance_id": "uuid-aqui",
     "cwd": "/caminho/aqui",
     "screenplay_id": "doc-id",
     "ai_provider": "claude"  // ← Deve aparecer
   }
   ```

5. **Testar com Provider Padrão**:
   - Selecionar "Padrão"
   - Enviar mensagem
   - Verificar que `ai_provider` **NÃO aparece** no payload (ou é `null`)

6. **Testar com Gemini**:
   - Selecionar "Gemini"
   - Enviar mensagem
   - Verificar `"ai_provider": "gemini"`

## 📦 Entregáveis

1. ✅ `@Output() messageSent` modificado para emitir objeto
2. ✅ Método `sendMessage()` modificado para incluir provider
3. ✅ `handleSendMessage()` atualizado para receber objeto
4. ✅ `AgentService.executeAgent()` atualizado com parâmetro `aiProvider`
5. ✅ Payload HTTP incluindo `ai_provider` quando aplicável
6. ✅ Validação manual via DevTools confirmando payload correto

## 🔗 Próxima Fase

Após validação desta fase, prosseguir para:
- **Fase 3**: Backend Gateway - Modelos e Propagação
  - Adicionar campo `ai_provider` em `AgentExecuteRequest`
  - Propagar `ai_provider` no `ConductorClient.execute_agent()`
  - Validar comunicação com Conductor CLI API

## ⚠️ Observações Importantes

1. **NÃO implementar persistência**: Seleção de provider NÃO será salva em localStorage nesta fase
2. **NÃO validar providers**: Validação de providers válidos será feita no backend
3. **NÃO adicionar loading states**: Estados de loading já existem
4. **Manter seleção**: Provider selecionado deve permanecer após envio de mensagem

## 🎯 Critério de Sucesso

A fase será considerada completa quando:
1. Seleção de provider no frontend propagada até AgentService
2. Payload HTTP contém `ai_provider` quando selecionado
3. Payload HTTP NÃO contém `ai_provider` quando "Padrão" selecionado
4. Aplicação build e executa sem erros
5. DevTools Network confirma estrutura correta do payload
