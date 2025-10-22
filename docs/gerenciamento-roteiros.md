# Gerenciamento de Roteiros no Conductor Web

Este documento detalha a funcionalidade de "Gerenciamento de Roteiros" na interface web do Conductor, cobrindo os fluxos de criação, carregamento, salvamento, importação e exportação de roteiros. O objetivo é fornecer uma compreensão clara de como os roteiros são persistidos e manipulados, tanto no banco de dados (MongoDB) quanto no disco local do usuário.

## 1. Conceitos Chave

*   **Roteiro (Screenplay):** Representa um documento Markdown interativo, que pode conter agentes de IA.
*   **`ScreenplayListItem`:** Uma versão leve do roteiro, usada para listagens (ex: no Gerenciador de Roteiros), contendo metadados como `id`, `name`, `description`, `version`, `createdAt`, `updatedAt`, `isDeleted` e `filePath`.
*   **`Screenplay`:** A representação completa do roteiro, estendendo `ScreenplayListItem` e incluindo o `content` (o conteúdo Markdown real).
*   **`ScreenplayPayload`:** Interface para os dados enviados ao backend para criar ou atualizar um roteiro, incluindo `name`, `content`, `description`, `tags` e `filePath`.
*   **`sourceOrigin`:** Um estado interno (`'database'`, `'disk'`, `'new'`) que indica a origem do roteiro atualmente carregado no editor, influenciando o comportamento de salvamento.
*   **`isDirty`:** Um flag booleano que indica se o roteiro atual no editor possui alterações não salvas.
*   **`filePath`:** Um campo opcional no objeto `Screenplay` que armazena o último caminho conhecido do arquivo no disco local, usado para sugerir nomes de arquivo e para a funcionalidade de exportação.

## 2. Fluxos de Trabalho

### 2.1. Criação de Novo Roteiro

#### Fluxo 2.1.1: "Novo Roteiro" (Em Branco)

1.  **Ação do Usuário:** Clica no botão "Novo Roteiro" (📄) na barra de ferramentas.
2.  **Componente Envolvido:** `ScreenplayInteractive`.
3.  **Processo:**
    *   O editor é limpo.
    *   O estado interno do `ScreenplayInteractive` é resetado: `currentScreenplay` torna-se `null`, `isDirty` é `false`, `sourceOrigin` é definido como `'new'`.
    *   Agentes e estado do chat são limpos.
    *   **Resultado:** Um roteiro em branco é apresentado ao usuário, sem vínculo imediato com o banco de dados. O usuário precisará salvá-lo explicitamente para persistir.

#### Fluxo 2.1.2: "Novo Roteiro" (Com Agente Padrão)

1.  **Ação do Usuário:** Clica no botão "Novo Roteiro" (📄) que, internamente, pode acionar a criação com um agente padrão.
2.  **Componente Envolvido:** `ScreenplayInteractive`.
3.  **Processo:**
    *   `ScreenplayInteractive.newScreenplayWithDefaultAgent()` é chamado.
    *   `ScreenplayInteractive.createNewScreenplayImmediately()` é executado:
        *   Um novo roteiro é criado no MongoDB via `ScreenplayStorage.createScreenplay()` com um nome padrão (`novo-roteiro-YYYY-MM-DDTHH-MM-SS`) e conteúdo vazio.
        *   O `sourceOrigin` é definido como `'database'`, `currentScreenplay` é atualizado, e a URL é modificada para incluir o `screenplayId`.
        *   Um agente padrão é criado e vinculado ao roteiro.
    *   **Resultado:** Um novo roteiro é criado no banco de dados, carregado no editor, e um agente padrão é adicionado, pronto para uso.

#### Fluxo 2.1.3: Criação via Gerenciador de Roteiros

1.  **Ação do Usuário:** Abre o Gerenciador de Roteiros (📂), clica em "Criar Novo Roteiro", e insere um nome.
2.  **Componentes Envolvidos:** `ScreenplayManager`, `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayManager.createScreenplay()` é chamado.
    *   `ScreenplayStorage.createScreenplay()` é invocado para criar o roteiro no MongoDB com o nome fornecido.
    *   Se bem-sucedido, `ScreenplayManager` emite um evento `action: 'create'` contendo o novo `Screenplay`.
    *   `ScreenplayInteractive` recebe este evento e chama `loadScreenplayIntoEditor()` com o roteiro recém-criado, e cria um agente padrão.
    *   **Resultado:** O novo roteiro é criado no banco de dados e carregado no editor.

### 2.2. Carregamento de Roteiro

#### Fluxo 2.2.1: Do Banco de Dados (via Gerenciador de Roteiros)

1.  **Ação do Usuário:** Abre o Gerenciador de Roteiros (📂), seleciona um roteiro da lista e clica em "Abrir".
2.  **Componentes Envolvidos:** `ScreenplayManager`, `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayManager.openScreenplay()` é chamado.
    *   `ScreenplayStorage.getScreenplay(id)` é invocado para buscar o conteúdo completo do roteiro do MongoDB.
    *   `ScreenplayManager` emite um evento `action: 'open'` com o objeto `Screenplay` completo.
    *   `ScreenplayInteractive` recebe o evento e chama `loadScreenplayIntoEditor()`:
        *   Limpa agentes e estado do chat.
        *   Define `currentScreenplay`, `sourceOrigin = 'database'`, e atualiza a URL.
        *   Carrega o conteúdo do roteiro no editor.
        *   Carrega os agentes associados a este roteiro do MongoDB.
    *   **Resultado:** O roteiro selecionado é carregado do banco de dados e exibido no editor, com seus agentes correspondentes.

#### Fluxo 2.2.2: Via Parâmetro de URL

1.  **Ação do Usuário:** Acessa a aplicação com um `screenplayId` na URL (ex: `http://localhost:4200/?screenplayId=some-uuid`).
2.  **Componentes Envolvidos:** `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   No `ngOnInit` e `ngAfterViewInit` de `ScreenplayInteractive`, o `screenplayId` é lido do `ActivatedRoute`.
    *   `ScreenplayInteractive.loadScreenplayById(id)` é chamado.
    *   `ScreenplayStorage.getScreenplay(id)` busca o roteiro.
    *   `loadScreenplayIntoEditor()` é chamado (mesmo processo do Fluxo 2.2.1).
    *   **Resultado:** O roteiro especificado na URL é carregado do banco de dados.

### 2.3. Salvamento de Roteiro

#### Fluxo 2.3.1: Salvando Roteiro Existente no Banco

1.  **Ação do Usuário:** Faz alterações no roteiro (`isDirty` torna-se `true`), e clica em "Salvar" (💾) ou o auto-salvamento é acionado.
2.  **Componentes Envolvidos:** `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayInteractive.save()` é chamado.
    *   Como `sourceOrigin` é `'database'`, `ScreenplayInteractive.saveCurrentScreenplay()` é invocado.
    *   O conteúdo atual do editor é obtido via `generateMarkdownForSave()`.
    *   `ScreenplayStorage.updateScreenplay()` é chamado para atualizar o roteiro no MongoDB com o novo conteúdo.
    *   **Resultado:** As alterações são persistidas no banco de dados.

#### Fluxo 2.3.2: Primeiro Salvamento de um Novo Roteiro

1.  **Ação do Usuário:** Faz alterações em um roteiro recém-criado (sem vínculo com o banco, `sourceOrigin = 'new'`, `isDirty = true`), e clica em "Salvar" (💾).
2.  **Componentes Envolvidos:** `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayInteractive.save()` é chamado.
    *   Como `sourceOrigin` é `'new'`, `ScreenplayInteractive.promptCreateNewScreenplay()` é invocado.
    *   O usuário é solicitado a fornecer um nome para o roteiro.
    *   `ScreenplayInteractive.createNewScreenplayInDatabase()` é chamado, que por sua vez usa `ScreenplayStorage.createScreenplay()` para criar o roteiro no MongoDB.
    *   Se bem-sucedido, `sourceOrigin` é atualizado para `'database'`, `currentScreenplay` é definido, e a URL é atualizada.
    *   **Resultado:** O roteiro é salvo pela primeira vez no banco de dados e passa a ser um roteiro gerenciado pelo banco.

#### Fluxo 2.3.3: Auto-Salvamento

1.  **Ação do Sistema:** Após um período de inatividade do usuário e se `isDirty` for `true` e `sourceOrigin` for `'database'`.
2.  **Componente Envolvido:** `ScreenplayInteractive`.
3.  **Processo:**
    *   Um `setTimeout` (`autoSaveTimeout`) é acionado após 3 segundos de inatividade.
    *   `ScreenplayInteractive.save()` é chamado, seguindo o Fluxo 2.3.1.
    *   **Resultado:** As alterações são automaticamente salvas no banco de dados.

### 2.4. Importação de Roteiro do Disco

#### Fluxo 2.4.1: Via Botão "Importar do Disco..." (com Detecção de Conflitos)

1.  **Ação do Usuário:** Clica no botão "Importar do Disco..." (📥) na barra de ferramentas.
2.  **Componentes Envolvidos:** `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayInteractive.importFromDisk()` aciona a abertura de um seletor de arquivos.
    *   `ScreenplayInteractive.handleFileSelect()` lê o conteúdo do arquivo selecionado.
    *   **Detecção de Conflitos:**
        *   O sistema busca roteiros existentes no MongoDB com o mesmo nome (derivado do nome do arquivo).
        *   **Cenário A: Nome e Conteúdo Idênticos:** Se um roteiro com o mesmo nome e conteúdo exato já existe no banco, o roteiro existente é carregado (`loadScreenplayIntoEditor()`).
        *   **Cenário B: Nome Idêntico, Conteúdo Diferente:** O usuário é alertado sobre o conflito e tem a opção de:
            *   **Sobrescrever:** O conteúdo do arquivo do disco substitui o conteúdo do roteiro no banco de dados (`screenplayStorage.updateScreenplay()`).
            *   **Manter Banco:** O roteiro existente no banco é carregado, e o conteúdo do disco é descartado.
        *   **Cenário C: Sem Conflito de Nome:** `ScreenplayInteractive.createAndLinkScreenplayAutomatically()` é chamado.
            *   Tenta criar um novo roteiro no MongoDB via `screenplayStorage.createScreenplay()`.
            *   Se houver um erro de nome duplicado (ex: devido a sanitização ou corrida), tenta criar com um nome único (`nome-do-arquivo-timestamp`).
            *   O roteiro (novo ou atualizado) é carregado no editor.
    *   **Resultado:** O conteúdo do arquivo do disco é carregado no editor e, dependendo da existência e do conteúdo de roteiros com o mesmo nome no banco de dados, é criado um novo roteiro, um existente é atualizado ou um existente é carregado.

#### Fluxo 2.4.2: Via Gerenciador de Roteiros (Criação Direta)

1.  **Ação do Usuário:** Abre o Gerenciador de Roteiros (📂), clica em "Importar do Disco" (📥).
2.  **Componentes Envolvidos:** `ScreenplayManager`, `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayManager.importFromDisk()` aciona a abertura de um seletor de arquivos.
    *   `ScreenplayManager.readFileAndImport()` lê o conteúdo do arquivo.
    *   **Criação Direta:** `ScreenplayStorage.createScreenplay()` é chamado diretamente com o nome do arquivo (sem extensão) e seu conteúdo.
    *   Se a criação for bem-sucedida, `ScreenplayManager` adiciona o novo roteiro à sua lista e emite um evento `action: 'import'`.
    *   `ScreenplayInteractive` recebe o evento e chama `loadScreenplayIntoEditor()`.
    *   **Resultado:** O roteiro é criado no banco de dados e carregado no editor. **Observação:** Este fluxo não possui a detecção de conflitos avançada do `ScreenplayInteractive`. Se um roteiro com o mesmo nome já existir no banco, a criação falhará, e o `ScreenplayInteractive` carregará o conteúdo do disco como um novo roteiro não salvo.

### 2.5. Exportação de Roteiro para Disco

#### Fluxo 2.5.1: Via Botão "Exportar para Disco..." (com Modal de Nome)

1.  **Ação do Usuário:** Clica no botão "Exportar para Disco..." (📤) na barra de ferramentas.
2.  **Componentes Envolvidos:** `ScreenplayInteractive`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayInteractive.openExportModal()` exibe um modal onde o usuário pode inserir um nome de arquivo. O nome sugerido é o `currentScreenplay.name` (se existir) ou `roteiro-vivo`.
    *   Após o usuário confirmar, `ScreenplayInteractive.confirmExport()` é chamado.
    *   O conteúdo atual do editor (`generateMarkdownForSave()`) é salvo.
    *   **API de Acesso ao Sistema de Arquivos:** Se o navegador suportar (`window.showSaveFilePicker`), o usuário é solicitado a escolher um local e nome de arquivo.
    *   **Fallback:** Caso contrário, um download tradicional do arquivo é iniciado.
    *   O `filePath` do `currentScreenplay` no banco de dados é atualizado via `screenplayStorage.updateScreenplay()` para registrar o local de exportação.
    *   **Resultado:** O conteúdo do roteiro é salvo no disco local do usuário com o nome especificado.

#### Fluxo 2.5.2: Via Gerenciador de Roteiros (Exportação Direta)

1.  **Ação do Usuário:** Abre o Gerenciador de Roteiros (📂), seleciona um roteiro e clica em "Exportar para Disco" (📤).
2.  **Componentes Envolvidos:** `ScreenplayManager`, `ScreenplayStorage`.
3.  **Processo:**
    *   `ScreenplayManager.exportToDisk()` é chamado.
    *   `ScreenplayStorage.getScreenplay()` busca o conteúdo completo do roteiro.
    *   `ScreenplayManager.exportScreenplayToDisk()` é chamado.
    *   **API de Acesso ao Sistema de Arquivos:** Se disponível, o usuário escolhe o local e o nome do arquivo (sugerindo `screenplay.filePath` ou `screenplay.name.md`).
    *   **Fallback:** Caso contrário, um download tradicional é iniciado.
    *   O `filePath` do roteiro no banco de dados é atualizado via `screenplayStorage.updateScreenplay()`.
    *   **Resultado:** O roteiro selecionado é salvo no disco local do usuário.

## 3. Gerenciamento de Nomes

A questão dos nomes dos roteiros é tratada com inteligência em todo o sistema:

*   **Nome do Roteiro no Banco de Dados:** O campo `name` do objeto `Screenplay` é o identificador principal legível por humanos no MongoDB.
*   **Sugestão ao Salvar:** Ao salvar um novo roteiro pela primeira vez, o sistema sugere um nome padrão (`novo-roteiro-timestamp`). O usuário pode alterá-lo.
*   **Sugestão ao Exportar:** Ao exportar para o disco, o nome do roteiro (`currentScreenplay.name`) é sempre sugerido como o nome do arquivo.
*   **Carregamento Inteligente:**
    *   Ao importar do disco, o nome do arquivo é usado para verificar a existência de roteiros com o mesmo nome no banco de dados.
    *   Se um roteiro com o mesmo nome já existe, o sistema verifica se o conteúdo é idêntico.
    *   Se o conteúdo for idêntico, o roteiro existente é carregado.
    *   Se o conteúdo for diferente, o usuário é questionado se deseja sobrescrever o roteiro no banco ou carregar o arquivo do disco como um novo roteiro.
    *   Se não houver conflito de nome, o roteiro é criado no banco com o nome do arquivo.
    *   Em caso de falha na criação devido a nome duplicado (mesmo após a verificação inicial), o sistema tenta criar um nome único adicionando um timestamp.
*   **`filePath` para Referência:** O `filePath` é armazenado no banco de dados para manter uma referência ao último local de disco onde o roteiro foi salvo ou de onde foi importado, facilitando futuras operações de exportação.

## 4. Considerações Importantes

*   **Detecção de Conflitos:** A detecção de conflitos durante a importação do disco é mais robusta quando iniciada diretamente pelo `ScreenplayInteractive` (botão na barra de ferramentas) do que pelo `ScreenplayManager`. O `ScreenplayManager` tenta uma criação direta, e o `ScreenplayInteractive` lida com o fallback se a criação falhar.
*   **Soft Delete:** A exclusão de roteiros é uma "soft delete", ou seja, o roteiro é marcado como `isDeleted = true` no banco de dados, mas não é removido fisicamente.
*   **Sincronização de Agentes:** A sincronização de agentes entre o conteúdo Markdown e as instâncias de agentes no MongoDB é um processo contínuo, garantindo que os agentes visíveis no editor correspondam aos dados persistidos.
*   **UI/UX:** Atualmente, alguns prompts de usuário (como detecção de conflitos) são implementados com `window.confirm` ou `window.prompt`, com planos futuros para substituí-los por componentes modais mais amigáveis.
