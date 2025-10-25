# Fase v2.4 — Sistema de Investigação (Ações)

## Objetivo
Permitir lançar agentes investigadores diretamente dos eventos do painel.

## Entregáveis
- `InvestigationLauncherComponent` (modal) com presets de agentes.
- Botão "🔎 Investigar" em eventos elegíveis (warning/error).
- Integração com `onAgentSelected` para criar instâncias no chat panel.
- KPI "Investigações Ativas" no header.

## Tarefas
- Criar modal `InvestigationLauncherComponent` com:
  - Seleção de tipo de agente (presets) e contexto adicional (textarea).
  - Geração de prompt contextualizado (evento + contexto + papel).
- Adicionar botão "🔎 Investigar" em itens do `NewsTickerComponent`.
- Emitir `investigationRequested` para o pai; pai chama `onAgentSelected`.
- Atualizar KPI "Investigações Ativas".

## Critérios de Aceitação
- Modal abre e permite selecionar 4 tipos de agentes.
- Ao confirmar, cria instância no chat panel com prompt correto.
- KPI de investigações ativas atualiza.

## Dependências
- Requer v2.3 (ticker) para o ponto de entrada do botão.
- Pode iniciar implementação do modal e presets em paralelo.

## Pode rodar em paralelo com
- Parte de modelagem/presets pode rodar em paralelo com v2.3; integração final depende do ticker.

## Riscos/Mitigação
- Conflito com fluxo manual de criação → reutilizar a mesma API `onAgentSelected` e marcar `source: 'investigation'`.
