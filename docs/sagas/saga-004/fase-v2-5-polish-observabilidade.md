# Fase v2.5 — Polish & Observabilidade (Finalização)

## Objetivo
Garantir qualidade, rastreabilidade e performance do painel gamificado.

## Entregáveis
- Telemetria de uso (`panel_expanded`, `panel_collapsed`, `investigation_launched`, `agent_personalized`).
- Testes unitários e e2e principais.
- Estados de erro/empty e otimizações de performance.
- Documentação de atalhos de teclado (P, I).

## Tarefas
- Instrumentar eventos de telemetria com propriedades relevantes.
- Testes unitários: painel, personalização, humanização de eventos.
- E2E: expandir painel → investigar → criar instância; personalização refletida nos eventos.
- Estados de erro: mensagens amigáveis + "Tentar novamente".
- Otimizações: debounce em expansão rápida, memoização de perfis, lazy load do modal.
- Documentar atalhos no modal "⌨️ Atalhos".

## Critérios de Aceitação
- Cobertura ≥ 70% nos novos componentes/serviços.
- Fluxos e2e passam; sem erros de console.
- Repaint ≤ 16ms; sem memory leaks aparentes.

## Dependências
- Consolida todas as fases v2; roda após v2.1–v2.4 estarem integradas.

## Pode rodar em paralelo com
- Escrita inicial de testes unitários pode começar junto com v2.2/v2.3, ajustando expectativas conforme a evolução.

## Riscos/Mitigação
- Flakiness em e2e → estabilizar waits, usar data-testid e retries controlados.
