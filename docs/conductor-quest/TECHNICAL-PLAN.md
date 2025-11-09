# 📋 Plano Técnico - Conductor Quest MVP

## 🎯 Escopo do MVP

### O que VAMOS construir
- Nova rota `/quest` (mobile/tablet first)
- Onboarding gamificado fixo (10-15 min)
- 5 NPCs pré-definidos
- Sistema de diálogos branching
- Quest tracker com XP
- Boss battle simplificada
- Auto-save local

### O que NÃO vamos construir (agora)
- Editor de NPCs
- Multiplayer real-time
- Customização profunda
- Sistema econômico
- User accounts/cloud save

## 🏗️ Arquitetura

### Estrutura de Componentes

```
conductor-web/src/app/
├── quest-adventure/
│   ├── quest-adventure.component.ts       # Página principal
│   ├── quest-adventure.component.html
│   ├── quest-adventure.component.css
│   ├── quest-adventure.module.ts
│   │
│   ├── components/
│   │   ├── quest-canvas/
│   │   │   ├── quest-canvas.component.ts  # Extends AgentGameComponent
│   │   │   └── quest-canvas.component.html
│   │   │
│   │   ├── quest-chat-modal/
│   │   │   ├── quest-chat-modal.component.ts  # Adapta ConductorChat
│   │   │   ├── quest-chat-modal.component.html
│   │   │   └── quest-chat-modal.component.css
│   │   │
│   │   ├── quest-tracker/
│   │   │   ├── quest-tracker.component.ts  # Adapta GamifiedPanel
│   │   │   └── quest-tracker.component.html
│   │   │
│   │   ├── boss-battle/
│   │   │   ├── boss-battle.component.ts
│   │   │   └── boss-battle.component.html
│   │   │
│   │   └── quest-inventory/
│   │       └── quest-inventory.component.ts
│   │
│   ├── services/
│   │   ├── quest-state.service.ts         # Estado global da quest
│   │   ├── npc-manager.service.ts         # Gerencia NPCs
│   │   ├── dialogue.service.ts            # Sistema de diálogos
│   │   ├── player-movement.service.ts     # Movimento do avatar
│   │   ├── quest-progression.service.ts   # Lógica de progressão
│   │   ├── quest-sound.service.ts         # Sons e música
│   │   └── quest-save.service.ts          # Auto-save
│   │
│   ├── models/
│   │   ├── quest.model.ts
│   │   ├── npc.model.ts
│   │   ├── dialogue.model.ts
│   │   └── player.model.ts
│   │
│   └── data/
│       ├── npcs.json                      # Configuração dos NPCs
│       ├── dialogues.json                 # Árvore de diálogos
│       └── quests.json                    # Definição das quests
```

## 📊 Modelos de Dados

### Quest Model
```typescript
interface Quest {
  id: string;
  title: string;
  description: string;
  tasks: QuestTask[];
  rewards: QuestReward;
  status: 'locked' | 'active' | 'completed';
  requiredLevel?: number;
  nextQuest?: string;
}

interface QuestTask {
  id: string;
  text: string;
  completed: boolean;
  action: 'talk' | 'summon' | 'collect' | 'defeat';
  target?: string;
}

interface QuestReward {
  xp: number;
  items?: string[];
  unlocks?: string[];
  achievement?: string;
}
```

### NPC Model
```typescript
interface NPC {
  id: string;
  name: string;
  emoji: string;
  agentId: string;           // Conductor agent ID
  position: Position;
  sprite: SpriteName;
  unlockCondition?: string;
  status: 'locked' | 'available' | 'busy' | 'completed';
  dialogueTree: string;       // Reference to dialogue ID
  personality: NPCPersonality;
}

interface NPCPersonality {
  greeting: string;
  idle: string[];
  working: string[];
  success: string;
  failure: string;
}
```

### Dialogue Model
```typescript
interface DialogueTree {
  id: string;
  nodes: DialogueNode[];
}

interface DialogueNode {
  id: string;
  speaker: 'npc' | 'player';
  text: string;
  options?: DialogueOption[];
  next?: string;
  action?: DialogueAction;
}

interface DialogueOption {
  text: string;
  next: string;
  condition?: string;
  xp?: number;
  flag?: string;
}

interface DialogueAction {
  type: 'unlock' | 'give_item' | 'complete_task' | 'trigger_event';
  target: string;
  value?: any;
}
```

### Player State
```typescript
interface PlayerState {
  position: Position;
  level: number;
  xp: number;
  xpToNextLevel: number;
  inventory: string[];
  unlockedNPCs: string[];
  completedQuests: string[];
  currentQuest: string;
  dialogueFlags: Record<string, boolean>;
  achievements: string[];
  statistics: PlayerStats;
}

interface PlayerStats {
  totalPlayTime: number;
  npcsInteracted: number;
  questsCompleted: number;
  bugsDefeated: number;
  codeGenerated: number;
}
```

## 🔄 Fluxo de Implementação (6 Semanas)

### Semana 1: Setup Base
- [x] Criar estrutura de pastas
- [ ] Setup routing para /quest
- [ ] Criar componente principal
- [ ] Configurar NPCs fixos (JSON)
- [ ] Implementar quest state service
- [ ] Setup localStorage save

### Semana 2: Canvas Interativo
- [ ] Adaptar AgentGameComponent
- [ ] Adicionar avatar do player
- [ ] Implementar movimento (click/touch)
- [ ] Desenhar NPCs no mapa
- [ ] Adicionar visual de reino destruído
- [ ] Pathfinding básico

### Semana 3: Sistema de Diálogos
- [ ] Criar chat modal estilizado
- [ ] Implementar dialogue tree parser
- [ ] Sistema de opções de resposta
- [ ] Typing animation
- [ ] Integração com agentes (opcional)
- [ ] Dialogue history/memory

### Semana 4: Quest System
- [ ] Quest tracker UI
- [ ] Sistema de tarefas
- [ ] XP e níveis
- [ ] Desbloqueio progressivo
- [ ] Quest completion logic
- [ ] Achievements básicos

### Semana 5: Polish e Feedback
- [ ] Animações (partículas, level up)
- [ ] Sistema de som básico
- [ ] Efeitos visuais (glow, shake)
- [ ] Transições suaves
- [ ] Loading states
- [ ] Error handling

### Semana 6: Boss Battle e Finalização
- [ ] Boss battle UI
- [ ] Lógica de combate simples
- [ ] Cutscenes básicas
- [ ] Victory celebration
- [ ] End game screen
- [ ] Testing e bugs

## 🔧 Componentes Reutilizados

### Do Sistema Atual

| Componente Original | Uso no Quest | Modificações |
|-------------------|--------------|--------------|
| AgentGameComponent | Base do canvas | Adicionar player, NPCs fixos |
| ConductorChatComponent | Chat com NPCs | Estilizar como pergaminho |
| GamifiedPanelComponent | Quest tracker | Mostrar objetivos e XP |
| EventTickerComponent | Battle log | Mostrar ações da batalha |
| AgentMetricsService | Player stats | Adaptar para XP/Level |
| GamificationEventsService | Quest events | Eventos de progressão |
| AgentExecutionService | NPC responses | Executar agentes reais (opcional) |

## 💾 Estrutura de Dados (localStorage)

```json
{
  "quest_save_v1": {
    "version": "1.0.0",
    "timestamp": 1700000000000,
    "player": {
      "position": { "x": 400, "y": 300 },
      "level": 3,
      "xp": 450,
      "inventory": ["requirements_doc", "test_potion"]
    },
    "quest": {
      "currentId": "learn_summoning",
      "currentStep": 2,
      "completedTasks": ["talk_elder", "summon_scribe"],
      "completedQuests": ["awakening"]
    },
    "npcs": {
      "elder_guide": {
        "unlocked": true,
        "interactionCount": 3,
        "lastDialogue": "quest_start"
      },
      "requirements_scribe": {
        "unlocked": true,
        "interactionCount": 1,
        "lastDialogue": "analysis_complete"
      }
    },
    "flags": {
      "hasSeenIntro": true,
      "knowsAboutBug": true,
      "choseAggressiveApproach": false
    }
  }
}
```

## 🎮 Configurações e Feature Flags

```typescript
// quest.config.ts
export const QUEST_CONFIG = {
  // Development
  DEBUG_MODE: !environment.production,
  SKIP_INTRO: false,
  SHOW_FPS: false,
  SHOW_COLLISION_BOXES: false,

  // Features
  USE_REAL_AGENTS: false,        // Use real Conductor agents
  ENABLE_SOUND: true,
  ENABLE_PARTICLES: true,
  ENABLE_BOSS_BATTLE: true,
  ENABLE_AUTO_SAVE: true,

  // Gameplay
  PLAYER_MOVE_SPEED: 200,        // pixels per second
  DIALOGUE_TYPE_SPEED: 50,       // ms per character
  AUTO_SAVE_INTERVAL: 30000,     // 30 seconds
  XP_PER_LEVEL: [
    0,     // Level 1
    100,   // Level 2
    300,   // Level 3
    600,   // Level 4
    1000,  // Level 5
  ],

  // Canvas
  CANVAS_WIDTH: 1024,
  CANVAS_HEIGHT: 768,
  MOBILE_CANVAS_SCALE: 1.0,
  TABLET_CANVAS_SCALE: 1.0,

  // NPCs
  NPC_INTERACTION_RANGE: 50,     // pixels
  NPC_INDICATOR_SIZE: 20,        // "!" size

  // Assets paths
  ASSETS_BASE: '/assets/quest/',
  SPRITES_PATH: '/assets/quest/sprites/',
  SOUNDS_PATH: '/assets/quest/sounds/',
  MUSIC_PATH: '/assets/quest/music/'
};
```

## 📱 Otimizações Mobile/Tablet

### Responsive Breakpoints
```css
/* Mobile (< 768px) */
@media (max-width: 767px) {
  .quest-canvas { touch-action: none; }
  .quest-chat-modal { height: 70vh; }
  .quest-tracker { font-size: 12px; }
}

/* Tablet (768px - 1024px) */
@media (min-width: 768px) and (max-width: 1024px) {
  .quest-chat-modal { width: 60%; height: 50vh; }
  .quest-tracker { position: fixed; top: 20px; }
}

/* Desktop (> 1024px) */
@media (min-width: 1025px) {
  .quest-container { max-width: 1200px; margin: 0 auto; }
}
```

### Touch Controls
```typescript
// Touch event handlers
@HostListener('touchstart', ['$event'])
onTouchStart(event: TouchEvent) {
  this.handlePlayerMove(event.touches[0]);
}

@HostListener('touchmove', ['$event'])
onTouchMove(event: TouchEvent) {
  event.preventDefault(); // Prevent scrolling
  this.updateMoveTarget(event.touches[0]);
}
```

## 🚀 Deployment Checklist

### Pre-Launch
- [ ] Comprimir todos os assets (sprites, sons)
- [ ] Minificar JSONs de configuração
- [ ] Implementar lazy loading da rota
- [ ] Adicionar analytics básico
- [ ] Testar em dispositivos reais
- [ ] Verificar performance (FPS > 30)
- [ ] Implementar error boundaries
- [ ] Criar fallbacks para assets faltando

### Performance Targets
- **Initial Load**: < 3 segundos
- **FPS**: > 30 em dispositivos médios
- **Memory**: < 100MB de uso
- **Battery**: < 10% drain em 30 min

### Analytics Events
```typescript
// Eventos principais para tracking
{
  "quest_start": {},
  "npc_interaction": { "npc_id": "elder_guide" },
  "quest_task_complete": { "task_id": "talk_elder" },
  "quest_complete": { "quest_id": "awakening", "time": 600 },
  "level_up": { "new_level": 2 },
  "boss_defeated": { "attempts": 1 },
  "game_complete": { "total_time": 900 }
}
```

## 🔐 Considerações de Segurança

- Todo estado é client-side (não há backend específico)
- Não armazenar dados sensíveis
- Validar todos os inputs do usuário
- Sanitizar conteúdo de diálogos
- Rate limiting em chamadas aos agentes
- Prevenir XSS em chat modal

## 📊 Métricas de Sucesso do MVP

| Métrica | Target | Como Medir |
|---------|--------|------------|
| Completion Rate | >70% | Analytics |
| Tempo Médio | 12 min | Analytics |
| FPS Médio | >30 | Performance API |
| Crash Rate | <1% | Error tracking |
| Load Time | <3s | Performance API |
| Satisfação | >4.5/5 | Feedback form |

---

## 🎯 Resultado Esperado

Um MVP funcional que:
1. Roda suavemente em mobile/tablet
2. Ensina Conductor de forma divertida
3. Pode ser usado no vídeo promocional
4. Serve como base para expansão futura
5. Reutiliza máximo de código existente

**Tempo Total Estimado: 6 semanas** com 1-2 desenvolvedores.