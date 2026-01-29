# Conductor Chat

Chat and messaging integration layer for Conductor Community. Provides multi-platform messaging capabilities through primobot-core with a clean REST API adapter.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        conductor-chat                           │
│                                                                 │
│  ┌────────────────────┐       ┌───────────────────────────────┐│
│  │   primobot-core    │       │        primobot-mcp           ││
│  │      (fork)        │       │                               ││
│  │                    │       │  ┌─────────────────────────┐  ││
│  │  ┌──────────────┐  │       │  │   REST API + OpenAPI    │  ││
│  │  │   Gateway    │◄─┼───────┼──│   /chat/send            │  ││
│  │  │  port 18789  │  │       │  │   /chat/channels        │  ││
│  │  └──────────────┘  │       │  │   /openapi.json         │  ││
│  │                    │       │  └─────────────────────────┘  ││
│  │  ┌──────────────┐  │       │             │                 ││
│  │  │   Channels   │  │       │             ▼                 ││
│  │  │  - Telegram  │  │       │  ┌─────────────────────────┐  ││
│  │  │  - Discord   │  │       │  │     MCP Sidecar         │  ││
│  │  │  - Slack     │  │       │  │   (reads OpenAPI)       │  ││
│  │  │  - WhatsApp  │  │       │  │     port 3101           │  ││
│  │  │  - Signal    │  │       │  └─────────────────────────┘  ││
│  │  │  - Web       │  │       │                               ││
│  │  └──────────────┘  │       │         port 3100             ││
│  └────────────────────┘       └───────────────────────────────┘│
│                                                                 │
│  docker-compose.yml (orchestrates both services)               │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### primobot-core (fork)

Fork of [moltbot](https://github.com/moltbot/moltbot) - a multi-platform personal AI assistant.

**Features:**
- Multi-channel messaging (Telegram, Discord, Slack, WhatsApp, Signal, iMessage, Web)
- Gateway server with WebSocket/HTTP
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
- Connects to primobot-core gateway
- MCP (Model Context Protocol) sidecar for AI tool integration
- Exposes only what Conductor needs

**Why this architecture:**
- Isolates primobot-core complexity
- Provides documented API (OpenAPI)
- Enables MCP tool integration without modifying the fork
- Allows Conductor to send/receive messages through any channel

## Quick Start

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check health
curl http://localhost:3100/health
```

## Configuration

### Environment Variables

```env
# primobot-core
PRIMOBOT_CORE_PORT=18789

# primobot-mcp
PRIMOBOT_MCP_PORT=3100
MCP_SIDECAR_PORT=3101

# General
NODE_ENV=production
LOG_LEVEL=info
```

### First-time Setup

For primobot-core channel configuration (Telegram, Discord, etc.), you need to run the onboarding wizard:

```bash
# Enter the container
docker exec -it primobot-core sh

# Run onboarding
moltbot onboard
```

Or configure channels via the gateway API.

## Ports

| Service | Port | Description |
|---------|------|-------------|
| primobot-core | 18789 | Main gateway |
| primobot-mcp | 3100 | REST API |
| primobot-mcp | 3101 | MCP Sidecar |

## Integration with Conductor

### Sending Messages

```bash
# Via primobot-mcp REST API
curl -X POST http://localhost:3100/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from Conductor!", "channel": "telegram"}'
```

### Available Channels

```bash
curl http://localhost:3100/chat/channels
```

### MCP Tools

The MCP sidecar at port 3101 exposes tools that can be used by AI agents:
- `send_message` - Send message to any channel
- `list_channels` - List available channels
- `get_channel_status` - Check channel connection status

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
```

## Flow

```
Conductor → primobot-mcp → primobot-core → Channel (Telegram/Discord/etc)
                ↑                              ↓
            OpenAPI                        User receives message
                ↓
          MCP Sidecar
                ↓
          AI Agent Tools
```

## License

Proprietary - Primoia
