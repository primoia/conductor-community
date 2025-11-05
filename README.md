# Conductor Community

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Community](https://img.shields.io/badge/Community-Welcome-orange.svg)](CONTRIBUTING.md)

> **Self-contained public repository** that allows you to run the complete Conductor stack in the simplest way possible.

## 🚀 Quick Start

### For End Users (Simple Usage)

If you just want to **use** Conductor without touching the code:

```bash
# 1. Clone the repository
git clone https://github.com/primoia/conductor-community.git
cd conductor-community

# 2. Configure environment files
./setup.sh

# 3. (IMPORTANT) Edit credentials for production
nano config/conductor/.env
nano config/gateway/.env

# 4. Start the complete stack
docker-compose up -d

# 5. Access the application
# Web UI: http://localhost:8080
# Gateway API: http://localhost:5006
# Conductor API: http://localhost:3000
```

**Done!** 🎉 The application will be running with pre-built images from Docker Hub.

### For Developers (Contributing)

If you want to **contribute** or modify the code:

```bash
# 1. Clone the repository WITH submodules
git clone --recurse-submodules https://github.com/primoia/conductor-community.git
cd conductor-community

# 2. Configure environment files
./setup.sh

# 3. Start EVERYTHING (Docker + Watcher)
./run-start-all-dev.sh

# 4. Access the application
# Web UI: http://localhost:8080
# Gateway API: http://localhost:5006
# Conductor API: http://localhost:3000

# 5. When finished
./run-stop-all-dev.sh
```

**Now you have:** 🔧
- Source code mapped for development
- Live-reload enabled
- Ability to make commits and PRs in submodules

## 📁 Project Structure

```
conductor-community/
├── docker-compose.yml         # For end users (ready-made images)
├── docker-compose.dev.yml     # For developers (local build)
├── README.md                  # This documentation
├── CONTRIBUTING.md            # Contributor guide
│
├── config/                    # Configuration files
│   ├── conductor/
│   │   └── config.yaml.example
│   └── gateway/
│       └── gateway.env.example
│
└── conductor/                 # Source code via Git submodules
    ├── conductor/             # Submodule: primoia/conductor
    ├── conductor-gateway/     # Submodule: primoia/conductor-gateway
    └── conductor-web/         # Submodule: primoia/conductor-web
```

## 🛠️ Included Services

| Service | Port | Description |
|---------|------|-------------|
| **MongoDB** | 27017 | Main database |
| **Conductor API** | 3000 | Main Conductor API (internal port: 8000) |
| **Gateway** | 5006 | FastAPI Gateway (internal port: 8080) |
| **Web UI** | 8080 | Conductor web interface (Nginx + Angular + React) |

## ⚙️ Configuration

### 🔐 Security - .env Files

The `.env` files should **NOT** be committed to the repository (they're in `.gitignore`).

**Structure:**
```
config/
├── conductor/
│   ├── .env.example          # Template
│   └── .env                  # Your credentials (gitignored)
└── gateway/
    ├── .env.example          # Template  
    └── .env                  # Your credentials (gitignored)
```

**To create your .env files:**
```bash
./setup.sh
```

⚠️ **IMPORTANT**: For production, change the default passwords in the `.env` files!

### Conductor API (`config/conductor/config.yaml`)

Main configurations:

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

Main configurations:

```env
PORT=8080
CONDUCTOR_API_URL=http://conductor-api:3000
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
CORS_ORIGIN=*
```

## 🐳 Useful Docker Commands

### Stack Management

```bash
# Start the stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the stack
docker-compose down

# Restart a specific service
docker-compose restart conductor-api

# View container status
docker-compose ps
```

### For Developers

```bash
# Start in development mode
docker-compose -f docker-compose.dev.yml up --build -d

# View development logs
docker-compose -f docker-compose.dev.yml logs -f

# Rebuild only one service
docker-compose -f docker-compose.dev.yml up --build conductor-api
```

## 🔧 Development

### Working with Submodules

```bash
# Update all submodules
git submodule update --remote

# Update a specific submodule
git submodule update --remote conductor/conductor

# Commit in a submodule
cd conductor/conductor
git add .
git commit -m "feat: new feature"
git push origin main
cd ../..
git add conductor/conductor
git commit -m "chore: update conductor submodule"
```

### Development Structure

- **`conductor/conductor/`**: Main Conductor API
- **`conductor/conductor-gateway/`**: API Gateway
- **`conductor/conductor-web/`**: Angular web interface

Each submodule is an independent Git repository that can be cloned and developed separately.

## 📚 Additional Documentation

- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contributor guide and submodule configuration
- **[SUBMODULES.md](SUBMODULES.md)** - Detailed reference on Git submodules
- **[docs/COMMIT_WORKFLOW.md](docs/COMMIT_WORKFLOW.md)** - Commit workflow with submodules
- **[QUICK_COMMANDS.md](QUICK_COMMANDS.md)** - Quick commands and useful aliases
- **[VOLUMES_GUIDE.md](VOLUMES_GUIDE.md)** - Guide to volumes and persistent data

## 🚨 Troubleshooting

### Common Issues

**1. MongoDB connection error**
```bash
# Check if MongoDB is running
docker-compose logs mongodb

# Restart MongoDB
docker-compose restart mongodb
```

**2. Configuration error**
```bash
# Check if configuration files exist
ls -la config/conductor/config.yaml
ls -la config/gateway/gateway.env

# If they don't exist, copy the examples
cp config/conductor/config.yaml.example config/conductor/config.yaml
cp config/gateway/gateway.env.example config/gateway/gateway.env
```

**3. Port already in use**
```bash
# Check which process is using the port
sudo lsof -i :8080
sudo lsof -i :5006
sudo lsof -i :3000

# Stop the process or change the port in docker-compose.yml
```

**4. Web doesn't connect to Gateway**
```bash
# Use the test script for diagnostics
./test-stack.sh

# View nginx and gateway logs
docker logs conductor-web-dev
docker logs conductor-gateway-dev

# Test proxy manually
curl http://localhost:8080/api/
curl http://localhost:5006
```

### Detailed Logs

```bash
# View logs from all services
docker-compose logs -f

# View logs from a specific service
docker-compose logs -f conductor-api
docker-compose logs -f gateway
docker-compose logs -f web
```

## 🤝 Contributing

Want to contribute? Check out our [Contributing Guide](CONTRIBUTING.md)!

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/primoia/conductor-community/issues)
- **Discussions**: [GitHub Discussions](https://github.com/primoia/conductor-community/discussions)
- **Documentation**: [Wiki](https://github.com/primoia/conductor-community/wiki)

---

**Made with ❤️ by the Primoia community**
