# Fase v2.3 — News Ticker Redesenhado (Gamificação)

## Objetivo
Transformar o feed horizontal em lista vertical com categorias e linguagem de jornal.

## Entregáveis
- `NewsTickerComponent` (lista vertical scrollável até 50 eventos).
- Categorias visuais: 🏗️ Build, 🔥 Crítico, 📊 Análise, 🎉 Sucesso, ⚠️ Alerta.
- Mensagens humanizadas e truncadas (80 caracteres) com tooltip.

## Tarefas
- Refatorar `EventTickerComponent` → `NewsTickerComponent` (vertical).
- Adicionar categorização automática de eventos no serviço.
- Templates de mensagens no `GamificationEventsService` (linguagem jornalística).
- Truncamento com tooltip para mensagens longas.
- Estado vazio: "Nenhum evento recente".

## Critérios de Aceitação
- Lista vertical com rotação automática até 50 itens.
- Emoji de categoria adequado em cada item.
- Tooltip mostra mensagem completa quando truncada.

## Dependências
- Integra melhor com v2.1 (área de body expandido) e v2.2 (nomes humanizados).

## Pode rodar em paralelo com
- v2.2 Personalização de Agentes (serviços/UI).

## Riscos/Mitigação
- Performance com histórico grande → limitar a 50, considerar virtual scroll se necessário.
