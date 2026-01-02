#!/usr/bin/env python3
"""
Script para adicionar MCP_NAME e MCP_REGISTRY_URL nos docker-compose.centralized.yml
que têm MCP sidecar mas não têm MCP_NAME configurado.

Uso:
    python add_mcp_name.py [--dry-run]
"""

import re
import argparse
from pathlib import Path

# Base path do Primoia
BASE_PATH = Path("/mnt/ramdisk/primoia-main/primoia")

# Linhas a adicionar
MCP_REGISTRY_URL_LINE = "    - MCP_REGISTRY_URL=${MCP_REGISTRY_URL:-http://community-conductor-mcp:8080}"


def find_files_missing_mcp_name(base_path: Path) -> list[tuple[Path, str, str]]:
    """
    Encontra arquivos com MCP sidecar mas sem MCP_NAME.

    Returns:
        Lista de tuplas (path, container_name, mcp_name_derivado)
    """
    files_missing = []

    for f in base_path.rglob("docker-compose.centralized.yml"):
        content = f.read_text()

        if 'mcp-sidecar' not in content.lower():
            continue

        if 'MCP_NAME' in content:
            continue

        # Extrair container_name do serviço MCP
        match = re.search(r'container_name:\s*(\S+-mcp)', content)
        if match:
            container = match.group(1)
            # Derivar MCP_NAME do container (remover -mcp no final)
            mcp_name = container.replace('-mcp', '').replace('_', '-')
            files_missing.append((f, container, mcp_name))
        else:
            # Tentar extrair do nome do serviço
            match = re.search(r'^\s+(\S+-mcp):\s*$', content, re.MULTILINE)
            if match:
                service = match.group(1)
                mcp_name = service.replace('-mcp', '').replace('_', '-')
                files_missing.append((f, service, mcp_name))

    return files_missing


def update_compose_file(file_path: Path, mcp_name: str, dry_run: bool = False) -> tuple[bool, str]:
    """
    Atualiza um arquivo docker-compose adicionando MCP_NAME e MCP_REGISTRY_URL.

    Returns:
        tuple: (updated, message)
    """
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        new_lines = []
        updated = False
        in_mcp_service = False
        added_mcp_name = False

        for i, line in enumerate(lines):
            new_lines.append(line)

            # Detectar se estamos no serviço MCP
            # Pode ser via container_name ou via nome do serviço (linha que termina com -mcp:)
            if 'container_name:' in line and '-mcp' in line:
                in_mcp_service = True
            elif line.strip().endswith('-mcp:') and not line.strip().startswith('#'):
                in_mcp_service = True

            # Se estamos no serviço MCP e encontramos linha de referência, adicionar MCP_NAME após
            # Referências em ordem de prioridade: MCP_PORT, TARGET_URL, ENABLE_IAM
            reference_found = any(ref in line for ref in ['MCP_PORT', 'TARGET_URL', 'ENABLE_IAM'])
            if in_mcp_service and reference_found and not added_mcp_name:
                # Adicionar MCP_NAME
                new_lines.append(f"    - MCP_NAME={mcp_name}")
                # Adicionar MCP_REGISTRY_URL se não existir
                if 'MCP_REGISTRY_URL' not in content:
                    new_lines.append(MCP_REGISTRY_URL_LINE)
                updated = True
                added_mcp_name = True
                in_mcp_service = False  # Reset para não adicionar novamente

        if updated:
            new_content = '\n'.join(new_lines)

            if dry_run:
                return True, f"would add MCP_NAME={mcp_name}"

            file_path.write_text(new_content)
            return True, f"added MCP_NAME={mcp_name}"

        return False, "no MCP_PORT found to insert after"

    except Exception as e:
        return False, f"error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Adiciona MCP_NAME e MCP_REGISTRY_URL nos docker-compose"
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

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Buscando arquivos sem MCP_NAME...")
    print()

    files_missing = find_files_missing_mcp_name(base_path)
    print(f"Encontrados {len(files_missing)} arquivos sem MCP_NAME")
    print()

    updated_count = 0
    error_count = 0

    for file_path, container, mcp_name in sorted(files_missing):
        relative_path = file_path.relative_to(base_path)
        updated, message = update_compose_file(file_path, mcp_name, dry_run=args.dry_run)

        if updated:
            print(f"  [UPDATE] {relative_path}")
            print(f"           {message}")
            updated_count += 1
        else:
            print(f"  [ERROR]  {relative_path}")
            print(f"           {message}")
            error_count += 1

    print()
    print("=" * 60)
    print(f"Resumo:")
    print(f"  Atualizados: {updated_count}")
    print(f"  Erros:       {error_count}")
    print(f"  Total:       {len(files_missing)}")
    print("=" * 60)

    if args.dry_run and updated_count > 0:
        print()
        print("Execute sem --dry-run para aplicar as mudanças.")


if __name__ == "__main__":
    main()
