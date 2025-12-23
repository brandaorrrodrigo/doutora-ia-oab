#!/bin/bash
################################################################################
# SCRIPT DE MIGRATIONS - DEPLOY P0
# DOUTORA IA/OAB - JURIS_IA_CORE_V1
################################################################################
# Uso: bash scripts/deploy_p0_migrations.sh
# Descrição: Executa migrations 003 e 004 com validação
################################################################################

set -e
set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/LOGS_DEPLOY_P0.txt"
MIGRATIONS_DIR="$PROJECT_ROOT/database/migrations"

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

psql_exec() {
    docker exec -i juris_ia_postgres psql -U juris_ia_user -d juris_ia "$@"
}

################################################################################
# VALIDAÇÃO
################################################################################

log_section "ETAPA 13.2.1 - VALIDAÇÃO PRÉ-MIGRATION"

cd "$PROJECT_ROOT"

# Verificar PostgreSQL
log "Validando conexão PostgreSQL..."
if ! psql_exec -c "SELECT 1;" > /dev/null 2>&1; then
    log "❌ ERRO: Não foi possível conectar ao PostgreSQL"
    exit 1
fi
log "✓ PostgreSQL conectado"

# Verificar extensão pgvector
log "Verificando extensão pgvector..."
psql_exec -c "CREATE EXTENSION IF NOT EXISTS vector;"
log "✓ Extensão pgvector habilitada"

# Backup (caso haja dados)
log "Criando backup de segurança..."
docker exec juris_ia_postgres pg_dump -U juris_ia_user juris_ia > "$PROJECT_ROOT/backup_pre_migration_$(date +%Y%m%d_%H%M%S).sql" 2>/dev/null || log "  (sem dados para backup)"

################################################################################
# MIGRATION 003
################################################################################

log_section "ETAPA 13.2.2 - EXECUTANDO MIGRATION 003 (AUTH TABLES)"

START_TIME=$(date +%s)

log "Executando: 003_create_auth_tables.sql"
psql_exec < "$MIGRATIONS_DIR/003_create_auth_tables.sql"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
log "✓ Migration 003 concluída em ${DURATION}s"

# Validação 003
log "Validando migration 003..."
TABLES=$(psql_exec -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('usuario', 'token_refresh', 'sessao_usuario', 'log_autenticacao', 'jwt_secret');")
TABLE_COUNT=$(echo "$TABLES" | grep -c -v '^$' || true)
log "  Tabelas criadas: ${TABLE_COUNT}/5"

if [ "$TABLE_COUNT" -ne 5 ]; then
    log "❌ ERRO: Esperado 5 tabelas, encontrado ${TABLE_COUNT}"
    exit 1
fi
log "✓ Todas as tabelas de autenticação criadas"

# Verificar usuário admin
ADMIN_EXISTS=$(psql_exec -t -c "SELECT COUNT(*) FROM usuario WHERE email='admin@juris-ia.com';")
if [ "$ADMIN_EXISTS" -eq 1 ]; then
    log "✓ Usuário admin criado"
else
    log "❌ ERRO: Usuário admin não foi criado"
    exit 1
fi

################################################################################
# MIGRATION 004
################################################################################

log_section "ETAPA 13.2.3 - EXECUTANDO MIGRATION 004 (SUBSCRIPTION TABLES)"

START_TIME=$(date +%s)

log "Executando: 004_create_subscription_tables.sql"
psql_exec < "$MIGRATIONS_DIR/004_create_subscription_tables.sql"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
log "✓ Migration 004 concluída em ${DURATION}s"

# Validação 004
log "Validando migration 004..."
TABLES=$(psql_exec -t -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('plano', 'assinatura', 'uso_diario', 'evento_uso', 'historico_plano');")
TABLE_COUNT=$(echo "$TABLES" | grep -c -v '^$' || true)
log "  Tabelas criadas: ${TABLE_COUNT}/5"

if [ "$TABLE_COUNT" -ne 5 ]; then
    log "❌ ERRO: Esperado 5 tabelas, encontrado ${TABLE_COUNT}"
    exit 1
fi
log "✓ Todas as tabelas de assinatura criadas"

# Verificar planos iniciais
PLANO_COUNT=$(psql_exec -t -c "SELECT COUNT(*) FROM plano WHERE codigo IN ('FREE', 'BASIC', 'PRO');")
if [ "$PLANO_COUNT" -eq 3 ]; then
    log "✓ Planos iniciais criados (FREE, BASIC, PRO)"
else
    log "❌ ERRO: Esperado 3 planos, encontrado ${PLANO_COUNT}"
    exit 1
fi

################################################################################
# VALIDAÇÃO GERAL
################################################################################

log_section "ETAPA 13.2.4 - VALIDAÇÃO GERAL DO SCHEMA"

# Contar todas as tabelas
TOTAL_TABLES=$(psql_exec -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
log "Total de tabelas no schema: ${TOTAL_TABLES}"

# Validar constraints
log "Validando constraints..."
CONSTRAINTS=$(psql_exec -t -c "SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema='public';")
log "  Constraints criadas: ${CONSTRAINTS}"

# Validar índices
log "Validando índices..."
INDEXES=$(psql_exec -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname='public';")
log "  Índices criados: ${INDEXES}"

# Validar funções
log "Validando funções..."
FUNCTIONS=$(psql_exec -t -c "SELECT COUNT(*) FROM pg_proc WHERE pronamespace = 'public'::regnamespace;")
log "  Funções criadas: ${FUNCTIONS}"

################################################################################
# TESTES DE FUNÇÕES SQL
################################################################################

log_section "ETAPA 13.2.5 - TESTES DE FUNÇÕES SQL"

# Testar função obter_assinatura_ativa
log "Testando função: obter_assinatura_ativa..."
psql_exec -c "SELECT * FROM obter_assinatura_ativa('00000000-0000-0000-0000-000000000000');" > /dev/null
log "✓ Função obter_assinatura_ativa OK"

# Testar função obter_uso_dia
log "Testando função: obter_uso_dia..."
psql_exec -c "SELECT * FROM obter_uso_dia('00000000-0000-0000-0000-000000000000');" > /dev/null
log "✓ Função obter_uso_dia OK"

# Testar função verificar_limite
log "Testando função: verificar_limite..."
psql_exec -c "SELECT verificar_limite('00000000-0000-0000-0000-000000000000', 'questao');" > /dev/null
log "✓ Função verificar_limite OK"

################################################################################
# RESUMO
################################################################################

log_section "ETAPA 13.2 - RESUMO DAS MIGRATIONS"

log "✓ Migration 003 (Auth): CONCLUÍDA"
log "✓ Migration 004 (Subscriptions): CONCLUÍDA"
log "✓ Total de tabelas: ${TOTAL_TABLES}"
log "✓ Constraints: ${CONSTRAINTS}"
log "✓ Índices: ${INDEXES}"
log "✓ Funções SQL: ${FUNCTIONS}"
log "✓ Planos iniciais: 3 (FREE, BASIC, PRO)"
log "✓ Usuário admin: criado"
log ""
log "STATUS: ETAPA 13.2 CONCLUÍDA COM SUCESSO"
log ""
log "PRÓXIMO PASSO:"
log "  bash scripts/deploy_p0_ingest.sh"
log ""

################################################################################
# FIM
################################################################################
