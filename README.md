# UniPost API

Uma API RESTful desenvolvida em Django para gerenciamento de textos para redes sociais com sistema avançado de **inteligência artificial e busca semântica**. A API permite criar, listar, visualizar, editar e deletar textos para diferentes plataformas sociais com autenticação JWT, além de **vetorização automática de conteúdo**, **web scraping** e **sincronização com ElasticSearch**.

## 🤖 Funcionalidades de IA e Busca Semântica

- **Vetorização Automática**: Embeddings gerados automaticamente com Google Gemini para todos os textos
- **Web Scraping Inteligente**: Coleta automática de conteúdo de sites de referência usando MCP SDK
- **Business Brain**: Sincronização e vetorização de dados corporativos do ElasticSearch
- **Busca Semântica**: Sistema de busca baseado em similaridade de vetores
- **Banco Vetorizado**: PostgreSQL com extensão pgvector para armazenamento de embeddings
- **🎨 Geração de Imagens com IA**: Sistema completo de geração de imagens usando DALL-E e GPT-4 para posts

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
├── unipost_automation/     # 🤖 Módulo de Automação Completa
│   ├── README.md          # Documentação da automação
│   ├── docs/setup.md      # Guia detalhado de configuração
│   ├── src/               # Código fonte da automação
│   │   ├── bot/async_bot.py         # Robô assíncrono principal
│   │   ├── scraping/webscraper.py   # Webscraper otimizado
│   │   ├── formatting/text_formatter.py # Formatação e embeddings
│   │   ├── posting/wordpress_client.py  # Cliente WordPress
│   │   └── storage/       # Módulos de armazenamento
│   ├── tests/             # Testes automatizados
│   └── logs/              # Logs do sistema
├── unipost_image_generator/ # 🎨 Módulo de Geração de Imagens com IA
│   ├── generator.py       # Orquestrador principal de geração
│   ├── clients.py         # Cliente DALL-E (OpenAI)
│   ├── prompt_builder.py  # Construtor de prompts com GPT-4
│   ├── storage.py         # Gerenciador de armazenamento
│   ├── models.py          # Modelos Django para metadados
│   ├── views.py           # Views REST para API
│   ├── serializers.py     # Serializers DRF
│   ├── urls.py            # URLs da API
│   ├── admin.py           # Interface Django Admin
│   └── tests/             # Testes automatizados
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

# 🤖 WordPress Configuration (for Unipost Automation)
WORDPRESS_URL=https://seusite.wordpress.com
WORDPRESS_USERNAME=seu_usuario_wp
WORDPRESS_APP_PASSWORD=sua_senha_de_aplicativo_wp

# 🤖 Unipost Automation Settings
UNIPOST_AUTOMATION_ENABLED=true
UNIPOST_AUTOMATION_INTERVAL=300  # seconds (300 = 5 minutes)
UNIPOST_AUTOMATION_MAX_PAGES=50
UNIPOST_AUTOMATION_MAX_DEPTH=2

# 🎨 Unipost Image Generator Settings
DALLE_API_KEY=sua_chave_openai
IMAGE_STORAGE_PATH=media/generated_images/
IMAGE_GENERATION_DEFAULT_SIZE=1024x1024
IMAGE_GENERATION_MAX_CONCURRENT=3
GPT4_MODEL=gpt-4

# Logging
LOG_FORMAT=json
```

### 3. Obtenha as chaves das APIs

#### Google Gemini (para embeddings)
1. Acesse [Google AI Studio](https://aistudio.google.com/)
2. Crie uma conta gratuita
3. Gere uma API Key
4. Adicione a chave no arquivo `.env`

#### OpenAI (para geração de imagens e construção de prompts)
1. Acesse [OpenAI Platform](https://platform.openai.com/)
2. Crie uma conta e configure um método de pagamento
3. Gere uma API Key
4. Adicione `DALLE_API_KEY` no arquivo `.env`
5. **Nota**: A mesma chave é usada para DALL-E (imagens) e GPT-4 (prompts)

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

### 7. Configure o WordPress para Automação (opcional)

Se você deseja usar o módulo de automação completa que replica posts automaticamente:

1. **Configure WordPress REST API**:
   - Acesse seu painel WordPress
   - Vá em **Usuários > Perfil**
   - Crie uma **Senha de Aplicativo** para "Unipost Automation"
   - Adicione as credenciais no `.env`

2. **Execute o Robô de Automação**:
   ```bash
   # Executar dentro do container
   docker-compose exec app python unipost_automation/src/bot/async_bot.py

   # Ou executar localmente (com ambiente virtual ativo)
   python unipost_automation/src/bot/async_bot.py
   ```

3. **Verificar Logs da Automação**:
   ```bash
   tail -f unipost_automation/logs/async_bot.log
   ```

### 8. Acesse a API

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

### 4. Automação Completa WordPress (Novo!)
```bash
# Executa robô que monitora sites e replica posts automaticamente
python unipost_automation/src/bot/async_bot.py

# Fluxo completo:
# Monitora URLs → WebScraping → Embeddings → Replica no WordPress
```

### 5. Geração de Imagens com IA (Novo!)
```bash
# Gerar imagem para um post específico
from unipost_image_generator.generator import generate_image_for_post

# Exemplo de uso
result = await generate_image_for_post(
    embedding_id="uuid-do-embedding",
    text="Texto do post",
    title="Título do post"
)

# Fluxo completo:
# Texto → GPT-4 gera prompt otimizado → DALL-E gera imagem → Armazena com metadados
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

### Geração de Imagens (Sistema de IA)

#### Gerar Imagem para Embedding
```
POST /api/v1/image-generator/generate/
Authorization: Bearer seu_access_token
Content-Type: application/json

{
    "embedding_id": "uuid-do-embedding",
    "custom_prompt": "Prompt personalizado (opcional)",
    "style_preferences": {
        "style": "vivid",
        "size": "1024x1024",
        "quality": "standard"
    }
}
```

#### Listar Imagens Geradas
```
GET /api/v1/image-generator/images/
Authorization: Bearer seu_access_token

# Filtros:
# ?embedding_id=uuid     - Imagens de um embedding específico
# ?created_at__gte=date  - Imagens criadas após data
```

#### Regenerar Imagem
```
POST /api/v1/image-generator/regenerate/{embedding_id}/
Authorization: Bearer seu_access_token
Content-Type: application/json

{
    "new_prompt": "Novo prompt personalizado (opcional)"
}
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

### Modelo GeneratedImage (Sistema de Geração de Imagens)
```python
class GeneratedImage(models.Model):
    id = models.UUIDField(primary_key=True)               # UUID único
    embedding = models.ForeignKey(Embedding)              # Relacionamento com embedding
    original_text = models.TextField()                    # Texto do post original
    generated_prompt = models.TextField()                 # Prompt otimizado pelo GPT-4
    image_path = models.CharField(max_length=500)         # Caminho da imagem gerada
    dalle_response = models.JSONField(default=dict)       # Metadados DALL-E
    generation_metadata = models.JSONField(default=dict)  # Metadados do processo
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

### Unipost Automation (Novo!)
```bash
# Executar robô de automação
python unipost_automation/src/bot/async_bot.py

# Testar módulos individuais
python unipost_automation/src/scraping/webscraper.py       # WebScraper
python unipost_automation/src/formatting/text_formatter.py # Formatador
python unipost_automation/src/posting/wordpress_client.py  # WordPress
python unipost_automation/src/storage/db.py               # Database

# Executar testes
python unipost_automation/tests/test_basic.py

# Verificar logs
tail -f unipost_automation/logs/async_bot.log
tail -f unipost_automation/logs/*.log
```

### Unipost Image Generator (Novo!)
```bash
# Gerar imagem manualmente (via Django shell)
python manage.py shell

>>> from unipost_image_generator.generator import generate_image_for_post
>>> import asyncio
>>>
>>> # Gerar imagem para um embedding existente
>>> result = asyncio.run(generate_image_for_post(
...     embedding_id="uuid-do-embedding",
...     text="Texto do post",
...     title="Título do post"
... ))
>>> print(f"Imagem gerada: {result.image_path}")

# Testar componentes individuais
python -c "
from unipost_image_generator.clients import DalleApiClient
from unipost_image_generator.prompt_builder import OpenAIPromptBuilder
import asyncio

async def test():
    # Testar DALL-E client
    dalle = DalleApiClient()
    await dalle.initialize()
    print('DALL-E Client OK')

    # Testar GPT-4 prompt builder
    gpt4 = OpenAIPromptBuilder()
    await gpt4.initialize()
    print('GPT-4 Client OK')

asyncio.run(test())
"

# Verificar estatísticas de geração
python manage.py shell -c "
from unipost_image_generator.models import GeneratedImage
from django.db.models import Count
print('Imagens por embedding:')
print(GeneratedImage.objects.values('embedding__title').annotate(count=Count('id')))
"
```

## 🐛 Solução de Problemas

### Problemas de IA/Embeddings

1. **API Key Google Gemini inválida**: Verifique a chave em `.env`
2. **pgvector não instalado**: Execute `CREATE EXTENSION vector;` no PostgreSQL
3. **ElasticSearch não conecta**: Verifique configurações de host/porta
4. **Embeddings não são criados**: Verifique logs dos signals do Django

### Problemas do Unipost Automation

1. **WordPress não conecta**: Verifique `WORDPRESS_URL`, `WORDPRESS_USERNAME` e `WORDPRESS_APP_PASSWORD`
2. **Erro 401 WordPress**: Confirme que a senha de aplicativo está correta
3. **Sites não são monitorados**: Verifique se existe pelo menos um Site cadastrado no admin Django
4. **Robô não processa posts**: Verifique logs em `unipost_automation/logs/async_bot.log`
5. **Conteúdo vazio no scraping**: Configure seletores CSS específicos para os sites no admin Django

### Problemas do Unipost Image Generator

1. **DALL-E API falha**: Verifique `DALLE_API_KEY` e créditos OpenAI
2. **GPT-4 API falha**: Verifique `DALLE_API_KEY` e créditos OpenAI
3. **Erro 401 OpenAI**: Confirme que a chave DALL-E é válida e tem créditos
4. **Imagens não são salvas**: Verifique permissões na pasta `IMAGE_STORAGE_PATH`
5. **Timeout na geração**: Ajuste `IMAGE_GENERATION_TIMEOUT` no .env
6. **Prompt muito longo**: DALL-E aceita máximo 1000 caracteres
7. **Módulo não inicializa**: Verifique logs do Django para erros de importação

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