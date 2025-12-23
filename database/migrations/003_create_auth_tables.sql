-- ================================================================================
-- MIGRATION 003: TABELAS DE AUTENTICAÇÃO E USUÁRIOS - ETAPA 10.1
-- ================================================================================
-- Objetivo: Criar estrutura de autenticação JWT com roles e modos
-- Data: 2025-12-17
-- ================================================================================

-- ================================================================================
-- 1. TABELA DE USUÁRIOS
-- ================================================================================

CREATE TABLE IF NOT EXISTS usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    email VARCHAR(255) NOT NULL UNIQUE,
    nome_completo VARCHAR(255) NOT NULL,
    cpf VARCHAR(11) UNIQUE,  -- Opcional, para billing

    -- Autenticação
    senha_hash VARCHAR(255) NOT NULL,  -- bcrypt hash
    email_verificado BOOLEAN DEFAULT FALSE,
    token_verificacao VARCHAR(255),

    -- Role e modo (ETAPA 10.2)
    role VARCHAR(50) NOT NULL DEFAULT 'role_pedagogico',
    modo_atual VARCHAR(50) NOT NULL DEFAULT 'pedagogico',

    -- Status
    ativo BOOLEAN DEFAULT TRUE,
    bloqueado BOOLEAN DEFAULT FALSE,
    motivo_bloqueio TEXT,

    -- Metadados
    ultimo_login TIMESTAMP,
    ip_ultimo_login INET,
    tentativas_login_falhas INTEGER DEFAULT 0,
    bloqueado_ate TIMESTAMP,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP  -- Soft delete
);

-- Índices
CREATE INDEX idx_usuario_email ON usuario(email);
CREATE INDEX idx_usuario_cpf ON usuario(cpf);
CREATE INDEX idx_usuario_role ON usuario(role);
CREATE INDEX idx_usuario_ativo ON usuario(ativo);

-- Comentários
COMMENT ON TABLE usuario IS 'Usuários do sistema com autenticação JWT';
COMMENT ON COLUMN usuario.role IS 'Role: role_pedagogico ou role_profissional';
COMMENT ON COLUMN usuario.modo_atual IS 'Modo: pedagogico ou profissional';
COMMENT ON COLUMN usuario.tentativas_login_falhas IS 'Reset após login bem-sucedido';


-- ================================================================================
-- 2. TABELA DE TOKENS DE REFRESH
-- ================================================================================

CREATE TABLE IF NOT EXISTS token_refresh (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamento
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,

    -- Token
    token VARCHAR(500) NOT NULL UNIQUE,
    token_family UUID NOT NULL,  -- Para detectar reutilização (rotation)

    -- Validade
    expira_em TIMESTAMP NOT NULL,
    revogado BOOLEAN DEFAULT FALSE,
    revogado_em TIMESTAMP,
    motivo_revogacao TEXT,

    -- Metadados
    ip_origem INET,
    user_agent TEXT,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_token_refresh_usuario_id ON token_refresh(usuario_id);
CREATE INDEX idx_token_refresh_token ON token_refresh(token);
CREATE INDEX idx_token_refresh_family ON token_refresh(token_family);
CREATE INDEX idx_token_refresh_expira_em ON token_refresh(expira_em);
CREATE INDEX idx_token_refresh_revogado ON token_refresh(revogado);

-- Comentários
COMMENT ON TABLE token_refresh IS 'Tokens de refresh JWT (7 dias de validade)';
COMMENT ON COLUMN token_refresh.token_family IS 'Família de tokens para detectar reutilização';


-- ================================================================================
-- 3. TABELA DE SESSÕES
-- ================================================================================

CREATE TABLE IF NOT EXISTS sessao_usuario (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamento
    usuario_id UUID NOT NULL REFERENCES usuario(id) ON DELETE CASCADE,

    -- Sessão
    token_acesso_jti VARCHAR(255) NOT NULL UNIQUE,  -- JWT ID do access token
    token_refresh_id UUID REFERENCES token_refresh(id) ON DELETE CASCADE,

    -- Validade
    iniciada_em TIMESTAMP DEFAULT NOW(),
    expira_em TIMESTAMP NOT NULL,
    finalizada_em TIMESTAMP,

    -- Metadados
    ip_origem INET,
    user_agent TEXT,
    dispositivo VARCHAR(100),
    localizacao JSONB,

    -- Status
    ativa BOOLEAN DEFAULT TRUE,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_sessao_usuario_usuario_id ON sessao_usuario(usuario_id);
CREATE INDEX idx_sessao_usuario_jti ON sessao_usuario(token_acesso_jti);
CREATE INDEX idx_sessao_usuario_ativa ON sessao_usuario(ativa);
CREATE INDEX idx_sessao_usuario_expira_em ON sessao_usuario(expira_em);

-- Comentários
COMMENT ON TABLE sessao_usuario IS 'Sessões ativas de usuários (access tokens)';
COMMENT ON COLUMN sessao_usuario.token_acesso_jti IS 'JWT ID para validação de token de acesso';


-- ================================================================================
-- 4. TABELA DE LOG DE AUTENTICAÇÃO
-- ================================================================================

CREATE TABLE IF NOT EXISTS log_autenticacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Relacionamento
    usuario_id UUID REFERENCES usuario(id) ON DELETE SET NULL,

    -- Evento
    tipo_evento VARCHAR(50) NOT NULL,  -- login, logout, login_falha, token_refresh, etc.
    email_tentativa VARCHAR(255),
    sucesso BOOLEAN NOT NULL,
    motivo_falha TEXT,

    -- Metadados
    ip_origem INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Contexto adicional
    detalhes JSONB
);

-- Índices
CREATE INDEX idx_log_autenticacao_usuario_id ON log_autenticacao(usuario_id);
CREATE INDEX idx_log_autenticacao_tipo_evento ON log_autenticacao(tipo_evento);
CREATE INDEX idx_log_autenticacao_timestamp ON log_autenticacao(timestamp);
CREATE INDEX idx_log_autenticacao_sucesso ON log_autenticacao(sucesso);

-- Comentários
COMMENT ON TABLE log_autenticacao IS 'Log completo de eventos de autenticação';


-- ================================================================================
-- 5. TABELA DE SECRETS PARA JWT (ROTAÇÃO)
-- ================================================================================

CREATE TABLE IF NOT EXISTS jwt_secret (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Secret
    secret_key VARCHAR(500) NOT NULL,

    -- Validade
    ativo BOOLEAN DEFAULT TRUE,
    valido_de TIMESTAMP NOT NULL DEFAULT NOW(),
    valido_ate TIMESTAMP,

    -- Tipo
    tipo VARCHAR(50) NOT NULL,  -- 'access' ou 'refresh'

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    rotacionado_em TIMESTAMP
);

-- Índices
CREATE INDEX idx_jwt_secret_ativo ON jwt_secret(ativo);
CREATE INDEX idx_jwt_secret_tipo ON jwt_secret(tipo);
CREATE INDEX idx_jwt_secret_valido_de ON jwt_secret(valido_de);

-- Comentários
COMMENT ON TABLE jwt_secret IS 'Secrets para assinatura JWT com suporte a rotação';


-- ================================================================================
-- 6. CONSTRAINT DE ROLES VÁLIDOS
-- ================================================================================

ALTER TABLE usuario
ADD CONSTRAINT check_role_valido
CHECK (role IN ('role_pedagogico', 'role_profissional', 'role_admin'));

ALTER TABLE usuario
ADD CONSTRAINT check_modo_valido
CHECK (modo_atual IN ('pedagogico', 'profissional'));


-- ================================================================================
-- 7. TRIGGER PARA updated_at
-- ================================================================================

CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_usuario_updated_at
    BEFORE UPDATE ON usuario
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- ================================================================================
-- 8. FUNÇÃO PARA LIMPAR TOKENS EXPIRADOS
-- ================================================================================

CREATE OR REPLACE FUNCTION limpar_tokens_expirados()
RETURNS INTEGER AS $$
DECLARE
    tokens_removidos INTEGER;
BEGIN
    -- Remover tokens de refresh expirados
    DELETE FROM token_refresh
    WHERE expira_em < NOW()
      AND revogado = FALSE;

    GET DIAGNOSTICS tokens_removidos = ROW_COUNT;

    -- Marcar sessões expiradas como inativas
    UPDATE sessao_usuario
    SET ativa = FALSE,
        finalizada_em = NOW()
    WHERE expira_em < NOW()
      AND ativa = TRUE;

    RETURN tokens_removidos;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION limpar_tokens_expirados IS 'Remove tokens expirados e marca sessões como inativas';


-- ================================================================================
-- 9. FUNÇÃO PARA REVOGAR TODOS OS TOKENS DE UM USUÁRIO
-- ================================================================================

CREATE OR REPLACE FUNCTION revogar_tokens_usuario(p_usuario_id UUID)
RETURNS INTEGER AS $$
DECLARE
    tokens_revogados INTEGER;
BEGIN
    -- Revogar todos os tokens de refresh
    UPDATE token_refresh
    SET revogado = TRUE,
        revogado_em = NOW(),
        motivo_revogacao = 'Revogação manual de todos os tokens'
    WHERE usuario_id = p_usuario_id
      AND revogado = FALSE;

    GET DIAGNOSTICS tokens_revogados = ROW_COUNT;

    -- Finalizar todas as sessões
    UPDATE sessao_usuario
    SET ativa = FALSE,
        finalizada_em = NOW()
    WHERE usuario_id = p_usuario_id
      AND ativa = TRUE;

    RETURN tokens_revogados;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION revogar_tokens_usuario IS 'Revoga todos os tokens e finaliza sessões de um usuário';


-- ================================================================================
-- 10. PERMISSÕES (ROLE-BASED ACCESS CONTROL)
-- ================================================================================

-- Garantir que role_profissional NUNCA acessa gabarito_questao
REVOKE ALL ON gabarito_questao FROM PUBLIC;
GRANT SELECT ON gabarito_questao TO role_pedagogico;
-- role_profissional NÃO recebe permissão

-- role_pedagogico acessa gabarito apenas após responder
-- (implementado em application layer, não em DB)


-- ================================================================================
-- 11. DADOS INICIAIS (ADMIN)
-- ================================================================================

-- Inserir usuário admin padrão (senha: Admin@123 - ALTERAR EM PRODUÇÃO!)
INSERT INTO usuario (
    email,
    nome_completo,
    senha_hash,
    email_verificado,
    role,
    modo_atual,
    ativo
) VALUES (
    'admin@juris-ia.com',
    'Administrador',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYfHK4KqHyi',  -- Admin@123
    TRUE,
    'role_admin',
    'profissional',
    TRUE
) ON CONFLICT (email) DO NOTHING;


-- ================================================================================
-- FIM DA MIGRATION 003
-- ================================================================================
