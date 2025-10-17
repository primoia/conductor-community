#!/bin/bash

# Script para testar a stack Conductor

echo "================================================"
echo "🧪 Testando a Stack Conductor"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para testar endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testando $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    
    if [ "$response" == "$expected" ] || [ "$response" == "200" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FALHOU${NC} (HTTP $response)"
        return 1
    fi
}

# Função para verificar se container está rodando
check_container() {
    local name=$1
    echo -n "Verificando container $name... "
    
    if docker ps | grep -q "$name"; then
        echo -e "${GREEN}✓ Rodando${NC}"
        return 0
    else
        echo -e "${RED}✗ Não encontrado${NC}"
        return 1
    fi
}

# 1. Verificar se os containers estão rodando
echo "1️⃣  Verificando Containers"
echo "----------------------------"
check_container "mongodb"
check_container "conductor-api"
check_container "conductor-gateway"
check_container "conductor-web"
echo ""

# 2. Aguardar serviços iniciarem
echo "2️⃣  Aguardando serviços iniciarem..."
echo "----------------------------"
sleep 5
echo -e "${GREEN}✓ Pronto${NC}"
echo ""

# 3. Testar endpoints
echo "3️⃣  Testando Endpoints"
echo "----------------------------"

# MongoDB (via telnet/nc se disponível)
echo -n "MongoDB (27017)... "
if nc -z localhost 27017 2>/dev/null; then
    echo -e "${GREEN}✓ Acessível${NC}"
else
    echo -e "${RED}✗ Não acessível${NC}"
fi

# Conductor API
test_endpoint "Conductor API (3000)" "http://localhost:3000" "200"

# Gateway (direto)
test_endpoint "Gateway (5006)" "http://localhost:5006" "200"

# Web (Nginx)
test_endpoint "Web Interface (8080)" "http://localhost:8080" "200"

# Gateway via Nginx (comunicação web→gateway)
test_endpoint "Gateway via Nginx" "http://localhost:8080/api/" "200"

echo ""

# 4. Testar comunicação interna
echo "4️⃣  Testando Comunicação Interna"
echo "----------------------------"

echo -n "Web → Gateway... "
if docker exec conductor-web ping -c 1 gateway &>/dev/null 2>&1 || \
   docker exec conductor-web-dev ping -c 1 gateway &>/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Ping não disponível (pode ser normal)${NC}"
fi

echo -n "Gateway → API... "
if docker exec conductor-gateway ping -c 1 conductor-api &>/dev/null 2>&1 || \
   docker exec conductor-gateway-dev ping -c 1 conductor-api &>/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Ping não disponível (pode ser normal)${NC}"
fi

echo -n "API → MongoDB... "
if docker exec conductor-api ping -c 1 mongodb &>/dev/null 2>&1 || \
   docker exec conductor-api-dev ping -c 1 mongodb &>/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Ping não disponível (pode ser normal)${NC}"
fi

echo ""

# 5. Verificar logs recentes
echo "5️⃣  Últimas Linhas dos Logs"
echo "----------------------------"

echo -e "${YELLOW}Gateway:${NC}"
docker logs conductor-gateway --tail 3 2>/dev/null || docker logs conductor-gateway-dev --tail 3 2>/dev/null
echo ""

echo -e "${YELLOW}Conductor API:${NC}"
docker logs conductor-api --tail 3 2>/dev/null || docker logs conductor-api-dev --tail 3 2>/dev/null
echo ""

# 6. Resumo
echo "================================================"
echo "📊 Resumo"
echo "================================================"
echo ""
echo "✅ URLs para testar:"
echo "   • Web Interface: http://localhost:8080"
echo "   • Gateway (direto): http://localhost:5006"
echo "   • Conductor API: http://localhost:3000"
echo ""
echo "📝 Para ver logs completos:"
echo "   docker logs conductor-web-dev"
echo "   docker logs conductor-gateway-dev"
echo "   docker logs conductor-api-dev"
echo ""
echo "🛠️  Para debugar:"
echo "   docker exec -it conductor-web-dev /bin/sh"
echo "   docker exec -it conductor-gateway-dev /bin/sh"
echo "   docker exec -it conductor-api-dev /bin/sh"
echo ""

