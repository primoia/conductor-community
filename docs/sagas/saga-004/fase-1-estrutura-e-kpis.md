# Saga 004 — Fase 1: Estrutura e KPIs no Rodapé

## Objetivo da Fase
- Criar a estrutura da barra de comandos no rodapé do Screenplay.
- Exibir KPIs essenciais na seção direita, preservando o status de arquivo na esquerda.
- Integrar a barra aos estilos existentes sem alterar o `game-canvas`.

## Escopo
- Inserção do componente de barra de comandos no `editor-footer` do `screenplay-interactive`.
- Uso de layout em três áreas: `footer-left` (status de arquivo), `footer-center` (reserva), `footer-right` (KPIs).
- Definição de KPIs mínimos: Agentes ativos, Execuções totais, Última execução.

## Referências no Código
```97:125:src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html
<div class="editor-footer">
  <div class="footer-section footer-left"> ... </div>
  <div class="footer-section footer-center"></div>
  <div class="footer-section footer-right"></div>
</div>
```
```199:212:src/conductor-web/src/app/living-screenplay-simple/screenplay-layout.css
.footer-section { display: flex; align-items: center; gap: 8px; }
.footer-right { justify-content: flex-end; }
```

## Entregáveis
- Estrutura de barra de comandos acoplada ao rodapé.
- Área de KPIs no `footer-right` com placeholders/valores provenientes do serviço de métricas.
- Estilos de suporte reutilizando `screenplay-layout.css` e `screenplay-controls.css`.

## Diretrizes de Implementação (para agentes executores)
- Criar componentes de UI (ex.: `CommandBarComponent` e `IndicatorComponent`) sem interromper a toolbar já existente.
- Consumir dados do `AgentMetricsService` (ou estender) para `activeAgents`, `totalExecutions`, `lastExecution`.
- Atualização periódica alinhada à cadência do AgentGame (~30s), com debounce.

## Critérios de Aceite
- A barra aparece no rodapé sem quebrar o layout.
- Três KPIs são exibidos na direita e atualizam periodicamente.
- `footer-left` mantém os indicadores de salvamento/modificação existentes.

## Fora de Escopo desta Fase
- Feed de eventos e modais.
- Testes automatizados e containers Docker.

## Checklist de Revisão
- Layout não sobrepõe conteúdo em larguras pequenas.
- Sem regressões visuais na toolbar ou no editor.
- KPIs degradam graciosamente quando API indisponível (placeholders/estado neutro).
