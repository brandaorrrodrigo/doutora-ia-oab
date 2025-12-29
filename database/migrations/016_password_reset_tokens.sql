-- Migration 016: Password Reset Tokens
-- Data: 2025-12-28
-- Descrição: Tabela para armazenar tokens de recuperação de senha

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    used_at TIMESTAMP,

    -- Índices
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Índice para busca rápida por token
CREATE INDEX idx_password_reset_tokens_hash ON password_reset_tokens(token_hash);

-- Índice para busca por usuário
CREATE INDEX idx_password_reset_tokens_user ON password_reset_tokens(user_id);

-- Índice para cleanup de tokens expirados
CREATE INDEX idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);

-- Constraint: apenas um token ativo por usuário
CREATE UNIQUE INDEX idx_password_reset_active_token
ON password_reset_tokens(user_id)
WHERE used_at IS NULL;

COMMENT ON TABLE password_reset_tokens IS 'Tokens de recuperação de senha';
COMMENT ON COLUMN password_reset_tokens.token_hash IS 'Hash SHA-256 do token (nunca armazenar token em plain text)';
COMMENT ON COLUMN password_reset_tokens.expires_at IS 'Data de expiração do token (1 hora após criação)';
COMMENT ON COLUMN password_reset_tokens.used_at IS 'Data em que o token foi usado (NULL = ainda válido)';
