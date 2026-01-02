# Plano de Implementação: MCP On-Demand

> **Data:** 2026-01-02
> **Status:** Planejado
> **Prioridade:** Alta

---

## 1. Problema

O Primoia opera com aproximadamente 80 serviços, onde cada serviço é um par indissociável:
- **MCP sidecar**: expõe ferramentas para a IA via protocolo MCP (Model Context Protocol)
- **API backend**: executa a lógica de negócio

Cada par está definido em seu próprio `docker-compose.centralized.yml`.

### Situação Atual

- Manter 80 pares de containers (160 containers) rodando simultaneamente consome recursos desnecessariamente
- Muitos agentes são usados esporadicamente ou estão em fase de testes
- O sistema atual (`/api/system/mcp/sidecars`) só mostra MCPs que já estão rodando
- Não há mecanismo para iniciar MCPs sob demanda quando um agente precisa deles
- Não há mecanismo para desligar MCPs após período de inatividade

### Impacto

- Desperdício de memória e CPU
- Necessidade de gerenciamento manual de containers
- Agentes não podem usar MCPs que não estão previamente iniciados

---

## 2. Discussão e Decisões de Arquitetura

### 2.1 Onde Colocar a Lógica de Orquestração?

**Opção descartada: Gateway (conductor-gateway)**
- Roda em container Docker
- Não tem acesso fácil ao Docker socket do host
- Inviabiliza execução de `docker-compose up/down`

**Opção escolhida: Watcher (claude-mongo-watcher.py)**
- Roda diretamente na máquina host
- Já tem acesso nativo ao Docker
- Já é o ponto de execução de todas as tasks (manuais e conselheiros)
- Já acessa MongoDB diretamente
- Fluxo linear: verificar → subir → executar → atualizar

### 2.2 Estratégia de Startup

**Decisão:** Health check primeiro, docker-compose up apenas se necessário.

```
1. Verificar se MCP está healthy (GET /health ou docker ps)
2. Se healthy → não faz nada (evita docker-compose up desnecessário)
3. Se stopped → docker-compose -f {path} up -d
4. Aguardar health check passar (retry com timeout)
5. Atualizar registro no MongoDB
```

**Justificativa:** Não queremos rodar `docker-compose up` em containers que já estão rodando, pois isso pode causar rebuild desnecessário ou atualização de imagem fora de hora.

### 2.3 Estratégia de Shutdown

**Decisão:** Conselheiro Zelador com ciclo periódico.

- Um agente promovido a Conselheiro roda a cada hora (configurável)
- Consulta `mcp_registry` por MCPs com `shutdown_after < now` e `status = healthy`
- Executa `docker-compose down` para cada um
- Atualiza status para `stopped`

**Justificativa:**
- Não é crítico se demorar alguns minutos a mais
- Conselheiro pode evoluir para decisões mais inteligentes
- Mantém a filosofia "IA First" do projeto

### 2.4 Unidade Atômica

**Decisão:** docker-compose como unidade de deploy.

Cada serviço tem seu `docker-compose.centralized.yml` que sobe o par MCP + API juntos. Não gerenciamos containers individuais.

```
services/
├── crm/
│   └── docker-compose.centralized.yml  # sobe crm-mcp-sidecar + crm-api
├── erp/
│   └── docker-compose.centralized.yml  # sobe erp-mcp-sidecar + erp-api
└── billing/
    └── docker-compose.centralized.yml  # sobe billing-mcp-sidecar + billing-api
```

---

## 3. Descoberta Automática de MCPs (Desativar/Modificar)

### 3.1 Situação Atual

O sistema possui descoberta automática de MCPs implementada em:

- **conductor**: `src/infrastructure/discovery_service.py`
- **conductor**: `src/api/routes/system.py` → endpoint `/api/system/mcp/sidecars`

Essa descoberta funciona via scan de containers Docker rodando, identificando MCPs pela porta ou nome.

### 3.2 Conflito com On-Demand

A descoberta automática **conflita** com a abordagem on-demand porque:

| Descoberta Automática | On-Demand |
|----------------------|-----------|
| Só vê MCPs rodando | Precisa ver MCPs parados também |
| Atualiza status baseado em containers ativos | Status controlado pelo Watcher |
| Pode sobrescrever `status: stopped` | Watcher gerencia transições de status |

### 3.3 Ações Necessárias

**Opção A: Desativar descoberta automática**

1. Remover ou comentar a lógica de scan em `discovery_service.py`
2. Endpoint `/api/system/mcp/sidecars` passa a ler do `mcp_registry` em vez de scanear

**Opção B: Modificar descoberta para coexistir**

1. Descoberta automática apenas **atualiza** MCPs existentes no registry
2. Não cria novos MCPs automaticamente
3. Não sobrescreve campos de on-demand (`status`, `shutdown_after`)

**Recomendação:** Opção A (desativar) é mais simples e evita conflitos.

### 3.4 Arquivos Afetados

| Arquivo | Ação |
|---------|------|
| `conductor/src/infrastructure/discovery_service.py` | Remover `scan_network()` ou similar |
| `conductor/src/api/routes/system.py` | Endpoint `/mcp/sidecars` lê do registry |
| `conductor-web/src/app/services/agent.service.ts` | Já planejado: mudar para `/mcp/list` do Gateway |

### 3.5 Migração

```python
# Antes (discovery_service.py)
def get_available_sidecars():
    # Scan Docker network
    containers = docker.containers.list()
    return [c for c in containers if "mcp" in c.name]

# Depois
def get_available_sidecars():
    # Ler do mcp_registry
    return list(db.mcp_registry.find({}))
```

---

## 4. Solução Técnica

### 4.1 Alterações no Modelo mcp_registry

**Arquivo:** `conductor-gateway/src/models/mcp_registry.py`

Adicionar novos status:

```python
class MCPStatus(str, Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STOPPED = "stopped"       # NOVO: Container parado
    STARTING = "starting"     # NOVO: Container subindo
```

Adicionar novos campos ao `MCPRegistryEntry`:

```python
class MCPRegistryEntry(BaseModel):
    # ... campos existentes ...
    # url: str  ← já existe (URL interna Docker, ex: "http://crm-mcp-sidecar:9201/sse")

    # NOVOS CAMPOS PARA ON-DEMAND:
    host_url: Optional[str] = Field(
        None,
        description="URL acessível do host para Watcher (ex: http://localhost:13145/sse)"
    )
    docker_compose_path: Optional[str] = Field(
        None,
        description="Caminho absoluto para docker-compose.centralized.yml"
    )
    shutdown_after: Optional[datetime] = Field(
        None,
        description="Timestamp após o qual o MCP pode ser desligado"
    )
    last_used: Optional[datetime] = Field(
        None,
        description="Último uso do MCP por um agente"
    )
    auto_shutdown_minutes: int = Field(
        30,
        description="Minutos de inatividade antes de permitir shutdown"
    )
```

**Nota sobre URLs:**
```
┌─────────────────────────────────────────────────────────────────┐
│  url (existente)                                                 │
│  - Usado pelo Gateway (dentro da rede Docker)                   │
│  - Ex: "http://crm-mcp-sidecar:9201/sse"                        │
├─────────────────────────────────────────────────────────────────┤
│  host_url (novo)                                                 │
│  - Usado pelo Watcher (roda no host)                            │
│  - Ex: "http://localhost:13145/sse"                             │
│  - Derivado do port mapping do docker-compose                    │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Nova Classe MCPContainerService no Watcher

**Arquivo:** `conductor/poc/container_to_host/mcp_container_service.py` (NOVO)

```python
import os
import subprocess
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from pymongo.database import Database
import requests

logger = logging.getLogger(__name__)

class MCPContainerService:
    """
    Serviço para gerenciar ciclo de vida de containers MCP.
    Roda no host, tem acesso direto ao Docker.
    """

    def __init__(self, db: Database, default_shutdown_minutes: int = 30):
        self.db = db
        self.mcp_registry = db["mcp_registry"]
        self.default_shutdown_minutes = default_shutdown_minutes

    def ensure_running(self, mcp_name: str, timeout: int = 60) -> bool:
        """
        Garante que um MCP está rodando.

        1. Busca MCP no registry
        2. Verifica health
        3. Se não healthy, executa docker-compose up
        4. Aguarda health check
        5. Atualiza timestamps

        Args:
            mcp_name: Nome do MCP (ex: "crm", "prospector")
            timeout: Timeout em segundos para aguardar startup

        Returns:
            bool: True se MCP está rodando, False se falhou
        """
        pass  # Implementar

    def health_check(self, mcp_name: str) -> bool:
        """
        Verifica se MCP está respondendo via host_url.

        Usa host_url do registry (ex: http://localhost:13145/sse)
        e substitui /sse por /health para o check.
        """
        mcp = self.mcp_registry.find_one({"name": mcp_name})
        if not mcp:
            logger.warning(f"MCP '{mcp_name}' não encontrado no registry")
            return False

        # Usar host_url (acessível do host onde Watcher roda)
        host_url = mcp.get("host_url")
        if not host_url:
            logger.warning(f"MCP '{mcp_name}' não tem host_url configurado")
            return False

        # Derivar URL de health do host_url
        health_url = host_url.replace("/sse", "/health")

        try:
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            logger.debug(f"Health check falhou para '{mcp_name}': {e}")
            return False

    def start_container(self, mcp_name: str) -> bool:
        """
        Inicia container via docker-compose up -d.

        Usa docker_compose_path do registry.
        """
        pass  # Implementar

    def stop_container(self, mcp_name: str) -> bool:
        """
        Para container via docker-compose down.
        """
        pass  # Implementar

    def update_timestamps(self, mcp_name: str):
        """
        Atualiza last_used e shutdown_after no registry.
        """
        pass  # Implementar

    def get_mcps_for_agent(self, agent_id: str, instance_id: str = None) -> List[str]:
        """
        Retorna lista de MCPs necessários para um agente/instância.

        Combina:
        - agents.mcp_configs (do template)
        - agent_instances.mcp_configs (extras da instância)
        """
        pass  # Implementar

    def get_expired_mcps(self) -> List[Dict]:
        """
        Retorna MCPs que podem ser desligados (shutdown_after < now).
        """
        pass  # Implementar
```

### 4.3 Integração no Watcher

**Arquivo:** `conductor/poc/container_to_host/claude-mongo-watcher.py`

Modificar o método `process_request`:

```python
def process_request(self, request: Dict) -> bool:
    request_id = request["_id"]
    agent_id = request.get("agent_id", "unknown")
    instance_id = request.get("instance_id")

    # ... código existente de logging ...

    # ═══════════════════════════════════════════════════════════════════
    # NOVO: Garantir MCPs rodando ANTES de executar
    # ═══════════════════════════════════════════════════════════════════
    try:
        mcp_service = MCPContainerService(self.db)
        required_mcps = mcp_service.get_mcps_for_agent(agent_id, instance_id)

        if required_mcps:
            logger.info(f"🔌 MCPs necessários: {required_mcps}")

            for mcp_name in required_mcps:
                if not mcp_service.ensure_running(mcp_name):
                    error_msg = f"Falha ao iniciar MCP '{mcp_name}'"
                    logger.error(f"❌ {error_msg}")
                    self.complete_request(request_id, error_msg, 1, 0.0)
                    return False

            logger.info(f"✅ Todos os MCPs estão rodando")

    except Exception as e:
        logger.error(f"❌ Erro ao verificar MCPs: {e}")
        self.complete_request(request_id, f"Erro ao iniciar MCPs: {e}", 1, 0.0)
        return False
    # ═══════════════════════════════════════════════════════════════════

    # Continua com o fluxo existente...
    if not self.mark_as_processing(request_id):
        # ...
```

### 4.4 Conselheiro Zelador

**Criar novo agente:** `config/agents/ResourceZelador_Agent/`

**definition.yaml:**
```yaml
name: "ResourceZelador_Agent"
version: "1.0.0"
schema_version: "1.0"
description: "Conselheiro responsável por desligar MCPs inativos"
author: "PrimoIA"
emoji: "🧹"
tags: ["system", "resources", "cleanup", "councilor"]
capabilities:
  - "docker_management"
  - "resource_cleanup"
allowed_tools:
  - "Bash"
  - "Read"
mcp_configs: []
```

**persona.md:**
```markdown
# Persona: Resource Zelador

Você é o Zelador de Recursos do sistema Primoia. Sua função é manter o sistema
limpo e eficiente, desligando containers MCP que não estão sendo utilizados.

## Suas Responsabilidades

1. Consultar a coleção `mcp_registry` no MongoDB
2. Identificar MCPs que podem ser desligados:
   - status = "healthy"
   - shutdown_after < horário atual
3. Para cada MCP identificado:
   - Executar: `docker-compose -f {docker_compose_path} down`
   - Atualizar no MongoDB: status = "stopped"
4. Reportar quantos MCPs foram desligados

## Regras

- NUNCA desligue MCPs com status diferente de "healthy"
- NUNCA desligue MCPs cujo shutdown_after ainda não passou
- Se docker-compose down falhar, registre o erro mas continue com os próximos
- Seja eficiente e direto

## Conexão MongoDB

Use a variável de ambiente MONGO_URI para conectar.
Database: conductor_state
Collection: mcp_registry
```

**Instrução para o Conselheiro (campo instructions no councilor):**
```
Consulte a coleção mcp_registry no database conductor_state.
Para cada documento onde status="healthy" e shutdown_after < now():
1. Execute: docker-compose -f {docker_compose_path} down
2. Atualize o documento: status="stopped", last_heartbeat=null
Reporte quantos MCPs foram desligados.
```

**Ciclo:** 1 hora (configurável)

---

## 5. Fluxo Completo

### 4.1 Execução de Agente (Manual ou Conselheiro)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Task inserida no MongoDB (status: pending)                               │
│     - agent_id, instance_id, prompt, cwd, etc.                              │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. Watcher pega task                                                        │
│     - Poll MongoDB por status: pending                                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. MCPContainerService.get_mcps_for_agent(agent_id, instance_id)           │
│     - Consulta agents.mcp_configs                                           │
│     - Consulta agent_instances.mcp_configs                                  │
│     - Retorna: ["crm", "database"]                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. Para cada MCP: ensure_running(mcp_name)                                 │
│     ┌─────────────────────────────────────────────────────────────────────┐ │
│     │ a) health_check() → GET http://localhost:{port}/health              │ │
│     │    - Se healthy → pula para (e)                                     │ │
│     │    - Se não → continua                                              │ │
│     ├─────────────────────────────────────────────────────────────────────┤ │
│     │ b) Busca docker_compose_path no mcp_registry                        │ │
│     ├─────────────────────────────────────────────────────────────────────┤ │
│     │ c) Executa: docker-compose -f {path} up -d                          │ │
│     ├─────────────────────────────────────────────────────────────────────┤ │
│     │ d) Aguarda health_check() passar (retry com timeout)                │ │
│     ├─────────────────────────────────────────────────────────────────────┤ │
│     │ e) Atualiza mcp_registry:                                           │ │
│     │    - status = "healthy"                                             │ │
│     │    - last_used = now()                                              │ │
│     │    - shutdown_after = now() + 30min                                 │ │
│     └─────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. Gera mcp_config.json com URLs dos MCPs ativos                           │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. Executa: claude --mcp-config {path} --print < prompt                    │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  7. Completa task no MongoDB (status: completed/error)                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Cleanup pelo Conselheiro Zelador

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Scheduler dispara execução do ResourceZelador_Agent (a cada 1h)         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. Task inserida no MongoDB (is_councilor_execution: true)                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. Watcher pega e executa (mesmo fluxo, mas sem MCPs próprios)             │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. Claude executa a instrução do Zelador:                                  │
│     - Consulta mcp_registry                                                 │
│     - Identifica MCPs expirados                                             │
│     - Executa docker-compose down para cada                                 │
│     - Atualiza status para "stopped"                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Arquivos a Modificar/Criar

### 7.1 Modificar

| Arquivo | Alteração |
|---------|-----------|
| `conductor-gateway/src/models/mcp_registry.py` | Adicionar campos e status |
| `conductor/poc/container_to_host/claude-mongo-watcher.py` | Integrar MCPContainerService |

### 7.2 Criar

| Arquivo | Descrição |
|---------|-----------|
| `conductor/poc/container_to_host/mcp_container_service.py` | Serviço de gerenciamento de containers |
| `conductor/config/agents/ResourceZelador_Agent/definition.yaml` | Definição do Conselheiro |
| `conductor/config/agents/ResourceZelador_Agent/persona.md` | Persona do Conselheiro |

### 7.3 Popular

A coleção `mcp_registry` precisa ser populada com os MCPs disponíveis, incluindo os novos campos:

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `host_url` | Sim | URL acessível do host (para Watcher fazer health check) |
| `docker_compose_path` | Sim | Caminho absoluto para docker-compose.centralized.yml |
| `auto_shutdown_minutes` | Não | Minutos de inatividade (default: 30) |

**Exemplo de documento completo:**

```json
{
    "name": "crm",
    "type": "external",
    "url": "http://crm-mcp-sidecar:9201/sse",
    "host_url": "http://localhost:13145/sse",
    "docker_compose_path": "/opt/primoia/services/crm/docker-compose.centralized.yml",
    "status": "stopped",
    "auto_shutdown_minutes": 30,
    "metadata": {
        "category": "verticals",
        "description": "CRM Lead Management"
    }
}
```

**Script de migração sugerido:**

```python
# Atualizar MCPs existentes com novos campos
db.mcp_registry.update_many(
    {"host_url": {"$exists": False}},
    {"$set": {
        "host_url": None,  # Preencher manualmente depois
        "docker_compose_path": None,
        "auto_shutdown_minutes": 30,
        "status": "unknown"
    }}
)
```

### 7.4 Tarefa: Levantamento e Cadastro dos MCPs

**Objetivo:** Identificar todos os ~80 pares MCP + API e cadastrá-los no `mcp_registry` com os campos necessários para on-demand.

#### 5.4.1 Descoberta

1. **Localizar docker-compose files:**
```bash
# Buscar todos os docker-compose.centralized.yml
find /opt/primoia -name "docker-compose.centralized.yml" -type f

# Ou buscar por padrão de nome de serviço MCP
find /opt/primoia -name "docker-compose*.yml" -exec grep -l "mcp-sidecar" {} \;
```

2. **Extrair informações de cada compose:**
   - Nome do serviço MCP
   - Porta interna (ex: 9201)
   - Porta mapeada no host (ex: 13145)
   - Nome do serviço API relacionado

#### 5.4.2 Template de Coleta

Para cada MCP encontrado, coletar:

| Campo | Como Obter | Exemplo |
|-------|------------|---------|
| `name` | Nome do serviço sem sufixo | `crm` |
| `url` | `{container_name}:{internal_port}/sse` | `http://crm-mcp-sidecar:9201/sse` |
| `host_url` | `localhost:{host_port}/sse` | `http://localhost:13145/sse` |
| `docker_compose_path` | Caminho absoluto do arquivo | `/opt/primoia/services/crm/docker-compose.centralized.yml` |
| `backend_url` | URL do backend API | `http://crm-api:8001` |
| `category` | Categoria do serviço | `verticals`, `core`, `billing` |

#### 5.4.3 Script de Descoberta Automática

```python
#!/usr/bin/env python3
"""
Script para descobrir MCPs e gerar cadastro para mcp_registry.
"""
import os
import yaml
import json
from pathlib import Path

def discover_mcps(base_path: str) -> list:
    """Descobre MCPs a partir dos docker-compose files."""
    mcps = []

    for compose_file in Path(base_path).rglob("docker-compose.centralized.yml"):
        try:
            with open(compose_file) as f:
                compose = yaml.safe_load(f)

            services = compose.get("services", {})

            for service_name, service_config in services.items():
                # Identificar serviço MCP (contém "mcp" no nome)
                if "mcp" in service_name.lower():
                    ports = service_config.get("ports", [])

                    # Extrair port mapping (ex: "13145:9201")
                    host_port = None
                    internal_port = None
                    for port in ports:
                        if isinstance(port, str) and ":" in port:
                            host_port, internal_port = port.split(":")[:2]
                            break

                    # Extrair nome base (ex: "crm" de "crm-mcp-sidecar")
                    base_name = service_name.replace("-mcp-sidecar", "").replace("-mcp", "")

                    mcp_entry = {
                        "name": base_name,
                        "type": "external",
                        "url": f"http://{service_name}:{internal_port}/sse",
                        "host_url": f"http://localhost:{host_port}/sse" if host_port else None,
                        "docker_compose_path": str(compose_file.absolute()),
                        "status": "unknown",
                        "auto_shutdown_minutes": 30,
                        "metadata": {
                            "category": categorize_service(str(compose_file)),
                            "description": f"MCP for {base_name}"
                        }
                    }
                    mcps.append(mcp_entry)

        except Exception as e:
            print(f"Erro ao processar {compose_file}: {e}")

    return mcps

def categorize_service(path: str) -> str:
    """Categoriza serviço baseado no path."""
    if "verticals" in path:
        return "verticals"
    elif "billing" in path:
        return "billing"
    elif "core" in path:
        return "core"
    return "other"

if __name__ == "__main__":
    import sys
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/opt/primoia"

    mcps = discover_mcps(base_path)

    print(f"Descobertos {len(mcps)} MCPs:\n")
    print(json.dumps(mcps, indent=2))

    # Salvar para arquivo
    with open("discovered_mcps.json", "w") as f:
        json.dump(mcps, f, indent=2)

    print(f"\nSalvo em discovered_mcps.json")
```

#### 5.4.4 Script de Cadastro no MongoDB

```python
#!/usr/bin/env python3
"""
Cadastra MCPs descobertos no mcp_registry.
"""
import json
from pymongo import MongoClient
from datetime import datetime, timezone

def register_mcps(json_file: str, mongo_uri: str = "mongodb://localhost:27017"):
    client = MongoClient(mongo_uri)
    db = client["conductor_state"]
    registry = db["mcp_registry"]

    with open(json_file) as f:
        mcps = json.load(f)

    registered = 0
    updated = 0

    for mcp in mcps:
        # Verificar se já existe
        existing = registry.find_one({"name": mcp["name"]})

        if existing:
            # Atualizar campos de on-demand
            registry.update_one(
                {"name": mcp["name"]},
                {"$set": {
                    "host_url": mcp["host_url"],
                    "docker_compose_path": mcp["docker_compose_path"],
                    "auto_shutdown_minutes": mcp["auto_shutdown_minutes"],
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            updated += 1
            print(f"✏️  Atualizado: {mcp['name']}")
        else:
            # Inserir novo
            mcp["registered_at"] = datetime.now(timezone.utc)
            registry.insert_one(mcp)
            registered += 1
            print(f"✅ Registrado: {mcp['name']}")

    print(f"\nResumo: {registered} novos, {updated} atualizados")

if __name__ == "__main__":
    import sys
    json_file = sys.argv[1] if len(sys.argv) > 1 else "discovered_mcps.json"
    register_mcps(json_file)
```

#### 5.4.5 Validação Manual

Após descoberta automática, validar manualmente:

- [ ] Verificar se todos os MCPs foram encontrados
- [ ] Conferir port mappings (host_url correto?)
- [ ] Conferir paths dos docker-compose
- [ ] Testar health check em alguns MCPs
- [ ] Categorizar serviços corretamente

#### 5.4.6 Resultado Esperado

Ao final desta tarefa, a coleção `mcp_registry` deve ter ~80 documentos com:

```javascript
db.mcp_registry.countDocuments({
    "host_url": { "$ne": null },
    "docker_compose_path": { "$ne": null }
})
// Esperado: ~80
```

---

## 7. Testes

### 7.1 Teste Manual

1. Parar todos os MCPs: `docker-compose down` em cada serviço
2. Executar um agente que precisa de MCP específico
3. Verificar que o MCP foi iniciado automaticamente
4. Aguardar 30+ minutos sem usar o agente
5. Executar o Conselheiro Zelador manualmente
6. Verificar que o MCP foi desligado

### 7.2 Verificações

- [ ] MCPs sobem corretamente via docker-compose
- [ ] Health check funciona
- [ ] Timestamps são atualizados no registry
- [ ] Conselheiro Zelador desliga MCPs expirados
- [ ] Execução de agente sem MCPs funciona normalmente
- [ ] Erro é tratado se docker-compose falhar

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Docker-compose demora para subir | Média | Alto | Timeout configurável, retry logic |
| Health check falha intermitentemente | Baixa | Médio | Retry com backoff exponencial |
| Conselheiro desliga MCP em uso | Baixa | Alto | Atualizar shutdown_after a cada uso |
| docker-compose path incorreto | Média | Alto | Validação no registro, logs claros |

---

## 9. Cronograma Sugerido

### Pré-requisitos

0. **Fase 0:** Desativar descoberta automática de MCPs
   - Modificar `discovery_service.py` para ler do `mcp_registry`
   - Atualizar endpoint `/api/system/mcp/sidecars`
   - **Importante:** Fazer ANTES de implementar on-demand para evitar conflitos

### Backend (conductor + conductor-gateway)

1. **Fase 1:** Adicionar campos ao modelo pydantic (`mcp_registry.py`)
   - `host_url`, `docker_compose_path`, `shutdown_after`, `last_used`, `auto_shutdown_minutes`
   - Novos status: `stopped`, `starting`

2. **Fase 2:** Levantamento e cadastro dos ~80 MCPs
   - Executar script de descoberta (`discover_mcps.py`)
   - Validar e corrigir dados manualmente
   - Cadastrar no `mcp_registry` via script

3. **Fase 3:** Implementar MCPContainerService no Watcher

4. **Fase 4:** Integrar MCPContainerService no `process_request`

5. **Fase 5:** Testar com 2-3 MCPs (fluxo completo up/down)

6. **Fase 6:** Criar Conselheiro Zelador (ResourceZelador_Agent)

7. **Fase 7:** Criar endpoint PATCH `/api/agents/instances/{id}/mcp-configs`

### Frontend (conductor-web)

8. **Fase 8:** Criar método `getAvailableMcps()` no `agent.service.ts`
   - Chamar `/mcp/list` do Gateway em vez de `/api/system/mcp/sidecars`

9. **Fase 9:** Atualizar `AgentCreatorComponent` para mostrar status dos MCPs

10. **Fase 10:** Criar componente `McpManagerModal`

11. **Fase 11:** Integrar modal no menu ⚙️ do dock

12. **Fase 12:** Testar fluxo completo (criação + gerenciamento de instância)

### Expansão

13. **Fase 13:** Expandir para todos os 80 MCPs
    - Validar que todos os MCPs estão cadastrados
    - Monitorar logs do Watcher e Conselheiro Zelador

---

## 10. Frontend (conductor-web)

O frontend precisa de ajustes para suportar o novo fluxo de MCPs.

### 11.1 Problema Atual

| Componente | Problema |
|------------|----------|
| **mcp-grid** (AgentCreatorComponent) | Chama `/api/system/mcp/sidecars` que só retorna MCPs rodando |
| **agent-launcher-dock** (ConductorChatComponent) | Não tem opção de gerenciar MCPs da instância |
| **Criação de agente** | Funciona, mas depende de MCPs já estarem online |

### 11.2 Alterações Necessárias

#### 9.2.1 Mudar Fonte de Dados do mcp-grid

**Arquivo:** `conductor-web/src/app/services/agent.service.ts`

**Antes:**
```typescript
getAvailableSidecars(): Observable<string[]> {
  return from(
    fetch(`${this.baseUrl}/api/system/mcp/sidecars`, { ... })
  ).pipe(
    map((response: any) => {
      // Retorna apenas MCPs rodando
      return response.sidecars.map((s: any) => s.name);
    })
  );
}
```

**Depois:**
```typescript
getAvailableMcps(): Observable<MCPRegistryEntry[]> {
  // Chamar o Gateway em vez do Conductor
  return from(
    fetch(`${this.gatewayUrl}/mcp/list`, { ... })
  ).pipe(
    map((response: MCPListResponse) => {
      // Retorna TODOS os MCPs registrados (rodando ou não)
      return response.items;
    })
  );
}
```

**Arquivo:** `conductor-web/src/app/living-screenplay-simple/agent-creator/agent-creator.component.ts`

Atualizar para mostrar status do MCP:

```typescript
// Interface para MCP com status
interface MCPOption {
  name: string;
  status: 'healthy' | 'stopped' | 'unknown';
  description?: string;
}

// No template, mostrar indicador de status
// ✅ = healthy (verde)
// ⏸️ = stopped (cinza)
// ❓ = unknown (amarelo)
```

**Template atualizado:**
```html
<div class="mcp-grid">
  <div
    *ngFor="let mcp of filteredMcps"
    class="mcp-option"
    [class.selected]="isMcpSelected(mcp.name)"
    [class.stopped]="mcp.status === 'stopped'"
    (click)="toggleMcp(mcp.name)">
    <span class="mcp-status">{{ getStatusIcon(mcp.status) }}</span>
    <span class="mcp-check">{{ isMcpSelected(mcp.name) ? '✅' : '⬜' }}</span>
    <span class="mcp-name">{{ mcp.name }}</span>
  </div>
</div>

<p class="mcp-hint" *ngIf="hasStoppedMcps()">
  ⏸️ MCPs parados serão iniciados automaticamente quando o agente for executado
</p>
```

#### 9.2.2 Adicionar Gerenciamento de MCP no Dock

**Arquivo:** `conductor-web/src/app/shared/conductor-chat/conductor-chat.component.ts`

Adicionar opção no menu de contexto (⚙️):

```html
<!-- Agent Options Menu -->
<div *ngIf="modalStateService.isOpen('agentOptionsMenu')" class="agent-options-menu">
  <button class="menu-item" (click)="viewAgentContext()">
    📋 Ver Contexto
  </button>
  <button class="menu-item" (click)="editPersona()">
    ✏️ Editar Persona
  </button>
  <button class="menu-item" (click)="editAgentCwd()">
    📁 Editar diretório
  </button>
  <!-- NOVO -->
  <button class="menu-item" (click)="manageMcps()">
    🔌 Gerenciar MCPs
  </button>
</div>
```

#### 9.2.3 Modal de Gerenciamento de MCPs da Instância

**Criar componente:** `conductor-web/src/app/shared/mcp-manager-modal/`

```typescript
@Component({
  selector: 'app-mcp-manager-modal',
  template: `
    <div class="modal-overlay" (click)="close()">
      <div class="modal-content" (click)="$event.stopPropagation()">
        <h3>🔌 Gerenciar MCPs - {{ instanceName }}</h3>

        <div class="mcp-section">
          <h4>MCPs do Template (herdados)</h4>
          <div class="mcp-list inherited">
            <span *ngFor="let mcp of templateMcps" class="mcp-tag">
              {{ mcp }}
            </span>
            <span *ngIf="templateMcps.length === 0" class="empty">
              Nenhum MCP no template
            </span>
          </div>
        </div>

        <div class="mcp-section">
          <h4>MCPs Extras (desta instância)</h4>
          <div class="mcp-list editable">
            <span
              *ngFor="let mcp of instanceMcps"
              class="mcp-tag removable"
              (click)="removeMcp(mcp)">
              {{ mcp }} ✕
            </span>
          </div>

          <div class="add-mcp">
            <select [(ngModel)]="selectedMcp">
              <option value="">Selecionar MCP...</option>
              <option
                *ngFor="let mcp of availableMcps"
                [value]="mcp.name"
                [disabled]="isAlreadyAdded(mcp.name)">
                {{ mcp.name }} ({{ mcp.status }})
              </option>
            </select>
            <button (click)="addMcp()" [disabled]="!selectedMcp">
              ➕ Adicionar
            </button>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-cancel" (click)="close()">Cancelar</button>
          <button class="btn-save" (click)="save()">Salvar</button>
        </div>
      </div>
    </div>
  `
})
export class McpManagerModalComponent {
  @Input() instanceId: string;
  @Input() agentId: string;
  @Output() closed = new EventEmitter<void>();
  @Output() saved = new EventEmitter<string[]>();

  templateMcps: string[] = [];      // MCPs do agent template
  instanceMcps: string[] = [];      // MCPs extras da instância
  availableMcps: MCPOption[] = [];  // Todos os MCPs disponíveis
  selectedMcp: string = '';

  // ... implementar métodos
}
```

#### 9.2.4 Atualizar Coleção agent_instances

A coleção `agent_instances` precisa suportar o campo `mcp_configs`:

```typescript
interface AgentInstance {
  instance_id: string;
  agent_id: string;
  conversation_id: string;
  screenplay_id: string;
  // ... outros campos existentes ...

  // NOVO: MCPs extras desta instância
  mcp_configs?: string[];
}
```

**Endpoint necessário no Gateway:**

```
PATCH /api/agents/instances/{instanceId}/mcp-configs
Body: { "mcp_configs": ["crm", "billing"] }
```

### 11.3 Fluxo de Criação de Agente com MCP

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Usuário clica "➕ Novo" no AgentCatalog                                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. AgentCreatorComponent abre                                              │
│     - Carrega MCPs de GET /mcp/list (Gateway)                              │
│     - Mostra TODOS os MCPs com status (healthy/stopped)                     │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. Usuário preenche formulário                                             │
│     - Nome, descrição, emoji, tags                                          │
│     - Seleciona MCPs (mesmo os stopped)                                     │
│     - Escreve persona                                                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. POST /api/agents                                                        │
│     {                                                                       │
│       "name": "MeuAgente_Agent",                                           │
│       "mcp_configs": ["crm", "billing"],  ← MCPs selecionados              │
│       ...                                                                   │
│     }                                                                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. Agente criado na coleção `agents` com mcp_configs                       │
│     - Quando executado, Watcher vai subir os MCPs necessários              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.4 Fluxo de Gerenciamento de MCP em Instância

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  1. Usuário clica ⚙️ no dock de um agente instanciado                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  2. Menu aparece, usuário clica "🔌 Gerenciar MCPs"                         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  3. McpManagerModal abre                                                    │
│     - Mostra MCPs do template (read-only)                                   │
│     - Mostra MCPs extras da instância (editável)                           │
│     - Lista MCPs disponíveis para adicionar                                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  4. Usuário adiciona/remove MCPs e clica "Salvar"                           │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  5. PATCH /api/agents/instances/{instanceId}/mcp-configs                    │
│     { "mcp_configs": ["extra-mcp-1", "extra-mcp-2"] }                       │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  6. Próxima execução do agente usará:                                       │
│     - MCPs do template (agents.mcp_configs)                                 │
│     - MCPs extras da instância (agent_instances.mcp_configs)               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.5 Arquivos do Frontend a Modificar/Criar

| Arquivo | Alteração |
|---------|-----------|
| `agent.service.ts` | Novo método `getAvailableMcps()` usando `/mcp/list` |
| `agent-creator.component.ts` | Usar novo método, mostrar status dos MCPs |
| `agent-creator.component.html` | Template com indicadores de status |
| `agent-creator.component.css` | Estilos para status (cores) |
| `conductor-chat.component.ts` | Adicionar `manageMcps()` no menu |
| `conductor-chat.component.html` | Novo item no menu de opções |
| **NOVO** `mcp-manager-modal/` | Componente para gerenciar MCPs da instância |

### 11.6 Endpoints Necessários no Gateway

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/mcp/list` | GET | Já existe - listar todos os MCPs |
| `/api/agents/instances/{id}/mcp-configs` | PATCH | **NOVO** - atualizar MCPs da instância |
| `/api/agents/instances/{id}/mcp-configs` | GET | **NOVO** - obter MCPs da instância |

---

## 11. Otimizações Futuras (Anthropic Advanced Tool Use)

> Baseado em: https://www.anthropic.com/engineering/advanced-tool-use

O artigo da Anthropic sobre "Advanced Tool Use" apresenta técnicas que podem ser aplicadas ao Primoia para otimizar ainda mais o uso de MCPs e tools.

### 11.1 Contexto

O MCP On-Demand já implementa o conceito de **defer_loading** no nível de containers:
- MCPs raramente usados ficam desligados
- Sobem apenas quando necessários
- Desligam após período de inatividade

Isso é validado pelo artigo:
> "Keep 3-5 most used tools always loaded; defer the rest"

As otimizações abaixo são o **próximo nível** de refinamento.

### 11.2 Tool Search Tool (Filtragem de Tools)

**Problema:** Um MCP como "CRM" pode expor 50+ tools. Mesmo com o container rodando, o Claude recebe definições de todas as 50 tools, consumindo tokens desnecessariamente.

**Solução:** Implementar filtragem de tools por agente/instância.

**Alteração no mcp_configs:**

```python
# Antes: carrega todas as tools do MCP
mcp_configs: ["crm", "database"]

# Depois: carrega apenas tools específicas
mcp_configs: [
    {"name": "crm", "tools": ["create_lead", "search_contacts", "update_lead"]},
    {"name": "database", "tools": ["find_documents", "insert_document"]}
]
```

**Implementação:**

1. Adicionar campo `tools_whitelist` ao vínculo agente-MCP:

```python
class AgentMCPBinding(BaseModel):
    mcp_name: str
    tools_whitelist: Optional[List[str]] = None  # None = todas as tools
```

2. Gateway filtra tools ao gerar `mcp_config.json`:

```python
def generate_filtered_mcp_config(agent_id: str, instance_id: str) -> dict:
    bindings = get_mcp_bindings(agent_id, instance_id)

    config = {"mcpServers": {}}
    for binding in bindings:
        mcp = get_mcp(binding.mcp_name)

        if binding.tools_whitelist:
            # Gerar config apenas com tools filtradas
            config["mcpServers"][binding.mcp_name] = {
                "type": "sse",
                "url": mcp.url,
                "tools": binding.tools_whitelist  # Filtro
            }
        else:
            # Todas as tools
            config["mcpServers"][binding.mcp_name] = {
                "type": "sse",
                "url": mcp.url
            }

    return config
```

**Benefício esperado:** Redução de até 85% no uso de tokens (conforme artigo).

### 11.3 Tool Use Examples (Exemplos de Uso)

**Problema:** Claude às vezes erra parâmetros ou usa tools de forma subótima porque schemas JSON não expressam padrões de uso.

**Solução:** Adicionar exemplos concretos de uso de tools.

**Alteração no mcp_registry:**

```python
class ToolExample(BaseModel):
    tool_name: str
    description: str
    input_example: dict
    output_example: Optional[dict] = None
    notes: Optional[str] = None

class MCPRegistryEntry(BaseModel):
    # ... campos existentes ...

    tool_examples: List[ToolExample] = Field(
        default_factory=list,
        description="Exemplos de uso das tools para injetar no prompt"
    )
```

**Exemplo de dados:**

```json
{
    "name": "crm",
    "tool_examples": [
        {
            "tool_name": "create_lead",
            "description": "Criar lead com dados mínimos",
            "input_example": {
                "name": "João Silva",
                "email": "joao@empresa.com"
            }
        },
        {
            "tool_name": "create_lead",
            "description": "Criar lead completo com empresa",
            "input_example": {
                "name": "Maria Santos",
                "email": "maria@techcorp.com",
                "company": "TechCorp",
                "phone": "+55 11 99999-0000",
                "source": "website"
            }
        }
    ]
}
```

**Injeção no prompt:**

O PromptEngine pode injetar exemplos relevantes no prompt do agente:

```markdown
## Exemplos de uso das tools disponíveis

### CRM - create_lead
Exemplo 1 (dados mínimos):
```json
{"name": "João Silva", "email": "joao@empresa.com"}
```

Exemplo 2 (dados completos):
```json
{"name": "Maria Santos", "email": "maria@techcorp.com", "company": "TechCorp"}
```
```

**Benefício esperado:** Melhoria de precisão de 72% → 90% (conforme artigo).

### 11.4 Programmatic Tool Calling (Migração para API)

**Situação atual:** O Watcher executa `claude --print` via CLI.

**Limitação:** Cada chamada de tool é uma passagem de inferência separada.

**Solução futura:** Migrar para API com code execution, permitindo:

1. **Execução paralela de tools:**

```python
# Claude gera código que executa múltiplas tools em paralelo
async def execute_task():
    # Buscar dados em paralelo
    leads, contacts, budget = await asyncio.gather(
        mcp.crm.search_leads(query="tech"),
        mcp.crm.get_contacts(company_id=123),
        mcp.finance.get_budget(department="sales")
    )

    # Processar sem nova inferência
    qualified = [l for l in leads if l.score > 80]
    return {"qualified_leads": qualified, "budget_remaining": budget.available}
```

2. **Filtragem de resultados intermediários:**
   - Claude não precisa "ver" todas as 2000 linhas de um resultado
   - Código processa e retorna apenas o relevante

3. **Redução de latência:**
   - Elimina múltiplas passagens de inferência
   - Uma única geração de código orquestra tudo

**Requisitos para migração:**
- Substituir CLI por SDK Python da Anthropic
- Implementar sandbox seguro para code execution
- Adaptar MCPs para serem chamáveis via código

**Benefício esperado:** Redução de 37% em tokens e eliminação de 19+ passagens de inferência em tarefas complexas.

### 11.5 Roadmap de Otimizações

| Otimização | Complexidade | Impacto | Prioridade |
|------------|--------------|---------|------------|
| Tool Search (filtro) | Média | Alto (85% tokens) | P1 - Após MCP On-Demand |
| Tool Use Examples | Baixa | Médio (precisão) | P2 - Quick win |
| Programmatic Calling | Alta | Alto (37% tokens + latência) | P3 - Longo prazo |

### 11.6 Referência

- Artigo original: https://www.anthropic.com/engineering/advanced-tool-use
- Conceitos aplicáveis: Tool Search Tool, Tool Use Examples, Programmatic Tool Calling
- Data de referência: Janeiro 2026

---

## 12. Referências do Projeto

- `conductor-gateway/src/models/mcp_registry.py` - Modelo atual
- `conductor-gateway/src/services/mcp_registry_service.py` - Service atual
- `conductor/poc/container_to_host/claude-mongo-watcher.py` - Watcher atual
- `conductor-web/src/app/services/agent.service.ts` - Service de agentes
- `conductor-web/src/app/living-screenplay-simple/agent-creator/` - Componente de criação
- `conductor-web/src/app/shared/conductor-chat/` - Componente de chat com dock
