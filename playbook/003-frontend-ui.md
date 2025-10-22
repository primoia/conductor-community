# Plano 003: Frontend - Melhorias de Interface e UX

## 🎯 Objetivo
Implementar melhorias de interface e experiência do usuário para o sistema de gerenciamento de roteiros, focando em modais aprimorados, indicadores visuais e feedback de usuário.

## 📋 Contexto
Após a implementação das funcionalidades core (Plano 002), é necessário aprimorar a interface para:
- Modais mais intuitivos e informativos
- Indicadores visuais de status e filePath
- Feedback visual para auto-save
- Notificações de conflitos e erros
- Melhor experiência geral do usuário

## 🔍 Análise do Código Atual

### Componentes de UI:
- `screenplay-interactive.html` - Template principal
- `screenplay-manager.html` - Modal de gerenciamento
- `screenplay-controls.css` - Estilos dos controles
- `screenplay-popup.css` - Estilos dos modais

### Funcionalidades de UI Existentes:
- ✅ Modais básicos de gerenciamento
- ✅ Botões de toolbar
- ✅ Lista de roteiros
- ❌ Indicadores de status
- ❌ Feedback visual avançado
- ❌ Notificações de sistema
- ❌ Modais de confirmação

## 📝 Checklist de Implementação

### 1. Melhorias nos Modais (2h)
- [ ] **1.1** Redesenhar modal de importação com indicadores de filePath
- [ ] **1.2** Melhorar modal de exportação com sugestão de caminho
- [ ] **1.3** Criar modal de renomeação com validação em tempo real
- [ ] **1.4** Implementar modal de resolução de conflitos
- [ ] **1.5** Adicionar animações e transições suaves

### 2. Indicadores de FilePath (1h)
- [ ] **2.1** Adicionar indicador de arquivo importado
- [ ] **2.2** Mostrar último caminho de exportação
- [ ] **2.3** Implementar tooltips informativos
- [ ] **2.4** Adicionar botão de navegação para arquivo

### 3. Feedback Visual para Auto-save (1h)
- [ ] **3.1** Implementar indicador de status de salvamento
- [ ] **3.2** Adicionar animação de salvamento
- [ ] **3.3** Mostrar timestamp do último salvamento
- [ ] **3.4** Implementar indicador de mudanças não salvas

### 4. Notificações de Sistema (1h)
- [ ] **4.1** Criar sistema de notificações toast
- [ ] **4.2** Implementar notificações de duplicatas
- [ ] **4.3** Adicionar notificações de erro
- [ ] **4.4** Implementar notificações de sucesso

### 5. Melhorias Gerais de UX (1h)
- [ ] **5.1** Adicionar loading states
- [ ] **5.2** Implementar confirmações para ações destrutivas
- [ ] **5.3** Melhorar responsividade
- [ ] **5.4** Adicionar atalhos de teclado

## 🛠️ Implementação Técnica

### 1. Sistema de Notificações
```typescript
// Serviço de notificações
@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notifications: Notification[] = [];
  
  showSuccess(message: string, duration: number = 3000): void {
    this.addNotification({
      id: this.generateId(),
      type: 'success',
      message,
      duration,
      timestamp: new Date()
    });
  }
  
  showError(message: string, duration: number = 5000): void {
    this.addNotification({
      id: this.generateId(),
      type: 'error',
      message,
      duration,
      timestamp: new Date()
    });
  }
  
  showWarning(message: string, duration: number = 4000): void {
    this.addNotification({
      id: this.generateId(),
      type: 'warning',
      message,
      duration,
      timestamp: new Date()
    });
  }
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration: number;
  timestamp: Date;
}
```

### 2. Indicadores de Status
```typescript
// Componente de status de salvamento
@Component({
  selector: 'app-save-status',
  template: `
    <div class="save-status" [class]="statusClass">
      <i [class]="statusIcon"></i>
      <span>{{ statusText }}</span>
      <span *ngIf="lastSaved" class="last-saved">
        Último salvamento: {{ lastSaved | date:'short' }}
      </span>
    </div>
  `
})
export class SaveStatusComponent {
  @Input() isDirty: boolean = false;
  @Input() isSaving: boolean = false;
  @Input() lastSaved: Date | null = null;
  
  get statusClass(): string {
    if (this.isSaving) return 'saving';
    if (this.isDirty) return 'dirty';
    return 'saved';
  }
  
  get statusIcon(): string {
    if (this.isSaving) return 'fas fa-spinner fa-spin';
    if (this.isDirty) return 'fas fa-circle';
    return 'fas fa-check-circle';
  }
  
  get statusText(): string {
    if (this.isSaving) return 'Salvando...';
    if (this.isDirty) return 'Alterações não salvas';
    return 'Salvo';
  }
}
```

### 3. Modal de Resolução de Conflitos
```typescript
// Modal para resolução de conflitos de duplicatas
@Component({
  selector: 'app-conflict-resolution-modal',
  template: `
    <div class="modal-overlay" (click)="onCancel()">
      <div class="modal-content" (click)="$event.stopPropagation()">
        <div class="modal-header">
          <h3>Conflito de Arquivo Detectado</h3>
          <button class="close-btn" (click)="onCancel()">×</button>
        </div>
        
        <div class="modal-body">
          <p>Um arquivo com o mesmo nome já existe:</p>
          <div class="file-info">
            <strong>{{ existingFile.name }}</strong>
            <small>{{ existingFile.filePath }}</small>
          </div>
          
          <div class="options">
            <button class="btn btn-primary" (click)="onOverwrite()">
              Sobrescrever
            </button>
            <button class="btn btn-secondary" (click)="onKeepExisting()">
              Manter Existente
            </button>
            <button class="btn btn-outline" (click)="onRename()">
              Renomear
            </button>
          </div>
        </div>
      </div>
    </div>
  `
})
export class ConflictResolutionModalComponent {
  @Input() existingFile: Screenplay;
  @Input() newFile: File;
  @Output() resolve = new EventEmitter<ConflictResolution>();
  
  onOverwrite(): void {
    this.resolve.emit({ action: 'overwrite' });
  }
  
  onKeepExisting(): void {
    this.resolve.emit({ action: 'keep-existing' });
  }
  
  onRename(): void {
    this.resolve.emit({ action: 'rename' });
  }
  
  onCancel(): void {
    this.resolve.emit({ action: 'cancel' });
  }
}

interface ConflictResolution {
  action: 'overwrite' | 'keep-existing' | 'rename' | 'cancel';
  newName?: string;
}
```

### 4. Indicadores de FilePath
```typescript
// Componente para exibir informações de filePath
@Component({
  selector: 'app-file-path-info',
  template: `
    <div class="file-path-info" *ngIf="screenplay">
      <div class="path-item" *ngIf="screenplay.importPath">
        <i class="fas fa-download"></i>
        <span>Importado de:</span>
        <span class="path">{{ screenplay.importPath }}</span>
        <button class="btn-icon" (click)="openFile(screenplay.importPath)">
          <i class="fas fa-external-link-alt"></i>
        </button>
      </div>
      
      <div class="path-item" *ngIf="screenplay.exportPath">
        <i class="fas fa-upload"></i>
        <span>Exportado para:</span>
        <span class="path">{{ screenplay.exportPath }}</span>
        <button class="btn-icon" (click)="openFile(screenplay.exportPath)">
          <i class="fas fa-external-link-alt"></i>
        </button>
      </div>
    </div>
  `
})
export class FilePathInfoComponent {
  @Input() screenplay: Screenplay | null = null;
  
  openFile(path: string): void {
    // Implementar abertura do arquivo no sistema
    window.open(`file://${path}`, '_blank');
  }
}
```

## 🎨 Melhorias de Design

### 1. Sistema de Cores
```scss
// Variáveis de cores para status
:root {
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;
  
  --color-save-status: var(--color-info);
  --color-dirty-status: var(--color-warning);
  --color-saving-status: var(--color-info);
}

// Classes de status
.save-status {
  &.saved { color: var(--color-success); }
  &.dirty { color: var(--color-warning); }
  &.saving { color: var(--color-info); }
}
```

### 2. Animações e Transições
```scss
// Animações suaves
.modal-overlay {
  animation: fadeIn 0.3s ease-out;
}

.modal-content {
  animation: slideIn 0.3s ease-out;
}

.notification {
  animation: slideInRight 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
```

### 3. Responsividade
```scss
// Breakpoints responsivos
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 20px auto;
  }
  
  .file-path-info {
    flex-direction: column;
    gap: 10px;
  }
  
  .path-item {
    flex-direction: column;
    align-items: flex-start;
  }
}
```

## 🧪 Testes

### Testes de Componentes
- Renderização de indicadores de status
- Funcionamento de modais
- Sistema de notificações
- Responsividade

### Testes de Integração
- Fluxo completo com feedback visual
- Interação entre componentes
- Validação de estados

### Testes de Acessibilidade
- Navegação por teclado
- Leitores de tela
- Contraste de cores
- Tamanhos de fonte

## 📊 Critérios de Sucesso

1. **Usabilidade**: Interface intuitiva e fácil de usar
2. **Feedback**: Usuário sempre sabe o que está acontecendo
3. **Responsividade**: Funciona bem em diferentes tamanhos de tela
4. **Acessibilidade**: Acessível para usuários com deficiências
5. **Performance**: Animações suaves sem impacto na performance
6. **Consistência**: Design consistente em toda a aplicação

## ⚠️ Riscos e Mitigações

### Riscos de UX:
- **Sobrecarga visual**: Implementar indicadores discretos
- **Confusão**: Usar ícones e cores consistentes
- **Performance**: Otimizar animações e transições

### Riscos Técnicos:
- **Complexidade**: Manter componentes simples e focados
- **Manutenibilidade**: Usar padrões consistentes
- **Compatibilidade**: Testar em diferentes navegadores

## 🔗 Dependências

### Internas:
- Funcionalidades core implementadas (Plano 002)
- Sistema de notificações
- Serviços de validação

### Externas:
- Angular Material (opcional)
- Font Awesome (ícones)
- CSS Grid/Flexbox

## 📅 Estimativa de Tempo

- **Total**: 6 horas
- **Modais**: 2 horas
- **Indicadores**: 1 hora
- **Feedback**: 1 hora
- **Notificações**: 1 hora
- **Melhorias gerais**: 1 hora

## 🚀 Próximos Passos

1. Aprovação do plano
2. Implementação dos componentes
3. Testes e validação
4. Integração com funcionalidades core
5. Documentação de design