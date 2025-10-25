#!/usr/bin/env python3
"""
Script de migração: councilor_executions → tasks

Este script migra execuções de conselheiros da coleção legacy councilor_executions
para a coleção unificada tasks, adicionando os campos necessários.

Uso:
    python migrate_councilor_executions.py [--dry-run] [--batch-size=100]
"""

import os
import sys
from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import argparse


def connect_to_mongodb(mongo_uri: str):
    """Conecta ao MongoDB e retorna o database"""
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client.conductor_state
        print(f"✅ Conectado ao MongoDB com sucesso")
        return db, client
    except ConnectionFailure as e:
        print(f"❌ Falha ao conectar com MongoDB: {e}")
        sys.exit(1)


def migrate_executions(db, dry_run: bool = False, batch_size: int = 100):
    """Migra execuções de councilor_executions para tasks"""

    legacy_collection = db.councilor_executions
    tasks_collection = db.tasks

    # Contar documentos a migrar
    total_docs = legacy_collection.count_documents({})
    print(f"\n📊 Total de execuções a migrar: {total_docs}")

    if total_docs == 0:
        print("ℹ️  Nenhuma execução para migrar")
        return 0

    if dry_run:
        print("🔍 MODO DRY-RUN: Nenhum dado será modificado")
        print("\nPrimeiro documento como exemplo:")
        sample = legacy_collection.find_one()
        if sample:
            print(f"   execution_id: {sample.get('execution_id')}")
            print(f"   councilor_id: {sample.get('councilor_id')}")
            print(f"   status: {sample.get('status')}")
            print(f"   severity: {sample.get('severity')}")
            print(f"   started_at: {sample.get('started_at')}")
        return 0

    # Processar em lotes
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    cursor = legacy_collection.find().batch_size(batch_size)

    print(f"\n🔄 Iniciando migração em lotes de {batch_size}...")

    for execution in cursor:
        try:
            # Verificar se já foi migrado
            existing = tasks_collection.find_one({
                "agent_id": execution.get("councilor_id"),
                "is_councilor_execution": True,
                "created_at": execution.get("started_at")
            })

            if existing:
                skipped_count += 1
                continue

            # Mapear campos de execution para task
            task_doc = {
                "agent_id": execution.get("councilor_id"),
                "provider": "claude",  # Default provider
                "prompt": f"Councilor task: {execution.get('councilor_id')}",  # Placeholder
                "cwd": os.getcwd(),  # Default cwd
                "timeout": 600,
                "status": execution.get("status", "completed"),
                "instance_id": None,  # Não temos no legacy
                "context": {},
                "created_at": execution.get("started_at") or execution.get("created_at"),
                "updated_at": execution.get("created_at"),
                "started_at": execution.get("started_at"),
                "completed_at": execution.get("completed_at"),
                "result": execution.get("output") or execution.get("error") or "",
                "exit_code": 0 if execution.get("status") == "completed" else 1,
                "duration": execution.get("duration_ms") / 1000.0 if execution.get("duration_ms") else None,
                # Campos específicos de conselheiros
                "is_councilor_execution": True,
                "councilor_config": None,  # Não temos no legacy
                "severity": execution.get("severity", "success")
            }

            # Inserir na coleção tasks
            tasks_collection.insert_one(task_doc)
            migrated_count += 1

            if migrated_count % 10 == 0:
                print(f"   ✓ Migrados: {migrated_count}/{total_docs}")

        except Exception as e:
            error_count += 1
            print(f"   ❌ Erro ao migrar execution {execution.get('execution_id')}: {e}")
            continue

    print(f"\n✅ Migração concluída!")
    print(f"   📊 Total processados: {total_docs}")
    print(f"   ✓ Migrados: {migrated_count}")
    print(f"   ⏭️  Pulados (já existentes): {skipped_count}")
    print(f"   ❌ Erros: {error_count}")

    return migrated_count


def create_indexes(db):
    """Cria índices necessários na coleção tasks"""
    print("\n📑 Criando índices na coleção tasks...")

    tasks_collection = db.tasks

    try:
        # Índice composto para queries de conselheiros
        tasks_collection.create_index([
            ("agent_id", 1),
            ("is_councilor_execution", 1),
            ("created_at", -1)
        ], name="councilor_executions_idx")

        # Índice para severity
        tasks_collection.create_index("severity", name="severity_idx")

        # Índice para is_councilor_execution
        tasks_collection.create_index("is_councilor_execution", name="is_councilor_idx")

        print("✅ Índices criados com sucesso")

    except Exception as e:
        print(f"⚠️  Aviso ao criar índices: {e}")


def backup_collection(db):
    """Cria backup da coleção councilor_executions"""
    print("\n💾 Criando backup da coleção councilor_executions...")

    legacy_collection = db.councilor_executions
    backup_collection = db.councilor_executions_backup

    try:
        # Copiar todos os documentos
        docs = list(legacy_collection.find())
        if docs:
            backup_collection.insert_many(docs)
            print(f"✅ Backup criado: {len(docs)} documentos em councilor_executions_backup")
        else:
            print("ℹ️  Nenhum documento para backup")

    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Migra execuções de conselheiros para coleção tasks unificada"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa sem modificar dados (apenas mostra o que seria feito)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Tamanho do lote para processamento (padrão: 100)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Pula criação de backup"
    )
    parser.add_argument(
        "--mongo-uri",
        type=str,
        default=os.getenv("MONGO_URI"),
        help="MongoDB connection URI (padrão: variável MONGO_URI)"
    )

    args = parser.parse_args()

    if not args.mongo_uri:
        print("❌ MONGO_URI não definida. Use --mongo-uri ou defina a variável de ambiente MONGO_URI")
        sys.exit(1)

    print("=" * 80)
    print("🔄 MIGRAÇÃO: councilor_executions → tasks")
    print("=" * 80)

    # Conectar ao MongoDB
    db, client = connect_to_mongodb(args.mongo_uri)

    try:
        # Criar backup se não for dry-run e não for --no-backup
        if not args.dry_run and not args.no_backup:
            backup_collection(db)

        # Criar índices
        if not args.dry_run:
            create_indexes(db)

        # Migrar execuções
        migrated = migrate_executions(db, dry_run=args.dry_run, batch_size=args.batch_size)

        if migrated > 0:
            print("\n🎉 Migração concluída com sucesso!")
            print("\n📝 Próximos passos:")
            print("   1. Verificar se os dados foram migrados corretamente")
            print("   2. Testar a aplicação para garantir compatibilidade")
            print("   3. Após validação, você pode remover a coleção legacy:")
            print("      db.councilor_executions.drop()")
        elif args.dry_run:
            print("\n✅ Dry-run concluído. Execute sem --dry-run para migrar.")
        else:
            print("\n✅ Nenhuma migração necessária (sem dados ou já migrados).")

    except Exception as e:
        print(f"\n❌ Erro durante migração: {e}")
        sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
