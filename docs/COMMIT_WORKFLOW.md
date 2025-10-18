# Guia de Workflow de Commits

> **Guia completo para trabalhar com submodules Git em projetos monorepo**

Este guia explica como fazer commits corretamente neste projeto monorepo que utiliza submodules Git.

## Índice

- [Estrutura do Projeto](#estrutura-do-projeto)
- [Workflow Básico](#workflow-básico)
- [Exemplos Completos](#exemplos-completos)
- [Cenários Comuns](#cenários-comuns)
- [Notas Importantes](#notas-importantes)
- [Comandos Úteis](#comandos-úteis)
- [Troubleshooting](#troubleshooting)
- [Boas Práticas](#boas-práticas)
- [Recursos Adicionais](#recursos-adicionais)

---

## Estrutura do Projeto

O repositório `conductor-community` é um **monorepo** que inclui três submodules:

```
conductor-community/           (Repositório principal)
└── src/
    ├── conductor/             (Submodule)
    ├── conductor-gateway/     (Submodule)
    └── conductor-web/         (Submodule)
```

### Conceito Importante

Cada submodule é um repositório Git independente. Isso significa que você precisa fazer commits em **dois lugares**:

1. **Primeiro** no repositório do **submodule**
2. **Depois** no **repositório principal** (para atualizar a referência do submodule)

---

## Workflow Básico

### Passo 1: Fazer Mudanças no Submodule

```bash
# Navegar para o diretório do submodule
cd src/conductor

# Verificar o status
git status

# Criar uma branch (recomendado)
git checkout -b feature/minha-nova-funcionalidade
```

### Passo 2: Commit e Push do Submodule

```bash
# Ainda dentro de src/conductor/
git add .
git commit -m "feat: adicionar nova funcionalidade"
git push origin feature/minha-nova-funcionalidade

# Ou fazer push para main se tiver permissões
git push origin main
```

### Passo 3: Voltar ao Repositório Principal

```bash
# Voltar para a raiz do repositório principal
cd ../..  # Agora você está em conductor-community/
```

### Passo 4: Commit da Atualização da Referência do Submodule

```bash
# Verificar o status - você verá que o submodule mudou
git status

# Adicionar a referência do submodule
git add src/conductor

# Fazer commit da atualização
git commit -m "chore: atualizar submodule conductor"

# Push para o repositório principal
git push origin main
```

---

## Exemplos Completos

### Exemplo 1: Desenvolvimento de Feature

```bash
# 1. Fazer mudanças no submodule conductor
cd src/conductor
git checkout -b feature/adicionar-validacao

# ... fazer suas mudanças no código ...
git add src/core/validation.py
git commit -m "feat: adicionar validação de entrada para workflows"
git push origin feature/adicionar-validacao

# 2. Voltar ao repo principal e atualizar referência do submodule
cd ../..
git add src/conductor
git commit -m "chore: atualizar submodule conductor com feature de validação"
git push origin main
```

### Exemplo 2: Trabalhando com Múltiplos Submodules

```bash
# 1. Commit das mudanças no primeiro submodule
cd src/conductor
git add .
git commit -m "feat: adicionar novo endpoint da API"
git push origin main

# 2. Commit das mudanças no segundo submodule
cd ../conductor-gateway
git add .
git commit -m "feat: adicionar rota do gateway para novo endpoint"
git push origin main

# 3. Voltar ao repo principal
cd ../..

# 4. Atualizar TODAS as referências dos submodules de uma vez
git add src/conductor src/conductor-gateway
git commit -m "chore: atualizar submodules conductor e gateway"
git push origin main
```

---

## Cenários Comuns

### Cenário 1: Correção Rápida de Bug

```bash
cd src/conductor
git checkout -b fix/bug-critico

# ... corrigir o bug ...
git add .
git commit -m "fix: resolver bug crítico de autenticação"
git push origin fix/bug-critico
cd ../..
git add src/conductor
git commit -m "chore: atualizar conductor com correção de bug crítico"
git push origin main
```

### Cenário 2: Desenvolvimento de Feature

```bash
cd src/conductor-web
git checkout -b feature/novo-dashboard

# ... desenvolver a feature ao longo de múltiplos commits ...
git add .
git commit -m "feat: adicionar componente de novo dashboard"
git add .
git commit -m "feat: adicionar integração da API do dashboard"
git add .
git commit -m "test: adicionar testes do dashboard"
git push origin feature/novo-dashboard
cd ../..
git add src/conductor-web
git commit -m "chore: atualizar conductor-web com feature de novo dashboard"
git push origin main
```

### Cenário 3: Sincronização com Mudanças da Equipe

```bash
# Obter o mais recente do repo principal
git pull origin main

# Atualizar todos os submodules
git submodule update --init --recursive

# Ou usar o atalho
git pull --recurse-submodules
```

---

## Notas Importantes

### ⚠️ SEMPRE Commite Submodules Primeiro

**NUNCA** faça commit do repositório principal antes de fazer commit das mudanças do submodule. Esta é a ordem correta:

1. ✅ **CORRETO**: Submodule → Repositório Principal
2. ❌ **ERRADO**: Repositório Principal → Submodule

Se você fizer commit do repo principal primeiro, ele referenciará um commit SHA que ainda não existe no repositório do submodule, causando problemas para outros desenvolvedores.

---

## Comandos Úteis

### Verificar Status dos Submodules

```bash
# A partir da raiz do repositório principal
git submodule status

# Ver todas as mudanças dos submodules
git submodule foreach git status

# Ver em qual commit cada submodule está
git submodule foreach git log --oneline -1
```

### Atualizar Submodules para a Versão Mais Recente

```bash
# Puxar mudanças mais recentes de todos os submodules
git submodule update --remote

# Atualizar um submodule específico
git submodule update --remote src/conductor

# Depois fazer commit da atualização da referência
git add src/conductor
git commit -m "chore: atualizar conductor para versão mais recente"
```

### Puxar Mudanças do Repositório Principal

Quando você puxar mudanças do repositório principal, precisa atualizar os submodules:

```bash
# Puxar mudanças do repositório principal
git pull origin main

# Atualizar submodules para corresponder às referências
git submodule update --init --recursive
```

---

## Troubleshooting

### "Detached HEAD" no Submodule

Submodules frequentemente ficam em estado detached HEAD. Para corrigir:

```bash
cd src/conductor
git checkout main
git pull origin main
cd ../..
```

### Mudanças Não Commitadas no Submodule

```bash
# Ver o que não foi commitado
cd src/conductor
git status

# Ou commitá-las
git add .
git commit -m "fix: mudanças não commitadas"
git push origin main

# Ou descartá-las
git checkout .
cd ../..
```

### Referência do Submodule Não Atualizada

```bash
# Verificar se o submodule precisa ser atualizado
git status

# Você verá algo como:
# modified:   src/conductor (new commits)

# Adicionar e fazer commit da referência
git add src/conductor
git commit -m "chore: atualizar submodule conductor"
```

---

## Boas Práticas

### Estratégias de Desenvolvimento

1. **Sempre trabalhe em branches** nos submodules, especialmente para features
2. **Escreva mensagens de commit claras** seguindo [Conventional Commits](https://www.conventionalcommits.org/)
3. **Teste antes de commitar** - execute testes no submodule antes de fazer push
4. **Documente mudanças que quebram compatibilidade** nas mensagens de commit
5. **Mantenha submodules sincronizados** - atualize regularmente para evitar conflitos
6. **Nunca force push** para branches main/master
7. **Faça commits frequentes** nos submodules, mas seja estratégico sobre quando atualizar a referência do repo principal

### Convenções de Commit

```bash
# Tipos de commit recomendados
feat:     nova funcionalidade
fix:      correção de bug
docs:     mudanças na documentação
style:    formatação, ponto e vírgula, etc.
refactor: refatoração de código
test:     adicionar ou corrigir testes
chore:    mudanças em ferramentas, configurações, etc.
```

---

## Recursos Adicionais

### Documentação Relacionada

- [SUBMODULES.md](../SUBMODULES.md) - Referência detalhada de submodules
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Diretrizes de contribuição
- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)

### Referência Rápida

```bash
# Workflow mais comum
cd src/[nome-do-submodule]
git checkout -b [nome-da-branch]
# ... fazer mudanças ...
git add .
git commit -m "[tipo]: [descrição]"
git push origin [nome-da-branch]
cd ../..
git add src/[nome-do-submodule]
git commit -m "chore: atualizar submodule [nome-do-submodule]"
git push origin main
```

---

## Resumo

> **Lembre-se**: Commits do submodule → Commit do repositório principal. Sempre nesta ordem!

### Checklist Rápido

- [ ] Fazer mudanças no submodule
- [ ] Commit e push no submodule
- [ ] Voltar ao repositório principal
- [ ] Atualizar referência do submodule
- [ ] Commit e push no repositório principal

---

**💡 Dica**: Use este guia como referência rápida sempre que trabalhar com submodules!