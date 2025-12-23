#!/bin/bash
################################################################################
# SCRIPT DE INICIALIZAÇÃO - DEPLOY P0
# DOUTORA IA/OAB - JURIS_IA_CORE_V1
################################################################################
# Uso: bash scripts/deploy_p0_init.sh
# Descrição: Valida ambiente e inicia serviços Docker para deploy P0
################################################################################

set -e  # Parar em caso de erro
set -u  # Parar se variável indefinida

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/LOGS_DEPLOY_P0.txt"

################################################################################
# FUNÇÕES AUXILIARES
################################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_section() {
    echo "" | tee -a "$LOG_FILE"
    echo "================================================================================" | tee -a "$LOG_FILE"
    echo "$1" | tee -a "$LOG_FILE"
    echo "================================================================================" | tee -a "$LOG_FILE"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log "❌ ERRO: $1 não encontrado"
        exit 1
    fi
    log "✓ $1 disponível"
}

################################################################################
# VALIDAÇÃO DE AMBIENTE
################################################################################

log_section "ETAPA 13.1.1 - VALIDAÇÃO DE PRÉ-REQUISITOS"

cd "$PROJECT_ROOT"

# Verificar comandos necessários
check_command docker
check_command docker-compose

# Verificar Docker daemon
log "Verificando Docker daemon..."
if ! docker info > /dev/null 2>&1; then
    log "❌ BLOQUEADOR: Docker daemon não está respondendo"
    log "   Ação: Inicie Docker Desktop e aguarde 1-2 minutos"
    exit 1
fi
log "✓ Docker daemon OK"

# Verificar arquivo .env
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log "❌ BLOQUEADOR: Arquivo .env não encontrado"
    exit 1
fi
log "✓ Arquivo .env OK"

################################################################################
# INICIALIZAÇÃO DE SERVIÇOS
################################################################################

log_section "ETAPA 13.1.2 - INICIALIZAÇÃO DE SERVIÇOS DOCKER"

# Parar containers existentes
log "Parando containers existentes (se houver)..."
docker-compose down || true

# Criar rede se não existir
log "Criando rede juris_ia_network..."
docker network create juris_ia_network 2>/dev/null || log "  (rede já existe)"

# Iniciar PostgreSQL
log_section "INICIANDO: PostgreSQL + pgvector"
docker-compose up -d postgres
log "Aguardando PostgreSQL ficar healthy (até 60s)..."
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker-compose ps postgres | grep -q "healthy"; then
        log "✓ PostgreSQL healthy"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -n "."
done
if [ $ELAPSED -ge $TIMEOUT ]; then
    log "❌ TIMEOUT: PostgreSQL não ficou healthy em ${TIMEOUT}s"
    exit 1
fi

# Iniciar Redis
log_section "INICIANDO: Redis"
docker-compose up -d redis
log "Aguardando Redis ficar healthy (até 30s)..."
TIMEOUT=30
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker-compose ps redis | grep -q "healthy"; then
        log "✓ Redis healthy"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -n "."
done
if [ $ELAPSED -ge $TIMEOUT ]; then
    log "❌ TIMEOUT: Redis não ficou healthy em ${TIMEOUT}s"
    exit 1
fi

# Iniciar Ollama
log_section "INICIANDO: Ollama (GPU)"
docker-compose up -d ollama
log "Aguardando Ollama ficar healthy (até 60s)..."
TIMEOUT=60
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker-compose ps ollama | grep -q "healthy"; then
        log "✓ Ollama healthy"
        break
    fi
    sleep 2
    ELAPSED=$((ELAPSED + 2))
    echo -n "."
done
if [ $ELAPSED -ge $TIMEOUT ]; then
    log "❌ TIMEOUT: Ollama não ficou healthy em ${TIMEOUT}s"
    exit 1
fi

################################################################################
# DOWNLOAD DE MODELOS
################################################################################

log_section "ETAPA 13.1.3 - DOWNLOAD DE MODELOS IA"

# Iniciar ollama_init para download de modelos
log "Iniciando download de modelos (nomic-embed-text, llama3.1:8b-instruct-q8_0)..."
log "  Isso pode levar 5-15 minutos dependendo da conexão..."
docker-compose up ollama_init

log "✓ Modelos baixados com sucesso"

################################################################################
# VALIDAÇÃO DE CONECTIVIDADE
################################################################################

log_section "ETAPA 13.1.4 - VALIDAÇÃO DE CONECTIVIDADE"

# Testar PostgreSQL
log "Testando conexão PostgreSQL..."
docker exec juris_ia_postgres psql -U juris_ia_user -d juris_ia -c "SELECT version();" > /dev/null
log "✓ PostgreSQL conectado"

# Testar Redis
log "Testando conexão Redis..."
docker exec juris_ia_redis redis-cli PING | grep -q "PONG"
log "✓ Redis conectado"

# Testar Ollama
log "Testando Ollama API..."
docker exec juris_ia_ollama curl -f http://localhost:11434/api/tags > /dev/null
log "✓ Ollama API respondendo"

################################################################################
# VALIDAÇÃO DE MODELOS
################################################################################

log_section "ETAPA 13.1.5 - VALIDAÇÃO DE MODELOS"

log "Verificando modelos disponíveis no Ollama..."
MODELS=$(docker exec juris_ia_ollama ollama list)
echo "$MODELS" | tee -a "$LOG_FILE"

if echo "$MODELS" | grep -q "nomic-embed-text"; then
    log "✓ Modelo de embedding (nomic-embed-text) disponível"
else
    log "❌ Modelo de embedding NÃO encontrado"
    exit 1
fi

if echo "$MODELS" | grep -q "llama3.1:8b-instruct-q8_0"; then
    log "✓ Modelo LLM (llama3.1:8b-instruct-q8_0) disponível"
else
    log "❌ Modelo LLM NÃO encontrado"
    exit 1
fi

################################################################################
# RESUMO
################################################################################

log_section "ETAPA 13.1 - RESUMO"

log "✓ Docker daemon: OK"
log "✓ PostgreSQL: RODANDO (healthy)"
log "✓ Redis: RODANDO (healthy)"
log "✓ Ollama: RODANDO (healthy)"
log "✓ Modelo embedding: nomic-embed-text"
log "✓ Modelo LLM: llama3.1:8b-instruct-q8_0"
log ""
log "STATUS: ETAPA 13.1 CONCLUÍDA COM SUCESSO"
log ""
log "PRÓXIMOS PASSOS:"
log "  1. Executar migrations: bash scripts/deploy_p0_migrations.sh"
log "  2. Ingerir dados: bash scripts/deploy_p0_ingest.sh"
log "  3. Executar testes: bash scripts/deploy_p0_tests.sh"
log ""

################################################################################
# FIM
################################################################################
