# Saga 004: Implementar Barra de Comandos Gamificada no Screenplay

## 📋 Contexto & Background
Atualmente, o rodapé (`editor-footer`) da tela "Screenplay" é uma área estática e subutilizada. A gamificação do Conductor, que envolve agentes autônomos monitorando a qualidade do código e gerando métricas, já existe funcionalmente no `AgentGameComponent` (o "canvas da cidade"), mas sua visibilidade e interação são limitadas.

A motivação desta saga é transformar esse rodapé em um "Painel de Comandos" dinâmico e interativo, inspirado em jogos de estratégia como SimCity. Este painel servirá como um hub central para o desenvolvedor ("prefeito") visualizar o estado de saúde do projeto ("cidade") em tempo real, receber relatórios de seus agentes ("secretários") e acessar rapidamente as funcionalidades de gamificação.

## 🎯 Objetivos
- **Transformar o rodapé estático** em um painel de controle de gamificação dinâmico e informativo.
- **Aumentar a consciência situacional** do desenvolvedor sobre a qualidade do código e a dívida técnica.
- **Exibir KPIs (Key Performance Indicators)** vitais do projeto de forma clara e imediata.
- **Criar um "Feed de Eventos"** para notificar sobre relatórios e alertas gerados pelos agentes.
- **Centralizar o acesso** às funcionalidades de gamificação, como o "Gabinete de Ministros" (🏛️) e o "Conselho Semanal" (📅).
- **Melhorar o engajamento** do desenvolvedor com as práticas de qualidade de código através de uma interface gamificada.

## 🔍 Escopo

**In-Scope:**
- Desenvolvimento de um novo componente Angular, `CommandBarComponent`, para abrigar a nova funcionalidade.
- Criação de sub-componentes reutilizáveis: `IndicatorComponent` (para KPIs), `EventTickerComponent` (para o feed) e `ReportModalComponent` (para exibir detalhes).
- Expansão do `AgentMetricsService` existente para transformar dados brutos em métricas e eventos consumíveis pela UI.
- Integração da barra de comandos para consumir dados do `AgentMetricsService`, reutilizando a fonte de dados do `AgentGameComponent`.
- Implementação do layout de três seções: ícones de acesso rápido (esquerda), feed de eventos (centro) e KPIs (direita).
- Implementação de interatividade para abrir modais com relatórios detalhados, evitando navegação de página inteira.

**Out-of-Scope:**
- Criação de novos endpoints no backend. A solução será puramente frontend, consumindo APIs existentes.
- Alterações visuais ou funcionais no `AgentGameComponent` (o canvas). Ele servirá apenas como fonte de inspiração e dados.
- Desenvolvimento de um sistema complexo de conquistas e recompensas. A gamificação se limitará à exibição de status, alertas e relatórios.
- Modificação da navegação principal da aplicação. A interação será primariamente através de modais.

## 💡 Solução Proposta
A solução consiste em desenvolver um `CommandBarComponent` em Angular que será injetado no `editor-footer` da tela Screenplay.

1.  **Estrutura do Componente:** O `CommandBarComponent` será dividido em três slots:
    *   **Esquerda:** Exibirá os ícones de acesso rápido (🏛️, 📅, 🏘️), com indicadores de notificação.
    *   **Centro:** Conterá o `EventTickerComponent`, um feed rotativo com as últimas mensagens dos agentes.
    *   **Direita:** Apresentará os `IndicatorComponent`, exibindo os KPIs vitais (ex: Qualidade do Código, Dívida Técnica, Agentes Ativos).

2.  **Fluxo de Dados:** O `AgentMetricsService` será estendido para incluir métodos que agregam e formatam os dados brutos dos agentes em estruturas prontas para a UI (ex: `getKpiSummary()`, `getEventFeed()`). O `CommandBarComponent` consumirá esses métodos para se manter atualizado.

3.  **Interatividade:** Cliques nos itens do feed de eventos ou nos ícones de acesso rápido não levarão a outras páginas. Em vez disso, acionarão o `ReportModalComponent`, que exibirá relatórios detalhados em uma janela flutuante (modal), mantendo o contexto do usuário na tela Screenplay.

## 📦 Entregáveis
- Código-fonte dos novos componentes Angular: `CommandBarComponent`, `IndicatorComponent`, `EventTickerComponent`, `ReportModalComponent`.
- Código-fonte com as atualizações no `AgentMetricsService`.
- Integração do `CommandBarComponent` no template do `screenplay-interactive.html`.
- Este documento de planejamento (`plan.md`).

## ⚠️ Riscos & Restrições
- **Risco de Performance:** A atualização constante de dados pode impactar a performance do frontend.
    - **Mitigação:** Adotar uma taxa de atualização razoável (ex: 30 segundos, a mesma do `AgentGame`) e garantir que a renderização dos componentes seja eficiente.
- **Risco de Poluição Visual:** Excesso de informações pode tornar a interface confusa.
    - **Mitigação:** Manter um design minimalista, focado nos 3-4 KPIs mais críticos e em um feed de eventos discreto.
- **Restrição de Backend:** A solução não deve depender de novas APIs. Toda a lógica de apresentação deve ser construída no frontend com base nos dados já disponíveis.

## 🗓️ Fases de Implementação
1.  **Fase 1 (Estrutura e KPIs):**
    -   Criar o `CommandBarComponent` e integrá-lo ao rodapé.
    -   Desenvolver o `IndicatorComponent`.
    -   Expandir o `AgentMetricsService` para calcular os KPIs.
    -   Exibir os KPIs estáticos na seção direita da barra.
2.  **Fase 2 (Dinamismo e Feed de Eventos):**
    -   Desenvolver o `EventTickerComponent`.
    -   Implementar a lógica de atualização de dados no `CommandBarComponent` para alimentar os KPIs e o feed.
    -   Exibir o feed de eventos dinâmico na seção central.
3.  **Fase 3 (Interatividade e Modais):**
    -   Desenvolver o `ReportModalComponent`.
    -   Implementar a lógica para abrir o modal com detalhes ao clicar em um item do feed.
    -   Adicionar indicadores de notificação (ex: um ponto piscando) nos ícones da seção esquerda.
    -   Implementar a abertura de modais ao clicar nos ícones principais (🏛️, 📅).

## ✅ Critérios de Sucesso
- A barra de comandos é renderizada corretamente no rodapé da tela Screenplay em todos os cenários.
- Os KPIs são exibidos e refletem os dados do `AgentMetricsService`, atualizando-se periodicamente.
- O feed de eventos exibe mensagens formatadas dos agentes de forma rotativa.
- Clicar em um evento do feed abre um modal com o relatório detalhado correspondente.
- Clicar nos ícones de acesso rápido (com ou sem notificação) abre um modal com o relatório agregado pertinente.
- A funcionalidade não introduz regressões de performance ou bugs visuais na aplicação.

## 🔗 Dependências
- **`AgentMetricsService`:** Fonte primária de dados para toda a funcionalidade.
- **API do Conductor (`/api/agents/instances`):** Fonte de dados brutos para o `AgentMetricsService`.

## 📚 Referências
- Documento de Requisitos: `docs/sagas/saga-004/requisitos_barra_comandos_screenplay.md`
- Análise Inicial: `docs/sagas/saga-004/Saga-004 - 2025-10-24T13-07-06.md`
- Componente de Referência (Fonte de Dados): `src/conductor-web/src/app/components/living-screenplay-simple/agent-game/agent-game.component.ts`
- Serviço a ser estendido: `src/conductor-web/src/app/services/agent-metrics.service.ts`
