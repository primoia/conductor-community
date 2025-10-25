# 🚀 Guia Rápido de Integração - Sistema de Conselheiros

> Copie e cole estes snippets para integrar o sistema de conselheiros rapidamente

---

## 1️⃣ Inicializar Scheduler (App Component)

**Arquivo:** `src/app/app.component.ts`

```typescript
import { Component, OnInit } from '@angular/core';
import { CouncilorSchedulerService } from './services/councilor-scheduler.service';

@Component({
  selector: 'app-root',
  template: `<router-outlet></router-outlet>`,
})
export class AppComponent implements OnInit {
  constructor(
    private councilorScheduler: CouncilorSchedulerService
  ) {}

  async ngOnInit() {
    // Inicializar sistema de conselheiros
    console.log('🏛️ Inicializando Conselho Municipal...');
    await this.councilorScheduler.initialize();
    console.log('✅ Conselho Municipal ativo');
  }
}
```

---

## 2️⃣ Adicionar Botão "Gerenciar Conselheiros" no Menu

**Arquivo:** `src/app/components/toolbar/toolbar.component.html`

```html
<!-- Adicionar ao menu existente -->
<button
  class="toolbar-btn"
  (click)="openCouncilorsDashboard()"
  title="Gerenciar Conselheiros"
>
  🏛️ Conselho
</button>
```

**Arquivo:** `src/app/components/toolbar/toolbar.component.ts`

```typescript
import { Component } from '@angular/core';
import { CouncilorsDashboardComponent } from '../living-screenplay-simple/councilors-dashboard/councilors-dashboard.component';
import { PromoteCouncilorModalComponent } from '../living-screenplay-simple/promote-councilor-modal/promote-councilor-modal.component';

@Component({
  selector: 'app-toolbar',
  templateUrl: './toolbar.component.html',
  styleUrls: ['./toolbar.component.css']
})
export class ToolbarComponent {
  showCouncilorsDashboard = false;
  showPromoteModal = false;
  selectedAgent: any;

  openCouncilorsDashboard() {
    this.showCouncilorsDashboard = true;
  }

  openPromoteModal(agent: any) {
    this.selectedAgent = agent;
    this.showPromoteModal = true;
  }

  async onPromote(request: any) {
    try {
      const response = await fetch(
        `/api/agents/${this.selectedAgent.agent_id}/promote-councilor`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request)
        }
      );

      const data = await response.json();

      if (data.success) {
        console.log('✅ Conselheiro promovido:', data.agent);
        this.showPromoteModal = false;

        // Recarregar conselheiros
        location.reload(); // ou recarregar via service
      }
    } catch (error) {
      console.error('❌ Erro ao promover:', error);
      alert('Erro ao promover conselheiro. Veja o console.');
    }
  }
}
```

**Template com modais:**

```html
<!-- No final do template -->

<!-- Dashboard de Conselheiros -->
<app-councilors-dashboard
  *ngIf="showCouncilorsDashboard"
  (close)="showCouncilorsDashboard = false"
  (promoteNew)="openPromoteModal(null)"
></app-councilors-dashboard>

<!-- Modal de Promoção -->
<app-promote-councilor-modal
  *ngIf="showPromoteModal"
  [agent]="selectedAgent"
  (promote)="onPromote($event)"
  (close)="showPromoteModal = false"
></app-promote-councilor-modal>
```

---

## 3️⃣ Adicionar Botão "Promover" no AgentGame (Context Menu)

**Arquivo:** `src/app/living-screenplay-simple/agent-game/agent-game.component.html`

```html
<!-- No context menu existente, adicionar opção -->
<div class="agent-context-menu" *ngIf="selectedAgent">
  <button (click)="onViewMetrics(selectedAgent)">📊 Ver Métricas</button>
  <button (click)="onTestAgent(selectedAgent)">🧪 Testar Agente</button>

  <!-- NOVO: Botão de promover -->
  <button
    *ngIf="!isCouncilor(selectedAgent)"
    (click)="onPromoteToCouncilor(selectedAgent)"
  >
    ⭐ Promover a Conselheiro
  </button>

  <button
    *ngIf="isCouncilor(selectedAgent)"
    (click)="onViewCouncilorConfig(selectedAgent)"
  >
    🏛️ Ver Configuração de Conselheiro
  </button>
</div>
```

**Arquivo:** `src/app/living-screenplay-simple/agent-game/agent-game.component.ts`

```typescript
// Adicionar ao componente
showPromoteModal = false;
selectedAgentForPromotion: any;

isCouncilor(agent: AgentCharacter): boolean {
  return agent.isCouncilor || false;
}

onPromoteToCouncilor(agent: AgentCharacter) {
  this.selectedAgentForPromotion = {
    agent_id: agent.agentId,
    name: agent.name,
    emoji: agent.emoji,
    description: `Agent ${agent.name}`
  };
  this.showPromoteModal = true;
}

onViewCouncilorConfig(agent: AgentCharacter) {
  // TODO: Abrir modal com configuração do conselheiro
  console.log('Ver configuração do conselheiro:', agent);
}

async onPromoteRequest(request: any) {
  try {
    const response = await fetch(
      `/api/agents/${this.selectedAgentForPromotion.agent_id}/promote-councilor`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }
    );

    const data = await response.json();

    if (data.success) {
      console.log('✅ Agente promovido a conselheiro');

      // Atualizar visual do agente
      const agent = this.agents.find(a => a.agentId === this.selectedAgentForPromotion.agent_id);
      if (agent) {
        agent.isCouncilor = true;
      }

      this.showPromoteModal = false;
    }
  } catch (error) {
    console.error('❌ Erro ao promover:', error);
  }
}
```

**Template (adicionar ao HTML):**

```html
<!-- Modal de promoção -->
<app-promote-councilor-modal
  *ngIf="showPromoteModal"
  [agent]="selectedAgentForPromotion"
  (promote)="onPromoteRequest($event)"
  (close)="showPromoteModal = false"
></app-promote-councilor-modal>
```

---

## 4️⃣ Marcar Agentes como Conselheiros ao Carregar

**Arquivo:** `src/app/living-screenplay-simple/agent-game/agent-game.component.ts`

No método `loadInstancesFromBackend()`:

```typescript
private async loadInstancesFromBackend(): Promise<void> {
  try {
    const instances = await this.agentService.loadAllInstances().toPromise();

    // Carregar lista de conselheiros
    const councilorIds = await this.loadCouncilorIds();

    for (const instance of instances || []) {
      // ... código existente ...

      this.agents.push({
        id: instance.instance_id,
        agentId: instance.agent_id,
        // ... outros campos ...

        // NOVO: Marcar se é conselheiro
        isCouncilor: councilorIds.has(instance.agent_id)
      });
    }
  } catch (error) {
    console.error('Erro ao carregar instâncias:', error);
  }
}

// NOVO: Método auxiliar
private async loadCouncilorIds(): Promise<Set<string>> {
  try {
    const response = await fetch('/api/agents?is_councilor=true');
    const data = await response.json();

    return new Set(data.agents?.map((a: any) => a.agent_id) || []);
  } catch (error) {
    console.warn('Falha ao carregar conselheiros:', error);
    return new Set();
  }
}
```

---

## 5️⃣ Mostrar KPI "Investigações Ativas" no Painel

**Arquivo:** `src/app/living-screenplay-simple/gamified-panel/gamified-panel.component.ts`

```typescript
import { CouncilorSchedulerService } from '../../services/councilor-scheduler.service';

export class GamifiedPanelComponent implements OnInit {
  activeInvestigations = 0;

  constructor(
    private councilorScheduler: CouncilorSchedulerService,
    // ... outros serviços
  ) {}

  ngOnInit() {
    // Subscribe para investigações ativas
    this.councilorScheduler.activeInvestigations$.subscribe(count => {
      this.activeInvestigations = count;
    });
  }
}
```

**Arquivo:** `src/app/living-screenplay-simple/gamified-panel/gamified-panel.component.html`

```html
<!-- Adicionar KPI -->
<div class="kpi-item">
  <span class="kpi-label">Investigações:</span>
  <span class="kpi-value">{{ activeInvestigations }}</span>
</div>
```

---

## 6️⃣ Criar Serviço Wrapper (Opcional)

**Arquivo:** `src/app/services/councilor-api.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { Observable, from } from 'rxjs';
import { PromoteToCouncilorRequest, AgentWithCouncilor } from '../models/councilor.types';

@Injectable({ providedIn: 'root' })
export class CouncilorApiService {
  private baseUrl = '/api';

  /**
   * Lista conselheiros ativos
   */
  listCouncilors(): Observable<AgentWithCouncilor[]> {
    return from(
      fetch(`${this.baseUrl}/agents?is_councilor=true`)
        .then(res => res.json())
        .then(data => data.agents || [])
    );
  }

  /**
   * Promove agente a conselheiro
   */
  promoteToCouncilor(
    agentId: string,
    request: PromoteToCouncilorRequest
  ): Observable<any> {
    return from(
      fetch(`${this.baseUrl}/agents/${agentId}/promote-councilor`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request)
      }).then(res => res.json())
    );
  }

  /**
   * Pausa conselheiro
   */
  pauseCouncilor(agentId: string): Observable<any> {
    return from(
      fetch(`${this.baseUrl}/agents/${agentId}/councilor-schedule`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: false })
      }).then(res => res.json())
    );
  }

  /**
   * Retoma conselheiro
   */
  resumeCouncilor(agentId: string): Observable<any> {
    return from(
      fetch(`${this.baseUrl}/agents/${agentId}/councilor-schedule`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: true })
      }).then(res => res.json())
    );
  }

  /**
   * Remove conselheiro
   */
  demoteCouncilor(agentId: string): Observable<any> {
    return from(
      fetch(`${this.baseUrl}/agents/${agentId}/demote-councilor`, {
        method: 'DELETE'
      }).then(res => res.json())
    );
  }
}
```

---

## 7️⃣ Imports Necessários no Module

**Arquivo:** `src/app/app.module.ts` (ou standalone imports)

```typescript
import { PromoteCouncilorModalComponent } from './living-screenplay-simple/promote-councilor-modal/promote-councilor-modal.component';
import { CouncilorsDashboardComponent } from './living-screenplay-simple/councilors-dashboard/councilors-dashboard.component';
import { CouncilorSchedulerService } from './services/councilor-scheduler.service';

@NgModule({
  declarations: [
    // ... outros componentes
  ],
  imports: [
    // ... outros imports
    PromoteCouncilorModalComponent,   // standalone
    CouncilorsDashboardComponent,     // standalone
  ],
  providers: [
    CouncilorSchedulerService,        // singleton
    // ... outros serviços
  ]
})
export class AppModule { }
```

---

## 8️⃣ Testar Localmente (Mock Backend)

**Arquivo:** `src/app/services/councilor-scheduler.service.ts`

Substituir temporariamente `loadCouncilorsFromBackend()`:

```typescript
private async loadCouncilorsFromBackend(): Promise<AgentWithCouncilor[]> {
  // MOCK: Retornar conselheiro de exemplo
  return [
    {
      _id: 'mock-id',
      agent_id: 'code_generator_agent',
      name: 'Code Generator',
      emoji: '🏗️',
      is_councilor: true,
      councilor_config: {
        title: 'Conselheiro de Arquitetura',
        schedule: {
          type: 'interval',
          value: '1m',
          enabled: true
        },
        task: {
          name: 'Verificar Arquivos Grandes',
          prompt: 'Liste arquivos com mais de 500 linhas',
          output_format: 'checklist'
        },
        notifications: {
          on_success: false,
          on_warning: true,
          on_error: true,
          channels: ['panel']
        }
      },
      customization: {
        enabled: true,
        display_name: 'Silva'
      },
      stats: {
        total_executions: 10,
        last_execution: new Date(),
        success_rate: 100
      }
    }
  ];
}
```

---

## 9️⃣ Checklist de Integração

- [ ] Adicionar `CouncilorSchedulerService` ao `app.component.ts`
- [ ] Adicionar botão "🏛️ Conselho" no menu
- [ ] Adicionar modal de promoção ao template principal
- [ ] Adicionar dashboard de conselheiros ao template
- [ ] Atualizar AgentGame para marcar `isCouncilor`
- [ ] Testar promoção de agente
- [ ] Testar pausa/retomada
- [ ] Testar remoção de conselheiro
- [ ] Verificar coroa dourada no AgentGame
- [ ] Verificar eventos no painel de gamificação

---

## 🔟 Solução de Problemas

### Erro: "CouncilorSchedulerService not found"

**Solução:** Importar no provider:

```typescript
import { CouncilorSchedulerService } from './services/councilor-scheduler.service';

providers: [CouncilorSchedulerService]
```

### Erro: "Cannot read property 'isCouncilor' of undefined"

**Solução:** Verificar se o campo foi adicionado ao criar o agente:

```typescript
this.agents.push({
  // ... campos existentes
  isCouncilor: false // adicionar este campo
});
```

### Coroa não aparece no AgentGame

**Solução:** Verificar se `renderAgent()` está sendo chamado e se `agent.isCouncilor === true`.

### Scheduler não executa tarefas

**Solução:** Verificar se `initialize()` foi chamado no `ngOnInit()` do AppComponent.

---

**Pronto!** 🎉 Sistema de Conselheiros integrado e funcionando.
