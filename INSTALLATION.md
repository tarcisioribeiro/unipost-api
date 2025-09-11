# Guia de Instalação Completo - UniPost API

Guia passo a passo para instalação e configuração do UniPost API com todos os recursos de **inteligência artificial** e **busca semântica**.

## 📋 Visão Geral do Sistema

O UniPost API é composto por:

- **🔗 API REST**: Django + DRF para gerenciamento de conteúdo
- **🤖 Sistema de IA**: Vetorização automática com Google Gemini
- **🌐 Web Scraping**: Coleta inteligente usando MCP SDK
- **🧠 Business Brain**: Sincronização com ElasticSearch corporativo
- **📊 Banco Vetorizado**: PostgreSQL + pgvector para busca semântica

## 🎯 Opções de Instalação

### 🐳 Opção 1: Docker (Recomendado)
- **Melhor para**: Produção, desenvolvimento rápido
- **Vantagens**: Configuração automática, isolamento completo
- **Tempo**: ~10 minutos

### 💻 Opção 2: Instalação Local
- **Melhor para**: Desenvolvimento avançado, customização
- **Vantagens**: Controle total, debugging facilitado  
- **Tempo**: ~30 minutos

---

## 🐳 INSTALAÇÃO COM DOCKER

### Pré-requisitos

- **Docker**: 20.10+ ([Instalar Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ ([Instalar Compose](https://docs.docker.com/compose/install/))
- **Git**: Para clonar repositório

### 1. Clone o Projeto

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd unipost-api

# Verifique a estrutura
ls -la
```

### 2. Configure Variáveis de Ambiente

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env
nano .env
```

**Configuração mínima no `.env`:**

```env
# Database (obrigatório)
DB_HOST=db
DB_PORT=5432
DB_USER=unipost_user
DB_PASSWORD=crie_uma_senha_forte_aqui
DB_NAME=unipost

# Django Admin (obrigatório)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@suaempresa.com
DJANGO_SUPERUSER_PASSWORD=crie_uma_senha_admin_forte

# Django Secret Key (obrigatório - gere uma nova)
SECRET_KEY=gere_uma_chave_secreta_de_50_caracteres_aqui

# 🤖 Google Gemini API (obrigatório para IA)
GOOGLE_GEMINI_API_KEY=sua_chave_google_gemini

# 🔍 ElasticSearch (opcional - apenas para Business Brain)
ELASTICSEARCH_HOST=seu_elasticsearch_host
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=seu_usuario_elasticsearch
ELASTICSEARCH_PASSWORD=sua_senha_elasticsearch
ELASTICSEARCH_USE_SSL=false
ELASTICSEARCH_VERIFY_CERTS=false

# Logging
LOG_FORMAT=json
```

### 3. Obtenha a Google Gemini API Key

1. **Acesse**: [Google AI Studio](https://aistudio.google.com/)
2. **Login**: Faça login com sua conta Google
3. **API Key**: Clique em "Get API key" → "Create API key in new project"
4. **Copie**: A chave gerada e cole no `.env`

### 4. Gere Django Secret Key

```bash
# Gere uma chave secreta forte
python3 -c "
import secrets
import string
alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
print('SECRET_KEY=' + ''.join(secrets.choice(alphabet) for i in range(50)))
"
```

### 5. Execute o Sistema

```bash
# Construa e inicie os serviços
docker-compose up -d --build

# Verifique se os serviços estão rodando
docker-compose ps

# Expected output:
# NAME       SERVICE   STATUS    PORTS
# app        app       running   0.0.0.0:8005->8005/tcp
# db         db        running   0.0.0.0:5437->5432/tcp
```

### 6. Configure o Banco de Dados

```bash
# Execute migrações (cria todas as tabelas incluindo embeddings)
docker-compose exec app python manage.py migrate

# Verifique se pgvector foi instalado
docker-compose exec db psql -U unipost_user -d unipost -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Deve retornar: vector | 0.8.0 | public | vector data type and ivfflat access method
```

### 7. Crie Usuário Administrador

```bash
# Se não foi criado automaticamente pelo DJANGO_SUPERUSER_*
docker-compose exec app python manage.py createsuperuser

# Ou force criar com as variáveis do .env
docker-compose exec app python createsuperuser.py
```

### 8. Teste a API

```bash
# Teste endpoint de saúde
curl http://localhost:8005/health/

# Teste admin interface
open http://localhost:8005/admin/

# Teste API base
curl http://localhost:8005/api/v1/

# Teste login
curl -X POST http://localhost:8005/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua_senha"}'
```

### 9. Configure Automações de IA (Opcional)

```bash
# Configure Business Brain para executar a cada 10 minutos
docker-compose exec app ./brain/crontab_setup.sh

# Verifique se crontab foi configurado
docker-compose exec app crontab -l
```

### ✅ Instalação Docker Completa!

**URLs principais:**
- **API**: http://localhost:8005/api/v1/
- **Admin**: http://localhost:8005/admin/
- **PostgreSQL**: localhost:5437

**Próximos passos:**
- [Teste a API](#teste-da-api)
- [Configure sites para web scraping](#configuração-inicial)
- [Execute scripts de IA](#scripts-de-ia)

---

## 💻 INSTALAÇÃO LOCAL

### Pré-requisitos

- **Python 3.13+**: [Instalar Python](https://python.org/downloads/)
- **PostgreSQL 16+**: [Instalar PostgreSQL](https://postgresql.org/download/)
- **pgvector**: Extensão para vetores
- **Node.js 18+**: Para MCP SDK ([Instalar Node](https://nodejs.org/))

### 1. Configure PostgreSQL + pgvector

#### Ubuntu/Debian:
```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-client

# Instalar pgvector
sudo apt install postgresql-16-pgvector

# Configurar usuário
sudo -u postgres createuser --interactive --pwprompt unipost_user
sudo -u postgres createdb -O unipost_user unipost

# Ativar extensão pgvector
sudo -u postgres psql -d unipost -c "CREATE EXTENSION vector;"
```

#### macOS:
```bash
# Instalar com Homebrew
brew install postgresql@16
brew install pgvector

# Iniciar PostgreSQL
brew services start postgresql@16

# Criar usuário e banco
createuser --interactive --pwprompt unipost_user
createdb -O unipost_user unipost
psql -d unipost -c "CREATE EXTENSION vector;"
```

#### Windows:
1. Baixe [PostgreSQL Windows](https://www.postgresql.org/download/windows/)
2. Compile [pgvector do source](https://github.com/pgvector/pgvector#installation)
3. Configure conforme documentação oficial

### 2. Clone e Configure Python

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd unipost-api

# Crie ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale dependências
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Variáveis de Ambiente

```bash
cp .env.example .env
```

**Configure `.env` para instalação local:**

```env
# Database (local)
DB_HOST=localhost
DB_PORT=5432
DB_USER=unipost_user
DB_PASSWORD=senha_que_voce_criou
DB_NAME=unipost

# Django
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@suaempresa.com
DJANGO_SUPERUSER_PASSWORD=senha_admin_forte
SECRET_KEY=gere_uma_chave_secreta_forte

# IA (obrigatório)
GOOGLE_GEMINI_API_KEY=sua_chave_google_gemini

# ElasticSearch (opcional)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Logging
LOG_FORMAT=json
```

### 4. Configure Banco e Execute Migrações

```bash
# Teste conexão com banco
python manage.py dbshell

# Execute migrações
python manage.py migrate

# Crie superusuário
python manage.py createsuperuser

# Colete arquivos estáticos
python manage.py collectstatic --noinput
```

### 5. Instale Dependências Node.js (Para MCP)

```bash
# Instalar npx globalmente (se não tiver)
npm install -g npx

# Testar MCP SDK
npx --yes @modelcontextprotocol/server-web-search@latest --version
```

### 6. Execute a API

```bash
# Inicie servidor de desenvolvimento
python manage.py runserver 8005

# Em outro terminal, configure crontab (opcional)
./brain/crontab_setup.sh
```

### ✅ Instalação Local Completa!

---

## 🧪 TESTE DA API

### 1. Teste Básico da API

```bash
# Health check
curl http://localhost:8005/health/

# Endpoint base
curl http://localhost:8005/api/v1/
```

### 2. Teste Autenticação

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8005/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua_senha"}' \
  | jq -r '.access')

echo "Token: $TOKEN"

# Teste endpoint protegido
curl -H "Authorization: Bearer $TOKEN" http://localhost:8005/api/v1/texts/
```

### 3. Teste Sistema de IA

```bash
# Criar um post (deve gerar embedding automaticamente)
curl -X POST http://localhost:8005/api/v1/texts/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "Teste de IA",
    "platform": "FCB", 
    "content": "Este é um teste do sistema de vetorização automática com Google Gemini",
    "is_approved": true
  }'

# Verificar se embedding foi criado
curl -H "Authorization: Bearer $TOKEN" http://localhost:8005/api/v1/embeddings/
```

### 4. Teste Web Scraping

```bash
# Criar site de referência
curl -X POST http://localhost:8005/api/v1/sites/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TechCrunch",
    "url": "https://techcrunch.com",
    "category": "NOTICIAS"
  }'

# Executar web scraping
python scraping/webscraper.py

# Vetorizar dados coletados
python scraping/text_vectorizer.py
```

---

## ⚙️ CONFIGURAÇÃO INICIAL

### 1. Admin Interface

1. **Acesse**: http://localhost:8005/admin/
2. **Login**: com credenciais do superusuário
3. **Explore**: Modelos Text, Site, Embedding

### 2. Cadastre Sites para Web Scraping

```bash
# Via Admin ou API
curl -X POST http://localhost:8005/api/v1/sites/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Blog", 
    "url": "https://github.blog",
    "category": "BLOG"
  }'
```

### 3. Configure ElasticSearch (Opcional)

Se você tem ElasticSearch corporativo:

```bash
# Teste conectividade
curl -X GET "seu_elasticsearch_host:9200/_cluster/health"

# Configure credenciais no .env
ELASTICSEARCH_HOST=seu_host
ELASTICSEARCH_USERNAME=usuario
ELASTICSEARCH_PASSWORD=senha

# Teste Business Brain
python brain/business_vectorizer.py
```

---

## 🤖 SCRIPTS DE IA

### Web Scraping + Vetorização

```bash
# Fluxo completo
python scraping/webscraper.py && python scraping/text_vectorizer.py

# Ou separadamente
python scraping/webscraper.py      # Coleta dados
python scraping/text_vectorizer.py # Vetoriza e salva
```

### Business Brain

```bash
# Execução manual
python brain/business_vectorizer.py

# Automação (executa a cada 10 minutos)
./brain/crontab_setup.sh
```

### Monitoramento

```bash
# Logs em tempo real
tail -f scraping/*.log brain/*.log logs/*.log

# Verificar embeddings no banco
python manage.py shell
>>> from embeddings.models import Embedding
>>> Embedding.objects.values('origin').annotate(count=Count('id'))
```

---

## 🔍 VERIFICAÇÃO E VALIDAÇÃO

### Checklist de Instalação

- [ ] **API responde**: `curl http://localhost:8005/health/`
- [ ] **Admin acessa**: http://localhost:8005/admin/
- [ ] **PostgreSQL conecta**: `python manage.py dbshell`
- [ ] **pgvector ativo**: Extensão instalada no banco
- [ ] **Google Gemini funciona**: API Key válida
- [ ] **Embeddings automáticos**: Criar post gera vetor
- [ ] **Web scraping funciona**: Scripts executam sem erro
- [ ] **Logs são gerados**: Arquivos de log criados

### Comandos de Verificação

```bash
# Status geral
docker-compose ps  # ou python manage.py check

# Banco de dados
python manage.py dbshell
\dt  # Listar tabelas
\dx  # Listar extensões (deve mostrar pgvector)

# APIs externas
python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
print('Google Gemini: OK')
"

# Elasticsearch (se configurado)
curl -X GET "$ELASTICSEARCH_HOST:$ELASTICSEARCH_PORT/_cluster/health"
```

---

## 🐛 SOLUÇÃO DE PROBLEMAS

### Problemas Comuns

#### 1. **API não inicia**

```bash
# Verificar logs
docker-compose logs app  # Docker
# ou
python manage.py runserver --traceback  # Local

# Verificar dependências
pip list | grep -E "(django|rest|google)"
```

#### 2. **pgvector não encontrado**

```bash
# Verificar extensão
psql -d unipost -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Se falhar, reinstalar pgvector
sudo apt install postgresql-16-pgvector  # Ubuntu
brew install pgvector  # macOS
```

#### 3. **Google Gemini API não funciona**

```bash
# Verificar chave
echo $GOOGLE_GEMINI_API_KEY

# Testar API
python -c "
import google.generativeai as genai
genai.configure(api_key='$GOOGLE_GEMINI_API_KEY')
result = genai.embed_content(model='models/embedding-001', content='teste')
print('API funcionando!')
"
```

#### 4. **Embeddings não são criados automaticamente**

```bash
# Verificar signals Django
python manage.py shell
>>> from texts.models import Text
>>> Text.objects.create(theme="Teste", platform="FCB", content="Teste automático")
>>> # Verificar logs para erros
```

#### 5. **Web scraping falha**

```bash
# Verificar MCP SDK
npx --yes @modelcontextprotocol/server-web-search@latest --version

# Verificar credenciais da API
python scraping/webscraper.py  # Ver logs de erro
```

### Logs de Debug

```bash
# Ativar debug máximo
export DJANGO_LOG_LEVEL=DEBUG
export DJANGO_DEBUG=True

# Ver todos os logs
find . -name "*.log" -exec tail -f {} +
```

---

## 🚀 PRÓXIMOS PASSOS

### 1. Configuração Avançada
- Configurar HTTPS/SSL
- Setup de cache (Redis)
- Backup automatizado
- Monitoramento (Prometheus/Grafana)

### 2. Desenvolvimento
- Implementar busca semântica
- APIs de recomendação
- Dashboard de analytics
- Testes automatizados

### 3. Produção
- Deploy com Docker Swarm/Kubernetes
- Load balancing
- CDN para arquivos estáticos
- Monitoring e alertas

---

**✅ Instalação Completa - UniPost API com IA pronto para uso! 🤖**