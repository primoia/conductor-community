#!/usr/bin/env python3
"""
Script de Soft Delete em Cascata: Screenplays -> Conversations -> Agent Instances

Este script propaga o soft delete de screenplays para suas entidades relacionadas:
1. Busca todos os screenplays com isDeleted = true
2. Marca as conversations relacionadas com isDeleted = true
3. Para cada conversation, marca os agent_instances (participants) com is_deleted = true

Autor: Claude Code Assistant
Data: 2025-01-10
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
# Tenta carregar .env.centralized primeiro, depois .env
script_dir = Path(__file__).parent.parent
env_centralized = script_dir / '.env.centralized'
env_local = script_dir / '.env'

if env_centralized.exists():
    load_dotenv(env_centralized)
    logger.info(f"Carregado: {env_centralized}")
elif env_local.exists():
    load_dotenv(env_local)
    logger.info(f"Carregado: {env_local}")
else:
    load_dotenv()  # Tenta .env no diretório atual


def connect_to_mongodb():
    """Conecta ao MongoDB usando variáveis de ambiente."""
    # Tenta diferentes nomes de variáveis usados no projeto
    mongo_uri = (
        os.getenv('MONGODB_URI') or
        os.getenv('MONGO_URI') or
        os.getenv('MONGO_URL') or
        os.getenv('MONGODB_URL')
    )

    if not mongo_uri:
        raise ValueError(
            "Nenhuma URI do MongoDB encontrada. "
            "Defina MONGODB_URI, MONGO_URI, MONGO_URL ou MONGODB_URL"
        )

    # Se rodando fora do Docker, substituir hostname do container por localhost
    if 'primoia-shared-mongo' in mongo_uri:
        mongo_uri_local = mongo_uri.replace('primoia-shared-mongo', 'localhost')
        logger.info("Detectado hostname Docker, tentando localhost primeiro...")
        try:
            client = MongoClient(mongo_uri_local, serverSelectionTimeoutMS=3000)
            client.admin.command('ping')
            mongo_uri = mongo_uri_local
        except Exception:
            logger.info("localhost falhou, usando URI original (Docker)")

    client = MongoClient(mongo_uri)

    # Usar conductor_state como padrão (banco principal do projeto)
    db_name = os.getenv('MONGO_DATABASE') or 'conductor_state'
    db = client[db_name]
    logger.info(f"Conectado ao MongoDB: {db_name}")
    return db


def get_deleted_screenplays(db):
    """Busca todos os screenplays com isDeleted = true."""
    screenplays = db.screenplays

    deleted = list(screenplays.find({"isDeleted": True}))
    logger.info(f"Encontrados {len(deleted)} screenplays deletados")

    return deleted


def soft_delete_conversations(db, screenplay_ids: list, dry_run: bool = True):
    """
    Marca conversations relacionadas aos screenplays como deletadas.

    Args:
        db: Database MongoDB
        screenplay_ids: Lista de IDs de screenplays deletados
        dry_run: Se True, apenas simula sem modificar dados

    Returns:
        Tuple (conversations_updated, instance_ids_to_delete)
    """
    conversations = db.conversations

    # Buscar conversations que ainda não estão deletadas
    query = {
        "screenplay_id": {"$in": screenplay_ids},
        "$or": [
            {"isDeleted": {"$exists": False}},
            {"isDeleted": False}
        ]
    }

    convs_to_update = list(conversations.find(query))
    logger.info(f"Encontradas {len(convs_to_update)} conversations para marcar como deletadas")

    # Coletar todos os instance_ids dos participants
    instance_ids = set()
    for conv in convs_to_update:
        participants = conv.get('participants', [])
        for participant in participants:
            instance_id = participant.get('instance_id')
            if instance_id:
                instance_ids.add(instance_id)

        if dry_run:
            logger.info(f"  [DRY RUN] Conversation: {conv.get('conversation_id')} "
                       f"(screenplay: {conv.get('screenplay_id')}, "
                       f"participants: {len(participants)})")

    # Atualizar conversations
    if not dry_run and convs_to_update:
        result = conversations.update_many(
            {"_id": {"$in": [c['_id'] for c in convs_to_update]}},
            {
                "$set": {
                    "isDeleted": True,
                    "deletedAt": datetime.utcnow().isoformat(),
                    "_cascadeDelete": {
                        "reason": "screenplay_deleted",
                        "deletedAt": datetime.utcnow().isoformat()
                    }
                }
            }
        )
        logger.info(f"Conversations atualizadas: {result.modified_count}")

    return len(convs_to_update), list(instance_ids)


def soft_delete_agent_instances(db, instance_ids: list, dry_run: bool = True):
    """
    Marca agent_instances como deletados.

    Args:
        db: Database MongoDB
        instance_ids: Lista de instance_ids para marcar como deletados
        dry_run: Se True, apenas simula sem modificar dados

    Returns:
        Número de instances atualizadas
    """
    if not instance_ids:
        logger.info("Nenhum agent_instance para atualizar")
        return 0

    agent_instances = db.agent_instances

    # Buscar apenas os que ainda não estão deletados (usa isDeleted camelCase)
    query = {
        "instance_id": {"$in": instance_ids},
        "$or": [
            {"isDeleted": {"$exists": False}},
            {"isDeleted": False}
        ]
    }

    instances_to_update = list(agent_instances.find(query))
    logger.info(f"Encontrados {len(instances_to_update)} agent_instances para marcar como deletados")

    if dry_run:
        for inst in instances_to_update:
            logger.info(f"  [DRY RUN] Agent instance: {inst.get('instance_id')} "
                       f"(agent_id: {inst.get('agent_id')}, "
                       f"screenplay_id: {inst.get('screenplay_id')})")
    else:
        if instances_to_update:
            result = agent_instances.update_many(
                {"_id": {"$in": [i['_id'] for i in instances_to_update]}},
                {
                    "$set": {
                        "isDeleted": True,
                        "deleted_at": datetime.utcnow().isoformat(),
                        "_cascadeDelete": {
                            "reason": "conversation_deleted",
                            "deletedAt": datetime.utcnow().isoformat()
                        }
                    }
                }
            )
            logger.info(f"Agent instances atualizados: {result.modified_count}")

    return len(instances_to_update)


def soft_delete_agent_instances_by_screenplay(db, screenplay_ids: list, dry_run: bool = True):
    """
    Marca agent_instances diretamente relacionados aos screenplays como deletados.
    (Para casos onde agent_instances têm screenplay_id diretamente)

    Args:
        db: Database MongoDB
        screenplay_ids: Lista de IDs de screenplays deletados
        dry_run: Se True, apenas simula sem modificar dados

    Returns:
        Número de instances atualizadas
    """
    agent_instances = db.agent_instances

    # Buscar agent_instances vinculados aos screenplays e ainda não deletados (usa isDeleted camelCase)
    query = {
        "screenplay_id": {"$in": screenplay_ids},
        "$or": [
            {"isDeleted": {"$exists": False}},
            {"isDeleted": False}
        ]
    }

    instances_to_update = list(agent_instances.find(query))
    logger.info(f"Encontrados {len(instances_to_update)} agent_instances diretamente vinculados aos screenplays")

    if dry_run:
        for inst in instances_to_update:
            logger.info(f"  [DRY RUN] Agent instance (via screenplay): {inst.get('instance_id')} "
                       f"(screenplay_id: {inst.get('screenplay_id')})")
    else:
        if instances_to_update:
            result = agent_instances.update_many(
                {"_id": {"$in": [i['_id'] for i in instances_to_update]}},
                {
                    "$set": {
                        "isDeleted": True,
                        "deleted_at": datetime.utcnow().isoformat(),
                        "_cascadeDelete": {
                            "reason": "screenplay_deleted",
                            "deletedAt": datetime.utcnow().isoformat()
                        }
                    }
                }
            )
            logger.info(f"Agent instances atualizados: {result.modified_count}")

    return len(instances_to_update)


def run_cascade_delete(db, dry_run: bool = True):
    """
    Executa o soft delete em cascata.

    Args:
        db: Database MongoDB
        dry_run: Se True, apenas simula sem modificar dados

    Returns:
        Dict com estatísticas da operação
    """
    stats = {
        "screenplays_deleted": 0,
        "conversations_updated": 0,
        "agent_instances_from_conversations": 0,
        "agent_instances_from_screenplays": 0
    }

    # 1. Buscar screenplays deletados
    deleted_screenplays = get_deleted_screenplays(db)
    stats["screenplays_deleted"] = len(deleted_screenplays)

    if not deleted_screenplays:
        logger.info("Nenhum screenplay deletado encontrado. Nada a fazer.")
        return stats

    # Extrair IDs dos screenplays
    screenplay_ids = [s.get('id') or str(s.get('_id')) for s in deleted_screenplays]
    logger.info(f"IDs dos screenplays deletados: {screenplay_ids}")

    # 2. Soft delete das conversations relacionadas
    logger.info("\n--- Processando Conversations ---")
    convs_updated, instance_ids_from_convs = soft_delete_conversations(db, screenplay_ids, dry_run)
    stats["conversations_updated"] = convs_updated

    # 3. Soft delete dos agent_instances (via participants das conversations)
    logger.info("\n--- Processando Agent Instances (via conversations) ---")
    instances_from_convs = soft_delete_agent_instances(db, instance_ids_from_convs, dry_run)
    stats["agent_instances_from_conversations"] = instances_from_convs

    # 4. Soft delete dos agent_instances (vinculados diretamente aos screenplays)
    logger.info("\n--- Processando Agent Instances (via screenplay_id) ---")
    instances_from_screenplays = soft_delete_agent_instances_by_screenplay(db, screenplay_ids, dry_run)
    stats["agent_instances_from_screenplays"] = instances_from_screenplays

    return stats


def print_summary(stats: dict, dry_run: bool):
    """Imprime resumo da operação."""
    mode = "[DRY RUN]" if dry_run else "[EXECUTADO]"

    logger.info(f"\n{'='*60}")
    logger.info(f"RESUMO DA OPERACAO {mode}")
    logger.info(f"{'='*60}")
    logger.info(f"Screenplays deletados encontrados: {stats['screenplays_deleted']}")
    logger.info(f"Conversations marcadas como deletadas: {stats['conversations_updated']}")
    logger.info(f"Agent instances (via conversations): {stats['agent_instances_from_conversations']}")
    logger.info(f"Agent instances (via screenplay_id): {stats['agent_instances_from_screenplays']}")
    logger.info(f"{'='*60}")

    total_instances = stats['agent_instances_from_conversations'] + stats['agent_instances_from_screenplays']
    logger.info(f"TOTAL agent_instances afetados: {total_instances}")


def main():
    """Função principal do script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Propaga soft delete de screenplays para conversations e agent_instances'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular sem modificar dados (recomendado executar primeiro)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Executar as alterações (use com cuidado!)'
    )

    args = parser.parse_args()

    # Por segurança, requer --execute explícito para modificar dados
    if not args.dry_run and not args.execute:
        logger.warning("Por seguranca, use --dry-run para simular ou --execute para aplicar")
        logger.warning("Exemplo: python cascade_soft_delete_from_screenplays.py --dry-run")
        sys.exit(1)

    dry_run = args.dry_run or not args.execute

    try:
        # Conectar ao MongoDB
        db = connect_to_mongodb()

        if dry_run:
            logger.info("\n[DRY RUN] Modo de simulacao - nenhuma alteracao sera feita\n")
        else:
            logger.info("\n[EXECUTE] Modo de execucao - alteracoes serao aplicadas!\n")

        # Executar cascade delete
        stats = run_cascade_delete(db, dry_run=dry_run)

        # Imprimir resumo
        print_summary(stats, dry_run)

        if dry_run:
            logger.info("\nPara aplicar as alteracoes, execute com --execute")

    except Exception as e:
        logger.error(f"Erro durante execucao: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
