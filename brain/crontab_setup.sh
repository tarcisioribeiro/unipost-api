#!/bin/bash
# Script para configurar crontab do Business Vectorizer

# Diretório do projeto
PROJECT_DIR="/home/tarcisio/Development/unipost-api"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"
SCRIPT_PATH="$PROJECT_DIR/brain/business_vectorizer.py"
LOG_PATH="$PROJECT_DIR/brain/crontab.log"

# Verifica se o ambiente virtual existe
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Erro: Ambiente virtual não encontrado em $PYTHON_PATH"
    echo "Execute: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Verifica se o script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Erro: Script não encontrado em $SCRIPT_PATH"
    exit 1
fi

# Linha do crontab (executa a cada 10 minutos)
CRON_LINE="*/10 * * * * cd $PROJECT_DIR && $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1"

echo "Configurando crontab para Business Vectorizer..."
echo "Linha do crontab: $CRON_LINE"

# Backup do crontab atual
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Adiciona nova linha ao crontab (remove duplicatas se existirem)
(crontab -l 2>/dev/null | grep -v "business_vectorizer.py"; echo "$CRON_LINE") | crontab -

echo "Crontab configurado com sucesso!"
echo "O Business Vectorizer será executado a cada 10 minutos."
echo "Logs serão salvos em: $LOG_PATH"
echo ""
echo "Para verificar o crontab: crontab -l"
echo "Para remover o crontab: crontab -r"
echo "Para editar o crontab: crontab -e"