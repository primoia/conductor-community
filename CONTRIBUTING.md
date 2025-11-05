# Guia de Contribuição

Obrigado por considerar contribuir com o Conductor Community! 🎉

Este guia irá te ajudar a configurar o ambiente de desenvolvimento e entender como contribuir com o projeto.

## 🚀 Configuração do Ambiente de Desenvolvimento

### Pré-requisitos

- **Docker** e **Docker Compose** instalados
- **Git** instalado
- **Node.js** (versão 18 ou superior) - para desenvolvimento local opcional
- **MongoDB** (opcional, se quiser rodar localmente)

### 1. Clone o Repositório com Submódulos

```bash
# Clone com todos os submódulos
git clone --recurse-submodules https://github.com/primoia/conductor-community.git
cd conductor-community

# Se já clonou sem submódulos, adicione-os agora
git submodule init
git submodule update
```

### 2. Configure o Ambiente

```bash
# Copie os arquivos de configuração
cp config/conductor/config.yaml.example config/conductor/config.yaml
cp config/gateway/gateway.env.example config/gateway/gateway.env

# Edite as configurações conforme necessário
nano config/conductor/config.yaml
nano config/gateway/gateway.env
```

### 3. Suba o Ambiente de Desenvolvimento

```bash
# Suba a stack em modo de desenvolvimento
docker-compose -f docker-compose.dev.yml up --build -d

# Verifique se tudo está rodando
docker-compose -f docker-compose.dev.yml ps
```

## 🏗️ Estrutura do Projeto

### Repositórios e Submódulos

Este repositório orquestra três projetos principais via submódulos Git:

| Submódulo | Repositório | Descrição |
|-----------|-------------|-----------|
| `conductor/conductor/` | [primoia/conductor](https://github.com/primoia/conductor) | API principal do Conductor |
| `conductor/conductor-gateway/` | [primoia/conductor-gateway](https://github.com/primoia/conductor-gateway) | Gateway de API |
| `conductor/conductor-web/` | [primoia/conductor-web](https://github.com/primoia/conductor-web) | Interface web Angular |

### Fluxo de Desenvolvimento

1. **Trabalhe no submódulo específico** onde está a funcionalidade
2. **Teste localmente** usando o docker-compose.dev.yml
3. **Faça commit e push** no submódulo
4. **Atualize a referência** no repositório principal

## 🔧 Desenvolvimento

### Trabalhando com Submódulos

#### Atualizar Submódulos

```bash
# Atualizar todos os submódulos para a versão mais recente
git submodule update --remote

# Atualizar um submódulo específico
git submodule update --remote conductor/conductor
```

#### Desenvolvendo em um Submódulo

```bash
# Entre no diretório do submódulo
cd conductor/conductor

# Crie uma branch para sua feature
git checkout -b feature/nova-funcionalidade

# Faça suas alterações e commits
git add .
git commit -m "feat: implementa nova funcionalidade"

# Push para o repositório do submódulo
git push origin feature/nova-funcionalidade

# Volte para o diretório principal
cd ../..

# Atualize a referência do submódulo
git add conductor/conductor
git commit -m "chore: atualiza conductor para nova funcionalidade"
```

### Modos de Desenvolvimento

#### 1. Desenvolvimento com Docker (Recomendado)

```bash
# Use o docker-compose.dev.yml
docker-compose -f docker-compose.dev.yml up --build -d

# Para ver logs em tempo real
docker-compose -f docker-compose.dev.yml logs -f

# Para rebuildar um serviço específico
docker-compose -f docker-compose.dev.yml up --build conductor-api
```

**Vantagens:**
- Ambiente isolado e consistente
- Live-reload automático
- Fácil de compartilhar com outros desenvolvedores

#### 2. Desenvolvimento Local (Avançado)

```bash
# Instale dependências em cada submódulo
cd conductor/conductor && npm install
cd ../conductor-gateway && npm install
cd ../conductor-web && npm install

# Rode cada serviço localmente
# Terminal 1: MongoDB
mongod

# Terminal 2: Conductor API
cd conductor/conductor && npm run dev

# Terminal 3: Gateway
cd conductor/conductor-gateway && npm run dev

# Terminal 4: Web UI
cd conductor/conductor-web && npm run start
```

## 🧪 Testes

### Executando Testes

```bash
# Testes em todos os serviços
docker-compose -f docker-compose.dev.yml exec conductor-api npm test
docker-compose -f docker-compose.dev.yml exec gateway npm test
docker-compose -f docker-compose.dev.yml exec web npm test

# Testes com coverage
docker-compose -f docker-compose.dev.yml exec conductor-api npm run test:coverage
```

### Testes de Integração

```bash
# Suba a stack completa
docker-compose -f docker-compose.dev.yml up -d

# Execute testes de integração
npm run test:integration
```

## 📝 Padrões de Commit

Seguimos o [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Tipos de Commit

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação, ponto e vírgula, etc.
- `refactor`: Refatoração de código
- `test`: Adição ou correção de testes
- `chore`: Tarefas de build, dependências, etc.

### Exemplos

```bash
git commit -m "feat(api): adiciona endpoint para listar workflows"
git commit -m "fix(gateway): corrige problema de autenticação JWT"
git commit -m "docs: atualiza README com novas instruções"
git commit -m "test(api): adiciona testes para workflow service"
```

## 🔄 Processo de Pull Request

### 1. Antes de Começar

- [ ] Verifique se existe uma issue relacionada
- [ ] Se não existir, crie uma issue descrevendo o problema/feature
- [ ] Atribua a issue para você mesmo

### 2. Desenvolvimento

- [ ] Faça fork do repositório
- [ ] Clone seu fork com submódulos
- [ ] Crie uma branch para sua feature: `git checkout -b feature/nome-da-feature`
- [ ] Desenvolva e teste sua funcionalidade
- [ ] Siga os padrões de commit
- [ ] Atualize a documentação se necessário

### 3. Submissão

- [ ] Faça push da sua branch
- [ ] Crie um Pull Request
- [ ] Preencha o template do PR
- [ ] Adicione reviewers
- [ ] Aguarde a revisão e feedback

### Template do Pull Request

```markdown
## Descrição
Breve descrição das mudanças

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova funcionalidade
- [ ] Breaking change
- [ ] Documentação

## Checklist
- [ ] Código segue os padrões do projeto
- [ ] Testes foram adicionados/atualizados
- [ ] Documentação foi atualizada
- [ ] Mudanças foram testadas localmente

## Screenshots (se aplicável)
Adicione screenshots para ajudar a explicar as mudanças

## Issues Relacionadas
Closes #123
```

## 🐛 Reportando Bugs

### Antes de Reportar

1. Verifique se o bug já foi reportado
2. Teste com a versão mais recente
3. Verifique os logs para mais detalhes

### Como Reportar

Use o template de issue para bugs:

```markdown
## Descrição do Bug
Descrição clara e concisa do bug

## Passos para Reproduzir
1. Vá para '...'
2. Clique em '...'
3. Veja o erro

## Comportamento Esperado
O que deveria acontecer

## Screenshots
Se aplicável, adicione screenshots

## Ambiente
- OS: [ex: Ubuntu 20.04]
- Docker: [ex: 20.10.7]
- Versão: [ex: v1.0.0]

## Logs
```
Cole os logs relevantes aqui
```
```

## 💡 Sugerindo Melhorias

### Antes de Sugerir

1. Verifique se a melhoria já foi sugerida
2. Considere se a melhoria se alinha com os objetivos do projeto
3. Pense em como implementar a melhoria

### Como Sugerir

Use o template de issue para melhorias:

```markdown
## Descrição da Melhoria
Descrição clara e concisa da melhoria sugerida

## Problema que Resolve
Que problema esta melhoria resolve?

## Solução Proposta
Descrição da solução que você propõe

## Alternativas Consideradas
Outras soluções que você considerou

## Contexto Adicional
Qualquer outro contexto sobre a melhoria
```

## 📚 Recursos Adicionais

- [Documentação do Conductor](https://github.com/primoia/conductor/wiki)
- [Guia de Desenvolvimento](https://github.com/primoia/conductor-community/wiki/Development)
- [Padrões de Código](https://github.com/primoia/conductor-community/wiki/Coding-Standards)
- [FAQ](https://github.com/primoia/conductor-community/wiki/FAQ)

## 🤝 Código de Conduta

Este projeto segue o [Código de Conduta](CODE_OF_CONDUCT.md). Ao participar, você concorda em manter este código.

## 📞 Contato

- **Issues**: [GitHub Issues](https://github.com/primoia/conductor-community/issues)
- **Discussões**: [GitHub Discussions](https://github.com/primoia/conductor-community/discussions)
- **Email**: community@primoia.com

---

**Obrigado por contribuir! 🎉**