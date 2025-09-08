# UniPost API

Uma API RESTful desenvolvida em Django para gerenciamento de textos para redes sociais. A API permite criar, listar, visualizar, editar e deletar textos para diferentes plataformas sociais (Facebook, Instagram, TikTok, LinkedIn) com sistema de autenticação JWT.

## 📋 Funcionalidades

- **Autenticação JWT**: Login, logout, refresh e verificação de tokens
- **Gerenciamento de Textos**: CRUD completo para textos de redes sociais
- **Suporte a Múltiplas Plataformas**: Facebook, Instagram, TikTok, LinkedIn
- **Sistema de Permissões**: Controle de acesso baseado em permissões Django
- **Aprovação de Conteúdo**: Sistema de aprovação para textos criados
- **API RESTful**: Endpoints padronizados seguindo convenções REST

## 🛠️ Tecnologias Utilizadas

- **Django 5.2.6**: Framework web principal
- **Django REST Framework**: Para construção da API REST
- **Simple JWT**: Autenticação via JSON Web Tokens
- **PostgreSQL**: Banco de dados principal
- **Docker & Docker Compose**: Containerização e orquestração
- **Python 3.13**: Linguagem de programação

## 📁 Estrutura do Projeto

```
unipost-api/
├── app/                    # Configurações principais do Django
│   ├── settings.py        # Configurações do projeto
│   ├── urls.py           # URLs principais
│   └── permissions.py    # Permissões customizadas
├── authentication/        # App de autenticação
│   ├── views.py          # Views de autenticação
│   └── urls.py           # URLs de autenticação
├── texts/                 # App de gerenciamento de textos
│   ├── models.py         # Modelo Text
│   ├── serializers.py    # Serializers DRF
│   ├── views.py          # Views CRUD
│   └── urls.py           # URLs de textos
├── docker-compose.yml     # Configuração Docker Compose
├── Dockerfile            # Imagem Docker da aplicação
├── requirements.txt      # Dependências Python
└── manage.py            # Utilitário de gerenciamento Django
```

## 🚀 Como Executar a API

### Pré-requisitos

- Docker
- Docker Compose
- Git

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
DB_NAME=unipost_db

# Django Superuser
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=sua_senha_admin

# Django Secret Key (gere uma nova)
SECRET_KEY=sua_secret_key_aqui

# Chave de criptografia (opcional)
ENCRYPTION_KEY=sua_chave_criptografia

# Logging
LOG_FORMAT=json
```

### 3. Execute com Docker Compose

```bash
# Inicie os serviços
docker-compose up -d

# Verifique os logs
docker-compose logs -f app
```

### 4. Execute as migrações e crie o superusuário

```bash
# Execute as migrações
docker-compose exec app python manage.py migrate

# Crie um superusuário (se não foi criado automaticamente)
docker-compose exec app python manage.py createsuperuser
```

### 5. Acesse a API

A API estará disponível em: `http://localhost:8005`

- **API Base**: `http://localhost:8005/api/v1/`
- **Admin Django**: `http://localhost:8005/admin/`

## 🔧 Executar Localmente (sem Docker)

### 1. Configure o ambiente Python

```bash
# Crie e ative um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configure o banco PostgreSQL

Certifique-se de ter PostgreSQL instalado e crie um banco de dados. Ajuste as variáveis de ambiente no `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=unipost_db
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
```

### 3. Execute as migrações

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Inicie o servidor

```bash
python manage.py runserver 8005
```

## 📚 Documentação da API

### Autenticação

#### Obter Token JWT
```
POST /api/v1/authentication/token/
Content-Type: application/json

{
    "username": "seu_usuario",
    "password": "sua_senha"
}
```

#### Renovar Token
```
POST /api/v1/authentication/token/refresh/
Content-Type: application/json

{
    "refresh": "seu_refresh_token"
}
```

#### Verificar Token
```
POST /api/v1/authentication/token/verify/
Content-Type: application/json

{
    "token": "seu_access_token"
}
```

#### Logout
```
POST /api/v1/authentication/logout/
Authorization: Bearer seu_access_token
```

#### Permissões do Usuário
```
GET /api/v1/user/permissions/
Authorization: Bearer seu_access_token
```

### Textos

#### Listar e Criar Textos
```
GET /api/v1/texts/
Authorization: Bearer seu_access_token

POST /api/v1/texts/
Authorization: Bearer seu_access_token
Content-Type: application/json

{
    "theme": "Tema do texto",
    "platform": "FCB",  // FCB, INT, TTK, LKN
    "content": "Conteúdo do texto",
    "is_aproved": false
}
```

#### Visualizar, Editar e Deletar Texto
```
GET /api/v1/texts/{id}/
Authorization: Bearer seu_access_token

PUT /api/v1/texts/{id}/
Authorization: Bearer seu_access_token
Content-Type: application/json

{
    "theme": "Tema atualizado",
    "platform": "INT",
    "content": "Conteúdo atualizado",
    "is_aproved": true
}

DELETE /api/v1/texts/{id}/
Authorization: Bearer seu_access_token
```

### Plataformas Suportadas

- `FCB` - Facebook
- `INT` - Instagram  
- `TTK` - TikTok
- `LKN` - LinkedIn

## 🔒 Sistema de Permissões

A API utiliza um sistema de permissões customizado que requer:

1. **Autenticação**: Usuário deve estar logado
2. **Permissões Django**: Usuário deve ter as permissões específicas:
   - `texts.view_text` - Visualizar textos
   - `texts.add_text` - Criar textos
   - `texts.change_text` - Editar textos
   - `texts.delete_text` - Deletar textos

## 🗄️ Banco de Dados

### Modelo Text

```python
class Text(models.Model):
    theme = models.CharField(max_length=200)           # Tema do texto
    platform = models.CharField(max_length=200)       # Plataforma (FCB/INT/TTK/LKN)
    content = models.TextField()                       # Conteúdo do texto
    created_at = models.DateTimeField(auto_now_add=True)  # Data de criação
    updated_at = models.DateTimeField(auto_now=True)   # Data de atualização
    is_aproved = models.BooleanField(default=False)    # Status de aprovação
```

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Erro de conexão com banco**: Verifique se o PostgreSQL está rodando e as credenciais estão corretas
2. **Erro de permissão**: Certifique-se de que o usuário tem as permissões necessárias
3. **Token JWT inválido**: Verifique se o token não expirou e está sendo enviado corretamente
4. **Docker não inicia**: Verifique se as portas 8005 e 5437 não estão em uso

### Logs

```bash
# Logs da aplicação
docker-compose logs app

# Logs do banco
docker-compose logs db

# Logs em tempo real
docker-compose logs -f
```

## 🔧 Desenvolvimento

### Comandos Úteis

```bash
# Criar migrações
docker-compose exec app python manage.py makemigrations

# Aplicar migrações
docker-compose exec app python manage.py migrate

# Shell Django
docker-compose exec app python manage.py shell

# Coletar arquivos estáticos
docker-compose exec app python manage.py collectstatic

# Executar testes
docker-compose exec app python manage.py test
```

### Estrutura das Migrações

As migrações ficam em:
- `authentication/migrations/`
- `texts/migrations/`

## 📄 Licença

Este projeto está licenciado sob a licença especificada no arquivo LICENSE.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

**Desenvolvido com ❤️ usando Django REST Framework**