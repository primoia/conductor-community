# 🛠️ Guia de Implementação - Conductor Quest

## 📋 Pré-requisitos

- Angular 16+ configurado
- Node.js 18+
- Acesso ao código fonte do conductor-web
- Conhecimento básico de TypeScript e Angular

## 🚀 Quick Start

### 1. Criar a estrutura base

```bash
# Na pasta conductor-web
cd src/app

# Criar módulo da quest
ng generate module quest-adventure --routing
ng generate component quest-adventure/quest-adventure
```

### 2. Configurar roteamento

```typescript
// app-routing.module.ts
const routes: Routes = [
  // ... outras rotas
  {
    path: 'quest',
    loadChildren: () => import('./quest-adventure/quest-adventure.module')
      .then(m => m.QuestAdventureModule)
  }
];
```

## 📁 Estrutura de Arquivos

### Criar a seguinte estrutura:

```
src/app/quest-adventure/
├── components/
│   ├── quest-canvas/
│   ├── quest-chat-modal/
│   ├── quest-tracker/
│   └── boss-battle/
├── services/
├── models/
├── data/
│   ├── npcs.json
│   ├── dialogues.json
│   └── quests.json
└── assets/
    └── quest/
        ├── sprites/
        ├── sounds/
        └── music/
```

## 🎮 Implementação Passo a Passo

### PASSO 1: Componente Principal

```typescript
// quest-adventure.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { QuestStateService } from './services/quest-state.service';

@Component({
  selector: 'app-quest-adventure',
  template: `
    <div class="quest-container" [class.mobile]="isMobile">
      <!-- Canvas Principal -->
      <app-quest-canvas
        [npcs]="npcs$ | async"
        [player]="player$ | async"
        (onNpcInteract)="handleNpcInteract($event)"
        (onPlayerMove)="handlePlayerMove($event)">
      </app-quest-canvas>

      <!-- Quest Tracker -->
      <app-quest-tracker
        [quest]="currentQuest$ | async"
        [tasks]="questTasks$ | async">
      </app-quest-tracker>

      <!-- Chat Modal -->
      <app-quest-chat-modal
        *ngIf="activeDialogue$ | async as dialogue"
        [npc]="dialogue.npc"
        [options]="dialogue.options"
        (onOptionSelect)="handleDialogueChoice($event)"
        (onClose)="closeDialogue()">
      </app-quest-chat-modal>

      <!-- Boss Battle (quando ativo) -->
      <app-boss-battle
        *ngIf="bossActive$ | async"
        [boss]="boss$ | async"
        [party]="party$ | async"
        (onAction)="handleBattleAction($event)"
        (onVictory)="handleVictory()">
      </app-boss-battle>
    </div>
  `,
  styleUrls: ['./quest-adventure.component.scss']
})
export class QuestAdventureComponent implements OnInit, OnDestroy {
  // Observables
  npcs$ = this.questState.npcs$;
  player$ = this.questState.player$;
  currentQuest$ = this.questState.currentQuest$;

  constructor(
    private questState: QuestStateService
  ) {}

  ngOnInit() {
    this.questState.initializeQuest();
  }

  handleNpcInteract(npcId: string) {
    this.questState.interactWithNpc(npcId);
  }

  handlePlayerMove(position: Position) {
    this.questState.movePlayer(position);
  }
}
```

### PASSO 2: Adaptar o Canvas Existente

```typescript
// quest-canvas.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';
import { AgentGameComponent } from '../../living-screenplay-simple/agent-game/agent-game.component';

@Component({
  selector: 'app-quest-canvas',
  template: `
    <canvas #gameCanvas
            class="quest-canvas"
            (click)="handleCanvasClick($event)"
            (touchstart)="handleTouchStart($event)">
    </canvas>
  `
})
export class QuestCanvasComponent extends AgentGameComponent {
  @Input() npcs: NPC[] = [];
  @Input() player: Player;
  @Output() onNpcInteract = new EventEmitter<string>();
  @Output() onPlayerMove = new EventEmitter<Position>();

  private playerSprite: HTMLImageElement;
  private npcSprites: Map<string, HTMLImageElement> = new Map();

  override ngAfterViewInit() {
    super.ngAfterViewInit();
    this.initQuestMode();
    this.loadSprites();
  }

  private initQuestMode() {
    // Desabilita features não necessárias do AgentGame
    this.showDebugPanel = false;
    this.viewMode = 'fixed';
    this.filters.showInstances = false;

    // Adiciona visual do reino
    this.drawKingdom();
  }

  private drawKingdom() {
    // Fundo destruído
    this.ctx.fillStyle = 'rgba(50, 50, 50, 0.3)';
    this.ctx.fillRect(0, 0, this.canvasWidth, this.canvasHeight);

    // Desenha ruínas
    this.drawRuins();

    // Desenha NPCs
    this.npcs.forEach(npc => this.drawNPC(npc));

    // Desenha player
    if (this.player) {
      this.drawPlayer();
    }
  }

  private drawPlayer() {
    const { x, y } = this.player.position;

    // Sprite ou emoji fallback
    if (this.playerSprite) {
      this.ctx.drawImage(this.playerSprite, x - 16, y - 16, 32, 32);
    } else {
      this.ctx.font = '24px Arial';
      this.ctx.fillText('🧙', x - 12, y + 6);
    }

    // Nome do player
    this.ctx.fillStyle = 'white';
    this.ctx.font = '10px Arial';
    this.ctx.fillText('You', x - 10, y - 20);
  }

  handleCanvasClick(event: MouseEvent) {
    const rect = this.canvasRef.nativeElement.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Verifica se clicou em NPC
    const clickedNpc = this.getNpcAtPosition({ x, y });
    if (clickedNpc) {
      this.onNpcInteract.emit(clickedNpc.id);
    } else {
      // Move player
      this.onPlayerMove.emit({ x, y });
      this.animatePlayerMovement({ x, y });
    }
  }

  private animatePlayerMovement(target: Position) {
    // Anima movimento suave do player
    const steps = 30;
    const dx = (target.x - this.player.position.x) / steps;
    const dy = (target.y - this.player.position.y) / steps;

    let step = 0;
    const animate = () => {
      if (step < steps) {
        this.player.position.x += dx;
        this.player.position.y += dy;
        step++;
        requestAnimationFrame(animate);
      }
    };
    animate();
  }
}
```

### PASSO 3: Sistema de Estado

```typescript
// quest-state.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class QuestStateService {
  // Estado principal
  private state = {
    player: {
      position: { x: 400, y: 500 },
      level: 1,
      xp: 0,
      inventory: []
    },
    npcs: this.loadNPCs(),
    currentQuest: 'awakening',
    questProgress: {
      awakening: {
        currentTask: 0,
        completed: false
      }
    },
    dialogueFlags: {},
    unlockedNpcs: ['elder_guide']
  };

  // Observables
  private stateSubject = new BehaviorSubject(this.state);

  player$ = this.stateSubject.pipe(
    map(state => state.player)
  );

  npcs$ = this.stateSubject.pipe(
    map(state => state.npcs.filter(npc =>
      state.unlockedNpcs.includes(npc.id)
    ))
  );

  constructor() {
    this.loadSavedState();
  }

  initializeQuest() {
    // Verifica se é primeira vez
    const saved = localStorage.getItem('quest_save');
    if (!saved) {
      this.startNewQuest();
    }
  }

  private startNewQuest() {
    // Reset estado
    this.state.player.level = 1;
    this.state.player.xp = 0;
    this.state.currentQuest = 'awakening';

    // Salva
    this.saveState();

    // Inicia primeira cutscene
    this.playIntro();
  }

  movePlayer(position: Position) {
    this.state.player.position = position;
    this.updateState();

    // Verifica proximidade com NPCs
    this.checkNearbyNpcs(position);
  }

  interactWithNpc(npcId: string) {
    const npc = this.state.npcs.find(n => n.id === npcId);
    if (!npc) return;

    // Abre diálogo
    this.openDialogue(npc);

    // Marca como interagido
    this.state.dialogueFlags[`talked_to_${npcId}`] = true;

    // Verifica progressão de quest
    this.checkQuestProgress();
  }

  private checkQuestProgress() {
    const quest = this.getCurrentQuest();
    const task = quest.tasks[quest.currentTask];

    if (task.type === 'talk' &&
        this.state.dialogueFlags[task.flag]) {
      this.completeTask(task);
    }
  }

  private saveState() {
    const saveData = {
      version: '1.0.0',
      timestamp: Date.now(),
      state: this.state
    };
    localStorage.setItem('quest_save', JSON.stringify(saveData));
  }

  private loadSavedState() {
    const saved = localStorage.getItem('quest_save');
    if (saved) {
      const data = JSON.parse(saved);
      this.state = data.state;
      this.updateState();
    }
  }
}
```

### PASSO 4: Chat Modal Adaptado

```typescript
// quest-chat-modal.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-quest-chat-modal',
  template: `
    <div class="quest-chat-overlay" (click)="onOverlayClick($event)">
      <div class="quest-chat-modal" #modalContent>
        <!-- Header -->
        <div class="chat-header">
          <span class="npc-emoji">{{ npc.emoji }}</span>
          <h3 class="npc-name">{{ npc.name }}</h3>
          <button class="close-btn" (click)="onClose.emit()">×</button>
        </div>

        <!-- Messages -->
        <div class="chat-messages" #messagesContainer>
          <div *ngFor="let msg of messages"
               class="message"
               [class.npc]="msg.sender === 'npc'"
               [class.player]="msg.sender === 'player'"
               [@messageAnimation]>
            <span class="speaker">{{ msg.sender === 'npc' ? npc.name : 'You' }}:</span>
            <span class="text" [innerHTML]="msg.text"></span>
          </div>

          <!-- Typing indicator -->
          <div class="typing-indicator" *ngIf="isTyping">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>

        <!-- Options -->
        <div class="chat-options" *ngIf="currentOptions && !isTyping">
          <button *ngFor="let option of currentOptions"
                  class="option-button"
                  (click)="selectOption(option)"
                  [@optionAnimation]>
            <span class="option-arrow">▶</span>
            <span class="option-text">{{ option.text }}</span>
            <span class="option-xp" *ngIf="option.xp">+{{ option.xp }} XP</span>
          </button>
        </div>
      </div>
    </div>
  `,
  styleUrls: ['./quest-chat-modal.component.scss'],
  animations: [
    trigger('messageAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(20px)' }),
        animate('300ms', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ]),
    trigger('optionAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateX(-20px)' }),
        animate('200ms {{ delay }}ms', style({ opacity: 1, transform: 'translateX(0)' }))
      ])
    ])
  ]
})
export class QuestChatModalComponent {
  @Input() npc: NPC;
  @Input() options: DialogueOption[];
  @Output() onOptionSelect = new EventEmitter<DialogueOption>();
  @Output() onClose = new EventEmitter<void>();

  messages: ChatMessage[] = [];
  currentOptions: DialogueOption[] = [];
  isTyping = false;

  ngOnInit() {
    this.startDialogue();
  }

  startDialogue() {
    // Mensagem inicial do NPC
    this.addNpcMessage(this.npc.greeting);

    // Mostra opções após delay
    setTimeout(() => {
      this.currentOptions = this.options;
    }, 1500);
  }

  selectOption(option: DialogueOption) {
    // Adiciona mensagem do player
    this.addPlayerMessage(option.text);

    // Limpa opções
    this.currentOptions = [];

    // Emite seleção
    this.onOptionSelect.emit(option);

    // Simula NPC pensando
    this.isTyping = true;

    // Resposta do NPC após delay
    setTimeout(() => {
      this.isTyping = false;
      this.processNpcResponse(option);
    }, 1000 + Math.random() * 1000);
  }

  private addNpcMessage(text: string) {
    this.messages.push({
      sender: 'npc',
      text: text,
      timestamp: Date.now()
    });
    this.scrollToBottom();
  }

  private addPlayerMessage(text: string) {
    this.messages.push({
      sender: 'player',
      text: text,
      timestamp: Date.now()
    });
    this.scrollToBottom();
  }
}
```

### PASSO 5: Quest Tracker

```typescript
// quest-tracker.component.ts
@Component({
  selector: 'app-quest-tracker',
  template: `
    <div class="quest-tracker" [@slideIn]>
      <!-- Quest Title -->
      <div class="quest-header">
        <span class="quest-icon">🎯</span>
        <h3 class="quest-title">{{ quest?.title }}</h3>
      </div>

      <!-- Progress Bar -->
      <div class="quest-progress">
        <div class="progress-bar">
          <div class="progress-fill"
               [style.width.%]="progressPercent"></div>
        </div>
        <span class="progress-text">{{ completedTasks }}/{{ totalTasks }}</span>
      </div>

      <!-- Tasks -->
      <div class="quest-tasks">
        <div *ngFor="let task of tasks"
             class="task-item"
             [class.completed]="task.completed"
             [@taskAnimation]>
          <span class="task-checkbox">
            {{ task.completed ? '✅' : '☐' }}
          </span>
          <span class="task-text">{{ task.text }}</span>
        </div>
      </div>

      <!-- XP Display -->
      <div class="xp-display">
        <span class="level">Lv.{{ playerLevel }}</span>
        <div class="xp-bar">
          <div class="xp-fill" [style.width.%]="xpPercent"></div>
        </div>
        <span class="xp-text">{{ currentXP }}/{{ nextLevelXP }} XP</span>
      </div>
    </div>
  `
})
export class QuestTrackerComponent {
  @Input() quest: Quest;
  @Input() tasks: QuestTask[];

  get progressPercent() {
    const completed = this.tasks.filter(t => t.completed).length;
    return (completed / this.tasks.length) * 100;
  }
}
```

### PASSO 6: Sistema de Diálogos

```typescript
// dialogue.service.ts
import { Injectable } from '@angular/core';
import dialoguesData from '../data/dialogues.json';

@Injectable({
  providedIn: 'root'
})
export class DialogueService {
  private dialogues = dialoguesData;

  getDialogue(npcId: string, dialogueId: string): DialogueNode {
    return this.dialogues[npcId]?.[dialogueId];
  }

  processDialogueChoice(npcId: string, choice: DialogueOption) {
    // Processa escolha e retorna próximo nó
    const nextNode = this.getDialogue(npcId, choice.next);

    // Aplica efeitos da escolha
    if (choice.action) {
      this.applyDialogueAction(choice.action);
    }

    // Dá XP se houver
    if (choice.xp) {
      this.grantXP(choice.xp);
    }

    return nextNode;
  }

  private applyDialogueAction(action: DialogueAction) {
    switch (action.type) {
      case 'unlock':
        this.unlockNPC(action.target);
        break;
      case 'give_item':
        this.giveItem(action.target);
        break;
      case 'complete_task':
        this.completeTask(action.target);
        break;
    }
  }
}
```

## 📦 Arquivos de Dados JSON

### npcs.json
```json
{
  "npcs": [
    {
      "id": "elder_guide",
      "name": "Elder Guide",
      "emoji": "🧙‍♂️",
      "agentId": "SystemGuide_Meta_Agent",
      "position": { "x": 400, "y": 300 },
      "sprite": "elder",
      "greeting": "Welcome, young Code Warrior!",
      "unlocked": true
    },
    {
      "id": "requirements_scribe",
      "name": "Requirements Scribe",
      "emoji": "📋",
      "agentId": "RequirementsAnalyst_Agent",
      "position": { "x": 200, "y": 200 },
      "sprite": "scribe",
      "greeting": "Let me analyze your needs.",
      "unlocked": false,
      "unlockCondition": "talked_to_elder"
    }
  ]
}
```

### dialogues.json
```json
{
  "elder_guide": {
    "initial": {
      "text": "Finally, you have awakened! Our kingdom needs you.",
      "options": [
        {
          "text": "What happened here?",
          "next": "explain_bug",
          "xp": 10
        },
        {
          "text": "How can I help?",
          "next": "explain_powers",
          "xp": 20
        }
      ]
    },
    "explain_bug": {
      "text": "A terrible bug has corrupted our main systems...",
      "options": [
        {
          "text": "I'll help rebuild everything!",
          "next": "teach_summoning",
          "xp": 30,
          "action": {
            "type": "unlock",
            "target": "requirements_scribe"
          }
        }
      ]
    }
  }
}
```

### quests.json
```json
{
  "quests": [
    {
      "id": "awakening",
      "title": "The Awakening",
      "description": "Learn the basics and save the kingdom",
      "tasks": [
        {
          "id": "talk_elder",
          "text": "Talk to the Elder Guide",
          "type": "talk",
          "target": "elder_guide",
          "completed": false
        },
        {
          "id": "summon_scribe",
          "text": "Summon Requirements Scribe",
          "type": "summon",
          "target": "requirements_scribe",
          "completed": false
        }
      ],
      "rewards": {
        "xp": 500,
        "unlocks": ["backend_knight"],
        "achievement": "first_quest"
      }
    }
  ]
}
```

## 🎨 Estilos SCSS

### quest-adventure.component.scss
```scss
.quest-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #1a1a2e, #0f0f1e);

  &.mobile {
    touch-action: none; // Previne scroll
  }
}

// Mobile first
.quest-tracker {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0, 0, 0, 0.8);
  border: 2px solid #gold;
  border-radius: 8px;
  padding: 12px;
  min-width: 250px;
  backdrop-filter: blur(10px);

  @media (max-width: 768px) {
    font-size: 12px;
    min-width: 200px;
  }
}

.quest-chat-modal {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60vh;
  background: url('/assets/quest/pergaminho.png');
  background-size: 100% 100%;
  padding: 20px;
  animation: slideUp 0.3s ease-out;

  @media (min-width: 768px) {
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    width: 500px;
    height: 400px;
    border-radius: 12px;
  }
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
```

## 🔧 Configurações

### environment.quest.ts
```typescript
export const questEnvironment = {
  // Feature flags
  useRealAgents: false,
  enableSound: true,
  enableParticles: true,
  skipIntro: false,

  // Gameplay
  playerSpeed: 200,
  dialogueSpeed: 50,
  autoSaveInterval: 30000,

  // Assets
  assetsPath: '/assets/quest/',

  // Analytics
  trackingEnabled: true,
  trackingId: 'UA-XXXXX'
};
```

## 🚀 Deploy

### Build para produção
```bash
# Build otimizado
ng build --configuration production

# Com service worker para offline
ng build --configuration production --service-worker
```

### Configuração nginx
```nginx
location /quest {
  try_files $uri $uri/ /index.html;

  # Cache assets
  location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
  }
}
```

## 🐛 Troubleshooting

### Problema: Canvas não renderiza em mobile
```typescript
// Adicionar no ngAfterViewInit
this.canvas.width = window.innerWidth;
this.canvas.height = window.innerHeight;

// Listener para resize
window.addEventListener('resize', () => {
  this.resizeCanvas();
});
```

### Problema: Touch não funciona
```typescript
// Adicionar touch handlers
@HostListener('touchstart', ['$event'])
handleTouchStart(e: TouchEvent) {
  e.preventDefault();
  const touch = e.touches[0];
  this.handleClick(touch.clientX, touch.clientY);
}
```

### Problema: Performance ruim
```typescript
// Otimizar render loop
private optimizedRender() {
  // Renderiza só o que mudou
  if (this.isDirty) {
    this.render();
    this.isDirty = false;
  }
  requestAnimationFrame(() => this.optimizedRender());
}
```

## ✅ Checklist de Implementação

- [ ] Setup inicial do módulo
- [ ] Canvas adaptado funcionando
- [ ] Sistema de movimento do player
- [ ] NPCs renderizados no mapa
- [ ] Chat modal estilizado
- [ ] Sistema de diálogos
- [ ] Quest tracker funcional
- [ ] Sistema de XP e níveis
- [ ] Salvamento local
- [ ] Sons básicos
- [ ] Animações e partículas
- [ ] Boss battle
- [ ] Tela de vitória
- [ ] Mobile responsive
- [ ] Performance otimizada

## 📈 Métricas para Acompanhar

```typescript
// analytics.service.ts
trackEvent('quest_start', { timestamp: Date.now() });
trackEvent('npc_interact', { npc_id: 'elder_guide' });
trackEvent('quest_complete', { quest_id: 'awakening', duration: 600 });
trackEvent('level_up', { new_level: 2 });
trackEvent('boss_defeated', { attempts: 1 });
```

---

**Pronto para implementar! 🚀**

Com este guia, você tem tudo necessário para construir o Conductor Quest MVP em 6 semanas.