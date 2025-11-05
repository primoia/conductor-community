# Configuração de Submódulos

Este documento explica como configurar os submódulos Git para desenvolvimento.

## Adicionando Submódulos

Para adicionar os submódulos ao repositório `conductor-community`, execute os seguintes comandos:

```bash
# Adicionar o submódulo do Conductor API
git submodule add https://github.com/primoia/conductor.git conductor/conductor

# Adicionar o submódulo do Gateway
git submodule add https://github.com/primoia/conductor-gateway.git conductor/conductor-gateway

# Adicionar o submódulo da Web UI
git submodule add https://github.com/primoia/conductor-web.git conductor/conductor-web

# Fazer commit das mudanças
git add .gitmodules conductor/
git commit -m "chore: adiciona submódulos para desenvolvimento"
```

## Clonando com Submódulos

Para clonar o repositório com todos os submódulos:

```bash
git clone --recurse-submodules https://github.com/primoia/conductor-community.git
cd conductor-community
```

Se você já clonou sem submódulos, pode adicioná-los depois:

```bash
git submodule init
git submodule update
```

## Atualizando Submódulos

Para atualizar todos os submódulos para a versão mais recente:

```bash
git submodule update --remote
```

Para atualizar um submódulo específico:

```bash
git submodule update --remote conductor/conductor
```

## Trabalhando com Submódulos

### Desenvolvendo em um Submódulo

```bash
# Entrar no diretório do submódulo
cd conductor/conductor

# Criar uma branch para sua feature
git checkout -b feature/nova-funcionalidade

# Fazer suas alterações e commits
git add .
git commit -m "feat: implementa nova funcionalidade"

# Push para o repositório do submódulo
git push origin feature/nova-funcionalidade

# Voltar para o diretório principal
cd ../..

# Atualizar a referência do submódulo
git add conductor/conductor
git commit -m "chore: atualiza conductor para nova funcionalidade"
```

### Verificando Status dos Submódulos

```bash
# Ver status de todos os submódulos
git submodule status

# Ver mudanças nos submódulos
git submodule foreach git status
```

## Estrutura dos Submódulos

```
conductor/
├── conductor/             # Submódulo: primoia/conductor
│   ├── .git/             # Repositório Git do submódulo
│   ├── src/              # Código-fonte da API
│   ├── package.json      # Dependências Node.js
│   ├── Dockerfile        # Imagem Docker
│   └── README.md         # Documentação
│
├── conductor-gateway/     # Submódulo: primoia/conductor-gateway
│   ├── .git/             # Repositório Git do submódulo
│   ├── src/              # Código-fonte do Gateway
│   ├── package.json      # Dependências Node.js
│   ├── Dockerfile        # Imagem Docker
│   └── README.md         # Documentação
│
└── conductor-web/         # Submódulo: primoia/conductor-web
    ├── .git/             # Repositório Git do submódulo
    ├── src/              # Código-fonte Angular
    ├── package.json      # Dependências Node.js
    ├── Dockerfile.angular # Imagem Docker
    └── README.md         # Documentação
```

## Troubleshooting

### Submódulo não atualiza

```bash
# Forçar atualização
git submodule update --remote --force

# Limpar cache do Git
git submodule deinit --all
git submodule init
git submodule update
```

### Submódulo com mudanças não commitadas

```bash
# Ver mudanças
git submodule foreach git status

# Descartar mudanças
git submodule foreach git checkout .

# Ou fazer commit das mudanças
git submodule foreach git add .
git submodule foreach git commit -m "chore: atualiza submódulo"
```

### Problemas de permissão

```bash
# Verificar URLs dos submódulos
git config --file .gitmodules --list

# Atualizar URL se necessário
git config --file .gitmodules submodule.conductor/conductor.url https://github.com/primoia/conductor.git
```

## Referências

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Git Submodule Tutorial](https://www.atlassian.com/git/tutorials/git-submodule)
- [Working with Git Submodules](https://gist.github.com/gitaarik/8735255)