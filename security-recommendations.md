# 🔐 Plano de Segurança - Conductor Community

## 🚨 Vulnerabilidades Críticas Identificadas

### 1. **Credenciais Hardcoded** - CRÍTICO
**Problema**: Senhas do MongoDB expostas no código
```yaml
# docker-compose.yml - LINHA 8
MONGO_INITDB_ROOT_PASSWORD: conductor123

# settings.py - LINHA 26  
"url": "mongodb://admin:czrimr@mongodb:27017/?authSource=admin"
```

**Solução Imediata**:
```yaml
# docker-compose.yml
environment:
  MONGO_INITDB_ROOT_USERNAME: ${MONGO_USERNAME}
  MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
  MONGO_INITDB_DATABASE: conductor
```

### 2. **CORS Permissivo** - ALTO
**Problema**: `Access-Control-Allow-Origin: *` permite qualquer origem
```nginx
# nginx.conf - LINHA 21
add_header Access-Control-Allow-Origin *;
```

**Solução**:
```nginx
# Configuração segura
add_header Access-Control-Allow-Origin "https://yourdomain.com";
add_header Access-Control-Allow-Credentials "true";
```

### 3. **Falta de Autenticação** - CRÍTICO
**Problema**: APIs expostas sem autenticação
- `/api/agents/{agent_id}/execute`
- `/api/agents`
- `/api/screenplays`

## 🛡️ Implementações de Segurança Recomendadas

### **1. Sistema de Autenticação JWT**

```python
# conductor/conductor-gateway/src/auth/jwt_handler.py
import jwt
from datetime import datetime, timedelta
from typing import Optional
import os

class JWTHandler:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7

    def create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
```

### **2. Middleware de Autenticação**

```python
# conductor/conductor-gateway/src/middleware/auth_middleware.py
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .jwt_handler import JWTHandler

security = HTTPBearer()
jwt_handler = JWTHandler()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = jwt_handler.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

# Aplicar em rotas críticas
@app.post("/api/agents/{agent_id}/execute")
async def execute_agent(
    agent_id: str, 
    payload: dict,
    current_user: dict = Depends(get_current_user)
):
    # ... código existente
```

### **3. Validação e Sanitização Robusta**

```python
# conductor/conductor-gateway/src/validation/input_validator.py
import re
import html
from typing import Any, Dict
import bleach

class InputValidator:
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitiza nome de arquivo removendo caracteres perigosos"""
        # Remove path traversal attempts
        filename = filename.replace("../", "").replace("..\\", "")
        # Remove caracteres perigosos
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Limita tamanho
        return filename[:255]
    
    @staticmethod
    def sanitize_html(content: str) -> str:
        """Sanitiza HTML removendo scripts e tags perigosas"""
        allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
        return bleach.clean(content, tags=allowed_tags, strip=True)
    
    @staticmethod
    def validate_agent_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida entrada para criação de agentes"""
        if not isinstance(data, dict):
            raise ValueError("Dados devem ser um dicionário")
        
        # Validar nome do agente
        name = data.get('name', '')
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            raise ValueError("Nome do agente contém caracteres inválidos")
        
        # Sanitizar descrição
        if 'description' in data:
            data['description'] = InputValidator.sanitize_html(data['description'])
        
        return data
```

### **4. Headers de Segurança**

```nginx
# nginx.conf - Configuração segura
server {
    listen 80;
    server_name localhost;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # CORS Seguro
    location /api/ {
        proxy_pass http://gateway:5006/api/;
        
        # CORS restritivo
        add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
        add_header Access-Control-Allow-Credentials "true" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
        
        # Preflight handling
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "https://yourdomain.com";
            add_header Access-Control-Allow-Credentials "true";
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain; charset=utf-8';
            add_header Content-Length 0;
            return 204;
        }
    }
}
```

### **5. Configuração Segura de Docker**

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  mongodb:
    image: mongo:7.0
    container_name: conductor-mongodb
    restart: unless-stopped
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: conductor
    ports:
      - "127.0.0.1:27017:27017"  # Bind apenas localhost
    volumes:
      - mongodb_data:/data/db
    networks:
      - conductor-network
    # Configurações de segurança
    command: mongod --auth --bind_ip_all
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run

  conductor-api:
    image: primoia/conductor:latest
    container_name: conductor-api
    restart: unless-stopped
    depends_on:
      - mongodb
    env_file:
      - ./config/conductor/.env
    volumes:
      - ./config/conductor/config.yaml:/app/config.yaml:ro
    ports:
      - "127.0.0.1:3000:8000"  # Bind apenas localhost
    networks:
      - conductor-network
    # Configurações de segurança
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    user: "1000:1000"  # Usuário não-root

  gateway:
    image: primoia/conductor-gateway:latest
    container_name: conductor-gateway
    restart: unless-stopped
    depends_on:
      - conductor-api
    env_file:
      - ./config/gateway/.env
    volumes:
      - ./config/gateway/config.yaml:/app/config.yaml:ro
    ports:
      - "127.0.0.1:5006:8080"  # Bind apenas localhost
    networks:
      - conductor-network
    # Configurações de segurança
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    user: "1000:1000"  # Usuário não-root

volumes:
  mongodb_data:
    driver: local

networks:
  conductor-network:
    driver: bridge
    internal: true  # Rede interna
```

### **6. Gerenciamento de Secrets**

```bash
# .env.example
# MongoDB
MONGO_USERNAME=admin
MONGO_PASSWORD=your_secure_password_here
MONGODB_URL=mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/?authSource=admin

# JWT
JWT_SECRET_KEY=your_jwt_secret_key_here_minimum_32_chars
JWT_ALGORITHM=HS256

# API Keys
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Environment
NODE_ENV=production
DEBUG=false
```

### **7. Logging de Segurança**

```python
# conductor/conductor-gateway/src/logging/security_logger.py
import logging
import json
from datetime import datetime
from typing import Dict, Any

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger("security")
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def log_auth_attempt(self, user_id: str, success: bool, ip: str):
        """Log tentativas de autenticação"""
        event = {
            "event_type": "auth_attempt",
            "user_id": user_id,
            "success": success,
            "ip": ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(event))

    def log_security_violation(self, violation_type: str, details: Dict[str, Any]):
        """Log violações de segurança"""
        event = {
            "event_type": "security_violation",
            "violation_type": violation_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.warning(json.dumps(event))

    def log_api_access(self, endpoint: str, user_id: str, method: str, ip: str):
        """Log acesso a APIs"""
        event = {
            "event_type": "api_access",
            "endpoint": endpoint,
            "user_id": user_id,
            "method": method,
            "ip": ip,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.logger.info(json.dumps(event))
```

### **8. Rate Limiting**

```python
# conductor/conductor-gateway/src/middleware/rate_limiter.py
from fastapi import HTTPException, Request
import time
from collections import defaultdict, deque

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(deque)
        self.max_requests = 100  # requests per minute
        self.window = 60  # seconds

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove requests outside the window
        while client_requests and client_requests[0] <= now - self.window:
            client_requests.popleft()
        
        # Check if under limit
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Try again later."
        )
    
    response = await call_next(request)
    return response
```

## 🔍 Checklist de Implementação

### **Prioridade CRÍTICA (Implementar Imediatamente)**
- [ ] Remover credenciais hardcoded
- [ ] Implementar autenticação JWT
- [ ] Configurar CORS restritivo
- [ ] Adicionar headers de segurança
- [ ] Implementar validação de entrada robusta

### **Prioridade ALTA (Próximas 2 semanas)**
- [ ] Configurar logging de segurança
- [ ] Implementar rate limiting
- [ ] Configurar containers seguros
- [ ] Implementar monitoramento de segurança
- [ ] Configurar backup seguro

### **Prioridade MÉDIA (Próximo mês)**
- [ ] Implementar MFA (Multi-Factor Authentication)
- [ ] Configurar WAF (Web Application Firewall)
- [ ] Implementar auditoria completa
- [ ] Configurar alertas de segurança
- [ ] Documentar políticas de segurança

## 🚀 Próximos Passos

1. **Imediato**: Criar arquivo `.env` com secrets seguros
2. **Hoje**: Implementar autenticação JWT básica
3. **Esta semana**: Configurar headers de segurança e CORS
4. **Próximas 2 semanas**: Implementar validação robusta e logging
5. **Próximo mês**: Auditoria completa e compliance

## 📚 Recursos Adicionais

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [Nginx Security Headers](https://securityheaders.com/)