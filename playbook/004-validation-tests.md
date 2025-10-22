# Plano 004: Validação e Testes de Integração

## 🎯 Objetivo
Implementar testes abrangentes e validação completa do sistema de gerenciamento de roteiros, garantindo que todas as funcionalidades implementadas funcionem corretamente e atendam aos critérios de sucesso.

## 📋 Contexto
Após a implementação dos planos anteriores (backend, frontend core e UI), é necessário validar:
- Todos os 3 fluxos de criação de roteiros
- Nomenclatura automática
- Auto-save e transições
- Gerenciamento de filePath
- Detecção de duplicatas
- Funcionalidade de renomeação
- Integração entre frontend e backend

## 🔍 Análise dos Testes Necessários

### Tipos de Testes:
- **Testes Unitários**: Componentes e serviços individuais
- **Testes de Integração**: Fluxos completos frontend-backend
- **Testes E2E**: Cenários de usuário completos
- **Testes de Performance**: Impacto na velocidade
- **Testes de Compatibilidade**: Diferentes navegadores

### Cenários Críticos:
- Criação de roteiros em todos os fluxos
- Importação/exportação com filePath
- Resolução de conflitos de duplicatas
- Auto-save em diferentes situações
- Validação de arquivos .md

## 📝 Checklist de Implementação

### 1. Testes dos 3 Fluxos de Criação (2h)
- [ ] **1.1** Testar "Novo Roteiro" (em branco)
- [ ] **1.2** Testar "Novo Roteiro" (com agente padrão)
- [ ] **1.3** Testar criação via Gerenciador de Roteiros
- [ ] **1.4** Validar nomenclatura automática em todos os fluxos
- [ ] **1.5** Verificar auto-save antes de transições
- [ ] **1.6** Testar validação de nomes únicos

### 2. Validação de Nomenclatura Automática (1h)
- [ ] **2.1** Verificar padrão "Novo Roteiro + data"
- [ ] **2.2** Testar geração de nomes únicos
- [ ] **2.3** Validar fallback para nomes duplicados
- [ ] **2.4** Testar em diferentes fusos horários
- [ ] **2.5** Verificar consistência entre frontend e backend

### 3. Testes de Auto-save e Transições (1h)
- [ ] **3.1** Testar auto-save com debounce
- [ ] **3.2** Verificar salvamento antes de criar novo roteiro
- [ ] **3.3** Testar salvamento antes de importar
- [ ] **3.4** Validar salvamento antes de exportar
- [ ] **3.5** Testar tratamento de erros de salvamento
- [ ] **3.6** Verificar indicadores visuais de status

### 4. Validação de Gerenciamento de FilePath (1h)
- [ ] **4.1** Testar importPath e exportPath
- [ ] **4.2** Verificar sincronização entre paths
- [ ] **4.3** Testar persistência no MongoDB
- [ ] **4.4** Validar exibição na UI
- [ ] **4.5** Testar navegação para arquivos
- [ ] **4.6** Verificar compatibilidade com filePath existente

### 5. Testes de Detecção de Duplicatas (1h)
- [ ] **5.1** Testar geração de chave única
- [ ] **5.2** Verificar detecção de arquivos duplicados
- [ ] **5.3** Testar resolução de conflitos
- [ ] **5.4** Validar modal de resolução
- [ ] **5.5** Testar diferentes cenários de conflito
- [ ] **5.6** Verificar performance com muitos arquivos

### 6. Validação de Funcionalidade de Renomeação (1h)
- [ ] **6.1** Testar renomeação no MongoDB
- [ ] **6.2** Verificar renomeação no disco (se aplicável)
- [ ] **6.3** Testar validação de nomes únicos
- [ ] **6.4** Validar sincronização de referências
- [ ] **6.5** Testar renomeação em lote
- [ ] **6.6** Verificar rollback em caso de erro

### 7. Testes de Validação de Arquivos (1h)
- [ ] **7.1** Testar aceitação apenas de arquivos .md
- [ ] **7.2** Verificar validação de conteúdo Markdown
- [ ] **7.3** Testar mensagens de erro específicas
- [ ] **7.4** Validar seletor de arquivos
- [ ] **7.5** Testar diferentes tipos de arquivo inválidos
- [ ] **7.6** Verificar feedback visual de validação

## 🛠️ Implementação Técnica

### 1. Testes Unitários (Jest/Karma)
```typescript
// Testes para geração de nomes
describe('ScreenplayNameGenerator', () => {
  it('should generate name with correct format', () => {
    const name = generateScreenplayName();
    expect(name).toMatch(/^Novo Roteiro \d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.md$/);
  });
  
  it('should generate unique names', () => {
    const name1 = generateScreenplayName();
    const name2 = generateScreenplayName();
    expect(name1).not.toBe(name2);
  });
});

// Testes para auto-save
describe('AutoSaveService', () => {
  it('should save before creating new screenplay', async () => {
    const service = new AutoSaveService();
    const mockSave = jest.fn();
    service.save = mockSave;
    
    await service.ensureCurrentScreenplaySaved();
    expect(mockSave).toHaveBeenCalled();
  });
});

// Testes para detecção de duplicatas
describe('DuplicateDetectionService', () => {
  it('should generate consistent file keys', () => {
    const key1 = generateFileKey('/path/to/file.md', 'file.md');
    const key2 = generateFileKey('/path/to/file.md', 'file.md');
    expect(key1).toBe(key2);
  });
  
  it('should detect duplicate files', async () => {
    const service = new DuplicateDetectionService();
    const existingFile = { fileKey: 'abc123' };
    const newFile = { fileKey: 'abc123' };
    
    const isDuplicate = await service.checkDuplicate(newFile);
    expect(isDuplicate).toBe(true);
  });
});
```

### 2. Testes de Integração (Cypress)
```typescript
// Teste E2E do fluxo completo
describe('Screenplay Management E2E', () => {
  it('should create new screenplay with auto-naming', () => {
    cy.visit('/');
    cy.get('[data-testid="new-screenplay-btn"]').click();
    cy.get('[data-testid="screenplay-name"]').should('contain', 'Novo Roteiro');
    cy.get('[data-testid="save-status"]').should('contain', 'Salvo');
  });
  
  it('should handle file import with conflict resolution', () => {
    cy.visit('/');
    cy.get('[data-testid="import-btn"]').click();
    cy.get('[data-testid="file-input"]').selectFile('test-file.md');
    cy.get('[data-testid="conflict-modal"]').should('be.visible');
    cy.get('[data-testid="overwrite-btn"]').click();
    cy.get('[data-testid="import-success"]').should('be.visible');
  });
  
  it('should auto-save before transitions', () => {
    cy.visit('/');
    cy.get('[data-testid="editor"]').type('Test content');
    cy.get('[data-testid="save-status"]').should('contain', 'Alterações não salvas');
    cy.get('[data-testid="new-screenplay-btn"]').click();
    cy.get('[data-testid="save-status"]').should('contain', 'Salvo');
  });
});
```

### 3. Testes de Performance
```typescript
// Teste de performance para detecção de duplicatas
describe('Performance Tests', () => {
  it('should handle large number of files efficiently', async () => {
    const startTime = performance.now();
    const files = generateMockFiles(1000);
    const duplicates = await findDuplicates(files);
    const endTime = performance.now();
    
    expect(endTime - startTime).toBeLessThan(1000); // < 1 segundo
    expect(duplicates.length).toBeGreaterThan(0);
  });
  
  it('should auto-save without blocking UI', async () => {
    const service = new AutoSaveService();
    const startTime = performance.now();
    await service.scheduleAutoSave();
    const endTime = performance.now();
    
    expect(endTime - startTime).toBeLessThan(100); // < 100ms
  });
});
```

### 4. Testes de Compatibilidade
```typescript
// Teste de compatibilidade com diferentes navegadores
describe('Browser Compatibility', () => {
  const browsers = ['chrome', 'firefox', 'safari', 'edge'];
  
  browsers.forEach(browser => {
    it(`should work in ${browser}`, () => {
      cy.visit('/');
      cy.get('[data-testid="new-screenplay-btn"]').click();
      cy.get('[data-testid="screenplay-name"]').should('be.visible');
    });
  });
});
```

## 📊 Critérios de Sucesso

### 1. Funcionalidade (100%)
- ✅ Todos os 3 fluxos de criação funcionam
- ✅ Nomenclatura automática implementada
- ✅ Auto-save funciona corretamente
- ✅ FilePath duplo gerenciado
- ✅ Validação de arquivos .md
- ✅ Detecção de duplicatas
- ✅ Funcionalidade de renomeação

### 2. Performance (95%+)
- ✅ Tempo de resposta < 500ms para operações básicas
- ✅ Auto-save não bloqueia UI
- ✅ Detecção de duplicatas < 1s para 1000 arquivos
- ✅ Carregamento de roteiros < 2s

### 3. Usabilidade (90%+)
- ✅ Interface intuitiva e clara
- ✅ Feedback visual adequado
- ✅ Mensagens de erro informativas
- ✅ Navegação fluida

### 4. Compatibilidade (95%+)
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### 5. Acessibilidade (80%+)
- ✅ Navegação por teclado
- ✅ Leitores de tela
- ✅ Contraste adequado
- ✅ Tamanhos de fonte apropriados

## 🧪 Estratégia de Testes

### 1. Testes Automatizados
- **Unitários**: 80%+ cobertura de código
- **Integração**: Todos os fluxos principais
- **E2E**: Cenários críticos de usuário
- **Performance**: Benchmarks definidos

### 2. Testes Manuais
- **Exploratórios**: Cenários não cobertos
- **Usabilidade**: Feedback de usuários reais
- **Compatibilidade**: Diferentes dispositivos
- **Acessibilidade**: Usuários com deficiências

### 3. Testes de Regressão
- **Automáticos**: Executados a cada commit
- **Manuais**: Antes de cada release
- **Smoke**: Validação rápida de funcionalidades críticas

## 📋 Plano de Execução

### Semana 1: Preparação
- Configurar ambiente de testes
- Implementar testes unitários
- Configurar CI/CD para testes automáticos

### Semana 2: Testes de Integração
- Implementar testes E2E
- Testes de performance
- Validação de compatibilidade

### Semana 3: Validação Final
- Testes manuais completos
- Validação com usuários
- Correção de bugs encontrados

## ⚠️ Riscos e Mitigações

### Riscos Técnicos:
- **Falsos positivos**: Configurar thresholds adequados
- **Testes lentos**: Otimizar e paralelizar
- **Ambiente inconsistente**: Usar Docker para testes

### Riscos de Qualidade:
- **Cobertura insuficiente**: Implementar métricas de cobertura
- **Cenários não cobertos**: Revisão regular de casos de teste
- **Regressões**: Implementar testes de regressão automáticos

## 🔗 Dependências

### Internas:
- Todos os planos anteriores implementados
- Ambiente de desenvolvimento configurado
- Dados de teste preparados

### Externas:
- Ferramentas de teste (Jest, Cypress)
- Serviços de CI/CD
- Ambientes de teste

## 📅 Estimativa de Tempo

- **Total**: 8 horas
- **Fluxos de criação**: 2 horas
- **Nomenclatura**: 1 hora
- **Auto-save**: 1 hora
- **FilePath**: 1 hora
- **Duplicatas**: 1 hora
- **Renomeação**: 1 hora
- **Validação de arquivos**: 1 hora

## 🚀 Próximos Passos

1. Aprovação do plano
2. Configuração do ambiente de testes
3. Implementação dos testes
4. Execução e validação
5. Correção de bugs encontrados
6. Documentação dos resultados