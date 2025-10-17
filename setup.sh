#!/bin/bash

# Setup script for Conductor Community

echo "================================================"
echo "🚀 Conductor Community - Setup"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env files exist
echo "📋 Verificando arquivos .env..."

if [ ! -f "config/conductor/.env" ]; then
    echo -e "${YELLOW}⚠  config/conductor/.env não encontrado${NC}"
    echo "   Copiando de .env.example..."
    cp config/conductor/.env.example config/conductor/.env
    echo -e "${GREEN}✓  Criado config/conductor/.env${NC}"
else
    echo -e "${GREEN}✓  config/conductor/.env já existe${NC}"
fi

if [ ! -f "config/gateway/.env" ]; then
    echo -e "${YELLOW}⚠  config/gateway/.env não encontrado${NC}"
    echo "   Copiando de .env.example..."
    cp config/gateway/.env.example config/gateway/.env
    echo -e "${GREEN}✓  Criado config/gateway/.env${NC}"
else
    echo -e "${GREEN}✓  config/gateway/.env já existe${NC}"
fi

echo ""
echo "================================================"
echo "⚠️  IMPORTANTE: Segurança"
echo "================================================"
echo ""
echo "Os arquivos .env contém credenciais padrão."
echo "Para produção, você DEVE alterar:"
echo ""
echo "  1. Senhas do MongoDB"
echo "  2. Chaves de API (se aplicável)"
echo "  3. Outras credenciais sensíveis"
echo ""
echo "📝 Edite os arquivos:"
echo "  - config/conductor/.env"
echo "  - config/gateway/.env"
echo ""

echo "================================================"
echo "✅ Setup concluído!"
echo "================================================"
echo ""
echo "Para iniciar:"
echo "  • Produção:      docker-compose up -d"
echo "  • Desenvolvimento: ./start-dev.sh"
echo ""
