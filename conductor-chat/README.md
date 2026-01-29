# Conductor Chat

Chat and messaging integration layer for Conductor Community. Provides multi-platform messaging capabilities through primobot-core with a clean REST API adapter and MCP tools for AI agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          conductor-chat                              │
│                                                                      │
│  ┌────────────────────┐       ┌─────────────────────────────────┐   │
│  │   primobot-core    │       │          primobot-mcp           │   │
│  │      (fork)        │       │                                 │   │
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
│                                                                      │
│  docker-compose.yml (orchestrates all services)                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### primobot-core (fork)

Fork of [moltbot](https://github.com/moltbot/moltbot) - a multi-platform personal AI assistant.

**Features:**
- Multi-channel messaging (Telegram, Discord, Slack, WhatsApp, Signal, iMessage, Web)
- Gateway server with WebSocket RPC protocol
- OpenAI-compatible API
- Plugin/extension system

**Kept as fork to:**
- Maintain upstream compatibility
- Receive updates easily
- Avoid modifying original codebase

### primobot-mcp (adapter)

REST API adapter/facade that bridges primobot-core to the Primoia ecosystem.

**Features:**
- Clean REST API with OpenAPI 3.0 specification
- Connects to primobot-core gateway via WebSocket
- MCP (Model Context Protocol) sidecar for AI tool integration
- Swagger UI for interactive API documentation
- Exposes only what Conductor needs

**Why this architecture:**
- Isolates primobot-core complexity
- Provides documented API (OpenAPI)
- Enables MCP tool integration without modifying the fork
- Allows Conductor to send/receive messages through any channel

## Prerequisites

Before starting conductor-chat, ensure the shared infrastructure is running:

```bash
# 1. Start shared infrastructure (from primoia root)
cd infrastructure/primoia-shared-infrastructure
docker-compose up -d

# Verify network exists
docker network ls | grep primoia-infra-net
```

## Quick Start (Host Mode - Recommended)

The chat services run directly on the host for better performance and easier debugging:

```bash
# 1. Start primobot-core (gateway)
cd conductor-chat/primobot-core
pnpm install
pnpm build
pnpm gateway:watch  # or: pnpm moltbot gateway --port 18789

# 2. In another terminal, start primobot-mcp (REST API adapter)
cd conductor-chat/primobot-mcp
cp .env.example .env
pnpm install
pnpm dev

# 3. (Optional) In another terminal, start MCP sidecar
cd shared/primoia-mcp-sidecar
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
TARGET_URL=http://localhost:3100 MCP_PORT=3101 MCP_NAME=primobot-chat python server.py
```

## Quick Start (Docker Mode)

```bash
# 1. Navigate to conductor-chat
cd conductor-community/conductor-chat

# 2. Copy environment file
cp .env.example .env

# 3. Build and start all services
docker-compose build
docker-compose up -d

# 4. Check services are running
docker-compose ps

# 5. Check health
curl http://localhost:3100/health
```

## Ports

| Service | Port | Description |
|---------|------|-------------|
| primobot-core | 18789 | WebSocket Gateway |
| primobot-core | 18790 | Bridge (optional) |
| primobot-mcp | 3100 | REST API |
| MCP Sidecar | 3101 | MCP Protocol |

## Configuration

### Environment Variables

```env
# primobot-core
PRIMOBOT_CORE_PORT=18789

# primobot-mcp
PRIMOBOT_MCP_PORT=3100
PRIMOBOT_CORE_URL=http://localhost:18789
GATEWAY_TOKEN=your-token-here     # Optional
GATEWAY_PASSWORD=your-password    # Optional

# MCP Sidecar
MCP_SIDECAR_PORT=3101
ENABLE_IAM=false                  # Enable IAM authentication
MCP_REGISTRY_ENABLED=false        # Enable MCP registry

# General
NODE_ENV=production
LOG_LEVEL=info
```

### First-time Setup

For primobot-core channel configuration (Telegram, Discord, etc.), you need to run the onboarding wizard:

```bash
# If using Docker
docker exec -it primobot-core sh
moltbot onboard

# If running on host
cd primobot-core
pnpm moltbot onboard
```

Or configure channels via the gateway API.

## Integration with Conductor

### Sending Messages

```bash
# Via primobot-mcp REST API
curl -X POST http://localhost:3100/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+5511999999999",
    "message": "Hello from Conductor!",
    "channel": "whatsapp"
  }'
```

### Available Channels

```bash
curl http://localhost:3100/channels
```

### MCP Tools

The MCP sidecar at port 3101 exposes tools that can be used by AI agents:

| Tool | Description |
|------|-------------|
| `send` | Send message to any channel |
| `poll` | Send a poll |
| `channels_status` | List available channels |
| `chat_send` | Send message via WebChat |
| `chat_history` | Get chat history |
| `sessions_list` | List all sessions |
| `agents_list` | List available agents |
| `models_list` | List available models |
| `health` | Check system health |
| `gateway_status` | Get full gateway status |

## API Documentation

- **Swagger UI**: http://localhost:3100/docs
- **OpenAPI Spec**: http://localhost:3100/openapi.json

## Development

### Running from Source

```bash
# primobot-core
cd primobot-core
pnpm install
pnpm build
pnpm gateway:watch

# primobot-mcp (in another terminal)
cd primobot-mcp
pnpm install
pnpm dev
```

### Testing

```bash
# Health check
curl http://localhost:3100/health

# OpenAPI spec
curl http://localhost:3100/openapi.json

# Swagger UI
open http://localhost:3100/docs

# Gateway status
curl http://localhost:3100/gateway/status
```

## Flow

```
Conductor → primobot-mcp (REST) → primobot-core (WebSocket) → Channel
                ↑                                                 ↓
            OpenAPI                                       User receives message
                ↓
          MCP Sidecar
                ↓
          AI Agent Tools (Claude, etc.)
```

## Troubleshooting

### Gateway not connected

If `/health` shows `status: degraded`, check:
1. primobot-core is running on port 18789
2. `PRIMOBOT_CORE_URL` is correct in .env
3. No firewall blocking the connection

### MCP sidecar not finding tools

1. Ensure REST API is running and healthy
2. Check `TARGET_URL` points to REST API (http://localhost:3100)
3. Verify OpenAPI spec is accessible: `curl http://localhost:3100/openapi.json`

## License

Proprietary - Primoia
