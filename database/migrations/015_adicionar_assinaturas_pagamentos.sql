-- Migration 015: Adicionar Assinaturas e Pagamentos
-- Criado em: 2025-12-28
-- Descrição: Sistema de assinaturas e pagamentos com integração Stripe

-- Criar tabela de assinaturas
CREATE TABLE IF NOT EXISTS assinaturas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Dados do plano
    plano VARCHAR(50) NOT NULL DEFAULT 'GRATUITO',
    status VARCHAR(20) NOT NULL DEFAULT 'ATIVO',
    preco_mensal DECIMAL(10, 2) NOT NULL DEFAULT 0.00,

    -- Limites do plano
    sessoes_por_dia INTEGER DEFAULT 5,
    questoes_por_sessao INTEGER DEFAULT 10,
    acesso_chat_ia BOOLEAN DEFAULT FALSE,
    acesso_pecas BOOLEAN DEFAULT FALSE,
    acesso_relatorios BOOLEAN DEFAULT FALSE,
    acesso_simulados BOOLEAN DEFAULT TRUE,

    -- Datas
    data_inicio TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_fim TIMESTAMP,
    proxima_cobranca TIMESTAMP,
    cancelado_em TIMESTAMP,

    -- Integração Stripe
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    stripe_price_id VARCHAR(255),

    -- Metadados
    metadata JSONB,

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Indexes
    CONSTRAINT chk_plano CHECK (plano IN ('GRATUITO', 'PREMIUM', 'PRO')),
    CONSTRAINT chk_status CHECK (status IN ('ATIVO', 'CANCELADO', 'EXPIRADO', 'TRIAL', 'PAUSADO'))
);

-- Criar índices para assinaturas
CREATE INDEX IF NOT EXISTS idx_assinaturas_user_id ON assinaturas(user_id);
CREATE INDEX IF NOT EXISTS idx_assinaturas_plano ON assinaturas(plano);
CREATE INDEX IF NOT EXISTS idx_assinaturas_status ON assinaturas(status);
CREATE INDEX IF NOT EXISTS idx_assinaturas_stripe_customer ON assinaturas(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_assinaturas_stripe_subscription ON assinaturas(stripe_subscription_id);

-- Criar tabela de pagamentos
CREATE TABLE IF NOT EXISTS pagamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assinatura_id UUID NOT NULL REFERENCES assinaturas(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Dados do pagamento
    valor DECIMAL(10, 2) NOT NULL,
    moeda VARCHAR(3) DEFAULT 'BRL',
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
    metodo_pagamento VARCHAR(50),

    -- Integração Stripe
    stripe_payment_intent_id VARCHAR(255),
    stripe_charge_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),

    -- Datas
    data_pagamento TIMESTAMP,
    data_vencimento TIMESTAMP,

    -- Metadados
    metadata JSONB,
    mensagem_erro TEXT,

    -- Auditoria
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT chk_pagamento_status CHECK (status IN ('PENDENTE', 'PROCESSANDO', 'PAGO', 'FALHOU', 'REEMBOLSADO', 'CANCELADO'))
);

-- Criar índices para pagamentos
CREATE INDEX IF NOT EXISTS idx_pagamentos_assinatura_id ON pagamentos(assinatura_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_user_id ON pagamentos(user_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_status ON pagamentos(status);
CREATE INDEX IF NOT EXISTS idx_pagamentos_stripe_payment ON pagamentos(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_pagamentos_data_pagamento ON pagamentos(data_pagamento);

-- Criar função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_assinatura_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_pagamento_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Criar triggers
DROP TRIGGER IF EXISTS trigger_assinatura_updated_at ON assinaturas;
CREATE TRIGGER trigger_assinatura_updated_at
    BEFORE UPDATE ON assinaturas
    FOR EACH ROW
    EXECUTE FUNCTION update_assinatura_updated_at();

DROP TRIGGER IF EXISTS trigger_pagamento_updated_at ON pagamentos;
CREATE TRIGGER trigger_pagamento_updated_at
    BEFORE UPDATE ON pagamentos
    FOR EACH ROW
    EXECUTE FUNCTION update_pagamento_updated_at();

-- Criar assinatura gratuita padrão para usuários existentes
INSERT INTO assinaturas (user_id, plano, status, preco_mensal, sessoes_por_dia, questoes_por_sessao, acesso_chat_ia, acesso_pecas, acesso_relatorios, acesso_simulados)
SELECT
    id,
    'GRATUITO',
    'ATIVO',
    0.00,
    5,
    10,
    FALSE,
    FALSE,
    FALSE,
    TRUE
FROM users
WHERE NOT EXISTS (
    SELECT 1 FROM assinaturas WHERE assinaturas.user_id = users.id
);

-- Comentários
COMMENT ON TABLE assinaturas IS 'Assinaturas de usuários com integração Stripe';
COMMENT ON TABLE pagamentos IS 'Histórico de pagamentos dos usuários';
COMMENT ON COLUMN assinaturas.plano IS 'GRATUITO, PREMIUM ou PRO';
COMMENT ON COLUMN assinaturas.status IS 'ATIVO, CANCELADO, EXPIRADO, TRIAL ou PAUSADO';
COMMENT ON COLUMN pagamentos.status IS 'PENDENTE, PROCESSANDO, PAGO, FALHOU, REEMBOLSADO ou CANCELADO';
