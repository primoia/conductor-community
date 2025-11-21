# Conductor Community

Project: conductor-community

## Contexto
Repositório público self-contained que permite executar o stack completo do Conductor da forma mais simples possível. Integra via Git submodules os 3 componentes principais (conductor, conductor-gateway, conductor-web) e provê orquestração Docker Compose para deployment imediato. Oferece dois modos: uso simples com imagens pré-buildadas do Docker Hub (end users) e modo desenvolvimento com submodules e live-reload (contributors).

## Stack
- **Orchestration**: Docker Compose (production + dev variants)
- **Submodules**: Git submodules para conductor, conductor-gateway, conductor-web
- **Database**: MongoDB 27017 (main database)
- **API**: Conductor API (port 3000, internal 8000)
- **Gateway**: FastAPI Gateway (port 5006, internal 8080)
- **Web UI**: Nginx + Angular + React (port 8080)
- **Configuration**: YAML-based config + .env files (gitignored)

## Capacidades Principais
- **One-Command Deployment**: `docker-compose up -d` para end users (imagens pré-buildadas)
- **Development Mode**: `./run-start-all-dev.sh` para contributors (build local + live-reload)
- **Git Submodules Management**: Scripts para update, commit e sincronização de submodules
- **Environment Setup**: `./setup.sh` cria todos os .env files a partir de templates
- **Pre-Built Images**: Docker Hub images para deployment sem build (rápido)
- **Source Code Access**: Modo dev mapeia source code para desenvolvimento local
- **Service Health Checks**: Health checks automáticos em todos os containers
- **Auto-Restart**: Containers com restart policy (unless-stopped)
- **Configuration Isolation**: Configs separados por serviço (conductor/, gateway/)
- **Port Mapping**: Ports externos mapeados para internos (3000→8000, 5006→8080, 8080→80)
- **Watcher Integration**: run-start-all-dev.sh inicia Docker + watchers simultaneamente
- **Test Stack**: `./test-stack.sh` para diagnósticos de conectividade e saúde
- **Volume Management**: Guia completo de volumes para dados persistentes
- **Commit Workflow**: Documentação detalhada para trabalhar com submodules
