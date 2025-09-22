# Instruções para ClaudeCode – Projeto Unipost Automação

Este documento contém instruções específicas para você, ClaudeCode, sobre como proceder no desenvolvimento do **fluxo automatizado de coleta, preparação e postagem de conteúdo** para o Unipost.  

O objetivo é estruturar o projeto em um **diretório próprio**, reaproveitando partes do código existente quando possível, e gerar uma **documentação clara de configuração e uso**.

---

## 📌 Tarefas principais

1. **Analisar o código atual**
   - Revise a estrutura existente do projeto:
     ```
     ├── app
     ├── authentication
     ├── backups
     ├── brain
     ├── docs
     ├── embeddings
     ├── logs
     ├── media
     ├── references
     ├── scraping
     ├── sites
     ├── static
     ├── staticfiles
     └── texts
     ```
   - Identifique o que pode ser **reutilizado** no novo fluxo (ex.: módulos de scraping, embeddings, API Django).
   - Verifique se já existem funções utilitárias que podem ser adaptadas (armazenamento no PostgreSQL, chamadas à API, etc.).

2. **Criar novo diretório para o projeto**
   - Nome sugerido: `unipost_automation`
   - Estrutura inicial esperada:
     ```
     unipost_automation
     ├── README.md
     ├── docs
     │   └── setup.md
     ├── src
     │   ├── bot
     │   │   └── async_bot.py
     │   ├── scraping
     │   │   └── webscraper.py
     │   ├── formatting
     │   │   └── text_formatter.py
     │   ├── posting
     │   │   └── wordpress_client.py
     │   └── storage
     │       ├── db.py
     │       └── vector_store.py
     └── tests
         └── test_basic.py
     ```

3. **Funcionalidades a implementar**
   - **Robô Assíncrono**: roda a cada 5 min, checa URLs de busca, detecta novos posts.
   - **Webscraping (MCP)**: coleta HTML, CSS e JS do site base.
   - **TextFormatter**: separa e normaliza conteúdo para postagem.
   - **Integração com PGVector**: gera embeddings e armazena no PostgreSQL.
   - **Integração com WordPress**: posta o conteúdo automaticamente via API REST.
   - **API Django** (reutilizar se possível): media a comunicação entre componentes.

4. **Documentação clara**
   - Criar em `docs/setup.md` um guia com:
     - **Pré-requisitos** (Python, PostgreSQL, PGVector, WordPress API).
     - **Instalação e configuração** (dependências, env vars, conexões DB e WP).
     - **Execução** (como rodar o robô, como disparar scraping manualmente).
     - **Fluxo de dados** (do scraping → processamento → embeddings → postagem).
     - **Boas práticas** (evitar duplicação de posts, logs, tratamento de erros).

5. **Critérios de qualidade**
   - Código modular e reutilizável.
   - Testes básicos automatizados (ex.: checar se o robô detecta URLs novas).
   - Logs adequados para debug.
   - Respeitar a estrutura de pacotes Python.
   - Documentação clara e atualizada.

---

## 🔹 Resultado esperado
- Um novo diretório `unipost_automation` no repositório.  
- Código funcional do fluxo descrito.  
- Documentação completa em `docs/setup.md` e `README.md`.  
- Uso de partes do código existente quando fizer sentido.  

---
