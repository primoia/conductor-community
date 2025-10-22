# Plano 002: Frontend - Melhorias Core do Sistema de Roteiros

## 🎯 Objetivo
Implementar as melhorias principais no frontend (conductor-web) para o sistema de gerenciamento de roteiros, incluindo nomenclatura automática, auto-save inteligente e gerenciamento de filePath duplo.

## 📋 Contexto
O frontend atual possui funcionalidades básicas de gerenciamento de roteiros, mas precisa ser aprimorado para:
- Nomenclatura automática com padrão "Novo Roteiro + data"
- Auto-save inteligente antes de transições
- Gerenciamento de filePath duplo (importPath/exportPath)
- Validação de arquivos .md
- Sistema de detecção de duplicatas
- Funcionalidade de renomeação

## 🔍 Análise do Código Atual

### Componentes Principais:
- `screenplay-interactive.ts` - Componente principal do editor
- `screenplay-manager.ts` - Modal de gerenciamento
- `screenplay-storage.ts` - Serviço de persistência
- `screenplay-interactive.html` - Template principal

### Funcionalidades Existentes:
- ✅ Criação de roteiros
- ✅ Importação/exportação básica
- ✅ Gerenciamento de estado
- ❌ Nomenclatura automática
- ❌ Auto-save inteligente
- ❌ FilePath duplo
- ❌ Validação de arquivos
- ❌ Detecção de duplicatas

## 📝 Checklist de Implementação

### 1. Nomenclatura Automática (2h)
- [ ] **1.1** Implementar função de geração de nomes
- [ ] **1.2** Atualizar fluxo de criação de roteiros
- [ ] **1.3** Adicionar validação de nomes únicos
- [ ] **1.4** Implementar fallback para nomes duplicados

### 2. Auto-save Inteligente (3h)
- [ ] **2.1** Implementar detecção de mudanças (isDirty)
- [ ] **2.2** Criar sistema de auto-save com debounce
- [ ] **2.3** Adicionar auto-save antes de transições
- [ ] **2.4** Implementar indicadores visuais de salvamento
- [ ] **2.5** Adicionar tratamento de erros de salvamento

### 3. Gerenciamento de FilePath Duplo (3h)
- [ ] **3.1** Estender interface Screenplay com importPath/exportPath
- [ ] **3.2** Atualizar ScreenplayStorage para suportar ambos os paths
- [ ] **3.3** Implementar lógica de sincronização
- [ ] **3.4** Adicionar validação de paths
- [ ] **3.5** Atualizar UI para exibir ambos os paths

### 4. Validação de Arquivos .md (1h)
- [ ] **4.1** Implementar validação de extensão .md
- [ ] **4.2** Adicionar validação de conteúdo Markdown
- [ ] **4.3** Criar mensagens de erro específicas
- [ ] **4.4** Atualizar seletor de arquivos

### 5. Sistema de Detecção de Duplicatas (2h)
- [ ] **5.1** Implementar geração de chave única
- [ ] **5.2** Criar serviço de detecção de duplicatas
- [ ] **5.3** Adicionar lógica de resolução de conflitos
- [ ] **5.4** Implementar notificações de duplicatas

### 6. Funcionalidade de Renomeação (1h)
- [ ] **6.1** Implementar modal de renomeação
- [ ] **6.2** Adicionar validação de nomes únicos
- [ ] **6.3** Implementar sincronização com backend
- [ ] **6.4** Adicionar feedback visual

## 🛠️ Implementação Técnica

### 1. Nomenclatura Automática
```typescript
// Função para gerar nomes automáticos
const generateScreenplayName = (): string => {
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 19).replace(/[:.]/g, '-');
  return `Novo Roteiro ${dateStr}.md`;
};

// Validação de nomes únicos
const ensureUniqueName = async (baseName: string): Promise<string> => {
  let name = baseName;
  let counter = 1;
  
  while (await screenplayStorage.nameExists(name)) {
    const nameWithoutExt = baseName.replace('.md', '');
    name = `${nameWithoutExt}-${counter}.md`;
    counter++;
  }
  
  return name;
};
```

### 2. Auto-save Inteligente
```typescript
// Sistema de auto-save com debounce
private autoSaveTimeout?: number;
private readonly AUTO_SAVE_DELAY = 3000; // 3 segundos

private scheduleAutoSave(): void {
  if (this.autoSaveTimeout) {
    clearTimeout(this.autoSaveTimeout);
  }
  
  this.autoSaveTimeout = window.setTimeout(() => {
    if (this.isDirty && this.sourceOrigin === 'database') {
      this.save();
    }
  }, this.AUTO_SAVE_DELAY);
}

// Auto-save antes de transições
private async ensureCurrentScreenplaySaved(): Promise<void> {
  if (this.isDirty && this.currentScreenplay) {
    await this.save();
  }
}
```

### 3. FilePath Duplo
```typescript
// Interface estendida
interface Screenplay extends ScreenplayListItem {
  content: string;
  filePath?: string; // Manter para compatibilidade
  importPath?: string; // Novo: caminho de importação
  exportPath?: string; // Novo: último caminho de exportação
  fileKey?: string; // Novo: chave única para detecção
}

// Lógica de sincronização
private syncFilePath(screenplay: Screenplay, type: 'import' | 'export', path: string): void {
  if (type === 'import') {
    screenplay.importPath = path;
  } else {
    screenplay.exportPath = path;
  }
  
  // Manter filePath para compatibilidade
  screenplay.filePath = path;
}
```

### 4. Validação de Arquivos
```typescript
// Validação de arquivos .md
private validateMarkdownFile(file: File): boolean {
  if (!file.name.endsWith('.md')) {
    this.showError('Apenas arquivos .md são aceitos');
    return false;
  }
  
  // Validação adicional de conteúdo se necessário
  return true;
}

// Atualizar seletor de arquivos
private updateFileInput(): void {
  const fileInput = document.getElementById('file-input') as HTMLInputElement;
  if (fileInput) {
    fileInput.accept = '.md';
  }
}
```

### 5. Detecção de Duplicatas
```typescript
// Geração de chave única
private generateFileKey(filePath: string, fileName: string): string {
  const keyData = `${filePath}:${fileName}`;
  return btoa(keyData).replace(/[^a-zA-Z0-9]/g, '');
}

// Detecção de duplicatas
private async checkForDuplicates(filePath: string, fileName: string): Promise<Screenplay | null> {
  const fileKey = this.generateFileKey(filePath, fileName);
  return await this.screenplayStorage.getByFileKey(fileKey);
}
```

## 🎨 Melhorias de UI/UX

### 1. Indicadores Visuais
- Status de salvamento (salvando, salvo, erro)
- Indicadores de filePath (importado de, exportado para)
- Notificações de duplicatas
- Feedback de validação

### 2. Modais Melhorados
- Modal de renomeação com validação
- Modal de resolução de conflitos
- Modal de exportação com sugestão de caminho

### 3. Validação em Tempo Real
- Validação de nomes únicos
- Validação de arquivos antes do upload
- Feedback imediato de erros

## 🧪 Testes

### Testes Unitários
- Geração de nomes automáticos
- Validação de arquivos
- Detecção de duplicatas
- Auto-save logic

### Testes de Integração
- Fluxo completo de criação
- Fluxo de importação/exportação
- Resolução de conflitos
- Sincronização de filePath

### Testes E2E
- Cenários de usuário completos
- Validação de todos os fluxos
- Testes de performance

## 📊 Critérios de Sucesso

1. **Funcionalidade**: Todos os fluxos funcionam perfeitamente
2. **Nomenclatura**: Nomes automáticos seguem padrão definido
3. **Auto-save**: Funciona sem perda de dados
4. **FilePath**: ImportPath e ExportPath gerenciados corretamente
5. **Validação**: Apenas arquivos .md aceitos
6. **Duplicatas**: Sistema detecta e resolve conflitos
7. **Renomeação**: Funciona sem quebrar referências
8. **UX**: Interface clara e intuitiva
9. **Performance**: Sem impacto significativo na velocidade

## ⚠️ Riscos e Mitigações

### Riscos Técnicos:
- **Perda de dados**: Implementar auto-save robusto
- **Conflitos de estado**: Usar gerenciamento de estado consistente
- **Performance**: Implementar debounce e otimizações

### Riscos de UX:
- **Confusão do usuário**: Implementar feedback visual claro
- **Perda de contexto**: Manter estado consistente
- **Erros de validação**: Implementar mensagens claras

## 🔗 Dependências

### Internas:
- Backend com novas funcionalidades (Plano 001)
- Serviços de validação
- Sistema de notificações

### Externas:
- Angular 17+
- File System Access API
- Navegadores modernos

## 📅 Estimativa de Tempo

- **Total**: 12 horas
- **Nomenclatura**: 2 horas
- **Auto-save**: 3 horas
- **FilePath**: 3 horas
- **Validação**: 1 hora
- **Duplicatas**: 2 horas
- **Renomeação**: 1 hora

## 🚀 Próximos Passos

1. Aprovação do plano
2. Implementação incremental
3. Testes e validação
4. Integração com backend
5. Documentação atualizada