# Saga 004 — Fase 3: Interatividade, Modais e Notificações

## Objetivo da Fase
- Tornar o painel interativo: abrir relatórios detalhados em modais a partir do feed e dos atalhos.
- Notificações/badges nos ícones de acesso rápido no rodapé.

## Escopo
- `ReportModalComponent` com detalhes do evento/agente.
- Ações de clique: itens do feed e atalhos (🏛️, 📅, 🏘️) abrem modais contextuais ou navegação leve (`navigateToCity`).
- Badges/indicadores nos atalhos conforme contagens/severidade atuais.

## Referências no Código
```60:66:src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.html
<button class="toolbar-btn" title="Gabinete de Ministros" (click)="navigateToCity('/city/ministers')">🏛️</button>
```
```184:197:src/conductor-web/src/app/living-screenplay-simple/screenplay-layout.css
.editor-footer { grid-template-columns: 1fr auto 1fr; min-height: 36px; }
```

## Entregáveis
- Modais com conteúdo detalhado e botões de ação (ex.: “Atualizar agora”).
- Badges nos atalhos com contagem ou ponto de atenção.
- Handlers de clique e integração com serviço de métricas/eventos.

## Critérios de Aceite
- Clicar em um item do feed abre modal correspondente.
- Clicar nos ícones (🏛️, 📅, 🏘️) abre visão/modal com dados agregados.
- Notificações refletem o estado atual e se atualizam periodicamente.

## Fora de Escopo desta Fase
- Novas rotas complexas ou refatorações do AgentGame.
- Testes automatizados e containers Docker.

## Checklist de Revisão
- UX: modais não bloqueiam o fluxo; fácil fechar (ESC, overlay, botão).
- Acessibilidade: foco gerenciado dentro do modal; aria-labels mínimos.
- Degradação graciosa sem dados de backend.
