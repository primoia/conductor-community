# ✅ Checklist de Validação - conversation_id

**Data:** 2025-11-01
**Propósito:** Validar implementação completa do novo modelo de conversas

---

## 📋 Pré-Requisitos

- [ ] MongoDB rodando e acessível
- [ ] Conductor backend iniciado
- [ ] Conductor gateway iniciado
- [ ] Frontend buildado com feature flag ativada

---

## 🔧 Validação: Scripts de Migração

### Script 1: Normalização de Tasks

```bash
cd /mnt/ramdisk/primoia-main/conductor-community/src/conductor

# 1. Dry run
python scripts/normalize_tasks_add_conversation_id.py --dry-run
```

**Verificar:**
- [ ] Script executa sem erros
- [ ] Mostra quantidade de instance_ids únicos
- [ ] Mostra preview do que seria modificado

```bash
# 2. Execução real
python scripts/normalize_tasks_add_conversation_id.py
```

**Verificar:**
- [ ] Backup criado
- [ ] Tasks atualizadas com conversation_id
- [ ] Índice criado

```bash
# 3. Verificação
python scripts/normalize_tasks_add_conversation_id.py --verify-only
```

**Esperado:**
- [ ] ✅ Todas as tasks têm conversation_id
- [ ] ✅ Nenhuma inconsistência encontrada

### Script 2: Migração de Históricos

```bash
# 1. Dry run
python scripts/migrate_histories_to_conversations.py --dry-run
```

**Verificar:**
- [ ] Script executa sem erros
- [ ] Mostra quantidade de conversas a migrar
- [ ] Mostra preview de conversão

```bash
# 2. Execução real
python scripts/migrate_histories_to_conversations.py
```

**Verificar:**
- [ ] Backup criado (agent_conversations_backup_*)
- [ ] Conversas criadas na collection `conversations`
- [ ] Mensagens convertidas corretamente

```bash
# 3. Verificação
python scripts/migrate_histories_to_conversations.py --verify-only
```

**Esperado:**
- [ ] ✅ Total de conversas migradas = total de instance_ids únicos
- [ ] ✅ Nenhuma conversa faltando

---

## 🌐 Validação: Backend API

### Teste 1: Criar Conversa

```bash
curl -X POST http://localhost:5006/api/conversations/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Teste API",
    "active_agent": {
      "agent_id": "test_agent",
      "instance_id": "test-uuid",
      "name": "Test Agent",
      "emoji": "🧪"
    }
  }'
```

**Verificar:**
- [ ] Status 200
- [ ] Response contém `conversation_id`
- [ ] Response contém `title` e `created_at`

**Salvar `conversation_id` para próximos testes:** `_____________________`

### Teste 2: Obter Conversa

```bash
CONV_ID="<conversation_id_do_teste_1>"

curl http://localhost:5006/api/conversations/$CONV_ID
```

**Verificar:**
- [ ] Status 200
- [ ] Response contém conversa completa
- [ ] Campo `messages` é array (vazio inicialmente)
- [ ] Campo `participants` contém agente criado

### Teste 3: Adicionar Mensagem

```bash
curl -X POST http://localhost:5006/api/conversations/$CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "Olá, teste!",
    "agent_response": "Resposta do agente",
    "agent_info": {
      "agent_id": "test_agent",
      "instance_id": "test-uuid",
      "name": "Test Agent",
      "emoji": "🧪"
    }
  }'
```

**Verificar:**
- [ ] Status 200
- [ ] Response: `{"success": true}`

**Recarregar conversa:**
```bash
curl http://localhost:5006/api/conversations/$CONV_ID
```

**Verificar:**
- [ ] `messages` array tem 2 elementos (user + bot)
- [ ] Mensagem user tem `type: "user"`
- [ ] Mensagem bot tem `type: "bot"` e campo `agent`

### Teste 4: Alterar Agente Ativo

```bash
curl -X PUT http://localhost:5006/api/conversations/$CONV_ID/active-agent \
  -H "Content-Type: application/json" \
  -d '{
    "agent_info": {
      "agent_id": "another_agent",
      "instance_id": "uuid-2",
      "name": "Another Agent",
      "emoji": "🎯"
    }
  }'
```

**Verificar:**
- [ ] Status 200
- [ ] Response: `{"success": true}`

**Recarregar conversa:**
```bash
curl http://localhost:5006/api/conversations/$CONV_ID
```

**Verificar:**
- [ ] Campo `active_agent` foi atualizado
- [ ] `participants` agora tem 2 agentes

### Teste 5: Listar Conversas

```bash
curl http://localhost:5006/api/conversations/?limit=10
```

**Verificar:**
- [ ] Status 200
- [ ] Response contém array `conversations`
- [ ] Cada conversa tem `conversation_id`, `title`, `message_count`, `participant_count`

### Teste 6: Deletar Conversa

```bash
curl -X DELETE http://localhost:5006/api/conversations/$CONV_ID
```

**Verificar:**
- [ ] Status 200
- [ ] Response: `{"success": true}`

**Tentar obter conversa deletada:**
```bash
curl http://localhost:5006/api/conversations/$CONV_ID
```

**Verificar:**
- [ ] Status 404

---

## 🖥️ Validação: Frontend (Feature Flag ON)

### Configuração

**Arquivo:** `src/environments/environment.ts`

```typescript
features: {
  useConversationModel: true  // ✅ ATIVADO
}
```

- [ ] Feature flag está `true`
- [ ] Frontend rebuilded após mudança

### Teste 1: Criar Conversa via UI

1. Abrir aplicação no navegador
2. Selecionar um agente na dock
3. Verificar console do navegador:
   ```
   🔥 [CHAT] Usando NOVO modelo de conversas globais
   🆕 [CHAT] Criando nova conversa
   ✅ [CHAT] Nova conversa criada: <uuid>
   ```

**Checklist:**
- [ ] Console mostra "NOVO modelo"
- [ ] Conversa criada com sucesso
- [ ] `activeConversationId` definido no componente

### Teste 2: Enviar Mensagem

1. Digitar mensagem: "Olá, teste de conversa"
2. Enviar
3. Aguardar resposta

**Checklist:**
- [ ] Mensagem do usuário aparece na UI
- [ ] Indicador de loading aparece
- [ ] Resposta do agente aparece
- [ ] Mensagem do agente mostra emoji e nome do agente

### Teste 3: Trocar Agente (CRÍTICO!)

1. Selecionar outro agente na dock
2. Verificar histórico exibido
3. Enviar nova mensagem: "Continue a conversa"

**Checklist:**
- [ ] Console mostra: "🔄 [CHAT] Trocando agente ativo na conversa"
- [ ] Histórico completo permanece visível
- [ ] Novo agente vê mensagens do agente anterior ✅
- [ ] Nova mensagem é adicionada à mesma conversa

### Teste 4: Recarregar Página

1. Recarregar página (F5)
2. Selecionar mesmo agente

**Checklist:**
- [ ] Histórico persiste (carregado do MongoDB)
- [ ] Todas as mensagens aparecem
- [ ] Informações dos agentes estão presentes

---

## 🖥️ Validação: Frontend (Feature Flag OFF)

### Configuração

**Arquivo:** `src/environments/environment.ts`

```typescript
features: {
  useConversationModel: false  // 🔄 DESATIVADO (legado)
}
```

- [ ] Feature flag está `false`
- [ ] Frontend rebuilded após mudança

### Teste: Modelo Legado

1. Selecionar agente A
2. Enviar mensagem
3. Selecionar agente B

**Checklist:**
- [ ] Console mostra: "🔄 [CHAT] Usando modelo LEGADO"
- [ ] Agente B NÃO vê mensagens do Agente A
- [ ] Históricos permanecem isolados (comportamento original)

---

## 📊 Validação: MongoDB

### Verificar Collections

```javascript
// No MongoDB shell ou MongoDB Compass

// 1. Verificar collection conversations
db.conversations.find().pretty()
```

**Checklist:**
- [ ] Collection `conversations` existe
- [ ] Documentos têm estrutura correta:
  - `conversation_id`
  - `title`
  - `active_agent`
  - `participants` (array)
  - `messages` (array)

```javascript
// 2. Verificar uma conversa específica
db.conversations.findOne({conversation_id: "<seu_conversation_id>"})
```

**Verificar:**
- [ ] Campo `messages` tem mensagens user e bot
- [ ] Mensagens bot têm campo `agent` com metadados
- [ ] `participants` lista todos os agentes que participaram

```javascript
// 3. Verificar collection tasks
db.tasks.findOne({}, {conversation_id: 1, instance_id: 1})
```

**Verificar:**
- [ ] Campo `conversation_id` existe
- [ ] Índice criado: `db.tasks.getIndexes()`

```javascript
// 4. Verificar collection legada (backup)
db.agent_conversations.count()
db.agent_conversations_backup_YYYYMMDD_HHMMSS.count()
```

**Verificar:**
- [ ] Backup foi criado
- [ ] Collection original preservada

---

## 🎯 Validação: Caso de Uso Completo

### Cenário: Análise → Execução

**Setup:**
- Agent A: RequirementsEngineer_Agent
- Agent B: Executor_Agent

**Passos:**

1. [ ] Selecionar Agent A
2. [ ] Enviar: "Analise os requisitos do sistema de autenticação"
3. [ ] Aguardar resposta completa
4. [ ] **Verificar:** Resposta mostra análise de requisitos
5. [ ] Selecionar Agent B
6. [ ] **Verificar CRÍTICO:** Agent B vê mensagens do Agent A
7. [ ] Enviar: "Execute os requisitos identificados"
8. [ ] Aguardar resposta
9. [ ] **Verificar:** Resposta do Agent B refere-se aos requisitos do Agent A

**Resultado Esperado:**
- [ ] ✅ Agent B teve contexto completo da conversa
- [ ] ✅ Resposta foi contextualmente relevante
- [ ] ✅ Histórico unificado funcionou corretamente

---

## 🐛 Troubleshooting durante Validação

### Problema: Script falha com "MONGO_URI not found"

**Solução:**
```bash
export MONGO_URI="mongodb://localhost:27017"
# ou adicionar ao .env
```

### Problema: API retorna 404 para conversas

**Possíveis causas:**
- [ ] Serviço conductor não foi reiniciado após mudanças
- [ ] Routes não foram registradas no server.py
- [ ] Gateway não está redirecionando corretamente

**Solução:**
```bash
# Reiniciar conductor
cd src/conductor
# (comando de restart)

# Reiniciar gateway
cd src/conductor-gateway
# (comando de restart)
```

### Problema: Frontend não usa novo modelo

**Possíveis causas:**
- [ ] Feature flag não está `true`
- [ ] Frontend não foi rebuilded
- [ ] Cache do navegador

**Solução:**
```bash
cd src/conductor-web
npm run build
# ou
ng serve --configuration=development

# Limpar cache do navegador (Ctrl+Shift+Del)
```

### Problema: Mensagens não mostram agente

**Possíveis causas:**
- [ ] Template não foi atualizado
- [ ] Interface `Message` não tem campo `agent`
- [ ] Backend não está retornando `agent` nas mensagens

**Solução:**
1. Verificar interface `Message` em `chat.models.ts`
2. Verificar template tem `*ngIf="message.agent"`
3. Verificar response da API inclui campo `agent`

---

## ✅ Checklist Final

### Backend
- [ ] Todos os testes de API passam
- [ ] Scripts de migração executam sem erros
- [ ] MongoDB tem collections corretas
- [ ] Índices criados

### Frontend
- [ ] Feature flag funciona (ON e OFF)
- [ ] Novo modelo funciona corretamente
- [ ] Modelo legado preservado
- [ ] UI mostra informações do agente
- [ ] Histórico compartilhado entre agentes

### Documentação
- [ ] Toda documentação criada
- [ ] Guias de troubleshooting funcionam
- [ ] Exemplos de uso testados

### Caso de Uso
- [ ] Colaboração multi-agente funciona
- [ ] Histórico compartilhado corretamente
- [ ] Performance aceitável

---

## 🎊 Status da Validação

**Data de Validação:** _______________

**Resultado:**
- [ ] ✅ APROVADO - Pronto para produção
- [ ] ⚠️ APROVADO COM RESSALVAS - Pequenos ajustes necessários
- [ ] ❌ REPROVADO - Problemas críticos encontrados

**Observações:**
```
[Escrever observações aqui]
```

**Validado por:** _______________

---

**Próximo passo:** Deploy em produção 🚀
