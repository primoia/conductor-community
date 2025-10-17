# 📜 Guia de Scripts - Conductor Community

## 🚀 Scripts de Inicialização

### `run-start-all-dev.sh` - Inicia TUDO (Docker + Watcher)
```bash
./run-start-all-dev.sh
```

**O que faz:**
1. ✅ Verifica Docker
2. ✅ Sobe stack completa (`docker compose -f docker-compose.dev.yml up -d --build`)
3. ✅ Aguarda serviços iniciarem
4. ✅ Inicia MongoDB Watcher em background
5. ✅ Mostra status completo

**Quando usar:** Início do dia de trabalho

---

### `run-stop-all-dev.sh` - Para TUDO (Docker + Watcher)
```bash
./run-stop-all-dev.sh
```

**O que faz:**
1. ✅ Para MongoDB Watcher
2. ✅ Para Docker Stack

**Quando usar:** Fim do dia ou para reiniciar tudo

---

## 🤖 Script do Watcher

### `run-watcher.sh` - Gerencia MongoDB Watcher

**Configuração automática:**
- Lê credenciais de `config/gateway/config.yaml`
- Converte `host.docker.internal` → `localhost`
- Log: `./logs/watcher.log`

**Comandos:**

```bash
# Testar conexão
./run-watcher.sh --test-connection

# Iniciar em background
./run-watcher.sh -b

# Ver status
./run-watcher.sh -s

# Ver logs (últimas 20 linhas)
./run-watcher.sh -t

# Ver logs em tempo real
tail -f logs/watcher.log

# Parar
./run-watcher.sh -k

# Ajuda
./run-watcher.sh -h
```

**Opções avançadas:**
```bash
# Poll interval customizado
./run-watcher.sh -b -i 2.0

# Collection diferente
./run-watcher.sh -b -c minha_collection

# Foreground (ver output em tempo real)
./run-watcher.sh
```

---

## 🔧 Scripts de Utilidade

### `setup.sh` - Configuração Inicial
```bash
./setup.sh
```

**O que faz:**
- Cria arquivos `.env` a partir dos `.env.example`
- Verifica estrutura de configuração

**Quando usar:** Primeira vez que clonar o projeto

---

### `start-dev.sh` - Só Docker (sem Watcher)
```bash
./start-dev.sh
```

**O que faz:**
- Sobe apenas a stack Docker
- Detecta `docker-compose.dev.local.yml` automaticamente

**Quando usar:** Quando você quer gerenciar o watcher separadamente

---

### `test-stack.sh` - Testa Comunicação
```bash
./test-stack.sh
```

**O que faz:**
- Testa todos os endpoints
- Verifica comunicação entre containers
- Mostra logs resumidos

**Quando usar:** Para debugar problemas de comunicação

---

## 📊 Fluxo de Trabalho Recomendado

### Primeira Vez:
```bash
./setup.sh                    # Criar .env
./run-start-all-dev.sh        # Inicia tudo
```

### Dia a Dia:
```bash
# Manhã
./run-start-all-dev.sh

# Durante o dia
./run-watcher.sh -s           # Ver status
./run-watcher.sh -t           # Ver logs

# Noite
./run-stop-all-dev.sh
```

### Debug:
```bash
# Ver logs do watcher
./run-watcher.sh -t
tail -f logs/watcher.log

# Ver logs do Docker
docker compose -f docker-compose.dev.yml logs -f gateway

# Testar stack
./test-stack.sh
```

### Reiniciar Apenas Watcher:
```bash
./run-watcher.sh -k           # Parar
./run-watcher.sh -b           # Iniciar
```

### Reiniciar Apenas Docker:
```bash
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d --build
```

---

## 🎯 Quick Reference

| Script | Uso | Descrição |
|--------|-----|-----------|
| `setup.sh` | Uma vez | Criar arquivos .env |
| `run-start-all-dev.sh` | Diário | Inicia Docker + Watcher |
| `run-stop-all-dev.sh` | Diário | Para tudo |
| `run-watcher.sh -b` | Manual | Só watcher em background |
| `run-watcher.sh -s` | Verificar | Status do watcher |
| `run-watcher.sh -t` | Debug | Ver logs |
| `run-watcher.sh -k` | Parar | Parar watcher |
| `start-dev.sh` | Manual | Só Docker stack |
| `test-stack.sh` | Debug | Testar comunicação |

---

## 💡 Dicas

1. **Primeira vez**: Sempre rode `./setup.sh` primeiro
2. **Logs**: O watcher grava em `./logs/watcher.log` (gitignored)
3. **Watcher duplicado**: O script mata processos antigos automaticamente
4. **MongoDB**: Usa seu MongoDB externo via `host.docker.internal`
5. **Parar tudo**: `./run-stop-all-dev.sh` é o jeito mais fácil

---

## 🔍 Troubleshooting

### Watcher não inicia
```bash
# Ver se já está rodando
./run-watcher.sh -s

# Matar e reiniciar
./run-watcher.sh -k
./run-watcher.sh -b
```

### Docker não sobe
```bash
# Ver logs
docker compose -f docker-compose.dev.yml logs -f

# Rebuild forçado
docker compose -f docker-compose.dev.yml up -d --build --force-recreate
```

### MongoDB não conecta
```bash
# Testar conexão
./run-watcher.sh --test-connection

# Verificar se MongoDB está rodando na máquina
ps aux | grep mongod
```

