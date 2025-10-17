#!/bin/bash

# Start All - Inicia Docker Stack + MongoDB Watcher

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 Conductor - Start All${NC}"
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
echo -e "${BLUE}2️⃣  Iniciando Docker Stack (dev)...${NC}"
echo -e "${YELLOW}   Isso pode levar alguns minutos...${NC}"
echo ""

docker compose -f docker-compose.dev.yml up -d --build

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
docker compose -f docker-compose.dev.yml ps --format "  ✓ {{.Name}}: {{.Status}}"

echo ""
echo -e "${BLUE}🤖 Watcher:${NC}"
./run-watcher.sh -s | grep -A 2 "Processos ativos" || echo "  ✓ Rodando em background"

echo ""
echo -e "${BLUE}🎯 Acesse:${NC}"
echo "  • Web Interface: http://localhost:8080"
echo "  • Screenplay Editor: http://localhost:8080/screenplay"
echo "  • Gateway API: http://localhost:5006"
echo "  • Conductor API: http://localhost:3000"

echo ""
echo -e "${BLUE}📝 Comandos úteis:${NC}"
echo "  • Ver logs watcher:  ./run-watcher.sh -t"
echo "  • Ver logs docker:   docker compose -f docker-compose.dev.yml logs -f"
echo "  • Parar tudo:        ./run-stop-all-dev.sh"
echo ""

