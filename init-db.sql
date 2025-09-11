-- Inicialização do PostgreSQL com extensão pgvector para embeddings

-- Instalar extensão pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Log da instalação
\echo 'Extensão pgvector instalada com sucesso'