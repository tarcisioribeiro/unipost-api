# UniPost API - Fluxo de Dados e Funcionalidades

Este documento descreve o fluxo de dados da UniPost API em formato Mermaid para geração de diagramas.

## Visão Geral da Arquitetura

```mermaid
graph TB
    Client[Cliente/Frontend]

    %% API Gateway/Main Entry
    API[UniPost API Gateway]

    %% Core Modules
    Auth[Módulo de Autenticação]
    Texts[Módulo de Textos/Conteúdo]
    Sites[Módulo de Sites]
    Embeddings[Módulo de Embeddings]
    Images[Módulo de Geração de Imagem]
    Core[Módulo Core/Dashboard]

    %% External Services
    OpenAI[OpenAI API]
    DALLE[DALL-E API]

    %% Database
    DB[(PostgreSQL Database)]

    %% File Storage
    Storage[Armazenamento de Arquivos]

    %% Connections
    Client --> API
    API --> Auth
    API --> Texts
    API --> Sites
    API --> Embeddings
    API --> Images
    API --> Core

    Auth --> DB
    Texts --> DB
    Sites --> DB
    Embeddings --> DB
    Images --> DB
    Core --> DB

    Embeddings --> OpenAI
    Images --> OpenAI
    Images --> DALLE
    Images --> Storage
```

## Fluxo de Autenticação

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth
    participant DB

    Client->>API: POST /api/v1/authentication/token/
    API->>Auth: Validar credenciais
    Auth->>DB: Verificar usuário
    DB-->>Auth: Dados do usuário
    Auth-->>API: Token JWT
    API-->>Client: Access & Refresh Token

    Note over Client: Armazenar tokens

    Client->>API: Requisições autenticadas
    API->>Auth: Verificar token
    Auth-->>API: Token válido
    API-->>Client: Resposta autorizada

    Client->>API: POST /api/v1/authentication/token/refresh/
    API->>Auth: Renovar token
    Auth-->>API: Novo access token
    API-->>Client: Novo token
```

## Fluxo de Gerenciamento de Conteúdo

```mermaid
flowchart TD
    Start([Usuário Inicia])

    %% Content Creation Flow
    CreateContent[Criar Novo Conteúdo]
    FillForm[Preencher Formulário]
    ValidateContent{Validar Conteúdo}
    SaveDraft[Salvar como Rascunho]

    %% Review Process
    SubmitReview[Enviar para Revisão]
    ReviewContent{Revisar Conteúdo}
    ApproveContent[Aprovar Conteúdo]
    RejectContent[Rejeitar/Solicitar Correções]

    %% Publishing
    ScheduleContent[Agendar Publicação]
    PublishContent[Publicar Imediatamente]
    Published[Conteúdo Publicado]

    %% Analytics
    TrackPerformance[Rastrear Performance]
    Analytics[Analytics Dashboard]

    Start --> CreateContent
    CreateContent --> FillForm
    FillForm --> ValidateContent

    ValidateContent -->|Válido| SaveDraft
    ValidateContent -->|Inválido| FillForm

    SaveDraft --> SubmitReview
    SubmitReview --> ReviewContent

    ReviewContent -->|Aprovado| ApproveContent
    ReviewContent -->|Rejeitado| RejectContent
    RejectContent --> FillForm

    ApproveContent --> ScheduleContent
    ApproveContent --> PublishContent
    ScheduleContent --> Published
    PublishContent --> Published

    Published --> TrackPerformance
    TrackPerformance --> Analytics
```

## Fluxo de Web Scraping e Embeddings

```mermaid
graph TD
    %% Site Registration
    RegisterSite[Registrar Site para Monitoramento]
    ConfigSite[Configurar Parâmetros de Scraping]

    %% Scraping Process
    ScheduledJob[Job Agendado de Scraping]
    ScrapeSite[Fazer Scraping do Site]
    ExtractContent[Extrair Conteúdo]
    ValidateContent{Validar Qualidade}

    %% Processing
    ProcessContent[Processar Conteúdo]
    GenerateEmbedding[Gerar Embedding com OpenAI]
    StoreEmbedding[Armazenar no Banco]

    %% Knowledge Base
    CreateKB[Criar Knowledge Base]
    IndexContent[Indexar Conteúdo]

    %% Search & Retrieval
    SearchQuery[Consulta de Busca]
    SimilaritySearch[Busca por Similaridade]
    ReturnResults[Retornar Resultados]

    RegisterSite --> ConfigSite
    ConfigSite --> ScheduledJob
    ScheduledJob --> ScrapeSite
    ScrapeSite --> ExtractContent
    ExtractContent --> ValidateContent

    ValidateContent -->|Qualidade OK| ProcessContent
    ValidateContent -->|Baixa Qualidade| ScheduledJob

    ProcessContent --> GenerateEmbedding
    GenerateEmbedding --> StoreEmbedding
    StoreEmbedding --> CreateKB
    CreateKB --> IndexContent

    SearchQuery --> SimilaritySearch
    SimilaritySearch --> ReturnResults
```

## Fluxo de Geração de Imagens

```mermaid
sequenceDiagram
    participant User
    participant API
    participant ImageGen
    participant OpenAI
    participant DALLE
    participant Storage
    participant DB

    User->>API: POST /api/images/generate/
    API->>ImageGen: Processar requisição

    Note over ImageGen: Analisar texto de entrada
    ImageGen->>OpenAI: Gerar prompt otimizado
    OpenAI-->>ImageGen: Prompt refinado

    ImageGen->>DALLE: Requisitar geração de imagem
    DALLE-->>ImageGen: URL da imagem gerada

    ImageGen->>Storage: Baixar e armazenar imagem
    Storage-->>ImageGen: Caminho do arquivo

    ImageGen->>DB: Salvar metadados
    DB-->>ImageGen: Registro criado

    ImageGen-->>API: Imagem gerada com sucesso
    API-->>User: Dados da imagem gerada

    User->>API: GET /api/images/status/{id}/
    API->>DB: Consultar status
    DB-->>API: Status atual
    API-->>User: Status da geração

    User->>API: GET /api/images/list/
    API->>DB: Listar imagens do usuário
    DB-->>API: Lista de imagens
    API-->>User: Galeria de imagens
```

## Estrutura de Dados e Relacionamentos

```mermaid
erDiagram
    USER {
        id integer PK
        username string
        email string
        password string
    }

    USER_PROFILE {
        id integer PK
        user_id integer FK
        company string
        api_quota integer
        api_usage integer
        plan_type string
    }

    CAMPAIGN {
        id uuid PK
        name string
        owner_id integer FK
        status string
        start_date datetime
        end_date datetime
        target_platforms json
    }

    CONTENT_PIECE {
        id uuid PK
        title string
        content text
        content_type string
        creator_id integer FK
        campaign_id uuid FK
        status string
        is_published boolean
        published_at datetime
    }

    SOURCE_SITE {
        id uuid PK
        name string
        url string
        category string
        owner_id integer FK
        is_active boolean
        monitor_frequency integer
    }

    SCRAPED_POST {
        id uuid PK
        title string
        url string
        content text
        source_site_id uuid FK
        status string
        quality_score float
    }

    KNOWLEDGE_BASE {
        id uuid PK
        name string
        owner_id integer FK
        embedding_model string
        total_embeddings integer
    }

    ENHANCED_EMBEDDING {
        id uuid PK
        title string
        content text
        embedding_vector json
        knowledge_base_id uuid FK
        source_type string
        quality_score float
    }

    AI_IMAGE_REQUEST {
        id uuid PK
        requester_id integer FK
        campaign_id uuid FK
        original_text text
        ai_prompt text
        status string
        model_name string
    }

    ENHANCED_GENERATED_IMAGE {
        id uuid PK
        image_request_id uuid FK
        image_path string
        width integer
        height integer
        is_approved boolean
    }

    %% Relationships
    USER ||--|| USER_PROFILE : has
    USER ||--o{ CAMPAIGN : owns
    USER ||--o{ CONTENT_PIECE : creates
    USER ||--o{ SOURCE_SITE : manages
    USER ||--o{ KNOWLEDGE_BASE : owns
    USER ||--o{ AI_IMAGE_REQUEST : requests

    CAMPAIGN ||--o{ CONTENT_PIECE : contains
    CAMPAIGN ||--o{ AI_IMAGE_REQUEST : includes
    CAMPAIGN ||--o{ ENHANCED_EMBEDDING : relates_to

    SOURCE_SITE ||--o{ SCRAPED_POST : generates

    KNOWLEDGE_BASE ||--o{ ENHANCED_EMBEDDING : contains

    AI_IMAGE_REQUEST ||--o{ ENHANCED_GENERATED_IMAGE : produces
```

## Endpoints da API por Módulo

### Autenticação (`/api/v1/authentication/`)
- `POST /token/` - Obter token de acesso
- `POST /token/refresh/` - Renovar token
- `POST /token/verify/` - Verificar token
- `POST /logout/` - Logout
- `GET /user/permissions/` - Obter permissões do usuário

### Conteúdo (`/api/v1/texts/`)
- `GET /` - Listar conteúdos
- `POST /` - Criar novo conteúdo
- `GET /{id}/` - Obter conteúdo específico
- `PUT /{id}/` - Atualizar conteúdo
- `DELETE /{id}/` - Deletar conteúdo
- `POST /webhook/approval/` - Webhook de aprovação

### Sites (`/api/v1/sites/`)
- `GET /` - Listar sites
- `POST /` - Registrar novo site
- `GET /{id}/` - Obter detalhes do site
- `PUT /{id}/` - Atualizar configurações do site
- `DELETE /{id}/` - Remover site

### Embeddings (`/api/v1/embeddings/`)
- `GET /` - Listar embeddings
- `POST /` - Criar embedding
- `GET /{id}/` - Obter embedding específico
- `PUT /{id}/` - Atualizar embedding
- `DELETE /{id}/` - Deletar embedding

### Core/Dashboard (`/api/v1/`)
- `GET /dashboard/analytics/` - Analytics do dashboard
- `GET /admin/system/health/` - Saúde do sistema
- `GET /admin/audit/logs/` - Logs de auditoria

### Geração de Imagens (`/api/images/`)
- `POST /generate/` - Gerar nova imagem
- `GET /status/{id}/` - Status da geração
- `GET /list/` - Listar imagens geradas

## Fluxo de Dados Completo

```mermaid
flowchart LR
    %% Input Sources
    UserInput[Entrada do Usuário]
    ScrapedData[Dados Extraídos]

    %% Processing Layers
    Validation[Validação]
    AIProcessing[Processamento IA]
    Storage[Armazenamento]

    %% Output Destinations
    API_Response[Resposta da API]
    Dashboard[Dashboard]
    Analytics[Analytics]

    %% External Integrations
    OpenAI_Service[Serviços OpenAI]

    %% Data Flow
    UserInput --> Validation
    ScrapedData --> Validation

    Validation --> AIProcessing
    AIProcessing --> OpenAI_Service
    OpenAI_Service --> AIProcessing

    AIProcessing --> Storage
    Storage --> API_Response
    Storage --> Dashboard
    Storage --> Analytics

    API_Response --> UserInput
```

---

Este documento fornece uma visão completa do fluxo de dados da UniPost API, incluindo todos os módulos principais, suas interações e os fluxos de dados entre eles. Os diagramas podem ser renderizados usando qualquer ferramenta compatível com Mermaid.