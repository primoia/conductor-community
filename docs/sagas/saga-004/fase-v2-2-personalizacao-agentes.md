# Fase v2.2 — Personalização de Agentes (Humanização)

## Objetivo
Humanizar mensagens substituindo `agentId` por perfis com nome, cargo e emoji.

## Entregáveis
- `AgentPersonalizationService` com CRUD e persistência (localStorage).
- `AgentPersonalizationModalComponent` para gerenciar perfis.
- Integração básica com `GamificationEventsService.humanizeEvent()`.

## Tarefas
- Implementar `AgentPersonalizationService`:
  - `getProfile(agentId)`, `setProfile(agentId, partial)`, `getAllProfiles()`.
  - Geração de nomes padrão: "Inspetor Alpha/Beta/...".
- Criar `AgentPersonalizationModalComponent` (lista editável + salvar).
- Botão ⚙️ no header do painel para abrir o modal.
- Adaptar `GamificationEventsService` para consumir perfis ao humanizar eventos.

## Critérios de Aceitação
- Perfis editáveis (nome, cargo, emoji) e persistentes após reload.
- Eventos passam a exibir nomes humanizados automaticamente.
- Perfis ausentes recebem nome padrão gerado.

## Dependências
- Nenhuma dependência estrita da v2.1; integração visual no header do painel.

## Pode rodar em paralelo com
- v2.1 Layout Expansível (estrutura do painel).
- v2.3 News Ticker (aparece com nomes humanizados quando integrado).

## Riscos/Mitigação
- Perfis duplicados → tolerar duplicidade; mostrar `agentId` em tooltip.
