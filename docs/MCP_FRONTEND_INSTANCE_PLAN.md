# Plano Frontend: Instância x MCP

> **Data:** 2026-01-02
> **Status:** Planejado
> **Escopo:** Gerenciamento de MCPs em instância ativa (conversa)
> **Complementa:** [MCP_ON_DEMAND_PLAN.md](./MCP_ON_DEMAND_PLAN.md)

---

## 1. Objetivo

Permitir que o usuário adicione ou remova MCPs de uma **instância de agente** durante uma conversa ativa, sem modificar o template original do agente.

---

## 2. Conceito: Template vs Instância

```
┌─────────────────────────────────────────────────────────────┐
│  Agent Template (definition.yaml)                           │
│  mcp_configs: ["crm"]                                       │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Instance A (conversa 1)                               │ │
│  │  template_mcps: ["crm"]       ← herdado (read-only)    │ │
│  │  instance_mcps: ["billing"]   ← extra (editável)       │ │
│  │  combined: ["crm", "billing"] ← usado na execução      │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Instance B (conversa 2)                               │ │
│  │  template_mcps: ["crm"]                                │ │
│  │  instance_mcps: []            ← sem extras             │ │
│  │  combined: ["crm"]                                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Regras:**
- MCPs do template **não podem ser removidos** na instância
- MCPs extras são **específicos da instância**
- Próxima execução usa a lista **combinada**

---

## 3. Estado Atual

### 3.1 Arquivos Relevantes

| Arquivo | Responsabilidade |
|---------|------------------|
| `services/agent.service.ts` | Métodos de MCP |
| `services/agent-instance-management.service.ts` | Ciclo de vida de instâncias |
| `shared/conductor-chat/conductor-chat.component.ts` | Chat com dock |
| `shared/conductor-chat/services/modal-state.service.ts` | Estado dos modais |

### 3.2 Métodos Existentes

```typescript
// agent.service.ts
updateInstanceMcpConfigs(instanceId: string, mcpConfigs: string[]): Observable<void>
getInstanceMcpConfigs(instanceId: string): Observable<InstanceMcpConfigs>
```

### 3.3 Interface de Resposta

```typescript
interface InstanceMcpConfigs {
  template_mcps: string[];   // Do template (read-only)
  instance_mcps: string[];   // Extras da instância
  combined: string[];        // União para execução
}
```

### 3.4 Menu de Opções Atual

O `conductor-chat` já tem menu de opções (⚙️) com:
- Ver Contexto
- Editar Persona
- Editar diretório

**Falta:** "Gerenciar MCPs"

---

## 4. Solução

### 4.1 Adicionar ao ModalState

**Arquivo:** `modal-state.service.ts`

```typescript
export interface ModalState {
  personaModal: boolean;
  personaEditModal: boolean;
  cwdModal: boolean;
  contextEditor: boolean;
  contextEditorModal: boolean;
  agentOptionsMenu: boolean;
  dockInfoModal: boolean;
  mcpManagerModal: boolean;  // NOVO
}
```

### 4.2 Criar MCP Manager Modal

**Criar:** `shared/mcp-manager-modal/`

#### 4.2.1 Componente

**Arquivo:** `mcp-manager-modal.component.ts`

```typescript
import { Component, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { BaseModalComponent } from '../modals/base/base-modal.component';
import { AgentService, MCPRegistryEntry } from '../../services/agent.service';

interface InstanceMcpConfigs {
  template_mcps: string[];
  instance_mcps: string[];
  combined: string[];
}

@Component({
  selector: 'app-mcp-manager-modal',
  templateUrl: './mcp-manager-modal.component.html',
  styleUrls: ['./mcp-manager-modal.component.scss']
})
export class McpManagerModalComponent extends BaseModalComponent implements OnInit {
  @Input() instanceId: string | null = null;
  @Input() instanceName: string = '';
  @Output() mcpsSaved = new EventEmitter<string[]>();

  // Data
  availableMcps: MCPRegistryEntry[] = [];
  templateMcps: string[] = [];
  instanceMcps: string[] = [];

  // State
  isLoading = true;
  isSaving = false;
  error: string | null = null;

  // Selection
  selectedMcpToAdd: string = '';

  // Original for change detection
  private originalInstanceMcps: string[] = [];

  constructor(private agentService: AgentService) {
    super();
  }

  ngOnInit(): void {
    this.loadData();
  }

  protected override onModalOpened(): void {
    this.loadData();
  }

  loadData(): void {
    if (!this.instanceId) return;

    this.isLoading = true;
    this.error = null;

    Promise.all([
      this.agentService.getAvailableMcps().toPromise(),
      this.agentService.getInstanceMcpConfigs(this.instanceId).toPromise()
    ]).then(([mcps, configs]) => {
      this.availableMcps = mcps || [];

      if (configs) {
        this.templateMcps = configs.template_mcps || [];
        this.instanceMcps = [...(configs.instance_mcps || [])];
        this.originalInstanceMcps = [...this.instanceMcps];
      }

      this.isLoading = false;
    }).catch(err => {
      this.error = 'Falha ao carregar dados';
      this.isLoading = false;
      console.error('Load error:', err);
    });
  }

  // Computed
  get combinedMcps(): string[] {
    return [...new Set([...this.templateMcps, ...this.instanceMcps])];
  }

  get availableToAdd(): MCPRegistryEntry[] {
    const combined = this.combinedMcps;
    return this.availableMcps.filter(mcp => !combined.includes(mcp.name));
  }

  get hasChanges(): boolean {
    return JSON.stringify([...this.instanceMcps].sort()) !==
           JSON.stringify([...this.originalInstanceMcps].sort());
  }

  // Actions
  addMcp(): void {
    if (!this.selectedMcpToAdd) return;
    if (!this.instanceMcps.includes(this.selectedMcpToAdd)) {
      this.instanceMcps.push(this.selectedMcpToAdd);
    }
    this.selectedMcpToAdd = '';
  }

  removeMcp(mcpName: string): void {
    const index = this.instanceMcps.indexOf(mcpName);
    if (index !== -1) {
      this.instanceMcps.splice(index, 1);
    }
  }

  // Helpers
  isTemplateMcp(mcpName: string): boolean {
    return this.templateMcps.includes(mcpName);
  }

  getMcpStatus(mcpName: string): string {
    const mcp = this.availableMcps.find(m => m.name === mcpName);
    return mcp?.status || 'unknown';
  }

  getStatusIcon(status: string): string {
    switch (status) {
      case 'healthy': return '●';
      case 'stopped': return '○';
      case 'starting': return '◐';
      default: return '?';
    }
  }

  // Save
  save(): void {
    if (!this.instanceId || !this.hasChanges) return;

    this.isSaving = true;
    this.error = null;

    this.agentService.updateInstanceMcpConfigs(this.instanceId, this.instanceMcps)
      .subscribe({
        next: () => {
          this.isSaving = false;
          this.originalInstanceMcps = [...this.instanceMcps];
          this.mcpsSaved.emit(this.combinedMcps);
          this.onClose();
        },
        error: (err) => {
          this.isSaving = false;
          this.error = 'Falha ao salvar';
          console.error('Save error:', err);
        }
      });
  }

  cancel(): void {
    if (this.hasChanges && !confirm('Descartar alterações?')) return;
    this.instanceMcps = [...this.originalInstanceMcps];
    this.onClose();
  }
}
```

#### 4.2.2 Template

**Arquivo:** `mcp-manager-modal.component.html`

```html
<div class="modal-overlay" *ngIf="isVisible" (click)="onBackdropClick($event)">
  <div class="modal-content mcp-manager" (click)="$event.stopPropagation()">

    <!-- Header -->
    <div class="modal-header">
      <h2>Gerenciar MCPs</h2>
      <span class="instance-name">{{ instanceName }}</span>
      <button class="close-btn" (click)="cancel()">✕</button>
    </div>

    <!-- Loading -->
    <div *ngIf="isLoading" class="modal-body loading">
      <span>Carregando...</span>
    </div>

    <!-- Error -->
    <div *ngIf="error" class="error-banner">{{ error }}</div>

    <!-- Content -->
    <div *ngIf="!isLoading" class="modal-body">

      <!-- Template MCPs -->
      <section class="mcp-section">
        <h3>
          MCPs do Template
          <span class="badge readonly">herdado</span>
        </h3>
        <p class="hint">Vêm do template do agente. Não podem ser removidos aqui.</p>

        <div class="mcp-tags">
          <span *ngFor="let mcp of templateMcps" class="tag template">
            <span class="status" [class]="getMcpStatus(mcp)">
              {{ getStatusIcon(getMcpStatus(mcp)) }}
            </span>
            {{ mcp }}
          </span>
          <span *ngIf="templateMcps.length === 0" class="empty">
            Nenhum MCP no template
          </span>
        </div>
      </section>

      <!-- Instance MCPs -->
      <section class="mcp-section">
        <h3>
          MCPs Extras
          <span class="badge editable">desta instância</span>
        </h3>
        <p class="hint">MCPs adicionais apenas para esta instância.</p>

        <div class="mcp-tags">
          <span
            *ngFor="let mcp of instanceMcps"
            class="tag instance removable"
            (click)="removeMcp(mcp)"
          >
            <span class="status" [class]="getMcpStatus(mcp)">
              {{ getStatusIcon(getMcpStatus(mcp)) }}
            </span>
            {{ mcp }}
            <span class="remove">✕</span>
          </span>
          <span *ngIf="instanceMcps.length === 0" class="empty">
            Nenhum MCP extra
          </span>
        </div>

        <!-- Add MCP -->
        <div class="add-row">
          <select [(ngModel)]="selectedMcpToAdd">
            <option value="">Selecionar MCP...</option>
            <option *ngFor="let mcp of availableToAdd" [value]="mcp.name">
              {{ getStatusIcon(mcp.status) }} {{ mcp.name }}
            </option>
          </select>
          <button
            class="btn-add"
            (click)="addMcp()"
            [disabled]="!selectedMcpToAdd"
          >
            + Adicionar
          </button>
        </div>
      </section>

      <!-- Combined View -->
      <section class="mcp-section combined">
        <h3>MCPs Ativos</h3>
        <p class="hint">Serão usados na próxima execução.</p>
        <div class="combined-list">
          <span *ngFor="let mcp of combinedMcps" class="combined-tag">
            {{ getStatusIcon(getMcpStatus(mcp)) }} {{ mcp }}
          </span>
        </div>
      </section>

      <!-- Info -->
      <div
        *ngIf="combinedMcps.some(m => getMcpStatus(m) === 'stopped')"
        class="info-banner"
      >
        MCPs parados serão iniciados automaticamente.
      </div>
    </div>

    <!-- Footer -->
    <div class="modal-footer">
      <button class="btn-secondary" (click)="cancel()" [disabled]="isSaving">
        Cancelar
      </button>
      <button
        class="btn-primary"
        (click)="save()"
        [disabled]="!hasChanges || isSaving"
      >
        {{ isSaving ? 'Salvando...' : 'Salvar' }}
      </button>
    </div>
  </div>
</div>
```

#### 4.2.3 Estilos

**Arquivo:** `mcp-manager-modal.component.scss`

```scss
.mcp-manager {
  width: 480px;
  max-width: 95vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);

  h2 {
    margin: 0;
    font-size: 1.1rem;
  }

  .instance-name {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .close-btn {
    margin-left: auto;
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: var(--text-secondary);

    &:hover { color: var(--text-primary); }
  }
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;

  &.loading {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 150px;
  }
}

.mcp-section {
  margin-bottom: 1.25rem;

  h3 {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin: 0 0 0.25rem 0;
    font-size: 0.9rem;
  }

  .hint {
    margin: 0 0 0.5rem 0;
    font-size: 0.75rem;
    color: var(--text-secondary);
  }

  &.combined {
    background: rgba(255,255,255,0.03);
    padding: 0.75rem;
    border-radius: 4px;
    margin-top: 1rem;
  }
}

.badge {
  font-size: 0.6rem;
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  text-transform: uppercase;

  &.readonly {
    background: #374151;
    color: #9ca3af;
  }

  &.editable {
    background: #1e40af;
    color: #93c5fd;
  }
}

.mcp-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  min-height: 28px;
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;

  &.template {
    background: #374151;
    color: #d1d5db;
  }

  &.instance {
    background: #1e40af;
    color: #bfdbfe;
  }

  &.removable {
    cursor: pointer;

    .remove {
      opacity: 0;
      margin-left: 0.2rem;
      transition: opacity 0.15s;
    }

    &:hover {
      background: #1e3a8a;

      .remove { opacity: 1; }
    }
  }
}

.status {
  font-size: 0.7rem;

  &.healthy { color: #10b981; }
  &.stopped { color: #6b7280; }
  &.starting { color: #f59e0b; }
}

.empty {
  color: var(--text-tertiary);
  font-style: italic;
  font-size: 0.8rem;
}

.add-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.6rem;

  select {
    flex: 1;
    padding: 0.4rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--input-bg);
    color: var(--text-primary);
    font-size: 0.8rem;
  }

  .btn-add {
    padding: 0.4rem 0.75rem;
    border: none;
    border-radius: 4px;
    background: var(--primary-color);
    color: white;
    cursor: pointer;
    font-size: 0.8rem;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    &:hover:not(:disabled) {
      background: var(--primary-hover);
    }
  }
}

.combined-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.combined-tag {
  font-size: 0.75rem;
  padding: 0.2rem 0.4rem;
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
}

.info-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.6rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 4px;
  font-size: 0.75rem;
  color: #93c5fd;
  margin-top: 0.75rem;
}

.error-banner {
  padding: 0.6rem;
  background: rgba(239, 68, 68, 0.1);
  color: #fca5a5;
  border-radius: 4px;
  margin: 0.5rem 1rem;
  font-size: 0.8rem;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid var(--border-color);

  button {
    padding: 0.45rem 1rem;
    border-radius: 4px;
    font-size: 0.85rem;
    cursor: pointer;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }

  .btn-secondary {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-primary);

    &:hover:not(:disabled) {
      background: var(--hover-bg);
    }
  }

  .btn-primary {
    background: var(--primary-color);
    border: none;
    color: white;

    &:hover:not(:disabled) {
      background: var(--primary-hover);
    }
  }
}
```

### 4.3 Integrar no conductor-chat

**Arquivo:** `conductor-chat.component.ts`

```typescript
// Adicionar método
manageMcps(): void {
  this.modalStateService.close('agentOptionsMenu');

  if (!this.activeAgentId) {
    console.warn('No active agent');
    return;
  }

  this.modalStateService.open('mcpManagerModal');
}

onMcpsSaved(mcps: string[]): void {
  console.log('MCPs updated:', this.activeAgentId, mcps);
  // Opcional: mostrar toast
}
```

**No template, adicionar item no menu:**

```html
<!-- Agent Options Menu -->
<div *ngIf="modalStateService.isOpen('agentOptionsMenu')" class="agent-options-menu">
  <button class="menu-item" (click)="viewAgentContext()">
    <span class="icon">📋</span> Ver Contexto
  </button>
  <button class="menu-item" (click)="editPersona()">
    <span class="icon">✏️</span> Editar Persona
  </button>
  <button class="menu-item" (click)="editAgentCwd()">
    <span class="icon">📁</span> Editar diretório
  </button>
  <!-- NOVO -->
  <button class="menu-item" (click)="manageMcps()">
    <span class="icon">🔌</span> Gerenciar MCPs
  </button>
</div>

<!-- Modal -->
<app-mcp-manager-modal
  [isVisible]="modalStateService.isOpen('mcpManagerModal')"
  [instanceId]="activeAgentId"
  [instanceName]="selectedAgentName"
  (closeModal)="modalStateService.close('mcpManagerModal')"
  (mcpsSaved)="onMcpsSaved($event)"
></app-mcp-manager-modal>
```

---

## 5. Arquivos a Criar/Modificar

### 5.1 Criar

| Arquivo | Descrição |
|---------|-----------|
| `shared/mcp-manager-modal/mcp-manager-modal.component.ts` | Componente |
| `shared/mcp-manager-modal/mcp-manager-modal.component.html` | Template |
| `shared/mcp-manager-modal/mcp-manager-modal.component.scss` | Estilos |

### 5.2 Modificar

| Arquivo | Alteração |
|---------|-----------|
| `services/modal-state.service.ts` | Adicionar `mcpManagerModal` |
| `conductor-chat.component.ts` | Método `manageMcps()` |
| `conductor-chat.component.html` | Item no menu + modal |
| `app.module.ts` | Declarar componente |

---

## 6. Endpoints Backend

### 6.1 Status Atual

| Endpoint | Método | Status | Localização |
|----------|--------|--------|-------------|
| `/mcp/list` | GET | ✅ Existe | `conductor-gateway/src/api/routers/mcp_registry.py` |
| `/api/agents/instances/{id}/mcp-configs` | GET | ✅ Existe | `conductor-gateway/src/api/app.py:2347` |
| `/api/agents/instances/{id}/mcp-configs` | PATCH | ✅ Existe | `conductor-gateway/src/api/app.py:2400` |

**Nota:** Todos os endpoints necessários para este plano **já estão implementados** no backend.

### 6.2 Detalhes dos Endpoints

**GET /api/agents/instances/{id}/mcp-configs**
```json
// Response
{
  "template_mcps": ["crm"],        // Do template do agente
  "instance_mcps": ["billing"],    // Extras da instância
  "combined": ["crm", "billing"]   // União para execução
}
```

**PATCH /api/agents/instances/{id}/mcp-configs**
```json
// Request
{
  "mcp_configs": ["billing", "database"]
}

// Response
{
  "success": true,
  "instance_id": "...",
  "mcp_configs": ["billing", "database"]
}
```

---

## 7. Fluxo de Usuário

```
Usuário clica ⚙️ no dock do agente
    ↓
Menu aparece
    ↓
Clica "🔌 Gerenciar MCPs"
    ↓
McpManagerModal abre
    ↓
├─► GET /api/agents/instances/{id}/mcp-configs
├─► GET /mcp/list
    ↓
Modal mostra:
  - MCPs do Template (read-only)
  - MCPs Extras (editável)
  - Lista combinada
    ↓
Usuário adiciona/remove MCPs extras
    ↓
Clica "Salvar"
    ↓
PATCH /api/agents/instances/{id}/mcp-configs
    ↓
Próxima execução usa MCPs combinados
```

---

## 8. Validações

| Cenário | Comportamento |
|---------|---------------|
| Remover MCP de template | Não permitido (não aparece opção) |
| Adicionar MCP já existente | Não aparece no dropdown |
| Sem instanceId | Modal não abre, log de erro |
| Fechar com alterações | Pede confirmação |

---

## 9. Testes

```typescript
describe('McpManagerModalComponent', () => {
  it('should load template and instance MCPs', () => {});
  it('should not show remove on template MCPs', () => {});
  it('should add new MCP to instance list', () => {});
  it('should remove MCP from instance list', () => {});
  it('should detect changes correctly', () => {});
  it('should save changes', () => {});
  it('should confirm before discarding changes', () => {});
});
```

---

## 10. Referências

- [MCP_ON_DEMAND_PLAN.md](./MCP_ON_DEMAND_PLAN.md)
- `agent.service.ts:531-594` - Métodos de instância
- `modal-state.service.ts` - Padrão de modais
- `conductor-chat.component.ts:4049-4069` - Padrão editPersona
