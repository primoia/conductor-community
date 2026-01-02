#!/usr/bin/env python3
"""
Script para descobrir MCPs e cadastrá-los no mcp_registry.

Usa docker-compose.centralized.yml como fonte de verdade para portas.

Uso:
    python discover_mcps.py                      # Descobrir e mostrar MCPs
    python discover_mcps.py --register           # Descobrir e cadastrar no MongoDB
    python discover_mcps.py --dry-run            # Mostrar o que seria cadastrado
    python discover_mcps.py --base-path /path    # Usar path customizado
"""

import os
import sys
import yaml
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Caminho base do Primoia (pode ser sobrescrito via argumento)
DEFAULT_BASE_PATH = "/mnt/ramdisk/primoia-main/primoia"


def discover_mcps(base_path: str = DEFAULT_BASE_PATH) -> List[Dict]:
    """
    Descobre MCPs a partir dos docker-compose.centralized.yml files.

    Args:
        base_path: Caminho base onde buscar os docker-compose files

    Returns:
        Lista de dicionários com informações dos MCPs descobertos
    """
    mcps = []
    base_path_obj = Path(base_path)

    if not base_path_obj.exists():
        logger.error(f"Caminho base não existe: {base_path}")
        return mcps

    logger.info(f"Buscando docker-compose.centralized.yml em: {base_path}")

    for compose_file in base_path_obj.rglob("docker-compose.centralized.yml"):
        try:
            with open(compose_file) as f:
                compose = yaml.safe_load(f)

            if not compose:
                continue

            services = compose.get("services", {})

            for service_name, service_config in services.items():
                # Identificar serviço MCP (contém "mcp" no nome)
                if "mcp" not in service_name.lower():
                    continue

                ports = service_config.get("ports", [])

                # Extrair port mapping do docker-compose.centralized.yml
                # Formato: "13145:9000" (host:container)
                host_port = None
                internal_port = "9000"  # Porta padrão MCP

                for port in ports:
                    if isinstance(port, str) and ":" in port:
                        parts = port.split(":")
                        host_port = parts[0]
                        internal_port = parts[1] if len(parts) > 1 else "9000"
                        break
                    elif isinstance(port, int):
                        host_port = str(port)

                # Extrair nome base do MCP_NAME do environment ou do service_name
                env = service_config.get("environment", [])
                mcp_name = None

                if isinstance(env, list):
                    for e in env:
                        if isinstance(e, str) and e.startswith("MCP_NAME="):
                            mcp_name = e.split("=")[1]
                            break
                elif isinstance(env, dict):
                    mcp_name = env.get("MCP_NAME")

                if not mcp_name:
                    # Fallback: extrair do nome do serviço
                    mcp_name = service_name.replace("-mcp", "").replace("verticals-", "").replace("billing-", "")

                # Caminho relativo ao base_path
                try:
                    relative_path = str(compose_file.relative_to(base_path_obj))
                except ValueError:
                    relative_path = str(compose_file)

                # Extrair auth se configurado
                auth = None
                if isinstance(env, list):
                    for e in env:
                        if isinstance(e, str) and e.startswith("MCP_AUTH="):
                            auth = e.split("=", 1)[1]
                            break
                elif isinstance(env, dict):
                    auth = env.get("MCP_AUTH")

                mcp_entry = {
                    "name": mcp_name,
                    "type": "external",
                    "url": f"http://{service_name}:{internal_port}/sse",
                    "host_url": f"http://localhost:{host_port}/sse" if host_port else None,
                    "docker_compose_path": relative_path,
                    "status": "stopped",  # Todos começam parados (on-demand)
                    "auto_shutdown_minutes": 30,
                    "tools_count": 0,
                    "auth": auth,
                    "metadata": {
                        "category": categorize_service(str(compose_file)),
                        "description": f"MCP for {mcp_name}",
                        "service_name": service_name,
                        "discovered_at": datetime.now(timezone.utc).isoformat()
                    }
                }

                mcps.append(mcp_entry)
                logger.info(f"  Descoberto: {mcp_name} -> localhost:{host_port}")

        except Exception as e:
            logger.warning(f"Erro ao processar {compose_file}: {e}")

    logger.info(f"Total de MCPs descobertos: {len(mcps)}")
    return mcps


def categorize_service(path: str) -> str:
    """
    Categoriza serviço baseado no path.

    Args:
        path: Caminho do arquivo docker-compose

    Returns:
        Categoria do serviço
    """
    path_lower = path.lower()

    if "/verticals/" in path_lower:
        return "verticals"
    elif "/billing/" in path_lower:
        return "billing"
    elif "/ai-services/" in path_lower:
        return "ai-services"
    elif "/analytics/" in path_lower:
        return "analytics"
    elif "/infrastructure/" in path_lower:
        return "infrastructure"
    elif "/platform/" in path_lower:
        return "platform"
    elif "/integrations/" in path_lower:
        return "integrations"
    elif "/conductor/" in path_lower:
        return "conductor"

    return "other"


def register_mcps(
    mcps: List[Dict],
    mongo_uri: str = "mongodb://localhost:27017",
    database: str = "conductor_state",
    dry_run: bool = False
) -> Dict:
    """
    Cadastra MCPs descobertos no mcp_registry.

    Args:
        mcps: Lista de MCPs descobertos
        mongo_uri: URI de conexão MongoDB
        database: Nome do database
        dry_run: Se True, apenas mostra o que seria feito

    Returns:
        Dict com estatísticas do cadastro
    """
    stats = {
        "total": len(mcps),
        "registered": 0,
        "updated": 0,
        "skipped": 0,
        "errors": 0
    }

    if dry_run:
        logger.info("=== DRY RUN - Nenhuma alteração será feita ===")
        for mcp in mcps:
            logger.info(f"  [DRY RUN] Cadastraria: {mcp['name']} -> {mcp.get('host_url', 'N/A')}")
        return stats

    try:
        from pymongo import MongoClient

        client = MongoClient(mongo_uri)
        db = client[database]
        registry = db["mcp_registry"]

        logger.info(f"Conectado ao MongoDB: {mongo_uri}/{database}")

        for mcp in mcps:
            try:
                # Verificar se já existe
                existing = registry.find_one({"name": mcp["name"]})

                if existing:
                    # Atualizar campos de on-demand (preservar campos existentes)
                    update_fields = {
                        "host_url": mcp["host_url"],
                        "docker_compose_path": mcp["docker_compose_path"],
                        "auto_shutdown_minutes": mcp["auto_shutdown_minutes"],
                        "metadata": mcp["metadata"],
                        "updated_at": datetime.now(timezone.utc)
                    }

                    # Não sobrescrever status se já estiver healthy
                    if existing.get("status") not in ["healthy", "starting"]:
                        update_fields["status"] = mcp["status"]

                    registry.update_one(
                        {"name": mcp["name"]},
                        {"$set": update_fields}
                    )
                    stats["updated"] += 1
                    logger.info(f"  Atualizado: {mcp['name']}")
                else:
                    # Inserir novo
                    mcp["registered_at"] = datetime.now(timezone.utc)
                    registry.insert_one(mcp)
                    stats["registered"] += 1
                    logger.info(f"  Registrado: {mcp['name']}")

            except Exception as e:
                stats["errors"] += 1
                logger.error(f"  Erro ao processar {mcp['name']}: {e}")

        client.close()

    except ImportError:
        logger.error("PyMongo não está instalado. Execute: pip install pymongo")
        stats["errors"] = len(mcps)
    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {e}")
        stats["errors"] = len(mcps)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Descobrir e cadastrar MCPs no mcp_registry"
    )
    parser.add_argument(
        "--base-path",
        default=DEFAULT_BASE_PATH,
        help=f"Caminho base do Primoia (padrão: {DEFAULT_BASE_PATH})"
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Cadastrar MCPs descobertos no MongoDB"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostrar o que seria cadastrado sem fazer alterações"
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://localhost:27017",
        help="URI de conexão MongoDB"
    )
    parser.add_argument(
        "--database",
        default="conductor_state",
        help="Nome do database MongoDB"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Salvar MCPs descobertos em arquivo JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verbose"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Descobrir MCPs
    logger.info("=" * 60)
    logger.info("MCP Discovery Tool - On-Demand System")
    logger.info("=" * 60)

    mcps = discover_mcps(args.base_path)

    if not mcps:
        logger.warning("Nenhum MCP descoberto!")
        sys.exit(1)

    # Mostrar resumo
    logger.info("")
    logger.info("=" * 60)
    logger.info("RESUMO DOS MCPs DESCOBERTOS")
    logger.info("=" * 60)

    categories = {}
    for mcp in mcps:
        cat = mcp["metadata"]["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(mcp["name"])

    for cat, names in sorted(categories.items()):
        logger.info(f"  {cat}: {len(names)} MCPs")
        for name in sorted(names):
            mcp = next(m for m in mcps if m["name"] == name)
            logger.info(f"    - {name} ({mcp.get('host_url', 'N/A')})")

    # Salvar em arquivo se solicitado
    if args.output:
        with open(args.output, "w") as f:
            json.dump(mcps, f, indent=2, default=str)
        logger.info(f"\nMCPs salvos em: {args.output}")

    # Cadastrar no MongoDB se solicitado
    if args.register or args.dry_run:
        logger.info("")
        logger.info("=" * 60)
        logger.info("CADASTRO NO MONGODB")
        logger.info("=" * 60)

        stats = register_mcps(
            mcps,
            mongo_uri=args.mongo_uri,
            database=args.database,
            dry_run=args.dry_run
        )

        logger.info("")
        logger.info("Estatísticas:")
        logger.info(f"  Total descobertos: {stats['total']}")
        logger.info(f"  Novos registrados: {stats['registered']}")
        logger.info(f"  Atualizados: {stats['updated']}")
        logger.info(f"  Erros: {stats['errors']}")

    logger.info("")
    logger.info("=" * 60)
    logger.info("Concluído!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
