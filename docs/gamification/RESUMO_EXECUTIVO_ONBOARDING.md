# SUMÁRIO EXECUTIVO: NARRATIVA DE ONBOARDING GAMIFICADA DO CONDUCTOR

## O DESAFIO
Explicar conceitos técnicos complexos (agentes de IA, screenplays, conversas multi-agente) através de uma narrativa envolvente e gamificada, em ~10 minutos, para usuários iniciantes.

## A SOLUÇÃO: 4 PILARES

### 1. METÁFORA COGNITIVA
```
Conductor = Guilda de Mestres Artesãos (RPG/Fantasia)
Você      = Iniciado aprendendo a orquestrar especialistas
Agentes   = NPCs com specialidades (Scribe, Knight, Critic, etc.)
Projeto   = Reino/Estandarte sendo construído
```

### 2. NARRATIVA COMPRESSÍVEL
- **ACT I (3 min):** Despertar no Salão e conhecer o Guia
- **ACT II (5 min):** Encontrar 4 mestres e aprender seus papéis
- **ACT III (7 min):** Criar o Estandarte colaborativamente
- **ACT IV (2 min):** Celebração e transformação em Condutor

### 3. EXPERIÊNCIA PRÁTICA
- Você **não apenas aprende**, você **faz**
- Cada NPC representa um conceito:
  - Scribe = Criar documentos (Screenplay)
  - Knight = Executar trabalho
  - Critic = Feedback e iteração
  - Guide = Orientação (Mentor)

### 4. MECÂNICAS DE GAMIFICAÇÃO
- Progressão visual (movimento, interação)
- Coleta de itens (documentos criados)
- Momentos "UAU" (animação épica da criação)
- Escolhas significativas (aceitar feedback ou não)
- Transformação final (Iniciado → Condutor)

---

## 5 CONCEITOS PRINCIPAIS ENSINADOS

| # | Conceito | Metáfora | Mecanismo Quest | Duração |
|---|----------|----------|-----------------|---------|
| 1 | **Agentes** | NPCs especialistas | Encontrar 4 mestres | 2-3 min |
| 2 | **Conversas** | Diálogos no chat | Chat modal com opções | 3-4 min |
| 3 | **Screenplays** | Documentos vivos | Documento criado em tempo real | 2 min |
| 4 | **Colaboração** | Fluxo entre NPCs | Scribe → Knight → Critic | 3 min |
| 5 | **Iteração** | Ciclo de feedback | Receber feedback → aceitar/rejeitar | 2 min |

---

## ARQUITETURA TÉCNICA

### Frontend (Angular)
```
Quest Adventure Component
├─ QuestWelcome (captura nome/email)
├─ QuestCanvas (renderiza Salão 2D)
├─ QuestChatModal (dialoga com NPC)
├─ QuestTracker (mostra progresso)
└─ QuestStateService (gerencia estado + auto-save)
```

### Backend (Conductor Core)
```
Conversation Service (RAG Engine)
├─ conversation_id (identifica conversa multi-agente)
├─ Histórico unificado (todos agentes veem tudo)
├─ Persona injection (injeta personalidade do agente)
├─ Document creation (cria artefatos)
└─ Screenplay update (atualiza em tempo real)
```

### Banco de Dados (MongoDB)
```
conversations: histórico multi-agente por conversation_id
screenplays: documentos vivos do projeto
agents: definições (persona.md + agent.yaml)
quest_sessions: estado do progresso do onboarding
```

---

## O "HERO MOMENT" (Crítico para Engajamento)

**Cenário:** Scribe está criando o Plano do Estandarte

```
Você vê em tempo real:
┌─────────────────────────────────┐
│                                 │
│  PLANO DO ESTANDARTE            │
│  ========================        │
│                                 │
│  Visão: Um símbolo da jornada   │
│  do Iniciado...                 │
│                                 │
│  Elementos:                     │
│  - Moldura dourada...           │
│  - Estrela central...           │
│                                 │
│  Significado: Representa a...   │
│                                 │
└─────────────────────────────────┘

Tipo de efeito: Typewriter animation
Tempo: 3-5 segundos
Som: Escrita suave
Sensação: "Wow, está sendo criado!"
```

---

## FLUXO CRÍTICO: CRIAÇÃO VISUAL ÉPICA

**Passo 2.1: Você vai até a Forja da Artesã**
```
Você: "Podemos criar o estandarte agora?"
Artesã: "Com prazer! Vou pintá-lo para você..."
```

**Passo 2.2: Animação Começa**
```
0s:    Tela branca aparece atrás da Artesã
1s:    Gradiente dourado começa do canto superior esquerdo
2s:    Expande lentamente pelo espaço
2.5s:  Estrela brilhante aparece no centro (POP!)
3s:    Letras começam a aparecer uma por uma
4s:    T-E-A-L-D-O... E-S-T-A-N-D-A-R-T-E
5s:    Partículas de brilho explodem ao redor
       Som épico crescendo
```

**Passo 2.3: Resultado**
```
Estandarte permanece visível:
- Aparece na parede atrás da Artesã
- Você ganha item no inventory
- XP é adicionado
- Popup: "Estandarte Criado! +100 XP"
- Botão: "Vamos refinar? →"
```

**Efeito Emocional:**
- Gratificação imediata
- Sensação de "eu fiz isso"
- Motivação para continuar (refinar)
- Memória positiva (quer jogar novamente)

---

## DADOS FUNDAMENTAIS

### Screenplay (Documento Vivo)
```markdown
# O Estandarte da Guilda

## Contexto
Criado por: Iniciado (você)
Data: 2025-11-09
Missão: Aprender a orquestrar agentes

## Plano (criado pelo Escriba)
...detalhes técnicos...

## Execução (feita pela Artesã)
...descrição visual...

## Feedback (da Crítica)
...sugestões de melhoria...

## Status
- Planejamento: ✅ Completo
- Execução: ✅ Completo
- Refinamento: ⏳ Em andamento
- Aprovação: ⏳ Aguardando
```

### conversation_id
```
"onboarding_quest_seu_email@.com"

Mensagens:
1. Você: "Qual é seu nome?"
2. Sistema: "[Você responde]"
3. Guia: "Bem-vindo, [Nome]!"
4. Escriba: "Vou criar o plano..."
5. [documento é criado]
6. Artesã: "Vou executar..."
7. [animação visual]
8. Crítica: "Ótimo! Mas sugiro..."
9. Você: "Vou aceitar!"
10. [loop de refinamento]
```

---

## MÉTRICAS DE SUCESSO

| Métrica | Target | Como Medir |
|---------|--------|-----------|
| **Completion Rate** | >75% | % de usuários que chegam ao final |
| **Time Spent** | 10-12 min | Registro de tempo no servidor |
| **Engagement Score** | >80/100 | Questionário ao final |
| **Concept Retention** | >70% | Quiz no fim: "O que é um Agente?" |
| **Conversion** | >25% | % que criam projeto após tutorial |
| **Replayability** | >40% | % que rejogam ou compartilham |

---

## ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Backend (2 semanas)
- [ ] Quest endpoints (/api/quest/*)
- [ ] Integration com conversation_service
- [ ] Document generation em tempo real
- [ ] Screenplay update automático

### Fase 2: Frontend (2 semanas)
- [ ] QuestWelcome component
- [ ] QuestCanvas (2D rendering)
- [ ] NPC pathfinding simples
- [ ] Chat modal com diálogos

### Fase 3: Visuais (1.5 semanas)
- [ ] Sprite NPCs (4 personagens)
- [ ] Animação de criação do estandarte
- [ ] Partículas de brilho
- [ ] Sound design (3-4 efeitos)

### Fase 4: Polimento (1 semana)
- [ ] Testes de UX
- [ ] Otimização de performance
- [ ] Feedback loop
- [ ] Ajustes finais

**Total: ~6-7 semanas para MVP completo**

---

## DIFERENCIAIS ÚNICOS

1. **Pedagogia Through Play:** Conceitos técnicos ensinados sem parecer "tutoria"
2. **Momento "UAU" Visual:** Animação épica cria memória positiva
3. **Escolhas Significativas:** Feedback leva a duas caminhos (loop ou continua)
4. **Narrativa com Propósito:** Cada elemento tem função pedagógica
5. **Transformação Emocional:** De "Iniciado" a "Condutor" é significativo
6. **Reutilização de Assets:** Usa os mesmos NPCs que aparecem no Mundo Aberto

---

## PRÓXIMOS PASSOS

### Imediato (Esta semana)
1. Aprovação do conceito e narrativa
2. Scoping técnico detalhado
3. Design de personagens (4 NPCs)

### Curto Prazo (Próximas 2 semanas)
1. Prototipagem de movimento 2D
2. Teste de primeiro chat com NPC
3. Design do Salão da Guilda (mapa)

### Médio Prazo (1 mês)
1. MVP funcional (conceitos 1-3)
2. Testes com primeiros usuários
3. Feedback e iteração

---

## CONCLUSÃO

O onboarding gamificado transforma o aprendizado de Conductor em uma **jornada narrativa emocionante** que:
- Ensina conceitos técnicos reais (agentes, conversas, screenplays)
- Cria memória positiva através de visuais épicos
- Motiva a exploração posterior (mundo aberto)
- Diferencia Conductor como ferramenta única e inovadora

**Tagline:** 
> *"Conductor Quest: Where Learning to Orchestrate Becomes an Adventure"*

---

**Documento Preparado:** 2025-11-09
**Público:** Product, Engineering, Design
**Status:** Pronto para Implementação
