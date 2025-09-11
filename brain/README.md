# Business Brain - ElasticSearch Vectorizer

Script para sincronização e vetorização de dados corporativos do ElasticSearch.

## Funcionalidades

- **Conexão automática** com ElasticSearch usando configurações do `.env`
- **Descoberta automática** de todos os índices disponíveis
- **Processamento incremental** - só processa documentos novos/modificados
- **Vetorização com Google Gemini** (`embedding-001`)
- **Armazenamento** no modelo `Embedding` com `origin="business_brain"`
- **Execução via crontab** a cada 10 minutos
- **Sistema de logging** completo com rastreamento de erros
- **Controle de duplicatas** via hash de documento

## Configuração

### 1. Variáveis de Ambiente

Configure no arquivo `.env`:

```env
# ElasticSearch Configuration
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=seu_usuario
ELASTICSEARCH_PASSWORD=sua_senha
ELASTICSEARCH_USE_SSL=false
ELASTICSEARCH_VERIFY_CERTS=false

# Google Gemini
GOOGLE_GEMINI_API_KEY=sua_chave_api
```

### 2. Instalação de Dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar Crontab

Execute o script de configuração:

```bash
./brain/crontab_setup.sh
```

Ou configure manualmente:

```bash
crontab -e
# Adicione a linha:
*/10 * * * * cd /caminho/para/projeto && /caminho/para/venv/bin/python /caminho/para/brain/business_vectorizer.py >> /caminho/para/logs/crontab.log 2>&1
```

## Execução Manual

```bash
cd /home/tarcisio/Development/unipost-api
python brain/business_vectorizer.py
```

## Como Funciona

### 1. Descoberta de Índices
- Conecta ao ElasticSearch
- Lista todos os índices (exceto os de sistema)
- Processa cada índice sequencialmente

### 2. Processamento Incremental
- Mantém timestamp da última execução em `last_run.txt`
- Busca apenas documentos modificados desde a última execução
- Na primeira execução, processa todos os documentos

### 3. Extração de Texto
- Identifica campos de texto comuns: `message`, `content`, `text`, `body`, etc.
- Extrai recursivamente texto de estruturas JSON complexas
- Limita tamanho para compatibilidade com API do Gemini

### 4. Vetorização
- Gera embeddings usando Google Gemini
- Cria hash único para cada documento (controle de duplicatas)
- Salva no banco com metadados completos

### 5. Metadados Salvos

```json
{
  "elasticsearch_id": "doc_123",
  "elasticsearch_index": "company_logs", 
  "elasticsearch_score": 1.0,
  "document_hash": "abc123def456",
  "source_fields": ["message", "@timestamp", "level"],
  "processed_at": "2025-01-01T10:00:00",
  "original_source": {...}
}
```

## Arquivos de Log

- **`business_brain.log`**: Log principal do script
- **`crontab.log`**: Log das execuções via crontab
- **`last_run.txt`**: Timestamp da última execução

## Monitoramento

### Verificar Status do Crontab

```bash
crontab -l                    # Lista tarefas
tail -f brain/crontab.log    # Acompanha logs
tail -f brain/business_brain.log # Logs detalhados
```

### Verificar Embeddings no Banco

```bash
python manage.py shell
>>> from embeddings.models import Embedding
>>> Embedding.objects.filter(origin='business_brain').count()
>>> Embedding.objects.filter(origin='business_brain').last()
```

## Solução de Problemas

### ElasticSearch não conecta
- Verifique configurações de host/porta no `.env`
- Teste conectividade: `curl http://elasticsearch_host:9200`
- Verifique credenciais se usar autenticação

### Erro de API do Gemini
- Verifique `GOOGLE_GEMINI_API_KEY`
- Consulte limites de quota da API
- Verifique logs para erros específicos

### Crontab não executa
- Verifique permissões: `chmod +x business_vectorizer.py`
- Teste execução manual primeiro
- Verifique logs em `crontab.log`