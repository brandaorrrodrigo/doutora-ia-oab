-- ================================================================================
-- MIGRATION 008: ADICIONAR LIMITES DE SESSÃO E ESTUDO CONTÍNUO
-- ================================================================================
-- Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
-- Data: 2025-12-19
-- Objetivo: Adicionar campos para controle fino de sessões e limites pedagógicos
-- ================================================================================

BEGIN;

-- ================================================================================
-- ADICIONAR CAMPOS DE LIMITES DE SESSÃO À TABELA PLANO
-- ================================================================================

-- Sessões e duração
ALTER TABLE plano ADD COLUMN IF NOT EXISTS limite_sessoes_dia INTEGER DEFAULT NULL;
ALTER TABLE plano ADD COLUMN IF NOT EXISTS duracao_maxima_sessao_minutos INTEGER DEFAULT NULL;
ALTER TABLE plano ADD COLUMN IF NOT EXISTS limite_questoes_por_sessao INTEGER DEFAULT NULL;

-- Estudo contínuo e extensões
ALTER TABLE plano ADD COLUMN IF NOT EXISTS permite_estudo_continuo BOOLEAN DEFAULT false;
ALTER TABLE plano ADD COLUMN IF NOT EXISTS permite_sessao_estendida BOOLEAN DEFAULT false;
ALTER TABLE plano ADD COLUMN IF NOT EXISTS sessoes_extras_condicionais INTEGER DEFAULT 0;

-- Relatórios
ALTER TABLE plano ADD COLUMN IF NOT EXISTS acesso_relatorio_tipo VARCHAR(20) DEFAULT 'nenhum';
-- Valores permitidos: 'nenhum', 'basico', 'completo'

-- Comentários dos novos campos
COMMENT ON COLUMN plano.limite_sessoes_dia IS 'Número máximo de sessões de estudo por dia (NULL = ilimitado)';
COMMENT ON COLUMN plano.duracao_maxima_sessao_minutos IS 'Duração máxima de uma sessão em minutos (NULL = ilimitado)';
COMMENT ON COLUMN plano.limite_questoes_por_sessao IS 'Número máximo de questões por sessão (NULL = ilimitado)';
COMMENT ON COLUMN plano.permite_estudo_continuo IS 'Se permite continuar estudando após finalizar sessão (revisão, leitura normativa)';
COMMENT ON COLUMN plano.permite_sessao_estendida IS 'Se permite sessões longas que não consomem sessão adicional';
COMMENT ON COLUMN plano.sessoes_extras_condicionais IS 'Número de sessões extras concedidas sob condições específicas (heavy users)';
COMMENT ON COLUMN plano.acesso_relatorio_tipo IS 'Tipo de relatório disponível: nenhum, basico, completo';

COMMIT;

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
\echo 'Migration 008: Campos de limites de sessão adicionados com sucesso'
