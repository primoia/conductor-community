# 🏛️ Sistema de Conselheiros - Implementação Completa

> **Status:** ✅ Implementação Frontend Completa (Backend pendente)
> **Data:** 2025-10-25
> **Versão:** 1.0

---

## 📋 Visão Geral

O Sistema de Conselheiros foi implementado com sucesso no frontend do **conductor-web**, trazendo gamificação inspirada em SimCity para o editor de roteiros.

**Conceito Principal:**
- Agentes podem ser **promovidos a Conselheiros**
- Conselheiros executam **tarefas automáticas periódicas** (ex: verificar CSS inline, testes, arquivos grandes)
- Cada conselheiro tem **personalidade** (nome, cargo, emoji)
- Resultados aparecem como **eventos narrativos** no painel
- Visual diferenciado: **coroa dourada 👑** no AgentGame

---

## 🎯 O Que Foi Implementado

### ✅ 1. Tipos e Interfaces (`councilor.types.ts`)

**Localização:** `/src/app/models/councilor.types.ts`

**Conteúdo:**
- `CouncilorConfig`: Configuração completa (tarefa, agendamento, notificações)
- `CouncilorSchedule`: Agendamento (interval ou cron)
- `CouncilorTask`: Definição da tarefa periódica
- `CouncilorNotifications`: Configuração de notificações
- `AgentWithCouncilor`: Interface estendida do Agent
- `CouncilorExecutionResult`: Resultado de execução
- `PromoteToCouncilorRequest`: Payload de promoção
- `INVESTIGATOR_PRESETS`: 4 presets de investigadores (Quality, Performance, Security, Architecture)
- `COUNCILOR_TASK_TEMPLATES`: 5 templates de tarefas pré-configuradas

---

### ✅ 2. Serviço de Scheduler (`CouncilorSchedulerService`)

**Localização:** `/src/app/services/councilor-scheduler.service.ts`

**Funcionalidades:**
- ✅ Inicialização e carregamento de conselheiros do backend
- ✅ Agendamento automático de tarefas (setInterval)
- ✅ Execução periódica via `AgentService.executeAgent()`
- ✅ Análise de severidade do resultado (success/warning/error)
- ✅ Sistema de notificações via `GamificationEventsService`
- ✅ Prevenção de execuções simultâneas (lock)
- ✅ Pausar/retomar conselheiros
- ✅ Parsing de intervalos (30m, 1h, 2h)
- ✅ Cleanup de recursos (ngOnDestroy)
- ✅ Observable de conselheiros ativos
- ✅ Contador de investigações ativas

**Exemplo de uso:**
```typescript
// No app.component.ts
constructor(private councilorScheduler: CouncilorSchedulerService) {}

async ngOnInit() {
  await this.councilorScheduler.initialize();
  console.log('🏛️ Conselheiros em patrulha');
}
```

---

### ✅ 3. Modal de Promoção (`PromoteCouncilorModalComponent`)

**Localização:** `/src/app/living-screenplay-simple/promote-councilor-modal/`

**Arquivos:**
- `promote-councilor-modal.component.ts`
- `promote-councilor-modal.component.html`
- `promote-councilor-modal.component.css`

**Funcionalidades:**
- ✅ Formulário completo de promoção
- ✅ Seletor de templates de tarefas pré-configuradas
- ✅ Configuração de periodicidade (interval ou cron)
- ✅ Gerenciamento de arquivos de contexto
- ✅ Configuração de notificações (canais e severidades)
- ✅ Validação de formulário
- ✅ Preview do agendamento
- ✅ Design moderno e responsivo

**Seções do formulário:**
1. **Personalização**: Nome do conselheiro, título/cargo
2. **Tarefa Automática**: Nome, prompt, arquivos de contexto
3. **Periodicidade**: Interval (30m, 1h, 2h) ou Cron
4. **Notificações**: Quando notificar e onde (panel, toast, email)

**Templates disponíveis:**
- Verificar Arquivos Monolíticos
- Verificar Cobertura de Testes
- Verificar Dependências Vulneráveis
- Verificar CSS Inline
- Verificar Performance de APIs

---

### ✅ 4. Dashboard de Conselheiros (`CouncilorsDashboardComponent`)

**Localização:** `/src/app/living-screenplay-simple/councilors-dashboard/`

**Arquivos:**
- `councilors-dashboard.component.ts`
- `councilors-dashboard.component.html`
- `councilors-dashboard.component.css`

**Funcionalidades:**
- ✅ Lista de conselheiros ativos
- ✅ Cards com informações completas de cada conselheiro
- ✅ Status visual (ativo/pausado) com cores
- ✅ Avatar com emoji e badge de status
- ✅ Informações da tarefa e agendamento
- ✅ Estatísticas (execuções, taxa de sucesso, intervalo)
- ✅ Ações: Ver relatório, editar, pausar/retomar, demover
- ✅ Estados: loading, empty, error
- ✅ Design responsivo e moderno

**Ações disponíveis:**
- 📋 Ver Último Relatório
- ⚙️ Editar Configuração
- ⏸️ Pausar / ▶️ Retomar
- 🗑️ Remover do Conselho

---

### ✅ 5. Visual Diferenciado no AgentGame

**Localização:** `/src/app/living-screenplay-simple/agent-game/agent-game.component.ts`

**Mudanças:**
- ✅ Adicionado campo `isCouncilor?: boolean` na interface `AgentCharacter`
- ✅ Renderização de **coroa dourada 👑** acima do agente
- ✅ **Borda dourada** (#FFD700) ao redor do círculo do agente
- ✅ **Efeito de brilho dourado** (shadowBlur) na coroa

**Código adicionado:**
```typescript
// Draw golden crown for councilors
if (agent.isCouncilor) {
  const crownSize = 16;
  const crownX = x;
  const crownY = y - agent.radius - 12;

  // Draw crown emoji with golden glow
  this.ctx.save();
  this.ctx.shadowColor = '#FFD700';
  this.ctx.shadowBlur = 10;
  this.ctx.font = `${crownSize}px Arial`;
  this.ctx.textAlign = 'center';
  this.ctx.textBaseline = 'middle';
  this.ctx.fillText('👑', crownX, crownY);
  this.ctx.restore();

  // Draw golden border around agent
  this.ctx.beginPath();
  this.ctx.arc(x, y, agent.radius + 2, 0, Math.PI * 2);
  this.ctx.strokeStyle = '#FFD700';
  this.ctx.lineWidth = 3;
  this.ctx.stroke();
}
```

---

### ✅ 6. Documentação de API

**Localização:** `/docs/api/councilor-endpoints.md`

**Conteúdo:**
- ✅ 8 endpoints documentados com exemplos
- ✅ Schemas MongoDB para `agents` e `councilor_executions`
- ✅ Diagramas de fluxo (Mermaid)
- ✅ Exemplos de Request/Response
- ✅ Status codes e tratamento de erros
- ✅ Considerações de segurança
- ✅ Notas de implementação backend (Python/FastAPI)
- ✅ Índices recomendados para MongoDB

**Endpoints documentados:**
1. `GET /api/agents?is_councilor=true` - Listar conselheiros
2. `POST /api/agents/:id/promote-councilor` - Promover agente
3. `PATCH /api/agents/:id/councilor-config` - Atualizar config
4. `PATCH /api/agents/:id/councilor-schedule` - Pausar/retomar
5. `DELETE /api/agents/:id/demote-councilor` - Demover
6. `POST /api/councilors/executions` - Salvar resultado
7. `GET /api/agents/:id/councilor-reports` - Buscar relatórios
8. `GET /api/agents/:id/councilor-reports/latest` - Última execução

---

## 🚀 Como Usar

### 1. Inicializar o Scheduler

No `app.component.ts`:

```typescript
import { CouncilorSchedulerService } from './services/councilor-scheduler.service';

@Component({ /* ... */ })
export class AppComponent implements OnInit {
  constructor(private councilorScheduler: CouncilorSchedulerService) {}

  async ngOnInit() {
    // Inicializar scheduler de conselheiros
    await this.councilorScheduler.initialize();
  }
}
```

### 2. Abrir Modal de Promoção

Em qualquer componente:

```typescript
import { PromoteCouncilorModalComponent } from './living-screenplay-simple/promote-councilor-modal/promote-councilor-modal.component';

// No template
showPromoteModal = false;
selectedAgent: AgentWithCouncilor | undefined;

openPromoteModal(agent: Agent) {
  this.selectedAgent = agent;
  this.showPromoteModal = true;
}

// No HTML
<app-promote-councilor-modal
  *ngIf="showPromoteModal"
  [agent]="selectedAgent"
  (promote)="onPromote($event)"
  (close)="showPromoteModal = false"
></app-promote-councilor-modal>
```

### 3. Promover Agente

```typescript
async onPromote(request: PromoteToCouncilorRequest) {
  try {
    // Chamar API backend
    const response = await fetch(`/api/agents/${this.selectedAgent.agent_id}/promote-councilor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });

    const data = await response.json();

    if (data.success) {
      console.log('✅ Agente promovido:', data.agent);

      // Recarregar lista de conselheiros
      await this.councilorScheduler.initialize();

      this.showPromoteModal = false;
    }
  } catch (error) {
    console.error('❌ Erro ao promover:', error);
  }
}
```

### 4. Abrir Dashboard

```typescript
import { CouncilorsDashboardComponent } from './living-screenplay-simple/councilors-dashboard/councilors-dashboard.component';

// No template
showDashboard = false;

openDashboard() {
  this.showDashboard = true;
}

// No HTML
<app-councilors-dashboard
  *ngIf="showDashboard"
  (close)="showDashboard = false"
  (promoteNew)="openPromoteModal()"
></app-councilors-dashboard>
```

---

## 🎨 Fluxo de Uso Completo

### Cenário: Promover e Monitorar Conselheiro

1. **Usuário clica em "Promover Conselheiro"** no AgentGame ou menu
2. Modal abre com formulário
3. Usuário preenche:
   - Nome: "Silva"
   - Cargo: "Conselheiro de Arquitetura"
   - Tarefa: Seleciona template "Verificar Arquivos Monolíticos"
   - Periodicidade: "30m" (a cada 30 minutos)
   - Notificações: ✅ Alertas e Erros
4. Clica "⭐ Promover"
5. Backend salva agente com `is_councilor: true`
6. Frontend agenda tarefa com `setInterval(30min)`
7. A cada 30min:
   - Conselheiro executa prompt
   - Analisa resultado (success/warning/error)
   - Se houver alertas → cria evento no painel
8. Usuário vê no painel: "🏗️ Silva: Verificar Arquivos Monolíticos - Encontrados 3 arquivos grandes"
9. Usuário clica no evento → modal com relatório detalhado
10. No AgentGame, o agente aparece com **coroa dourada 👑**

---

## 🔧 Próximas Implementações (Backend)

### Prioridade Alta
- [ ] Implementar 8 endpoints de API (ver `councilor-endpoints.md`)
- [ ] Criar collection `councilor_executions` no MongoDB
- [ ] Adicionar campos de conselheiro na collection `agents`
- [ ] Implementar validação de configuração de conselheiros

### Prioridade Média
- [ ] Sistema de notificações Toast
- [ ] Sistema de notificações por Email
- [ ] Suporte a expressões Cron (além de interval)
- [ ] Logs de execuções para debug

### Prioridade Baixa
- [ ] Dashboard de analytics de conselheiros
- [ ] Exportação de relatórios em PDF
- [ ] Integração com Slack/Discord para notificações

---

## 📊 Arquivos Criados

```
src/conductor-web/
├── src/app/
│   ├── models/
│   │   └── councilor.types.ts                        ✅ (tipos e interfaces)
│   ├── services/
│   │   └── councilor-scheduler.service.ts            ✅ (scheduler)
│   └── living-screenplay-simple/
│       ├── promote-councilor-modal/
│       │   ├── promote-councilor-modal.component.ts  ✅
│       │   ├── promote-councilor-modal.component.html ✅
│       │   └── promote-councilor-modal.component.css  ✅
│       ├── councilors-dashboard/
│       │   ├── councilors-dashboard.component.ts     ✅
│       │   ├── councilors-dashboard.component.html   ✅
│       │   └── councilors-dashboard.component.css    ✅
│       └── agent-game/
│           └── agent-game.component.ts               ✅ (atualizado)

docs/
├── api/
│   └── councilor-endpoints.md                        ✅ (doc de API)
└── sagas/saga-004/
    └── IMPLEMENTACAO-CONSELHEIROS.md                 ✅ (este arquivo)
```

**Total:** 9 arquivos criados + 1 atualizado

---

## 🎯 Comparação: O Que Mudou vs Saga-004 Original

### ❌ O Que NÃO Implementamos (da saga-004 v1/v2)

- ~~Barra horizontal de comandos~~ → Substituído por sistema de conselheiros
- ~~Event Ticker horizontal~~ → Eventos aparecem no painel existente
- ~~KPIs no rodapé~~ → Substituído por dashboard de conselheiros
- ~~News Ticker redesenhado~~ → Usar GamificationEventsService existente

### ✅ O Que Implementamos (MELHOR que saga-004)

- ✅ **Sistema de Conselheiros** (similar aos advisors do SimCity)
- ✅ **Promoção de agentes** com personalização completa
- ✅ **Tarefas automáticas periódicas** configuráveis
- ✅ **Templates de tarefas** pré-configuradas
- ✅ **Dashboard dedicado** para gerenciar conselheiros
- ✅ **Visual diferenciado** (coroa dourada no AgentGame)
- ✅ **Eventos narrativos** humanizados
- ✅ **Integração nativa** com AgentService existente

### 💡 Por Que Esta Abordagem É Melhor

1. **Mais próxima do SimCity**: Advisors vs barra de comandos
2. **Personalização**: Cada conselheiro tem nome, cargo, tarefa própria
3. **Automação real**: Executa tarefas sem intervenção do usuário
4. **Escalável**: Fácil adicionar novos templates de tarefas
5. **Reutiliza infraestrutura**: AgentService, GamificationEvents, AgentGame

---

## 🧪 Como Testar (Quando Backend Estiver Pronto)

### Teste 1: Promover Conselheiro

```bash
# 1. Promover agente
curl -X POST http://localhost:8000/api/agents/code_generator_agent/promote-councilor \
  -H "Content-Type: application/json" \
  -d '{
    "councilor_config": {
      "title": "Conselheiro de Testes",
      "schedule": { "type": "interval", "value": "1m", "enabled": true },
      "task": {
        "name": "Teste Simples",
        "prompt": "Retorne 'Olá do conselheiro!'",
        "output_format": "summary"
      },
      "notifications": {
        "on_success": true,
        "on_warning": true,
        "on_error": true,
        "channels": ["panel"]
      }
    },
    "customization": { "display_name": "TestBot" }
  }'

# 2. Verificar promoção
curl http://localhost:8000/api/agents?is_councilor=true

# 3. Aguardar 1 minuto

# 4. Verificar execuções
curl http://localhost:8000/api/agents/code_generator_agent/councilor-reports

# 5. Ver último resultado
curl http://localhost:8000/api/agents/code_generator_agent/councilor-reports/latest
```

### Teste 2: Pausar/Retomar

```bash
# Pausar
curl -X PATCH http://localhost:8000/api/agents/code_generator_agent/councilor-schedule \
  -H "Content-Type: application/json" \
  -d '{ "enabled": false }'

# Retomar
curl -X PATCH http://localhost:8000/api/agents/code_generator_agent/councilor-schedule \
  -H "Content-Type: application/json" \
  -d '{ "enabled": true }'
```

### Teste 3: Demover

```bash
curl -X DELETE http://localhost:8000/api/agents/code_generator_agent/demote-councilor
```

---

## 📝 Notas Finais

1. **Nomenclatura**: "Conselheiro" (não "Secretário" ou "Ministro")
2. **Persistência**: Usar MongoDB (não localStorage) para configurações
3. **Integração**: Sistemas já existem (AgentService, GamificationEvents)
4. **Backend**: Python/FastAPI (ver `councilor-endpoints.md`)
5. **Visual**: Coroa dourada 👑 = conselheiro no AgentGame

---

**Implementado por:** Claude Code
**Data:** 2025-10-25
**Status:** ✅ Frontend Completo | ⏳ Backend Pendente
