#!/bin/bash

# Stop All - Para Docker Stack (centralized) + MongoDB Watcher

set -e

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}🛑 Conductor Community - Stop All${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# 1. Parar Watcher
echo -e "${BLUE}1️⃣  Parando MongoDB Watcher...${NC}"
./run-watcher.sh -k
echo ""

# 2. Parar Docker Stack
echo -e "${BLUE}2️⃣  Parando Docker Stack (centralized)...${NC}"
docker compose -f docker-compose.centralized.yml down

echo ""
echo -e "${GREEN}✅ Tudo Parado!${NC}"
echo ""
