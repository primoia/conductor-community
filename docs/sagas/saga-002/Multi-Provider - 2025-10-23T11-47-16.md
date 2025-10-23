# 📝 Seleção de Provider no Chat - Análise de Requisitos

## 📋 Visão Geral

Este documento analisa a funcionalidade de **seleção de provider de IA (gemini, claude, cursor-agent) no chat** do Conductor Community. O objetivo é permitir que cada agente instanciado possa trocar o provider de IA antes de enviar uma mensagem através do botão de envio (`class="icon-button send-button"`).

A análise abrange três camadas principais:
- **Frontend**: `conductor-web` (Angular) - Interface do chat
- **BFF**: `conductor-gateway` (Python/FastAPI) - Gateway intermediário
- **CLI**: `conductor` (Python) - Motor de execução com suporte a múltiplos providers

## 🎯 Requisitos Identificados

### Requisitos Funcionais

- **RF1**: O usuário deve poder selecionar um provider de IA (gemini, claude, cursor-agent) antes de enviar uma mensagem no chat
- **RF2**: A seleção de provider deve ser por instância de agente (cada chat pode ter seu próprio provider)
- **RF3**: O provider selecionado deve sobrepor a configuração padrão do `config.yaml`
- **RF4**: A mudança de provider deve ser possível antes de cada envio de mensagem
- **RF5**: O sistema deve validar se o provider selecionado é suportado (claude, gemini)
- **RF6**: O provider selecionado deve ser enviado junto com a mensagem para o backend

### Requisitos Não-Funcionais

- **RNF1**: A seleção de provider não deve atrasar o envio da mensagem (processo síncrono simples)
- **RNF2**: O provider deve ser persistido no estado da instância do agente (localStorage ou MongoDB)
- **RNF3**: O sistema deve ter fallback para provider padrão caso nenhum seja selecionado

## 🔄 Fluxo do Processo Atual (Sem Seleção de Provider)

### 1. Início: Usuário Digita Mensagem

O usuário interage com o componente `ChatInputComponent` localizado em:
- **Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`

O template contém:
- Um `<textarea>` para entrada de texto
- Um botão de envio com `class="icon-button send-button"` (linha 30)
- Ícone de envio: ⬆️ (normal) ou ⏳ (enviando)

### 2. Processamento: Clique no Botão de Envio

Quando o usuário clica no botão:

1. **No Frontend** (`ChatInputComponent.sendMessage()` - linha 245-254):
   ```typescript
   sendMessage(): void {
     if (this.message.trim() && !this.isLoading) {
       this.messageSent.emit(this.message);  // Emite evento para componente pai
       this.message = '';
       this.adjustTextareaHeight();
     }
   }
   ```

2. **No Componente Pai** (`ConductorChatComponent.handleSendMessage()` - recebe evento):
   ```typescript
   handleSendMessage(message: string): void {
     // Valida se pode enviar (CWD definido, agente selecionado)
     // Chama AgentService.executeAgent()
   }
   ```

3. **No AgentService** (`src/conductor-web/src/app/services/agent.service.ts`):
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

4. **No Gateway** (conductor-gateway `/api/agents/{agent_id}/execute`):
   - Recebe o payload JSON
   - Valida os campos
   - Encaminha para o ConductorClient

5. **No ConductorClient** (`src/clients/conductor_client.py`):
   ```python
   async def execute_agent(
       agent_name: str,
       prompt: str,
       instance_id: str | None = None,
       context_mode: str = "stateless",
       cwd: str | None = None,
       timeout: int = 600,
   ) -> dict[str, Any]:
       payload = {
           "agent_name": agent_name,
           "prompt": prompt,
           "context_mode": context_mode,
           "timeout": timeout,
           "instance_id": instance_id,
           "cwd": cwd
           # NÃO ENVIA ai_provider atualmente
       }
       # POST para http://conductor-api:8000/conductor/execute
   ```

6. **No Conductor CLI API** (`src/api/routes/conductor_cli.py`):
   ```python
   @router.post("/conductor/execute")
   def execute_conductor(request: ConductorExecuteRequest):
       # request.ai_provider está disponível mas não está sendo enviado pelo frontend

       # Resolução hierárquica de provider:
       provider = container.get_ai_provider(
           agent_definition=agent_definition,
           cli_provider=request.ai_provider  # Seria usado aqui se enviado
       )
   ```

### 3. Finalização: Resposta Retornada

O Conductor CLI executa o agente usando o provider resolvido (atualmente sempre padrão do config.yaml), e a resposta é retornada via streaming SSE:
- Gateway recebe resultado do Conductor API
- Frontend recebe eventos SSE (`on_llm_new_token`, `result`, etc.)
- Mensagem do bot é exibida no chat com streaming em tempo real

## 🏗️ Componentes Principais

### Frontend (Angular)

#### 1. **ConductorChatComponent**
- **Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts`
- **Responsabilidade**: Orquestrador principal do chat
- **Funcionalidades**:
  - Gerencia estado do chat (`chatState.messages`, `isLoading`)
  - Coordena envio de mensagens entre subcomponentes
  - Gerencia dock de agentes (seleção, instâncias)
  - Controla modos: Ask Mode (💬) vs Agent Mode (🤖)

#### 2. **ChatInputComponent**
- **Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`
- **Responsabilidade**: Captura entrada do usuário e dispara envio
- **Local de Intervenção**:
  - **Template (linha 29-37)**: Botão de envio
  - **Método `sendMessage()`**: Emite evento `messageSent`
  - **NECESSÁRIO**: Adicionar seletor de provider antes do botão de envio

#### 3. **AgentService**
- **Arquivo**: `src/conductor-web/src/app/services/agent.service.ts`
- **Responsabilidade**: Comunicação com o backend (gateway)
- **Método Principal**: `executeAgent(agentId, inputText, instanceId, cwd, documentId)`
- **NECESSÁRIO**: Adicionar parâmetro `aiProvider?: string` e incluir no payload

#### 4. **ChatState (Estado do Chat)**
```typescript
export interface ChatState {
  messages: Message[];
  isConnected: boolean;
  isLoading: boolean;
  currentStreamingMessageId?: string;
  selectedProvider?: string;  // ADICIONAR: Provider selecionado
}
```

### Backend (Gateway - Python/FastAPI)

#### 1. **AgentRouter** (`src/api/routes/agents.py`)
- **Endpoint**: `POST /api/agents/{agent_id}/execute`
- **Modelo de Request Atual**:
  ```python
  class AgentExecuteRequest(BaseModel):
      input_text: str
      instance_id: Optional[str] = None
      context_mode: str = "stateless"
      cwd: Optional[str] = None
      screenplay_id: Optional[str] = None
      # ai_provider: Optional[str] = None  # ADICIONAR
  ```
- **Responsabilidade**: Receber requisição do frontend e validar dados
- **NECESSÁRIO**: Adicionar campo `ai_provider` ao modelo e passar para o ConductorClient

#### 2. **ConductorClient** (`src/clients/conductor_client.py`)
- **Método**: `execute_agent()`
- **Responsabilidade**: Comunicação com Conductor CLI API
- **Payload Enviado**:
  ```python
  payload = {
      "agent_name": agent_name,
      "prompt": prompt,
      "context_mode": context_mode,
      "timeout": timeout,
      "instance_id": instance_id,
      "cwd": cwd,
      # "ai_provider": ai_provider  # ADICIONAR
  }
  ```
- **NECESSÁRIO**: Adicionar parâmetro `ai_provider` e incluir no payload

### Backend (Conductor CLI - Python)

#### 1. **ConductorExecuteRequest** (`src/api/routes/conductor_cli.py` linha 61-97)
- **Modelo de Request**: JÁ POSSUI campo `ai_provider: Optional[str] = None`
- **Responsabilidade**: Receber requisições do gateway
- **Status**: ✅ **Já preparado para receber ai_provider**

#### 2. **Container** (`src/container.py` linha 163-213)
- **Método**: `get_ai_provider(agent_definition, cli_provider)`
- **Responsabilidade**: Resolver qual provider usar seguindo hierarquia
- **Hierarquia de Resolução** (do mais prioritário para menos):
  1. **CLI Provider** (`cli_provider` parameter) - **USADO QUANDO ENVIADO PELO FRONTEND**
  2. **Agent Definition** (`agent_definition.ai_provider`)
  3. **Config Default** (`config.yaml` → `ai_providers.default_providers.generation`)
  4. **Fallback** (`config.yaml` → `ai_providers.fallback_provider`)

#### 3. **LLM Client Factory** (`src/infrastructure/llm/cli_client.py` linha 228-274)
- **Função**: `create_llm_client(ai_provider, working_directory, timeout)`
- **Providers Suportados**:
  - `"claude"` → `ClaudeCLIClient`
  - `"gemini"` → `GeminiCLIClient`
  - Outros → `LLMClientError`
- **Responsabilidade**: Instanciar o cliente LLM correto baseado no provider

## 🔗 Relacionamentos e Dependências

### Fluxo de Dados Completo (Proposto com Provider)

```
[Usuário]
    ↓ digita mensagem + seleciona provider
[ChatInputComponent]
    ↓ emite evento messageSent(message, provider)
[ConductorChatComponent]
    ↓ chama AgentService.executeAgent()
[AgentService]
    ↓ HTTP POST /api/agents/{agent_id}/execute
    ↓ body: { input_text, instance_id, cwd, ai_provider }
[Gateway: AgentRouter]
    ↓ valida AgentExecuteRequest
    ↓ chama ConductorClient.execute_agent()
[ConductorClient]
    ↓ HTTP POST http://conductor-api:8000/conductor/execute
    ↓ body: { agent_name, prompt, instance_id, cwd, ai_provider }
[Conductor CLI API: conductor_cli.py]
    ↓ valida ConductorExecuteRequest
    ↓ chama Container.get_ai_provider(cli_provider=request.ai_provider)
[Container: get_ai_provider()]
    ↓ resolve provider (hierarquia)
    ↓ retorna "claude" | "gemini"
[TaskExecutionService]
    ↓ cria LLM client
[create_llm_client(ai_provider)]
    ↓ instancia ClaudeCLIClient ou GeminiCLIClient
[LLM Client]
    ↓ executa prompt via CLI
    ↓ retorna resposta
[Response Stream]
    ↓ SSE events (on_llm_new_token, result)
[Frontend]
    ↓ exibe resposta no chat
```

### Dependências de Comunicação

1. **Frontend ↔ Gateway**:
   - Protocolo: HTTP/HTTPS
   - Formato: JSON
   - Endpoints: `/api/agents/{agent_id}/execute`
   - Streaming: SSE (Server-Sent Events)

2. **Gateway ↔ Conductor CLI API**:
   - Protocolo: HTTP (interno via Docker)
   - URL: `http://conductor-api:8000/conductor/execute`
   - Formato: JSON

3. **Conductor CLI ↔ LLM Providers**:
   - Claude: Subprocess execução de `claude code` CLI
   - Gemini: Subprocess execução de Gemini CLI
   - Timeout: 600s (10 minutos)

## 💡 Regras de Negócio Identificadas

### 1. **Hierarquia de Resolução de Provider**
- **Descrição**: O sistema segue uma ordem de prioridade para determinar qual provider usar
- **Ordem**:
  1. Provider enviado pelo frontend (maior prioridade)
  2. Provider definido no arquivo `definition.yaml` do agente
  3. Provider padrão do `config.yaml` (`ai_providers.default_providers.generation`)
  4. Provider de fallback do `config.yaml` (`ai_providers.fallback_provider`)
- **Implementação**: `src/container.py:163-213` método `get_ai_provider()`

### 2. **Validação de Provider Suportado**
- **Descrição**: Apenas providers implementados são aceitos
- **Providers Válidos**: `"claude"`, `"gemini"`
- **Providers Configuráveis**: `"cursor-agent"` (aparece em config.yaml mas não tem implementação)
- **Implementação**: `src/infrastructure/llm/cli_client.py:263-274` - levanta `LLMClientError` se provider inválido

### 3. **Provider por Instância de Agente**
- **Descrição**: Cada instância de agente pode ter seu próprio provider
- **Identificação**: Via `instance_id` (UUID único por chat)
- **Contexto Isolado**: Conversas, CWD, e configurações são isoladas por instância
- **Implementação**: Sistema de instâncias no MongoDB via `AgentService`

### 4. **Obrigatoriedade de CWD para Agentes**
- **Descrição**: Antes de enviar mensagem com agente selecionado, CWD (Current Working Directory) deve estar definido
- **Validação**: Frontend bloqueia envio se agente selecionado mas sem CWD
- **Persistência**:
  - MongoDB: via `AgentService.updateInstanceCwd()`
  - Fallback: localStorage `agent-cwd-${instanceId}`
- **Implementação**: `ChatInputComponent` valida antes de emitir evento

### 5. **Timeout de Execução**
- **Descrição**: Requisições ao LLM têm timeout máximo para evitar travamentos
- **Valor Padrão**: 600 segundos (10 minutos)
- **Configurável**: Via parâmetro `--timeout` no CLI ou campo `timeout` na requisição
- **Implementação**: Passado para subprocess do LLM client

## 🎓 Conceitos-Chave

### 1. **Provider de IA (AI Provider)**
Refere-se ao serviço de inteligência artificial utilizado para processar as mensagens do chat. No Conductor, o provider determina qual CLI será executado:
- **Claude**: Usa `claude code` CLI da Anthropic
- **Gemini**: Usa Gemini CLI do Google
- **Cursor Agent**: Configurável mas sem implementação atual

### 2. **Instance ID**
UUID único que identifica uma conversa isolada com um agente. Permite:
- Manter histórico de conversação separado
- Configurações específicas (CWD, provider, etc.)
- Múltiplas conversas simultâneas com mesmo agente

### 3. **Context Mode**
Define como o histórico de conversação é gerenciado:
- **Stateless**: Sem histórico, cada mensagem é independente
- **Stateful**: Mantém histórico de conversação via `instance_id`

### 4. **CWD (Current Working Directory)**
Diretório de trabalho usado pelo agente durante execução. Necessário para:
- Operações de leitura/escrita de arquivos
- Execução de comandos shell
- Contexto de projeto

### 5. **SSE (Server-Sent Events)**
Protocolo usado para streaming de respostas em tempo real:
- Eventos: `on_llm_start`, `on_llm_new_token`, `result`, `error`
- Permite exibição progressiva da resposta do LLM
- Unidirecional: servidor → cliente

### 6. **Ask Mode vs Agent Mode**
Modos de operação do chat:
- **Ask Mode** (💬): Modo leitura, sem modificação de screenplay
- **Agent Mode** (🤖): Modo completo, pode executar agentes e modificar screenplay

## 📌 Plano de Implementação Proposto

### Fase 1: Frontend (conductor-web)

#### 1.1. Adicionar Seletor de Provider no Chat Input

**Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`

**Alterações no Template**:
```typescript
// Adicionar antes do botão de envio (linha ~25)
<div class="provider-selector">
  <label for="provider-select">IA Provider:</label>
  <select
    id="provider-select"
    [(ngModel)]="selectedProvider"
    class="provider-dropdown"
  >
    <option value="">Padrão (config.yaml)</option>
    <option value="claude">Claude</option>
    <option value="gemini">Gemini</option>
  </select>
</div>
```

**Alterações no Component**:
```typescript
export class ChatInputComponent {
  // Adicionar propriedade
  selectedProvider: string = '';  // '' = usar padrão

  // Modificar método sendMessage()
  sendMessage(): void {
    if (this.message.trim() && !this.isLoading) {
      this.messageSent.emit({
        message: this.message,
        provider: this.selectedProvider || undefined
      });
      this.message = '';
      this.adjustTextareaHeight();
    }
  }
}
```

**Alterações no Output**:
```typescript
// Mudar de:
@Output() messageSent = new EventEmitter<string>();

// Para:
@Output() messageSent = new EventEmitter<{message: string, provider?: string}>();
```

#### 1.2. Atualizar ConductorChatComponent

**Arquivo**: `src/conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts`

```typescript
handleSendMessage(data: {message: string, provider?: string}): void {
  // Validações existentes...

  // Adicionar provider na chamada
  this.agentService.executeAgent(
    this.selectedAgentId!,
    data.message,
    this.activeInstanceId,
    this.currentCwd,
    this.screenplayId,
    data.provider  // NOVO PARÂMETRO
  ).subscribe(/* ... */);
}
```

#### 1.3. Atualizar AgentService

**Arquivo**: `src/conductor-web/src/app/services/agent.service.ts`

```typescript
executeAgent(
  agentId: string,
  inputText: string,
  instanceId?: string,
  cwd?: string,
  documentId?: string,
  aiProvider?: string  // NOVO PARÂMETRO
): Observable<any> {
  const url = `${this.baseUrl}/api/agents/${agentId}/execute`;
  const body: any = {
    input_text: inputText,
    instance_id: instanceId,
    cwd: cwd,
    screenplay_id: documentId
  };

  // Adicionar provider se fornecido
  if (aiProvider) {
    body.ai_provider = aiProvider;
  }

  return this.http.post<any>(url, body);
}
```

#### 1.4. Persistir Provider Selecionado (Opcional)

Para manter o provider selecionado entre envios:

```typescript
// No ChatInputComponent
ngOnInit(): void {
  // Carregar provider salvo do localStorage
  const savedProvider = localStorage.getItem(`agent-provider-${this.instanceId}`);
  if (savedProvider) {
    this.selectedProvider = savedProvider;
  }
}

sendMessage(): void {
  // Salvar provider selecionado
  if (this.instanceId && this.selectedProvider) {
    localStorage.setItem(`agent-provider-${this.instanceId}`, this.selectedProvider);
  }
  // ... resto do código
}
```

### Fase 2: Backend Gateway (conductor-gateway)

#### 2.1. Atualizar Modelo de Request

**Arquivo**: `src/api/routes/agents.py`

```python
class AgentExecuteRequest(BaseModel):
    """Payload para execução de agente."""
    input_text: str
    instance_id: Optional[str] = None
    context_mode: str = "stateless"
    cwd: Optional[str] = None
    screenplay_id: Optional[str] = None
    ai_provider: Optional[str] = None  # ADICIONAR ESTE CAMPO
```

#### 2.2. Atualizar ConductorClient

**Arquivo**: `src/clients/conductor_client.py`

```python
async def execute_agent(
    agent_name: str,
    prompt: str,
    instance_id: str | None = None,
    context_mode: str = "stateless",
    cwd: str | None = None,
    timeout: int = 600,
    ai_provider: str | None = None,  # ADICIONAR PARÂMETRO
) -> dict[str, Any]:
    """
    Executa um agente no Conductor CLI.
    """
    payload = {
        "agent_name": agent_name,
        "prompt": prompt,
        "context_mode": context_mode,
        "timeout": timeout,
    }

    if instance_id:
        payload["instance_id"] = instance_id
    if cwd:
        payload["cwd"] = cwd
    if ai_provider:
        payload["ai_provider"] = ai_provider  # ADICIONAR AO PAYLOAD

    # Enviar para Conductor API
    # ... código existente
```

#### 2.3. Atualizar AgentRouter

**Arquivo**: `src/api/routes/agents.py`

```python
@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: str,
    request: AgentExecuteRequest,
    conductor_client: ConductorClient = Depends(get_conductor_client),
):
    """Executa um agente específico."""

    result = await conductor_client.execute_agent(
        agent_name=agent_id,
        prompt=request.input_text,
        instance_id=request.instance_id,
        context_mode=request.context_mode,
        cwd=request.cwd,
        timeout=600,
        ai_provider=request.ai_provider,  # PASSAR PROVIDER
    )

    return result
```

### Fase 3: Backend Conductor CLI (conductor)

**Status**: ✅ **JÁ IMPLEMENTADO**

O Conductor CLI já está preparado para receber o campo `ai_provider`:

1. **Modelo de Request**: `ConductorExecuteRequest` já possui campo `ai_provider: Optional[str]`
2. **Resolução Hierárquica**: `Container.get_ai_provider()` já usa `cli_provider` como maior prioridade
3. **Factory de LLM**: `create_llm_client()` já instancia o cliente correto baseado no provider

**Nenhuma alteração necessária nesta camada.**

### Fase 4: Testes e Validação

#### 4.1. Teste de Integração Completo

1. **Selecionar Provider no Frontend**:
   - Abrir chat
   - Selecionar "Gemini" no dropdown
   - Enviar mensagem
   - Verificar logs do backend para confirmar provider recebido

2. **Validar Hierarquia de Resolução**:
   - Testar com provider selecionado no frontend → deve usar selecionado
   - Testar sem seleção → deve usar padrão do config.yaml
   - Testar com agente que tem `ai_provider` em `definition.yaml` → deve usar do agente se frontend não enviar

3. **Validar Provider Inválido**:
   - Tentar enviar `ai_provider: "invalid"` → deve retornar erro ou usar fallback

4. **Persistência de Seleção**:
   - Selecionar provider
   - Enviar mensagem
   - Recarregar página
   - Verificar se provider ainda está selecionado

#### 4.2. Logs de Diagnóstico

Adicionar logs temporários para rastreamento:

```python
# No conductor_cli.py
logger.info("🔍 [CONDUCTOR_CLI] Determinando provider:")
logger.info(f"   - request.ai_provider: {request.ai_provider}")
logger.info(f"   - agent_definition.ai_provider: {agent_definition.ai_provider}")
logger.info(f"✅ [CONDUCTOR_CLI] Provider final: {provider}")
```

### Fase 5: Documentação e Refinamento

1. Atualizar README com nova funcionalidade
2. Adicionar comentários no código explicando a hierarquia
3. Criar diagramas de fluxo atualizados
4. Documentar limitações (cursor-agent não implementado)

## 📊 Estimativa de Esforço

| Fase | Componente | Esforço Estimado | Complexidade |
|------|-----------|------------------|--------------|
| 1 | Frontend - Seletor UI | 2-3 horas | Baixa |
| 1 | Frontend - Integração Service | 1-2 horas | Baixa |
| 2 | Gateway - Modelo Request | 30 min | Baixa |
| 2 | Gateway - ConductorClient | 1 hora | Baixa |
| 3 | Conductor CLI | 0 (já implementado) | - |
| 4 | Testes e Validação | 2-3 horas | Média |
| 5 | Documentação | 1-2 horas | Baixa |
| **TOTAL** | - | **8-12 horas** | **Baixa-Média** |

## 🚀 Próximos Passos Recomendados

1. **Decisão de Design UX**:
   - Dropdown simples vs. botões/badges?
   - Mostrar ícone do provider ativo?
   - Indicar provider em uso na mensagem do bot?

2. **Persistência de Preferência**:
   - Salvar no localStorage (por instância)?
   - Salvar no MongoDB (via API)?
   - Permitir configuração de provider padrão por usuário?

3. **Implementação de cursor-agent**:
   - Definir como integrar Cursor Agent CLI
   - Criar `CursorAgentCLIClient` em `cli_client.py`
   - Adicionar ao factory `create_llm_client()`

4. **Feedback Visual**:
   - Exibir badge do provider usado em cada mensagem do bot
   - Mostrar notificação ao trocar provider
   - Indicar no status bar qual provider está ativo

5. **Validação de Disponibilidade**:
   - Verificar se CLI do provider está instalado antes de usar
   - Mostrar apenas providers disponíveis no dropdown
   - Fallback automático se provider selecionado falhar

## ⚠️ Observações e Limitações Identificadas

### 1. Cursor Agent Não Implementado
- **Problema**: `cursor-agent` aparece em `config.yaml.example` mas não tem implementação em `cli_client.py`
- **Impacto**: Se usuário selecionar `cursor-agent`, receberá erro `LLMClientError`
- **Solução**: Remover opção do frontend OU implementar `CursorAgentCLIClient`

### 2. Validação de Provider no Frontend
- **Problema**: Frontend não valida se provider existe antes de enviar
- **Impacto**: Erro só aparece no backend, experiência ruim para usuário
- **Solução**: Validar choices no frontend conforme disponibilidade do backend

### 3. Falta de Feedback de Provider Usado
- **Problema**: Usuário não vê qual provider foi realmente usado na resposta
- **Impacto**: Difícil validar se hierarquia está funcionando
- **Solução**: Adicionar metadata na resposta do bot indicando provider

### 4. Timeout Fixo de 10 Minutos
- **Problema**: Providers diferentes podem precisar timeouts diferentes
- **Impacto**: Gemini pode ser mais rápido que Claude, mas usa mesmo timeout
- **Solução**: Permitir configuração de timeout por provider no config.yaml

### 5. Provider por Instância vs. Por Mensagem
- **Decisão Necessária**: Provider deve ser persistente por instância ou selecionável a cada mensagem?
- **Trade-offs**:
  - **Por instância**: Consistente, menos cliques, mas menos flexível
  - **Por mensagem**: Máxima flexibilidade, mas mais cliques
- **Recomendação**: Híbrido - salvar última seleção mas permitir mudança antes de cada envio

## 🎯 Conclusão

A implementação da seleção de provider no chat é **viável e de baixa complexidade**, pois:

✅ **Backend já está preparado**: Conductor CLI já possui toda a infraestrutura para receber e processar `ai_provider`

✅ **Mudanças minimamente invasivas**: Apenas adicionar campo nos modelos e passar parâmetro através das camadas

✅ **Hierarquia bem definida**: Sistema de resolução de provider já implementado e testado

✅ **Arquitetura suporta**: Separação clara entre frontend, gateway e CLI permite mudanças isoladas

⚠️ **Principais desafios**:
- Decidir melhor UX para seleção (dropdown, botões, etc.)
- Implementar ou remover opção `cursor-agent`
- Adicionar feedback visual do provider em uso
- Validar disponibilidade de providers antes de exibir

**Recomendação**: Começar implementação pela Fase 1 (Frontend) com dropdown simples, validar funcionamento end-to-end, e depois refinar UX baseado em feedback.
