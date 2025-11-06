# Análise de Requisitos: Editor Footer (class="editor-footer")

## 📋 Visão Geral

O **Editor Footer** é uma seção crítica da interface do editor de roteiros vivos (Living Screenplay), localizada na parte inferior da coluna central do editor. Sua função principal é exibir em tempo real informações sobre o estado de execução dos agentes, métricas do sistema e notícias sobre eventos de gamificação. Este componente é fundamental para fornecer feedback visual ao usuário sobre o que está acontecendo nos bastidores do sistema.

**Localização no código:** `screenplay-interactive.html:143`

```html
<div class="editor-footer">
  <app-gamified-panel
    [refreshMs]="30000"
    [isSaving]="isSaving"
    [isDirty]="isDirty"
    [hasCurrentScreenplay]="!!currentScreenplay"
    [showStatusInHeaderWhenCollapsed]="true"
    (settings)="openAgentPersonalization()"
    (stateChange)="onPanelStateChange($event)"
    (loadScreenplay)="onLoadProjectScreenplay()">
    <app-event-ticker
      [isExpanded]="isPanelExpanded"
      (select)="onTickerSelect($event)"
      (investigate)="onTickerInvestigate($event)">
    </app-event-ticker>
  </app-gamified-panel>
</div>
```

---

## 🎯 Requisitos Identificados

### Requisitos Funcionais

- **RF1**: O footer deve exibir um painel gamificado (GamifiedPanel) com notícias de eventos dos agentes em tempo real
- **RF2**: O painel deve suportar dois estados visuais: colapsado (120px) e expandido (350px)
- **RF3**: O sistema deve exibir indicadores visuais de status de salvamento (salvando, modificado, salvo)
- **RF4**: O painel deve mostrar métricas agregadas (KPIs) quando expandido: agentes ativos, total de execuções, última execução e investigações ativas
- **RF5**: O ticker de eventos deve permitir filtragem por nível: "Todos", "Resultados" ou "Debug"
- **RF6**: Os eventos devem ser ordenados do mais recente para o mais antigo
- **RF7**: O sistema deve suportar carregamento sob demanda ("carregar mais") quando há muitos eventos
- **RF8**: Cada evento deve exibir emoji do agente, nome, título, timestamp relativo e resumo (quando expandido ou for resultado)
- **RF9**: O painel deve permitir acesso rápido ao último screenplay carregado através de localStorage
- **RF10**: O sistema deve conectar via WebSocket para receber eventos em tempo real do backend

### Requisitos Não-Funcionais

- **RNF1**: Os KPIs devem ser atualizados automaticamente a cada 30 segundos (configurável via `refreshMs`)
- **RNF2**: O sistema deve manter um histórico máximo de 50 eventos em memória para evitar vazamento de memória
- **RNF3**: As atualizações de métricas devem usar debouncing (50ms) para evitar renderizações excessivas
- **RNF4**: O painel deve ter transições suaves (0.3s) ao expandir/colapsar
- **RNF5**: O sistema deve usar fallback para polling de métricas caso o WebSocket desconecte
- **RNF6**: Eventos devem ser processados com formatação Markdown (via biblioteca `marked`) e sanitização HTML
- **RNF7**: O componente deve ser responsivo e suportar diferentes tamanhos de tela

---

## 🔄 Fluxo do Processo

### 1. Inicialização do Componente

Quando a página é carregada, o componente `ScreenplayInteractive` inicializa o footer através dos seguintes passos:

1. **Montagem do DOM**: O Angular renderiza a estrutura HTML do `editor-footer` dentro da seção `screenplay-canvas`
2. **Inicialização do GamifiedPanel**: O componente `app-gamified-panel` é criado com estado inicial "colapsado"
3. **Configuração de Inputs**: Propriedades reativas são vinculadas do componente pai:
   - `isSaving`: Estado de salvamento do screenplay
   - `isDirty`: Indica se há modificações não salvas
   - `hasCurrentScreenplay`: Verifica se existe screenplay carregado
   - `isPanelExpanded`: Estado de expansão (vinculado a `onPanelStateChange`)
4. **Inicialização do EventTicker**: Componente filho que gerencia a lista de eventos
5. **Conexão WebSocket**: O serviço `GamificationWebSocketService` estabelece conexão com o backend em `ws://localhost:8000/ws/gamification`

### 2. Fluxo de Dados em Tempo Real

O sistema possui duas fontes de dados que alimentam o footer:

#### A) WebSocket (Fonte Primária - Real-time)

1. **Conexão**: Frontend conecta ao endpoint `/ws/gamification` do backend
2. **Autenticação**: Cliente recebe `client_id` único
3. **Subscrição**: Por padrão, inscreve-se em todos os tipos de eventos (`"all"`)
4. **Recepção de Eventos**: Backend envia eventos JSON com estrutura:
   ```json
   {
     "type": "agent_execution_completed",
     "data": {
       "agentId": "uuid-v4",
       "agentName": "Performance Agent",
       "agentEmoji": "🚀",
       "summary": "Análise concluída com sucesso...",
       "severity": "info"
     },
     "timestamp": 1699999999999
   }
   ```
5. **Processamento**: `GamificationEventsService` recebe evento e o transforma em `GamificationEvent`
6. **Atualização do UI**: `EventTickerComponent` recebe novo evento via Observable `events$`
7. **Renderização**: Evento aparece instantaneamente no ticker

#### B) Polling de Métricas (Fonte Secundária - Fallback)

Caso o WebSocket falhe ou desconecte:

1. **Detecção**: `GamificationEventsService` detecta desconexão via `websocketService.isConnected()`
2. **Ativação de Fallback**: Sistema ativa polling de métricas via `AgentMetricsService`
3. **Polling**: A cada 30 segundos, serviço consulta `AgentExecutionService.agentState$`
4. **Derivação de Eventos**: Sistema detecta mudanças em `totalExecutions` e cria eventos artificiais
5. **Exibição**: Eventos derivados são exibidos normalmente no ticker

### 3. Atualização de KPIs (Métricas)

O GamifiedPanel exibe métricas agregadas quando expandido:

1. **Inicialização**: No `ngOnInit`, componente se inscreve em `AgentMetricsService.metrics$`
2. **Timer**: Interval de 30 segundos (ou `refreshMs`) dispara `refreshKpis()`
3. **Cálculo**: Sistema agrega dados de todos os agentes:
   - **Agentes Ativos**: Conta agentes com `isCurrentlyExecuting === true`
   - **Total de Execuções**: Soma de `totalExecutions` de todos os agentes
   - **Última Execução**: Maior timestamp de `lastExecutionTime` convertido em formato relativo (ex: "5m", "2h", "3d")
   - **Investigações Ativas**: Obtido via `ScreenplayKpiService.investigationsActive$`
4. **Renderização**: Valores são exibidos em tempo real na seção `panel-footer`

### 4. Interação do Usuário

#### Expandir/Colapsar Painel

1. **Ação**: Usuário clica no botão "▲" (expandido) ou "▼" (colapsado)
2. **Evento**: `toggleState()` alterna entre estados
3. **Propagação**: Emite evento `stateChange` para componente pai
4. **Atualização de Limite**: `EventTicker` ajusta limite de exibição:
   - Colapsado: 3 eventos
   - Expandido: 10 eventos
5. **Animação CSS**: Altura do painel transiciona suavemente (0.3s ease)

#### Filtrar Eventos

1. **Ação**: Usuário clica em botão de filtro ("Todos", "Resultados", "Debug")
2. **Evento**: `ticker.setFilter(filterType)` é chamado
3. **Filtragem**: Sistema aplica filtro em `allEvents`:
   - `"all"`: Mostra todos os eventos
   - `"result"`: Mostra apenas eventos com `level === "result"`
   - `"debug"`: Mostra apenas eventos com `level === "debug"`
4. **Re-renderização**: Lista filtrada é exibida

#### Carregar Mais Eventos

1. **Ação**: Usuário clica em "Carregar mais" no footer do ticker
2. **Incremento**: `itemsLimit` aumenta em 10
3. **Atualização**: Sistema re-aplica filtro com novo limite
4. **Exibição**: Mais eventos são renderizados

#### Selecionar Evento

1. **Ação**: Usuário clica em um card de evento
2. **Emissão**: EventTicker emite evento `(select)` com objeto `GamificationEvent`
3. **Propagação**: Evento sobe para `ScreenplayInteractive` via `onTickerSelect(event)`
4. **Ação Futura**: (Fase 4) Pode abrir modal de detalhes ou iniciar investigação

#### Carregar Screenplay do Projeto

1. **Ação**: Usuário clica em botão "📜 Screenplay" no footer (quando expandido)
2. **Emissão**: GamifiedPanel emite evento `(loadScreenplay)`
3. **Handler**: `ScreenplayInteractive.onLoadProjectScreenplay()` é executado
4. **Recuperação**: Sistema busca `last_screenplay_id` do `localStorage`
5. **Carregamento**: Se ID existe, carrega screenplay via `ScreenplayStorage.getScreenplay(id)`
6. **Fallback**: Se ID não existe ou screenplay foi deletada, carrega screenplay mais recente via API

---

## 🏗️ Componentes Principais

### Frontend (Angular)

#### 1. **GamifiedPanelComponent** (`gamified-panel.component.ts`)
   - **Responsabilidade**: Container principal do footer, gerencia estado de expansão e exibição de KPIs
   - **Inputs**:
     - `refreshMs`: Intervalo de atualização de métricas (padrão: 30000ms)
     - `isSaving`: Flag de salvamento em progresso
     - `isDirty`: Flag de modificações não salvas
     - `hasCurrentScreenplay`: Verifica existência de screenplay
     - `showStatusInHeaderWhenCollapsed`: Exibe status compacto quando colapsado
   - **Outputs**:
     - `stateChange`: Emitido quando painel expande/colapsa
     - `loadScreenplay`: Emitido quando usuário quer carregar screenplay
     - `settings`: Emitido quando usuário abre personalização (Fase 2)
   - **Serviços Utilizados**:
     - `AgentMetricsService`: Para obter métricas agregadas
     - `ScreenplayKpiService`: Para investigações ativas
   - **Estados**: `collapsed` (120px) | `expanded` (350px)

#### 2. **EventTickerComponent** (`event-ticker.component.ts`)
   - **Responsabilidade**: Exibe lista de eventos em formato de feed de notícias
   - **Inputs**:
     - `isExpanded`: Estado de expansão recebido do painel pai
     - `collapsedLimit`: Limite de eventos quando colapsado (padrão: 3)
     - `expandedLimit`: Limite de eventos quando expandido (padrão: 10)
   - **Outputs**:
     - `select`: Emitido quando usuário clica em evento
     - `investigate`: Emitido quando usuário solicita investigação (Fase 4)
   - **Serviços Utilizados**:
     - `GamificationEventsService`: Observable de eventos em tempo real
     - `DomSanitizer`: Sanitiza HTML renderizado de Markdown
   - **Filtros**: `all`, `result`, `debug`
   - **Formatação**: Markdown via biblioteca `marked`

#### 3. **ScreenplayInteractive** (`screenplay-interactive.ts`)
   - **Responsabilidade**: Componente pai que gerencia todo o editor, incluindo o footer
   - **Propriedades Relacionadas ao Footer**:
     - `isPanelExpanded`: Estado de expansão do painel (padrão: `false`)
     - `isSaving`: Estado de salvamento
     - `isDirty`: Flag de modificações não salvas
     - `currentScreenplay`: Screenplay atual carregado
   - **Métodos Relacionados**:
     - `onPanelStateChange(state)`: Atualiza `isPanelExpanded` quando painel muda de estado
     - `onTickerSelect(event)`: Handler para seleção de evento
     - `onTickerInvestigate(event)`: Handler para investigação (Fase 4)
     - `onLoadProjectScreenplay()`: Carrega último screenplay via localStorage

### Serviços (Angular)

#### 4. **GamificationEventsService** (`gamification-events.service.ts`)
   - **Responsabilidade**: Gerencia fluxo de eventos de gamificação e mantém histórico
   - **Observable Principal**: `events$: Observable<GamificationEvent[]>`
   - **Propriedades**:
     - `maxEvents`: 50 (limite de histórico em memória)
     - `eventsSubject`: BehaviorSubject que emite lista de eventos
   - **Fontes de Eventos**:
     1. **WebSocket** (Primário): `GamificationWebSocketService.events$`
     2. **Métricas** (Fallback): `AgentMetricsService.metrics$`
   - **Métodos Principais**:
     - `pushEvent(event)`: Adiciona novo evento ao histórico
     - `getRecent(limit)`: Retorna últimos N eventos
     - `deriveExecutionEvents(metricsMap)`: Cria eventos a partir de mudanças em métricas
     - `handleWebSocketEvent(event)`: Processa eventos do WebSocket

#### 5. **AgentMetricsService** (`agent-metrics.service.ts`)
   - **Responsabilidade**: Agrega métricas de execução de todos os agentes
   - **Observable Principal**: `metrics$: Observable<Map<string, AgentExecutionMetrics>>`
   - **Estrutura de Métrica**:
     ```typescript
     interface AgentExecutionMetrics {
       totalExecutions: number;
       totalExecutionTime: number;
       averageExecutionTime: number;
       lastExecutionTime?: Date;
       isCurrentlyExecuting: boolean;
     }
     ```
   - **Otimizações**:
     - Debouncing de 50ms para evitar atualizações excessivas
     - Processamento em lote via `requestAnimationFrame`
     - Fila de atualizações para agrupar mudanças

#### 6. **GamificationWebSocketService** (`gamification-websocket.service.ts`)
   - **Responsabilidade**: Gerencia conexão WebSocket com backend para eventos em tempo real
   - **Endpoint**: `ws://localhost:8000/ws/gamification`
   - **Observable Principal**: `events$: Observable<GamificationWebSocketEvent>`
   - **Métodos**:
     - `connect()`: Estabelece conexão WebSocket
     - `disconnect()`: Encerra conexão
     - `isConnected()`: Verifica estado da conexão
   - **Reconexão Automática**: Sim (implementado no serviço)

#### 7. **ScreenplayStorage** (`screenplay-storage.ts`)
   - **Responsabilidade**: Comunicação com API backend para operações de screenplay
   - **Base URL**: `/api/screenplays`
   - **Métodos Relevantes**:
     - `getScreenplay(id)`: Busca screenplay por ID (usado no carregamento via localStorage)
     - `getScreenplays(search, page, limit)`: Lista screenplays com paginação

#### 8. **ScreenplayKpiService** (`screenplay-kpi.service.ts`)
   - **Responsabilidade**: Gerencia KPIs específicos de screenplay
   - **Observable Principal**: `investigationsActive$: Observable<number>`
   - **Função**: Fornece contador de investigações ativas para exibição no footer

---

## 🔗 Relacionamentos e Dependências

### Hierarquia de Componentes

```
ScreenplayInteractive (screenplay-interactive.ts)
  └── <div class="editor-footer">
        └── GamifiedPanelComponent (gamified-panel.component.ts)
              ├── Header (título + filtros + status compacto)
              ├── Body (ng-content)
              │     └── EventTickerComponent (event-ticker.component.ts)
              │           ├── Lista de eventos (news-article)
              │           └── Footer "Carregar mais"
              └── Footer (KPIs + botão "Screenplay")
```

### Fluxo de Dados

```
Backend (FastAPI + MongoDB)
  │
  ├─── WebSocket (/ws/gamification)
  │      │
  │      └──> GamificationWebSocketService
  │             │
  │             └──> GamificationEventsService ──┐
  │                                              │
  ├─── REST API (/api/screenplays)              │
  │      │                                       │
  │      └──> ScreenplayStorage                 │
  │                                              │
  └─── Métricas (via AgentExecutionService)     │
         │                                       │
         └──> AgentMetricsService ──────────────┤
                                                 │
                                                 v
                                    EventTickerComponent
                                    (exibe eventos no UI)
```

### Dependências de Injeção

- **GamifiedPanelComponent** depende de:
  - `AgentMetricsService`
  - `ScreenplayKpiService`

- **EventTickerComponent** depende de:
  - `GamificationEventsService`
  - `DomSanitizer`

- **GamificationEventsService** depende de:
  - `AgentMetricsService`
  - `AgentPersonalizationService`
  - `GamificationWebSocketService`

- **ScreenplayInteractive** depende de:
  - `ScreenplayService`
  - `ScreenplayStorage`
  - `AgentExecutionService`
  - `GamificationEventsService`
  - `NotificationService`
  - `ScreenplayKpiService`
  - (e outros 7+ serviços)

---

## 💡 Regras de Negócio Identificadas

### 1. **Persistência de Estado via localStorage**
   - **Regra**: O sistema deve salvar o ID do último screenplay carregado em `localStorage` com chave `'last_screenplay_id'`
   - **Implementação**:
     - Salvamento em `screenplay-interactive.ts:2251` dentro de `loadScreenplayIntoEditor()`
     - Recuperação em `screenplay-interactive.ts:357` dentro de `onLoadProjectScreenplay()`
   - **Comportamento**: Quando usuário clica em "📜 Screenplay", sistema tenta carregar último screenplay acessado

### 2. **Limite de Eventos em Memória**
   - **Regra**: Sistema deve manter no máximo 50 eventos em memória para evitar vazamento
   - **Implementação**: `gamification-events.service.ts:29` define `maxEvents = 50`
   - **Comportamento**: Quando novo evento é adicionado via `pushEvent()`, se lista exceder 50, eventos mais antigos são descartados

### 3. **Priorização de WebSocket sobre Polling**
   - **Regra**: Eventos em tempo real têm prioridade; polling só é ativado se WebSocket desconectar
   - **Implementação**: `gamification-events.service.ts:49-56` verifica `websocketService.isConnected()` antes de derivar eventos de métricas
   - **Comportamento**: Frontend sempre prefere dados em tempo real; fallback é transparente ao usuário

### 4. **Filtragem Padrão de Eventos**
   - **Regra**: Por padrão, apenas eventos de nível "result" são exibidos no ticker
   - **Implementação**: `event-ticker.component.ts:310` define `currentFilter = 'result'`
   - **Comportamento**: Usuário vê apenas resultados importantes; pode alternar para "Todos" ou "Debug"

### 5. **Limite Dinâmico de Exibição**
   - **Regra**: Quantidade de eventos exibidos depende do estado de expansão do painel
   - **Implementação**:
     - Colapsado: `collapsedLimit = 3` (event-ticker.component.ts:304)
     - Expandido: `expandedLimit = 10` (event-ticker.component.ts:305)
   - **Comportamento**: Ao expandir painel, mais eventos aparecem automaticamente

### 6. **Formatação de Tempo Relativo**
   - **Regra**: Timestamps devem ser exibidos em formato relativo humanizado (ex: "5m atrás", "2h atrás")
   - **Implementação**: `event-ticker.component.ts:368-377` e `gamified-panel.component.ts:319-329`
   - **Comportamento**: Usuário vê tempo de forma intuitiva; hover mostra timestamp absoluto

### 7. **Sanitização de Markdown**
   - **Regra**: Todo conteúdo Markdown deve ser processado com `marked` e sanitizado com `DomSanitizer` para prevenir XSS
   - **Implementação**: `event-ticker.component.ts:389-396` usa `marked()` + `bypassSecurityTrustHtml()`
   - **Comportamento**: Sumários de eventos podem conter formatação rica (negrito, listas, links) de forma segura

### 8. **Truncamento Inteligente de Resumos**
   - **Regra**: Resumos de eventos devem ser truncados baseado no estado de expansão
   - **Implementação**: `event-ticker.component.ts:389-396`
     - Colapsado: 150 caracteres
     - Expandido: 500 caracteres
   - **Comportamento**: Resumos longos são encurtados com "..." para manter UI limpa

### 9. **Auto-refresh de KPIs**
   - **Regra**: Métricas devem ser atualizadas automaticamente a cada intervalo configurável
   - **Implementação**: `gamified-panel.component.ts:283` cria interval com `refreshMs` (padrão: 30000ms)
   - **Comportamento**: Usuário sempre vê dados atualizados sem precisar atualizar página

### 10. **Fallback para Screenplay Mais Recente**
   - **Regra**: Se última screenplay acessada não existir ou foi deletada, carregar screenplay mais recente
   - **Implementação**: `screenplay-interactive.ts:366-383`
   - **Comportamento**: Sistema nunca deixa usuário "sem screenplay"; sempre há fallback

### 11. **Detecção de Screenplay Deletada**
   - **Regra**: Se screenplay tem flag `isDeleted = true`, deve ser considerada inválida
   - **Implementação**: `screenplay-interactive.ts:366` verifica `screenplay.isDeleted`
   - **Comportamento**: Sistema remove ID do localStorage e notifica usuário com warning

---

## 🎓 Conceitos-Chave

### Gamificação de Eventos
O sistema utiliza uma abordagem de "gamificação" para tornar logs técnicos mais envolventes. Eventos são apresentados como "notícias" de agentes, com emojis, nomes humanizados e narrativas contextualizadas.

### Event Sourcing em Tempo Real
O footer implementa uma versão simplificada de Event Sourcing, onde:
- Eventos são imutáveis (uma vez criados, não são modificados)
- Eventos têm timestamps únicos
- Histórico é mantido em memória (últimos 50 eventos)
- UI se atualiza reativamente via Observables

### Arquitetura Reativa (RxJS)
Todo o sistema de eventos usa programação reativa com RxJS:
- `BehaviorSubject` para estado compartilhado
- `Observable.pipe()` para transformações
- Operadores como `debounceTime`, `distinctUntilChanged`, `map`, `catchError`

### Dual-Source Pattern
O footer implementa padrão de "fonte dupla" para resiliência:
1. **Fonte Primária**: WebSocket (baixa latência, real-time)
2. **Fonte Secundária**: Polling (fallback quando WebSocket falha)

Este padrão garante que UI sempre tenha dados atualizados, mesmo em caso de instabilidade de rede.

### Progressive Disclosure
O design do painel usa "divulgação progressiva" de informação:
- Estado colapsado: Informações mínimas (3 eventos, status compacto)
- Estado expandido: Informações completas (10+ eventos, KPIs, filtros)

### Content Projection (ng-content)
`GamifiedPanelComponent` usa projeção de conteúdo para compor UI:
```html
<app-gamified-panel>
  <app-event-ticker></app-event-ticker>
</app-gamified-panel>
```
Isso permite separação de responsabilidades: painel gerencia layout/estado, ticker gerencia conteúdo.

### localStorage como Cache de UX
O sistema usa `localStorage` não apenas para persistência, mas como **cache de experiência do usuário**:
- Última aba ativa da coluna lateral (`firstColumnActiveTab`)
- Último screenplay acessado (`last_screenplay_id`)

Isso melhora UX ao preservar contexto do usuário entre sessões.

---

## 🔍 Problema da Perda de Dados no Reload

### Causa Raiz

**O problema ocorre porque os dados exibidos no editor-footer são armazenados APENAS EM MEMÓRIA (RAM), e não persistidos em localStorage, sessionStorage ou banco de dados.**

#### Detalhamento Técnico

1. **Estado Volátil em Memória**:
   - O `GamificationEventsService` mantém eventos em um `BehaviorSubject` que vive apenas durante a sessão do Angular
   - Quando a página é recarregada (F5), o JavaScript é reinicializado e todos os observables são recriados vazios
   - Não há código para **serializar** eventos para `localStorage` antes do reload
   - Não há código para **deserializar** eventos de `localStorage` após o reload

2. **Fluxo do Problema**:
   ```
   1. Usuário usa aplicação normalmente
      └─> Eventos acumulam em GamificationEventsService.eventsSubject

   2. Usuário pressiona F5 (reload)
      └─> Navegador destroi contexto JavaScript
          └─> Memória é liberada
              └─> eventsSubject é destruído
                  └─> TODOS OS EVENTOS SÃO PERDIDOS

   3. Angular reinicializa
      └─> GamificationEventsService cria novo eventsSubject VAZIO
          └─> EventTickerComponent recebe lista vazia
              └─> UI mostra "Nenhum evento recente"
   ```

3. **Fontes de Dados Temporárias**:
   - **WebSocket**: Conecta após reload, mas backend **não reenvia eventos antigos** (só envia novos eventos que ocorrem após conexão)
   - **Polling de Métricas**: Só detecta **novas execuções** (diferença entre contadores), não recupera histórico
   - **Backend não armazena histórico de eventos UI**: Os eventos de gamificação são gerados em tempo real e enviados via WebSocket, mas não são persistidos em MongoDB

4. **Evidências no Código**:

   **gamification-events.service.ts (linha 25-26)**:
   ```typescript
   private readonly eventsSubject = new BehaviorSubject<GamificationEvent[]>([]);
   public readonly events$: Observable<GamificationEvent[]> = this.eventsSubject.asObservable();
   ```
   ↳ Array inicial vazio `[]`, sem recuperação de `localStorage`

   **gamification-events.service.ts (linha 67-71)**:
   ```typescript
   pushEvent(event: GamificationEvent): void {
     const list = [...this.eventsSubject.value, event];
     const bounded = list.length > this.maxEvents ? list.slice(list.length - this.maxEvents) : list;
     this.eventsSubject.next(bounded);
   }
   ```
   ↳ Adiciona eventos em memória, mas **não persiste** em `localStorage`

   **Nenhum código de serialização encontrado**:
   ```typescript
   // ❌ NÃO EXISTE no código atual
   localStorage.setItem('gamification_events', JSON.stringify(events));
   ```

   **Nenhum código de deserialização encontrado**:
   ```typescript
   // ❌ NÃO EXISTE no código atual
   const cached = localStorage.getItem('gamification_events');
   if (cached) {
     this.eventsSubject.next(JSON.parse(cached));
   }
   ```

### Comparação com Outros Dados que Persistem

Para entender melhor o problema, vejamos dados que **NÃO são perdidos** no reload:

| Dado | Persiste no Reload? | Motivo |
|------|---------------------|--------|
| **Eventos de Gamificação** | ❌ NÃO | Apenas em memória (BehaviorSubject) |
| **Conteúdo do Screenplay** | ✅ SIM | Salvo em MongoDB via API `/api/screenplays` |
| **ID do Último Screenplay** | ✅ SIM | Salvo em `localStorage.getItem('last_screenplay_id')` |
| **Aba Ativa da Coluna** | ✅ SIM | Salvo em `localStorage.getItem('firstColumnActiveTab')` |
| **Instâncias de Agentes** | ✅ SIM | Salvas em MongoDB (coleção `agent_instances`) |
| **Métricas de Execução** | ⚠️ PARCIAL | Re-calculadas do MongoDB após reload |

### Por que o Backend Não Ajuda?

O backend **não persiste eventos de gamificação** em MongoDB por design:

1. **Eventos são Efêmeros**: Projetados para serem notificações transientes, não registros permanentes
2. **Volume Alto**: Persistir todos os eventos geraria muitos dados (cada execução = múltiplos eventos)
3. **WebSocket é Stateless**: Backend só envia eventos para clientes conectados no momento; não mantém fila de eventos antigos

### Impacto no Usuário

Quando o usuário recarrega a página:

1. **Perde contexto visual**: Não sabe mais o que aconteceu recentemente
2. **Perde histórico de debug**: Logs de execução são perdidos
3. **Experiência fragmentada**: Sente que aplicação "resetou"
4. **Confiança reduzida**: Pode achar que sistema é instável

### Soluções Possíveis (Fora do Escopo desta Análise)

Esta documentação identifica o problema, mas não propõe soluções. Possíveis abordagens incluiriam:

1. **Persistência em localStorage**: Serializar eventos antes de `beforeunload`
2. **Persistência no Backend**: Criar coleção `gamification_events` no MongoDB
3. **IndexedDB**: Armazenar eventos localmente com maior capacidade
4. **Session Replay**: Backend mantém buffer de últimos N eventos por sessão

---

## 📌 Observações

### Pontos Fortes da Arquitetura

1. **Separação de Responsabilidades**: Cada componente tem função bem definida
2. **Reatividade**: Uso consistente de Observables para propagação de mudanças
3. **Resiliência**: Fallback automático quando WebSocket falha
4. **Performance**: Debouncing e throttling evitam renderizações excessivas
5. **UX Adaptativo**: UI se adapta ao estado de expansão/colapso
6. **Segurança**: Sanitização de HTML previne XSS

### Limitações Identificadas

1. **Perda de Dados no Reload**: Eventos não persistem entre reloads (detalhado acima)
2. **Histórico Limitado**: Apenas 50 eventos em memória
3. **Sem Busca/Filtro Avançado**: Usuário não pode buscar eventos antigos por texto
4. **Eventos Não Recuperáveis**: Uma vez perdidos (>50 ou reload), não há como recuperar
5. **WebSocket Único**: Sem suporte a múltiplas conexões ou reconexão com buffer
6. **KPIs Agregados Limitados**: Não mostra histórico de métricas, apenas snapshot atual

### Oportunidades de Melhoria (Sugestões Enxutas)

Se solicitado pelo usuário, potenciais melhorias incluiriam:

1. **Persistência Local**: Implementar `localStorage` para eventos (requisito claro do usuário)
2. **Paginação de Histórico**: Backend poderia manter últimos 500 eventos e fornecer via API
3. **Busca de Eventos**: Campo de busca para filtrar por agente, tipo ou texto
4. **Exportação**: Botão para exportar eventos como JSON ou CSV
5. **Configurabilidade**: Usuário poder ajustar limite de eventos, intervalo de refresh, etc.
6. **Indicadores Visuais Melhorados**: Badges para criticidade, animações para novos eventos

### Dependências Externas Críticas

- **MongoDB**: Banco de dados para screenplays e agentes
- **FastAPI**: Backend que fornece WebSocket e REST API
- **WebSocket**: Protocolo para comunicação em tempo real
- **marked**: Biblioteca para parsing de Markdown
- **RxJS**: Biblioteca para programação reativa
- **Angular 17+**: Framework frontend

### Compatibilidade de Browser

O sistema requer:
- **WebSocket API**: Suportado em todos os browsers modernos
- **localStorage API**: Suportado universalmente
- **CSS Grid/Flexbox**: Para layout responsivo
- **ES6+ Features**: Promises, async/await, Map, Set

---

## 📊 Mapeamento de Arquivos

### Frontend (Angular)

| Arquivo | Caminho Completo | Função |
|---------|-----------------|--------|
| **Template HTML** | `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html:143` | Define estrutura do editor-footer |
| **Componente Principal** | `conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts` | Gerencia todo o editor, incluindo footer |
| **GamifiedPanel** | `conductor-web/src/app/living-screenplay-simple/gamified-panel/gamified-panel.component.ts` | Painel gamificado com KPIs |
| **EventTicker** | `conductor-web/src/app/living-screenplay-simple/event-ticker/event-ticker.component.ts` | Feed de eventos em tempo real |
| **GamificationEventsService** | `conductor-web/src/app/services/gamification-events.service.ts` | Gerencia fluxo de eventos |
| **AgentMetricsService** | `conductor-web/src/app/services/agent-metrics.service.ts` | Agrega métricas de execução |
| **ScreenplayStorage** | `conductor-web/src/app/services/screenplay-storage.ts` | Comunicação com API de screenplays |
| **ScreenplayKpiService** | `conductor-web/src/app/services/screenplay-kpi.service.ts` | KPIs de screenplay |
| **GamificationWebSocketService** | `conductor-web/src/app/services/gamification-websocket.service.ts` | Gerencia WebSocket |

### Backend (Python/FastAPI)

| Arquivo | Caminho Completo | Função |
|---------|-----------------|--------|
| **WebSocket Manager** | `conductor-gateway/src/api/websocket.py` | Gerencia conexões WebSocket |
| **Screenplay Router** | `conductor-gateway/src/api/routers/screenplays.py` | API REST para screenplays |
| **App Principal** | `conductor-gateway/src/api/app.py` | Configuração FastAPI e lifespan |

---

## 🎯 Conclusão

O **editor-footer** é um componente crítico da aplicação Conductor que fornece feedback em tempo real sobre execução de agentes e estado do sistema. Sua arquitetura reativa baseada em WebSocket + fallback de polling garante que usuário sempre tenha visibilidade do que está acontecendo nos bastidores.

**Problema Central Identificado**: Os dados exibidos no footer (eventos de gamificação, métricas) são voláteis e **perdidos ao recarregar a página** porque residem apenas em memória RAM do Angular. Não há persistência em `localStorage`, `sessionStorage` ou banco de dados. O backend não armazena histórico de eventos, apenas os emite em tempo real via WebSocket para clientes conectados.

**Impacto**: Usuário perde contexto visual e histórico de debug ao fazer reload da página, resultando em experiência fragmentada.

**Requisitos Funcionais Críticos**: O sistema precisa implementar persistência de eventos em `localStorage` (serialização antes de `beforeunload` + deserialização no `ngOnInit`) para resolver o problema de perda de dados.

---

## 📚 Referências Técnicas

- **Angular Reactive Forms**: https://angular.io/guide/reactive-forms
- **RxJS Observables**: https://rxjs.dev/guide/observable
- **WebSocket API**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **marked (Markdown Parser)**: https://marked.js.org/
- **FastAPI WebSockets**: https://fastapi.tiangolo.com/advanced/websockets/
- **localStorage API**: https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage
- **MongoDB Change Streams**: https://www.mongodb.com/docs/manual/changeStreams/

---

**Documento gerado em**: 2025-11-05
**Versão**: 1.0.0
**Autor**: Claude (Requirements Engineer)
**Última atualização**: 2025-11-05
