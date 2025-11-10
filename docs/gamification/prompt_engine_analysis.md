# 🔬 Análise Técnica do PromptEngine - Conductor

## Sumário Executivo

O **PromptEngine** é o coração do sistema RAG (Retrieval-Augmented Generation) do Conductor. Ele é responsável por construir prompts complexos e contextualizados para os agentes de IA, concatenando múltiplas fontes de informação em uma estrutura organizada.

## 📊 Ordem de Concatenação do Prompt

O PromptEngine constrói o prompt final na seguinte ordem **EXATA**:

### Formato Texto (build_prompt)
```
1. PERSONA (persona.md do agente)
2. INSTRUÇÕES DO AGENTE (definition.yaml)
3. KNOWLEDGE BASE (playbook.yaml - se disponível)
4. HISTÓRICO DA TAREFA ATUAL (conversation history)
5. NOVA INSTRUÇÃO DO USUÁRIO (message/input atual)
```

### Formato XML (build_xml_prompt)
```xml
<prompt>
    <system_context>
        <persona><!-- Conteúdo da persona.md --></persona>
        <instructions><!-- definition.yaml: prompt/instructions/description --></instructions>
        <playbook><!-- playbook.yaml formatado --></playbook>
        <screenplay><!-- Conteúdo do screenplay.md se disponível --></screenplay>
        <conversation_context><!-- Contexto específico da conversa --></conversation_context>
    </system_context>
    <conversation_history>
        <turn>
            <user><!-- Pergunta do usuário --></user>
            <assistant><!-- Resposta do assistente --></assistant>
        </turn>
        <!-- ... mais turns ... -->
    </conversation_history>
    <user_request><!-- Nova mensagem do usuário --></user_request>
</prompt>
```

## 🔄 Fluxo de Carregamento de Contexto

O método `load_context()` carrega os elementos na seguinte sequência:

```python
1. _load_agent_config()        # definition.yaml ou MongoDB
2. _validate_agent_config()     # Validação de campos obrigatórios
3. _load_agent_persona()        # persona.md
4. _load_agent_playbook()       # playbook.yaml (opcional)
5. _resolve_persona_placeholders() # Substitui {{placeholders}}
6. _load_screenplay_context()   # Screenplay associado (se houver)
7. _load_conversation_context() # Contexto da conversa (bug/feature/etc)
8. _load_conversation_history() # Histórico completo de mensagens
```

## 📦 Elementos do Prompt Detalhados

### 1. **PERSONA** (`persona.md`)
- **Fonte**: Arquivo `persona.md` no diretório do agente ou MongoDB
- **Conteúdo**: Personalidade, papel, estilo de comunicação do agente
- **Tamanho máximo**: 20.000 caracteres (truncado se maior)
- **Placeholders suportados**:
  - `{{agent_id}}` - ID do agente
  - `{{agent_name}}` - Nome amigável extraído do título
  - `{{agent_description}}` - Descrição do agente
  - `Contexto` - Substituído pelo nome amigável

### 2. **INSTRUÇÕES** (`definition.yaml`)
- **Fonte**: Campo `prompt`, `instructions` ou `description` (nessa ordem de prioridade)
- **Conteúdo**: Instruções específicas para a tarefa do agente
- **Tamanho máximo**: 5.000 caracteres

### 3. **PLAYBOOK** (`playbook.yaml`)
- **Opcional**: Pode não existir
- **Conteúdo formatado**:
  - Best Practices
  - Anti-patterns
  - Guidelines
- **Estrutura**:
```yaml
best_practices:
  - title: "Nome da prática"
    description: "Descrição"
    category: "Categoria"
    priority: "Alta/Média/Baixa"
anti_patterns:
  - title: "Padrão a evitar"
    description: "Por que evitar"
    severity: "Alta/Média/Baixa"
```

### 4. **SCREENPLAY** (Documento Vivo)
- **Fonte**: MongoDB, collection `screenplays`
- **Carregamento**: Via `screenplay_id` (direto) ou via `instance_id` (indireto)
- **Conteúdo**: Documento Markdown que evolui durante o projeto
- **Apenas no formato XML**: Incluído como `<screenplay>` tag

### 5. **CONVERSATION CONTEXT**
- **Fonte**: MongoDB, collection `conversations`
- **Campo**: `context` da conversa
- **Conteúdo**: Descrição do bug, feature ou problema específico
- **Apenas no formato XML**: Incluído como `<conversation_context>` tag

### 6. **HISTÓRICO DE CONVERSAS**
- **Fonte**: MongoDB, campo `messages` da conversa
- **Filtros aplicados**:
  - Remove mensagens com `isDeleted: true`
  - Remove última mensagem se for user sem resposta
  - Limita a 100 turns mais recentes
  - Ordena por timestamp (mais antigo primeiro)
- **Truncamento**: Mensagens > 1000 chars são truncadas

### 7. **USER REQUEST** (Input Atual)
- **Fonte**: Parâmetro `message` passado ao `build_prompt()`
- **Posição**: SEMPRE por último
- **Escapamento**: CDATA no formato XML

## 🛡️ Mecanismos de Segurança

### Limites de Tamanho
- **Persona**: Máx 20.000 caracteres
- **Instructions**: Máx 5.000 caracteres
- **Mensagem individual**: Máx 1.000 caracteres
- **Histórico**: Máx 100 turns
- **Prompt final**: Aviso se > 40.000 caracteres

### Tratamento de Dados
- **Soft Delete**: Mensagens com `isDeleted: true` são ignoradas
- **Ordenação**: Histórico sempre cronológico (timestamp)
- **Escapamento XML**: Usa CDATA para conteúdo seguro
- **Fallbacks**: Múltiplos campos verificados (prompt → instructions → description)

## 🔍 Pontos Importantes para a Narrativa

### Correção Necessária
Na narrativa gamificada, devemos explicar que:

1. **O Screenplay NÃO vem primeiro** - A Persona do agente vem primeiro
2. **Ordem correta**:
   - Persona (quem é o agente)
   - Instruções (o que fazer)
   - Knowledge Base (como fazer)
   - Histórico (o que já foi feito)
   - Pedido atual (o que fazer agora)

### Conceito de RAG (Retrieval-Augmented Generation)
O PromptEngine implementa RAG ao:
1. **Retrieval**: Buscar contexto de múltiplas fontes (MongoDB, arquivos)
2. **Augmentation**: Enriquecer o prompt com todo esse contexto
3. **Generation**: Enviar para o LLM (Claude/Gemini) gerar resposta contextualizada

## 💾 Salvamento e Debug

### Logs de Prompt
- **Diretório**: `prompts_log/`
- **Formato do arquivo**: `{timestamp}_{agent_name}_{format}.txt`
- **Conteúdo**: Header com metadados + prompt completo
- **XML**: Formatado com indentação para legibilidade

### Flags de Debug
```python
logger.debug(f"MongoDB definition loaded for {self.agent_id}")
logger.info(f"✅ Contexto do screenplay '{screenplay_id}' carregado")
logger.info(f"✅ Histórico de conversa '{conversation_id}' carregado")
```

## 🎮 Implicações para o Onboarding Gamificado

### Metáfora Correta
```
PERSONA           → "Alma do Agente" (personalidade)
INSTRUÇÕES        → "Missão do Agente" (objetivo)
PLAYBOOK          → "Manual de Sabedoria" (boas práticas)
SCREENPLAY        → "Pergaminho Vivo" (documento que evolui)
CONVERSATION      → "Fio da História" (contexto compartilhado)
HISTÓRICO         → "Memória Coletiva" (o que já aconteceu)
USER REQUEST      → "Novo Comando" (ação atual)
```

### Fluxo no Game
1. **Mentor explica**: "Cada agente tem uma alma (persona) que define quem ele é"
2. **Escriba ensina**: "O pergaminho vivo (screenplay) guarda o conhecimento do projeto"
3. **Cavaleiro demonstra**: "As instruções direcionam minha espada"
4. **Alquimista revela**: "O playbook contém séculos de sabedoria"
5. **Crítico mostra**: "A conversa une todos em uma única história"

## 📈 Métricas e Limites

| Componente | Tamanho Máximo | Truncamento |
|------------|----------------|-------------|
| Persona | 20.000 chars | Sim, com aviso |
| Instructions | 5.000 chars | Sim, com aviso |
| Playbook | Sem limite | Não |
| Screenplay | Sem limite | Não |
| Conversation Context | Sem limite | Não |
| História (turns) | 100 últimos | Sim, automático |
| Mensagem individual | 1.000 chars | Sim, com "..." |
| Prompt final | 40.000 chars | Aviso apenas |

## 🔗 Integração com MongoDB

### Collections Utilizadas
1. **agents**: Definições dos agentes (via repository)
2. **agent_instances**: Instâncias com screenplay_id e conversation_id
3. **screenplays**: Documentos vivos (conteúdo markdown)
4. **conversations**: Contexto e histórico de mensagens

### Fluxo de Busca
```
instance_id → agent_instances → screenplay_id → screenplays
                              ↘ conversation_id → conversations
```

## ✅ Conclusão

O PromptEngine é um sistema sofisticado de construção de contexto que:
1. **Agrega** informações de múltiplas fontes
2. **Ordena** em uma estrutura lógica e consistente
3. **Protege** contra overflow com limites inteligentes
4. **Flexibiliza** com formatos texto e XML
5. **Persiste** logs para análise e debug

A ordem de concatenação é fundamental para o funcionamento correto do sistema RAG, garantindo que o LLM receba primeiro o contexto geral (persona), depois as instruções específicas, o conhecimento acumulado, o histórico relevante, e por fim o pedido atual do usuário.