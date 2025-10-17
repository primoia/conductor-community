#!/bin/bash

# Script para iniciar a stack Conductor em modo desenvolvimento

echo "================================================"
echo "🚀 Iniciando Conductor Stack (Desenvolvimento)"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Verificar se o docker está rodando
echo -n "Verificando Docker... "
if ! docker info &>/dev/null; then
    echo -e "${RED}✗ Docker não está rodando${NC}"
    echo "Por favor, inicie o Docker e tente novamente."
    exit 1
fi
echo -e "${GREEN}✓ OK${NC}"

# 2. Parar containers anteriores
echo ""
echo "Parando containers anteriores..."
docker-compose -f docker-compose.dev.yml down 2>/dev/null

# 3. Build e start
echo ""
echo "Construindo e iniciando serviços..."
echo -e "${YELLOW}Isso pode levar alguns minutos na primeira vez...${NC}"
echo ""

# Se existe docker-compose.dev.local.yml, usa ele (configurações locais)
if [ -f "docker-compose.dev.local.yml" ]; then
    echo "✓ Usando docker-compose.dev.local.yml (configurações locais)"
    docker compose -f docker-compose.dev.yml -f docker-compose.dev.local.yml up --build -d
elif [ -f "docker-compose.override.yml" ]; then
    echo "✓ Usando docker-compose.override.yml (configurações locais)"
    docker compose -f docker-compose.dev.yml -f docker-compose.override.yml up --build -d
else
    docker compose -f docker-compose.dev.yml up --build -d
fi

# 4. Aguardar serviços
echo ""
echo "Aguardando serviços iniciarem..."
sleep 10

# 5. Mostrar status
echo ""
echo "================================================"
echo "✅ Stack Iniciada!"
echo "================================================"
echo ""

docker-compose -f docker-compose.dev.yml ps

echo ""
echo "📍 URLs disponíveis:"
echo "   • Web Interface: http://localhost:8080"
echo "   • Gateway API:   http://localhost:5006"
echo "   • Conductor API: http://localhost:3000"
echo "   • MongoDB:       localhost:27017"
echo ""
echo "📝 Comandos úteis:"
echo "   • Ver logs:      docker-compose -f docker-compose.dev.yml logs -f"
echo "   • Parar:         docker-compose -f docker-compose.dev.yml down"
echo "   • Rebuild:       docker-compose -f docker-compose.dev.yml up --build"
echo "   • Testar stack:  ./test-stack.sh"
echo ""
echo "🔍 Para testar a comunicação, execute:"
echo "   ./test-stack.sh"
echo ""

