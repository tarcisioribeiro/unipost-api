# UniPost API

Uma API RESTful desenvolvida em Django para gerenciamento de textos para redes sociais com sistema avançado de **inteligência artificial e busca semântica**. A API permite criar, listar, visualizar, editar e deletar textos para diferentes plataformas sociais com autenticação JWT, além de **vetorização automática de conteúdo**, **web scraping** e **sincronização com ElasticSearch**.

## 🤖 Funcionalidades de IA e Busca Semântica

- **Vetorização Automática**: Embeddings gerados automaticamente com Google Gemini para todos os textos
- **Web Scraping Inteligente**: Coleta automática de conteúdo de sites de referência usando MCP SDK
- **Business Brain**: Sincronização e vetorização de dados corporativos do ElasticSearch
- **Busca Semântica**: Sistema de busca baseado em similaridade de vetores
- **Banco Vetorizado**: PostgreSQL com extensão pgvector para armazenamento de embeddings

## 📋 Funcionalidades Principais

- **Autenticação JWT**: Login, logout, refresh e verificação de tokens
- **Gerenciamento de Textos**: CRUD completo para textos de redes sociais
- **Gerenciamento de Sites**: CRUD para sites de referência para web scraping
- **Sistema de Embeddings**: Armazenamento e gerenciamento de vetores de IA
- **Suporte a Múltiplas Plataformas**: Facebook, Instagram, TikTok, LinkedIn
- **Sistema de Permissões**: Controle de acesso baseado em permissões Django
- **Aprovação de Conteúdo**: Sistema de aprovação para textos criados
- **API RESTful**: Endpoints padronizados seguindo convenções REST

## 🛠️ Tecnologias Utilizadas

### Backend & API
- **Django 5.2.6**: Framework web principal
- **Django REST Framework**: Para construção da API REST
- **Simple JWT**: Autenticação via JSON Web Tokens
- **PostgreSQL + pgvector**: Banco de dados com suporte a vetores

### Inteligência Artificial
- **Google Gemini**: Modelo de embedding (`embedding-001`) para vetorização
- **MCP SDK Python**: Protocolo para web scraping inteligente
- **ElasticSearch**: Integração para dados corporativos

### Infraestrutura
- **Docker & Docker Compose**: Containerização e orquestração
- **Crontab**: Automação de tarefas periódicas
- **Python 3.13**: Linguagem de programação

## 📁 Estrutura do Projeto

```
unipost-api/
├── app/                    # Configurações principais do Django
│   ├── settings.py         # Configurações do projeto
│   ├── urls.py            # URLs principais
│   └── permissions.py     # Permissões customizadas
├── authentication/         # App de autenticação
│   ├── views.py           # Views de autenticação
│   └── urls.py            # URLs de autenticação
├── texts/                  # App de gerenciamento de textos
│   ├── models.py          # Modelo Text
│   ├── serializers.py     # Serializers DRF
│   ├── views.py           # Views CRUD
│   ├── signals.py         # ✨ Signals para vetorização automática
│   └── urls.py            # URLs de textos
├── sites/                  # App de gerenciamento de sites
│   ├── models.py          # Modelo Site para web scraping
│   ├── serializers.py     # Serializers DRF
│   ├── views.py           # Views CRUD
│   └── urls.py            # URLs de sites
├── embeddings/             # ✨ App de sistema de vetores/IA
│   ├── models.py          # Modelo Embedding
│   ├── serializers.py     # Serializers DRF
│   ├── views.py           # Views CRUD
│   ├── admin.py           # Admin interface
│   └── urls.py            # URLs de embeddings
├── scraping/               # ✨ Scripts de web scraping
│   ├── webscraper.py      # Web scraping com MCP SDK
│   ├── text_vectorizer.py # Vetorização de dados coletados
│   └── README.md          # Documentação do web scraping
├── brain/                  # ✨ Scripts de Business Brain
│   ├── business_vectorizer.py    # Sincronização com ElasticSearch
│   ├── crontab_setup.sh   # Configuração automática do crontab
│   └── README.md          # Documentação do Business Brain
├── docker-compose.yml      # Configuração Docker Compose
├── init-db.sql            # ✨ Inicialização PostgreSQL com pgvector
├── Dockerfile             # Imagem Docker da aplicação
├── requirements.txt       # Dependências Python (inclui IA)
└── manage.py             # Utilitário de gerenciamento Django
```

## 🚀 Como Executar a API

### Pré-requisitos

- Docker
- Docker Compose
- Git
- Chave da API Google Gemini (gratuita)

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd unipost-api
```

### 2. Configure as variáveis de ambiente

Copie o arquivo de exemplo e preencha as variáveis:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
# Database
DB_HOST=db
DB_PORT=5432
DB_USER=seu_usuario_db
DB_PASSWORD=sua_senha_db
DB_NAME=unipost

# Django Superuser
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=sua_senha_admin

# Django Secret Key (gere uma nova)
SECRET_KEY=sua_secret_key_aqui

# Chave de criptografia (opcional)
ENCRYPTION_KEY=sua_chave_criptografia

# ✨ Google Gemini API Key for embeddings
GOOGLE_GEMINI_API_KEY=sua_chave_google_gemini

# ✨ ElasticSearch Configuration (opcional)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_USE_SSL=false
ELASTICSEARCH_VERIFY_CERTS=false

# Logging
LOG_FORMAT=json
```

### 3. Obtenha a chave da API Google Gemini

1. Acesse [Google AI Studio](https://aistudio.google.com/)
2. Crie uma conta gratuita
3. Gere uma API Key
4. Adicione a chave no arquivo `.env`

### 4. Execute com Docker Compose

```bash
# Inicie os serviços (inclui PostgreSQL com pgvector)
docker-compose up -d

# Verifique os logs
docker-compose logs -f app
```

### 5. Execute as migrações e crie o superusuário

```bash
# Execute as migrações (inclui tabelas de embeddings)
docker-compose exec app python manage.py migrate

# Crie um superusuário (se não foi criado automaticamente)
docker-compose exec app python manage.py createsuperuser
```

### 6. Configure automações (opcional)

```bash
# Configure web scraping e business brain para executar automaticamente
docker-compose exec app ./brain/crontab_setup.sh
```

### 7. Acesse a API

A API estará disponível em: `http://localhost:8005`

- **API Base**: `http://localhost:8005/api/v1/`
- **Admin Django**: `http://localhost:8005/admin/`

## 🤖 Fluxo de Inteligência Artificial

### 1. Vetorização Automática de Posts (Django Signals)
```
Usuário cria post → Signal detecta → Google Gemini gera embedding → Salva automaticamente
```

### 2. Web Scraping Inteligente
```bash
# Execução manual
python scraping/webscraper.py          # Coleta dados de sites
python scraping/text_vectorizer.py     # Vetoriza dados coletados
```

### 3. Business Brain (ElasticSearch)
```bash
# Configurar execução automática (a cada 10 minutos)
./brain/crontab_setup.sh

# Ou execução manual
python brain/business_vectorizer.py
```

## 📚 Documentação da API

### Autenticação

#### Obter Token JWT
```
POST /api/v1/auth/login/
Content-Type: application/json

{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

#### Renovar Token
```
POST /api/v1/auth/refresh/
Content-Type: application/json

{
    "refresh": "seu_refresh_token"
}
```

### Textos (Com Vetorização Automática)

#### Criar Texto (Gera Embedding Automaticamente)
```
POST /api/v1/texts/
Authorization: Bearer seu_access_token
Content-Type: application/json

{
    "theme": "Marketing Digital",
    "platform": "FCB",
    "content": "Conteúdo do post para Facebook",
    "is_approved": true
}
```
**→ Sistema cria embedding automaticamente via Django Signal**

#### Listar Textos
```
GET /api/v1/texts/
Authorization: Bearer seu_access_token
```

### Sites (Para Web Scraping)

#### Criar Site de Referência
```
POST /api/v1/sites/
Authorization: Bearer seu_access_token
Content-Type: application/json

{
    "name": "TechCrunch",
    "url": "https://techcrunch.com",
    "category": "NOTICIAS"
}
```

#### Listar Sites
```
GET /api/v1/sites/
Authorization: Bearer seu_access_token
```

### Embeddings (Sistema de IA)

#### Listar Embeddings por Origem
```
GET /api/v1/embeddings/
Authorization: Bearer seu_access_token

# Filtros de exemplo:
# ?origin=webscraping    - Dados de web scraping
# ?origin=generated      - Posts criados pelos usuários
# ?origin=business_brain - Dados do ElasticSearch
```

#### Visualizar Embedding
```
GET /api/v1/embeddings/{uuid}/
Authorization: Bearer seu_access_token
```

## 🗄️ Modelos de Banco de Dados

### Modelo Text (com Signal de Vetorização)
```python
class Text(models.Model):
    theme = models.CharField(max_length=200)              # Tema
    platform = models.CharField(max_length=200)          # FCB/INT/TTK/LKN
    content = models.TextField()                          # Conteúdo
    is_approved = models.BooleanField(default=False)      # Aprovação
    created_at = models.DateTimeField(auto_now_add=True)  # Criação
    updated_at = models.DateTimeField(auto_now=True)      # Atualização
```

### Modelo Site (Para Web Scraping)
```python
class Site(models.Model):
    name = models.CharField(max_length=200)               # Nome do site
    url = models.URLField()                               # URL para scraping
    category = models.CharField(max_length=200)           # Categoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Modelo Embedding (Sistema de IA)
```python
class Embedding(models.Model):
    id = models.UUIDField(primary_key=True)               # UUID único
    origin = models.CharField(max_length=20)              # webscraping/generated/business_brain
    content = models.TextField()                          # Texto original
    title = models.CharField(max_length=500)              # Título
    embedding_vector = models.JSONField()                 # Vetor do Gemini (1536 dim)
    metadata = models.JSONField(default=dict)             # Metadados enriquecidos
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## 🤖 Origens de Embeddings

### 1. `webscraping`
- **Fonte**: Sites cadastrados no modelo Site
- **Processo**: `webscraper.py` → `text_vectorizer.py`
- **Metadados**: URL, categoria, data de scraping

### 2. `generated` 
- **Fonte**: Posts criados no modelo Text
- **Processo**: Django Signal automático
- **Metadados**: Plataforma, tema, ID do texto

### 3. `business_brain`
- **Fonte**: Dados do ElasticSearch corporativo
- **Processo**: `business_vectorizer.py` (crontab 10min)
- **Metadados**: Índice, documento ID, score

## 🔧 Executar Localmente (Desenvolvimento)

### 1. Configure o ambiente Python

```bash
# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Instale as dependências (inclui IA)
pip install -r requirements.txt
```

### 2. Configure PostgreSQL com pgvector

```bash
# Instale PostgreSQL e extensão pgvector
sudo apt-get install postgresql postgresql-contrib
sudo apt-get install postgresql-16-pgvector

# Configure o banco
sudo -u postgres psql
CREATE DATABASE unipost;
CREATE USER seu_usuario WITH PASSWORD 'sua_senha';
GRANT ALL PRIVILEGES ON DATABASE unipost TO seu_usuario;
\c unipost;
CREATE EXTENSION vector;
```

### 3. Configure variáveis de ambiente

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=unipost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
GOOGLE_GEMINI_API_KEY=sua_chave_gemini
```

### 4. Execute migrações e servidor

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8005
```

## 🔍 Monitoramento e Logs

### Logs dos Scripts de IA

```bash
# Web scraping
tail -f scraping/scraping.log
tail -f scraping/vectorizer.log

# Business brain
tail -f brain/business_brain.log
tail -f brain/crontab.log

# Django (geral)
tail -f logs/django.log
```

### Verificar Status dos Embeddings

```bash
python manage.py shell

>>> from embeddings.models import Embedding
>>> Embedding.objects.values('origin').annotate(count=models.Count('id'))
# [{'origin': 'webscraping', 'count': 150}, 
#  {'origin': 'generated', 'count': 89}, 
#  {'origin': 'business_brain', 'count': 1200}]
```

## 🔧 Scripts Utilitários

### Web Scraping
```bash
# Executar scraping manual
python scraping/webscraper.py

# Vetorizar dados coletados
python scraping/text_vectorizer.py
```

### Business Brain
```bash
# Executar sincronização manual
python brain/business_vectorizer.py

# Configurar automação
./brain/crontab_setup.sh

# Verificar crontab
crontab -l
```

## 🐛 Solução de Problemas

### Problemas de IA/Embeddings

1. **API Key Google Gemini inválida**: Verifique a chave em `.env`
2. **pgvector não instalado**: Execute `CREATE EXTENSION vector;` no PostgreSQL
3. **ElasticSearch não conecta**: Verifique configurações de host/porta
4. **Embeddings não são criados**: Verifique logs dos signals do Django

### Problemas Gerais

1. **Erro de conexão com banco**: Verifique PostgreSQL e credenciais
2. **Token JWT inválido**: Verifique expiração do token
3. **Docker não inicia**: Verifique portas 8005 e 5437
4. **Scripts de crontab não executam**: Verifique permissões e logs

## 🚀 Recursos Avançados

### Busca Semântica (Futura implementação)
```python
# Exemplo de como implementar busca semântica
from embeddings.models import Embedding
import numpy as np

def semantic_search(query_text, limit=10):
    query_embedding = generate_embedding(query_text)
    # Implementar busca por similaridade de cosseno
    # usando pgvector <-> operator
```

### APIs de IA (Futuro)
```
POST /api/v1/ai/search/          # Busca semântica
POST /api/v1/ai/similar/         # Conteúdo similar  
GET /api/v1/ai/analytics/        # Analytics de IA
```

## 📄 Licença

Este projeto está licenciado sob a licença especificada no arquivo LICENSE.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

**Desenvolvido com ❤️ usando Django REST Framework + AI 🤖**