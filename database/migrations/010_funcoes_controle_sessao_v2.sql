-- ================================================================================
-- MIGRATION 010: FUNÇÕES DE CONTROLE DE SESSÃO E LIMITES (V2)
-- ================================================================================
-- Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
-- Data: 2025-12-19
-- Objetivo: Implementar lógica de negócio para controle de sessões e limites
-- ================================================================================

BEGIN;

-- ================================================================================
-- FUNÇÃO: Verificar se usuário pode iniciar nova sessão
-- ================================================================================

CREATE OR REPLACE FUNCTION pode_iniciar_sessao(
    p_user_id UUID,
    p_modo_estudo_continuo BOOLEAN DEFAULT false
)
RETURNS TABLE(
    pode_iniciar BOOLEAN,
    motivo TEXT,
    sessoes_usadas INTEGER,
    sessoes_disponiveis INTEGER
) AS $$
DECLARE
    v_limite_sessoes INTEGER;
    v_permite_estudo_continuo BOOLEAN;
    v_sessoes_extras INTEGER;
    v_sessoes_hoje INTEGER;
BEGIN
    -- Buscar limites do plano do usuário
    SELECT
        p.limite_sessoes_dia,
        p.permite_estudo_continuo,
        p.sessoes_extras_condicionais
    INTO
        v_limite_sessoes,
        v_permite_estudo_continuo,
        v_sessoes_extras
    FROM assinatura a
    INNER JOIN plano p ON a.plano_id = p.id
    WHERE a.user_id = p_user_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.data_inicio DESC
    LIMIT 1;

    -- Se não tem assinatura ativa, não pode iniciar
    IF NOT FOUND THEN
        RETURN QUERY SELECT false::boolean, 'Nenhuma assinatura ativa encontrada'::text, 0::integer, 0::integer;
        RETURN;
    END IF;

    -- Se é modo estudo contínuo, sempre pode (não conta no limite)
    IF p_modo_estudo_continuo AND v_permite_estudo_continuo THEN
        RETURN QUERY SELECT true::boolean, 'Estudo contínuo permitido (não conta no limite)'::text, 0::integer, 999::integer;
        RETURN;
    END IF;

    -- Se plano não permite estudo contínuo mas usuário tentou
    IF p_modo_estudo_continuo AND NOT v_permite_estudo_continuo THEN
        RETURN QUERY SELECT false::boolean, 'Seu plano não permite estudo contínuo. Faça upgrade!'::text, 0::integer, 0::integer;
        RETURN;
    END IF;

    -- Contar sessões de hoje que contam no limite
    SELECT COUNT(*)::INTEGER INTO v_sessoes_hoje
    FROM sessao_estudo
    WHERE user_id = p_user_id
      AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
      AND conta_limite_diario = true;

    -- Verificar se ultrapassou limite
    IF v_sessoes_hoje >= (v_limite_sessoes + v_sessoes_extras) THEN
        RETURN QUERY SELECT
            false::boolean,
            'Limite de sessões diárias atingido. Continue amanhã ou estude conteúdo teórico!'::text,
            v_sessoes_hoje::integer,
            (v_limite_sessoes + v_sessoes_extras)::integer;
        RETURN;
    END IF;

    -- Pode iniciar sessão
    RETURN QUERY SELECT
        true::boolean,
        'Pode iniciar nova sessão'::text,
        v_sessoes_hoje::integer,
        (v_limite_sessoes + v_sessoes_extras)::integer;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FUNÇÃO: Obter estatísticas de uso diário
-- ================================================================================

CREATE OR REPLACE FUNCTION estatisticas_uso_diario(
    p_user_id UUID,
    p_data DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE(
    sessoes_total INTEGER,
    sessoes_que_contam INTEGER,
    sessoes_estudo_continuo INTEGER,
    questoes_total INTEGER,
    limite_sessoes INTEGER,
    limite_questoes INTEGER,
    sessoes_disponiveis INTEGER,
    questoes_disponiveis INTEGER,
    permite_estudo_continuo BOOLEAN,
    permite_sessao_estendida BOOLEAN
) AS $$
DECLARE
    v_limite_sessoes INTEGER;
    v_limite_questoes INTEGER;
    v_permite_estudo_continuo BOOLEAN;
    v_permite_sessao_estendida BOOLEAN;
    v_sessoes_extras INTEGER;
BEGIN
    -- Buscar limites do plano
    SELECT
        p.limite_sessoes_dia,
        p.limite_questoes_dia,
        p.permite_estudo_continuo,
        p.permite_sessao_estendida,
        p.sessoes_extras_condicionais
    INTO
        v_limite_sessoes,
        v_limite_questoes,
        v_permite_estudo_continuo,
        v_permite_sessao_estendida,
        v_sessoes_extras
    FROM assinatura a
    INNER JOIN plano p ON a.plano_id = p.id
    WHERE a.user_id = p_user_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.data_inicio DESC
    LIMIT 1;

    IF NOT FOUND THEN
        -- Se não tem plano ativo, retorna zeros
        RETURN QUERY SELECT
            0::integer, 0::integer, 0::integer, 0::integer,
            0::integer, 0::integer, 0::integer, 0::integer,
            false::boolean, false::boolean;
        RETURN;
    END IF;

    -- Retornar estatísticas
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data),

        (SELECT COUNT(*)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data
           AND conta_limite_diario = true),

        (SELECT COUNT(*)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data
           AND modo_estudo_continuo = true),

        (SELECT COALESCE(SUM(total_questoes), 0)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data),

        v_limite_sessoes,
        v_limite_questoes,

        GREATEST(0, v_limite_sessoes + v_sessoes_extras -
                (SELECT COUNT(*)::INTEGER
                 FROM sessao_estudo
                 WHERE user_id = p_user_id
                   AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data
                   AND conta_limite_diario = true))::INTEGER,

        GREATEST(0, v_limite_questoes -
                (SELECT COALESCE(SUM(total_questoes), 0)::INTEGER
                 FROM sessao_estudo
                 WHERE user_id = p_user_id
                   AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data))::INTEGER,

        v_permite_estudo_continuo,
        v_permite_sessao_estendida;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- COMENTÁRIOS
-- ================================================================================

COMMENT ON FUNCTION pode_iniciar_sessao IS 'Verifica se usuário pode iniciar nova sessão baseado nos limites do plano';
COMMENT ON FUNCTION estatisticas_uso_diario IS 'Retorna estatísticas de uso diário do usuário';

COMMIT;

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
\echo 'Migration 010 v2: Funções de controle de sessão criadas com sucesso'
