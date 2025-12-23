-- ================================================================================
-- MIGRATION 006: GOVERNANÇA E COMPLIANCE JURÍDICO
-- ================================================================================
-- Objetivo: Estrutura para compliance LGPD e responsabilidade jurídica
-- Data: 2025-12-17
-- ================================================================================

-- ================================================================================
-- 1. TABELA DE TERMOS E POLÍTICAS
-- ================================================================================

CREATE TABLE IF NOT EXISTS termo_politica (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    tipo VARCHAR(50) NOT NULL,  -- termos_uso, privacidade, uso_aceitavel
    versao VARCHAR(20) NOT NULL,
    titulo TEXT NOT NULL,

    -- Conteúdo
    conteudo TEXT NOT NULL,
    resumo TEXT,

    -- Vigência
    data_publicacao TIMESTAMP NOT NULL DEFAULT NOW(),
    data_vigencia TIMESTAMP NOT NULL,
    data_expiracao TIMESTAMP,

    -- Estado
    ativo BOOLEAN DEFAULT TRUE,
    obrigatorio BOOLEAN DEFAULT TRUE,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraint única: apenas uma versão ativa por tipo
    UNIQUE (tipo, ativo, data_expiracao)
);

-- Índices
CREATE INDEX idx_termo_politica_tipo ON termo_politica(tipo);
CREATE INDEX idx_termo_politica_ativo ON termo_politica(ativo);
CREATE INDEX idx_termo_politica_vigencia ON termo_politica(data_vigencia);

-- Comentários
COMMENT ON TABLE termo_politica IS 'Termos de uso e políticas do sistema';


-- ================================================================================
-- 2. TABELA DE ACEITAÇÃO DE TERMOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS aceitacao_termo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    termo_politica_id UUID NOT NULL REFERENCES termo_politica(id),

    -- Aceitação
    data_aceitacao TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_origem INET,
    user_agent TEXT,

    -- Metadados
    aceite_explicito BOOLEAN DEFAULT TRUE,
    versao_aceita VARCHAR(20) NOT NULL,

    -- Constraint única: usuário aceita apenas uma vez cada termo
    UNIQUE (usuario_id, termo_politica_id)
);

-- Índices
CREATE INDEX idx_aceitacao_termo_usuario_id ON aceitacao_termo(usuario_id);
CREATE INDEX idx_aceitacao_termo_data ON aceitacao_termo(data_aceitacao);

-- Comentários
COMMENT ON TABLE aceitacao_termo IS 'Registro de aceitação de termos e políticas';


-- ================================================================================
-- 3. TABELA DE LOGS LEGAIS (LGPD)
-- ================================================================================

CREATE TABLE IF NOT EXISTS log_legal (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID REFERENCES usuario(id) ON DELETE SET NULL,

    -- Tipo de ação
    tipo_acao VARCHAR(100) NOT NULL,
    categoria VARCHAR(50) NOT NULL,  -- acesso_dados, modificacao, exclusao, exportacao

    -- Descrição
    descricao TEXT NOT NULL,
    recurso_acessado VARCHAR(255),

    -- Contexto
    ip_origem INET,
    user_agent TEXT,
    dados_acessados JSONB,

    -- Consentimento
    consentimento_presente BOOLEAN DEFAULT FALSE,
    base_legal VARCHAR(100),  -- consentimento, legítimo_interesse, obrigação_legal

    -- Timestamp
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Retenção
    data_anonimizacao TIMESTAMP,
    anonimizado BOOLEAN DEFAULT FALSE
);

-- Índices
CREATE INDEX idx_log_legal_usuario_id ON log_legal(usuario_id);
CREATE INDEX idx_log_legal_tipo_acao ON log_legal(tipo_acao);
CREATE INDEX idx_log_legal_categoria ON log_legal(categoria);
CREATE INDEX idx_log_legal_timestamp ON log_legal(timestamp);
CREATE INDEX idx_log_legal_anonimizado ON log_legal(anonimizado);

-- Comentários
COMMENT ON TABLE log_legal IS 'Logs de ações sensíveis para compliance LGPD';


-- ================================================================================
-- 4. TABELA DE AVISOS OBRIGATÓRIOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS aviso_obrigatorio (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    codigo VARCHAR(100) NOT NULL UNIQUE,
    titulo TEXT NOT NULL,
    mensagem TEXT NOT NULL,

    -- Contexto de exibição
    contexto VARCHAR(50) NOT NULL,  -- pre_sessao, pre_peca, pre_cadastro
    tipo_aviso VARCHAR(50) NOT NULL,  -- disclaimer, warning, info

    -- Configuração
    obrigatorio BOOLEAN DEFAULT TRUE,
    requer_confirmacao BOOLEAN DEFAULT TRUE,
    exibir_sempre BOOLEAN DEFAULT TRUE,  -- ou apenas 1x

    -- Estado
    ativo BOOLEAN DEFAULT TRUE,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_aviso_obrigatorio_codigo ON aviso_obrigatorio(codigo);
CREATE INDEX idx_aviso_obrigatorio_contexto ON aviso_obrigatorio(contexto);
CREATE INDEX idx_aviso_obrigatorio_ativo ON aviso_obrigatorio(ativo);

-- Comentários
COMMENT ON TABLE aviso_obrigatorio IS 'Avisos e disclaimers obrigatórios do sistema';


-- ================================================================================
-- 5. TABELA DE CONFIRMAÇÃO DE AVISOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS confirmacao_aviso (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,
    aviso_obrigatorio_id UUID NOT NULL REFERENCES aviso_obrigatorio(id),

    -- Confirmação
    data_confirmacao TIMESTAMP NOT NULL DEFAULT NOW(),
    ip_origem INET,

    -- Contexto
    sessao_id UUID,  -- Referência opcional à sessão
    contexto_exibicao VARCHAR(100)
);

-- Índices
CREATE INDEX idx_confirmacao_aviso_usuario_id ON confirmacao_aviso(usuario_id);
CREATE INDEX idx_confirmacao_aviso_data ON confirmacao_aviso(data_confirmacao);

-- Comentários
COMMENT ON TABLE confirmacao_aviso IS 'Registro de confirmação de avisos pelo usuário';


-- ================================================================================
-- 6. TABELA DE SOLICITAÇÕES LGPD
-- ================================================================================

CREATE TABLE IF NOT EXISTS solicitacao_lgpd (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamentos
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,

    -- Tipo de solicitação
    tipo_solicitacao VARCHAR(50) NOT NULL,  -- acesso, retificacao, exclusao, portabilidade, oposicao
    status VARCHAR(50) NOT NULL DEFAULT 'pendente',  -- pendente, processando, concluida, rejeitada

    -- Descrição
    descricao TEXT,
    justificativa_rejeicao TEXT,

    -- Processamento
    data_solicitacao TIMESTAMP DEFAULT NOW(),
    data_conclusao TIMESTAMP,
    processado_por UUID REFERENCES usuario(id),

    -- Arquivos gerados
    arquivo_exportacao_url TEXT,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_solicitacao_lgpd_usuario_id ON solicitacao_lgpd(usuario_id);
CREATE INDEX idx_solicitacao_lgpd_tipo ON solicitacao_lgpd(tipo_solicitacao);
CREATE INDEX idx_solicitacao_lgpd_status ON solicitacao_lgpd(status);
CREATE INDEX idx_solicitacao_lgpd_data ON solicitacao_lgpd(data_solicitacao);

-- Comentários
COMMENT ON TABLE solicitacao_lgpd IS 'Solicitações de direitos LGPD pelos usuários';


-- ================================================================================
-- 7. AVISOS OBRIGATÓRIOS INICIAIS
-- ================================================================================

-- Aviso: Início de Sessão OAB
INSERT INTO aviso_obrigatorio (
    id, codigo, titulo, mensagem, contexto, tipo_aviso,
    obrigatorio, requer_confirmacao, exibir_sempre, ativo
) VALUES (
    gen_random_uuid(),
    'disclaimer_pre_sessao_oab',
    'AVISO IMPORTANTE',
    'Este sistema destina-se EXCLUSIVAMENTE à preparação para o Exame da OAB.

ESTE SISTEMA NÃO:
• Substitui a orientação de advogado constituído
• Fornece aconselhamento jurídico final sobre casos reais
• Estabelece relação advogado-cliente
• Deve ser usado para decisões jurídicas concretas

ESTE SISTEMA É:
• Uma ferramenta educacional de preparação para o Exame da OAB
• Um simulador de questões e situações típicas do exame
• Um recurso de estudo e prática

Para orientação jurídica sobre casos reais, consulte um advogado devidamente inscrito na OAB.

Ao continuar, você confirma que compreende estas limitações.',
    'pre_sessao',
    'disclaimer',
    TRUE,
    TRUE,
    TRUE,
    TRUE
) ON CONFLICT (codigo) DO NOTHING;

-- Aviso: Geração de Peça Processual (quando habilitado)
INSERT INTO aviso_obrigatorio (
    id, codigo, titulo, mensagem, contexto, tipo_aviso,
    obrigatorio, requer_confirmacao, exibir_sempre, ativo
) VALUES (
    gen_random_uuid(),
    'disclaimer_pre_peca',
    'AVISO - PRÁTICA DE PEÇA PROCESSUAL',
    'A peça processual gerada é EXCLUSIVAMENTE para fins de PRÁTICA e TREINAMENTO para o Exame da OAB.

NÃO USE ESTA PEÇA:
• Em processos judiciais reais
• Para protocolo em qualquer instância
• Como modelo definitivo para casos concretos

ESTA PEÇA É:
• Um exercício de preparação para a prova prática da OAB
• Um modelo de estudo e aprendizado
• Gerada por IA para fins educacionais

Para elaboração de peças processuais em casos reais, consulte um advogado.',
    'pre_peca',
    'disclaimer',
    TRUE,
    TRUE,
    TRUE,
    TRUE
) ON CONFLICT (codigo) DO NOTHING;

-- Aviso: Cadastro Inicial
INSERT INTO aviso_obrigatorio (
    id, codigo, titulo, mensagem, contexto, tipo_aviso,
    obrigatorio, requer_confirmacao, exibir_sempre, ativo
) VALUES (
    gen_random_uuid(),
    'info_cadastro_inicial',
    'Bem-vindo à DOUTORA IA/OAB',
    'Sistema de preparação para o Exame da Ordem dos Advogados do Brasil.

FINALIDADE:
Auxiliar estudantes e bacharéis em Direito na preparação para as provas da OAB através de questões, simulados e prática de peças processuais.

LIMITAÇÕES:
Este sistema NÃO substitui orientação jurídica profissional para casos reais. Consulte sempre um advogado inscrito na OAB para questões jurídicas concretas.

SEUS DADOS:
Seus dados pessoais são tratados conforme nossa Política de Privacidade, em conformidade com a LGPD (Lei 13.709/2018).',
    'pre_cadastro',
    'info',
    FALSE,
    FALSE,
    FALSE,
    TRUE
) ON CONFLICT (codigo) DO NOTHING;


-- ================================================================================
-- 8. TRIGGERS
-- ================================================================================

CREATE TRIGGER trigger_termo_politica_updated_at
    BEFORE UPDATE ON termo_politica
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_solicitacao_lgpd_updated_at
    BEFORE UPDATE ON solicitacao_lgpd
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_aviso_obrigatorio_updated_at
    BEFORE UPDATE ON aviso_obrigatorio
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- ================================================================================
-- 9. FUNÇÕES DE COMPLIANCE
-- ================================================================================

CREATE OR REPLACE FUNCTION verificar_aceitacao_termos(p_usuario_id UUID)
RETURNS TABLE (
    termos_aceitos BOOLEAN,
    termos_pendentes TEXT[]
) AS $$
DECLARE
    v_termos_pendentes TEXT[];
BEGIN
    -- Buscar termos obrigatórios não aceitos
    SELECT ARRAY_AGG(tp.tipo)
    INTO v_termos_pendentes
    FROM termo_politica tp
    LEFT JOIN aceitacao_termo at ON tp.id = at.termo_politica_id
        AND at.usuario_id = p_usuario_id
    WHERE tp.ativo = TRUE
      AND tp.obrigatorio = TRUE
      AND tp.data_vigencia <= NOW()
      AND (tp.data_expiracao IS NULL OR tp.data_expiracao > NOW())
      AND at.id IS NULL;

    -- Retornar resultado
    RETURN QUERY SELECT
        (v_termos_pendentes IS NULL OR ARRAY_LENGTH(v_termos_pendentes, 1) = 0) AS termos_aceitos,
        COALESCE(v_termos_pendentes, ARRAY[]::TEXT[]) AS termos_pendentes;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verificar_aceitacao_termos IS 'Verifica se usuário aceitou todos os termos obrigatórios';


CREATE OR REPLACE FUNCTION registrar_acao_sensivel(
    p_usuario_id UUID,
    p_tipo_acao VARCHAR,
    p_descricao TEXT,
    p_recurso VARCHAR DEFAULT NULL,
    p_dados_acessados JSONB DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    v_log_id := gen_random_uuid();

    INSERT INTO log_legal (
        id, usuario_id, tipo_acao, categoria, descricao,
        recurso_acessado, dados_acessados, timestamp
    ) VALUES (
        v_log_id, p_usuario_id, p_tipo_acao, 'acesso_dados', p_descricao,
        p_recurso, p_dados_acessados, NOW()
    );

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION registrar_acao_sensivel IS 'Registra ação sensível para compliance LGPD';


-- ================================================================================
-- 10. POLÍTICA DE RETENÇÃO DE DADOS
-- ================================================================================

CREATE OR REPLACE FUNCTION anonimizar_dados_antigos()
RETURNS INTEGER AS $$
DECLARE
    v_registros_anonimizados INTEGER := 0;
BEGIN
    -- Anonimizar logs legais com mais de 5 anos
    UPDATE log_legal
    SET usuario_id = NULL,
        ip_origem = NULL,
        user_agent = NULL,
        dados_acessados = NULL,
        anonimizado = TRUE,
        data_anonimizacao = NOW()
    WHERE timestamp < NOW() - INTERVAL '5 years'
      AND anonimizado = FALSE;

    GET DIAGNOSTICS v_registros_anonimizados = ROW_COUNT;

    RETURN v_registros_anonimizados;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION anonimizar_dados_antigos IS 'Anonimiza dados conforme política de retenção LGPD';


-- ================================================================================
-- FIM DA MIGRATION 006
-- ================================================================================
