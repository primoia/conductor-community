# Fase v2.1 — Layout Expansível (Fundação)

## Objetivo
Resolver altura/scroll e preparar o rodapé para operar como painel vertical expansível do "Jornal da Cidade".

## Entregáveis
- `GamifiedPanelComponent` com estados: `collapsed (60px)`, `expanded (300px)`.
- Header fixo com KPIs sempre visíveis.
- Botão de toggle expand/collapse com transição suave (≤ 300ms).
- Scroll vertical no corpo do painel expandido; remover scroll horizontal.

## Tarefas
- Criar `GamifiedPanelComponent` e máquina de estados (collapsed/normal/expanded).
- Implementar CSS responsivo e transições.
- Adicionar botão de toggle (▼/▲) e atalhos `P` para expand/collapse.
- Mover KPIs para o header fixo do painel.
- Garantir `overflow-x: hidden` e `overflow-y: auto` no corpo expandido.
- Testar responsividade (1024, 1366, 1920, 4K) e acessibilidade (tab/ARIA).

## Critérios de Aceitação
- Painel expande/colapsa suavemente (≤ 300ms).
- KPIs visíveis em todos os estados.
- Sem scroll horizontal nas resoluções suportadas.
- Scroll vertical funcional no estado expanded.

## Dependências
- Reutiliza dados de `AgentMetricsService` (v1). Nenhuma nova API.

## Pode rodar em paralelo com
- v2.2 Personalização de Agentes (serviço/UI) — integração posterior no header.

## Riscos/Mitigação
- Flickering em transições → usar `will-change`, `transform/opacity` e debouncing.
- Quebra de layout em telas pequenas → media queries e testes manuais.
