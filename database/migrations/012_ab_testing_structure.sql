-- ================================================================================
-- MIGRATION 012: A/B TESTING STRUCTURE
-- ================================================================================
-- Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing Avançado
-- Data: 2025-12-19
-- Objetivo: Implementar estrutura para testes A/B de pricing e limites
-- ================================================================================

BEGIN;

-- ================================================================================
-- TABELA DE EXPERIMENTOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS ab_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    enabled BOOLEAN DEFAULT false,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    target_plan_codigo VARCHAR(50),  -- Plano alvo do experimento (ex: OAB_MENSAL)
    control_group_percentage DECIMAL(5,2) DEFAULT 50.00,  -- % no grupo A (controle)
    variant_group_percentage DECIMAL(5,2) DEFAULT 50.00,  -- % no grupo B (variante)
    assignment_strategy VARCHAR(50) DEFAULT 'hash_modulo',  -- hash_modulo, random, manual
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ab_experiments_enabled
ON ab_experiments(enabled, experiment_name);

COMMENT ON TABLE ab_experiments IS 'Definição de experimentos A/B para pricing e limites';
COMMENT ON COLUMN ab_experiments.assignment_strategy IS 'hash_modulo: consistente por user_id, random: aleatório, manual: atribuição manual';
COMMENT ON COLUMN ab_experiments.metadata IS 'Configurações do experimento: limites, mensagens, etc.';

-- ================================================================================
-- TABELA DE ATRIBUIÇÃO DE GRUPOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS ab_user_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    group_name VARCHAR(50) NOT NULL,  -- 'control' ou 'variant'
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(experiment_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_ab_user_groups_user
ON ab_user_groups(user_id, experiment_id);

CREATE INDEX IF NOT EXISTS idx_ab_user_groups_experiment
ON ab_user_groups(experiment_id, group_name);

COMMENT ON TABLE ab_user_groups IS 'Atribuição de usuários a grupos de experimentos A/B';
COMMENT ON COLUMN ab_user_groups.group_name IS 'control: grupo A (padrão), variant: grupo B (variação)';

-- ================================================================================
-- TABELA DE MÉTRICAS DO EXPERIMENTO
-- ================================================================================

CREATE TABLE IF NOT EXISTS ab_experiment_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    group_name VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,  -- conversion, retention_7d, sessions_per_day, blocks_per_day, upgrade_click
    metric_value DECIMAL(10,2),
    metric_date DATE DEFAULT CURRENT_DATE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ab_metrics_experiment
ON ab_experiment_metrics(experiment_id, metric_name, metric_date);

CREATE INDEX IF NOT EXISTS idx_ab_metrics_user
ON ab_experiment_metrics(user_id, experiment_id);

COMMENT ON TABLE ab_experiment_metrics IS 'Métricas coletadas durante experimentos A/B';
COMMENT ON COLUMN ab_experiment_metrics.metric_name IS 'Nome da métrica: conversion, retention_7d, sessions_per_day, blocks_per_day, upgrade_click, etc.';

-- ================================================================================
-- FUNÇÃO: Atribuir usuário a grupo de experimento
-- ================================================================================

CREATE OR REPLACE FUNCTION atribuir_grupo_experimento(
    p_experiment_name VARCHAR(100),
    p_user_id UUID
)
RETURNS TABLE(
    group_assigned VARCHAR(50),
    is_new_assignment BOOLEAN
) AS $$
DECLARE
    v_experiment_id UUID;
    v_experiment_enabled BOOLEAN;
    v_assignment_strategy VARCHAR(50);
    v_control_pct DECIMAL(5,2);
    v_existing_group VARCHAR(50);
    v_hash_value INTEGER;
    v_assigned_group VARCHAR(50);
BEGIN
    -- Buscar experimento
    SELECT id, enabled, assignment_strategy, control_group_percentage
    INTO v_experiment_id, v_experiment_enabled, v_assignment_strategy, v_control_pct
    FROM ab_experiments
    WHERE experiment_name = p_experiment_name
    LIMIT 1;

    -- Se experimento não existe ou está desabilitado, retornar NULL
    IF NOT FOUND OR NOT v_experiment_enabled THEN
        RETURN QUERY SELECT NULL::VARCHAR(50), false::BOOLEAN;
        RETURN;
    END IF;

    -- Verificar se usuário já tem grupo atribuído
    SELECT group_name INTO v_existing_group
    FROM ab_user_groups
    WHERE experiment_id = v_experiment_id
      AND user_id = p_user_id
    LIMIT 1;

    IF FOUND THEN
        -- Já tem grupo, retornar existente
        RETURN QUERY SELECT v_existing_group, false::BOOLEAN;
        RETURN;
    END IF;

    -- Nova atribuição baseada na estratégia
    IF v_assignment_strategy = 'hash_modulo' THEN
        -- Hash consistente do user_id
        v_hash_value := ('x' || substring(p_user_id::text, 1, 8))::bit(32)::int;
        v_hash_value := ABS(v_hash_value) % 100;

        IF v_hash_value < v_control_pct THEN
            v_assigned_group := 'control';
        ELSE
            v_assigned_group := 'variant';
        END IF;

    ELSIF v_assignment_strategy = 'random' THEN
        -- Aleatório
        IF RANDOM() * 100 < v_control_pct THEN
            v_assigned_group := 'control';
        ELSE
            v_assigned_group := 'variant';
        END IF;

    ELSE
        -- Estratégia desconhecida, default para controle
        v_assigned_group := 'control';
    END IF;

    -- Inserir atribuição
    INSERT INTO ab_user_groups (experiment_id, user_id, group_name)
    VALUES (v_experiment_id, p_user_id, v_assigned_group);

    -- Retornar grupo atribuído
    RETURN QUERY SELECT v_assigned_group, true::BOOLEAN;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FUNÇÃO: Registrar métrica de experimento
-- ================================================================================

CREATE OR REPLACE FUNCTION registrar_metrica_experimento(
    p_experiment_name VARCHAR(100),
    p_user_id UUID,
    p_metric_name VARCHAR(100),
    p_metric_value DECIMAL(10,2),
    p_metadata JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_experiment_id UUID;
    v_group_name VARCHAR(50);
BEGIN
    -- Buscar experimento
    SELECT id INTO v_experiment_id
    FROM ab_experiments
    WHERE experiment_name = p_experiment_name
      AND enabled = true
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN false;
    END IF;

    -- Buscar grupo do usuário
    SELECT group_name INTO v_group_name
    FROM ab_user_groups
    WHERE experiment_id = v_experiment_id
      AND user_id = p_user_id
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN false;
    END IF;

    -- Inserir métrica
    INSERT INTO ab_experiment_metrics (
        experiment_id,
        user_id,
        group_name,
        metric_name,
        metric_value,
        metadata
    ) VALUES (
        v_experiment_id,
        p_user_id,
        v_group_name,
        p_metric_name,
        p_metric_value,
        p_metadata
    );

    RETURN true;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FUNÇÃO: Obter configuração de experimento para usuário
-- ================================================================================

CREATE OR REPLACE FUNCTION obter_config_experimento(
    p_experiment_name VARCHAR(100),
    p_user_id UUID
)
RETURNS TABLE(
    group_name VARCHAR(50),
    experiment_metadata JSONB
) AS $$
DECLARE
    v_experiment_id UUID;
    v_metadata JSONB;
    v_group VARCHAR(50);
BEGIN
    -- Buscar experimento
    SELECT id, metadata INTO v_experiment_id, v_metadata
    FROM ab_experiments
    WHERE experiment_name = p_experiment_name
      AND enabled = true
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN QUERY SELECT NULL::VARCHAR(50), NULL::JSONB;
        RETURN;
    END IF;

    -- Buscar grupo do usuário
    SELECT aug.group_name INTO v_group
    FROM ab_user_groups aug
    WHERE aug.experiment_id = v_experiment_id
      AND aug.user_id = p_user_id
    LIMIT 1;

    -- Retornar grupo e metadata
    RETURN QUERY SELECT v_group, v_metadata;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- INSERIR EXPERIMENTO EXEMPLO: OAB Mensal - Limites Ajustados
-- ================================================================================

INSERT INTO ab_experiments (
    experiment_name,
    description,
    enabled,
    target_plan_codigo,
    control_group_percentage,
    variant_group_percentage,
    assignment_strategy,
    metadata
) VALUES (
    'oab_mensal_limite_ajustado_2025_q1',
    'Teste A/B: Grupo A = 3 sessões/dia (padrão), Grupo B = 4 sessões/dia + mensagem de destaque Semestral',
    false,  -- Desabilitado por padrão
    'OAB_MENSAL',
    50.00,
    50.00,
    'hash_modulo',
    jsonb_build_object(
        'control', jsonb_build_object(
            'limite_sessoes_dia', 3,
            'limite_questoes_por_sessao', 15,
            'acesso_relatorio_tipo', 'completo',
            'permite_estudo_continuo', true,
            'mensagem_upsell', 'padrão'
        ),
        'variant', jsonb_build_object(
            'limite_sessoes_dia', 4,
            'limite_questoes_por_sessao', 15,
            'acesso_relatorio_tipo', 'completo',
            'permite_estudo_continuo', true,
            'mensagem_upsell', 'destaque_semestral'
        ),
        'metricas_alvo', ARRAY[
            'conversion_to_semestral',
            'retention_7d',
            'sessions_per_day',
            'blocks_per_day',
            'upgrade_click'
        ]
    )
)
ON CONFLICT (experiment_name) DO UPDATE
SET
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Comentários
COMMENT ON FUNCTION atribuir_grupo_experimento IS 'Atribui usuário a grupo de experimento (control ou variant) de forma consistente';
COMMENT ON FUNCTION registrar_metrica_experimento IS 'Registra métrica de usuário em experimento ativo';
COMMENT ON FUNCTION obter_config_experimento IS 'Obtém configuração do experimento para usuário específico';

COMMIT;

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
\echo 'Migration 012: A/B Testing Structure implementado com sucesso'
