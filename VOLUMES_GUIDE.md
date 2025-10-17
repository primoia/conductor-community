# 📦 Guia de Volumes e Dados Persistentes

## 🎯 Configuração Padrão

Por padrão, o projeto usa **named volumes** do Docker:

```yaml
# docker-compose.yml
volumes:
  mongodb_data:      # Produção
  mongodb_data_dev:  # Desenvolvimento
```

Estes volumes são gerenciados automaticamente pelo Docker em:
- Linux: `/var/lib/docker/volumes/`
- Mac: `~/Library/Containers/com.docker.docker/Data/vms/0/`
- Windows: `C:\ProgramData\Docker\volumes\`

## 🔧 Usando um Path Local Específico

Se você quer usar um diretório específico (ex: dados já existentes), use o arquivo `docker-compose.override.yml`:

### 1. Copie o exemplo:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

### 2. Edite com seu path:
```yaml
version: '3.8'

services:
  mongodb:
    volumes:
      - /home/SEU_USUARIO/Workspace/mongo/data:/data/db
```

### 3. Suba normalmente:
```bash
docker compose up -d
```

O Docker Compose **automaticamente** aplica o override! ✨

## 📝 Importantes:

### ✅ O que VAI para o Git:
- `docker-compose.yml` - configuração base
- `docker-compose.dev.yml` - configuração de dev
- `docker-compose.override.yml.example` - exemplo de override

### ❌ O que NÃO VAI para o Git:
- `docker-compose.override.yml` - sua configuração local (no `.gitignore`)

## 🔍 Verificando qual volume está sendo usado:

```bash
# Ver configuração final (com override aplicado)
docker compose config | grep -A 5 "mongodb:"

# Ver volumes ativos
docker volume ls

# Inspecionar volume
docker volume inspect conductor-community_mongodb_data
```

## 🗑️ Limpando volumes:

```bash
# Parar containers
docker compose down

# Remover volumes (CUIDADO: apaga os dados!)
docker compose down -v

# Remover volume específico
docker volume rm conductor-community_mongodb_data
```

## 🚀 Casos de Uso:

### Usuário Normal (Desenvolvedor):
```bash
# Usa named volume automático
docker compose up -d
# Volume criado em: /var/lib/docker/volumes/conductor-community_mongodb_data
```

### Usuário com Dados Existentes:
```bash
# 1. Cria override
cp docker-compose.override.yml.example docker-compose.override.yml

# 2. Edita path
nano docker-compose.override.yml

# 3. Sobe normalmente
docker compose up -d
# Usa: /seu/path/específico
```

### CI/CD:
```bash
# Usa configuração padrão (sem override)
docker compose up -d
```

## 🔐 Backup e Restore:

### Backup (Named Volume):
```bash
# Criar backup
docker run --rm \
  -v conductor-community_mongodb_data:/data \
  -v $(pwd):/backup \
  busybox tar czf /backup/mongodb-backup.tar.gz /data
```

### Restore:
```bash
# Restaurar backup
docker run --rm \
  -v conductor-community_mongodb_data:/data \
  -v $(pwd):/backup \
  busybox tar xzf /backup/mongodb-backup.tar.gz -C /
```

## 💡 Dicas:

1. **Desenvolvimento Local**: Use named volumes (mais rápido, menos problemas de permissão)
2. **Dados Existentes**: Use docker-compose.override.yml
3. **Produção**: Considere usar volumes externos ou backups regulares
4. **Colaboração**: Nunca commite docker-compose.override.yml (está no .gitignore)

## 🆘 Troubleshooting:

### Problema: Permissões no volume local
```bash
# Dar permissão para o MongoDB (UID 999)
sudo chown -R 999:999 /seu/path/mongo/data
```

### Problema: Volume não atualiza
```bash
# Forçar recreação dos containers
docker compose up -d --force-recreate
```

### Problema: Ver qual configuração está ativa
```bash
# Ver configuração final mesclada
docker compose config
```

