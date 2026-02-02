# Arquitetura de Sugestão de Agentes

Este documento descreve a arquitetura unificada para sugestão semântica de agentes no Conductor, incluindo como manter os índices sincronizados.

## Visão Geral

O sistema de sugestão de agentes usa busca semântica para recomendar o melhor agente baseado na mensagem do usuário. A arquitetura utiliza dois backends de busca com fallback automático:

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUXO DE SUGESTÃO                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  conductor-web                                                  │
│       │                                                         │
│       ▼  POST /api/agents/suggest                               │
│  conductor-gateway (BFF)                                        │
│       │                                                         │
│       ├──► (1) Primário: Knowledge Hub API                      │
│       │         POST /api/v1/suggest-agent                      │
│       │         OpenAI embeddings (1536 dims)                   │
│       │         Collection: ecosystem_docs                      │
│       │                                                         │
│       └──► (2) Fallback: Qdrant Local                           │
│                 sentence-transformers (384 dims)                │
│                 Collection: conductor_agents_capabilities       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Componentes

### 1. Knowledge Hub API (Primário)

- **URL**: `http://primoia-shared-knowledge-hub-api:8000`
- **Endpoint**: `POST /api/v1/suggest-agent`
- **Embedding**: OpenAI `text-embedding-3-small` (1536 dimensões)
- **Collection**: `ecosystem_docs` (filtrado por `source_project=conductor-agents`)
- **Vantagens**: Embeddings de alta qualidade, suporte multilíngue robusto

### 2. Qdrant Local no Gateway (Fallback)

- **Serviço**: `qdrant_service` dentro do conductor-gateway
- **Embedding**: `paraphrase-multilingual-MiniLM-L12-v2` (384 dimensões)
- **Collection**: `conductor_agents_capabilities`
- **Quando usado**: Se Knowledge Hub estiver indisponível ou retornar erro

## Índices e Sincronização

### Dois Índices Separados

| Índice | Gerenciado por | Collection | Dimensões |
|--------|----------------|------------|-----------|
| **Primário** | Knowledge Hub API | `ecosystem_docs` | 1536 (OpenAI) |
| **Fallback** | Conductor Gateway | `conductor_agents_capabilities` | 384 (sentence-transformers) |

### Por que dois índices?

1. **Resiliência**: Se Knowledge Hub falhar, o sistema continua funcionando
2. **Sem dependência de API key**: Gateway não precisa de `OPENAI_API_KEY`
3. **Transição gradual**: Permite migrar sem quebrar o sistema existente

---

## Como Reindexar Agentes

### Cenário 1: Reindexar Todos os Agentes

#### No Knowledge Hub (Primário)

```bash
# Via script Python
cd /mnt/ramdisk/primoia-main/primoia/infrastructure/primoia-knowledge-hub
python scripts/index_agents.py
```

Ou via API diretamente:

```bash
# Para cada agente, indexar sua persona
curl -X POST http://localhost:12075/api/v1/index \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/agents/MeuAgente_Agent/persona.md",
    "content": "# Persona do Agente\n\nConteúdo completo...",
    "context": "ecosystem",
    "source_project": "conductor-agents"
  }'
```

#### No Gateway Local (Fallback)

```bash
# Via endpoint do gateway
curl -X POST http://localhost:14199/api/agents/index
```

Este endpoint lê todos os agentes do MongoDB e indexa no Qdrant local.

### Cenário 2: Indexar um Novo Agente

Quando um novo agente é criado, ele precisa ser indexado em **ambos** os lugares:

#### Passo 1: Indexar no Knowledge Hub

```bash
# Obter persona do agente via MCP
AGENT_ID="NovoAgente_Agent"

# Obter info e persona
INFO=$(curl -s -X POST http://localhost:13199/tools/get_agent_info_agents__agent_id__info_get \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\": \"$AGENT_ID\"}")

PERSONA=$(curl -s -X POST http://localhost:13199/tools/get_agent_persona_agents__agent_id__persona_get \
  -H "Content-Type: application/json" \
  -d "{\"agent_id\": \"$AGENT_ID\"}")

# Extrair conteúdo
PERSONA_CONTENT=$(echo "$PERSONA" | jq -r '.persona_content')
NAME=$(echo "$INFO" | jq -r '.definition.name')
DESCRIPTION=$(echo "$INFO" | jq -r '.definition.description')
EMOJI=$(echo "$INFO" | jq -r '.definition.emoji // "🤖"')

# Criar markdown
MARKDOWN="# $EMOJI $NAME

**Agent ID**: \`$AGENT_ID\`

## Descrição
$DESCRIPTION

## Persona

$PERSONA_CONTENT"

# Indexar no Knowledge Hub
curl -X POST http://localhost:12075/api/v1/index \
  -H "Content-Type: application/json" \
  -d "$(jq -n \
    --arg fp "/agents/$AGENT_ID/persona.md" \
    --arg content "$MARKDOWN" \
    '{file_path: $fp, content: $content, context: "ecosystem", source_project: "conductor-agents"}')"
```

#### Passo 2: Indexar no Gateway Local

```bash
# Reindexar todos (inclui o novo agente)
curl -X POST http://localhost:14199/api/agents/index
```

Ou, se preferir indexar apenas o novo:

```bash
# O gateway não tem endpoint para indexar um único agente
# A solução é chamar o endpoint de reindexação completa
curl -X POST http://localhost:14199/api/agents/index
```

### Cenário 3: Atualizar Persona de Agente Existente

Quando a persona de um agente é atualizada:

```bash
AGENT_ID="AgenteExistente_Agent"

# 1. Deletar do Knowledge Hub (opcional, o index faz upsert)
curl -X DELETE "http://localhost:12075/api/v1/documents//agents/$AGENT_ID/persona.md"

# 2. Reindexar no Knowledge Hub (mesmos passos do Cenário 2, Passo 1)

# 3. Reindexar no Gateway
curl -X POST http://localhost:14199/api/agents/index
```

### Cenário 4: Deletar um Agente

```bash
AGENT_ID="AgenteRemovido_Agent"

# 1. Deletar do Knowledge Hub
curl -X DELETE "http://localhost:12075/api/v1/documents//agents/$AGENT_ID/persona.md"

# 2. Reindexar Gateway (atualiza removendo o agente deletado)
curl -X POST http://localhost:14199/api/agents/index
```

---

## Script de Sincronização Automática

Para manter ambos os índices sincronizados, use este script:

```python
#!/usr/bin/env python3
"""
sync_agent_indexes.py - Sincroniza índices de agentes entre Knowledge Hub e Gateway
"""

import requests
import sys

CONDUCTOR_MCP = "http://localhost:13199"
KNOWLEDGE_HUB = "http://localhost:12075"
GATEWAY = "http://localhost:14199"

def get_agent_persona(agent_id: str) -> dict:
    """Obtém persona do agente via MCP."""
    info = requests.post(
        f"{CONDUCTOR_MCP}/tools/get_agent_info_agents__agent_id__info_get",
        json={"agent_id": agent_id},
        timeout=30
    ).json()

    persona = requests.post(
        f"{CONDUCTOR_MCP}/tools/get_agent_persona_agents__agent_id__persona_get",
        json={"agent_id": agent_id},
        timeout=30
    ).json()

    return {
        "info": info,
        "persona": persona
    }


def index_in_knowledge_hub(agent_id: str, info: dict, persona: dict) -> bool:
    """Indexa agente no Knowledge Hub."""
    definition = info.get("definition", {})
    name = definition.get("name", agent_id)
    emoji = definition.get("emoji", "🤖")
    description = definition.get("description", "")
    persona_content = persona.get("persona_content", "")

    if not persona_content:
        print(f"  ⚠️  {agent_id}: sem persona")
        return False

    markdown = f"""# {emoji} {name}

**Agent ID**: `{agent_id}`

## Descrição
{description}

## Persona

{persona_content}
"""

    response = requests.post(
        f"{KNOWLEDGE_HUB}/api/v1/index",
        json={
            "file_path": f"/agents/{agent_id}/persona.md",
            "content": markdown,
            "context": "ecosystem",
            "source_project": "conductor-agents"
        },
        timeout=60
    )

    return response.status_code == 200


def index_in_gateway() -> bool:
    """Reindexar todos os agentes no Gateway."""
    response = requests.post(f"{GATEWAY}/api/agents/index", timeout=120)
    return response.status_code == 200


def sync_single_agent(agent_id: str):
    """Sincroniza um único agente em ambos os índices."""
    print(f"🔄 Sincronizando {agent_id}...")

    # Obter dados
    data = get_agent_persona(agent_id)

    # Indexar no Knowledge Hub
    if index_in_knowledge_hub(agent_id, data["info"], data["persona"]):
        print(f"  ✅ Knowledge Hub")
    else:
        print(f"  ❌ Knowledge Hub")

    # Reindexar Gateway
    if index_in_gateway():
        print(f"  ✅ Gateway")
    else:
        print(f"  ❌ Gateway")


def sync_all_agents():
    """Sincroniza todos os agentes."""
    # Listar agentes via MCP
    response = requests.post(
        f"{CONDUCTOR_MCP}/tools/list_agents_conductor_agents_get",
        json={},
        timeout=30
    )

    # Parse stdout para extrair agent_ids
    import re
    stdout = response.json().get("stdout", "")
    pattern = r'\d+\.\s+(\w+_Agent)'
    agents = re.findall(pattern, stdout)

    print(f"📋 Encontrados {len(agents)} agentes")

    # Indexar cada um no Knowledge Hub
    for i, agent_id in enumerate(agents, 1):
        print(f"[{i:02d}/{len(agents)}] {agent_id}...")
        try:
            data = get_agent_persona(agent_id)
            if index_in_knowledge_hub(agent_id, data["info"], data["persona"]):
                print(f"  ✅ Knowledge Hub")
            else:
                print(f"  ⏭️  Pulado")
        except Exception as e:
            print(f"  ❌ Erro: {e}")

    # Reindexar Gateway uma vez
    print("\n🔄 Reindexando Gateway...")
    if index_in_gateway():
        print("✅ Gateway sincronizado")
    else:
        print("❌ Erro no Gateway")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Sincronizar agente específico
        sync_single_agent(sys.argv[1])
    else:
        # Sincronizar todos
        sync_all_agents()
```

### Uso do Script

```bash
# Sincronizar todos os agentes
python sync_agent_indexes.py

# Sincronizar um agente específico
python sync_agent_indexes.py NovoAgente_Agent
```

---

## Automação via Webhook (Futuro)

Para automatizar a sincronização quando agentes são criados/atualizados:

### Opção 1: Webhook no conductor-api

Modificar o endpoint de criação de agentes para notificar o Knowledge Hub:

```python
# Em conductor-api, após criar/atualizar agente:
async def notify_knowledge_hub(agent_id: str):
    async with httpx.AsyncClient() as client:
        # Notificar para reindexar
        await client.post(
            "http://primoia-shared-knowledge-hub-api:8000/api/v1/reindex-agent",
            json={"agent_id": agent_id}
        )
```

### Opção 2: Cron Job

Executar sincronização periódica:

```bash
# Crontab - a cada hora
0 * * * * python /path/to/sync_agent_indexes.py >> /var/log/agent-sync.log 2>&1
```

### Opção 3: MongoDB Change Streams

Monitorar alterações na collection `agents` e sincronizar automaticamente.

---

## Endpoints de Referência

### Knowledge Hub API

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/suggest-agent` | POST | Sugerir agente baseado na mensagem |
| `/api/v1/sync-agents` | POST | **Sincronizar agentes com detecção inteligente de mudanças** |
| `/api/v1/index` | POST | Indexar documento markdown |
| `/api/v1/documents/{path}` | DELETE | Remover documento do índice |
| `/api/v1/stats` | GET | Estatísticas das collections |

### Endpoint de Sincronização Inteligente

O endpoint `POST /api/v1/sync-agents` usa hash para detectar mudanças:

```bash
# Sincronizar apenas agentes alterados (economiza tokens)
curl -X POST http://localhost:12075/api/v1/sync-agents \
  -H "Content-Type: application/json" \
  -d '{
    "conductor_mcp_url": "http://community-conductor-api-mcp:9000"
  }'

# Forçar re-indexação de todos (ignora hash)
curl -X POST http://localhost:12075/api/v1/sync-agents \
  -H "Content-Type: application/json" \
  -d '{
    "conductor_mcp_url": "http://community-conductor-api-mcp:9000",
    "force": true
  }'
```

**Resposta:**
```json
{
  "status": "completed",
  "total_agents": 57,
  "indexed": 2,        // Apenas 2 tinham mudanças
  "skipped": 55,       // 55 estavam iguais
  "errors": 0,
  "tokens_saved": 82500,  // ~1500 tokens/agente * 55 skipped
  "duration_ms": 5234
}
```

**Como funciona:**
1. Obtém lista de agentes do Conductor MCP
2. Para cada agente, calcula hash SHA256 do conteúdo (nome + descrição + tags + persona)
3. Compara com hash armazenado no Qdrant
4. Se hash igual → SKIP (0 tokens gastos)
5. Se hash diferente → RE-INDEX (usa tokens da OpenAI)

### Conductor Gateway

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/agents/suggest` | POST | Sugerir agente (usa Knowledge Hub + fallback) |
| `/api/agents/index` | POST | Reindexar todos os agentes no Qdrant local |
| `/api/agents/index/status` | GET | Status do índice local |

### Conductor MCP

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/tools/list_agents_conductor_agents_get` | POST | Listar todos os agentes |
| `/tools/get_agent_info_agents__agent_id__info_get` | POST | Info de um agente |
| `/tools/get_agent_persona_agents__agent_id__persona_get` | POST | Persona de um agente |

### Knowledge Hub MCP (porta 13075)

| Tool | Descrição |
|------|-----------|
| `index_markdown` | Indexar markdown com conteúdo |
| `index_file` | Indexar arquivo do disco |
| `search` | Busca semântica |
| `suggest_agent` | Sugerir agente para mensagem |
| `sync_agents` | **Sincronizar agentes com detecção de mudanças** |
| `scan_directory` | Escanear diretório |
| `delete_document` | Remover documento |
| `list_documents` | Listar documentos |
| `get_stats` | Estatísticas |

Exemplo de uso do `suggest_agent` via MCP:

```bash
curl -X POST http://localhost:13075/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "suggest_agent",
    "arguments": {
      "message": "preciso criar uma API REST",
      "current_agent_id": "Counselor_Agent"
    }
  }'
```

---

## Variáveis de Ambiente

### Gateway

```env
# URL do Knowledge Hub (primário para sugestões)
KNOWLEDGE_HUB_URL=http://primoia-shared-knowledge-hub-api:8000

# Timeout para chamadas ao Knowledge Hub (segundos)
KNOWLEDGE_HUB_TIMEOUT=10.0

# Qdrant para fallback local
QDRANT_HOST=primoia-shared-qdrant
QDRANT_PORT=6333
```

### Knowledge Hub

```env
# Qdrant
QDRANT_URL=http://primoia-shared-qdrant:6333

# OpenAI
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
```

---

## Configuração de Rate Limit

O Conductor MCP usa rate limiting para proteger a API. Por padrão:
- **Limite**: 100 requisições por minuto
- **Janela**: 60 segundos

### Requisitos para Sync-Agents

A sincronização de 57 agentes requer aproximadamente:
- 1 requisição para listar agentes
- 2 requisições por agente (info + persona)
- **Total**: ~115 requisições

Por isso, o `docker-compose.centralized.yml` configura um limite maior:

```yaml
community-conductor-api-mcp:
  environment:
    - RATE_LIMIT_MAX_REQUESTS=300
    - RATE_LIMIT_WINDOW=60
```

### Variáveis de Ambiente do MCP

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `RATE_LIMIT_ENABLED` | `true` | Habilitar rate limiting |
| `RATE_LIMIT_WINDOW` | `60` | Janela em segundos |
| `RATE_LIMIT_MAX_REQUESTS` | `100` | Requisições por janela |

Para desabilitar rate limiting (apenas em desenvolvimento):

```yaml
- RATE_LIMIT_ENABLED=false
```

---

## Troubleshooting

### Sugestões retornando "fallback"

1. Verificar se Knowledge Hub está rodando:
   ```bash
   curl http://localhost:12075/health
   ```

2. Verificar se agentes estão indexados:
   ```bash
   curl http://localhost:12075/api/v1/stats
   # ecosystem_docs deve ter vectors_count > 0
   ```

3. Verificar logs do Gateway:
   ```bash
   docker logs community-conductor-bff --tail 50 | grep SUGGEST
   ```

### Agente não aparece nas sugestões

1. Verificar se está indexado no Knowledge Hub:
   ```bash
   curl "http://localhost:12075/api/v1/documents?source_project=conductor-agents" | jq '.documents[].file_path'
   ```

2. Reindexar o agente:
   ```bash
   python sync_agent_indexes.py MeuAgente_Agent
   ```

### Scores muito baixos

- OpenAI embeddings retornam scores entre 0-1
- Scores < 0.30 são considerados baixa confiança
- Se todos os scores estão baixos, a persona do agente pode não ter keywords relevantes

### Rate Limit Error (429) no Sync-Agents

Se o endpoint `sync-agents` retornar erros 429:

1. Verificar configuração do MCP:
   ```bash
   docker exec community-conductor-api-mcp env | grep RATE_LIMIT
   ```

2. Aumentar limite se necessário no `docker-compose.centralized.yml`:
   ```yaml
   - RATE_LIMIT_MAX_REQUESTS=500
   ```

3. Reiniciar o container:
   ```bash
   docker-compose -f docker-compose.centralized.yml restart community-conductor-api-mcp
   ```

---

## Histórico de Alterações

| Data | Alteração |
|------|-----------|
| 2026-01-25 | Criação da arquitetura unificada |
| 2026-01-25 | Adicionado endpoint suggest-agent no Knowledge Hub |
| 2026-01-25 | Gateway modificado para usar Knowledge Hub com fallback |
| 2026-01-25 | Adicionado endpoint sync-agents com detecção de hash |
| 2026-01-25 | Configurado rate limit do MCP para 300 req/min |
| 2026-01-25 | Validado: 57 agentes, skip funcional, ~85k tokens economizados por sync |
