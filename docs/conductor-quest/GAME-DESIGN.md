# 🎮 Game Design Document - Conductor Quest

## 🎯 Visão Central

**Conductor Quest transforma o processo de desenvolvimento em uma jornada de aprendizado gamificada, onde o jogador aprende a orquestrar agentes de IA através de uma narrativa envolvente.**

---

## 🏛️ Conceito Principal

### O Salão da Guilda

O jogo se passa no **Salão da Guilda dos Condutores**, um espaço que mistura elementos medievais-fantásticos com tecnologia moderna. Este ambiente serve como:

1. **Hub Central**: Onde todas as interações principais acontecem
2. **Showcase Visual**: Cada NPC tem sua própria estação de trabalho temática
3. **Metáfora Viva**: O salão representa um projeto/workspace do Conductor

### A Jornada do Iniciado

O jogador é um **Iniciado** que deve:
1. Aprender o papel de cada especialista (agente)
2. Entender o fluxo de trabalho (planejar → executar → revisar → refinar)
3. Praticar a orquestração através de uma missão prática
4. Graduar-se como Condutor

---

## 🎭 Personagens (NPCs/Agentes)

### Hierarquia e Papéis

| NPC | Papel no Fluxo | Personalidade | Localização | Visual |
|-----|---------------|---------------|-------------|---------|
| **Guia** | Mentor/Orientador | Sábio, paciente, encorajador | Centro do Salão | Robes modernos, aura sábia |
| **Escriba** | Planejamento | Metódico, intelectual, detalhista | Mesa com pergaminhos | Óculos, pena mágica |
| **Artesã** | Execução | Energética, apaixonada, mãos-na-massa | Forja criativa | Avental, ferramentas |
| **Crítica** | Revisão/QA | Refinada, observadora, perfeccionista | Galeria elegante | Vestimenta elegante |

### Sistema de Diálogos

```typescript
interface DialogueSystem {
  // Tipos de interação
  interactionTypes: {
    greeting: string;      // Primeira interação
    working: string[];     // Durante tarefa
    success: string;       // Tarefa completa
    feedback: string;      // Dando feedback
  };

  // Estados do NPC
  npcStates: {
    idle: "Aguardando interação";
    listening: "Ouvindo o jogador";
    thinking: "Processando pedido";
    working: "Executando tarefa";
    complete: "Tarefa finalizada";
  };

  // Opções de resposta
  responseOptions: {
    guided: DialogueOption[];  // Opções pré-definidas
    freeText: boolean;         // Permite entrada livre
    hybrid: boolean;           // Combina ambos
  };
}
```

---

## 🎮 Mecânicas Principais

### 1. Movimento e Navegação

```typescript
interface MovementSystem {
  // Controles
  controls: {
    mobile: "Tap to move";
    desktop: "Click to move";
    keyboard: "WASD opcional";
  };

  // Pathfinding
  movement: {
    type: "Point and click";
    pathfinding: "A* simplificado";
    speed: "200px/segundo";
    animation: "Pegadas no caminho";
  };

  // Indicadores visuais
  indicators: {
    destination: "Círculo no destino";
    path: "Linha pontilhada";
    interactable: "Glow em NPCs próximos";
  };
}
```

### 2. Sistema de Interação

```typescript
interface InteractionSystem {
  // Detecção de proximidade
  proximity: {
    range: 50;  // pixels
    indicator: "!" sobre NPC";
    autoPrompt: true;
  };

  // Chat Modal
  chatModal: {
    style: "Pergaminho digital";
    position: "Bottom 60% (mobile)";
    animations: "Slide up/down";
    typing: "Efeito de digitação";
  };

  // Feedback visual
  feedback: {
    npcBusy: "Animação de trabalho";
    taskComplete: "✅ visual";
    newObjective: "Glow dourado";
  };
}
```

### 3. Sistema de Quests

```typescript
interface QuestSystem {
  // Estrutura da Quest
  mainQuest: {
    title: "O Estandarte da Guilda";
    objectives: QuestObjective[];
    reward: "Transformação em Condutor";
  };

  // Objetivos
  objectives: [
    {
      id: "talk_guide",
      description: "Fale com o Guia",
      type: "dialogue",
      target: "guide_npc",
      complete: false
    },
    {
      id: "get_plan",
      description: "Obtenha o plano do Escriba",
      type: "interaction",
      target: "scribe_npc",
      complete: false
    },
    {
      id: "execute_plan",
      description: "Execute com a Artesã",
      type: "creation",
      target: "artisan_npc",
      complete: false
    },
    {
      id: "review_work",
      description: "Refine com a Crítica",
      type: "refinement",
      target: "critic_npc",
      complete: false
    }
  ];

  // Tracking
  tracking: {
    currentObjective: number;
    completedObjectives: string[];
    questProgress: "linear" | "branching";
  };
}
```

### 4. Sistema de Criação (Hero Feature)

```typescript
interface CreationSystem {
  // O momento "UAU" - Artesã criando o estandarte
  visualCreation: {
    canvas: "Parede atrás da Artesã";
    method: "Pixel por pixel";
    timing: "3-5 segundos";
    effects: "Partículas, brilho, som";
  };

  // Elementos criados
  createdElements: {
    background: "Gradiente animado";
    centerPiece: "Estrela dourada";
    text: "Aparece letra por letra";
    polish: "Efeitos de brilho final";
  };

  // Feedback
  feedback: {
    npcReaction: "Orgulho visível";
    playerNotification: "Item criado!";
    visualPersistence: "Estandarte fica visível";
  };
}
```

### 5. Sistema de Refinamento (Ciclo de Feedback)

```typescript
interface RefinementSystem {
  // Feedback da Crítica
  critiqueMechanic: {
    analysis: "Animação de inspeção";
    feedback: "Sugestões específicas";
    choice: "Aceitar ou manter original";
  };

  // Ciclo iterativo
  iterationCycle: {
    steps: [
      "Receber feedback",
      "Voltar ao Escriba",
      "Atualizar plano",
      "Retornar à Artesã",
      "Aplicar mudanças",
      "Validar com Crítica"
    ];
  };

  // Aprendizado
  lessonTaught: "Importância da iteração e melhoria contínua";
}
```

---

## 🏆 Progressão e Recompensas

### Sistema de Transformação

```typescript
interface ProgressionSystem {
  // Estados do jogador
  playerStates: {
    initial: "Iniciado";
    learning: "Aprendiz";
    practicing: "Praticante";
    final: "Condutor";
  };

  // Transformação final
  transformation: {
    trigger: "Quest completa";
    visuals: [
      "Nova roupa/badge",
      "Aura dourada",
      "Título sobre o avatar"
    ];
    unlocks: [
      "Modo Mundo Aberto",
      "Todos os agentes",
      "Projetos customizados"
    ];
  };

  // Celebração
  celebration: {
    estandartePlacement: "Sobe ao portão",
    npcGathering: "Todos se reúnem",
    gateOpening: "Portal para novo mundo",
    fanfare: "Música triunfante"
  };
}
```

---

## 📱 Design Mobile-First

### Layout Responsivo

```typescript
interface MobileDesign {
  // Orientação
  orientation: "Portrait preferencial";

  // UI Zones
  zones: {
    gameWorld: "70% superior";
    questTracker: "Overlay compacto";
    chatModal: "60% inferior quando ativo";
  };

  // Touch targets
  touchTargets: {
    minimumSize: "44x44px";
    spacing: "8px entre elementos";
    feedback: "Haptic em interações";
  };

  // Gestos
  gestures: {
    tap: "Mover/Interagir";
    pinch: "Zoom (opcional)";
    swipe: "Dismiss modal";
    hold: "Mais informações";
  };
}
```

### Performance

```typescript
interface PerformanceTargets {
  fps: {
    target: 60;
    minimum: 30;
    degradation: "Reduz partículas primeiro";
  };

  loading: {
    initial: "< 3 segundos";
    assets: "Lazy loading";
    transitions: "< 300ms";
  };

  memory: {
    target: "< 100MB";
    optimization: "Sprite atlases";
    cleanup: "Aggressive GC";
  };
}
```

---

## 🎨 Direção de Arte

### Estilo Visual

```typescript
interface ArtDirection {
  // Estética geral
  style: "Medieval-fantástico com toques modernos";

  // Paleta de cores
  colors: {
    primary: "#FFD700";     // Dourado (sucesso, importante)
    secondary: "#4A90E2";   // Azul (informação)
    tertiary: "#7B68EE";    // Roxo (mágico)
    neutral: "#F5F5F5";     // Backgrounds
    dark: "#2C3E50";        // Textos
  };

  // Ambiente
  lighting: {
    ambient: "Quente e acolhedor";
    spotlights: "Direcionam atenção";
    particles: "Poeira mágica flutuante";
  };

  // NPCs
  characterDesign: {
    style: "Low poly ou pixel art";
    animations: "Idle, talking, working";
    expressions: "Feliz, concentrado, orgulhoso";
  };
}
```

---

## 🔊 Design de Som

### Paisagem Sonora

```typescript
interface SoundDesign {
  // Música
  music: {
    ambient: "Orquestral suave";
    working: "Uptempo sutil";
    success: "Fanfarra triunfante";
    volume: "0.3 default";
  };

  // Efeitos sonoros
  sfx: {
    footsteps: "Passos no salão";
    npcGreeting: "Sino suave";
    creation: "Martelo + mágica";
    complete: "Harpa ascendente";
    transformation: "Crescendo épico";
  };

  // Vozes (opcional)
  voices: {
    type: "Gibberish ou grunts";
    emotion: "Reflete personalidade";
    frequency: "Início de diálogos apenas";
  };
}
```

---

## 🎯 Fluxo de Jogo Completo

### Timeline de 10 minutos

```
00:00 - 01:00: Introdução e encontro com Guia
01:00 - 03:00: Interação com Escriba, criação do plano
03:00 - 05:00: Artesã executa o plano (MOMENTO HERO)
05:00 - 07:00: Crítica analisa e sugere melhorias
07:00 - 08:00: Ciclo de refinamento
08:00 - 10:00: Conclusão épica e transformação
```

### Pontos de Decisão

1. **Escolha do design do estandarte** (com Escriba)
2. **Aceitar ou rejeitar feedback** (com Crítica)
3. **Explorar mundo aberto ou rejogar** (final)

---

## 🎮 Controles Completos

### Mobile/Tablet
- **Tap**: Mover avatar ou interagir com NPC
- **Tap no NPC**: Abrir diálogo
- **Tap em opção**: Selecionar resposta
- **Swipe down**: Fechar modal
- **Pinch**: Zoom no mapa (opcional)

### Desktop (Suporte)
- **Click**: Mesmo que tap
- **ESC**: Fechar modais
- **WASD**: Movimento alternativo
- **Space**: Interagir com NPC próximo
- **1-4**: Selecionar opções de diálogo

---

## 📊 Métricas e Analytics

### Eventos para Tracking

```typescript
interface Analytics {
  criticalEvents: [
    "game_start",
    "first_npc_interaction",
    "plan_created",
    "banner_created",
    "feedback_received",
    "refinement_accepted",
    "quest_complete",
    "transformation_achieved"
  ];

  metrics: {
    completionRate: ">85%";
    averageTime: "8-12 minutos";
    refinementAcceptance: ">70%";
    conversionToOpenWorld: ">30%";
  };
}
```

---

## 🚀 Expansões Futuras

### Modo Mundo Aberto
- Criar projetos próprios
- Invocar qualquer agente
- Múltiplas quests paralelas
- Sistema de reputação

### Multiplayer Assíncrono
- Ver criações de outros jogadores
- Deixar feedback nas criações
- Ranking de melhores estandartes
- Guilds colaborativas

### Conteúdo Adicional
- Novas profissões (NPCs)
- Quests temáticas
- Eventos sazonais
- Customização de avatar

---

## 💡 Unique Selling Points

1. **Ensina um produto real** através de gameplay
2. **Narrativa com propósito** - cada elemento tem função pedagógica
3. **Momento "UAU" visual** - criação em tempo real
4. **Ciclo de feedback gamificado** - iteração como mecânica
5. **Transformação significativa** - de Iniciado a Condutor

---

*"Conductor Quest não é apenas um jogo - é uma experiência transformadora que ensina o poder da orquestração criativa."* 🎮✨