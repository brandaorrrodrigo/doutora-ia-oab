-- ================================================================================
-- MIGRATION 004: TABELAS DE ASSINATURAS E PLANOS - ETAPA 10.3
-- ================================================================================
-- Objetivo: Criar estrutura de planos, assinaturas e metering de uso
-- Data: 2025-12-17
-- ================================================================================

-- ================================================================================
-- 1. TABELA DE PLANOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS plano (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    codigo VARCHAR(50) NOT NULL UNIQUE,  -- FREE, BASIC, PRO
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,

    -- Limites
    limite_questoes_dia INTEGER,  -- NULL = ilimitado
    limite_consultas_dia INTEGER,  -- NULL = ilimitado
    limite_peca_mes INTEGER,  -- NULL = ilimitado

    -- Funcionalidades
    acesso_modo_pedagogico BOOLEAN DEFAULT TRUE,
    acesso_modo_profissional BOOLEAN DEFAULT FALSE,
    acesso_piece_engine BOOLEAN DEFAULT FALSE,
    acesso_jurisprudencia BOOLEAN DEFAULT FALSE,
    acesso_analytics BOOLEAN DEFAULT FALSE,

    -- Pricing
    preco_mensal DECIMAL(10, 2),  -- NULL = gratuito
    preco_anual DECIMAL(10, 2),  -- NULL = gratuito
    moeda VARCHAR(3) DEFAULT 'BRL',

    -- Status
    ativo BOOLEAN DEFAULT TRUE,
    visivel_publico BOOLEAN DEFAULT TRUE,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_plano_codigo ON plano(codigo);
CREATE INDEX idx_plano_ativo ON plano(ativo);

-- Comentários
COMMENT ON TABLE plano IS 'Planos de assinatura disponíveis';
COMMENT ON COLUMN plano.limite_questoes_dia IS 'NULL = ilimitado';


-- ================================================================================
-- 2. TABELA DE ASSINATURAS
-- ================================================================================

CREATE TABLE IF NOT EXISTS assinatura (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    plano_id UUID NOT NULL REFERENCES plano(id),

    -- Período
    status VARCHAR(50) NOT NULL,  -- active, canceled, expired, trial
    periodo VARCHAR(20) NOT NULL,  -- monthly, yearly, trial

    -- Datas
    data_inicio TIMESTAMP NOT NULL DEFAULT NOW(),
    data_fim TIMESTAMP,
    data_cancelamento TIMESTAMP,
    data_renovacao TIMESTAMP,

    -- Trial
    em_trial BOOLEAN DEFAULT FALSE,
    trial_ate TIMESTAMP,

    -- Billing
    stripe_subscription_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),

    -- Auto-renovação
    auto_renovar BOOLEAN DEFAULT TRUE,
    motivo_cancelamento TEXT,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_assinatura_usuario_id ON assinatura(usuario_id);
CREATE INDEX idx_assinatura_plano_id ON assinatura(plano_id);
CREATE INDEX idx_assinatura_status ON assinatura(status);
CREATE INDEX idx_assinatura_stripe_subscription_id ON assinatura(stripe_subscription_id);

-- Comentários
COMMENT ON TABLE assinatura IS 'Assinaturas ativas e históricas de usuários';


-- ================================================================================
-- 3. TABELA DE USO (METERING)
-- ================================================================================

CREATE TABLE IF NOT EXISTS uso_diario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    assinatura_id UUID REFERENCES assinatura(id) ON DELETE SET NULL,

    -- Data
    data DATE NOT NULL,

    -- Contadores
    questoes_respondidas INTEGER DEFAULT 0,
    consultas_realizadas INTEGER DEFAULT 0,
    pecas_geradas INTEGER DEFAULT 0,
    tempo_uso_segundos INTEGER DEFAULT 0,

    -- Metadados
    primeira_atividade TIMESTAMP,
    ultima_atividade TIMESTAMP,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraint única por usuário/dia
    UNIQUE (usuario_id, data)
);

-- Índices
CREATE INDEX idx_uso_diario_usuario_id ON uso_diario(usuario_id);
CREATE INDEX idx_uso_diario_data ON uso_diario(data);
CREATE INDEX idx_uso_diario_assinatura_id ON uso_diario(assinatura_id);

-- Comentários
COMMENT ON TABLE uso_diario IS 'Metering de uso por usuário/dia para enforcement de limites';


-- ================================================================================
-- 4. TABELA DE EVENTOS DE USO (LOG DETALHADO)
-- ================================================================================

CREATE TABLE IF NOT EXISTS evento_uso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    uso_diario_id UUID REFERENCES uso_diario(id) ON DELETE CASCADE,

    -- Tipo de evento
    tipo_evento VARCHAR(50) NOT NULL,  -- questao_respondida, consulta_realizada, peca_gerada
    recurso_id UUID,  -- ID do recurso usado (questao_id, etc.)

    -- Resultado
    sucesso BOOLEAN DEFAULT TRUE,
    bloqueado_por_limite BOOLEAN DEFAULT FALSE,
    limite_atingido VARCHAR(50),  -- qual limite foi atingido

    -- Metadados
    detalhes JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_evento_uso_usuario_id ON evento_uso(usuario_id);
CREATE INDEX idx_evento_uso_tipo ON evento_uso(tipo_evento);
CREATE INDEX idx_evento_uso_timestamp ON evento_uso(timestamp);
CREATE INDEX idx_evento_uso_bloqueado ON evento_uso(bloqueado_por_limite);

-- Comentários
COMMENT ON TABLE evento_uso IS 'Log detalhado de eventos de uso para analytics';


-- ================================================================================
-- 5. TABELA DE HISTÓRICO DE PLANOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS historico_plano (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    plano_anterior_id UUID REFERENCES plano(id),
    plano_novo_id UUID REFERENCES plano(id),

    -- Mudança
    tipo_mudanca VARCHAR(50) NOT NULL,  -- upgrade, downgrade, cancelamento, renovacao
    motivo TEXT,

    -- Auditoria
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_historico_plano_usuario_id ON historico_plano(usuario_id);
CREATE INDEX idx_historico_plano_timestamp ON historico_plano(timestamp);

-- Comentários
COMMENT ON TABLE historico_plano IS 'Histórico de mudanças de plano';


-- ================================================================================
-- 6. CONSTRAINTS
-- ================================================================================

-- Status de assinatura válidos
ALTER TABLE assinatura
ADD CONSTRAINT check_status_valido
CHECK (status IN ('active', 'canceled', 'expired', 'trial', 'past_due'));

-- Período de assinatura válido
ALTER TABLE assinatura
ADD CONSTRAINT check_periodo_valido
CHECK (periodo IN ('monthly', 'yearly', 'trial'));


-- ================================================================================
-- 7. FUNÇÃO: OBTER ASSINATURA ATIVA
-- ================================================================================

CREATE OR REPLACE FUNCTION obter_assinatura_ativa(p_usuario_id UUID)
RETURNS TABLE (
    assinatura_id UUID,
    plano_id UUID,
    plano_codigo VARCHAR,
    status VARCHAR,
    limite_questoes_dia INTEGER,
    limite_consultas_dia INTEGER,
    limite_peca_mes INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        a.id,
        a.plano_id,
        p.codigo,
        a.status,
        p.limite_questoes_dia,
        p.limite_consultas_dia,
        p.limite_peca_mes
    FROM assinatura a
    JOIN plano p ON a.plano_id = p.id
    WHERE a.usuario_id = p_usuario_id
      AND a.status = 'active'
      AND (a.data_fim IS NULL OR a.data_fim > NOW())
    ORDER BY a.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION obter_assinatura_ativa IS 'Retorna assinatura ativa do usuário com limites do plano';


-- ================================================================================
-- 8. FUNÇÃO: OBTER USO DO DIA
-- ================================================================================

CREATE OR REPLACE FUNCTION obter_uso_dia(p_usuario_id UUID, p_data DATE DEFAULT CURRENT_DATE)
RETURNS TABLE (
    questoes_respondidas INTEGER,
    consultas_realizadas INTEGER,
    pecas_geradas INTEGER,
    tempo_uso_segundos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(ud.questoes_respondidas, 0),
        COALESCE(ud.consultas_realizadas, 0),
        COALESCE(ud.pecas_geradas, 0),
        COALESCE(ud.tempo_uso_segundos, 0)
    FROM uso_diario ud
    WHERE ud.usuario_id = p_usuario_id
      AND ud.data = p_data;

    -- Se não existe registro, retornar zeros
    IF NOT FOUND THEN
        RETURN QUERY SELECT 0, 0, 0, 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION obter_uso_dia IS 'Retorna uso do dia para enforcement de limites';


-- ================================================================================
-- 9. FUNÇÃO: INCREMENTAR USO
-- ================================================================================

CREATE OR REPLACE FUNCTION incrementar_uso(
    p_usuario_id UUID,
    p_tipo_evento VARCHAR,
    p_incremento INTEGER DEFAULT 1
)
RETURNS BOOLEAN AS $$
DECLARE
    v_assinatura_id UUID;
BEGIN
    -- Obter assinatura ativa
    SELECT assinatura_id INTO v_assinatura_id
    FROM obter_assinatura_ativa(p_usuario_id);

    -- Inserir ou atualizar uso_diario
    INSERT INTO uso_diario (
        id,
        usuario_id,
        assinatura_id,
        data,
        questoes_respondidas,
        consultas_realizadas,
        pecas_geradas,
        primeira_atividade,
        ultima_atividade
    ) VALUES (
        gen_random_uuid(),
        p_usuario_id,
        v_assinatura_id,
        CURRENT_DATE,
        CASE WHEN p_tipo_evento = 'questao' THEN p_incremento ELSE 0 END,
        CASE WHEN p_tipo_evento = 'consulta' THEN p_incremento ELSE 0 END,
        CASE WHEN p_tipo_evento = 'peca' THEN p_incremento ELSE 0 END,
        NOW(),
        NOW()
    )
    ON CONFLICT (usuario_id, data)
    DO UPDATE SET
        questoes_respondidas = uso_diario.questoes_respondidas +
            CASE WHEN p_tipo_evento = 'questao' THEN p_incremento ELSE 0 END,
        consultas_realizadas = uso_diario.consultas_realizadas +
            CASE WHEN p_tipo_evento = 'consulta' THEN p_incremento ELSE 0 END,
        pecas_geradas = uso_diario.pecas_geradas +
            CASE WHEN p_tipo_evento = 'peca' THEN p_incremento ELSE 0 END,
        ultima_atividade = NOW();

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION incrementar_uso IS 'Incrementa contador de uso do dia';


-- ================================================================================
-- 10. FUNÇÃO: VERIFICAR LIMITE
-- ================================================================================

CREATE OR REPLACE FUNCTION verificar_limite(
    p_usuario_id UUID,
    p_tipo_recurso VARCHAR  -- 'questao', 'consulta', 'peca'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_limite INTEGER;
    v_uso_atual INTEGER;
BEGIN
    -- Obter limite do plano
    IF p_tipo_recurso = 'questao' THEN
        SELECT limite_questoes_dia INTO v_limite
        FROM obter_assinatura_ativa(p_usuario_id);
    ELSIF p_tipo_recurso = 'consulta' THEN
        SELECT limite_consultas_dia INTO v_limite
        FROM obter_assinatura_ativa(p_usuario_id);
    ELSIF p_tipo_recurso = 'peca' THEN
        SELECT limite_peca_mes INTO v_limite
        FROM obter_assinatura_ativa(p_usuario_id);
    ELSE
        RETURN FALSE;  -- Tipo inválido
    END IF;

    -- NULL = ilimitado
    IF v_limite IS NULL THEN
        RETURN TRUE;
    END IF;

    -- Obter uso atual
    IF p_tipo_recurso = 'questao' THEN
        SELECT questoes_respondidas INTO v_uso_atual
        FROM obter_uso_dia(p_usuario_id, CURRENT_DATE);
    ELSIF p_tipo_recurso = 'consulta' THEN
        SELECT consultas_realizadas INTO v_uso_atual
        FROM obter_uso_dia(p_usuario_id, CURRENT_DATE);
    ELSIF p_tipo_recurso = 'peca' THEN
        -- Peça é limite mensal, não diário
        SELECT SUM(pecas_geradas) INTO v_uso_atual
        FROM uso_diario
        WHERE usuario_id = p_usuario_id
          AND data >= DATE_TRUNC('month', CURRENT_DATE);
    END IF;

    -- Verificar se atingiu limite
    RETURN (v_uso_atual < v_limite);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verificar_limite IS 'Verifica se usuário atingiu limite do plano';


-- ================================================================================
-- 11. DADOS INICIAIS: PLANOS
-- ================================================================================

-- Plano FREE
INSERT INTO plano (
    id,
    codigo,
    nome,
    descricao,
    limite_questoes_dia,
    limite_consultas_dia,
    limite_peca_mes,
    acesso_modo_pedagogico,
    acesso_modo_profissional,
    acesso_piece_engine,
    acesso_jurisprudencia,
    acesso_analytics,
    preco_mensal,
    preco_anual,
    ativo,
    visivel_publico
) VALUES (
    gen_random_uuid(),
    'FREE',
    'Plano Gratuito',
    'Acesso básico à plataforma com limites diários',
    10,  -- 10 questões/dia
    NULL,  -- Consultas ilimitadas
    0,  -- Sem acesso a peças
    TRUE,  -- Modo pedagógico
    FALSE,  -- Sem modo profissional
    FALSE,  -- Sem piece engine
    FALSE,  -- Sem jurisprudência
    FALSE,  -- Sem analytics
    NULL,  -- Gratuito
    NULL,  -- Gratuito
    TRUE,
    TRUE
) ON CONFLICT (codigo) DO NOTHING;

-- Plano BASIC
INSERT INTO plano (
    id,
    codigo,
    nome,
    descricao,
    limite_questoes_dia,
    limite_consultas_dia,
    limite_peca_mes,
    acesso_modo_pedagogico,
    acesso_modo_profissional,
    acesso_piece_engine,
    acesso_jurisprudencia,
    acesso_analytics,
    preco_mensal,
    preco_anual,
    ativo,
    visivel_publico
) VALUES (
    gen_random_uuid(),
    'BASIC',
    'Plano Básico',
    'Acesso ampliado com analytics e peças limitadas',
    50,  -- 50 questões/dia
    NULL,  -- Consultas ilimitadas
    5,  -- 5 peças/mês
    TRUE,  -- Modo pedagógico
    FALSE,  -- Sem modo profissional
    TRUE,  -- Com piece engine (limitado)
    FALSE,  -- Sem jurisprudência
    TRUE,  -- Com analytics
    49.90,  -- R$ 49,90/mês
    479.00,  -- R$ 479,00/ano (20% desconto)
    TRUE,
    TRUE
) ON CONFLICT (codigo) DO NOTHING;

-- Plano PRO
INSERT INTO plano (
    id,
    codigo,
    nome,
    descricao,
    limite_questoes_dia,
    limite_consultas_dia,
    limite_peca_mes,
    acesso_modo_pedagogico,
    acesso_modo_profissional,
    acesso_piece_engine,
    acesso_jurisprudencia,
    acesso_analytics,
    preco_mensal,
    preco_anual,
    ativo,
    visivel_publico
) VALUES (
    gen_random_uuid(),
    'PRO',
    'Plano Profissional',
    'Acesso ilimitado com modo profissional e todos os recursos',
    NULL,  -- Questões ilimitadas
    NULL,  -- Consultas ilimitadas
    NULL,  -- Peças ilimitadas
    TRUE,  -- Modo pedagógico
    TRUE,  -- Modo profissional
    TRUE,  -- Piece engine completo
    TRUE,  -- Com jurisprudência
    TRUE,  -- Com analytics
    199.90,  -- R$ 199,90/mês
    1919.00,  -- R$ 1.919,00/ano (20% desconto)
    TRUE,
    TRUE
) ON CONFLICT (codigo) DO NOTHING;


-- ================================================================================
-- 12. TRIGGER: updated_at para tabelas
-- ================================================================================

CREATE TRIGGER trigger_plano_updated_at
    BEFORE UPDATE ON plano
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_assinatura_updated_at
    BEFORE UPDATE ON assinatura
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_uso_diario_updated_at
    BEFORE UPDATE ON uso_diario
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- ================================================================================
-- 13. VIEW: ASSINATURAS ATIVAS
-- ================================================================================

CREATE OR REPLACE VIEW v_assinaturas_ativas AS
SELECT
    a.id AS assinatura_id,
    a.usuario_id,
    u.email,
    u.nome_completo,
    p.codigo AS plano_codigo,
    p.nome AS plano_nome,
    p.limite_questoes_dia,
    p.limite_consultas_dia,
    p.limite_peca_mes,
    a.status,
    a.data_inicio,
    a.data_fim,
    a.em_trial,
    a.trial_ate
FROM assinatura a
JOIN usuario u ON a.usuario_id = u.id
JOIN plano p ON a.plano_id = p.id
WHERE a.status = 'active'
  AND (a.data_fim IS NULL OR a.data_fim > NOW());

COMMENT ON VIEW v_assinaturas_ativas IS 'View de assinaturas ativas com informações do plano';


-- ================================================================================
-- FIM DA MIGRATION 004
-- ================================================================================
