# Saga-005: Implementação do Portfólio Interativo com Assistente de IA

**Visão Estratégica:** Construir um portfólio web interativo que atue como uma ferramenta de marketing pessoal, apresentando projetos e um currículo através de um assistente de IA. A implementação deve garantir a segurança da infraestrutura backend existente, seguindo as melhores práticas de arquitetura de sistemas.

---

## Fase 1: Fortalecimento da Segurança no Gateway (Hardening)

**Objetivo:** "Blindar" o `conductor-gateway` para proteger o backend contra abusos e acessos não autorizados antes de expor qualquer funcionalidade publicamente.

*   **Passo 1.1: Implementar Rate Limiting**
    *   **Projeto:** `conductor-gateway`
    *   **Arquivo:** `src/main.py` (ou onde a instância do FastAPI é criada).
    *   **Ação:** Adicionar a biblioteca `slowapi` para limitar as requisições no novo endpoint do chat a um nível razoável (ex: 20 requisições por minuto por IP).

*   **Passo 1.2: Implementar CORS**
    *   **Projeto:** `conductor-gateway`
    *   **Arquivo:** `src/main.py`.
    *   **Ação:** Configurar o middleware CORS para permitir requisições apenas do futuro domínio do portfólio (usar um placeholder como `https://<YOUR-DOMAIN>.com`) e `http://localhost:4321` (porta padrão do Astro para desenvolvimento).

*   **Passo 1.3: Criar Endpoint de Chat (Placeholder)**
    *   **Projeto:** `conductor-gateway`
    *   **Ação:** Criar um novo arquivo de rota, ex: `src/api/v1/portfolio.py`.
    *   **Detalhes:** Definir um endpoint `POST /api/v1/portfolio-chat` que recebe uma mensagem, realiza uma validação básica (Pydantic model) e retorna uma resposta mockada, como `{"response": "Endpoint funcionando"}`.

*   **Validação da Fase:**
    *   Verificar se o `slowapi` bloqueia requisições após o limite.
    *   Testar se requisições de domínios não autorizados são bloqueadas pelo CORS.
    *   Confirmar com `curl` que o novo endpoint está acessível e retorna a resposta mockada.

---

## Fase 2: Isolamento de Rede via Docker

**Objetivo:** Garantir que o serviço `conductor` e o banco de dados `mongodb` estejam completamente inacessíveis pela internet, usando redes Docker distintas.

*   **Passo 2.1: Definir Novas Redes**
    *   **Projeto:** `conductor-community` (raiz)
    *   **Arquivo:** `docker-compose.dev.yml`
    *   **Ação:** Definir duas novas redes no final do arquivo: `public-net` e `private-net`.

*   **Passo 2.2: Atribuir Serviços às Redes**
    *   **Arquivo:** `docker-compose.dev.yml`
    *   **Ação:**
        *   `conductor-gateway`: Conectar a `public-net` e `private-net`.
        *   `conductor-web`: Conectar apenas a `public-net`.
        *   `conductor-api` (`conductor`): Conectar **apenas** a `private-net`.
        *   `mongodb`: Conectar **apenas** a `private-net`.
    *   **Importante:** Atualizar as URLs de conexão nos arquivos de configuração (`.env` ou `config.yaml`) para usar os nomes dos serviços, que funcionarão como DNS dentro da rede Docker.

*   **Validação da Fase:**
    *   Confirmar que a aplicação web (`conductor-web`) ainda consegue se comunicar com o `gateway`.
    *   Confirmar que o `gateway` ainda consegue se comunicar com o `conductor-api`.
    *   Tentar acessar o `conductor-api` diretamente da máquina host (ex: `curl http://localhost:3000`) e verificar que a conexão é recusada.

---

## Fase 3: Criação do Agente de IA e Conexão do Endpoint

**Objetivo:** Criar o agente de IA que responderá às perguntas e conectar o endpoint do gateway a ele.

*   **Passo 3.1: Criar Definição do Agente**
    *   **Projeto:** `conductor`
    *   **Diretório:** `src/conductor/agents/` (ou diretório correspondente).
    *   **Ação:** Criar um arquivo `portfolio_assistant_agent.yaml` (ou o formato de definição de agente do projeto).
    *   **Conteúdo:** Definir o agente `PortfolioAssistant_Agent` e inserir um prompt de sistema detalhado com informações do currículo e projetos (usar placeholders por enquanto).

*   **Passo 3.2: Conectar Gateway ao Agente**
    *   **Projeto:** `conductor-gateway`
    *   **Arquivo:** `src/api/v1/portfolio.py`.
    *   **Ação:** Modificar o endpoint `POST /api/v1/portfolio-chat` para, em vez de retornar uma resposta mockada, chamar o serviço `conductor-api`, especificando a execução do `PortfolioAssistant_Agent` com a mensagem do usuário.

*   **Validação da Fase:**
    *   Reiniciar a stack de desenvolvimento.
    *   Enviar uma requisição via `curl` para `http://localhost:5006/api/v1/portfolio-chat`.
    *   Verificar se a resposta é gerada pela IA, com base no prompt do agente.

---

## Fase 4: Estabelecimento do Projeto de Portfólio a partir do Chat Existente

**Objetivo:** Isolar o projeto de chat existente (`src/conductor-web/chat`) em seu próprio submódulo (`src/portfolio-web`) e adaptá-lo para servir como a base do novo site de portfólio, acelerando o desenvolvimento.

*   **Passo 4.1: Mover e Desacoplar o Projeto de Chat**
    *   **Ação 1:** Mover o diretório `src/conductor-web/chat` para `src/portfolio-web`.
    *   **Ação 2:** No submódulo `conductor-web`, fazer o commit da remoção do diretório `chat` para registrar a mudança.

*   **Passo 4.2: Criar o Novo Submódulo `portfolio-web`**
    *   **Ação 1:** Criar um novo repositório vazio no GitHub (ex: `portfolio-web`).
    *   **Ação 2:** No diretório local `src/portfolio-web`, inicializar um repositório git, adicionar o novo repositório do GitHub como `origin`, e fazer o push do código movido. (`git init && git remote add origin <URL> && git add . && git commit -m "Initial commit from existing chat project" && git push -u origin main`).
    *   **Ação 3:** No repositório raiz `conductor-community`, remover o diretório `src/portfolio-web` (que agora é um repositório git comum) e registrá-lo como um submódulo oficial: `rm -rf src/portfolio-web && git submodule add <URL> src/portfolio-web`.

*   **Passo 4.3: Adaptar o Projeto para um Portfólio**
    *   **Projeto:** `portfolio-web`
    *   **Ação 1:** Adicionar um sistema de rotas (ex: `react-router-dom`) para permitir múltiplas páginas.
    *   **Ação 2:** Criar componentes de página básicos para "Home", "Sobre Mim", "Projetos". O componente de chat existente pode ser integrado na página "Home" ou em uma página dedicada.
    *   **Ação 3:** Atualizar o `package.json`, `vite.config.ts` e `README.md` do `portfolio-web` para refletir seu novo propósito e nome.

*   **Validação da Fase:**
    *   O submódulo `conductor-web` não contém mais o diretório `chat`.
    *   O diretório `src/portfolio-web` é um submódulo git funcional e independente.
    *   O projeto `portfolio-web` roda localmente (`npm run dev`) e exibe as novas páginas de portfólio.

---

## Fase 5: Integração Frontend-Backend

**Objetivo:** Conectar o chat do novo `portfolio-web` ao endpoint seguro do `PortfolioAssistant_Agent`.

*   **Passo 5.1: Ajustar a Lógica de API no Chat**
    *   **Projeto:** `portfolio-web`
    *   **Arquivo:** `src/services/conductorApi.ts` (ou similar).
    *   **Ação:** Revisar e garantir que a lógica de `fetch` existente aponte para o endpoint correto (`/api/v1/portfolio-chat`) e que o payload enviado esteja alinhado com o que o backend espera. A configuração de proxy no `vite.config.ts` deve ser mantida para o desenvolvimento local.

*   **Validação da Fase:**
    *   Realizar um teste ponta-a-ponta:
        1.  Abrir o site do portfólio no navegador.
        2.  Digitar uma pergunta no chat.
        3.  Confirmar que a resposta do `PortfolioAssistant_Agent` é exibida corretamente na tela.
