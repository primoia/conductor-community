#!/usr/bin/env python3
"""
Script para atualizar todos os docker-compose.centralized.yml
adicionando MCP_REGISTRY_URL nos serviços MCP sidecar.

Uso:
    python update_mcp_registry_url.py [--dry-run]
"""

import os
import sys
import argparse
from pathlib import Path

# Base path do Primoia
BASE_PATH = Path("/mnt/ramdisk/primoia-main/primoia")

# Variável a adicionar
MCP_REGISTRY_URL_LINE = "    - MCP_REGISTRY_URL=${MCP_REGISTRY_URL:-http://community-conductor-mcp:8080}"

# Linhas de referência para inserir após (em ordem de prioridade)
REFERENCE_LINES = ["MCP_REGISTRY_ENABLED", "MCP_NAME"]


def find_compose_files(base_path: Path) -> list[Path]:
    """Encontra todos os docker-compose.centralized.yml"""
    return list(base_path.rglob("docker-compose.centralized.yml"))


def is_mcp_service(lines: list[str], start_idx: int) -> bool:
    """Verifica se um serviço é um MCP sidecar"""
    for i in range(start_idx, min(start_idx + 20, len(lines))):
        line = lines[i]
        if "mcp-sidecar" in line.lower() or "mcp_name" in line.upper():
            return True
        # Se encontrar outro serviço, parar
        if i > start_idx and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
            break
    return False


def needs_update(content: str) -> bool:
    """Verifica se o arquivo precisa de atualização"""
    # Tem MCP sidecar mas não tem MCP_REGISTRY_URL
    has_mcp = "mcp-sidecar" in content.lower() or "MCP_NAME" in content
    has_registry_url = "MCP_REGISTRY_URL" in content
    return has_mcp and not has_registry_url


def update_compose_file(file_path: Path, dry_run: bool = False) -> tuple[bool, str]:
    """
    Atualiza um arquivo docker-compose adicionando MCP_REGISTRY_URL.

    Returns:
        tuple: (updated, message)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        if not needs_update(content):
            if "MCP_REGISTRY_URL" in content:
                return False, "already has MCP_REGISTRY_URL"
            return False, "not an MCP sidecar service"

        lines = content.split('\n')
        new_lines = []
        updated = False

        for i, line in enumerate(lines):
            new_lines.append(line)

            # Encontrar a linha de referência e inserir após ela
            for ref_line in REFERENCE_LINES:
                if ref_line in line and "MCP_REGISTRY_URL" not in line:
                    # Verificar se a próxima linha já não tem MCP_REGISTRY_URL
                    if i + 1 < len(lines) and "MCP_REGISTRY_URL" not in lines[i + 1]:
                        new_lines.append(MCP_REGISTRY_URL_LINE)
                        updated = True
                    break  # Só inserir uma vez por serviço

        if updated:
            new_content = '\n'.join(new_lines)

            if dry_run:
                return True, "would be updated (dry-run)"

            with open(file_path, 'w') as f:
                f.write(new_content)

            return True, "updated successfully"

        return False, "no changes needed"

    except Exception as e:
        return False, f"error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Atualiza docker-compose.centralized.yml com MCP_REGISTRY_URL"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Apenas mostra o que seria feito, sem modificar arquivos"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=str(BASE_PATH),
        help=f"Caminho base para buscar (default: {BASE_PATH})"
    )

    args = parser.parse_args()
    base_path = Path(args.path)

    if not base_path.exists():
        print(f"Erro: Caminho não existe: {base_path}")
        sys.exit(1)

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Buscando docker-compose.centralized.yml em {base_path}...")
    print()

    compose_files = find_compose_files(base_path)
    print(f"Encontrados {len(compose_files)} arquivos docker-compose.centralized.yml")
    print()

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for file_path in sorted(compose_files):
        relative_path = file_path.relative_to(base_path)
        updated, message = update_compose_file(file_path, dry_run=args.dry_run)

        if updated:
            print(f"  [UPDATE] {relative_path}")
            print(f"           {message}")
            updated_count += 1
        elif "error" in message:
            print(f"  [ERROR]  {relative_path}")
            print(f"           {message}")
            error_count += 1
        else:
            print(f"  [SKIP]   {relative_path} - {message}")
            skipped_count += 1

    print()
    print("=" * 60)
    print(f"Resumo:")
    print(f"  Atualizados: {updated_count}")
    print(f"  Ignorados:   {skipped_count}")
    print(f"  Erros:       {error_count}")
    print(f"  Total:       {len(compose_files)}")
    print("=" * 60)

    if args.dry_run and updated_count > 0:
        print()
        print("Execute sem --dry-run para aplicar as mudanças.")


if __name__ == "__main__":
    main()
