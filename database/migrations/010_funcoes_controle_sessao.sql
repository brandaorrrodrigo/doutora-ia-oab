-- ================================================================================
-- MIGRATION 010: FUNÇÕES DE CONTROLE DE SESSÃO E LIMITES
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
    v_assinatura RECORD;
    v_plano RECORD;
    v_sessoes_hoje INTEGER;
    v_sessoes_extras_disponiveis INTEGER;
BEGIN
    -- Buscar assinatura ativa do usuário
    SELECT a.*, p.* INTO v_assinatura, v_plano
    FROM assinatura a
    INNER JOIN plano p ON a.plano_id = p.id
    WHERE a.user_id = p_user_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.data_inicio DESC
    LIMIT 1;

    -- Se não tem assinatura ativa, não pode iniciar
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Nenhuma assinatura ativa encontrada', 0, 0;
        RETURN;
    END IF;

    -- Se é modo estudo contínuo, sempre pode (não conta no limite)
    IF p_modo_estudo_continuo AND v_plano.permite_estudo_continuo THEN
        RETURN QUERY SELECT true, 'Estudo contínuo permitido (não conta no limite)', 0, 999;
        RETURN;
    END IF;

    -- Se plano não permite estudo contínuo mas usuário tentou
    IF p_modo_estudo_continuo AND NOT v_plano.permite_estudo_continuo THEN
        RETURN QUERY SELECT false, 'Seu plano não permite estudo contínuo. Faça upgrade!', 0, 0;
        RETURN;
    END IF;

    -- Contar sessões de hoje que contam no limite
    SELECT COUNT(*)::INTEGER INTO v_sessoes_hoje
    FROM sessao_estudo
    WHERE user_id = p_user_id
      AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
      AND conta_limite_diario = true;

    -- Verificar se tem sessões extras disponíveis
    v_sessoes_extras_disponiveis := v_plano.sessoes_extras_condicionais;

    -- Verificar se ultrapassou limite
    IF v_sessoes_hoje >= (v_plano.limite_sessoes_dia + v_sessoes_extras_disponiveis) THEN
        RETURN QUERY SELECT
            false,
            'Limite de sessões diárias atingido. Continue amanhã ou estude conteúdo teórico!',
            v_sessoes_hoje,
            v_plano.limite_sessoes_dia + v_sessoes_extras_disponiveis;
        RETURN;
    END IF;

    -- Pode iniciar sessão
    RETURN QUERY SELECT
        true,
        'Pode iniciar nova sessão',
        v_sessoes_hoje,
        v_plano.limite_sessoes_dia + v_sessoes_extras_disponiveis;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FUNÇÃO: Verificar se sessão deve ser estendida (não consome adicional)
-- ================================================================================

CREATE OR REPLACE FUNCTION deve_marcar_sessao_estendida(
    p_sessao_id UUID,
    p_duracao_minutos INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_sessao RECORD;
    v_assinatura RECORD;
    v_plano RECORD;
BEGIN
    -- Buscar sessão
    SELECT * INTO v_sessao
    FROM sessao_estudo
    WHERE id = p_sessao_id;

    IF NOT FOUND THEN
        RETURN false;
    END IF;

    -- Buscar plano do usuário
    SELECT a.*, p.* INTO v_assinatura, v_plano
    FROM assinatura a
    INNER JOIN plano p ON a.plano_id = p.id
    WHERE a.user_id = v_sessao.user_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.data_inicio DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN false;
    END IF;

    -- Se plano não permite sessão estendida, retorna false
    IF NOT v_plano.permite_sessao_estendida THEN
        RETURN false;
    END IF;

    -- Se duração ultrapassou o limite, marca como estendida
    IF p_duracao_minutos > v_plano.duracao_maxima_sessao_minutos THEN
        RETURN true;
    END IF;

    RETURN false;
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
    v_plano RECORD;
BEGIN
    -- Buscar plano do usuário
    SELECT p.* INTO v_plano
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
            0, 0, 0, 0, 0, 0, 0, 0, false, false;
        RETURN;
    END IF;

    -- Retornar estatísticas
    RETURN QUERY
    SELECT
        (SELECT COUNT(*)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data) as sessoes_total,

        (SELECT COUNT(*)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data
           AND conta_limite_diario = true) as sessoes_que_contam,

        (SELECT COUNT(*)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data
           AND modo_estudo_continuo = true) as sessoes_estudo_continuo,

        (SELECT COALESCE(SUM(total_questoes), 0)::INTEGER
         FROM sessao_estudo
         WHERE user_id = p_user_id
           AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data) as questoes_total,

        v_plano.limite_sessoes_dia as limite_sessoes,
        v_plano.limite_questoes_dia as limite_questoes,

        GREATEST(0, v_plano.limite_sessoes_dia + v_plano.sessoes_extras_condicionais -
                (SELECT COUNT(*)::INTEGER
                 FROM sessao_estudo
                 WHERE user_id = p_user_id
                   AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data
                   AND conta_limite_diario = true))::INTEGER as sessoes_disponiveis,

        GREATEST(0, v_plano.limite_questoes_dia -
                (SELECT COALESCE(SUM(total_questoes), 0)::INTEGER
                 FROM sessao_estudo
                 WHERE user_id = p_user_id
                   AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = p_data))::INTEGER as questoes_disponiveis,

        v_plano.permite_estudo_continuo,
        v_plano.permite_sessao_estendida;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- FUNÇÃO: Ativar sessão extras condicional (heavy users)
-- ================================================================================

CREATE OR REPLACE FUNCTION ativar_sessao_extra_condicional(
    p_user_id UUID
)
RETURNS TABLE(
    ativado BOOLEAN,
    motivo TEXT
) AS $$
DECLARE
    v_plano RECORD;
    v_uso_7dias INTEGER;
    v_sessoes_hoje INTEGER;
BEGIN
    -- Buscar plano do usuário
    SELECT p.* INTO v_plano
    FROM assinatura a
    INNER JOIN plano p ON a.plano_id = p.id
    WHERE a.user_id = p_user_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.data_inicio DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Nenhuma assinatura ativa';
        RETURN;
    END IF;

    -- Se plano não tem sessões extras, retorna false
    IF v_plano.sessoes_extras_condicionais = 0 THEN
        RETURN QUERY SELECT false, 'Seu plano não possui sessões extras condicionais';
        RETURN;
    END IF;

    -- Contar sessões dos últimos 7 dias (heavy user = 80%+ do limite)
    SELECT COUNT(*)::INTEGER INTO v_uso_7dias
    FROM sessao_estudo
    WHERE user_id = p_user_id
      AND iniciado_em >= CURRENT_DATE - INTERVAL '7 days'
      AND conta_limite_diario = true;

    -- Heavy user = usou 80% ou mais do limite nos últimos 7 dias
    IF v_uso_7dias >= (v_plano.limite_sessoes_dia * 7 * 0.8) THEN
        -- Contar sessões de hoje
        SELECT COUNT(*)::INTEGER INTO v_sessoes_hoje
        FROM sessao_estudo
        WHERE user_id = p_user_id
          AND DATE(iniciado_em AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
          AND conta_limite_diario = true;

        -- Se já usou o limite padrão mas não usou a extra
        IF v_sessoes_hoje >= v_plano.limite_sessoes_dia
           AND v_sessoes_hoje < (v_plano.limite_sessoes_dia + v_plano.sessoes_extras_condicionais) THEN
            RETURN QUERY SELECT
                true,
                'Heavy user! Sessão extra liberada por uso consistente.';
            RETURN;
        END IF;
    END IF;

    RETURN QUERY SELECT false, 'Critérios para sessão extra não atendidos';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ================================================================================
-- COMENTÁRIOS
-- ================================================================================

COMMENT ON FUNCTION pode_iniciar_sessao IS 'Verifica se usuário pode iniciar nova sessão baseado nos limites do plano';
COMMENT ON FUNCTION deve_marcar_sessao_estendida IS 'Determina se sessão longa deve ser marcada como estendida (plano Semestral)';
COMMENT ON FUNCTION estatisticas_uso_diario IS 'Retorna estatísticas de uso diário do usuário';
COMMENT ON FUNCTION ativar_sessao_extra_condicional IS 'Verifica se heavy user pode ativar sessão extra condicional';

COMMIT;

-- ================================================================================
-- VERIFICAÇÃO
-- ================================================================================
\echo 'Migration 010: Funções de controle de sessão criadas com sucesso'
