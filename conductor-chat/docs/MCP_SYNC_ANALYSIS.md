# Primobot MCP Sync Analysis

Este documento serve como referência para manter o MCP sincronizado com a evolução do gateway primobot-core.

**Última análise:** 2025-01-30
**Versão do gateway analisada:** commit atual do fork

---

## Como Usar Este Documento

### Quando Atualizar
- Após merge de mudanças do upstream (moltbot)
- Ao adicionar novos métodos ao gateway
- Ao modificar schemas de parâmetros
- Periodicamente para revisão

### Metodologia de Análise

1. **Listar métodos do gateway:**
   ```bash
   # Ver arquivo de métodos
   cat primobot-core/src/gateway/server-methods-list.ts
   ```

2. **Comparar com tools do MCP:**
   ```bash
   # Ver tools expostas
   cat primobot-mcp/src/mcp-server.ts
   ```

3. **Verificar schemas de parâmetros:**
   ```bash
   # Schemas de validação
   ls primobot-core/src/gateway/protocol/schema/
   ```

4. **Atualizar seções abaixo**

---

## Inventário de Métodos do Gateway

### Fonte
`primobot-core/src/gateway/server-methods-list.ts`

### Métodos Base (85+)

| Categoria | Métodos |
|-----------|---------|
| **Health/Status** | `health`, `status`, `channels.status`, `channels.logout` |
| **Messaging** | `send`, `poll` |
| **Chat (WebSocket)** | `chat.send`, `chat.history`, `chat.abort`, `chat.inject` |
| **Sessions** | `sessions.list`, `sessions.preview`, `sessions.resolve`, `sessions.patch`, `sessions.reset`, `sessions.delete`, `sessions.compact` |
| **Config** | `config.get`, `config.set`, `config.apply`, `config.patch`, `config.schema` |
| **Agents** | `agent`, `agent.identity.get`, `agent.wait`, `agents.list` |
| **Models** | `models.list` |
| **Skills** | `skills.status`, `skills.bins`, `skills.install`, `skills.update` |
| **Cron** | `cron.list`, `cron.status`, `cron.add`, `cron.update`, `cron.remove`, `cron.run`, `cron.runs` |
| **Nodes** | `node.pair.*`, `node.list`, `node.describe`, `node.invoke`, `node.event`, `node.rename` |
| **Devices** | `device.pair.*`, `device.token.*` |
| **TTS** | `tts.status`, `tts.providers`, `tts.enable`, `tts.disable`, `tts.convert`, `tts.setProvider` |
| **Wizard** | `wizard.start`, `wizard.next`, `wizard.cancel`, `wizard.status` |
| **Misc** | `logs.tail`, `usage.status`, `usage.cost`, `voicewake.*`, `update.run`, `browser.request`, `talk.mode`, `wake` |
| **Exec Approvals** | `exec.approvals.*`, `exec.approval.request`, `exec.approval.resolve` |

---

## Mapeamento MCP ↔ Gateway

### Tools Atualmente Expostas

| MCP Tool | Gateway Method | Paridade | Notas |
|----------|----------------|----------|-------|
| `primobot_health` | `health` | ✅ Completo | |
| `primobot_status` | `status` | ✅ Completo | |
| `primobot_channels` | `channels.status` | ✅ Completo | |
| `primobot_send` | `send` | ⚠️ Parcial | Faltam: mediaUrl, mediaUrls, gifPlayback, sessionKey |
| `primobot_poll` | `poll` | ⚠️ Parcial | Faltam: durationHours, accountId |
| `primobot_sessions` | `sessions.list` | ❌ Mínimo | Nenhum parâmetro exposto |
| `primobot_chat_history` | `chat.history` | ✅ Completo | |
| `primobot_chat_send` | `chat.send` | ⚠️ Parcial | Faltam: thinking, deliver, attachments, timeoutMs |
| `primobot_agents` | `agents.list` | ✅ Completo | |
| `primobot_models` | `models.list` | ✅ Completo | |
| `primobot_config` | `config.get` | ⚠️ Parcial | Falta: key parameter |
| `primobot_gateway_call` | (any) | ✅ Escape hatch | |

### Métodos Úteis NÃO Expostos

| Método | Utilidade | Prioridade |
|--------|-----------|------------|
| `chat.abort` | Cancelar execução | Alta |
| `chat.inject` | Injetar mensagem | Média |
| `sessions.resolve` | Resolver alias | Alta |
| `usage.status` | Ver consumo tokens | Média |
| `logs.tail` | Debug em tempo real | Baixa |
| `cron.list` | Ver agendamentos | Baixa |

---

## Schema de Parâmetros por Método

### send
**Arquivo:** `primobot-core/src/gateway/protocol/schema/agent.ts`

```typescript
SendParamsSchema = {
  to: string            // OBRIGATÓRIO
  message: string       // OBRIGATÓRIO
  mediaUrl?: string     // URL de mídia única
  mediaUrls?: string[]  // Múltiplas mídias
  gifPlayback?: boolean // Reproduzir como GIF
  channel?: string      // Canal (telegram, whatsapp, etc)
  accountId?: string    // ID da conta se múltiplas
  sessionKey?: string   // Para espelhar no transcript
  idempotencyKey: string // Gerado pelo MCP
}
```

**MCP expõe:** to, message, channel, accountId
**MCP omite:** mediaUrl, mediaUrls, gifPlayback, sessionKey

### poll
**Arquivo:** `primobot-core/src/gateway/protocol/schema/agent.ts`

```typescript
PollParamsSchema = {
  to: string             // OBRIGATÓRIO
  question: string       // OBRIGATÓRIO
  options: string[]      // 2-12 opções
  maxSelections?: number // 1-12
  durationHours?: number // Duração da poll
  channel?: string
  accountId?: string
  idempotencyKey: string
}
```

**MCP expõe:** to, question, options, channel, maxSelections
**MCP omite:** durationHours, accountId

### sessions.list
**Arquivo:** `primobot-core/src/gateway/protocol/schema/sessions.ts`

```typescript
SessionsListParamsSchema = {
  limit?: number              // Limitar resultados
  activeMinutes?: number      // Filtrar por atividade
  includeGlobal?: boolean     // Incluir sessão global
  includeUnknown?: boolean    // Incluir sessão unknown
  includeDerivedTitles?: boolean  // Derivar títulos
  includeLastMessage?: boolean    // Preview última msg
  label?: string              // Filtrar por label
  spawnedBy?: string          // Filtrar por parent
  agentId?: string            // Filtrar por agente
  search?: string             // Busca textual
}
```

**MCP expõe:** NENHUM
**MCP omite:** TODOS

### chat.send
**Arquivo:** `primobot-core/src/gateway/protocol/schema/logs-chat.ts`

```typescript
ChatSendParamsSchema = {
  sessionKey: string      // OBRIGATÓRIO
  message: string
  thinking?: string       // Nível de thinking
  deliver?: boolean       // Entregar resposta
  attachments?: unknown[] // Anexos
  timeoutMs?: number      // Timeout
  idempotencyKey: string
}
```

**MCP expõe:** message, sessionKey
**MCP omite:** thinking, deliver, attachments, timeoutMs

### chat.history
**Arquivo:** `primobot-core/src/gateway/protocol/schema/logs-chat.ts`

```typescript
ChatHistoryParamsSchema = {
  sessionKey: string  // OBRIGATÓRIO
  limit?: number      // 1-1000
}
```

**MCP expõe:** sessionKey, limit ✅

### config.get
**Arquivo:** `primobot-core/src/gateway/protocol/schema/config.ts`

```typescript
ConfigGetParamsSchema = {
  key?: string  // Caminho específico
}
```

**MCP expõe:** NENHUM
**MCP omite:** key

---

## Problemas de UX Identificados

### 1. Resolução de Destinatário (Crítico)

**Problema:** `send` e `poll` exigem `to` explícito.

**Impacto:** Claude precisa:
1. Chamar `sessions` primeiro
2. Parsear resposta para encontrar ID
3. Só então chamar `send`

**Solução proposta:** Resolver `to` automaticamente no MCP:
- Se omitido → usar sessão mais recente do canal
- Se "me"/"owner" → resolver para owner
- Se "@username" → buscar por username

### 2. Sessions sem Filtros (Crítico)

**Problema:** `primobot_sessions` retorna TUDO.

**Impacto:**
- Resposta muito grande
- Claude não consegue buscar sessão específica
- Overhead desnecessário

**Solução proposta:** Expor parâmetros:
```typescript
{
  channel?: string      // Filtrar por canal
  limit?: number        // Default: 10
  activeMinutes?: number
  search?: string
}
```

### 3. Confusão send vs chat_send (Médio)

**Problema:** Nomes não indicam a diferença.

**Diferença real:**
- `send` → Canal externo (telegram, whatsapp) - apenas entrega mensagem
- `chat_send` → WebChat interno - invoca agente IA

**Solução proposta:** Renomear ou documentar melhor:
- `primobot_send` → enviar para canal
- `primobot_chat` ou `primobot_webchat` → invocar agente

### 4. Sobreposição de Status (Baixo)

**Problema:** 3 tools retornam info similar:
- `health` → snapshot de saúde
- `status` → status completo
- `channels` → status de canais

**Solução proposta:** Consolidar ou documentar diferenças claramente.

---

## Retorno de Sessões (Referência)

Quando `sessions.list` é chamado, cada sessão retorna:

```typescript
{
  key: string           // Ex: "telegram:123456789"
  sessionId: string     // UUID
  channel?: string      // "telegram", "whatsapp", etc
  displayName?: string  // Nome legível
  label?: string        // Label customizado
  updatedAt?: number    // Timestamp última atividade
  lastTo?: string       // Último destinatário usado
  lastChannel?: string  // Último canal usado
  lastAccountId?: string
  // ... outros campos
}
```

**Campos úteis para resolver destinatário:**
- `key` → pode extrair ID (ex: "telegram:123456789" → "123456789")
- `lastTo` → destinatário já resolvido
- `channel` → canal da sessão

---

## Checklist de Sincronização

Ao atualizar o MCP após mudanças no gateway:

- [ ] Verificar novos métodos em `server-methods-list.ts`
- [ ] Comparar schemas em `protocol/schema/`
- [ ] Atualizar mapeamento neste documento
- [ ] Adicionar novas tools se necessário
- [ ] Atualizar parâmetros de tools existentes
- [ ] Testar tools afetadas
- [ ] Atualizar versão do MCP

---

## Arquivos de Referência

| Arquivo | Conteúdo |
|---------|----------|
| `primobot-core/src/gateway/server-methods-list.ts` | Lista de métodos |
| `primobot-core/src/gateway/server-methods.ts` | Handlers e autorização |
| `primobot-core/src/gateway/server-methods/*.ts` | Implementações |
| `primobot-core/src/gateway/protocol/schema/*.ts` | Schemas de parâmetros |
| `primobot-mcp/src/mcp-server.ts` | Tools do MCP |
| `primobot-mcp/src/gateway-client/client.ts` | Cliente WebSocket |

---

## Histórico de Análises

| Data | Analista | Mudanças |
|------|----------|----------|
| 2025-01-30 | Claude | Análise inicial completa |
