# Primobot MCP Implementation Guide

Guia para implementar melhorias no MCP baseado na análise de sincronização.

**Documento de referência:** `MCP_SYNC_ANALYSIS.md`

---

## Padrões de Implementação

### Estrutura de uma Tool

```typescript
// Em mcp-server.ts

// 1. Definir a tool com schema
const tools: Tool[] = [
  {
    name: 'primobot_example',
    description: 'Descrição clara do que faz e quando usar',
    inputSchema: {
      type: 'object',
      properties: {
        requiredParam: {
          type: 'string',
          description: 'O que é e como usar',
        },
        optionalParam: {
          type: 'number',
          description: 'Descrição',
          default: 10,
        },
      },
      required: ['requiredParam'],
    },
  },
];

// 2. Implementar handler no switch
case 'primobot_example':
  return gatewayClient.request('method.name', {
    param: args.requiredParam as string,
    // ... mapear parâmetros
  });
```

### Adicionando Método ao GatewayClient

```typescript
// Em gateway-client/client.ts

// Adicionar método de conveniência
async exampleMethod(params: {
  required: string;
  optional?: number;
}): Promise<unknown> {
  return this.request('method.name', params);
}
```

---

## Implementações Pendentes

### P1: Resolução Inteligente de Destinatário

**Objetivo:** `primobot_send` funcionar sem `to` explícito.

**Arquivos a modificar:**
- `primobot-mcp/src/mcp-server.ts`

**Implementação:**

```typescript
// Adicionar helper no topo do arquivo
interface ResolvedRecipient {
  to: string;
  channel: string;
  accountId?: string;
}

async function resolveRecipient(
  client: GatewayClient,
  params: { to?: string; channel?: string }
): Promise<ResolvedRecipient> {
  const channel = params.channel || 'telegram';

  // Se to explícito e não é alias
  if (params.to && !['me', 'owner', 'self'].includes(params.to.toLowerCase())) {
    return { to: params.to, channel };
  }

  // Buscar sessões do canal
  const result = await client.request('sessions.list', {
    limit: 10,
    includeGlobal: false,
    includeUnknown: false,
  }) as { sessions: Array<{ key: string; channel?: string; lastTo?: string; lastChannel?: string; lastAccountId?: string }> };

  const sessions = result.sessions || [];

  // Filtrar por canal
  const filtered = sessions.filter(s =>
    s.channel === channel || s.key?.startsWith(`${channel}:`)
  );

  // Preferir sessão com lastTo
  const withLastTo = filtered.find(s => s.lastTo);
  if (withLastTo?.lastTo) {
    return {
      to: withLastTo.lastTo,
      channel: withLastTo.lastChannel || channel,
      accountId: withLastTo.lastAccountId,
    };
  }

  // Fallback: extrair do key
  const session = filtered[0];
  if (session?.key) {
    const match = session.key.match(new RegExp(`${channel}:(\\d+)`));
    if (match) {
      return { to: match[1], channel };
    }
  }

  throw new Error(
    `No active ${channel} session found. Specify recipient with "to" parameter.`
  );
}

// Modificar handler de send
case 'primobot_send': {
  const resolved = await resolveRecipient(gatewayClient, {
    to: args.to as string | undefined,
    channel: args.channel as string | undefined,
  });

  return gatewayClient.send({
    to: resolved.to,
    message: args.message as string,
    channel: resolved.channel,
    accountId: resolved.accountId || (args.accountId as string),
  });
}
```

**Atualizar schema da tool:**

```typescript
{
  name: 'primobot_send',
  description: 'Send a message via messaging channel. If "to" is omitted, sends to most recent active session.',
  inputSchema: {
    type: 'object',
    properties: {
      message: {
        type: 'string',
        description: 'The message text to send',
      },
      to: {
        type: 'string',
        description: 'Recipient (chat ID, username, or "me"). Optional - uses recent session if omitted.',
      },
      channel: {
        type: 'string',
        description: 'Channel (telegram, whatsapp, discord). Default: telegram',
        default: 'telegram',
      },
      // ... resto
    },
    required: ['message'],  // <-- to não é mais required
  },
}
```

**Testes:**
```bash
# Com to explícito (backward compat)
primobot_send({ to: "123456789", message: "teste" })

# Sem to (nova funcionalidade)
primobot_send({ message: "teste" })

# Com alias
primobot_send({ to: "me", message: "teste" })
```

---

### P2: Filtros em Sessions

**Objetivo:** `primobot_sessions` aceitar parâmetros de filtro.

**Implementação:**

```typescript
// Atualizar schema
{
  name: 'primobot_sessions',
  description: 'List chat sessions with optional filters',
  inputSchema: {
    type: 'object',
    properties: {
      channel: {
        type: 'string',
        description: 'Filter by channel (telegram, whatsapp, etc)',
      },
      limit: {
        type: 'number',
        description: 'Max sessions to return',
        default: 10,
      },
      activeMinutes: {
        type: 'number',
        description: 'Only sessions active in last N minutes',
      },
      search: {
        type: 'string',
        description: 'Search in session name/label',
      },
    },
  },
}

// Atualizar handler
case 'primobot_sessions': {
  const params: Record<string, unknown> = {
    limit: (args.limit as number) || 10,
    includeGlobal: false,
    includeUnknown: false,
  };

  if (args.activeMinutes) {
    params.activeMinutes = args.activeMinutes;
  }
  if (args.search) {
    params.search = args.search;
  }

  const result = await gatewayClient.sessionsList(params);

  // Filtrar por channel client-side se especificado
  if (args.channel && result.sessions) {
    result.sessions = result.sessions.filter((s: any) =>
      s.channel === args.channel || s.key?.startsWith(`${args.channel}:`)
    );
  }

  return result;
}
```

---

### P3: Expor Parâmetros de Mídia no Send

**Objetivo:** Permitir enviar mídia via `primobot_send`.

```typescript
{
  name: 'primobot_send',
  inputSchema: {
    properties: {
      // ... existentes ...
      mediaUrl: {
        type: 'string',
        description: 'URL of media to attach (image, video, audio)',
      },
      mediaUrls: {
        type: 'array',
        items: { type: 'string' },
        description: 'Multiple media URLs',
      },
    },
  },
}

// Handler
case 'primobot_send': {
  return gatewayClient.send({
    to: resolved.to,
    message: args.message as string,
    channel: resolved.channel,
    mediaUrl: args.mediaUrl as string | undefined,
    mediaUrls: args.mediaUrls as string[] | undefined,
    // ...
  });
}
```

---

### P4: Nova Tool - primobot_abort

**Objetivo:** Cancelar operação em andamento.

```typescript
{
  name: 'primobot_abort',
  description: 'Abort a running chat operation',
  inputSchema: {
    type: 'object',
    properties: {
      sessionKey: {
        type: 'string',
        description: 'Session to abort. If omitted, aborts all.',
      },
      runId: {
        type: 'string',
        description: 'Specific run ID to abort',
      },
    },
  },
}

// Handler
case 'primobot_abort':
  return gatewayClient.request('chat.abort', {
    sessionKey: args.sessionKey as string,
    runId: args.runId as string | undefined,
  });
```

---

### P5: Nova Tool - primobot_usage

**Objetivo:** Ver consumo de tokens.

```typescript
{
  name: 'primobot_usage',
  description: 'Get token usage statistics',
  inputSchema: {
    type: 'object',
    properties: {},
  },
}

// Handler
case 'primobot_usage':
  return gatewayClient.request('usage.status', {});
```

---

## Checklist de Implementação

Para cada mudança:

- [ ] Atualizar schema da tool em `tools[]`
- [ ] Atualizar handler no `switch`
- [ ] Adicionar método helper se necessário em `gateway-client/client.ts`
- [ ] Testar backward compatibility
- [ ] Testar nova funcionalidade
- [ ] Atualizar `MCP_SYNC_ANALYSIS.md`

---

## Testes Manuais

### Testar via Claude Code

```bash
# Reiniciar MCP após mudanças
# No Claude Code, usar tools diretamente

# Exemplo de teste
"Use primobot_send para enviar 'teste' para telegram"
# Deve funcionar sem especificar 'to'
```

### Testar via curl (API REST)

Se usando o container primobot-api:

```bash
# Health check
curl http://localhost:12198/health

# Send message
curl -X POST http://localhost:12198/api/send \
  -H "Content-Type: application/json" \
  -d '{"message": "teste"}'
```

---

## Versionamento

Ao fazer mudanças significativas:

1. Atualizar versão em `mcp-server.ts`:
   ```typescript
   const server = new Server({
     name: 'primobot-mcp',
     version: '0.2.0',  // incrementar
   }, ...);
   ```

2. Documentar mudanças no commit

3. Atualizar `MCP_SYNC_ANALYSIS.md` com data da análise

---

## Troubleshooting

### MCP não conecta ao gateway

```bash
# Verificar se gateway está rodando
curl http://localhost:18789/health

# Verificar token
cat ~/.clawdbot/moltbot.json | jq '.gateway.auth.token'
```

### Tool retorna erro de validação

Verificar se parâmetros batem com schema do gateway em:
`primobot-core/src/gateway/protocol/schema/`

### Mudanças não refletem

```bash
# Reiniciar Claude Code para recarregar MCP
# Ou verificar se .mcp.json aponta para arquivo correto
```
