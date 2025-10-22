# Saga 001: Validação e Melhoria do Fluxo "Criar Novo Roteiro"

## 📋 Context & Background

O sistema Conductor Web possui funcionalidades de gerenciamento de roteiros (screenplays) com integração MongoDB e sincronização com disco local. O fluxo de "Criar Novo Roteiro" é fundamental para a experiência do usuário, mas apresenta gaps identificados na análise do código atual.

**Problemas Identificados:**
- Nomenclatura automática não segue padrão "Novo Roteiro + data"
- Falta auto-save antes de criar novo roteiro
- Gerenciamento de filePath pode ser melhorado
- Validação de arquivos aceita .txt além de .md
- Falta detecção inteligente de duplicatas por path

**Motivação:** Garantir que o fluxo de criação de roteiros seja robusto, intuitivo e mantenha consistência entre MongoDB e disco local.

## 🎯 Objectives

1. **Validar implementação atual** do fluxo "Criar Novo Roteiro"
2. **Implementar nomenclatura automática** com padrão "Novo Roteiro + data"
3. **Melhorar gerenciamento de filePath** para importação/exportação
4. **Implementar auto-save** antes de criar novo roteiro
5. **Adicionar validação** para aceitar apenas arquivos .md
6. **Criar sistema de detecção** de duplicatas por path
7. **Implementar renomeação** tanto no MongoDB quanto no disco

## 🔍 Scope

**In Scope:**
- Validação dos 3 fluxos de criação de roteiros existentes
- Implementação de nomenclatura automática com data
- Melhoria do gerenciamento de filePath (importPath/exportPath)
- Auto-save antes de transições de roteiro
- Validação de arquivos apenas .md
- Sistema de detecção de duplicatas
- Funcionalidade de renomeação
- Testes de validação para todos os fluxos
- Documentação de comportamento esperado

**Out of Scope:**
- Refatoração completa da arquitetura de roteiros
- Migração de dados existentes
- Implementação de versionamento de arquivos
- Sistema de backup automático
- Interface de usuário para configurações avançadas

## 💡 Proposed Solution

### Estratégia de Validação
1. **Análise de Código Atual** - Mapear implementação existente
2. **Testes de Fluxo** - Validar cada cenário de criação
3. **Implementação Incremental** - Melhorar gaps identificados
4. **Validação Contínua** - Testes após cada melhoria

### Melhorias Propostas

#### 1. Nomenclatura Automática
```typescript
// Padrão atual: novo-roteiro-YYYY-MM-DDTHH-MM-SS
// Novo padrão: Novo Roteiro YYYY-MM-DD HH-MM-SS.md
const generateScreenplayName = (): string => {
  const now = new Date();
  const dateStr = now.toISOString().slice(0, 19).replace(/[:.]/g, '-');
  return `Novo Roteiro ${dateStr}.md`;
};
```

#### 2. Gerenciamento de FilePath Duplo
```typescript
interface Screenplay extends ScreenplayListItem {
  content: string;
  importPath?: string;  // Caminho de onde foi importado
  exportPath?: string;  // Último caminho de exportação
}
```

#### 3. Auto-save Inteligente
```typescript
// Salvar roteiro atual antes de criar novo
private async ensureCurrentScreenplaySaved(): Promise<void> {
  if (this.isDirty && this.currentScreenplay) {
    await this.save();
  }
}
```

#### 4. Detecção de Duplicatas
```typescript
// Chave única baseada em path + nome
const generateFileKey = (filePath: string, fileName: string): string => {
  return btoa(`${filePath}:${fileName}`).replace(/[^a-zA-Z0-9]/g, '');
};
```

## 📦 Deliverables

1. **Documento de Validação** - Checklist detalhado para cada fluxo
2. **Implementação de Nomenclatura** - Geração automática de nomes
3. **Sistema de FilePath Duplo** - ImportPath e ExportPath
4. **Auto-save Inteligente** - Salvamento antes de transições
5. **Validação de Arquivos** - Apenas .md aceitos
6. **Detecção de Duplicatas** - Sistema de chaves únicas
7. **Funcionalidade de Renomeação** - MongoDB + disco
8. **Testes de Validação** - Cobertura completa dos fluxos
9. **Documentação Atualizada** - Comportamento esperado

## ⚠️ Risks & Constraints

**Riscos Técnicos:**
- Quebra de compatibilidade com roteiros existentes
- Performance impact com validações adicionais
- Complexidade do gerenciamento de dois paths

**Riscos de UX:**
- Confusão do usuário com dois paths
- Perda de dados se auto-save falhar
- Conflitos de nomenclatura

**Constraints:**
- Manter compatibilidade com MongoDB existente
- Não quebrar funcionalidades atuais
- Manter performance aceitável
- Suporte apenas a navegadores modernos (File System Access API)

## 🗓️ Phasing Considerations

### Fase 1: Validação e Análise (1-2 dias)
- Mapear implementação atual
- Criar testes de validação
- Identificar gaps críticos

### Fase 2: Melhorias Core (2-3 dias)
- Implementar nomenclatura automática
- Adicionar auto-save inteligente
- Implementar validação .md

### Fase 3: Gerenciamento de Arquivos (2-3 dias)
- Implementar filePath duplo
- Criar detecção de duplicatas
- Implementar renomeação

### Fase 4: Validação e Testes (1-2 dias)
- Testes completos de todos os fluxos
- Validação de compatibilidade
- Documentação final

## ✅ Success Criteria

1. **Funcionalidade** - Todos os 3 fluxos de criação funcionam perfeitamente
2. **Nomenclatura** - Nomes automáticos seguem padrão "Novo Roteiro + data"
3. **FilePath** - ImportPath e ExportPath gerenciados corretamente
4. **Auto-save** - Roteiro anterior salvo antes de criar novo
5. **Validação** - Apenas arquivos .md aceitos
6. **Duplicatas** - Sistema detecta arquivos duplicados por path
7. **Renomeação** - Funciona tanto no MongoDB quanto no disco
8. **Performance** - Sem impacto significativo na velocidade
9. **UX** - Interface clara e intuitiva
10. **Compatibilidade** - Não quebra funcionalidades existentes

## 🔗 Dependencies

**Dependências Técnicas:**
- MongoDB com campos filePath existentes
- File System Access API do navegador
- Angular framework atual
- ScreenplayStorage service

**Dependências de Equipe:**
- Desenvolvedor frontend para implementação
- QA para testes de validação
- UX para revisão de interface

**Dependências Externas:**
- Navegadores modernos (Chrome 86+, Firefox 111+)
- Sistema de arquivos do usuário

## 📚 References

- [Documento Original do Screenplay](../001-frontend-gerenciamento-roteiros.md)
- [Código ScreenplayInteractive](../../src/conductor-web/src/app/living-screenplay-simple/screenplay-interactive.ts)
- [Código ScreenplayManager](../../src/conductor-web/src/app/living-screenplay-simple/screenplay-manager/screenplay-manager.ts)
- [Código ScreenplayStorage](../../src/conductor-web/src/app/services/screenplay-storage.ts)
- [File System Access API](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API)