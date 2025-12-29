-- Migration 014: Adicionar tabelas de reset de senha e configurações de usuário
-- Data: 2025-12-28
-- Descrição: Implementa recuperação de senha e configurações personalizadas

-- 1. Adicionar coluna foto_perfil à tabela users
ALTER TABLE users ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(500);

-- 2. Criar tabela password_reset_tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,

    expira_em TIMESTAMP NOT NULL,
    usado BOOLEAN DEFAULT FALSE NOT NULL,
    usado_em TIMESTAMP,

    ip_solicitacao VARCHAR(45),
    user_agent VARCHAR(500),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índices para password_reset_tokens
CREATE INDEX IF NOT EXISTS idx_reset_token ON password_reset_tokens(token);
CREATE INDEX IF NOT EXISTS idx_reset_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_reset_expiracao ON password_reset_tokens(expira_em);

-- 3. Criar tabela user_settings
CREATE TABLE IF NOT EXISTS user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Preferências de notificação
    notificacao_email BOOLEAN DEFAULT TRUE,
    notificacao_push BOOLEAN DEFAULT TRUE,
    lembrete_diario BOOLEAN DEFAULT TRUE,
    horario_lembrete VARCHAR(5) DEFAULT '09:00',

    -- Preferências de estudo
    tema VARCHAR(20) DEFAULT 'light',
    questoes_por_sessao INTEGER DEFAULT 10,
    dificuldade_preferida VARCHAR(20) DEFAULT 'mista',

    -- Preferências de som
    som_ativado BOOLEAN DEFAULT TRUE,
    som_acerto BOOLEAN DEFAULT TRUE,
    som_erro BOOLEAN DEFAULT TRUE,

    -- Preferências de privacidade
    perfil_publico BOOLEAN DEFAULT FALSE,
    mostrar_ranking BOOLEAN DEFAULT TRUE,
    compartilhar_estatisticas BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Índice para user_settings
CREATE INDEX IF NOT EXISTS idx_settings_user ON user_settings(user_id);

-- 4. Criar função para limpar tokens expirados (executar diariamente via cron)
CREATE OR REPLACE FUNCTION limpar_tokens_expirados()
RETURNS void AS $$
BEGIN
    DELETE FROM password_reset_tokens
    WHERE expira_em < NOW() OR (usado = TRUE AND usado_em < NOW() - INTERVAL '7 days');
END;
$$ LANGUAGE plpgsql;

-- 5. Criar configurações padrão para usuários existentes
INSERT INTO user_settings (user_id)
SELECT id FROM users
WHERE id NOT IN (SELECT user_id FROM user_settings)
ON CONFLICT (user_id) DO NOTHING;

-- 6. Comentários nas tabelas
COMMENT ON TABLE password_reset_tokens IS 'Armazena tokens de recuperação de senha (válidos por 1 hora)';
COMMENT ON TABLE user_settings IS 'Configurações personalizadas do usuário';
COMMENT ON COLUMN users.foto_perfil IS 'URL da foto de perfil do usuário (CDN ou storage)';
