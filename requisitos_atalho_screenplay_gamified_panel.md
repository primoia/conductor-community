# Atalho para Carregar Screenplay no Gamified Panel

## 📋 Visão Geral

Este documento analisa a viabilidade de implementar um **atalho para carregar a screenplay do projeto** dentro do `app-gamified-panel`, ativado quando um agente termina seu trabalho. O objetivo é permitir acesso rápido à screenplay diretamente do painel de notificações de agentes, melhorando a experiência do usuário ao navegar entre eventos de agentes e a documentação do projeto.

## 🎯 Requisitos Identificados

### Requisitos Funcionais

**RF1**: Exibir botão/atalho no painel gamificado quando houver eventos de conclusão de agentes
- O atalho deve aparecer contextualmente, relacionado aos eventos exibidos
- Deve ser visível tanto no estado expandido quanto recolhido do painel

**RF2**: Carregar screenplay do projeto ao clicar no atalho
- Deve buscar a screenplay através do `ScreenplayStorage` ou `ScreenplayFileManagementService`
- Precisa identificar qual screenplay é a "do projeto" (pode ser a última aberta ou uma marcada como principal)

**RF3**: Integrar com sistema de carregamento de screenplays existente
- Reutilizar mecanismos de `ScreenplayManager` para abertura de roteiros
- Manter consistência com fluxo atual de carregamento via modal

**RF4**: Feedback visual durante carregamento
- Indicar estado de loading enquanto busca a screenplay
- Mostrar notificação de sucesso/erro após tentativa de carregamento

### Requisitos Não-Funcionais

**RNF1**: Performance
- O carregamento não deve bloquear a interface
- Deve usar Observables/Promises para operações assíncronas

**RNF2**: Usabilidade
- Atalho deve ser intuitivo e de fácil acesso
- Posicionamento deve respeitar hierarquia visual do painel

**RNF3**: Consistência
- Seguir padrões visuais do `GamifiedPanelComponent`
- Manter coesão com design system existente (ícones, cores, tipografia)

## 🔄 Fluxo do Processo

### Cenário de Uso

1. **Início**: Usuário está visualizando o `app-gamified-panel` (expandido ou recolhido)
2. **Evento de Agente**: Um agente conclui execução e evento `agent_execution_completed` é recebido
3. **Exibição do Atalho**: Atalho "Carregar Screenplay" aparece no header ou footer do painel
4. **Interação do Usuário**: Usuário clica no atalho
5. **Carregamento**: Sistema identifica screenplay do projeto e inicia carregamento
6. **Feedback**: Loading spinner é exibido durante busca
7. **Finalização**: Screenplay é carregada no editor principal ou modal de gerenciamento é aberto
8. **Notificação**: Usuário recebe confirmação visual (toast ou mensagem)

### Fluxo Técnico Detalhado

```
EventTicker (eventos de agentes)
    ↓
GamifiedPanelComponent (detecta evento 'result' level)
    ↓
Botão "Carregar Screenplay" habilitado
    ↓
Usuário clica no botão
    ↓
GamifiedPanelComponent emite evento @Output loadScreenplay
    ↓
ScreenplayInteractive (componente pai) recebe evento
    ↓
Chama ScreenplayStorage.getScreenplays() para listar
    ↓
Identifica screenplay principal (última aberta ou padrão)
    ↓
Chama ScreenplayStorage.getScreenplay(id) para carregar conteúdo completo
    ↓
Carrega screenplay no InteractiveEditor via ScreenplayService
    ↓
Exibe NotificationToast com sucesso/erro
```

## 🏗️ Componentes Principais

### Frontend (Angular)

#### **GamifiedPanelComponent**
- **Localização**: `src/conductor-web/src/app/living-screenplay-simple/gamified-panel/gamified-panel.component.ts`
- **Responsabilidade**: Exibir painel de notificações com KPIs e eventos de agentes
- **Modificações Necessárias**:
  - Adicionar novo `@Output() loadScreenplay = new EventEmitter<void>()`
  - Adicionar botão no header ou footer do template
  - Detectar quando há eventos de nível `result` para habilitar atalho
  - Estilizar botão seguindo padrão visual existente

#### **EventTickerComponent**
- **Localização**: `src/conductor-web/src/app/living-screenplay-simple/event-ticker/event-ticker.component.ts`
- **Responsabilidade**: Exibir lista de eventos gamificados filtrados
- **Papel**: Fonte de informação sobre eventos de conclusão de agentes
- **Modificações**: Nenhuma necessária (já fornece eventos filtrados)

#### **ScreenplayInteractive**
- **Localização**: `src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts`
- **Responsabilidade**: Componente principal que orquestra screenplay, editor e agentes
- **Modificações Necessárias**:
  - Escutar evento `loadScreenplay` do `GamifiedPanelComponent`
  - Implementar lógica para identificar screenplay do projeto
  - Chamar método de carregamento (`openScreenplay()` ou similar)
  - Gerenciar estados de loading e erro

#### **ScreenplayStorage**
- **Localização**: `src/conductor-web/src/app/services/screenplay-storage.ts`
- **Responsabilidade**: Comunicação com API backend para CRUD de screenplays
- **Métodos Utilizados**:
  - `getScreenplays(search?, page?, limit?)`: Listar screenplays disponíveis
  - `getScreenplay(id)`: Buscar screenplay completa por ID
- **Modificações**: Nenhuma necessária (API já existe)

#### **ScreenplayFileManagementService**
- **Localização**: `src/conductor-web/src/app/services/screenplay-file-management.service.ts`
- **Responsabilidade**: Gerenciar importação/exportação de arquivos .md
- **Papel**: Pode ser usado se screenplay estiver em disco ao invés de MongoDB
- **Modificações**: Nenhuma necessária

### Backend (Python)

Não são necessárias modificações no backend, pois as APIs já existem:
- `GET /api/screenplays` (listagem)
- `GET /api/screenplays/{id}` (obter screenplay completa)

## 🔗 Relacionamentos e Dependências

### Cadeia de Componentes

```
ScreenplayInteractive (orquestrador)
    ├── GamifiedPanelComponent (painel de eventos)
    │   └── EventTickerComponent (lista de eventos)
    │       └── GamificationEventsService (eventos WebSocket)
    ├── InteractiveEditor (editor TipTap)
    │   └── ScreenplayService (sincronização editor)
    └── ScreenplayManager (modal gerenciamento)
        └── ScreenplayStorage (API HTTP)
```

### Fluxo de Dados

1. **WebSocket → GamificationEventsService**: Eventos de agentes chegam via WebSocket
2. **GamificationEventsService → EventTickerComponent**: Eventos são filtrados e exibidos
3. **EventTickerComponent → GamifiedPanelComponent**: Eventos passados via projeção de conteúdo
4. **GamifiedPanelComponent → ScreenplayInteractive**: Emit de evento `loadScreenplay`
5. **ScreenplayInteractive → ScreenplayStorage**: Busca screenplay via HTTP
6. **ScreenplayStorage → Backend API**: GET /api/screenplays
7. **Backend → ScreenplayStorage**: Retorna lista/screenplay
8. **ScreenplayInteractive → ScreenplayService**: Carrega screenplay no editor

## 💡 Regras de Negócio Identificadas

### **Regra 1**: Identificação da Screenplay do Projeto
- **Descrição**: O sistema precisa determinar qual screenplay carregar quando usuário clica no atalho
- **Implementação Sugerida**:
  - **Opção A**: Carregar a screenplay atualmente aberta (se houver)
  - **Opção B**: Carregar a última screenplay modificada/acessada
  - **Opção C**: Permitir usuário configurar uma "screenplay principal" (requer nova feature)
  - **Recomendação**: Opção A (screenplay atual) como primeira versão

### **Regra 2**: Visibilidade do Atalho
- **Descrição**: Quando o atalho deve ser exibido
- **Implementação**:
  - Sempre visível (acessível a qualquer momento)
  - Habilitado/desabilitado baseado em contexto (se há screenplay carregada)
  - Badge de notificação quando agente termina trabalho

### **Regra 3**: Comportamento ao Carregar
- **Descrição**: O que acontece quando screenplay é carregada
- **Implementação**:
  - Se já há screenplay aberta: perguntar se deseja substituir (modal de confirmação)
  - Se não há screenplay: carregar diretamente
  - Se há alterações não salvas: avisar usuário antes de substituir

### **Regra 4**: Tratamento de Erros
- **Descrição**: Como lidar com falhas no carregamento
- **Implementação**:
  - Screenplay não encontrada: exibir toast de erro + abrir modal de gerenciamento
  - Erro de rede: exibir toast com mensagem de reconexão
  - Timeout: exibir toast e permitir retry

## 🎓 Conceitos-Chave

### **Gamified Panel**
Painel visual na parte inferior da interface que exibe eventos dos agentes em formato de "notícias". Pode estar expandido (350px altura) ou recolhido (120px altura). Contém filtros (Todos, Resultados, Debug) e KPIs (agentes ativos, execuções totais, etc.).

### **Event Ticker**
Componente de lista de eventos que processa eventos do tipo `GamificationEvent` provenientes do `GamificationEventsService`. Filtra eventos por nível (`debug`, `info`, `result`) e exibe em formato de artigo de notícia.

### **Screenplay**
Roteiro em formato Markdown que descreve tarefas, agentes e processos do projeto. Pode ser armazenado em MongoDB ou em disco como arquivo `.md`. Possui estrutura:
```typescript
interface Screenplay {
  screenplay_id: string;
  title: string;
  content: string; // Markdown
  created_at: Date;
  updated_at: Date;
}
```

### **Agent Execution Events**
Eventos emitidos quando agentes começam ou terminam execução:
- `agent_execution_started`: Agente iniciou trabalho (nível `debug`)
- `agent_execution_completed`: Agente terminou trabalho (nível `result`)

Esses eventos são capturados via WebSocket e processados pelo `GamificationEventsService` (linhas 230-259 em `gamification-events.service.ts`).

### **Screenplay do Projeto**
Conceito que precisa ser definido: qual screenplay representa o roteiro principal/atual do projeto. Pode ser:
- A screenplay atualmente carregada no editor
- A última screenplay acessada (via localStorage ou session)
- Uma screenplay marcada como "principal" (feature futura)

## 📌 Viabilidade Técnica

### ✅ Aspectos Positivos

1. **Infraestrutura Existente**: Todos os serviços necessários já existem
   - `ScreenplayStorage` para buscar screenplays
   - `ScreenplayManager` para gerenciar carregamento
   - `GamificationEventsService` para detectar conclusão de agentes

2. **Arquitetura Preparada**: Sistema já usa padrão de eventos
   - `GamifiedPanelComponent` já possui `@Output` para eventos
   - `ScreenplayInteractive` já orquestra carregamento de screenplays

3. **API Backend Pronta**: Endpoints já implementados
   - GET `/api/screenplays` (listagem)
   - GET `/api/screenplays/{id}` (busca por ID)

4. **UX Consistente**: Padrões visuais estabelecidos
   - Botões no header do painel já existem (filtros, toggle)
   - Sistema de notificação (`NotificationToast`) já implementado

### ⚠️ Desafios e Considerações

1. **Definição de "Screenplay do Projeto"**
   - Não há conceito claro de qual screenplay é a "principal"
   - Pode causar confusão se usuário tiver múltiplas screenplays abertas
   - **Solução Proposta**: Usar screenplay atualmente carregada ou última acessada

2. **Espaço Visual no Painel**
   - Header já contém filtros e botão toggle
   - Adicionar mais um botão pode poluir interface
   - **Solução Proposta**: Usar footer do painel (quando expandido) ou ícone compacto no header

3. **Estado Recolhido vs Expandido**
   - No estado recolhido (120px), espaço é muito limitado
   - **Solução Proposta**: Atalho visível apenas quando expandido, ou ícone minimalista quando recolhido

4. **Contexto de Uso**
   - Usuário pode não querer carregar screenplay toda vez que agente termina
   - **Solução Proposta**: Atalho passivo (não carrega automaticamente, apenas torna ação disponível)

### 🛠️ Implementação Sugerida (MVP)

#### **Fase 1: Interface (GamifiedPanelComponent)**

Adicionar botão no **footer do painel** (visível apenas quando expandido):

```typescript
// gamified-panel.component.ts
@Output() loadScreenplay = new EventEmitter<void>();

loadProjectScreenplay(): void {
  this.loadScreenplay.emit();
}
```

Template (footer):
```html
<div class="panel-footer" *ngIf="state === 'expanded'">
  <div class="kpis">
    <!-- KPIs existentes -->
  </div>
  <button class="action-btn" (click)="loadProjectScreenplay()" title="Carregar screenplay do projeto">
    📜 Screenplay
  </button>
</div>
```

#### **Fase 2: Lógica de Carregamento (ScreenplayInteractive)**

Implementar handler no componente pai:

```typescript
// screenplay-interactive.ts
onLoadProjectScreenplay(): void {
  // 1. Verificar se já há screenplay carregada
  if (this.currentScreenplay) {
    // Opção: carregar a mesma novamente (refresh) ou não fazer nada
    this.notificationService.info('Screenplay já está carregada');
    return;
  }

  // 2. Buscar última screenplay ou screenplay padrão
  this.loading = true;
  this.screenplayStorage.getScreenplays('', 1, 1).subscribe({
    next: (response) => {
      if (response.items.length > 0) {
        const latestScreenplay = response.items[0];
        this.openScreenplay(latestScreenplay);
      } else {
        this.notificationService.warn('Nenhuma screenplay encontrada');
      }
      this.loading = false;
    },
    error: (err) => {
      this.notificationService.error('Erro ao carregar screenplay');
      this.loading = false;
    }
  });
}
```

#### **Fase 3: Persistência de Contexto (Opcional)**

Armazenar última screenplay acessada em `localStorage`:

```typescript
// Ao carregar screenplay
localStorage.setItem('last_screenplay_id', screenplay.screenplay_id);

// Ao usar atalho
const lastScreenplayId = localStorage.getItem('last_screenplay_id');
if (lastScreenplayId) {
  this.screenplayStorage.getScreenplay(lastScreenplayId).subscribe(/* ... */);
}
```

## 🎨 Proposta de Design

### Posicionamento do Atalho

**Opção Recomendada**: Footer do painel (quando expandido)

```
┌─────────────────────────────────────────────┐
│ Header: 📰 Notícias | [Filtros] [▲]        │
├─────────────────────────────────────────────┤
│ Body: EventTicker (lista de eventos)        │
│  🤖 Agente X - Sucesso (5s)                 │
│  🧪 Teste Agent - Erro (2s)                 │
│  📄 README Agent - Sucesso (10s)            │
├─────────────────────────────────────────────┤
│ Footer: [Agentes: 3] [Execuções: 15]       │
│         [📜 Screenplay] ← NOVO BOTÃO        │
└─────────────────────────────────────────────┘
```

### Estilos Sugeridos

```scss
.action-btn {
  padding: 6px 12px;
  font-size: 11px;
  font-weight: 600;
  color: #2563eb;
  background: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: #eff6ff;
    border-color: #2563eb;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
```

## 📊 Estimativa de Esforço

| Tarefa | Complexidade | Tempo Estimado |
|--------|--------------|----------------|
| Adicionar botão no `GamifiedPanelComponent` | Baixa | 1h |
| Implementar evento `@Output loadScreenplay` | Baixa | 30min |
| Criar handler em `ScreenplayInteractive` | Média | 2h |
| Implementar lógica de identificação de screenplay | Média | 2h |
| Adicionar tratamento de erros e loading | Baixa | 1h |
| Testes manuais e ajustes visuais | Baixa | 1h |
| **TOTAL** | **Média** | **~7.5h** |

## ✅ Conclusão

A implementação do atalho para carregar screenplay no `app-gamified-panel` é **tecnicamente viável** e **relativamente simples**, aproveitando infraestrutura existente. A principal decisão de design é definir **qual screenplay será carregada** (atual, última acessada ou configurável).

### Recomendação

**Implementar em 2 fases**:

1. **MVP (Quick Win)**: Botão que carrega a última screenplay acessada
   - Menor complexidade
   - Entrega rápida de valor
   - Usa localStorage para persistir última screenplay

2. **Evolução Futura**: Sistema de "screenplay principal/favorita"
   - Permite usuário marcar uma screenplay como padrão
   - Requer backend para persistir preferência
   - Melhor UX a longo prazo

### Próximos Passos

1. Validar com stakeholders qual screenplay deve ser carregada (última vs. principal vs. atual)
2. Definir posicionamento final do botão (footer vs. header)
3. Implementar MVP conforme especificado na Fase 1-3
4. Testar com usuários reais e coletar feedback
5. Iterar baseado em uso real

---

**Documento gerado em**: 2025-11-03
**Autor**: Requirements Engineer
**Versão**: 1.0
