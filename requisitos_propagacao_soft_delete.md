# Propagação de Soft-Delete: Agent_Instance → History

## 📋 Visão Geral

Atualmente, quando uma instância de agente é deletada (marcada com `isDeleted=true` no MongoDB), as mensagens associadas na coleção `history` não são atualizadas automaticamente. Isso gera uma **inconsistência de dados** onde:

- Uma instância está marcada como deletada (`agent_instance.isDeleted = true`)
- Mas suas mensagens no histórico continuam acessíveis (`history.isDeleted` permanece ausente ou `false`)

**Objetivo**: Implementar propagação automática do soft-delete para que, ao deletar uma instância de agente, todas as mensagens de histórico relacionadas também sejam marcadas como deletadas.

---

## 🎯 Requisitos Identificados

### Requisitos Funcionais

**RF1: Propagação Automática de Soft-Delete**
- Quando `agent_instance.isDeleted` é setado para `true`, todas as mensagens em `history` com o mesmo `instance_id` devem receber `isDeleted=true`

**RF2: Manter Integridade de Timestamps**
- Ao propagar o soft-delete, deve-se adicionar/atualizar `deleted_at` nas mensagens de histórico

**RF3: Preservar Comportamento de Hard-Delete**
- Hard-delete com `cascade=true` já remove permanentemente as mensagens (comportamento atual deve ser mantido)

**RF4: Respeitar Escopo de Deleção**
- Apenas mensagens com `instance_id` correspondente devem ser afetadas
- Mensagens de outras instâncias do mesmo agente não devem ser tocadas

### Requisitos Não-Funcionais

**RNF1: Atomicidade**
- A operação de soft-delete deve ser atômica: ou atualiza tudo (instância + mensagens) ou nada

**RNF2: Performance**
- A atualização em lote de mensagens deve ser eficiente (`update_many`)

**RNF3: Logging e Auditoria**
- Registrar quantas mensagens foram afetadas pela propagação

---

## 🔄 Fluxo Atual vs. Fluxo Desejado

### Fluxo Atual (Problema)

1. **Usuário solicita deleção**: Frontend chama `DELETE /api/agents/instances/{instance_id}`
2. **Backend executa soft-delete**: Atualiza apenas `agent_instances`
   ```python
   agent_instances.update_one(
       {"instance_id": instance_id},
       {"$set": {"isDeleted": True, "deleted_at": ISO8601, "updated_at": ISO8601}}
   )
   ```
3. **Mensagens ficam órfãs**: Coleção `history` não é afetada
4. **Inconsistência**: Instância deletada, mas mensagens ainda "ativas"

### Fluxo Desejado (Solução)

1. **Usuário solicita deleção**: Frontend chama `DELETE /api/agents/instances/{instance_id}`
2. **Backend executa soft-delete na instância**: Atualiza `agent_instances`
3. **Backend propaga para histórico**: Atualiza todas as mensagens relacionadas
   ```python
   history.update_many(
       {"instance_id": instance_id},
       {"$set": {"isDeleted": True, "deleted_at": ISO8601}}
   )
   ```
4. **Consistência garantida**: Instância e mensagens deletadas em sincronia
5. **Log de auditoria**: Registra quantas mensagens foram afetadas

---

## 🏗️ Componentes Principais

### Backend (Python)

**Arquivo**: `src/conductor-gateway/src/api/app.py`
**Função**: `delete_agent_instance(instance_id, hard, cascade)`
**Linhas**: 1439-1542

**Responsabilidade Atual**:
- Validar existência da instância
- Executar soft-delete (default) ou hard-delete
- No hard-delete com cascade, deletar permanentemente mensagens de histórico

**Modificação Necessária**:
- **Na seção de soft-delete (linhas 1476-1498)**, adicionar propagação para `history`

---

**Arquivo**: `src/conductor/src/infrastructure/storage/mongo_repository.py`
**Classe**: `MongoRepository`
**Método relacionado**: `append_to_history()` (linhas 153-205)

**Responsabilidade**:
- Inserir mensagens na coleção `history` com `instance_id`
- Este arquivo mostra como mensagens são vinculadas a instâncias

---

### Frontend (Angular)

**Arquivo**: `src/conductor-web/src/app/services/agent.service.ts`
**Método**: `deleteInstance(instanceId, cascade)` (linhas 437-466)

**Responsabilidade**:
- Chamar endpoint DELETE no backend
- Receber confirmação de sucesso

**Observação**: Não precisa modificar frontend - mudança é transparente

---

**Arquivo**: `src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts`
**Método**: `deleteAgentFromMongoDB()`

**Responsabilidade**:
- Remover instância da UI após deleção bem-sucedida

---

## 🔗 Relacionamentos e Dependências

### Estrutura de Dados MongoDB

**Coleção: `agent_instances`**
```javascript
{
  instance_id: "uuid-12345",           // Chave única da instância
  agent_id: "agent-abc",               // ID do template de agente
  isDeleted: false,                    // Flag de soft-delete
  deleted_at: "2025-11-02T10:00:00Z",  // Timestamp de deleção
  updated_at: "2025-11-02T10:00:00Z",
  // ... outros campos
}
```

**Coleção: `history`**
```javascript
{
  _id: "uuid-msg-001",                 // ID único da mensagem
  agent_id: "agent-abc",               // ID do agente
  instance_id: "uuid-12345",           // 🔑 Referência à instância
  user_input: "Olá",
  ai_response: "Olá! Como posso ajudar?",
  isDeleted: false,                    // ⚠️ Flag que deve ser propagada
  createdAt: "2025-11-02T09:55:00Z"
}
```

### Relacionamento

```
agent_instances (1) ----< history (N)
      |                       |
  instance_id  ==  instance_id
```

Uma instância pode ter **muitas mensagens** de histórico. O campo `instance_id` é a **chave estrangeira** que conecta as coleções.

---

## 💡 Regras de Negócio Identificadas

### Regra 1: Soft-Delete por Padrão
**Descrição**: Por padrão, deleções são reversíveis (soft-delete). Dados não são removidos fisicamente.
**Implementação**: `app.py:1476-1498` - parâmetro `hard=False` (default)

### Regra 2: Hard-Delete com Cascade
**Descrição**: Hard-delete só remove mensagens se `cascade=true` for explicitamente passado.
**Implementação**: `app.py:1504-1522` - deleta de `history`, `agent_chat_history` e `agent_conversations`

### Regra 3: Filtragem Automática no Prompt
**Descrição**: Mensagens com `isDeleted=true` são automaticamente excluídas ao montar prompts.
**Implementação**: `src/conductor/src/core/prompt_engine.py:423,514`

### Regra 4: Isolamento por Instance_ID
**Descrição**: Mensagens são isoladas por `instance_id` para separar contextos de diferentes sessões/UIs.
**Implementação**: `mongo_repository.py:170-175` - `instance_id` obrigatório ao inserir mensagem

### Regra 5 (NOVA): Propagação de Soft-Delete
**Descrição**: Ao marcar uma instância como deletada, todas as suas mensagens devem ser marcadas também.
**Implementação**: **PENDENTE - requer implementação**

---

## 🎓 Conceitos-Chave

### Soft-Delete
Técnica de "deleção lógica" onde dados não são removidos fisicamente, apenas marcados como inativos. Benefícios:
- **Auditoria**: Dados históricos preservados
- **Reversibilidade**: Possível recuperar dados deletados
- **Integridade**: Referências não quebram

### Hard-Delete
Deleção física permanente. Dados são removidos do banco de dados e não podem ser recuperados.

### Cascade Delete
Quando um registro principal é deletado, todos os registros relacionados também são deletados automaticamente.

### Instance_ID
Identificador único de uma sessão/contexto de execução de um agente. Permite que:
- Múltiplos usuários usem o mesmo agente simultaneamente sem conflitos
- Históricos sejam isolados por sessão
- Deleção afete apenas o contexto específico

---

## 🛠️ Solução Proposta

### Localização da Modificação
**Arquivo**: `src/conductor-gateway/src/api/app.py`
**Função**: `delete_agent_instance()`
**Seção**: Soft-Delete (linhas 1476-1498)

### Código Atual (Soft-Delete)
```python
# SOFT DELETE (default behavior)
if not hard:
    logger.info(f"Soft deleting instance {instance_id} (setting isDeleted=true)")

    result = agent_instances.update_one(
        {"instance_id": instance_id},
        {
            "$set": {
                "isDeleted": True,
                "deleted_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
    )

    logger.info(f"Successfully soft deleted instance {instance_id}")

    return {
        "success": True,
        "message": "Instance soft deleted successfully (marked as deleted)",
        "instance_id": instance_id,
        "deletion_type": "soft",
        "isDeleted": True
    }
```

### Código Proposto (Com Propagação)
```python
# SOFT DELETE (default behavior)
if not hard:
    logger.info(f"Soft deleting instance {instance_id} (setting isDeleted=true)")

    deletion_timestamp = datetime.now().isoformat()

    # 1. Marcar a instância como deletada
    result = agent_instances.update_one(
        {"instance_id": instance_id},
        {
            "$set": {
                "isDeleted": True,
                "deleted_at": deletion_timestamp,
                "updated_at": deletion_timestamp
            }
        }
    )

    # 2. NOVO: Propagar soft-delete para mensagens de histórico
    history_collection = mongo_db["history"]
    history_result = history_collection.update_many(
        {"instance_id": instance_id},
        {
            "$set": {
                "isDeleted": True,
                "deleted_at": deletion_timestamp
            }
        }
    )

    history_count = history_result.modified_count
    logger.info(
        f"Successfully soft deleted instance {instance_id} "
        f"and {history_count} history messages"
    )

    return {
        "success": True,
        "message": "Instance soft deleted successfully (marked as deleted)",
        "instance_id": instance_id,
        "deletion_type": "soft",
        "isDeleted": True,
        "history_messages_affected": history_count  # NOVO: informar quantas mensagens
    }
```

---

## 📊 Impacto da Mudança

### O que Muda
- ✅ Soft-delete agora atualiza `agent_instances` **E** `history` em sincronia
- ✅ Response do endpoint inclui `history_messages_affected` para auditoria
- ✅ Logs registram quantas mensagens foram afetadas

### O que NÃO Muda
- ✅ Hard-delete continua funcionando exatamente como antes
- ✅ Frontend não precisa ser alterado
- ✅ Comportamento de filtragem no PromptEngine permanece igual
- ✅ Deleção individual de mensagens (`PUT /agents/history/{id}/delete`) continua independente

### Compatibilidade
- ✅ **Backward-compatible**: Mensagens antigas sem `isDeleted` são tratadas como `false`
- ✅ **Idempotente**: Executar soft-delete novamente não causa problemas
- ✅ **Sem breaking changes**: API externa permanece idêntica

---

## 🧪 Cenários de Teste

### Teste 1: Soft-Delete Simples
**Entrada**: `DELETE /api/agents/instances/abc-123`
**Esperado**:
- `agent_instances.isDeleted = true` para `abc-123`
- Todas mensagens com `instance_id=abc-123` recebem `isDeleted=true`
- Response retorna `history_messages_affected: N`

### Teste 2: Instância Sem Mensagens
**Entrada**: `DELETE /api/agents/instances/xyz-999` (instância nova, sem histórico)
**Esperado**:
- `agent_instances.isDeleted = true`
- Response retorna `history_messages_affected: 0`
- Sem erros

### Teste 3: Hard-Delete com Cascade
**Entrada**: `DELETE /api/agents/instances/def-456?hard=true&cascade=true`
**Esperado**:
- Instância removida permanentemente
- Mensagens de histórico removidas permanentemente
- Comportamento atual preservado (sem mudanças)

### Teste 4: Soft-Delete Duas Vezes
**Entrada**: Deletar mesma instância duas vezes
**Esperado**:
- Primeira vez: mensagens atualizadas
- Segunda vez: `modified_count=0` (já estavam deletadas)
- Sem erros

### Teste 5: Isolamento de Instance_ID
**Entrada**: Deletar instância `A`, verificar instância `B` do mesmo agente
**Esperado**:
- Apenas mensagens de `A` são afetadas
- Mensagens de `B` permanecem intactas

---

## 📌 Observações

### Vantagens da Solução
1. **Simplicidade**: Apenas 10 linhas de código adicionadas
2. **Consistência**: Garante sincronia entre instância e histórico
3. **Auditoria**: Logs e response informam quantas mensagens foram afetadas
4. **Reversibilidade**: Soft-delete permite recuperação futura (se implementada)

### Considerações Futuras
- **Recuperação de soft-delete**: Considerar implementar endpoint `PATCH /api/agents/instances/{id}/restore` que reverte `isDeleted=false` tanto em instância quanto em mensagens
- **Limpeza periódica**: Job agendado para hard-delete de instâncias/mensagens soft-deletadas há mais de X dias
- **Índices MongoDB**: Criar índice em `history.instance_id` + `history.isDeleted` para otimizar queries de filtragem

### Arquivos Relacionados
- **Backend**: `src/conductor-gateway/src/api/app.py:1476-1498`
- **Repository**: `src/conductor/src/infrastructure/storage/mongo_repository.py`
- **Prompt Engine**: `src/conductor/src/core/prompt_engine.py` (filtragem de `isDeleted`)
- **Frontend**: `src/conductor-web/src/app/services/agent.service.ts`

---

## ✅ Checklist de Implementação

- [ ] Modificar `app.py` para adicionar propagação no soft-delete
- [ ] Testar soft-delete com instância que tem mensagens
- [ ] Testar soft-delete com instância sem mensagens
- [ ] Verificar que hard-delete continua funcionando
- [ ] Testar isolamento (deletar instância A não afeta instância B)
- [ ] Validar logs e response retornando `history_messages_affected`
- [ ] Atualizar documentação da API (se existir)
- [ ] Considerar criar índice `{instance_id: 1, isDeleted: 1}` em `history`

---

**Documento gerado em**: 2025-11-02
**Versão**: 1.0
**Status**: Análise completa - Aguardando implementação
