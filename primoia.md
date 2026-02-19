# Conductor Community

Repositorio publico que integra os 3 componentes do Conductor (core, gateway, web) via Git submodules e orquestra o deployment completo com Docker Compose.

## Responsabilidades
- Orquestrar deployment do stack Conductor com um unico comando
- Gerenciar submodules (conductor, conductor-gateway, conductor-web)
- Prover modo desenvolvimento com live-reload e modo producao com imagens pre-buildadas
- Configurar ambiente via scripts de setup e templates .env

## Stack
- Docker Compose (orquestracao)
- Git Submodules
- MongoDB

## Portas
- API: 12199 | MCP: 13199

## Arquivos-chave
- `conductor/conductor/src/server.py`, `conductor/conductor/src/api/routes/`, `conductor/conductor/projects/desafio-meli/app/models/`, `docker-compose.centralized.yml`

## Integra com
- Infra padrão: IAM
