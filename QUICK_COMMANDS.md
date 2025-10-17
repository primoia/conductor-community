# 🚀 Comandos Rápidos - Conductor Community

## 📋 Comandos Essenciais

### Produção (imagens Docker Hub)
```bash
# Iniciar
docker compose up -d

# Com override local (se você tem docker-compose.override.yml)
# O override é aplicado AUTOMATICAMENTE

# Parar
docker compose down

# Ver logs
docker compose logs -f

# Reiniciar serviço específico
docker compose restart gateway
```

### Desenvolvimento (build local)

#### Com override de volumes (seu banco local):
```bash
# Iniciar (aplica override automaticamente)
docker compose -f docker-compose.dev.yml -f docker-compose.override.yml up -d --build

# OU use o script (detecta override automaticamente):
./start-dev.sh

# Parar
docker compose -f docker-compose.dev.yml down

# Ver logs
docker compose -f docker-compose.dev.yml logs -f gateway

# Rebuild só um serviço
docker compose -f docker-compose.dev.yml up --build -d gateway
```

#### Sem override (volume padrão do Docker):
```bash
# Iniciar
docker compose -f docker-compose.dev.yml up -d --build

# Parar
docker compose -f docker-compose.dev.yml down
```

## 🔍 Verificar Configuração

```bash
# Ver configuração final (com overrides aplicados)
docker compose config | grep -A 5 "mongodb:"

# Dev com override
docker compose -f docker-compose.dev.yml -f docker-compose.override.yml config | grep -A 5 "mongodb:"

# Ver se override existe
ls -la docker-compose.override.yml

# Ver volumes ativos
docker volume ls
```

## 📦 Gestão de Volumes

```bash
# Ver volumes
docker volume ls

# Inspecionar volume específico
docker volume inspect conductor-community_mongodb_data

# Remover volumes (CUIDADO: apaga dados!)
docker compose down -v

# Backup do volume
docker run --rm \
  -v conductor-community_mongodb_data:/data \
  -v $(pwd):/backup \
  busybox tar czf /backup/mongodb-backup.tar.gz /data
```

## 🧪 Testes

```bash
# Testar stack completa
./test-stack.sh

# Testar endpoints manualmente
curl http://localhost:8080                # Web
curl http://localhost:5006/docs          # Gateway (Swagger)
curl http://localhost:3000               # Conductor API
curl http://localhost:8080/api/screenplays  # Via proxy
```

## 🔧 Debug

```bash
# Ver logs de um serviço específico
docker compose logs -f gateway

# Dev
docker compose -f docker-compose.dev.yml logs -f gateway

# Entrar em um container
docker exec -it conductor-gateway-dev /bin/sh

# Ver portas
docker compose ps

# Ver uso de recursos
docker stats
```

## 🗑️ Limpeza

```bash
# Parar e remover containers
docker compose down

# Remover também os volumes (APAGA DADOS!)
docker compose down -v

# Remover imagens não usadas
docker image prune -a

# Limpeza completa (CUIDADO!)
docker system prune -a --volumes
```

## 📝 Fluxo de Trabalho Comum

### Primeira vez:
```bash
./setup.sh                    # Criar .env
./start-dev.sh                # Iniciar dev
./test-stack.sh               # Testar
```

### Dia a dia (com seu banco local):
```bash
# Se mudou código
docker compose -f docker-compose.dev.yml -f docker-compose.override.yml up -d --build

# Se só reiniciar
docker compose -f docker-compose.dev.yml up -d

# Ou simplesmente:
./start-dev.sh
```

### Desenvolvimento:
```bash
# Editar código...
# Rebuild só o que mudou:
docker compose -f docker-compose.dev.yml up --build -d web

# Ver logs:
docker compose -f docker-compose.dev.yml logs -f web
```

## 🎯 Aliases Úteis (adicione ao seu ~/.bashrc ou ~/.zshrc)

```bash
# Aliases para Conductor
alias dc='docker compose'
alias dcd='docker compose -f docker-compose.dev.yml'
alias dcdo='docker compose -f docker-compose.dev.yml -f docker-compose.override.yml'
alias dcl='docker compose logs -f'
alias dcdl='docker compose -f docker-compose.dev.yml logs -f'
alias dcp='docker compose ps'
alias dcdown='docker compose down'

# Uso:
# dcdo up -d --build    # Dev com override
# dcdl gateway          # Ver logs do gateway
# dcp                   # Ver status
```

## 💡 Dicas

1. **Use o script**: `./start-dev.sh` detecta o override automaticamente
2. **Override em dev**: Sempre use `-f docker-compose.dev.yml -f docker-compose.override.yml`
3. **Logs**: Use `-f` para follow (Ctrl+C para sair)
4. **Rebuild seletivo**: Só rebuilde o serviço que mudou
5. **Volumes**: Cuidado com `down -v` (apaga dados!)

