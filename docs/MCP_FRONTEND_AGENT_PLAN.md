# Plano Frontend: Agente x MCP

> **Data:** 2026-01-02
> **Status:** Planejado
> **Escopo:** Criação e edição de agentes com MCPs
> **Complementa:** [MCP_ON_DEMAND_PLAN.md](./MCP_ON_DEMAND_PLAN.md)

---

## 1. Objetivo

Implementar no frontend a vinculação de MCPs durante:
- **Criação** de novos agentes
- **Edição** de agentes existentes

---

## 2. Estado Atual

### 2.1 Arquivos Relevantes

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/agent.service.ts` | CRUD de agentes, descoberta de MCPs |
| `living-screenplay-simple/agent-creator/agent-creator.component.ts` | Formulário de criação |
| `living-screenplay-simple/agent-catalog/agent-catalog.component.ts` | Lista de agentes |

### 2.2 Interfaces Existentes

```typescript
// agent.service.ts
export interface MCPRegistryEntry {
  name: string;
  type: 'internal' | 'external';
  url: string;
  host_url?: string;
  status: 'healthy' | 'unhealthy' | 'unknown' | 'stopped' | 'starting';
  tools_count: number;
  docker_compose_path?: string;
  auto_shutdown_minutes?: number;
  last_used?: string;
  metadata?: {
    category?: string;
    description?: string;
  };
}

export interface Agent {
  id: string;
  name: string;
  emoji: string;
  description: string;
  mcp_configs?: string[];  // Lista de MCPs vinculados
  // ... outros campos
}
```

### 2.3 Métodos Existentes

| Método | Status | Uso |
|--------|--------|-----|
| `getAvailableMcps()` | Existe | Retorna `MCPRegistryEntry[]` |
| `createAgent()` | Existe | Inclui `mcp_configs` no payload |
| `updateAgent()` | **Falta** | Necessário para edição |

---

## 3. Cenário 1: Criação de Agente

### 3.1 Problemas Atuais

| Problema | Impacto |
|----------|---------|
| Não mostra status (healthy/stopped) | Usuário não sabe se MCP está ativo |
| Não mostra categoria | Lista longa sem organização |
| Não indica que MCPs stopped serão iniciados | Confusão |

### 3.2 Solução: Novo MCP Grid

**Arquivo:** `agent-creator.component.html`

```html
<div class="form-section mcp-section">
  <h3>MCPs (Ferramentas)</h3>
  <p class="section-hint">
    Selecione os MCPs que este agente poderá usar.
    <span class="stopped-hint">MCPs parados serão iniciados automaticamente.</span>
  </p>

  <!-- Filtros -->
  <div class="mcp-filters">
    <input
      type="text"
      [(ngModel)]="mcpFilter.search"
      (ngModelChange)="filterMcps()"
      placeholder="Buscar MCP..."
      class="mcp-search"
    />
    <select
      [(ngModel)]="mcpFilter.category"
      (ngModelChange)="filterMcps()"
      class="mcp-category-filter"
    >
      <option value="">Todas categorias</option>
      <option *ngFor="let cat of mcpCategories" [value]="cat">
        {{ cat | titlecase }}
      </option>
    </select>
    <select
      [(ngModel)]="mcpFilter.status"
      (ngModelChange)="filterMcps()"
      class="mcp-status-filter"
    >
      <option value="">Todos status</option>
      <option value="healthy">Ativos</option>
      <option value="stopped">Parados</option>
    </select>
  </div>

  <!-- Contador -->
  <div class="mcp-counter">
    {{ selectedMcps.length }} selecionado(s) de {{ filteredMcps.length }}
  </div>

  <!-- Grid -->
  <div class="mcp-grid">
    <div
      *ngFor="let mcp of filteredMcps"
      class="mcp-card"
      [class.selected]="isMcpSelected(mcp.name)"
      [class.stopped]="mcp.status === 'stopped'"
      (click)="toggleMcp(mcp)"
    >
      <span class="mcp-status-dot" [class]="mcp.status"></span>
      <span class="mcp-checkbox">{{ isMcpSelected(mcp.name) ? '✓' : '' }}</span>
      <div class="mcp-info">
        <span class="mcp-name">{{ mcp.name }}</span>
        <span class="mcp-category">{{ mcp.metadata?.category || 'other' }}</span>
      </div>
    </div>
  </div>

  <!-- Empty State -->
  <div *ngIf="filteredMcps.length === 0" class="mcp-empty">
    Nenhum MCP encontrado.
  </div>
</div>
```

### 3.3 Lógica do Componente

**Arquivo:** `agent-creator.component.ts`

```typescript
// Interfaces
interface McpFilter {
  search: string;
  category: string;
  status: string;
}

// Properties
availableMcps: MCPRegistryEntry[] = [];
filteredMcps: MCPRegistryEntry[] = [];
selectedMcps: string[] = [];
mcpFilter: McpFilter = { search: '', category: '', status: '' };
mcpCategories: string[] = [];

// Lifecycle
ngOnInit(): void {
  this.loadMcps();
}

// Methods
loadMcps(): void {
  this.agentService.getAvailableMcps().subscribe({
    next: (mcps) => {
      this.availableMcps = mcps;
      this.extractCategories();
      this.filterMcps();
    },
    error: (err) => console.error('Failed to load MCPs:', err)
  });
}

extractCategories(): void {
  const categories = new Set<string>();
  this.availableMcps.forEach(mcp => {
    if (mcp.metadata?.category) {
      categories.add(mcp.metadata.category);
    }
  });
  this.mcpCategories = Array.from(categories).sort();
}

filterMcps(): void {
  let result = [...this.availableMcps];

  if (this.mcpFilter.search) {
    const search = this.mcpFilter.search.toLowerCase();
    result = result.filter(mcp =>
      mcp.name.toLowerCase().includes(search)
    );
  }

  if (this.mcpFilter.category) {
    result = result.filter(mcp =>
      mcp.metadata?.category === this.mcpFilter.category
    );
  }

  if (this.mcpFilter.status) {
    result = result.filter(mcp => mcp.status === this.mcpFilter.status);
  }

  // Ordenar: selecionados primeiro
  result.sort((a, b) => {
    const aSelected = this.selectedMcps.includes(a.name);
    const bSelected = this.selectedMcps.includes(b.name);
    if (aSelected && !bSelected) return -1;
    if (!aSelected && bSelected) return 1;
    return a.name.localeCompare(b.name);
  });

  this.filteredMcps = result;
}

toggleMcp(mcp: MCPRegistryEntry): void {
  const index = this.selectedMcps.indexOf(mcp.name);
  if (index === -1) {
    this.selectedMcps.push(mcp.name);
  } else {
    this.selectedMcps.splice(index, 1);
  }
}

isMcpSelected(name: string): boolean {
  return this.selectedMcps.includes(name);
}

// No onCreate(), incluir MCPs
onCreate(): void {
  const agentData = {
    name: this.agentName,
    description: this.description,
    emoji: this.selectedEmoji,
    persona: this.persona,
    mcp_configs: [...this.selectedMcps],
    // ... outros campos
  };
  this.agentCreated.emit(agentData);
}
```

### 3.4 Estilos

**Arquivo:** `agent-creator.component.scss`

```scss
.mcp-section {
  .section-hint {
    color: var(--text-secondary);
    font-size: 0.85rem;
    margin-bottom: 1rem;

    .stopped-hint {
      display: block;
      font-style: italic;
      margin-top: 0.25rem;
    }
  }

  .mcp-filters {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;

    input, select {
      padding: 0.5rem;
      border: 1px solid var(--border-color);
      border-radius: 4px;
      background: var(--input-bg);
      color: var(--text-primary);
    }

    .mcp-search {
      flex: 1;
      min-width: 180px;
    }
  }

  .mcp-counter {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }

  .mcp-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 0.5rem;
    max-height: 280px;
    overflow-y: auto;
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
  }

  .mcp-card {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: var(--primary-color);
    }

    &.selected {
      border-color: var(--primary-color);
      background: var(--selected-bg);

      .mcp-checkbox {
        background: var(--primary-color);
        color: white;
      }
    }

    &.stopped {
      opacity: 0.7;
    }
  }

  .mcp-status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;

    &.healthy { background: #10b981; }
    &.stopped { background: #6b7280; }
    &.starting { background: #f59e0b; }
  }

  .mcp-checkbox {
    width: 18px;
    height: 18px;
    border: 1px solid var(--border-color);
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    flex-shrink: 0;
  }

  .mcp-info {
    flex: 1;
    min-width: 0;

    .mcp-name {
      display: block;
      font-weight: 500;
      font-size: 0.85rem;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .mcp-category {
      display: block;
      font-size: 0.65rem;
      color: var(--text-secondary);
      text-transform: uppercase;
    }
  }

  .mcp-empty {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
  }
}
```

---

## 4. Cenário 2: Edição de Agente

### 4.1 Problema

Não existe fluxo para editar MCPs de um agente já criado.

### 4.2 Solução

#### 4.2.1 Novo Endpoint Backend

```
PATCH /api/agents/{agentId}
Content-Type: application/json

{
  "mcp_configs": ["crm", "billing"]
}
```

**Resposta:**
```json
{
  "success": true,
  "agent": { "id": "...", "mcp_configs": ["crm", "billing"] }
}
```

#### 4.2.2 Novo Método no AgentService

**Arquivo:** `agent.service.ts`

```typescript
/**
 * Atualiza MCPs de um agente existente
 */
updateAgentMcpConfigs(agentId: string, mcpConfigs: string[]): Observable<Agent> {
  return from(
    fetch(`${this.gatewayUrl}/api/agents/${agentId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders()
      },
      body: JSON.stringify({ mcp_configs: mcpConfigs })
    })
  ).pipe(
    switchMap(response => {
      if (!response.ok) {
        throw new Error(`Failed to update agent: ${response.status}`);
      }
      return from(response.json());
    }),
    map((data: any) => data.agent as Agent)
  );
}
```

#### 4.2.3 Modal de Edição

**Criar:** `shared/agent-edit-modal/`

**Arquivo:** `agent-edit-modal.component.ts`

```typescript
import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { BaseModalComponent } from '../modals/base/base-modal.component';
import { AgentService, Agent, MCPRegistryEntry } from '../../services/agent.service';

@Component({
  selector: 'app-agent-edit-modal',
  templateUrl: './agent-edit-modal.component.html',
  styleUrls: ['./agent-edit-modal.component.scss']
})
export class AgentEditModalComponent extends BaseModalComponent implements OnInit {
  @Input() agent: Agent | null = null;
  @Output() agentUpdated = new EventEmitter<Agent>();

  availableMcps: MCPRegistryEntry[] = [];
  filteredMcps: MCPRegistryEntry[] = [];
  selectedMcps: string[] = [];
  mcpFilter = { search: '', category: '' };
  mcpCategories: string[] = [];

  isLoading = false;
  isSaving = false;
  error: string | null = null;

  private originalMcps: string[] = [];

  constructor(private agentService: AgentService) {
    super();
  }

  ngOnInit(): void {
    this.loadMcps();
  }

  protected override onModalOpened(): void {
    if (this.agent) {
      this.selectedMcps = [...(this.agent.mcp_configs || [])];
      this.originalMcps = [...this.selectedMcps];
    }
  }

  get hasChanges(): boolean {
    return JSON.stringify([...this.selectedMcps].sort()) !==
           JSON.stringify([...this.originalMcps].sort());
  }

  loadMcps(): void {
    this.isLoading = true;
    this.agentService.getAvailableMcps().subscribe({
      next: (mcps) => {
        this.availableMcps = mcps;
        this.extractCategories();
        this.filterMcps();
        this.isLoading = false;
      },
      error: () => {
        this.error = 'Falha ao carregar MCPs';
        this.isLoading = false;
      }
    });
  }

  extractCategories(): void {
    const categories = new Set<string>();
    this.availableMcps.forEach(mcp => {
      if (mcp.metadata?.category) categories.add(mcp.metadata.category);
    });
    this.mcpCategories = Array.from(categories).sort();
  }

  filterMcps(): void {
    let result = [...this.availableMcps];

    if (this.mcpFilter.search) {
      const search = this.mcpFilter.search.toLowerCase();
      result = result.filter(mcp => mcp.name.toLowerCase().includes(search));
    }

    if (this.mcpFilter.category) {
      result = result.filter(mcp => mcp.metadata?.category === this.mcpFilter.category);
    }

    result.sort((a, b) => {
      const aSelected = this.selectedMcps.includes(a.name);
      const bSelected = this.selectedMcps.includes(b.name);
      if (aSelected && !bSelected) return -1;
      if (!aSelected && bSelected) return 1;
      return a.name.localeCompare(b.name);
    });

    this.filteredMcps = result;
  }

  toggleMcp(mcp: MCPRegistryEntry): void {
    const index = this.selectedMcps.indexOf(mcp.name);
    if (index === -1) {
      this.selectedMcps.push(mcp.name);
    } else {
      this.selectedMcps.splice(index, 1);
    }
  }

  isMcpSelected(name: string): boolean {
    return this.selectedMcps.includes(name);
  }

  save(): void {
    if (!this.agent || !this.hasChanges) return;

    this.isSaving = true;
    this.error = null;

    this.agentService.updateAgentMcpConfigs(this.agent.id, this.selectedMcps)
      .subscribe({
        next: (updatedAgent) => {
          this.isSaving = false;
          this.originalMcps = [...this.selectedMcps];
          this.agentUpdated.emit(updatedAgent);
          this.onClose();
        },
        error: () => {
          this.isSaving = false;
          this.error = 'Falha ao salvar';
        }
      });
  }

  cancel(): void {
    if (this.hasChanges && !confirm('Descartar alterações?')) return;
    this.selectedMcps = [...this.originalMcps];
    this.onClose();
  }
}
```

**Arquivo:** `agent-edit-modal.component.html`

```html
<div class="modal-overlay" *ngIf="isVisible" (click)="onBackdropClick($event)">
  <div class="modal-content" (click)="$event.stopPropagation()">

    <!-- Header -->
    <div class="modal-header">
      <h2>
        <span class="emoji">{{ agent?.emoji }}</span>
        Editar MCPs - {{ agent?.name }}
      </h2>
      <button class="close-btn" (click)="cancel()">✕</button>
    </div>

    <!-- Body -->
    <div class="modal-body">
      <div *ngIf="error" class="error-msg">{{ error }}</div>

      <div *ngIf="isLoading" class="loading">Carregando...</div>

      <div *ngIf="!isLoading" class="mcp-edit">
        <!-- Filters -->
        <div class="filters">
          <input
            type="text"
            [(ngModel)]="mcpFilter.search"
            (ngModelChange)="filterMcps()"
            placeholder="Buscar..."
          />
          <select [(ngModel)]="mcpFilter.category" (ngModelChange)="filterMcps()">
            <option value="">Todas categorias</option>
            <option *ngFor="let cat of mcpCategories" [value]="cat">
              {{ cat | titlecase }}
            </option>
          </select>
        </div>

        <!-- Counter -->
        <div class="counter">
          {{ selectedMcps.length }} MCP(s) selecionado(s)
          <span *ngIf="hasChanges" class="changes">(alterações pendentes)</span>
        </div>

        <!-- Grid -->
        <div class="mcp-grid">
          <div
            *ngFor="let mcp of filteredMcps"
            class="mcp-item"
            [class.selected]="isMcpSelected(mcp.name)"
            [class.stopped]="mcp.status === 'stopped'"
            (click)="toggleMcp(mcp)"
          >
            <span class="status-dot" [class]="mcp.status"></span>
            <span class="checkbox">{{ isMcpSelected(mcp.name) ? '✓' : '' }}</span>
            <span class="name">{{ mcp.name }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="modal-footer">
      <button class="btn-secondary" (click)="cancel()" [disabled]="isSaving">
        Cancelar
      </button>
      <button class="btn-primary" (click)="save()" [disabled]="!hasChanges || isSaving">
        {{ isSaving ? 'Salvando...' : 'Salvar' }}
      </button>
    </div>
  </div>
</div>
```

#### 4.2.4 Integração no Agent Catalog

**Arquivo:** `agent-catalog.component.ts`

```typescript
// Properties
selectedAgentForEdit: Agent | null = null;
isEditModalOpen = false;

// Methods
editAgentMcps(agent: Agent): void {
  this.selectedAgentForEdit = agent;
  this.isEditModalOpen = true;
}

onAgentUpdated(agent: Agent): void {
  const index = this.agents.findIndex(a => a.id === agent.id);
  if (index !== -1) {
    this.agents[index] = agent;
  }
  this.isEditModalOpen = false;
}
```

**No template do card:**

```html
<div class="agent-card" *ngFor="let agent of filteredAgents">
  <!-- conteúdo existente -->

  <div class="agent-actions" *ngIf="!agent.isSystemDefault">
    <button
      class="action-btn"
      (click)="editAgentMcps(agent); $event.stopPropagation()"
      title="Editar MCPs"
    >
      ⚙️
    </button>
  </div>
</div>

<!-- Modal -->
<app-agent-edit-modal
  [isVisible]="isEditModalOpen"
  [agent]="selectedAgentForEdit"
  (closeModal)="isEditModalOpen = false"
  (agentUpdated)="onAgentUpdated($event)"
></app-agent-edit-modal>
```

---

## 5. Arquivos a Criar/Modificar

### 5.1 Criar

| Arquivo | Descrição |
|---------|-----------|
| `shared/agent-edit-modal/agent-edit-modal.component.ts` | Modal de edição |
| `shared/agent-edit-modal/agent-edit-modal.component.html` | Template |
| `shared/agent-edit-modal/agent-edit-modal.component.scss` | Estilos |

### 5.2 Modificar

| Arquivo | Alteração |
|---------|-----------|
| `services/agent.service.ts` | Adicionar `updateAgentMcpConfigs()` |
| `agent-creator.component.ts` | Melhorar grid de MCPs |
| `agent-creator.component.html` | Novo template com filtros |
| `agent-creator.component.scss` | Novos estilos |
| `agent-catalog.component.ts` | Botão de edição |
| `agent-catalog.component.html` | Integrar modal |
| `app.module.ts` | Declarar `AgentEditModalComponent` |

---

## 6. Endpoints Backend

### 6.1 Status Atual

| Endpoint | Método | Status | Localização |
|----------|--------|--------|-------------|
| `/mcp/list` | GET | ✅ Existe | `conductor-gateway/src/api/routers/mcp_registry.py` |
| `/api/agents` | GET | ✅ Existe | `conductor-gateway/src/api/routers/agents.py:40` |
| `/api/agents` | POST | ✅ Existe | `conductor-gateway/src/api/routers/agents.py:60` |
| `/api/agents/{id}` | PATCH | ❌ **Criar** | - |

### 6.2 POST /api/agents (Já Existe)

O endpoint de criação já suporta `mcp_configs`:

```python
# conductor-gateway/src/api/routers/agents.py:21-28
class AgentCreateRequest(BaseModel):
    name: str
    description: str
    persona_content: str
    emoji: str = "🤖"
    tags: Optional[List[str]] = None
    mcp_configs: Optional[List[str]] = None  # ✅ Já suportado
```

### 6.3 PATCH /api/agents/{id} (A Criar)

Este endpoint precisa ser implementado no backend:

**Gateway:** `conductor-gateway/src/api/routers/agents.py`
**Conductor:** `conductor/src/api/routes/agents.py`

```python
# Modelo de request
class AgentUpdateRequest(BaseModel):
    mcp_configs: Optional[List[str]] = None
    # Futuramente: outros campos editáveis

# Endpoint no Gateway
@router.patch("/agents/{agent_id}")
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    client: ConductorClient = Depends(get_conductor_client)
):
    result = await client.update_agent(agent_id, request.dict(exclude_none=True))
    return result
```

---

## 7. Fluxos

### 7.1 Criação

```
Usuário abre AgentCreator
    ↓
loadMcps() → GET /mcp/list
    ↓
Grid mostra MCPs com status
    ↓
Usuário seleciona MCPs
    ↓
Clica "Criar"
    ↓
POST /api/agents { mcp_configs: [...] }
```

### 7.2 Edição

```
Usuário clica ⚙️ no card do agente
    ↓
AgentEditModal abre
    ↓
Carrega MCPs e seleção atual
    ↓
Usuário modifica seleção
    ↓
Clica "Salvar"
    ↓
PATCH /api/agents/{id} { mcp_configs: [...] }
```

---

## 8. Testes

```typescript
describe('AgentCreator - MCP Selection', () => {
  it('should load MCPs on init', () => {});
  it('should filter by search', () => {});
  it('should filter by category', () => {});
  it('should toggle selection', () => {});
  it('should include MCPs in creation', () => {});
});

describe('AgentEditModal', () => {
  it('should load current MCPs', () => {});
  it('should detect changes', () => {});
  it('should save changes', () => {});
  it('should confirm discard', () => {});
});
```

---

## 9. Referências

- [MCP_ON_DEMAND_PLAN.md](./MCP_ON_DEMAND_PLAN.md)
- `agent.service.ts:159-185` - `getAvailableMcps()`
- `agent-creator.component.ts:727-845` - Implementação atual
