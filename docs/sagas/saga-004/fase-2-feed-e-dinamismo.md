# Saga 004 — Fase 2: Feed de Eventos e Dinamismo

## Objetivo da Fase
- Adicionar um feed rotativo de eventos de gamificação no centro do rodapé.
- Tornar os KPIs e o feed dinâmicos, atualizando-se periodicamente.

## Escopo
- `EventTickerComponent` exibindo eventos recentes (ex.: classes grandes, CSS inline, falhas, tendências).
- Integração com as mesmas fontes de dados do AgentGame; quando não houver endpoint dedicado, derivar eventos das métricas disponíveis e regras simples.
- Polling/observables a cada ~30s com backoff básico.

## Referências no Código
```118:124:src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html
<div class="footer-section footer-center"> <!-- vazio por enquanto --> </div>
```
```52:68:src/conductor-web/src/app/living-screenplay-simple/screenplay-controls.css
.bottom-section .editor-footer .footer-section { display: flex; }
.bottom-section .editor-footer .footer-center { justify-content: center; }
```

## Modelo de Evento (sugerido)
```json
{
  "id": "evt-uuid",
  "title": "Classe excessivamente grande detectada",
  "severity": "warning|error|info",
  "timestamp": "2025-10-24T13:00:00Z",
  "meta": { "file": "src/...", "lines": 1200 }
}
```

## Entregáveis
- Componente de feed com rotação suave e tooltips.
- Serviço/adapter que consolida eventos a partir das métricas/endpoints já existentes.
- Atualizações periódicas compartilhadas com os KPIs.

## Critérios de Aceite
- Feed visível no `footer-center` com no mínimo 5 últimos eventos.
- Atualização periódica sem causar travamentos ou jumps visuais.
- Tolerância a falhas: estado “indisponível” quando sem dados.

## Fora de Escopo desta Fase
- Abertura de modais/overlays ao clicar.
- Testes automatizados e containers Docker.

## Checklist de Revisão
- Acessibilidade: foco/teclas de navegação percorrem o feed.
- Performance: sem bloqueios de UI; uso de change detection eficiente.
- Consistência visual com toolbar e status bar.
