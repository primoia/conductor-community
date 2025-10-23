# 🎨 Fase 1: Frontend - UI do Seletor de Provider

## 📋 Metadados
- **ID**: fase-01
- **Título**: Frontend - UI do Seletor de Provider
- **Executor**: Agente Frontend
- **Dependências**: Nenhuma
- **Status**: Pendente

## 🎯 Objetivo
Adicionar componente visual de seleção de AI Provider (Claude, Gemini) no `ChatInputComponent`, posicionado ao lado do botão de envio de mensagem.

## 📍 Contexto
O `ChatInputComponent` é responsável por capturar a entrada do usuário e disparar o evento de envio de mensagem. Atualmente possui:
- Textarea para digitação
- Botão de envio com ícone ⬆️
- Estado de loading com ícone ⏳

Precisamos adicionar um dropdown para seleção do provider, que será usado posteriormente para enviar junto com a mensagem.

## 📁 Arquivos a Modificar

### 1. `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.html`
**Localização**: Template do componente de input do chat

### 2. `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.ts`
**Localização**: Lógica do componente de input do chat

### 3. `src/conductor-web/src/app/shared/conductor-chat/components/chat-input/chat-input.component.scss`
**Localização**: Estilos do componente de input do chat

## 🔧 Tarefas Detalhadas

### ✅ Tarefa 1.1: Adicionar Propriedade `selectedProvider` no Component

**Arquivo**: `chat-input.component.ts`

**Ação**: Adicionar nova propriedade à classe `ChatInputComponent`

**Código a Adicionar**:
```typescript
// Adicionar após as outras propriedades (por volta da linha 20-30)
selectedProvider: string = '';  // '' = usar provider padrão do config.yaml
```

**Justificativa**:
- String vazia (`''`) representa o uso do provider padrão configurado no `config.yaml`
- Valores possíveis: `''`, `'claude'`, `'gemini'`

---

### ✅ Tarefa 1.2: Adicionar Seletor no Template HTML

**Arquivo**: `chat-input.component.html`

**Localização**: Antes do botão de envio (aproximadamente linha 25-29)

**Código Atual** (referência):
```html
<button
  class="icon-button send-button"
  [disabled]="!message.trim() || isLoading"
  (click)="sendMessage()"
>
  <span class="material-icons">{{ isLoading ? 'hourglass_empty' : 'arrow_upward' }}</span>
</button>
```

**Código a Adicionar** (ANTES do botão acima):
```html
<!-- Seletor de Provider -->
<div class="provider-selector">
  <select
    id="provider-select"
    [(ngModel)]="selectedProvider"
    class="provider-dropdown"
    [disabled]="isLoading"
    title="Selecione o AI Provider para esta mensagem"
  >
    <option value="">Padrão</option>
    <option value="claude">Claude</option>
    <option value="gemini">Gemini</option>
  </select>
</div>
```

**Justificativa**:
- `[(ngModel)]`: Two-way binding com a propriedade `selectedProvider`
- `[disabled]="isLoading"`: Desabilita durante envio de mensagem
- Valor vazio (`""`) representa o provider padrão do sistema

---

### ✅ Tarefa 1.3: Adicionar Estilos CSS

**Arquivo**: `chat-input.component.scss`

**Código a Adicionar**:
```scss
.provider-selector {
  display: flex;
  align-items: center;
  margin-right: 8px;

  .provider-dropdown {
    padding: 6px 12px;
    border: 1px solid var(--border-color, #ccc);
    border-radius: 6px;
    background-color: var(--input-bg, white);
    color: var(--text-color, #333);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 100px;

    &:hover:not(:disabled) {
      border-color: var(--primary-color, #007bff);
    }

    &:focus {
      outline: none;
      border-color: var(--primary-color, #007bff);
      box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      background-color: var(--disabled-bg, #f5f5f5);
    }

    option {
      padding: 8px;
    }
  }
}
```

**Justificativa**:
- Consistente com design system existente (variáveis CSS)
- Responsivo e acessível
- Estados visuais claros (hover, focus, disabled)

---

### ✅ Tarefa 1.4: Garantir Importação do FormsModule (se necessário)

**Arquivo**: Verificar em `chat-input.component.ts` ou módulo pai

**Verificação**:
```typescript
// Verificar se FormsModule está importado no módulo
// Se não estiver, adicionar no módulo correspondente:
import { FormsModule } from '@angular/forms';

// E no @NgModule:
imports: [
  // ... outros imports
  FormsModule
]
```

**Nota**: Se o componente já usa `[(ngModel)]` em outros lugares, essa importação já existe.

---

## ✅ Checklist de Validação

Após implementação, verificar:

- [ ] **Visual**: Dropdown aparece ao lado do botão de envio
- [ ] **Funcional**: Dropdown permite seleção de "Padrão", "Claude", "Gemini"
- [ ] **Estado**: Dropdown fica desabilitado quando `isLoading === true`
- [ ] **Binding**: Valor selecionado é armazenado em `selectedProvider`
- [ ] **CSS**: Estilos estão consistentes com o resto da aplicação
- [ ] **Acessibilidade**: Dropdown tem atributo `title` para tooltips
- [ ] **Console**: Nenhum erro no console do navegador
- [ ] **Build**: Aplicação compila sem erros (`npm run build` ou `ng build`)

## 📦 Entregáveis

1. ✅ Propriedade `selectedProvider` adicionada no component
2. ✅ Dropdown HTML adicionado no template
3. ✅ Estilos CSS implementados
4. ✅ FormsModule importado (se necessário)
5. ✅ Aplicação buildando sem erros

## 🔗 Próxima Fase

Após validação desta fase, prosseguir para:
- **Fase 2**: Frontend - Integração com AgentService
  - Modificar evento `messageSent` para incluir provider
  - Atualizar `ConductorChatComponent` para receber provider
  - Atualizar `AgentService.executeAgent()` para enviar provider ao backend

## ⚠️ Observações Importantes

1. **Não implementar lógica de envio**: Esta fase é APENAS UI visual
2. **Não modificar método `sendMessage()`**: Será feito na Fase 2
3. **Não alterar `@Output() messageSent`**: Será feito na Fase 2
4. **Não adicionar persistência**: Será discutido após validação do fluxo completo

## 🎯 Critério de Sucesso

A fase será considerada completa quando:
1. Dropdown visível e funcional no chat input
2. Valor selecionado armazenado em `selectedProvider`
3. Interface responsiva e sem erros de console
4. Build da aplicação executando sem erros
