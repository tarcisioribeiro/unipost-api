# Docker Setup - UniPost API

Documentação completa para execução do UniPost API com **Docker Compose**, incluindo todos os recursos de **IA** e **vetorização**.

## 🐳 Visão Geral

O Docker Compose está configurado para executar:

- **API Django**: Aplicação principal com endpoints REST
- **PostgreSQL + pgvector**: Banco de dados com suporte a vetores
- **Scripts de IA**: Web scraping, vectorização e Business Brain
- **Cron Jobs**: Automação para sincronização contínua

## 📋 Pré-requisitos

- **Docker**: Versão 20.10+
- **Docker Compose**: Versão 2.0+
- **Git**: Para clonar o repositório
- **Google Gemini API Key**: Para funcionalidades de IA

## 🚀 Quick Start

### 1. Clone e Configure

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd unipost-api

# Configure variáveis de ambiente
cp .env.example .env
```

### 2. Configure o .env

```env
# Database
DB_HOST=db
DB_PORT=5432
DB_USER=unipost_user
DB_PASSWORD=senha_segura_aqui
DB_NAME=unipost

# Django Superuser
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=senha_admin_aqui

# Django Secret Key (gere uma nova)
SECRET_KEY=gere_uma_chave_secreta_forte_aqui

# ✨ Google Gemini API Key (OBRIGATÓRIO para IA)
GOOGLE_GEMINI_API_KEY=sua_chave_google_gemini

# ✨ ElasticSearch (OPCIONAL para Business Brain)
ELASTICSEARCH_HOST=seu_elasticsearch_host
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=seu_usuario_es
ELASTICSEARCH_PASSWORD=sua_senha_es
ELASTICSEARCH_USE_SSL=false
ELASTICSEARCH_VERIFY_CERTS=false

# Logging
LOG_FORMAT=json
```

### 3. Obter Google Gemini API Key

1. Acesse [Google AI Studio](https://aistudio.google.com/)
2. Faça login com conta Google
3. Clique em "Get API key" → "Create API key"
4. Copie a chave e adicione no `.env`

### 4. Execute o Sistema

```bash
# Inicie todos os serviços
docker-compose up -d

# Verifique se os serviços estão rodando
docker-compose ps

# Acompanhe os logs
docker-compose logs -f app
```

### 5. Configure o Banco

```bash
# Execute migrações (inclui tabelas de IA)
docker-compose exec app python manage.py migrate

# Crie superusuário (se não foi criado automaticamente)
docker-compose exec app python manage.py createsuperuser

# Verifique instalação do pgvector
docker-compose exec db psql -U $DB_USER -d $DB_NAME -c "\\dx"
```

### 6. Configure Automações (Opcional)

```bash
# Configure Business Brain para executar a cada 10 minutos
docker-compose exec app ./brain/crontab_setup.sh
```

## 🗂️ Estrutura dos Serviços

### Serviço `app` (Django API)

```yaml
services:
  app:
    build: .
    ports:
      - "8005:8005"          # API disponível em localhost:8005
    env_file:
      - .env                 # Todas as variáveis de ambiente
    volumes:
      - ./media:/app/media   # Uploads de mídia
      - ./logs:/app/logs     # Logs da aplicação
      - ./static:/app/static # Arquivos estáticos
    depends_on:
      db:
        condition: service_healthy  # Aguarda banco estar pronto
```

### Serviço `db` (PostgreSQL + pgvector)

```yaml
services:
  db:
    image: postgres:16.9-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Dados persistentes
      - ./backups:/backups                      # Backups
      - ./init-db.sql:/docker-entrypoint-initdb.d/init-db.sql  # ✨ pgvector
    ports:
      - "5437:5432"          # PostgreSQL em localhost:5437
```

## 🔧 Comandos Essenciais

### Gerenciamento Básico

```bash
# Iniciar serviços
docker-compose up -d

# Parar serviços
docker-compose down

# Reiniciar apenas um serviço
docker-compose restart app

# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs apenas da API
docker-compose logs -f app

# Ver status dos serviços
docker-compose ps
```

### Django Management

```bash
# Executar comandos Django
docker-compose exec app python manage.py <comando>

# Migrações
docker-compose exec app python manage.py makemigrations
docker-compose exec app python manage.py migrate

# Shell interativo
docker-compose exec app python manage.py shell

# Coletar arquivos estáticos
docker-compose exec app python manage.py collectstatic

# Criar superusuário
docker-compose exec app python manage.py createsuperuser
```

### Scripts de IA

```bash
# Web scraping manual
docker-compose exec app python scraping/webscraper.py

# Vetorização manual
docker-compose exec app python scraping/text_vectorizer.py

# Business Brain manual
docker-compose exec app python brain/business_vectorizer.py

# Ver logs das automações
docker-compose exec app tail -f brain/crontab.log
```

### Banco de Dados

```bash
# Conectar ao PostgreSQL
docker-compose exec db psql -U $DB_USER -d $DB_NAME

# Backup do banco
docker-compose exec db pg_dump -U $DB_USER -d $DB_NAME > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U $DB_USER -d $DB_NAME < backup.sql

# Verificar extensão pgvector
docker-compose exec db psql -U $DB_USER -d $DB_NAME -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

## 📊 Monitoramento e Logs

### Estrutura de Logs

```
logs/
├── django.log          # Logs da aplicação Django
├── access.log          # Logs de acesso HTTP
└── error.log           # Logs de erro

scraping/
├── scraping.log        # Logs do web scraping
└── vectorizer.log      # Logs da vetorização

brain/
├── business_brain.log  # Logs do Business Brain
└── crontab.log         # Logs do crontab
```

### Comandos de Monitoramento

```bash
# Logs em tempo real da API
tail -f logs/django.log

# Logs de IA
tail -f scraping/*.log brain/*.log

# Buscar erros específicos
grep -r "ERROR" logs/ scraping/ brain/

# Monitorar embeddings sendo criados
docker-compose exec app python manage.py shell
>>> from embeddings.models import Embedding
>>> Embedding.objects.count()
```

### Health Check

```bash
# Verificar saúde da API
curl http://localhost:8005/health/

# Verificar Admin Django
curl http://localhost:8005/admin/

# Testar endpoint de autenticação
curl -X POST http://localhost:8005/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sua_senha"}'
```

## 🐛 Solução de Problemas

### Problemas Comuns

#### 1. Serviço não inicia

```bash
# Ver logs detalhados
docker-compose logs app

# Reconstruir imagem
docker-compose build --no-cache app
docker-compose up -d

# Verificar dependências
docker-compose exec app pip list
```

#### 2. Erro de banco de dados

```bash
# Verificar se PostgreSQL está rodando
docker-compose exec db pg_isready

# Verificar conexão
docker-compose exec app python manage.py dbshell

# Reset completo do banco
docker-compose down -v  # CUIDADO: Remove dados!
docker-compose up -d
```

#### 3. pgvector não instalado

```bash
# Verificar se extensão está ativa
docker-compose exec db psql -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Recrear banco com init script
docker-compose down -v
docker-compose up -d
```

#### 4. Scripts de IA não funcionam

```bash
# Verificar Google Gemini API Key
docker-compose exec app python -c "
import os
print('GOOGLE_GEMINI_API_KEY:', os.getenv('GOOGLE_GEMINI_API_KEY')[:10] + '...')
"

# Testar conexão com Gemini
docker-compose exec app python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
result = genai.embed_content(model='models/embedding-001', content='teste')
print('Google Gemini funcionando!')
"
```

#### 5. Crontab não executa

```bash
# Verificar se crontab está configurado
docker-compose exec app crontab -l

# Ver logs do crontab
docker-compose exec app tail -f brain/crontab.log

# Reconfigurar crontab
docker-compose exec app ./brain/crontab_setup.sh
```

### Limpeza e Reset

```bash
# Parar e remover containers
docker-compose down

# Remover volumes (CUIDADO: Remove dados!)
docker-compose down -v

# Remover imagens
docker-compose down --rmi all

# Reset completo
docker-compose down -v --rmi all
docker system prune -a
```

## 🔧 Configurações Avançadas

### Variáveis de Ambiente Avançadas

```env
# Performance
DJANGO_DEBUG=False                    # Produção
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,seu_dominio.com

# Logging avançado
LOG_LEVEL=INFO                        # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json                       # json ou plain

# Database Pool
DB_CONN_MAX_AGE=600                   # Conexões persistentes
DB_CONN_HEALTH_CHECKS=true            # Health check das conexões

# IA Settings
GEMINI_RATE_LIMIT=60                  # Requests por minuto
VECTORIZER_CHUNK_SIZE=1000            # Tamanho dos chunks
VECTORIZER_MAX_TEXT_LENGTH=2048       # Limite de texto
```

### Volumes Personalizados

```yaml
# docker-compose.override.yml
services:
  app:
    volumes:
      - ./custom_scripts:/app/scripts     # Scripts customizados
      - ./exports:/app/exports            # Exports/relatórios
      - /host/path/logs:/app/logs         # Logs em local específico
  
  db:
    volumes:
      - /host/path/postgres:/var/lib/postgresql/data  # DB em local específico
```

### Networking Customizado

```yaml
# docker-compose.override.yml
services:
  app:
    networks:
      - unipost-network
      - external-network                 # Rede externa
    expose:
      - 8005
    # ports: []                          # Remove exposição pública
  
  nginx:                                # Proxy reverso
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app

networks:
  external-network:
    external: true
```

## 📈 Performance e Escalabilidade

### Otimizações de Performance

```yaml
# docker-compose.prod.yml
services:
  app:
    deploy:
      replicas: 3                       # Múltiplas instâncias
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    environment:
      - DJANGO_DEBUG=False
      - LOG_LEVEL=WARNING
  
  db:
    command: >
      postgres
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=4MB
```

### Cache e Redis

```yaml
# Adicionar ao docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - unipost-network
    restart: unless-stopped

volumes:
  redis_data:
    driver: local
```

## 🚀 Deploy e Produção

### Docker Compose para Produção

```bash
# Usar arquivo específico de produção
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Build de produção
docker-compose -f docker-compose.prod.yml build --no-cache

# Deploy com zero downtime
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

### Backup Automatizado

```bash
# Adicionar ao crontab do host
0 2 * * * docker-compose exec -T db pg_dump -U $DB_USER -d $DB_NAME | gzip > /backups/unipost_$(date +\%Y\%m\%d).sql.gz
```

---

**Docker Setup UniPost API 🐳 - Inteligência Artificial em container!**