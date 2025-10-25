# v2 — Resumo de Fases e Paralelização

## Mapa de Fases
- v2.1: Layout Expansível (Fundação)
- v2.2: Personalização de Agentes (Humanização)
- v2.3: News Ticker Redesenhado (Gamificação)
- v2.4: Sistema de Investigação (Ações)
- v2.5: Polish & Observabilidade (Finalização)

## Dependências Principais
- v2.1 → base visual e estrutural para v2.3.
- v2.2 → alimenta nomes/avatares usados em v2.3.
- v2.3 → necessário para encaixar o botão "Investigar" de v2.4.
- v2.5 → consolidação após v2.1–v2.4.

## Execução em Paralelo (Sugerida)
- Grupo Paralelo A (começo):
  - v2.1 Layout Expansível
  - v2.2 Personalização de Agentes
  Justificativa: independentes; integração visual posterior.

- Grupo Paralelo B (meio):
  - v2.2 Personalização (continua/incremental)
  - v2.3 News Ticker
  Justificativa: ticker pode nascer com placeholders, depois integrar perfis.

- Grupo Paralelo C (final):
  - v2.3 News Ticker (finalizando)
  - v2.4 Investigação (modal/presets em paralelo; integração após v2.3)

- v2.5 Polish & Observabilidade: após integração das anteriores; testes unitários podem iniciar cedo em paralelo com v2.2/v2.3.

## Gateways (Critérios de Passagem)
- Gate 1: v2.1 atende CA de transições, KPIs visíveis e sem scroll horizontal.
- Gate 2: v2.2 com perfis persistentes e humanização aplicada ao serviço.
- Gate 3: v2.3 lista vertical com categorias e truncamento/tooltip.
- Gate 4: v2.4 lança investigação com prompt correto e KPI atualizado.
- Gate Final: v2.5 telemetria + testes ≥70% e2e passando.
