# Sistema de Gamificação - Conductor

## O que é isso?

Este diretório contém a documentação completa do **sistema de onboarding gamificado** do Conductor - uma experiência interativa que ensina novos usuários a orquestrar agentes de IA através de uma jornada narrativa.

## Conceito Central

O Conductor permite que você trabalhe com **agentes de IA especializados** (como Escriba, Artesã, Crítica) que colaboram em projetos através de conversas unificadas. Em vez de aprender isso lendo documentação técnica, você vive uma experiência hands-on com robôs sintéticos em um mundo digital.

## A Jornada

**Você é um Iniciado** que acaba de chegar ao Salão Digital, onde robôs especializados (Condutores Sintéticos) estão em modo de hibernação. Sua missão é reativá-los e aprender a orquestrá-los para criar seu primeiro artefato digital.

**Cadeia de Ativação:**
```
💾 Código Primordial → 📚 Bibliotecária → 🔑 Chave Alpha →
📋 Escriba → ⚙️ Núcleo Beta → 👩‍🔧 Artesã →
🔧 Módulo Gamma → 👩‍🎨 Crítica → 🎼 Protocolo Omega →
🧙‍♂️ Guia → ⚡ SINCRONIZAÇÃO COMPLETA
```

Ao completar a jornada, você se transforma de **Iniciado** em **Condutor Híbrido**.

## O que você aprende?

Em aproximadamente 10 minutos, você domina 5 conceitos essenciais:

1. **Agentes** - Robôs especializados, cada um com habilidades únicas
2. **Conversas** - Memória compartilhada entre todos os agentes (conversation_id)
3. **Screenplays** - Documentos vivos que evoluem durante o projeto
4. **Colaboração** - Como múltiplos agentes trabalham juntos no mesmo problema
5. **Iteração** - Ciclo natural de criação, feedback e refinamento

## Sistema de Inventário

Um sistema completo de itens permite:

- Coletar itens indestrutíveis que contam a história dos Condutores
- Entregar itens para NPCs para desbloqueá-los progressivamente
- Persistência entre sessões
- Visual tech/robô alinhado com a narrativa

**Teclas de atalho:** TAB ou I para abrir, ESC para fechar

## Como funciona tecnicamente?

**PromptEngine (RAG)** constrói contexto inteligente na ordem:
```
Persona → Instruções → Knowledge Base → Histórico → Pedido Atual
```

**Agentes** são especializados através de:
- `persona.md` - Personalidade e estilo
- `agent.yaml` - Configuração técnica
- `playbook.yaml` - Boas práticas e conhecimento

**Conversas** unificam tudo:
- Todos os agentes compartilham o mesmo histórico (conversation_id)
- Screenplays atualizam em tempo real
- Artefatos criados ficam visíveis no inventário

## Arquivos Principais

| Arquivo | Descrição |
|---------|-----------|
| `conductor_narrative_guide.md` | Guia completo da narrativa e conceitos |
| `conductor_relationship_map.md` | Como os componentes se conectam |
| `inventory_implementation_guide.md` | Implementação do sistema de inventário |
| `inventory_quest_integration_summary.md` | Integração inventário + quest |
| `narrative_adjusted_tech_robots.md` | Narrativa tech/robô refinada |
| `prompt_engine_analysis.md` | Análise técnica do PromptEngine |
| `RESUMO_EXECUTIVO_ONBOARDING.md` | Visão executiva do projeto |

## Status

✅ Sistema de inventário implementado
✅ Narrativa tech/robô definida
✅ Cadeia de itens mapeada
✅ Integração com /quest completa
✅ Build passando sem erros

## Para Desenvolvedores

**Frontend:** Angular com componentes de quest, inventário e diálogos
**Backend:** Python/FastAPI com ConversationService e PromptEngine
**Database:** MongoDB para conversas, screenplays e agentes

**Para rodar:**
```bash
npm run dev
# Acesse: http://127.0.0.1:8080/quest
```

## Resultado Final

Usuários não apenas entendem o Conductor - eles **vivenciam** como é trabalhar com agentes de IA colaborativos, criando uma memória positiva e motivação para explorar o sistema completo.

---

*"Onde aprender a orquestrar se torna uma aventura"*
