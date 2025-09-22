#!/bin/bash

set -e

if [ -f .env ]; then
  set -a
  source .env
  set +a
else
  echo "Arquivo .env não encontrado!"
  exit 1
fi

echo "Aguardando banco de dados em $DB_HOST:$DB_PORT..."

until nc -z -v -w30 "$DB_HOST" "$DB_PORT"; do
  echo "Aguardando banco de dados..."
  sleep 1
done

echo "Banco de dados está disponível!"

export PGPASSWORD="$DB_PASSWORD"

psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
DO \$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_database WHERE datname = '$DB_NAME'
   ) THEN
      CREATE DATABASE "$DB_NAME"
      WITH OWNER = "$DB_USER"
      ENCODING = 'UTF8'
      LC_COLLATE = 'pt_BR.UTF-8'
      LC_CTYPE = 'pt_BR.UTF-8'
      TABLESPACE = pg_default
      CONNECTION LIMIT = -1
      IS_TEMPLATE = false;
   END IF;
END
\$\$;
EOF

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_superuser
python manage.py create_members_group

echo "Instalando MCP SDK..."
npm install -g @modelcontextprotocol/sdk

echo "Executando vetorização do Elasticsearch em background..."
(cd brain && python business_vectorizer.py >vectorizer.log 2>&1) &
VECTORIZER_PID=$!
echo "Business Vectorizer iniciado com PID: $VECTORIZER_PID"
echo "Logs da vetorização: /app/brain/vectorizer.log"

echo "Iniciando robô de monitoramento de posts em background..."
mkdir -p unipost_automation/logs
nohup python unipost_automation/src/bot/async_bot.py > unipost_automation/logs/async_bot.log 2>&1 &
ASYNC_BOT_PID=$!
echo "Async Bot iniciado com PID: $ASYNC_BOT_PID"
echo "Logs do async bot: /app/unipost_automation/logs/async_bot.log"

gunicorn --bind 0.0.0.0:8005 --workers 4 --timeout 120 app.wsgi:application
