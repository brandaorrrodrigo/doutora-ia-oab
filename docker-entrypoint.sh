#!/bin/bash
set -e

echo "Iniciando JURIS-IA API..."
cd /app

# Aguardar PostgreSQL
echo "Aguardando PostgreSQL..."
sleep 5

# Iniciar aplicação
echo "Iniciando servidor..."
exec python -m uvicorn api.api_server:app --host 0.0.0.0 --port 8000 --reload
