-- ================================================================================
-- MIGRATION 009: ADICIONAR CAMPOS PARA SESSÕES ESPECIAIS
-- ================================================================================
-- Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
-- Data: 2025-12-19
-- Objetivo: Adicionar campos para controle de sessões longas e estudo contínuo
-- ================================================================================

BEGIN;

-- ================================================================================
-- ADICIONAR CAMPOS PARA SESSÃO ESTENDIDA E ESTUDO CONTÍNUO
-- ================================================================================

-- Indicador de estudo contínuo (revisão após sessão principal)
ALTER TABLE sessao_estudo ADD COLUMN IF NOT EXISTS modo_estudo_continuo BOOLEAN DEFAULT false;

-- Indicador de sessão estendida (não consome sessão adicional)
ALTER TABLE sessao_estudo ADD COLUMN IF NOT EXISTS sessao_estendida BOOLEAN DEFAULT false;

-- Referência à sessão principal (para sessões de estudo contínuo)
ALTER TABLE sessao_estudo ADD COLUMN IF NOT EXISTS sessao_principal_id UUID;

-- Indicador se conta ou não no limite diário
ALTER TABLE sessao_estudo ADD COLUMN IF NOT EXISTS conta_limite_diario BOOLEAN DEFAULT true;

-- Adicionar foreign key para sessao_principal_id
ALTER TABLE sessao_estudo
ADD CONSTRAINT fk_sessao_principal
FOREIGN KEY (sessao_principal_id)
REFERENCES sessao_estudo(id)
ON DELETE SET NULL;

-- Criar índice para buscar sessões relacionadas
CREATE INDEX IF NOT EXISTS idx_sessao_principal ON sessao_estudo(sessao_principal_id) WHERE sessao_principal_id IS NOT NULL;

-- Criar índice para filtrar sessões que contam no limite
CREATE INDEX IF NOT EXISTS idx_sessao_conta_limite ON sessao_estudo(user_id, conta_limite_diario, iniciado_em)
WHERE conta_limite_diario = true;

-- Comentários
COMMENT ON COLUMN sessao_estudo.modo_estudo_continuo IS 'Se true, é uma sessão de revisão/estudo que não consome limite diário (planos Mensal e Semestral)';
COMMENT ON COLUMN sessao_estudo.sessao_estendida IS 'Se true, é uma sessão longa que não conta como múltiplas sessões (apenas plano Semestral)';
COMMENT ON COLUMN sessao_estudo.sessao_principal_id IS 'ID da sessão principal à qual esta sessão de estudo contínuo está vinculada';
COMMENT ON COLUMN sessao_estudo.conta_limite_diario IS 'Se true, conta no limite diário de sessões (false para estudo contínuo e sessões extras)';

COMMIT;

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
\echo 'Migration 009: Campos de sessão especial adicionados com sucesso'
