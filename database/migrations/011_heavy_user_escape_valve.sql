-- ================================================================================
-- MIGRATION 011: HEAVY USER ESCAPE VALVE
-- ================================================================================
-- Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
-- Data: 2025-12-19
-- Objetivo: Implementar válvula de escape automática para heavy users (Semestral)
-- ================================================================================

BEGIN;

-- ================================================================================
-- TABELA DE LOG DE ATIVAÇÃO DE ESCAPE
-- ================================================================================

CREATE TABLE IF NOT EXISTS heavy_user_escape_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    plano_codigo VARCHAR(50) NOT NULL,
    data_ativacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criterio_atendido VARCHAR(255),
    sessoes_ultimos_7_dias INTEGER,
    sessoes_extras_concedidas INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_heavy_user_escape_user
ON heavy_user_escape_log(user_id, data_ativacao DESC);

CREATE INDEX IF NOT EXISTS idx_heavy_user_escape_data
ON heavy_user_escape_log(data_ativacao DESC);

-- Comentários
COMMENT ON TABLE heavy_user_escape_log IS 'Log de ativações da válvula de escape para heavy users';
COMMENT ON COLUMN heavy_user_escape_log.criterio_atendido IS 'Critério que ativou o escape (ex: 80%_uso_7dias)';
COMMENT ON COLUMN heavy_user_escape_log.sessoes_extras_concedidas IS 'Quantas sessões extras foram liberadas';

-- ================================================================================
-- FUNÇÃO: Verificar e ativar escape para heavy user
-- ================================================================================

CREATE OR REPLACE FUNCTION verificar_heavy_user_escape(
    p_user_id UUID
)
RETURNS TABLE(
    escape_ativado BOOLEAN,
    motivo TEXT,
    sessoes_extras INTEGER,
    sessoes_7dias INTEGER
) AS $$
DECLARE
    v_plano_codigo VARCHAR(50);
    v_permite_extras BOOLEAN;
    v_sessoes_extras_disponiveis INTEGER;
    v_limite_sessoes_dia INTEGER;
    v_sessoes_7dias INTEGER;
    v_sessoes_hoje INTEGER;
    v_criterio_80_pct INTEGER;
    v_ja_ativado_hoje BOOLEAN;
BEGIN
    -- Buscar informações do plano
    SELECT
        p.codigo,
        p.sessoes_extras_condicionais > 0,
        p.sessoes_extras_condicionais,
        p.limite_sessoes_dia
    INTO
        v_plano_codigo,
        v_permite_extras,
        v_sessoes_extras_disponiveis,
        v_limite_sessoes_dia
    FROM assinatura a
    INNER JOIN plano p ON a.plano_id = p.id
    WHERE a.user_id = p_user_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.data_inicio DESC
    LIMIT 1;

    -- Se não encontrou plano ou plano não permite extras
    IF NOT FOUND OR NOT v_permite_extras THEN
        RETURN QUERY SELECT
            false::boolean,
            'Plano não permite sessões extras condicionais'::text,
            0::integer,
            0::integer;
        RETURN;
    END IF;

    -- Se plano não é SEMESTRAL, não ativa
    IF v_plano_codigo != 'OAB_SEMESTRAL' THEN
        RETURN QUERY SELECT
            false::boolean,
            'Escape disponível apenas para plano Semestral'::text,
            0::integer,
            0::integer;
        RETURN;
    END IF;

    -- Verificar se já foi ativado hoje
    SELECT EXISTS(
        SELECT 1
        FROM heavy_user_escape_log
        WHERE user_id = p_user_id
          AND DATE(data_ativacao AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
    ) INTO v_ja_ativado_hoje;

    IF v_ja_ativado_hoje THEN
        RETURN QUERY SELECT
            false::boolean,
            'Escape já ativado hoje'::text,
            0::integer,
            0::integer;
        RETURN;
    END IF;

    -- Contar sessões dos últimos 7 dias (que contam no limite)
    SELECT COUNT(*)::INTEGER INTO v_sessoes_7dias
    FROM sessao_estudo
    WHERE user_id = p_user_id
      AND iniciado_em >= CURRENT_DATE - INTERVAL '6 days'
      AND conta_limite_diario = true;

    -- Calcular critério 80% (limite diário * 7 dias * 0.8)
    v_criterio_80_pct := (v_limite_sessoes_dia * 7 * 0.8)::INTEGER;

    -- Verificar se atende critério de heavy user
    IF v_sessoes_7dias < v_criterio_80_pct THEN
        RETURN QUERY SELECT
            false::boolean,
            format('Não atingiu critério heavy user (%s/%s sessões)',
                   v_sessoes_7dias, v_criterio_80_pct)::text,
            0::integer,
            v_sessoes_7dias::integer;
        RETURN;
    END IF;

    -- Contar sessões de hoje
    SELECT COUNT(*)::INTEGER INTO v_sessoes_hoje
    FROM sessao_estudo
    WHERE user_id = p_user_id
      AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
      AND conta_limite_diario = true;

    -- Verificar se já atingiu limite padrão
    IF v_sessoes_hoje < v_limite_sessoes_dia THEN
        RETURN QUERY SELECT
            false::boolean,
            'Ainda não atingiu limite padrão de sessões'::text,
            0::integer,
            v_sessoes_7dias::integer;
        RETURN;
    END IF;

    -- ATIVAR ESCAPE!
    -- Registrar no log
    INSERT INTO heavy_user_escape_log (
        user_id,
        plano_codigo,
        criterio_atendido,
        sessoes_ultimos_7_dias,
        sessoes_extras_concedidas,
        metadata
    ) VALUES (
        p_user_id,
        v_plano_codigo,
        '80%_uso_7dias',
        v_sessoes_7dias,
        v_sessoes_extras_disponiveis,
        jsonb_build_object(
            'limite_sessoes_dia', v_limite_sessoes_dia,
            'sessoes_hoje', v_sessoes_hoje,
            'criterio_80_pct', v_criterio_80_pct
        )
    );

    -- Retornar sucesso
    RETURN QUERY SELECT
        true::boolean,
        format('Heavy user detectado! +%s sessões extra(s) liberada(s)',
               v_sessoes_extras_disponiveis)::text,
        v_sessoes_extras_disponiveis::integer,
        v_sessoes_7dias::integer;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FUNÇÃO: Verificar se usuário pode usar sessão extra hoje
-- ================================================================================

CREATE OR REPLACE FUNCTION pode_usar_sessao_extra_heavy_user(
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_escape_ativado BOOLEAN;
BEGIN
    -- Verificar se escape foi ativado hoje
    SELECT EXISTS(
        SELECT 1
        FROM heavy_user_escape_log
        WHERE user_id = p_user_id
          AND DATE(data_ativacao AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
    ) INTO v_escape_ativado;

    RETURN v_escape_ativado;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FLAG GLOBAL DE ATIVAÇÃO/DESATIVAÇÃO
-- ================================================================================

CREATE TABLE IF NOT EXISTS feature_flags (
    flag_name VARCHAR(100) PRIMARY KEY,
    enabled BOOLEAN DEFAULT true,
    description TEXT,
    metadata JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir flag do heavy user escape valve
INSERT INTO feature_flags (flag_name, enabled, description, metadata)
VALUES (
    'heavy_user_escape_valve',
    true,
    'Válvula de escape automática para heavy users do plano Semestral',
    jsonb_build_object(
        'criterio', '80% uso em 7 dias',
        'planos_aplicaveis', ARRAY['OAB_SEMESTRAL'],
        'sessoes_extras', 1,
        'reversivel', true
    )
)
ON CONFLICT (flag_name) DO UPDATE
SET
    enabled = EXCLUDED.enabled,
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = NOW();

-- Comentários
COMMENT ON TABLE feature_flags IS 'Flags de features que podem ser ativadas/desativadas';
COMMENT ON FUNCTION verificar_heavy_user_escape IS 'Verifica e ativa automaticamente escape para heavy users';
COMMENT ON FUNCTION pode_usar_sessao_extra_heavy_user IS 'Verifica se usuário pode usar sessão extra de heavy user hoje';

COMMIT;

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
\echo 'Migration 011: Heavy User Escape Valve implementado com sucesso'
