# MAPA DE RELACIONAMENTOS - CONCEITOS CONDUCTOR

## 1. COMO TUDO SE CONECTA

```
┌─────────────────────────────────────────────────────────────────┐
│                     VOCÊ (Desenvolvedor/Iniciado)               │
└────────────────────────┬────────────────────────────────────────┘
                         │ Escreve mensagem
                         ↓
         ┌───────────────────────────────┐
         │   CONVERSA (Conversation)     │
         │  ┌─────────────────────────┐  │
         │  │ conversation_id:        │  │  ← Identifica TODA a
         │  │ "proj_123_email@.com"   │  │    conversa multi-agente
         │  │                         │  │
         │  │ Mensagens:              │  │
         │  │ 1. você: "criar auth"   │  │
         │  │ 2. scribe: "plano..."   │  │
         │  │ 3. knight: "código..."  │  │
         │  │ 4. alchemist: "testes"  │  │
         │  └─────────────────────────┘  │
         └────────┬──────────────────────┘
                  │ Alimenta
      ┌───────────┴───────────┐
      │                       │
      ↓                       ↓
┌──────────────┐      ┌──────────────────┐
│  SCREENPLAY  │      │     AGENTES      │
│ (Documento   │      │  (Especialistas) │
│   Vivo)      │      │                  │
│              │      │ - Scribe         │
│ # Projeto    │      │ - Knight         │
│ ## Fase 1    │      │ - Alchemist      │
│ ...          │      │ - Hunter         │
│              │      │                  │
│ Status:      │      │ cada um tem:     │
│ atualizado   │      │ - persona.md     │
│ em tempo     │      │ - agent.yaml     │
│ real         │      │ - ferramentas    │
│              │      │ - provider (IA)  │
└──────────────┘      └──────────────────┘
      ↑                       ↑
      │ Contextualiza         │ Participam
      │                       │
      └───────────────────────┘
```

---

## 2. FLUXO DE EXECUÇÃO (Como um Agente Responde)

```
                    VOCÊ
                    │ "Preciso de autenticação"
                    ↓
        ┌────────────────────────┐
        │  Gateway (FastAPI)     │
        │ - Valida input         │
        │ - Extrai conversation  │
        │   _id do sessionStorage│
        └────────┬───────────────┘
                 │
                 ↓
    ┌────────────────────────────────┐
    │ Conductor Core (Python)         │
    │ ┌──────────────────────────┐   │
    │ │ ConversationService      │   │
    │ │ - Carrega histórico      │   │ ← conversation_id é a chave!
    │ │   (tudo que foi dito)    │   │
    │ └────────┬─────────────────┘   │
    │          ↓                      │
    │ ┌──────────────────────────┐   │
    │ │ PromptEngine (RAG)       │   │
    │ │ - Lê persona do agente   │   │ ← "Você é Requirements Scribe"
    │ │ - Lê screenplay          │   │ ← Contexto do projeto
    │ │ - Lê histórico completo  │   │ ← Tudo que foi conversado
    │ │ - Monta XML estruturado  │   │
    │ │                          │   │
    │ │ Prompt final:            │   │
    │ │ <persona>...             │   │
    │ │ <context>...             │   │
    │ │ <history>...             │   │
    │ │ <tools>...               │   │
    │ └────────┬─────────────────┘   │
    │          ↓                      │
    │ ┌──────────────────────────┐   │
    │ │ AgentExecutor            │   │
    │ │ - Envia para Claude/     │   │
    │ │   Gemini com prompt XML  │   │
    │ │ - Recebe resposta        │   │
    │ │ - Se pede, executa       │   │
    │ │   ferramentas (Write,    │   │
    │ │   Read, etc)             │   │
    │ └────────┬─────────────────┘   │
    │          ↓                      │
    │ ┌──────────────────────────┐   │
    │ │ ConversationService      │   │
    │ │ - Adiciona resposta do   │   │
    │ │   agente à conversation  │   │
    │ │ - Atualiza screenplay    │   │
    │ │   se necessário          │   │
    │ └────────┬─────────────────┘   │
    └─────────┬────────────────────┘
              ↓
    ┌─────────────────────────┐
    │ Gateway (SSE Stream)    │
    │ - Retorna resposta      │
    │   em tempo real         │
    └──────────┬──────────────┘
               ↓
            VOCÊ vê a resposta
        + documento criado
        + screenplay atualizado
```

---

## 3. RELAÇÃO ENTRE COMPONENTES

### A) CONVERSAS (conversation_id)

**O "Fio Vermelho" que conecta tudo**

```
conversation_id = "projeto_001_seu@email.com"
                   ├─ projeto_001: identificador único do projeto
                   └─ seu@email.com: para rastrear múltiplas conversas do mesmo usuário

Dentro da conversa:
┌─────────────────────────────────────────────────┐
│ Mensagem 1 (você)                               │
│ - timestamp: 2025-11-09 10:00                   │
│ - role: "user"                                  │
│ - content: "Preciso de autenticação JWT"        │
└─────────────────────────────────────────────────┘
│
├─ Todos os agentes veem ESTA MENSAGEM
│  ↓
┌─────────────────────────────────────────────────┐
│ Mensagem 2 (Requirements Scribe)                │
│ - timestamp: 2025-11-09 10:05                   │
│ - role: "assistant"                             │
│ - agent_id: "requirements_scribe"               │
│ - emoji: 📋                                      │
│ - content: "Vou analisar os requisitos..."      │
│ - created_artifact: {                           │
│     type: "document",                           │
│     name: "JWT_REQUIREMENTS.md",                │
│     content: "..."                              │
│   }                                             │
└─────────────────────────────────────────────────┘
│
├─ TODOS veem este artefato criado
│  ↓
┌─────────────────────────────────────────────────┐
│ Mensagem 3 (Backend Knight)                     │
│ - timestamp: 2025-11-09 10:10                   │
│ - role: "assistant"                             │
│ - agent_id: "backend_knight"                    │
│ - emoji: ⚔️                                      │
│ - content: "Lendo o documento do Scribe..."     │
│ - created_artifact: {                           │
│     type: "code",                               │
│     file: "src/auth/jwt.py",                    │
│     content: "..."                              │
│   }                                             │
└─────────────────────────────────────────────────┘
```

**Diferença com Chat tradicional:**
```
Chat Isolado (ANTES):
user → agent_A (tem history_A)
user → agent_B (tem history_B)  ← Agent B não vê o que A fez!

Chat com conversation_id (AGORA):
user → agent_A (vê conversation_id)
     ↓ adiciona à conversation
user → agent_B (vê TUDO anterior)  ← Agent B sabe o que A fez!
```

---

### B) SCREENPLAYS (Documentos Vivos)

**O "Contexto Compartilhado" que cresce**

```
screenplay.md (Documento Markdown)
│
├─ Seção 1: Visão do Projeto
│  └─ Escrito por: Você
│
├─ Seção 2: Requisitos
│  ├─ Criado por: Requirements Scribe
│  ├─ Conteúdo: JWT_REQUIREMENTS.md (link ou embed)
│  └─ Status: ✅ Aprovado
│
├─ Seção 3: Implementação Backend
│  ├─ Criado por: Backend Knight
│  ├─ Arquivos:
│  │  ├─ src/auth/jwt.py (implementação)
│  │  └─ src/auth/config.py (config)
│  └─ Status: ✅ Completo
│
├─ Seção 4: Testes
│  ├─ Criado por: Test Alchemist
│  ├─ Arquivo: test_jwt_auth.py
│  └─ Status: ✅ 100% coverage
│
├─ Seção 5: Segurança
│  ├─ Criado por: Bug Hunter
│  ├─ Findings: 3 potenciais issues
│  └─ Status: ⚠️ Requer revisão
│
└─ Notas da Conversa:
   └─ Links para cada decision point

Cada seção tem ORIGEM (qual agente criou)
Cada seção tem TIMESTAMP
Cada seção é AUDITÁVEL
```

**Como screenplay é atualizado em tempo real:**

```
Você escreve em chat:
"Precisamos suportar OAuth2"
        ↓
Scribe responde e cria documento
"OAuth2_REQUIREMENTS.md"
        ↓
Documento é adicionado automaticamente ao screenplay
section "Requisitos Adicionais":
  - [OAuth2_REQUIREMENTS.md]
        ↓
Você vê o screenplay sendo atualizado ENQUANTO escreve
(ou logo após)
```

---

### C) AGENTES (Especialistas)

**O "Quem Faz" em cada Conversa**

```
┌─────────────────────────────────┐
│ Agent: Requirements Scribe       │
├─────────────────────────────────┤
│ ID: requirements_scribe          │
│ Emoji: 📋                         │
│ Nome: Escriba de Requisitos      │
│                                 │
│ Definição:                      │
│ ├─ agent.yaml (config técnica)  │
│ │  ├─ provider: claude           │
│ │  ├─ model: claude-3-sonnet     │
│ │  └─ tools: [Read, Write, List] │
│ │                                │
│ └─ persona.md (personalidade)   │
│    ├─ "Você é meticuloso"       │
│    ├─ "Transforma ideias em     │
│    │   planos precisos"          │
│    ├─ "Você gosta de detalhes"  │
│    └─ "Sua meta é clareza"      │
│                                 │
│ Quando é invocado em uma        │
│ conversa, TUDO isso é injetado   │
│ no prompt XML para o LLM         │
│                                 │
│ Resultado:                      │
│ └─ Resposta que soa como um      │
│    Escriba real (traços,        │
│    estilo, tom)                 │
└─────────────────────────────────┘
```

**Conceito de "Instance":**

```
Agente é TEMPLATE
   ↓
Instance é EXECUÇÃO

requirements_scribe (agent)
      ↓
projeto_001 + requirements_scribe = INSTANCE
projeto_002 + requirements_scribe = OUTRA INSTANCE (contexto diferente)

Cada instance:
- Tem seu próprio conversation_id
- Tem acesso scoped a arquivos específicos
- Mantém memória do projeto
- Pode ser "desativado" ou "ativado"
```

---

## 4. ELEMENTO GAMIFICADO: QUEST

```
Conductor Quest mapeia conceitos técnicos em narrativa:

CONCEITO                    MECÂNICA QUEST             NPC ENVOLVIDO
─────────────────────────────────────────────────────────────────
Agente                  →   NPC especialista        →   4 NPCs (Guia, Scribe, Artisan, Critic)
Persona                 →   Personalidade do NPC    →   Cada NPC tem jeito único
Ferramenta              →   Habilidade do NPC       →   Scribe lê/escreve, Knight executa
Conversa                →   Diálogo no chat modal   →   Você clica no NPC → abre chat
conversation_id         →   Fio da jornada          →   Todos os NPCs sabem o que fez
Screenplay              →   Estandarte being        →   Vê o documento sendo criado
Document criado         →   Item no inventory       →   "Plano do Estandarte" no inventário
Iteração                →   Ciclo de refinamento    →   Crítica → Scribe → Knight → Crítica
Colaboração             →   Todos reunidos          →   Final: todos os 4 NPCs celebram
```

---

## 5. TIMELINE VISUAL DO ONBOARDING

```
0:00 ├─ Abertura: Salão destruído
     │
1:00 ├─ Encontra Guia (aprende navegação)
     │  "Bem-vindo, Iniciado"
     │  ✓ Conceito 1: Agentes existem
     │
2:00 ├─ Conhece Scribe (aprende planejamento)
     │  "Transformo ideias em planos"
     │  ✓ Conceito 2: Agentes criam documentos
     │  + Ganha item: "Plano Básico"
     │
3:00 ├─ Conhece Knight (aprende execução)
     │  "Faço planos virarem realidade"
     │  ✓ Conceito 3: Agentes executam
     │  + Ganha item: "Ferramentas"
     │
4:00 ├─ Conhece Alchemist (aprende testes)
     │  "Qualidade é tudo"
     │  ✓ Conceito 4: Agentes validam
     │  + Ganha item: "Testes Escritos"
     │
5:00 ├─ Conhece Critic (aprende refinamento)
     │  "Feedback leva à excelência"
     │  ✓ Conceito 5: Iteração é importante
     │  + Ganha item: "Sugestões"
     │
6:00 ├─ MISSÃO PRINCIPAL: Criar Estandarte
     │
7:00 ├─ FASE 1: Planejar (com Scribe)
     │  Você: "Como deveria ser?"
     │  Scribe: "Deixe-me criar..." [HERO MOMENT]
     │  ✓ Documento criado em tempo real
     │  + Level UP!
     │
8:00 ├─ FASE 2: Executar (com Knight)
     │  Você: "Vamos criar?"
     │  Knight: "Vou pintar..." [VISUAL ÉPICA]
     │  ✓ Estandarte é criado em 3-5 seg
     │  + XP + Level UP!
     │
9:00 ├─ FASE 3: Refinar (com Critic)
     │  Critic: "Ótimo, mas..." [CHOICE POINT]
     │
9:30 ├─ LOOP (opcional):
     │  Aceitar → Scribe → Knight → Critic → Aprovado
     │
10:00├─ CELEBRAÇÃO: Todos reunidos
     │  ┌─────────────────┐
     │  │   ✨ GANHOU! ✨  │
     │  │ Iniciado →      │
     │  │  CONDUTOR       │
     │  └─────────────────┘
     │
10:30├─ Desbloqueio: Mundo Aberto
     │  "Agora você pode..."
     │
