# Barra de Comandos do Screenplay (Painel Gamificado no Rodapé)

## 📋 Visão Geral
A funcionalidade propõe ampliar o rodapé do editor vivo (`footer-section footer-left`) para funcionar como um painel de comandos gamificado, inspirado no SimCity 3000. O objetivo de negócio é centralizar, em um só lugar, o acesso rápido aos eventos da gamificação do projeto (ex.: status de agentes que inspecionam o código, alertas do “Gabinete de Ministros”, pautas do “Conselho Semanal”, comparativos de arquitetura de bairros) e indicadores resumidos de saúde/atividade dos agentes.

## 🎯 Requisitos Identificados
### Requisitos Funcionais
- RF1: Exibir no rodapé ícones/atalhos gamificados (🏛️ Ministros, 📅 Conselho, 🏘️ Bairro) com contadores/indicadores.
- RF2: Ao clicar em cada atalho, abrir a respectiva visão/cena (rota `city-sim`) ou overlay modal contextual.
- RF3: Exibir indicadores de atividade dos agentes (ex.: ativos agora, execuções totais, última execução) consolidados do sistema de métricas.
- RF4: Mostrar fila/eventos recentes de gamificação (ex.: “classe excessivamente grande detectada”, “p95 piorou 18%”) com tooltip/expansão.
- RF5: Disponibilizar ações rápidas: atualizar/sincronizar métricas, abrir filtro/visão detalhada do `game-canvas`, navegar para relatórios dos agentes.
- RF6: Integrar com o mecanismo atual de navegação (`navigateToCity`) e com o `AgentGame`/`AgentMetricsService` para dados em tempo quase-real.
- RF7: Manter o estado de salvamento do arquivo visível (já existente), combinando com o novo painel sem poluir a UI.

### Requisitos Não-Funcionais
- RNF1: Não bloquear a edição; atualizações devem ser suaves e assíncronas (polling/observables).
- RNF2: Responsivo; funcionar bem em larguras pequenas sem sobrepor conteúdo.
- RNF3: Consistência visual com a `editor-toolbar` e o design atual.
- RNF4: Tolerante a falhas de backend: exibir estados “indisponível” sem erros na UI.
- RNF5: Atualização periódica com impacto mínimo (ex.: sincronização a cada ~30s já usada pelo `AgentGame`).

## 🔄 Fluxo do Processo
1. Início: Ao carregar o Screenplay, o rodapé inicializa o painel gamificado e solicita dados consolidados de agentes (instâncias, métricas) e de “cenas” (Ministros, Conselho, Bairro).
2. Processamento: O painel recebe atualizações do `AgentMetricsService` (observables) e sincronizações periódicas do backend (via endpoints do BFF utilizados pelo `AgentGame`). Agrega contagens e status em tempo quase-real.
3. Finalização: Interações do usuário (cliques nos botões, abrir overlay, reset de filtros) atualizam a UI localmente; os dados continuam a sincronizar em background.

## 🏗️ Componentes Principais
### Frontend (Angular)
- Componente Screenplay (`screenplay-interactive`)
  - Responsável por hospedar o rodapé e navegação rápida para as cenas gamificadas.
  - Ponto de integração visual do painel gamificado no `footer-left`.
- `AgentGameComponent` (game-canvas)
  - Superfície visual de agentes com métricas, agrupamentos e tooltips.
  - Fonte de verdades visuais e interações aprofundadas.
- `AgentMetricsService`
  - Serviço que coleta e consolida métricas de execução (execuções totais, tempo total/médio, status de execução atual), com debounce e processamento em lote.
- Módulos City-Sim (Ministros, Conselho, Bairro)
  - Telas temáticas que apresentam alertas/dashboards gamificados alinhados às “metáforas” do jogo.

### Backend (Python)
- BFF/Endpoints já consumidos pelo `AgentGame` (ex.: `/api/agents/instances`, `/api/agents/instances/{id}`)
  - Fonte de instâncias e estatísticas persistidas. O painel se beneficiará desses mesmos endpoints para contagens e indicadores.

## 🔗 Relacionamentos e Dependências
- O painel no rodapé consome:
  - Dados reativos do `AgentMetricsService` (front) para estado imediato (executando agora, totais locais).
  - Dados consolidados via BFF já utilizados pelo `AgentGame` para números agregados e últimas execuções.
- Os atalhos (🏛️, 📅, 🏘️) usam `navigateToCity` para abrir as rotas correspondentes do City-Sim ou invocar overlays contextuais.
- O `game-canvas` permanece como visão detalhada; o rodapé funciona como “sumário/lançador”.

## 💡 Regras de Negócio Identificadas
1. Regra: Métricas por instância usam `instance_id` (não apenas `agentId`).
   - Implementação: `AgentGameComponent` e `AgentMetricsService` vinculam métricas por `instanceId`; sincronização periódica (~30s).
2. Regra: Indicadores devem degradar graciosamente quando a API estiver indisponível.
   - Implementação: `AgentGameComponent` já trata ausência de dados e falhas com logs/estados vazios; o painel deve seguir a mesma estratégia.
3. Regra: Ícones/atalhos no rodapé devem refletir o estado atual (ex.: badges com contagem, cores por severidade quando aplicável).
   - Implementação: Derivar contagens a partir de endpoints do BFF e/ou coleções de alertas ativos apresentados nas telas City-Sim.

## 🎓 Conceitos-Chave
- Agente vs Instância: Um “Agente” pode ter várias instâncias; métricas são rastreadas por `instance_id` para precisão.
- Gamificação Temática: “Gabinete de Ministros”, “Conselho Semanal”, “Bairro Monolito vs Modular” representam perspectivas/relatórios da saúde do projeto.
- Painel Sumário: O rodapé mostra o essencial (indicadores e atalhos), deixando detalhes e exploração para o `game-canvas` e telas City-Sim.

## 🏷️ Exemplos do Código (trechos relevantes)
- Toolbar com botões de acesso às cenas do City-Sim (existentes):
```97:125:src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html
<div class="editor-footer">
  <div class="footer-section footer-left">
    ...
  </div>
  <div class="footer-section footer-center"></div>
  <div class="footer-section footer-right"></div>
</div>
```
```60:66:src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html
<!-- Quick access to City-Sim mockups -->
<button class="toolbar-btn" title="Gabinete de Ministros" (click)="navigateToCity('/city/ministers')">🏛️</button>
```
- Game Canvas e métricas de agentes:
```83:90:src/conductor-web/src/app/living-screenplay-simple/agent-game/agent-game.component.html
<canvas
  #gameCanvas
  class="game-canvas"
  (click)="onCanvasClick($event)"
  (mousemove)="onCanvasMouseMove($event)"
  (mouseleave)="onCanvasMouseLeave($event)">
</canvas>
```
```487:506:src/conductor-web/src/app/living-screenplay-simple/agent-game/agent-game.component.ts
const url = `${baseUrl}/api/agents/instances?limit=500`;
const response = await this.http.get<{ success: boolean, count: number, instances: any[] }>(url).toPromise();
if (response && response.success && response.instances && response.instances.length > 0) {
  // Cria personagens/agentes e agrupa por tipo
}
```
```188:205:src/conductor-web/src/app/services/agent-metrics.service.ts
getAgentMetrics(agentId: string): Observable<AgentExecutionMetrics> {
  return new Observable(observer => {
    const subscription = this.metrics$.subscribe(metricsMap => {
      const metrics = metricsMap.get(agentId) || { ...defaults };
      observer.next(metrics);
    });
    return () => subscription.unsubscribe();
  });
}
```

## 📌 Observações
- O painel no rodapé deve coexistir com o status de salvamento já exibido no `footer-left`; recomenda-se usar `footer-center` e/ou compor uma área expandida com colapsável.
- As telas City-Sim (ex.: Ministros) já exemplificam “alertas” que podem alimentar contagens/indicadores no rodapé.
- Sincronização: reutilizar a cadência e endpoints consumidos pelo `AgentGame` para manter números atuais sem duplicar lógica.

---

### Dúvidas para Fechamento de Requisitos
1. Os indicadores no rodapé devem mostrar só contagens (ex.: total de alertas/execuções) ou também severidade/status (cores/badges)?
2. Preferimos abrir as cenas City-Sim em navegação de rota ou como overlays/modais sobre o Screenplay?
3. Qual é a fonte dos “eventos gamificados” (ex.: code smells)? Já existe endpoint consolidado de alertas ou derivaremos dos dados atuais (instâncias/métricas + regras)?
4. Qual SLA/cadência de atualização é aceitável no rodapé (ex.: 30s, 60s)? Haverá botão de “Atualizar agora”?
5. Quais KPIs devem aparecer no rodapé por padrão (ex.: agentes ativos, execuções hoje, últimas falhas)?
6. Há necessidade de logs/auditoria acessíveis a partir do rodapé (ex.: última análise do secretário)?
