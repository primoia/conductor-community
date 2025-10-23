# ⚙️ Fase 3: Backend Gateway - Modelos e Propagação

## 📋 Metadados
- **ID**: fase-03
- **Título**: Backend Gateway - Modelos e Propagação de ai_provider
- **Executor**: Agente Backend
- **Dependências**: Fase 2 (Frontend já envia `ai_provider` no payload)
- **Status**: Pendente

## 🎯 Objetivo
Atualizar o backend Gateway (`conductor-gateway`) para receber o campo `ai_provider` do frontend e propagá-lo até o Conductor CLI API, completando a cadeia de comunicação.

## 📍 Contexto
O Conductor CLI (`src/conductor`) **já está preparado** para receber `ai_provider`:
- ✅ `ConductorExecuteRequest` já possui campo `ai_provider: Optional[str]`
- ✅ `Container.get_ai_provider()` já usa `cli_provider` na hierarquia de resolução
- ✅ `create_llm_client()` já instancia o cliente correto baseado no provider

**O que falta**: O Gateway (`conductor-gateway`) precisa ser o "mensageiro" entre frontend e CLI.

## 📁 Arquivos a Modificar

### 1. `src/conductor-gateway/src/api/routes/agents.py`
**Modificações**:
- Adicionar campo `ai_provider` ao modelo `AgentExecuteRequest`
- Passar `ai_provider` para `ConductorClient.execute_agent()`

### 2. `src/conductor-gateway/src/clients/conductor_client.py`
**Modificações**:
- Adicionar parâmetro `ai_provider` no método `execute_agent()`
- Incluir `ai_provider` no payload enviado para Conductor CLI API

## 🔧 Tarefas Detalhadas

### ✅ Tarefa 3.1: Adicionar Campo `ai_provider` ao Modelo de Request

**Arquivo**: `src/conductor-gateway/src/api/routes/agents.py`

**Localização**: Procurar classe `AgentExecuteRequest` (modelo Pydantic)

**Código Atual** (aproximadamente linha 174-183):
```python
class AgentExecuteRequest(BaseModel):
    """Payload para execução de agente."""
    input_text: str
    instance_id: Optional[str] = None
    context_mode: str = "stateless"
    cwd: Optional[str] = None
    screenplay_id: Optional[str] = None
    # ai_provider: Optional[str] = None  # COMENTADO OU AUSENTE
```

**Código Modificado**:
```python
class AgentExecuteRequest(BaseModel):
    """Payload para execução de agente."""
    input_text: str
    instance_id: Optional[str] = None
    context_mode: str = "stateless"
    cwd: Optional[str] = None
    screenplay_id: Optional[str] = None
    ai_provider: Optional[str] = None  # ADICIONAR ESTA LINHA
```

**Justificativa**:
- Campo opcional: compatível com requisições antigas que não enviam provider
- Pydantic validará automaticamente o tipo

---

### ✅ Tarefa 3.2: Passar `ai_provider` para ConductorClient no Router

**Arquivo**: `src/conductor-gateway/src/api/routes/agents.py`

**Localização**: Procurar endpoint `@router.post("/{agent_id}/execute")`

**Código Atual** (aproximadamente):
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
        # ai_provider NÃO ESTÁ SENDO PASSADO
    )

    return result
```

**Código Modificado**:
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
        ai_provider=request.ai_provider,  # ADICIONAR ESTA LINHA
    )

    return result
```

**Justificativa**: Propaga o campo `ai_provider` recebido do frontend para o ConductorClient.

---

### ✅ Tarefa 3.3: Adicionar Parâmetro `ai_provider` no ConductorClient

**Arquivo**: `src/conductor-gateway/src/clients/conductor_client.py`

**Localização**: Procurar método `execute_agent` (aproximadamente linha 93-125)

**Código Atual**:
```python
async def execute_agent(
    agent_name: str,
    prompt: str,
    instance_id: str | None = None,
    context_mode: str = "stateless",
    cwd: str | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    """
    Executa um agente no Conductor CLI.

    Args:
        agent_name: Nome do agente a executar
        prompt: Prompt/mensagem do usuário
        instance_id: ID da instância (para contexto stateful)
        context_mode: Modo de contexto (stateless/stateful)
        cwd: Diretório de trabalho atual
        timeout: Timeout em segundos

    Returns:
        dict: Resultado da execução do agente
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
    # NÃO INCLUI ai_provider

    # POST para http://conductor-api:8000/conductor/execute
    # ... código de envio
```

**Código Modificado**:
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

    Args:
        agent_name: Nome do agente a executar
        prompt: Prompt/mensagem do usuário
        instance_id: ID da instância (para contexto stateful)
        context_mode: Modo de contexto (stateless/stateful)
        cwd: Diretório de trabalho atual
        timeout: Timeout em segundos
        ai_provider: Provider de IA a usar (claude, gemini, etc.)

    Returns:
        dict: Resultado da execução do agente
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
        payload["ai_provider"] = ai_provider  # ADICIONAR ESTA LINHA

    # POST para http://conductor-api:8000/conductor/execute
    # ... código de envio (continua igual)
```

**Justificativa**:
- Adiciona `ai_provider` ao payload apenas quando fornecido
- Mantém compatibilidade com código existente (parâmetro opcional)

---

## ✅ Checklist de Validação

Após implementação, verificar:

- [ ] **Modelo Atualizado**: `AgentExecuteRequest` possui campo `ai_provider: Optional[str]`
- [ ] **Router Propagando**: Endpoint `/api/agents/{id}/execute` passa `ai_provider` para client
- [ ] **Client Atualizado**: `ConductorClient.execute_agent()` aceita parâmetro `ai_provider`
- [ ] **Payload Montado**: Payload HTTP para Conductor CLI inclui `ai_provider` quando fornecido
- [ ] **Type Hints**: Todos os type hints corretos (Python typing)
- [ ] **Linting**: Código passa em verificações de lint (`ruff`, `mypy`, etc.)
- [ ] **Imports**: Nenhum import adicional necessário (usa `Optional` de `typing`)

## 🧪 Teste Manual

### Cenário 1: Provider Selecionado (Claude)

1. **Frontend**: Selecionar "Claude" e enviar mensagem
2. **Gateway Logs**: Verificar payload recebido:
   ```python
   # Em agents.py, adicionar log temporário:
   logger.info(f"📥 [GATEWAY] Recebido: ai_provider={request.ai_provider}")
   ```
3. **Conductor CLI Logs**: Verificar no Conductor CLI:
   ```python
   # Em conductor_cli.py, verificar log:
   logger.info(f"🔍 [CLI] request.ai_provider: {request.ai_provider}")
   logger.info(f"✅ [CLI] Provider final: {provider}")
   ```

**Resultado Esperado**:
```
📥 [GATEWAY] Recebido: ai_provider=claude
🔍 [CLI] request.ai_provider: claude
✅ [CLI] Provider final: claude
```

### Cenário 2: Provider Padrão (None)

1. **Frontend**: Selecionar "Padrão" e enviar mensagem
2. **Verificar Logs**

**Resultado Esperado**:
```
📥 [GATEWAY] Recebido: ai_provider=None
🔍 [CLI] request.ai_provider: None
✅ [CLI] Provider final: gemini  # (ou outro padrão do config.yaml)
```

### Cenário 3: Testar Hierarquia de Resolução

Criar agente com `ai_provider: gemini` no `definition.yaml`:
1. **Enviar sem selecionar provider** → Deve usar Gemini (do agent definition)
2. **Enviar selecionando Claude** → Deve usar Claude (frontend sobrepõe)

**Hierarquia Validada**:
1. ✅ Frontend (`cli_provider`) - maior prioridade
2. ✅ Agent Definition (`agent_definition.ai_provider`)
3. ✅ Config Default (`config.yaml`)
4. ✅ Fallback

## 📦 Entregáveis

1. ✅ Campo `ai_provider` adicionado em `AgentExecuteRequest`
2. ✅ Router passando `ai_provider` para `ConductorClient`
3. ✅ `ConductorClient.execute_agent()` com parâmetro `ai_provider`
4. ✅ Payload HTTP incluindo `ai_provider` no POST para Conductor CLI
5. ✅ Logs de diagnóstico confirmando propagação correta
6. ✅ Hierarquia de resolução validada com testes manuais

## 🔗 Próximos Passos (Pós-Saga)

Após validação desta fase, considerar melhorias futuras:
1. **Persistência de Provider**: Salvar preferência em MongoDB ou localStorage
2. **Validação de Provider**: Retornar apenas providers disponíveis/instalados
3. **Feedback Visual**: Badge indicando provider usado em cada resposta
4. **Implementar cursor-agent**: Adicionar suporte a Cursor Agent CLI
5. **Configuração de Timeout por Provider**: Timeouts específicos por provider

## ⚠️ Observações Importantes

1. **Backend CLI já está pronto**: Não é necessário modificar nada em `src/conductor`
2. **Validação de providers**: Conductor CLI já valida providers em `create_llm_client()`
3. **Erro ao usar provider inválido**: Sistema levanta `LLMClientError` automaticamente
4. **Compatibilidade**: Mudanças são retrocompatíveis (campo opcional)

## 🎯 Critério de Sucesso

A fase será considerada completa quando:
1. Gateway recebe `ai_provider` do frontend sem erros
2. Gateway propaga `ai_provider` para Conductor CLI
3. Conductor CLI usa `cli_provider` na hierarquia de resolução
4. Logs confirmam provider correto sendo usado
5. Testes manuais validam todos os cenários:
   - Provider selecionado (Claude/Gemini) → usa selecionado
   - Provider padrão → usa config.yaml
   - Provider no agent definition → respeitado quando frontend não envia

## 🎉 Conclusão da Saga

Com a conclusão desta fase, o fluxo completo estará implementado:

```
[Frontend] Usuário seleciona provider
    ↓
[ChatInputComponent] Emite {message, provider}
    ↓
[ConductorChatComponent] Chama AgentService
    ↓
[AgentService] POST /api/agents/{id}/execute { ai_provider: "claude" }
    ↓
[Gateway: AgentRouter] Recebe AgentExecuteRequest
    ↓
[ConductorClient] POST /conductor/execute { ai_provider: "claude" }
    ↓
[Conductor CLI] Container.get_ai_provider(cli_provider="claude")
    ↓
[LLM Factory] create_llm_client("claude")
    ↓
[ClaudeCLIClient] Executa claude code CLI
    ↓
[Resposta] Retorna resultado para frontend
```

✅ **Funcionalidade completa e end-to-end testada!**
