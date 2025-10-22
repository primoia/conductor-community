# Plano 001: Backend - Validação e Melhorias da API de Roteiros

## 🎯 Objetivo
Implementar melhorias no backend (conductor-gateway) para suportar as funcionalidades avançadas de gerenciamento de roteiros, incluindo validação de arquivos, filePath duplo e detecção de duplicatas.

## 📋 Contexto
O backend atual possui uma API básica de roteiros, mas precisa ser expandida para suportar:
- Validação rigorosa de arquivos .md
- Gerenciamento de filePath duplo (importPath/exportPath)
- Detecção de duplicatas por path
- Funcionalidade de renomeação

## 🔍 Análise do Código Atual

### Arquivos Principais:
- `src/conductor-gateway/src/api/routes/screenplays.py` - Rotas da API
- `src/conductor-gateway/src/models/screenplay.py` - Modelos de dados
- `src/conductor-gateway/src/services/screenplay_service.py` - Lógica de negócio

### Funcionalidades Existentes:
- ✅ CRUD básico de roteiros
- ✅ Paginação e busca
- ✅ Soft delete
- ❌ Validação de arquivos
- ❌ FilePath duplo
- ❌ Detecção de duplicatas
- ❌ Renomeação

## 📝 Checklist de Implementação

### 1. Análise da API Atual (1h)
- [ ] **1.1** Mapear endpoints existentes
- [ ] **1.2** Analisar modelos de dados atuais
- [ ] **1.3** Identificar gaps de validação
- [ ] **1.4** Documentar estrutura atual

### 2. Validação de Arquivos .md (2h)
- [ ] **2.1** Implementar validação de extensão .md
- [ ] **2.2** Adicionar validação de conteúdo Markdown
- [ ] **2.3** Criar middleware de validação
- [ ] **2.4** Adicionar mensagens de erro específicas

### 3. FilePath Duplo (2h)
- [ ] **3.1** Estender modelo Screenplay com importPath/exportPath
- [ ] **3.2** Atualizar endpoints para suportar ambos os paths
- [ ] **3.3** Implementar lógica de sincronização
- [ ] **3.4** Adicionar validação de paths

### 4. Detecção de Duplicatas (2h)
- [ ] **4.1** Implementar algoritmo de geração de chave única
- [ ] **4.2** Criar serviço de detecção de duplicatas
- [ ] **4.3** Adicionar endpoint de verificação
- [ ] **4.4** Implementar lógica de resolução de conflitos

### 5. Funcionalidade de Renomeação (1h)
- [ ] **5.1** Criar endpoint de renomeação
- [ ] **5.2** Implementar validação de nomes únicos
- [ ] **5.3** Adicionar suporte a renomeação em lote
- [ ] **5.4** Implementar rollback em caso de erro

## 🛠️ Implementação Técnica

### 1. Modelo de Dados Atualizado
```python
class Screenplay(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content: str
    tags: List[str] = []
    version: int = 1
    created_at: datetime
    updated_at: datetime
    is_deleted: bool = False
    file_path: Optional[str] = None  # Manter para compatibilidade
    import_path: Optional[str] = None  # Novo: caminho de importação
    export_path: Optional[str] = None  # Novo: último caminho de exportação
    file_key: Optional[str] = None  # Novo: chave única para detecção de duplicatas
```

### 2. Validação de Arquivos
```python
def validate_markdown_file(file_path: str) -> bool:
    """Valida se o arquivo é um Markdown válido"""
    if not file_path.endswith('.md'):
        raise ValueError("Apenas arquivos .md são aceitos")
    
    # Validação adicional de conteúdo Markdown
    # Implementar validação de sintaxe básica
    return True
```

### 3. Detecção de Duplicatas
```python
def generate_file_key(file_path: str, file_name: str) -> str:
    """Gera chave única baseada em path + nome"""
    import base64
    key_data = f"{file_path}:{file_name}"
    return base64.b64encode(key_data.encode()).decode().replace('/', '_')

def check_duplicate_by_path(file_path: str, file_name: str) -> Optional[Screenplay]:
    """Verifica se já existe roteiro com mesmo path"""
    file_key = generate_file_key(file_path, file_name)
    return screenplay_service.get_by_file_key(file_key)
```

## 🧪 Testes

### Testes Unitários
- Validação de arquivos .md
- Geração de chaves únicas
- Detecção de duplicatas
- Funcionalidade de renomeação

### Testes de Integração
- Fluxo completo de importação
- Fluxo completo de exportação
- Resolução de conflitos
- Sincronização de filePath

## 📊 Critérios de Sucesso

1. **Funcionalidade**: Todos os endpoints funcionam corretamente
2. **Validação**: Apenas arquivos .md são aceitos
3. **FilePath**: ImportPath e ExportPath gerenciados corretamente
4. **Duplicatas**: Sistema detecta arquivos duplicados
5. **Renomeação**: Funciona sem quebrar referências
6. **Performance**: Sem impacto significativo na velocidade
7. **Compatibilidade**: Não quebra funcionalidades existentes

## ⚠️ Riscos e Mitigações

### Riscos Técnicos:
- **Quebra de compatibilidade**: Manter campo file_path para compatibilidade
- **Performance**: Implementar índices adequados no MongoDB
- **Complexidade**: Implementar em fases incrementais

### Riscos de Dados:
- **Perda de filePath**: Implementar migração gradual
- **Conflitos de chaves**: Usar algoritmo determinístico
- **Inconsistência**: Implementar validação rigorosa

## 🔗 Dependências

### Internas:
- MongoDB com coleção screenplays
- Serviços de validação existentes
- Sistema de logging

### Externas:
- Python 3.8+
- FastAPI
- Pydantic
- Motor (MongoDB driver)

## 📅 Estimativa de Tempo

- **Total**: 8 horas
- **Análise**: 1 hora
- **Validação**: 2 horas
- **FilePath**: 2 horas
- **Duplicatas**: 2 horas
- **Renomeação**: 1 hora

## 🚀 Próximos Passos

1. Aprovação do plano
2. Análise detalhada do código atual
3. Implementação incremental
4. Testes e validação
5. Documentação atualizada