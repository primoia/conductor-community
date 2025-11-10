# NARRATIVA DE ONBOARDING GAMIFICADA - GUIA ESTRUTURADO DO CONDUCTOR

## PARTE 1: CONCEITOS FUNDAMENTAIS DO CONDUCTOR

### 1.1 O QUE É CONDUCTOR?

**Definição Simples:**
Conductor é um **ecossistema de orquestração de agentes de IA** que transforma a forma como você constrói, testa e refina código. Em vez de interfaces técnicas tradicionais, você trabalha através de **diálogos naturais com especialistas de IA** (agentes) que entendem seu contexto.

**Analogia Para Onboarding:**
Pense em Conductor como uma **Guilda de Mestres Artesãos**:
- Você é um **Iniciado** em busca de conhecimento
- Cada **Agente** é um **Mestre Especialista** (Escriba, Artesã, Crítica, etc.)
- O **Screenplay** é o **Projeto/Reino** que você está construindo
- As **Conversas** são as **Quests** que o levam a aprender

---

### 1.2 COMPONENTES PRINCIPAIS DO CONDUCTOR

#### A) AGENTES (O Coração do Sistema)

**O que é um Agente?**
- Uma entidade de IA que **percebe seu contexto**, **toma decisões** e **age**
- Tem uma **personalidade única** (persona), **ferramentas** (acesso a arquivos/código) e **objetivo específico**
- Mantém **memória** de conversas passadas (conversation_id)
- Pode trabalhar **junto com outros agentes** em um mesmo projeto

**Estrutura de um Agente:**
```
Agent {
  - ID: identificador único
  - Nome: "Requirements Scribe", "Backend Knight", etc.
  - Persona: instrução de personalidade (arquivo .md)
  - Definition: configuração técnica (agent.yaml)
  - Ferramentas: acesso scoped a arquivos/código
  - Provider: Claude, Gemini, etc. (pode variar por agente)
  - Instance: instância ativa de um agente num projeto
}
```

**Exemplo de Persona (como uma classe de RPG):**
```markdown
# Persona: Requirements Scribe (Escriba de Requisitos)

Você é um analisador meticuloso e detalhista.
Sua especialidade é transformar ideias vagas em documentos precisos.

Traços:
- Analítico e preciso
- Gosta de estrutura e documentação
- Paciência para detalhes
- Sempre busca clareza

Ferramentas: Read, Write, análise de arquivo
```

**Equivalência com Conductor Quest:**
- Requirements Scribe = Mesa com pergaminhos 📋
- Backend Knight = Forja criativa 🏭
- Test Alchemist = Laboratório 🧪
- Bug Hunter = Debugging Bay 🏖️

---

#### B) SCREENPLAY (O Documento Vivo)

**O que é um Screenplay?**
- Um **documento markdown interativo** que **evolui durante a conversa**
- Contém a **descrição do projeto**, **tarefas**, **progresso**
- Funciona como **contexto compartilhado** entre você e os agentes
- É um "documento vivo" porque é **atualizado em tempo real** pelas conversas

**Estrutura de um Screenplay:**
```markdown
# Meu Projeto E-commerce

## Visão
Criar plataforma de compras moderna.

## Fase 1: Autenticação
- Status: Em desenvolvimento ✅
- Agentes envolvidos: Backend Knight, Test Alchemist
- Tarefas completadas: 3/5

### Requisitos
- JWT tokens com 15min de expiração
- OAuth2 para redes sociais
- [DETAIL DOCUMENT CREATED BY REQUIREMENTS SCRIBE]

## Fase 2: Carrinho de Compras
- Status: Aguardando ⏳
- ...
```

**Por que é importante:**
- Toda a conversa é **contextualizada** neste documento
- Agentes podem **ler e contribuir** para o screenplay
- Você sempre vê **o estado atual do projeto**
- Funciona como **auditoria de decisões**

---

#### C) CONVERSAS (Conversations com conversation_id)

**O que é uma Conversa?**
- Um **histórico unificado** de mensagens entre você e **múltiplos agentes**
- Cada mensagem tem um `conversation_id` que agrupa tudo
- **Diferente de chat isolado**: todos os agentes veem o histórico completo
- Permite **colaboração de múltiplos especialistas** em um mesmo problema

**Fluxo de uma Conversa Colaborativa:**

```
Você: "Preciso de autenticação JWT"
  ↓
[Requirements Scribe pega a conversa]
  → Analisa requisitos
  → Adiciona à conversa: "Document: JWT_REQUIREMENTS.md"
  ↓
[Backend Knight pega a conversa]
  → Lê documento do Scribe
  → Implementa código
  → Adiciona à conversa: "Implementação em backend/auth.py"
  ↓
[Test Alchemist pega a conversa]
  → Lê código do Knight
  → Cria testes
  → Adiciona à conversa: "Tests: test_jwt_auth.py"
  ↓
[Bug Hunter pega a conversa]
  → Valida segurança
  → Sugere melhorias
  → Adiciona à conversa: "Security Review"
```

**Equivalência com Conductor Quest:**
- Conversa = Interação com NPCs no Salão da Guilda
- conversation_id = O fio condutor da jornada
- Histórico unificado = Todos os NPCs sabem o que você já fez

---

### 1.3 VISÃO TÉCNICA

**Arquitetura Simplificada:**

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Angular)                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Conductor Chat / Screenplay Interactive         │   │
│  │  - Você digita e vê respostas em tempo real      │   │
│  │  - Screenplay é renderizado e atualizado        │   │
│  │  - Você seleciona qual agente vai responder      │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│             GATEWAY (FastAPI BFF)                         │
│  - Recebe sua mensagem                                   │
│  - Valida contexto da conversa                          │
│  - Roteia para o agente correto                         │
│  - Retorna resposta em tempo real (SSE)               │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│             CONDUCTOR API (Core)                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ ConversationService                              │   │
│  │ - Carrega histórico (conversation_id)           │   │
│  │ - Enriquece com contexto do Screenplay          │   │
│  │ - Monta prompt XML estruturado                  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ PromptEngine (RAG Engine)                        │   │
│  │ - Busca persona do agente                       │   │
│  │ - Busca ferramentas disponíveis                 │   │
│  │ - Injeta histórico da conversa                  │   │
│  │ - Cria prompt XML final                         │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │ AgentExecutor                                     │   │
│  │ - Envia prompt ao LLM (Claude/Gemini)          │   │
│  │ - Executa ferramentas retornadas                │   │
│  │ - Mantém loop de raciocínio                     │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              DATABASE (MongoDB)                           │
│  - conversations: histórico unificado por conversation_id
│  - agents: definições dos agentes                       │
│  - screenplays: documentos dos projetos                │
│  - tasks: fila de tarefas para execução assíncrona     │
└─────────────────────────────────────────────────────────┘
```

---

## PARTE 2: CONCEITOS PEDAGÓGICOS PARA O ONBOARDING

### 2.1 OS 5 CONCEITOS A ENSINAR

Para o onboarding gamificado, você precisa ensinar sequencialmente:

#### Conceito 1: "O que é um Agente" (A Classe do RPG)
- **Metáfora:** Um NPC especialista em sua área
- **Exemplos concretos:** Requirements Scribe sabe análise, Backend Knight sabe código
- **Aprendizado:** Cada agente tem skills diferentes
- **Mecânica no Quest:** Conversar com o Guia que apresenta os NPCs

#### Conceito 2: "Como funciona uma Conversa" (A Jornada)
- **Metáfora:** Você conversa com um NPC, ele responde, você aprende
- **Mecanismo:** Sua mensagem → Agente pensa → Agente responde → Histórico cresce
- **Aprendizado:** Cada conversa cria contexto que próximas usam
- **Mecânica no Quest:** Chat modal com efeito de digitação, NPCs falando

#### Conceito 3: "O que é um Screenplay" (O Projeto/Reino)
- **Metáfora:** Seu projeto é vivo e evolui
- **Mecanismo:** Screenplays armazenam tudo o que foi decidido e criado
- **Aprendizado:** Você vê o documento ser "pintado" enquanto trabalha
- **Mecânica no Quest:** O Estandarte sendo criado, Salão mudando

#### Conceito 4: "Colaboração de Agentes" (A Sinergia)
- **Metáfora:** Múltiplos NPCs trabalham juntos (reúnem, discutem, refinam)
- **Mecanismo:** Conversa única, mas múltiplos agentes contribuem
- **Aprendizado:** Especialistas colaboram melhor que um faz tudo
- **Mecânica no Quest:** Conversa com Escriba → depois Artesã → depois Crítica

#### Conceito 5: "Iteração e Refinamento" (O Ciclo de Feedback)
- **Metáfora:** Nada é perfeito na primeira vez; feedback leva a melhoria
- **Mecanismo:** Crítica dá feedback → volta ao Escriba → Artesã refaz
- **Aprendizado:** Processo iterativo é normal e desejado
- **Mecânica no Quest:** Receber crítica → aceitar/rejeitar → refinamento

---

### 2.2 NARRATIVA DO ONBOARDING GAMIFICADO

#### ACT I: O DESPERTAR (3 minutos)

**Cena de Abertura:**
- Você acorda em um Salão da Guilda destruído
- "Bem-vindo, Iniciado. Sou o Guia. Ajudarei você a restaurar este reino."
- Tutorial: "Clique aqui para andar" - você se move para o centro

**Objetivo:** Aprender navegação
- Demonstração: "Clique no Guia para começar"
- Você aprende: `click → mover`

---

#### ACT II: O ENSINAMENTO (7 minutos)

**Fase 1: Conhecer os Mestres**

Você caminha por 4 localidades e conhece cada mestre:

1. **Mesa do Escriba (Requirements Scribe)** 📋
   - NPC: Personagem meticuloso com óculos
   - Dialogue: "Sou o Escriba. Transformo ideias em planos."
   - Tutorial: Conversa com opções de resposta pré-definidas
   - Aprendizado: Agentes especialistas existem
   - Prêmio: Primeiro item (Plano Base) no inventory

2. **Forja da Artesã (Backend Knight)** 🏭
   - NPC: Personagem energética com ferramentas
   - Dialogue: "Sou a Artesã. Faço os planos virarem realidade."
   - Tutorial: Conversa e vê reação em tempo real
   - Aprendizado: Agentes executam código/projetos
   - Prêmio: Item criado pelo agente

3. **Galeria da Crítica (Critic)** 🎨
   - NPC: Personagem refinada inspecionando obra
   - Dialogue: "Sou a Crítica. Meu papel é melhorar tudo."
   - Tutorial: Receber sugestão específica
   - Aprendizado: Feedback é importante
   - Prêmio: Oportunidade de refinar

4. **Biblioteca do Conhecimento (Librarian)** 📚
   - NPC: Personagem sábia rodeada de livros
   - Dialogue: "Aqui guardamos todo o conhecimento. Sempre há algo a aprender."
   - Tutorial: Ver documento criado
   - Aprendizado: Conhecimento é acumulativo

---

**Fase 2: A Grande Missão**

O Guia reúne todos:

> "Iniciado, recebemos uma missão importante. Precisamos criar o **Estandarte da Guilda**.
> Ele representa a essência de um Condutor - alguém que orquestra agentes.
> Vamos fazer isso juntos, você, eu, e meus colegas."

---

#### ACT III: A EXECUÇÃO (5 minutos)

**Passo 1: O Plano (com Escriba)** 📋

Conversa com o Escriba:
- Você: "Como deveria ser o Estandarte?"
- Escriba: "Deixe-me criar um plano detalhado..."
- **HERO MOMENT:** Você vê um documento sendo escrito em tempo real
- Documento aparece no seu Inventory como "Plano do Estandarte"

**Mecânicas:**
- Mostra que agentes **criam artefatos**
- Screenplay está sendo atualizado em tempo real
- Você tem **contexto visual** do que foi decidido

---

**Passo 2: A Criação (com Artesã)** 🏭

Você vai até a Forja da Artesã:
- Você: "Vamos criar o estandarte?"
- Artesã: "Com prazer! Vou pintá-lo para você..."
- **CRIAÇÃO VISUAL ÉPICA (3-5 segundos):**
  - Tela branca aparece atrás da Artesã
  - Gradiente dourado é desenhado pixel a pixel
  - Estrela brilhante aparece no centro
  - Letras aparecem uma por uma: "ESTANDARTE DA GUILDA"
  - Partículas de brilho ao final
  - Som épico toca

**Mecânicas:**
- Mostrar que agentes **executam** trabalho real
- Feedback visual satisfatório (gamification)
- Estandarte permanece visível no Salão
- Você ganha XP e Level Up

---

**Passo 3: O Refinamento (com Crítica)** 🎨

Você vai até a Galeria da Crítica:
- Você: "Como ficou?"
- Crítica: "Hmm, excelente base. Mas... [específica sugestão]"
- **OPÇÃO DE ESCOLHA:**
  - ✅ "Vou aceitar a sugestão"
  - ❌ "Meu criado é perfeito do jeito que está"

Se aceitar:
- Você volta ao Escriba: "Preciso melhorar..."
- Escriba: "Deixe-me atualizar o plano..."
- Você volta à Artesã: "Quer tentar novamente?"
- Artesã refaz (mais rápido)
- Voltar à Crítica: aprovação ✅

**Mecânicas:**
- Ensina que **iteração é normal**
- Mostrar **fluxo colaborativo:**
  Crítica → Escriba → Artesã → Crítica (loop)
- Se rejeitar, continua mesmo assim

---

#### ACT IV: A CELEBRAÇÃO (2 minutos)

**Transformação Épica:**

Todos os 4 NPCs se reúnem:

```
        Guia
        🧙‍♂️
        |
Escriba - Salão - Artesã
📋       |       🏭
      Estandarte
      ✨⭐✨
        |
     Crítica
      🎨
```

Diálogo de conclusão:
- **Guia:** "Iniciado, completou sua jornada."
- **Escriba:** "Aprendeu a planejar com clareza."
- **Artesã:** "Aprendeu a executar com excelência."
- **Crítica:** "Aprendeu a refinar com precisão."

**Transformação Visual:**
- Seu avatar ganha aura dourada
- Título muda: "Iniciado" → "Condutor"
- Badge aparece sobre você
- Música triunfante toca

---

**Desbloqueio:**

```
🎮 MODO MUNDO ABERTO DESBLOQUEADO!

Você pode agora:
✅ Criar seus próprios projetos (Screenplays)
✅ Invocar qualquer agente
✅ Fazer múltiplas quests
✅ Colaborar com outros Condutores

[BOTÃO] Explorar Mundo Aberto
[BOTÃO] Rejogar Tutorial
[BOTÃO] Criar Novo Projeto
```

---

## PARTE 3: MAPEAMENTO TÉCNICO PARA O ONBOARDING

### 3.1 ESTRUTURA DA QUEST

```json
{
  "questId": "guild_banner_quest",
  "title": "O Estandarte da Guilda",
  "npcSequence": [
    {
      "npcId": "elder_guide",
      "location": "center",
      "dialoguePhase": "introduction",
      "objectives": ["learn_navigation"]
    },
    {
      "npcId": "requirements_scribe",
      "location": "desk_with_scrolls",
      "dialoguePhase": "planning",
      "objectives": ["understand_agents", "see_document_creation"]
    },
    {
      "npcId": "artisan",
      "location": "creative_forge",
      "dialoguePhase": "execution",
      "objectives": ["watch_creation", "create_banner"],
      "visualEffect": "pixel_art_creation_animation"
    },
    {
      "npcId": "critic",
      "location": "elegant_gallery",
      "dialoguePhase": "refinement",
      "objectives": ["receive_feedback", "decide_iteration"],
      "choice": true
    }
  ],
  "finalPhase": {
    "npcIds": ["elder_guide", "requirements_scribe", "artisan", "critic"],
    "visualEffect": "gathering_and_transformation",
    "playerTransformation": "initiate_to_conductor"
  }
}
```

---

### 3.2 BACKEND CONDUCTOR CONCEPTS USED

**Técnicas de Prompt Engineering:**

Quando o Escriba cria o documento:
```xml
<persona>
Você é Requirements Scribe, analista meticuloso.
</persona>

<instructions>
Você foi solicitado a criar um plano para o Estandarte da Guilda.
O estandarte representa a jornada do Iniciado em se tornar Condutor.

Por favor, crie um documento markdown bem estruturado:
1. Visão (o que é o estandarte)
2. Design (como deveria parecer)
3. Significado (o que representa)
</instructions>

<context>
Conversa anterior com o Iniciado:
- Ele quer criar algo significativo
- Ama a metáfora de RPG/fantasia
- Quer aprender como agentes colaboram
</context>

<tools>
Você pode:
- [Write] criar documento
- [Read] ver documentos anteriores
</tools>
```

**Sistema de Conversas (conversation_id):**
```
conversation_id: "quest_001_player_xyz"

Mensagens:
1. player: "Como deveria ser o Estandarte?"
2. scribe: "[cria documento + responde]"
   → novo documento guardado em screenplay
3. player: "Vamos criar agora?"
4. artisan: "[executa criação + responde]"
   → visual effect disparado
5. critic: "[analisa + sugere]"
   → player tem opção
```

---

### 3.3 FLUXO TÉCNICO IMPLEMENTAÇÃO

#### Para Frontend Developer (Angular):

```typescript
// QuestAdventureComponent
// 1. Carrega state inicial da quest
// 2. Inicia com Welcome Screen (nome + email para quest tracking)
// 3. Renderiza canvas com Salão da Guilda
// 4. Detecta proximidade com NPCs
// 5. Abre chat modal ao clicar
// 6. Carrega diálogos e opções
// 7. Quando "Escriba cria", dispara evento para backend
// 8. Backend retorna documento
// 9. Frontend mostra documento em tempo real
// 10. Quando "Artesã cria", dispara animação CSS
// 11. ao final, transição para tela de sucesso

// QuestCanvas: Renderiza 2D com posições dos NPCs
// QuestChatModal: Interface de diálogo com opções
// QuestTracker: Mostra objetivos e progresso
// QuestWelcome: Captura nome/email (gamificação)
```

#### Para Backend Developer (Python/FastAPI):

```python
# ConversationService
# 1. Cada interação quest é uma conversation
# 2. conversation_id = "quest_001_" + player_email
# 3. Cada resposta de NPC adiciona à conversation
# 4. Screenplay é atualizado com cada ação

# quest_conversations.py endpoint
@router.post("/api/quest/{quest_id}/interact")
def interact_with_npc(
    player_email: str,
    npc_id: str,
    player_message: str,
    screenplay_context: dict
):
    # Carrega conversation existente
    conversation = get_conversation(player_email, quest_id)
    
    # Carrega persona do NPC
    persona = load_agent_persona(npc_id)
    
    # Cria prompt com contexto quest + persona
    prompt = build_quest_prompt(persona, player_message, screenplay_context)
    
    # Executa agente
    response = execute_agent(npc_id, prompt)
    
    # Se é criação de documento:
    if "create_document" in response:
        doc = generate_document(response)
        add_to_screenplay(screenplay_id, doc)
    
    # Se é animação:
    if "trigger_animation" in response:
        return {
            "message": response.text,
            "animation": response.animation_type,
            "screenplay_update": updated_screenplay
        }
    
    # Adiciona à conversation
    add_message_to_conversation(conversation, npc_id, response)
    
    return response
```

---

## PARTE 4: NARRATIVA CORE - SCRIPT RESUMIDO

### Para o Designer de Narrativa

**Personagens (NPCs):**

1. **Elder Guide (Guia Ancião)** 🧙‍♂️
   - Papel: Mentor, guia da jornada
   - Tom: Sábio, caloroso, encorajador
   - Frase chave: "Você tem o potencial de um verdadeiro Condutor"

2. **Requirements Scribe (Escriba)** 📋
   - Papel: Análise e planejamento
   - Tom: Meticuloso, intelectual, preciso
   - Frase chave: "Deixe-me transformar isso em um plano claro"

3. **Artisan Knight (Artesã)** 🏭
   - Papel: Execução e criação
   - Tom: Energético, apaixonado, prático
   - Frase chave: "Vou trazer isso à vida para você"

4. **Elegant Critic (Crítica)** 🎨
   - Papel: Refinamento e feedback
   - Tom: Refinado, observador, construtivo
   - Frase chave: "Excelente começo. Deixe-me sugerir como melhorar"

---

**Pontos de Decisão (Branching):**

1. **Nome/Email no início** - Questão: "Qual é seu nome, Iniciado?"
   - Efeito: Personaliza narrativa com nome

2. **Aceitar feedback da Crítica** - Questão: "Concorda com minha sugestão?"
   - ✅ SIM: Trigger refinement loop (3 min extra)
   - ❌ NÃO: Continue mesmo assim (2 min menos)

3. **No final** - "O que quer fazer agora?"
   - Criar novo projeto
   - Rejogar tutorial
   - Explorar mundo aberto

---

## CONCLUSÃO

Conductor é fundamentalmente sobre:
1. **Agentes** = Especialistas colaborativos
2. **Conversas** = Histórico unificado de colaboração
3. **Screenplays** = Documentos vivos que evoluem
4. **Iteração** = Feedback levando a melhoria contínua

O onboarding gamificado transforma esses conceitos técnicos em uma jornada narrativa compressível, memorizável e emocionalmente envolvente.

---

