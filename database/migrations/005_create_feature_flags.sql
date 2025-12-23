-- ================================================================================
-- MIGRATION 005: FEATURE FLAGS E CONTROLES DE GO-LIVE
-- ================================================================================
-- Objetivo: Controle granular de features para go-live controlado
-- Data: 2025-12-17
-- ================================================================================

-- ================================================================================
-- 1. TABELA DE FEATURE FLAGS
-- ================================================================================

CREATE TABLE IF NOT EXISTS feature_flag (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    codigo VARCHAR(100) NOT NULL UNIQUE,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,

    -- Estado
    habilitado BOOLEAN DEFAULT FALSE,
    habilitado_globalmente BOOLEAN DEFAULT FALSE,

    -- Limites quantitativos
    limite_usuarios INTEGER,  -- NULL = sem limite
    usuarios_atuais INTEGER DEFAULT 0,

    -- Controle de rollout
    percentual_rollout INTEGER DEFAULT 0,  -- 0-100
    whitelist_usuarios UUID[],  -- Array de usuario_id

    -- Metadados
    ambiente VARCHAR(50) DEFAULT 'production',  -- production, staging, development
    categoria VARCHAR(50),  -- mode, feature, limit

    -- Auditoria
    habilitado_em TIMESTAMP,
    desabilitado_em TIMESTAMP,
    habilitado_por UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_feature_flag_codigo ON feature_flag(codigo);
CREATE INDEX idx_feature_flag_habilitado ON feature_flag(habilitado);
CREATE INDEX idx_feature_flag_categoria ON feature_flag(categoria);

-- Comentários
COMMENT ON TABLE feature_flag IS 'Feature flags para controle de go-live';
COMMENT ON COLUMN feature_flag.percentual_rollout IS 'Percentual de usuários com acesso (0-100)';


-- ================================================================================
-- 2. TABELA DE LIMITES DE USO (GO-LIVE)
-- ================================================================================

CREATE TABLE IF NOT EXISTS limite_go_live (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tipo de limite
    tipo_limite VARCHAR(50) NOT NULL,  -- sessoes_dia, questoes_sessao, pecas_semana

    -- Valores
    valor_limite INTEGER NOT NULL,
    valor_padrao INTEGER NOT NULL,

    -- Aplicação
    aplicar_a VARCHAR(50) DEFAULT 'todos',  -- todos, plano_free, plano_basic, plano_pro

    -- Estado
    ativo BOOLEAN DEFAULT TRUE,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_limite_go_live_tipo ON limite_go_live(tipo_limite);
CREATE INDEX idx_limite_go_live_ativo ON limite_go_live(ativo);

-- Comentários
COMMENT ON TABLE limite_go_live IS 'Limites específicos para período de go-live';


-- ================================================================================
-- 3. TABELA DE MÉTRICAS DE SESSÃO
-- ================================================================================

CREATE TABLE IF NOT EXISTS metrica_sessao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    sessao_id UUID,  -- ID da sessão de estudo (não sessão_usuario)

    -- Temporal
    data_sessao DATE NOT NULL DEFAULT CURRENT_DATE,
    hora_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
    hora_fim TIMESTAMP,
    duracao_segundos INTEGER,

    -- Métricas de uso
    questoes_respondidas INTEGER DEFAULT 0,
    questoes_corretas INTEGER DEFAULT 0,
    questoes_incorretas INTEGER DEFAULT 0,

    -- Métricas de erro (por tipo)
    erros_conceitual INTEGER DEFAULT 0,
    erros_normativo INTEGER DEFAULT 0,
    erros_interpretacao INTEGER DEFAULT 0,
    erros_estrategico INTEGER DEFAULT 0,
    erros_leitura INTEGER DEFAULT 0,
    erros_confusao_institutos INTEGER DEFAULT 0,

    -- Métricas de conclusão
    sessao_concluida BOOLEAN DEFAULT FALSE,
    abandonada BOOLEAN DEFAULT FALSE,
    motivo_abandono VARCHAR(100),

    -- Contexto
    modo_utilizado VARCHAR(50),  -- pedagogico, profissional
    plano_ativo VARCHAR(50),

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_metrica_sessao_usuario_id ON metrica_sessao(usuario_id);
CREATE INDEX idx_metrica_sessao_data ON metrica_sessao(data_sessao);
CREATE INDEX idx_metrica_sessao_concluida ON metrica_sessao(sessao_concluida);
CREATE INDEX idx_metrica_sessao_abandonada ON metrica_sessao(abandonada);

-- Comentários
COMMENT ON TABLE metrica_sessao IS 'Métricas por sessão de estudo para go-live';


-- ================================================================================
-- 4. TABELA DE EVENTOS DE GO-LIVE
-- ================================================================================

CREATE TABLE IF NOT EXISTS evento_go_live (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tipo de evento
    tipo_evento VARCHAR(100) NOT NULL,
    severidade VARCHAR(20) NOT NULL,  -- info, warning, error, critical

    -- Contexto
    usuario_id UUID REFERENCES usuario(id) ON DELETE SET NULL,
    feature_flag_codigo VARCHAR(100),

    -- Descrição
    mensagem TEXT NOT NULL,
    detalhes JSONB,

    -- Stack trace (para erros)
    stack_trace TEXT,

    -- Timestamp
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_evento_go_live_tipo ON evento_go_live(tipo_evento);
CREATE INDEX idx_evento_go_live_severidade ON evento_go_live(severidade);
CREATE INDEX idx_evento_go_live_timestamp ON evento_go_live(timestamp);
CREATE INDEX idx_evento_go_live_usuario_id ON evento_go_live(usuario_id);

-- Comentários
COMMENT ON TABLE evento_go_live IS 'Log de eventos durante período de go-live';


-- ================================================================================
-- 5. FEATURE FLAGS INICIAIS (GO-LIVE CONTROLADO)
-- ================================================================================

-- Flag: Modo OAB (HABILITADO)
INSERT INTO feature_flag (
    id, codigo, nome, descricao,
    habilitado, habilitado_globalmente,
    limite_usuarios, categoria, ambiente
) VALUES (
    gen_random_uuid(),
    'modo_oab',
    'Modo OAB (Pedagógico)',
    'Habilita modo pedagógico para preparação OAB',
    TRUE,
    TRUE,
    50,  -- Limite de 50 usuários
    'mode',
    'production'
) ON CONFLICT (codigo) DO NOTHING;

-- Flag: Modo Profissional (DESABILITADO)
INSERT INTO feature_flag (
    id, codigo, nome, descricao,
    habilitado, habilitado_globalmente,
    limite_usuarios, categoria, ambiente
) VALUES (
    gen_random_uuid(),
    'modo_profissional',
    'Modo Profissional',
    'Habilita modo profissional sem gabarito',
    FALSE,
    FALSE,
    NULL,
    'mode',
    'production'
) ON CONFLICT (codigo) DO NOTHING;

-- Flag: Piece Engine (DESABILITADO)
INSERT INTO feature_flag (
    id, codigo, nome, descricao,
    habilitado, habilitado_globalmente,
    limite_usuarios, categoria, ambiente
) VALUES (
    gen_random_uuid(),
    'piece_engine',
    'Geração de Peças',
    'Habilita geração de peças processuais',
    FALSE,
    FALSE,
    NULL,
    'feature',
    'production'
) ON CONFLICT (codigo) DO NOTHING;

-- Flag: Analytics (HABILITADO)
INSERT INTO feature_flag (
    id, codigo, nome, descricao,
    habilitado, habilitado_globalmente,
    categoria, ambiente
) VALUES (
    gen_random_uuid(),
    'analytics',
    'Analytics de Uso',
    'Coleta métricas de uso do sistema',
    TRUE,
    TRUE,
    'feature',
    'production'
) ON CONFLICT (codigo) DO NOTHING;

-- Flag: Cadastro de Novos Usuários (HABILITADO COM LIMITE)
INSERT INTO feature_flag (
    id, codigo, nome, descricao,
    habilitado, habilitado_globalmente,
    limite_usuarios, categoria, ambiente
) VALUES (
    gen_random_uuid(),
    'novos_cadastros',
    'Cadastro de Novos Usuários',
    'Permite registro de novos usuários',
    TRUE,
    TRUE,
    50,  -- Limite de 50 cadastros
    'feature',
    'production'
) ON CONFLICT (codigo) DO NOTHING;


-- ================================================================================
-- 6. LIMITES INICIAIS (GO-LIVE)
-- ================================================================================

-- Limite: Sessões por dia
INSERT INTO limite_go_live (
    id, tipo_limite, valor_limite, valor_padrao, aplicar_a, ativo
) VALUES (
    gen_random_uuid(),
    'sessoes_dia',
    3,  -- Máximo 3 sessões/dia
    3,
    'todos',
    TRUE
) ON CONFLICT DO NOTHING;

-- Limite: Questões por sessão
INSERT INTO limite_go_live (
    id, tipo_limite, valor_limite, valor_padrao, aplicar_a, ativo
) VALUES (
    gen_random_uuid(),
    'questoes_sessao',
    20,  -- Máximo 20 questões/sessão
    20,
    'todos',
    TRUE
) ON CONFLICT DO NOTHING;

-- Limite: Práticas de peça por semana
INSERT INTO limite_go_live (
    id, tipo_limite, valor_limite, valor_padrao, aplicar_a, ativo
) VALUES (
    gen_random_uuid(),
    'pecas_semana',
    0,  -- Peças desabilitadas no go-live
    0,
    'todos',
    TRUE
) ON CONFLICT DO NOTHING;

-- Limite: Duração máxima de sessão (minutos)
INSERT INTO limite_go_live (
    id, tipo_limite, valor_limite, valor_padrao, aplicar_a, ativo
) VALUES (
    gen_random_uuid(),
    'duracao_sessao_minutos',
    90,  -- Máximo 90 minutos por sessão
    90,
    'todos',
    TRUE
) ON CONFLICT DO NOTHING;


-- ================================================================================
-- 7. FUNÇÕES DE VERIFICAÇÃO
-- ================================================================================

CREATE OR REPLACE FUNCTION verificar_feature_habilitada(
    p_codigo_feature VARCHAR,
    p_usuario_id UUID DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_habilitada BOOLEAN;
    v_limite_usuarios INTEGER;
    v_usuarios_atuais INTEGER;
    v_whitelist UUID[];
BEGIN
    -- Buscar feature flag
    SELECT habilitado, limite_usuarios, usuarios_atuais, whitelist_usuarios
    INTO v_habilitada, v_limite_usuarios, v_usuarios_atuais, v_whitelist
    FROM feature_flag
    WHERE codigo = p_codigo_feature;

    -- Feature não existe ou desabilitada
    IF NOT FOUND OR NOT v_habilitada THEN
        RETURN FALSE;
    END IF;

    -- Se não há usuário específico, retornar status global
    IF p_usuario_id IS NULL THEN
        RETURN v_habilitada;
    END IF;

    -- Verificar whitelist
    IF v_whitelist IS NOT NULL AND p_usuario_id = ANY(v_whitelist) THEN
        RETURN TRUE;
    END IF;

    -- Verificar limite de usuários
    IF v_limite_usuarios IS NOT NULL AND v_usuarios_atuais >= v_limite_usuarios THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verificar_feature_habilitada IS 'Verifica se feature está habilitada para usuário';


CREATE OR REPLACE FUNCTION verificar_limite_go_live(
    p_tipo_limite VARCHAR,
    p_usuario_id UUID,
    p_periodo VARCHAR DEFAULT 'dia'  -- dia, sessao, semana
)
RETURNS TABLE (
    atingido BOOLEAN,
    limite INTEGER,
    uso_atual INTEGER,
    restante INTEGER
) AS $$
DECLARE
    v_limite INTEGER;
    v_uso_atual INTEGER;
BEGIN
    -- Obter limite
    SELECT valor_limite INTO v_limite
    FROM limite_go_live
    WHERE tipo_limite = p_tipo_limite
      AND ativo = TRUE
    LIMIT 1;

    IF NOT FOUND THEN
        -- Sem limite configurado
        RETURN QUERY SELECT FALSE, NULL::INTEGER, 0, NULL::INTEGER;
        RETURN;
    END IF;

    -- Calcular uso atual baseado no tipo
    IF p_tipo_limite = 'sessoes_dia' THEN
        SELECT COUNT(*) INTO v_uso_atual
        FROM metrica_sessao
        WHERE usuario_id = p_usuario_id
          AND data_sessao = CURRENT_DATE;

    ELSIF p_tipo_limite = 'questoes_sessao' THEN
        -- Última sessão aberta
        SELECT COALESCE(questoes_respondidas, 0) INTO v_uso_atual
        FROM metrica_sessao
        WHERE usuario_id = p_usuario_id
          AND hora_fim IS NULL
        ORDER BY hora_inicio DESC
        LIMIT 1;

        IF NOT FOUND THEN
            v_uso_atual := 0;
        END IF;

    ELSIF p_tipo_limite = 'pecas_semana' THEN
        SELECT COALESCE(SUM(pecas_geradas), 0) INTO v_uso_atual
        FROM uso_diario
        WHERE usuario_id = p_usuario_id
          AND data >= CURRENT_DATE - INTERVAL '7 days';

    ELSE
        v_uso_atual := 0;
    END IF;

    -- Retornar resultado
    RETURN QUERY SELECT
        (v_uso_atual >= v_limite) AS atingido,
        v_limite,
        v_uso_atual,
        GREATEST(0, v_limite - v_uso_atual) AS restante;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verificar_limite_go_live IS 'Verifica limites específicos do go-live';


-- ================================================================================
-- 8. TRIGGERS
-- ================================================================================

CREATE TRIGGER trigger_feature_flag_updated_at
    BEFORE UPDATE ON feature_flag
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_limite_go_live_updated_at
    BEFORE UPDATE ON limite_go_live
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_metrica_sessao_updated_at
    BEFORE UPDATE ON metrica_sessao
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- ================================================================================
-- FIM DA MIGRATION 005
-- ================================================================================
