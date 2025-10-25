# Saga 004 v2: Painel Gamificado "Jornal da Cidade" no Screenplay

## 📋 Contexto & Background

### Situação Atual (v1)
A v1 da barra de comandos foi implementada com sucesso técnico, mas apresenta limitações de design e gamificação:
- Barra horizontal compacta (36px altura) dificulta leitura
- Mensagens técnicas ("agent-id") em vez de linguagem humanizada
- Scroll lateral indesejado em telas pequenas
- Eventos são terminais, sem ações de aprofundamento
- Sem personalização de agentes com nomes humanos

### Nova Visão (v2): "Jornal da Cidade"
Transformar a barra em um **painel expansível vertical** inspirado em jornais de jogos de estratégia (SimCity, Tropico), onde:
- **Manchetes gamificadas** aparecem como notícias de uma cidade ("🏗️ Secretário João detectou monolito no Bairro Central")
- **Agentes personalizados** têm nomes humanos e emojis de "cargo" (🔍 Inspetor, 🏛️ Ministro, 📊 Analista)
- **Ações de investigação** permitem lançar agentes especializados para aprofundar problemas
- **Scroll vertical** para ler histórico de eventos confortavelmente
- **Altura ajustável** (colapsada 60px / expandida 200-400px)

## 🎯 Objetivos v2

1. **Redesenhar o layout** para painel vertical expansível (não apenas uma barra horizontal fina)
2. **Humanizar mensagens** com linguagem de notícias/jornal da cidade
3. **Implementar sistema de personalização** para agentes (nomes, cargos, avatares)
4. **Adicionar botões de ação** nos eventos para lançar "agentes investigadores"
5. **Eliminar scroll horizontal**, adotar scroll vertical no painel expandido
6. **Melhorar gamificação** com categorias de eventos (🏗️ Construção, 🔥 Urgente, 📊 Relatório, 🎉 Conquista)

## 🔍 Escopo v2

### In-Scope

**Layout & Design:**
- Painel com 3 estados: `collapsed` (60px), `normal` (120px), `expanded` (300px)
- Botão de expansão/colapso no canto direito
- Scroll vertical dentro do painel expandido
- Grid responsivo que acomoda KPIs + feed verticalmente

**Personalização de Agentes:**
- Novo serviço `AgentPersonalizationService` para mapear `agentId` → `{name, role, emoji}`
- Persistência em `localStorage` ou MongoDB (coleção `agent_profiles`)
- UI de configuração: modal "Gerenciar Secretários" com lista de agentes editáveis
- Nomes padrão auto-gerados se não configurados (ex: "Inspetor Alpha", "Analista Beta")

**Humanização de Eventos:**
- Reescrever templates de mensagens no `GamificationEventsService`
- Usar linguagem de jornal: "🔍 Inspetor Maria concluiu ronda no módulo Auth"
- Categorias visuais: 🏗️ Build, 🔥 Crítico, 📊 Análise, 🎉 Sucesso, ⚠️ Alerta
- Texto compacto (max 60 caracteres) no modo collapsed, completo no expanded

**Agentes Investigadores:**
- Botão "🔎 Investigar" em cada evento no painel expandido
- Ao clicar, abre modal "Lançar Investigação" com:
  - Seleção de agente especialista (ex: "Code Quality Analyst", "Performance Investigator")
  - Campo de contexto adicional (textarea)
  - Botão "Iniciar Investigação" que cria uma nova instância de agente com prompt contextualizado
- Integração com o sistema de agentes do Screenplay (reutilizar lógica de `onAgentSelected`)

**KPIs Redesenhados:**
- Mover KPIs para seção superior do painel (sempre visível mesmo collapsed)
- Adicionar KPI "Investigações Ativas" (contagem de agentes investigadores em execução)
- KPI com cores dinâmicas: verde (saudável), amarelo (atenção), vermelho (crítico)
- Mini-gráficos sparkline (opcional) para tendências semanais

### Out-of-Scope (mantido da v1)

- Criação de novos endpoints backend (reutilizar APIs existentes)
- Alterações no `AgentGameComponent` (canvas permanece independente)
- Sistema complexo de conquistas/achievements (gamificação futura)
- Tradução i18n (manter pt-BR por ora)

## 💡 Solução Proposta v2

### Arquitetura de Componentes

```
┌─────────────────────────────────────────────────────────┐
│ screenplay-interactive.html                             │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ .editor-footer (flexível, min-height:60px)          │ │
│ │ ┌──────────────────────────────────────────────────┐│ │
│ │ │ <app-gamified-panel>                             ││ │
│ │ │   [state]="panelState" (investigate)="..."       ││ │
│ │ │ ┌──────────────────────────────────────────────┐ ││ │
│ │ │ │ Header: KPIs + Botão Expand/Collapse         │ ││ │
│ │ │ ├──────────────────────────────────────────────┤ ││ │
│ │ │ │ Body (se expanded):                          │ ││ │
│ │ │ │  <app-news-ticker [events]="..."             │ ││ │
│ │ │ │     (investigate)="...">                     │ ││ │
│ │ │ │  - Scroll vertical                           │ ││ │
│ │ │ │  - Botões de ação por evento                 │ ││ │
│ │ │ └──────────────────────────────────────────────┘ ││ │
│ │ └──────────────────────────────────────────────────┘│ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Novos Componentes

1. **`GamifiedPanelComponent`** (substitui `CommandBarComponent`)
   - Gerencia estados: collapsed/normal/expanded
   - Renderiza KPIs no header sempre visível
   - Contém slot para `NewsTickerComponent` no body

2. **`NewsTickerComponent`** (evolução do `EventTickerComponent`)
   - Lista vertical (não horizontal) de eventos
   - Cada item tem: emoji de categoria + manchete + tempo + botão "Investigar"
   - Scroll vertical com max-height

3. **`InvestigationLauncherComponent`** (novo)
   - Modal para configurar e lançar agente investigador
   - Inputs: tipo de agente, contexto adicional, prioridade
   - Output: emite evento para criar instância de agente

4. **`AgentPersonalizationModalComponent`** (novo)
   - Lista de agentes com campos editáveis: nome, cargo, emoji
   - Salva via `AgentPersonalizationService`

### Novos Serviços

1. **`AgentPersonalizationService`**
   ```typescript
   interface AgentProfile {
     agentId: string;
     displayName: string; // "Maria"
     role: string;         // "Inspetora de Qualidade"
     emoji: string;        // "🔍"
   }

   getProfile(agentId: string): AgentProfile
   setProfile(agentId: string, profile: Partial<AgentProfile>): void
   getAllProfiles(): AgentProfile[]
   ```

2. **`GamificationEventsService` (refatorado)**
   - Adicionar método `humanizeEvent(event, profile)` que transforma:
     - De: "Execução concluída por agent-123 (+1)"
     - Para: "🔍 Inspetora Maria finalizou ronda no Módulo Auth"
   - Adicionar categorização automática:
     - Build/Deploy → 🏗️
     - Erro/Falha → 🔥
     - Análise/Métrica → 📊
     - Sucesso/Melhoria → 🎉

### Fluxo de Uso Redesenhado

**Cenário 1: Desenvolvedor monitora saúde da cidade**
1. Abre Screenplay, painel está em modo `collapsed` (60px)
2. Vê 3 KPIs no header: "✅ 5 Agentes Ativos | 📊 42 Inspeções | 🔥 2 Críticos"
3. KPI "2 Críticos" está em vermelho, chama atenção
4. Clica no botão "Expandir" (v ou ^)
5. Painel cresce para 300px, mostra lista de eventos:
   - 🔥 Inspetora Maria: "Detectado monolito com 850 linhas em UserService"
   - 📊 Analista João: "P95 de latência subiu 18% na última hora"
   - 🏗️ Engenheiro Pedro: "Build finalizado com sucesso"

**Cenário 2: Lançar investigação aprofundada**
1. Desenvolvedor vê evento crítico: "Detectado monolito com 850 linhas"
2. Clica no botão "🔎 Investigar" ao lado do evento
3. Modal `InvestigationLauncherComponent` abre
4. Seleciona agente "Code Quality Analyst" (lista pré-definida)
5. Adiciona contexto: "Focar em complexidade ciclomática e dependencies"
6. Clica "Iniciar Investigação"
7. Sistema cria nova instância de agente com prompt:
   ```
   Você é o Code Quality Analyst. Investigue o arquivo UserService.ts que possui 850 linhas.
   Contexto adicional: Focar em complexidade ciclomática e dependencies.
   Gere um relatório detalhado com sugestões de refatoração.
   ```
8. Agente aparece no chat panel à direita, iniciando execução

**Cenário 3: Personalizar "secretários"**
1. Usuário clica em ⚙️ no canto do painel
2. Abre modal "Gerenciar Secretários"
3. Vê lista:
   - agent-abc-123 | "Inspetor Alpha" | 🔍 | [Editar]
4. Clica [Editar], muda para:
   - Nome: "Maria" | Cargo: "Inspetora de Qualidade" | Emoji: 🔍
5. Salva, próximos eventos usam "Inspetora Maria"

## 📦 Entregáveis v2

1. **Componentes Refatorados:**
   - `GamifiedPanelComponent` (novo, substitui CommandBar)
   - `NewsTickerComponent` (refatorado do EventTicker)
   - `InvestigationLauncherComponent` (novo)
   - `AgentPersonalizationModalComponent` (novo)

2. **Serviços:**
   - `AgentPersonalizationService` (novo)
   - `GamificationEventsService` (refatorado com humanização)

3. **Estilos:**
   - CSS para estados collapsed/normal/expanded
   - Animações de transição suaves
   - Scroll vertical estilizado

4. **Documentação:**
   - Este documento `plan-v2.md`
   - Guia de personalização para usuários

## ⚠️ Riscos & Mitigações v2

### Risco 1: Complexidade de Estado do Painel
- **Descrição**: Gerenciar 3 estados (collapsed/normal/expanded) pode causar bugs visuais
- **Mitigação**: Usar state machine simples com enum `PanelState` e testes de cada transição

### Risco 2: Performance com Histórico Grande
- **Descrição**: 500+ eventos no histórico podem travar o scroll
- **Mitigação**:
  - Limitar exibição a últimos 50 eventos
  - Virtual scrolling se necessário (CDK Virtual Scroll)
  - Paginação "Carregar mais"

### Risco 3: Nomes Duplicados de Agentes
- **Descrição**: Usuário pode dar mesmo nome para 2 agentes diferentes
- **Mitigação**:
  - Permitir duplicatas (não é crítico para UX)
  - Exibir `agentId` em tooltip se hover no nome

### Risco 4: Integração com Launcher de Agentes
- **Descrição**: Lançar agentes programaticamente pode conflitar com fluxo manual
- **Mitigação**:
  - Reutilizar exatamente a mesma API do `onAgentSelected`
  - Marcar instâncias como `source: 'investigation'` para rastreamento

### Risco 5: Scroll Horizontal Persistente
- **Descrição**: CSS mal configurado pode manter scroll lateral
- **Mitigação**:
  - `overflow-x: hidden` forçado no painel
  - `word-wrap: break-word` em mensagens longas
  - Testar em resoluções 1024px, 1366px, 1920px

## 🗓️ Fases de Implementação v2

### Fase 1: Layout Expansível (Fundação)
**Objetivo**: Resolver problema de altura e scroll

**Tarefas:**
- Criar `GamifiedPanelComponent` com lógica de estados
- Implementar CSS para collapsed (60px) / expanded (300px)
- Adicionar botão de toggle expand/collapse
- Mover KPIs para header fixo do painel
- Remover scroll horizontal, adicionar vertical
- Testar responsividade em telas pequenas

**Critérios de Aceitação:**
- ✅ Painel expande/colapsa suavemente (transition 0.3s)
- ✅ KPIs visíveis em todos os estados
- ✅ Sem scroll horizontal em telas >= 1024px
- ✅ Scroll vertical funcional no estado expanded

---

### Fase 2: Personalização de Agentes (Humanização)
**Objetivo**: Resolver problema de mensagens técnicas

**Tarefas:**
- Criar `AgentPersonalizationService` com métodos CRUD
- Implementar persistência em localStorage
- Criar `AgentPersonalizationModalComponent`
- Adicionar botão ⚙️ "Gerenciar Secretários" no painel
- Gerar nomes padrão automáticos (Inspetor Alpha, Beta, etc.)
- Integrar perfis no `GamificationEventsService.humanizeEvent()`

**Critérios de Aceitação:**
- ✅ Modal permite editar nome/cargo/emoji de qualquer agente
- ✅ Mudanças persistem após reload
- ✅ Eventos usam nomes personalizados automaticamente
- ✅ Agentes sem personalização recebem nome padrão gerado

---

### Fase 3: News Ticker Redesenhado (Gamificação)
**Objetivo**: Tornar eventos mais envolventes e acionáveis

**Tarefas:**
- Refatorar `EventTickerComponent` → `NewsTickerComponent`
- Mudar layout de horizontal (carrossel) para vertical (lista)
- Adicionar categorias de evento (🏗️ 🔥 📊 🎉 ⚠️)
- Reescrever templates de mensagens no serviço:
  - "Execução concluída" → "🏗️ Engenheiro Pedro finalizou build"
  - "Alerta de complexidade" → "🔥 Inspetora Maria detectou monolito"
- Adicionar botão "🔎 Investigar" em cada item (Fase 4)
- Limitar texto a 80 caracteres, truncar com "..." e tooltip

**Critérios de Aceitação:**
- ✅ Eventos exibidos em lista vertical scrollável
- ✅ Cada evento tem emoji de categoria apropriado
- ✅ Linguagem humanizada ("Secretário X fez Y no local Z")
- ✅ Tooltip mostra mensagem completa se truncada
- ✅ Máximo 50 eventos na lista (rotação automática)

---

### Fase 4: Sistema de Investigação (Ações)
**Objetivo**: Permitir lançar agentes investigadores a partir de eventos

**Tarefas:**
- Criar `InvestigationLauncherComponent` (modal)
- Adicionar botão "🔎 Investigar" em cada evento do ticker
- Definir lista de agentes investigadores (presets):
  - "Code Quality Analyst" (analisa complexidade, code smells)
  - "Performance Investigator" (analisa latência, bottlenecks)
  - "Security Auditor" (analisa vulnerabilidades)
  - "Architecture Reviewer" (analisa acoplamento, coesão)
- Implementar lógica de geração de prompt contextualizado:
  - Incluir: evento original, contexto adicional do usuário, papel do agente
- Integrar com sistema de agentes do Screenplay:
  - Emitir evento `investigationRequested` para componente pai
  - Pai chama `onAgentSelected` com configuração gerada
- Adicionar KPI "Investigações Ativas" no header

**Critérios de Aceitação:**
- ✅ Botão "Investigar" visível em eventos com severity warning/error
- ✅ Modal abre com 4 tipos de agentes investigadores
- ✅ Usuário pode adicionar contexto adicional (textarea)
- ✅ Clicar "Iniciar" cria instância de agente no chat panel
- ✅ Prompt gerado inclui evento original + contexto
- ✅ KPI "Investigações Ativas" atualiza corretamente

---

### Fase 5: Polish & Observabilidade (Finalização)
**Objetivo**: Garantir qualidade e rastreabilidade

**Tarefas:**
- Adicionar telemetria de uso:
  - Eventos: `panel_expanded`, `panel_collapsed`, `investigation_launched`, `agent_personalized`
  - Propriedades: `event_category`, `agent_type`, `duration`
- Implementar testes unitários:
  - `GamifiedPanelComponent`: transições de estado
  - `AgentPersonalizationService`: CRUD de perfis
  - `GamificationEventsService`: humanização de eventos
- Testes e2e:
  - Fluxo completo: expandir painel → clicar investigar → lançar agente
  - Fluxo de personalização: editar nome → ver em eventos
- Adicionar estados de erro/empty:
  - "Nenhum evento recente" com ilustração vazia
  - "Falha ao carregar métricas" com botão "Tentar novamente"
- Otimizar performance:
  - Debounce em expansão rápida (evitar flickering)
  - Memoização de perfis de agentes
  - Lazy loading do modal de investigação
- Documentar shortcuts de teclado:
  - `P` (Panel) para toggle expand/collapse
  - `I` (Investigate) para investigar evento selecionado

**Critérios de Aceitação:**
- ✅ Cobertura de testes >= 70% nos componentes novos
- ✅ Teste e2e passa em CI/CD
- ✅ Telemetria registra corretamente (verificar logs)
- ✅ Estados de erro exibem mensagem amigável + ação
- ✅ Performance: repaint <= 16ms, sem memory leaks
- ✅ Documentação de atalhos adicionada ao modal "⌨️ Atalhos"

## ✅ Critérios de Sucesso v2

### Funcionais
1. ✅ Painel tem altura mínima de 60px e expande até 300px
2. ✅ Scroll vertical funciona, scroll horizontal não existe
3. ✅ Eventos usam nomes humanizados ("Inspetora Maria", não "agent-123")
4. ✅ Usuário consegue personalizar nome/cargo/emoji de agentes
5. ✅ Botão "Investigar" lança agente especialista com contexto
6. ✅ Linguagem de eventos é gamificada (jornal da cidade, não logs técnicos)

### Não-Funcionais
1. ✅ Transição expand/collapse leva <= 300ms
2. ✅ Painel não quebra layout em resoluções 1024px - 4K
3. ✅ Personalização persiste após reload da página
4. ✅ Máximo 50 eventos carregados (performance)
5. ✅ Sem erros de console em operação normal
6. ✅ Acessibilidade: tab navigation funciona, ARIA labels corretos

### Experiência do Usuário
1. ✅ Desenvolvedor entende eventos sem ler código
2. ✅ Ação de investigar leva <= 3 cliques (expandir → investigar → confirmar)
3. ✅ Personalização de agente leva <= 2 minutos para 5 agentes
4. ✅ Painel não atrapalha edição (não cobre editor)
5. ✅ Feedback positivo em teste de usabilidade com 3+ usuários

## 🔗 Dependências v2

### Mantidas da v1
- `AgentMetricsService` (fonte de dados)
- API `/api/agents/instances` (lista de agentes)
- Sistema de agentes do Screenplay (para lançar investigações)

### Novas Dependências
- **localStorage** (para persistir perfis de agentes)
  - Alternativa: MongoDB se backend permitir endpoint CRUD simples
- **Sistema de criação de instâncias** (já existe em `onAgentSelected`)
  - Reutilizar, não reimplementar
- **Definições de agentes investigadores** (presets)
  - Pode ser JSON estático em `assets/investigator-presets.json`

## 📚 Referências v2

### Documentos da Saga
- `requisitos_barra_comandos_screenplay.md` (requisitos originais)
- `plan.md` (v1, implementação atual)
- `plan-v2.md` (este documento)

### Código Relevante (v1)
- `command-bar/command-bar.component.ts` (base para refatoração)
- `event-ticker/event-ticker.component.ts` (base para NewsTickerComponent)
- `gamification-events.service.ts` (adicionar humanização)
- `report-modal/report-modal.component.ts` (referência para modal de investigação)

### Inspiração de Design
- SimCity 4: Painel de notícias com manchetes e categorias
- Tropico 6: "El Presidente Gazette" com eventos humorísticos
- Frostpunk: Sistema de leis e investigações de eventos críticos

## 🎨 Especificações Visuais

### Estados do Painel

```
┌────────────────────────────────────────────────┐
│ COLLAPSED (60px)                               │
├────────────────────────────────────────────────┤
│ KPI₁: 5   KPI₂: 42   KPI₃: 2 🔥    [⚙️] [▼]   │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ EXPANDED (300px)                               │
├────────────────────────────────────────────────┤
│ KPI₁: 5   KPI₂: 42   KPI₃: 2 🔥    [⚙️] [▲]   │
├────────────────────────────────────────────────┤
│ ╔════════════════════════════════════════════╗ │
│ ║ 🔥 Inspetora Maria: Monolito 850 linhas  ║ │
│ ║    em UserService           [🔎 Investig] ║ │
│ ║                                     2m ago ║ │
│ ╠════════════════════════════════════════════╣ │
│ ║ 📊 Analista João: P95 subiu 18%          ║ │
│ ║    na rota /api/users      [🔎 Investig] ║ │
│ ║                                    15m ago ║ │
│ ╠════════════════════════════════════════════╣ │
│ ║ 🏗️ Eng. Pedro: Build #142 finalizado    ║ │
│ ║    com sucesso                            ║ │
│ ║                                    22m ago ║ │
│ ╚════════════════════════════════════════════╝ │
│       [▼ Scroll para mais eventos]             │
└────────────────────────────────────────────────┘
```

### Paleta de Cores (Categorias)

| Categoria | Emoji | Background | Border    | Uso                     |
|-----------|-------|------------|-----------|-------------------------|
| Build     | 🏗️    | `#e8f5e9`  | `#66bb6a` | Builds, deploys         |
| Crítico   | 🔥    | `#ffebee`  | `#ef5350` | Erros, alertas urgentes |
| Análise   | 📊    | `#e3f2fd`  | `#42a5f5` | Métricas, relatórios    |
| Sucesso   | 🎉    | `#f3e5f5`  | `#ab47bc` | Conquistas, melhorias   |
| Alerta    | ⚠️    | `#fff8e1`  | `#ffca28` | Warnings, atenção       |

### Tipografia

- **KPIs**: `font-size: 13px`, `font-weight: 700`
- **Manchetes**: `font-size: 12px`, `font-weight: 600`
- **Detalhes**: `font-size: 11px`, `font-weight: 400`, `color: #6b7280`
- **Timestamps**: `font-size: 10px`, `color: #9ca3af`, `font-variant-numeric: tabular-nums`

## 🧪 Estratégia de Testes

### Testes Unitários (Jasmine/Karma)

**GamifiedPanelComponent:**
```typescript
describe('GamifiedPanelComponent', () => {
  it('should toggle state from collapsed to expanded', () => {
    component.toggleState();
    expect(component.state).toBe('expanded');
  });

  it('should emit investigate event when investigate button clicked', () => {
    spyOn(component.investigate, 'emit');
    component.onInvestigateClick(mockEvent);
    expect(component.investigate.emit).toHaveBeenCalledWith(mockEvent);
  });
});
```

**AgentPersonalizationService:**
```typescript
describe('AgentPersonalizationService', () => {
  it('should save and retrieve profile from localStorage', () => {
    service.setProfile('agent-1', { displayName: 'Maria' });
    const profile = service.getProfile('agent-1');
    expect(profile.displayName).toBe('Maria');
  });

  it('should generate default name if profile not found', () => {
    const profile = service.getProfile('unknown-agent');
    expect(profile.displayName).toMatch(/Inspetor [A-Z]/);
  });
});
```

### Testes E2E (Playwright/Cypress)

**Fluxo Completo de Investigação:**
```typescript
test('should launch investigation from panel event', async ({ page }) => {
  await page.goto('/screenplay');

  // Expandir painel
  await page.click('.panel-toggle-btn');
  await expect(page.locator('.gamified-panel')).toHaveClass(/expanded/);

  // Clicar em investigar no primeiro evento crítico
  await page.click('.news-item.critical .investigate-btn');

  // Modal de investigação abre
  await expect(page.locator('.investigation-launcher')).toBeVisible();

  // Selecionar agente e confirmar
  await page.selectOption('.agent-type-select', 'code-quality-analyst');
  await page.fill('.context-textarea', 'Focar em complexidade');
  await page.click('.launch-investigation-btn');

  // Verificar agente criado no chat panel
  await expect(page.locator('.chat-panel .agent-instance')).toContainText('Code Quality Analyst');
});
```

## 📋 Checklist de Implementação

### Fase 1: Layout Expansível
- [ ] Criar `GamifiedPanelComponent` com estados (collapsed/expanded)
- [ ] Implementar CSS para transições suaves
- [ ] Adicionar botão toggle expand/collapse
- [ ] Mover KPIs para header fixo
- [ ] Remover `overflow-x`, adicionar `overflow-y: auto`
- [ ] Testar em resoluções 1024px, 1366px, 1920px, 4K
- [ ] Verificar acessibilidade (tab navigation, ARIA)

### Fase 2: Personalização
- [ ] Criar `AgentPersonalizationService` com CRUD
- [ ] Implementar persistência em localStorage
- [ ] Criar `AgentPersonalizationModalComponent`
- [ ] Adicionar botão ⚙️ no painel
- [ ] Gerar nomes padrão (Inspetor Alpha, Beta...)
- [ ] Integrar perfis no `GamificationEventsService`
- [ ] Testes unitários do serviço

### Fase 3: News Ticker
- [ ] Refatorar `EventTickerComponent` → layout vertical
- [ ] Adicionar categorias de eventos (emojis)
- [ ] Reescrever templates de mensagens (humanizar)
- [ ] Truncar texto longo com tooltip
- [ ] Limitar histórico a 50 eventos
- [ ] Adicionar estado empty ("Nenhum evento")
- [ ] Testes de renderização

### Fase 4: Investigação
- [ ] Criar `InvestigationLauncherComponent` (modal)
- [ ] Adicionar botão "Investigar" nos eventos
- [ ] Definir presets de agentes investigadores (JSON)
- [ ] Implementar geração de prompt contextualizado
- [ ] Integrar com `onAgentSelected` do Screenplay
- [ ] Adicionar KPI "Investigações Ativas"
- [ ] Teste e2e do fluxo completo

### Fase 5: Polish
- [ ] Adicionar telemetria (panel_expanded, investigation_launched)
- [ ] Testes unitários (coverage >= 70%)
- [ ] Teste e2e completo
- [ ] Estados de erro com retry
- [ ] Otimizar performance (debounce, memoização)
- [ ] Documentar atalhos de teclado (P, I)
- [ ] Code review final

---

## 💬 Perguntas para Refinamento

Antes de iniciar a implementação, precisamos definir:

1. **Persistência de Perfis**: Preferência entre localStorage (simples, só client-side) ou MongoDB (compartilhado entre sessões/usuários)?

2. **Agentes Investigadores**: Lista de 4 tipos é suficiente? Precisa ser configurável pelo usuário?

3. **Altura do Painel Expandido**: 300px é adequado ou preferir ajustável (resize manual como splitter)?

4. **Integração com City-Sim**: Eventos do painel devem linkar para telas City-Sim (ex: clicar evento de build → ir para /city/neighborhood)?

5. **Notificações Sonoras**: Adicionar som opcional quando evento crítico (🔥) aparecer?

6. **Filtros de Eventos**: Usuário deve poder filtrar por categoria (só 🔥, só 📊, etc.)?

---

**Pronto para implementação após aprovação deste plano v2.**
