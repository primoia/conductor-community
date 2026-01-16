#!/usr/bin/env python3
"""
Script para adicionar MCP_HOST_PORT nos docker-compose.centralized.yml
que têm MCP sidecar mas não têm MCP_HOST_PORT configurado.

Extrai a porta externa do mapeamento de portas (ex: 13145:9000 → 13145)
e adiciona como MCP_HOST_PORT no environment do sidecar.

Uso:
    python add_mcp_host_port.py [--dry-run]
"""

import re
import argparse
from pathlib import Path

# Base path do Primoia
BASE_PATH = Path("/mnt/ramdisk/primoia-main/primoia")


def find_files_needing_update(base_path: Path) -> list[tuple[Path, str, str]]:
    """
    Encontra arquivos com MCP sidecar mas sem MCP_HOST_PORT.

    Returns:
        Lista de tuplas (path, external_port, mcp_name)
    """
    files_to_update = []

    for f in base_path.rglob("docker-compose.centralized.yml"):
        content = f.read_text()

        # Deve ter mcp-sidecar
        if "mcp-sidecar" not in content.lower():
            continue

        # Já tem MCP_HOST_PORT? Pular
        if "MCP_HOST_PORT" in content:
            continue

        # Extrair porta externa do mapeamento
        # Padrão: "- 13145:9000" ou "- '13145:9000'"
        port_match = re.search(r'ports:\s*\n\s*-\s*["\']?(\d+):9000', content)
        if not port_match:
            continue

        external_port = port_match.group(1)

        # Extrair MCP_NAME se existir
        name_match = re.search(r'MCP_NAME=(\S+)', content)
        mcp_name = name_match.group(1) if name_match else "unknown"

        files_to_update.append((f, external_port, mcp_name))

    return files_to_update


def update_compose_file(file_path: Path, external_port: str, dry_run: bool = False) -> tuple[bool, str]:
    """
    Atualiza um arquivo docker-compose adicionando MCP_HOST_PORT.

    Returns:
        tuple: (updated, message)
    """
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        new_lines = []
        updated = False

        for i, line in enumerate(lines):
            new_lines.append(line)

            # Procurar linha com MCP_NAME ou MCP_PORT para inserir após
            # Suporta ambos formatos: "- MCP_NAME=value" e "MCP_NAME: value"
            has_mcp_key = ('MCP_NAME=' in line or 'MCP_PORT=' in line or
                          'MCP_NAME:' in line or 'MCP_PORT:' in line)

            if has_mcp_key and not updated:
                # Verificar se próxima linha já não tem MCP_HOST_PORT
                if i + 1 < len(lines) and 'MCP_HOST_PORT' in lines[i + 1]:
                    continue

                # Detectar indentação
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent

                # Detectar formato (com = ou com :)
                if '=' in line and line.strip().startswith('-'):
                    # Formato: "- MCP_NAME=value"
                    new_lines.append(f"{indent_str}- MCP_HOST_PORT={external_port}")
                else:
                    # Formato: "MCP_NAME: value"
                    new_lines.append(f"{indent_str}MCP_HOST_PORT: '{external_port}'")
                updated = True

        if updated:
            new_content = '\n'.join(new_lines)

            if dry_run:
                return True, f"would add MCP_HOST_PORT={external_port}"

            file_path.write_text(new_content)
            return True, f"added MCP_HOST_PORT={external_port}"

        return False, "MCP_NAME or MCP_PORT not found to insert after"

    except Exception as e:
        return False, f"error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Adiciona MCP_HOST_PORT nos docker-compose.centralized.yml"
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

    print(f"{'[DRY-RUN] ' if args.dry_run else ''}Buscando arquivos sem MCP_HOST_PORT...")
    print()

    files_to_update = find_files_needing_update(base_path)
    print(f"Encontrados {len(files_to_update)} arquivos para atualizar")
    print()

    updated_count = 0
    error_count = 0

    for file_path, external_port, mcp_name in sorted(files_to_update):
        relative_path = file_path.relative_to(base_path)
        updated, message = update_compose_file(file_path, external_port, dry_run=args.dry_run)

        if updated:
            print(f"  [UPDATE] {relative_path}")
            print(f"           MCP: {mcp_name}, Port: {external_port}")
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
    print(f"  Total:       {len(files_to_update)}")
    print("=" * 60)

    if args.dry_run and updated_count > 0:
        print()
        print("Execute sem --dry-run para aplicar as mudanças.")


if __name__ == "__main__":
    main()
