# Conductor Chat

Chat and messaging integration layer for Conductor Community. Provides multi-platform messaging capabilities through primobot-core with a clean REST API adapter and MCP tools for AI agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          conductor-chat                              │
│                                                                      │
│  ┌────────────────────┐       ┌─────────────────────────────────┐   │
│  │   primobot-core    │       │          primobot-mcp           │   │
│  │      (fork)        │       │         (container)             │   │
│  │    RUNS ON HOST    │       │                                 │   │
│  │                    │       │  ┌───────────────────────────┐  │   │
│  │  ┌──────────────┐  │       │  │    REST API + OpenAPI     │  │   │
│  │  │   Gateway    │◄─┼───────┼──│    /send, /channels       │  │   │
│  │  │  port 18789  │  │       │  │    /openapi.json          │  │   │
│  │  │  (WebSocket) │  │       │  │    port 3100              │  │   │
│  │  └──────────────┘  │       │  └───────────────────────────┘  │   │
│  │                    │       │               │                 │   │
│  │  ┌──────────────┐  │       │               ▼                 │   │
│  │  │   Channels   │  │       │  ┌───────────────────────────┐  │   │
│  │  │  - Telegram  │  │       │  │       MCP Sidecar         │  │   │
│  │  │  - Discord   │  │       │  │    (reads OpenAPI)        │  │   │
│  │  │  - Slack     │  │       │  │    port 3101              │  │   │
│  │  │  - WhatsApp  │  │       │  └───────────────────────────┘  │   │
│  │  │  - Signal    │  │       │                                 │   │
│  │  │  - Web       │  │       │                                 │   │
│  │  └──────────────┘  │       └─────────────────────────────────┘   │
│  └────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Importante:** primobot-core roda no **host** (não em container) para melhor performance e integração com o sistema. O primobot-mcp roda em container com `network_mode: host` para acessar o gateway.

## Components

### primobot-core (fork) - Runs on Host

Fork of [moltbot](https://github.com/moltbot/moltbot) - a multi-platform personal AI assistant.

**Features:**
- Multi-channel messaging (Telegram, Discord, Slack, WhatsApp, Signal, iMessage, Web)
- Gateway server with WebSocket RPC protocol (v3)
- OpenAI-compatible API
- Plugin/extension system
- 80+ gateway methods disponíveis

**Kept as fork to:**
- Maintain upstream compatibility
- Receive updates easily
- Avoid modifying original codebase

**Config location:** `~/.clawdbot/moltbot.json`

### primobot-mcp (adapter) - Runs in Container

REST API adapter/facade that bridges primobot-core to the Primoia ecosystem.

**Features:**
- Clean REST API with OpenAPI 3.0 specification
- Connects to primobot-core gateway via WebSocket
- Token-based authentication (no device identity required)
- Swagger UI for interactive API documentation
- Generic gateway proxy for all 80+ methods

**Why this architecture:**
- Isolates primobot-core complexity
- Provides documented API (OpenAPI)
- Enables MCP tool integration without modifying the fork
- Allows Conductor to send/receive messages through any channel

## Quick Start (Recommended)

Use the unified PrimoIA startup script:

```bash
# From primoia root directory
./start-primoia.sh
```

This starts all infrastructure including conductor-chat services.

To stop:
```bash
./stop-primoia.sh
```

## Manual Start

### 1. Start primobot-core (on host)

```bash
cd primobot-core
pnpm install
pnpm build
pnpm gateway:watch  # or: pnpm moltbot gateway --port 18789
```

### 2. Start primobot-mcp (in container)

```bash
cd primobot-mcp

# Configure token from ~/.clawdbot/moltbot.json -> gateway.auth.token
cp .env.example .env
# Edit .env and set GATEWAY_TOKEN

# Start container
docker compose up -d
```

Or run on host:
```bash
cd primobot-mcp
pnpm install
pnpm dev
```

### 3. (Optional) Start MCP Sidecar

```bash
cd shared/primoia-mcp-sidecar
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
TARGET_URL=http://localhost:3100 MCP_PORT=3101 MCP_NAME=primobot-chat python server.py
```

## Ports

| Service | Port | Description |
|---------|------|-------------|
| primobot-core | 18789 | WebSocket Gateway (host) |
| primobot-mcp | 3100 | REST API (container) |
| MCP Sidecar | 3101 | MCP Protocol (optional) |

## Configuration

### primobot-mcp/.env

```env
# Token from ~/.clawdbot/moltbot.json -> gateway.auth.token
GATEWAY_TOKEN=your-token-here

# Gateway URL (localhost because of network_mode: host)
PRIMOBOT_CORE_URL=http://localhost:18789

# Logging
LOG_LEVEL=info
NODE_ENV=development
```

### Gateway Authentication

O primobot-mcp usa autenticação por token para conectar ao gateway:

1. O token está em `~/.clawdbot/moltbot.json` no campo `gateway.auth.token`
2. Copie o token para `primobot-mcp/.env` como `GATEWAY_TOKEN`
3. Não é necessário device identity - apenas o token é suficiente

### Gateway Protocol

O primobot-mcp implementa o protocolo WebSocket v3 do gateway:

```typescript
// Connect handshake
{
  type: 'req',
  id: 'connect',
  method: 'connect',
  params: {
    minProtocol: 3,
    maxProtocol: 3,
    client: {
      id: 'gateway-client',    // Valid: gateway-client, node-host, cli, webchat
      version: '0.1.0',
      platform: 'node',
      mode: 'backend',         // Valid: backend, node, cli, webchat, ui
    },
    auth: {
      token: 'your-token',
    },
  }
}

// Response contains hello-ok in payload
{
  type: 'res',
  id: 'connect',
  ok: true,
  payload: {
    type: 'hello-ok',
    protocol: 3,
    server: { version, connId },
    features: { methods: [...], events: [...] }
  }
}
```

## API Endpoints

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (includes gateway status) |
| `GET` | `/openapi.json` | OpenAPI 3.0 specification |
| `GET` | `/docs` | Swagger UI |

### Gateway
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/gateway/health` | Gateway health status |
| `GET` | `/gateway/status` | Full gateway status with available methods |
| `POST` | `/gateway/:method` | Generic gateway method proxy (80+ methods) |

### Messaging
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/channels` | List available channels |
| `POST` | `/send` | Send message to recipient |
| `POST` | `/poll` | Send poll to recipient |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/chat/send` | Send message via WebChat |
| `GET` | `/chat/history` | Get chat history |

### Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/sessions` | List all sessions |
| `GET` | `/agents` | List available agents |
| `GET` | `/models` | List available models |
| `GET` | `/config` | Get configuration |

## Example Usage

### Check health
```bash
curl http://localhost:3100/health
# {"status":"ok","gateway":{"connected":true}}
```

### List available gateway methods
```bash
curl http://localhost:3100/gateway/status | jq '.features.methods'
```

### Send a message
```bash
curl -X POST http://localhost:3100/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+5511999999999",
    "message": "Hello from Conductor!",
    "channel": "whatsapp"
  }'
```

### Use generic gateway proxy
```bash
# Call any gateway method
curl -X POST http://localhost:3100/gateway/sessions.list \
  -H "Content-Type: application/json" \
  -d '{}'
```

## API Documentation

- **Swagger UI**: http://localhost:3100/docs
- **OpenAPI Spec**: http://localhost:3100/openapi.json

## Troubleshooting

### Gateway not connected

Se `/health` mostrar `"gateway":{"connected":false}`:

1. Verifique se primobot-core está rodando: `curl http://localhost:18789`
2. Verifique o token em `.env` (deve ser igual ao de `~/.clawdbot/moltbot.json`)
3. Verifique os logs: `docker compose logs -f primobot-mcp`

### Connection timeout

Se o MCP não conseguir conectar:

1. Verifique se está usando `network_mode: host` no docker-compose
2. Verifique se a URL é `http://localhost:18789` (não IP do Docker)

### Invalid client ID

Se aparecer erro "client/id must be equal to constant":
- O client.ts deve usar `id: 'gateway-client'` (não 'primobot-mcp')
- Valores válidos: gateway-client, node-host, cli, webchat

### Protocol mismatch

Se aparecer erro de versão de protocolo:
- O gateway usa protocolo v3
- O client.ts deve usar `minProtocol: 3, maxProtocol: 3`

## Available Gateway Methods (80+)

O gateway expõe diversos métodos via WebSocket que são proxied pelo REST API:

**System:** health, status, config.get, config.set, version

**Channels:** channels.status, channel.connect, channel.disconnect, send, poll

**Chat:** chat.send, chat.stream, chat.history, chat.clear

**Sessions:** sessions.list, sessions.get, sessions.create, sessions.fork, sessions.delete

**Agents:** agents.list, agents.get, agents.default

**Models:** models.list, models.capabilities

**Skills:** skills.list, skills.get, skills.enable, skills.disable

**Devices:** devices.list, devices.me, devices.revoke

**E mais:** tts, cron, nodes, execution approvals, etc.

Para lista completa: `curl http://localhost:3100/gateway/status | jq '.features.methods'`

## License

Proprietary - Primoia
