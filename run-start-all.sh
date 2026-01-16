#!/bin/bash

# Start All - Inicia Docker Stack (centralized) + MongoDB Watcher

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
NO_CACHE=""
FORCE_RECREATE=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --fresh|--no-cache)
            NO_CACHE="--no-cache"
            FORCE_RECREATE="--force-recreate"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --fresh, --no-cache  Rebuild all images without Docker cache"
            echo "  --help, -h           Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Conductor Community - Start All${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# 1. Verificar Docker
echo -e "${BLUE}1️⃣  Verificando Docker...${NC}"
if ! docker info &>/dev/null; then
    echo -e "${RED}❌ Docker não está rodando${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker OK${NC}"
echo ""

# 2. Subir Docker Stack
echo -e "${BLUE}2️⃣  Iniciando Docker Stack (centralized)...${NC}"
if [[ -n "$NO_CACHE" ]]; then
    echo -e "${YELLOW}   🔄 Modo --fresh: Rebuild completo SEM cache...${NC}"
else
    echo -e "${YELLOW}   Isso pode levar alguns minutos...${NC}"
fi
echo ""

# Build com ou sem cache
if [[ -n "$NO_CACHE" ]]; then
    docker compose -f docker-compose.centralized.yml build $NO_CACHE
fi
docker compose -f docker-compose.centralized.yml up -d --build $FORCE_RECREATE

echo ""
echo -e "${GREEN}✓ Docker Stack iniciada${NC}"
echo ""

# 3. Aguardar serviços iniciarem
echo -e "${BLUE}3️⃣  Aguardando serviços iniciarem...${NC}"
sleep 8
echo -e "${GREEN}✓ Serviços prontos${NC}"
echo ""

# 4. Iniciar Watcher
echo -e "${BLUE}4️⃣  Iniciando MongoDB Watcher...${NC}"
./run-watcher.sh -b

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Tudo Iniciado!${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# 5. Mostrar status
echo -e "${BLUE}📦 Containers:${NC}"
docker compose -f docker-compose.centralized.yml ps --format "  ✓ {{.Name}}: {{.Status}}"

echo ""
echo -e "${BLUE}🤖 Watcher:${NC}"
./run-watcher.sh -s | grep -A 2 "Processos ativos" || echo "  ✓ Rodando em background"

echo ""
echo -e "${BLUE}🎯 Acesse:${NC}"
echo "  • Web Interface: http://localhost:11299"
echo "  • MCP Sidecar:   http://localhost:13199  (conductor-mcp)"
echo "  • Gateway BFF:   http://localhost:14199  (conductor-bff)"
echo "  • Conductor API: http://localhost:12199"

echo ""
echo -e "${BLUE}📝 Comandos úteis:${NC}"
echo "  • Ver logs watcher:  ./run-watcher.sh -t"
echo "  • Ver logs docker:   docker compose -f docker-compose.centralized.yml logs -f"
echo "  • Parar tudo:        ./run-stop-all.sh"
echo "  • Rebuild sem cache: ./run-start-all.sh --fresh"
echo ""
