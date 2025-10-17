# Conductor Community

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Community](https://img.shields.io/badge/Community-Welcome-orange.svg)](CONTRIBUTING.md)

> **Repositório público e autocontido** que permite rodar a stack completa do Conductor da maneira mais simples possível.

## 🚀 Início Rápido

### Para Usuários Finais (Uso Simples)

Se você só quer **usar** o Conductor sem mexer no código:

```bash
# 1. Clone o repositório
git clone https://github.com/primoia/conductor-community.git
cd conductor-community

# 2. Configure os arquivos de ambiente
./setup.sh

# 3. (IMPORTANTE) Edite as credenciais para produção
nano config/conductor/.env
nano config/gateway/.env

# 4. Suba a stack completa
docker-compose up -d

# 5. Acesse a aplicação
# Web UI: http://localhost:8080
# Gateway API: http://localhost:5006
# Conductor API: http://localhost:3000
```

**Pronto!** 🎉 A aplicação estará rodando com imagens pré-construídas do Docker Hub.

### Para Desenvolvedores (Contribuição)

Se você quer **contribuir** ou modificar o código:

```bash
# 1. Clone o repositório COM os submódulos
git clone --recurse-submodules https://github.com/primoia/conductor-community.git
cd conductor-community

# 2. Configure os arquivos de ambiente
./setup.sh

# 3. Inicie TUDO (Docker + Watcher)
./run-start-all-dev.sh

# 4. Acesse a aplicação
# Web UI: http://localhost:8080
# Gateway API: http://localhost:5006
# Conductor API: http://localhost:3000

# 5. Quando terminar
./run-stop-all-dev.sh
```

**Agora você tem:** 🔧
- Código-fonte mapeado para desenvolvimento
- Live-reload habilitado
- Capacidade de fazer commits e PRs nos submódulos

## 📁 Estrutura do Projeto

```
conductor-community/
├── docker-compose.yml         # Para usuários finais (imagens prontas)
├── docker-compose.dev.yml     # Para desenvolvedores (build local)
├── README.md                  # Esta documentação
├── CONTRIBUTING.md            # Guia para contribuidores
│
├── config/                    # Arquivos de configuração
│   ├── conductor/
│   │   └── config.yaml.example
│   └── gateway/
│       └── gateway.env.example
│
└── src/                       # Código-fonte via submódulos Git
    ├── conductor/             # Submódulo: primoia/conductor
    ├── conductor-gateway/     # Submódulo: primoia/conductor-gateway
    └── conductor-web/         # Submódulo: primoia/conductor-web
```

## 🛠️ Serviços Incluídos

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| **MongoDB** | 27017 | Banco de dados principal |
| **Conductor API** | 3000 | API principal do Conductor (porta interna: 8000) |
| **Gateway** | 5006 | Gateway FastAPI (porta interna: 8080) |
| **Web UI** | 8080 | Interface web do Conductor (Nginx + Angular + React) |

## ⚙️ Configuração

### 🔐 Segurança - Arquivos .env

Os arquivos `.env` **NÃO** devem ser commitados no repositório (estão no `.gitignore`).

**Estrutura:**
```
config/
├── conductor/
│   ├── .env.example          # Template
│   └── .env                  # Suas credenciais (gitignored)
└── gateway/
    ├── .env.example          # Template  
    └── .env                  # Suas credenciais (gitignored)
```

**Para criar seus .env:**
```bash
./setup.sh
```

⚠️ **IMPORTANTE**: Para produção, altere as senhas padrão nos arquivos `.env`!

### Conductor API (`config/conductor/config.yaml`)

Principais configurações:

```yaml
server:
  port: 3000

database:
  mongodb:
    uri: "mongodb://admin:conductor123@mongodb:27017/conductor?authSource=admin"

conductor:
  workflows:
    maxConcurrentWorkflows: 100
  tasks:
    defaultTimeout: 300
    maxRetryCount: 3
```

### Gateway (`config/gateway/gateway.env`)

Principais configurações:

```env
PORT=8080
CONDUCTOR_API_URL=http://conductor-api:3000
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
CORS_ORIGIN=*
```

## 🐳 Comandos Docker Úteis

### Gerenciamento da Stack

```bash
# Subir a stack
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar a stack
docker-compose down

# Reiniciar um serviço específico
docker-compose restart conductor-api

# Ver status dos containers
docker-compose ps
```

### Para Desenvolvedores

```bash
# Subir em modo de desenvolvimento
docker-compose -f docker-compose.dev.yml up --build -d

# Ver logs de desenvolvimento
docker-compose -f docker-compose.dev.yml logs -f

# Rebuildar apenas um serviço
docker-compose -f docker-compose.dev.yml up --build conductor-api
```

## 🔧 Desenvolvimento

### Trabalhando com Submódulos

```bash
# Atualizar todos os submódulos
git submodule update --remote

# Atualizar um submódulo específico
git submodule update --remote src/conductor

# Fazer commit em um submódulo
cd src/conductor
git add .
git commit -m "feat: nova funcionalidade"
git push origin main
cd ../..
git add src/conductor
git commit -m "chore: atualiza submódulo conductor"
```

### Estrutura de Desenvolvimento

- **`src/conductor/`**: API principal do Conductor
- **`src/conductor-gateway/`**: Gateway de API
- **`src/conductor-web/`**: Interface web Angular

Cada submódulo é um repositório Git independente que pode ser clonado e desenvolvido separadamente.

## 📚 Documentação Adicional

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Guia para contribuidores e configuração de submódulos
- **[SUBMODULES.md](SUBMODULES.md)** - Referência detalhada sobre submódulos Git
- **[QUICK_COMMANDS.md](QUICK_COMMANDS.md)** - Comandos rápidos e aliases úteis
- **[VOLUMES_GUIDE.md](VOLUMES_GUIDE.md)** - Guia de volumes e dados persistentes

## 🚨 Solução de Problemas

### Problemas Comuns

**1. Erro de conexão com MongoDB**
```bash
# Verificar se o MongoDB está rodando
docker-compose logs mongodb

# Reiniciar o MongoDB
docker-compose restart mongodb
```

**2. Erro de configuração**
```bash
# Verificar se os arquivos de configuração existem
ls -la config/conductor/config.yaml
ls -la config/gateway/gateway.env

# Se não existirem, copie os exemplos
cp config/conductor/config.yaml.example config/conductor/config.yaml
cp config/gateway/gateway.env.example config/gateway/gateway.env
```

**3. Porta já em uso**
```bash
# Verificar qual processo está usando a porta
sudo lsof -i :8080
sudo lsof -i :5006
sudo lsof -i :3000

# Parar o processo ou mudar a porta no docker-compose.yml
```

**4. Web não conecta ao Gateway**
```bash
# Use o script de teste para diagnóstico
./test-stack.sh

# Ver logs do nginx e gateway
docker logs conductor-web-dev
docker logs conductor-gateway-dev

# Testar proxy manualmente
curl http://localhost:8080/api/
curl http://localhost:5006
```

### Logs Detalhados

```bash
# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f conductor-api
docker-compose logs -f gateway
docker-compose logs -f web
```

## 🤝 Contribuindo

Quer contribuir? Veja nosso [Guia de Contribuição](CONTRIBUTING.md)!

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](LICENSE).

## 🆘 Suporte

- **Issues**: [GitHub Issues](https://github.com/primoia/conductor-community/issues)
- **Discussões**: [GitHub Discussions](https://github.com/primoia/conductor-community/discussions)
- **Documentação**: [Wiki](https://github.com/primoia/conductor-community/wiki)

---

**Feito com ❤️ pela comunidade Primoia**