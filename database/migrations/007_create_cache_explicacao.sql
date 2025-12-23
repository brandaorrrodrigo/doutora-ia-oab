-- ================================================================================
-- MIGRATION 007: CACHE DE EXPLICAÇÕES LLM
-- ================================================================================
-- Objetivo: Cache de explicações geradas por LLM para otimizar custo e performance
-- Data: 2025-12-17
-- Prioridade: P0 (CRÍTICA)
-- ================================================================================

-- ================================================================================
-- 1. TABELA DE CACHE DE EXPLICAÇÕES
-- ================================================================================

CREATE TABLE IF NOT EXISTS cache_explicacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Chave de cache (MD5 hash)
    cache_key VARCHAR(32) UNIQUE NOT NULL,

    -- Explicação gerada
    explicacao TEXT NOT NULL,

    -- Expiração
    expires_at TIMESTAMP NOT NULL,

    -- Métricas de uso
    acessos INTEGER DEFAULT 1,

    -- Auditoria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_cache_explicacao_key ON cache_explicacao(cache_key);
CREATE INDEX idx_cache_explicacao_expires ON cache_explicacao(expires_at);
CREATE INDEX idx_cache_explicacao_acessos ON cache_explicacao(acessos DESC);

-- Comentário
COMMENT ON TABLE cache_explicacao IS 'Cache de explicações pedagógicas geradas por LLM';
COMMENT ON COLUMN cache_explicacao.cache_key IS 'MD5(questao_id + alternativa_escolhida + tipo_erro)';
COMMENT ON COLUMN cache_explicacao.expires_at IS 'Data de expiração do cache (TTL: 30 dias)';
COMMENT ON COLUMN cache_explicacao.acessos IS 'Número de vezes que esta explicação foi reutilizada';


-- ================================================================================
-- 2. TRIGGER DE UPDATED_AT
-- ================================================================================

CREATE TRIGGER trigger_cache_explicacao_updated_at
    BEFORE UPDATE ON cache_explicacao
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- ================================================================================
-- 3. FUNÇÃO DE LIMPEZA AUTOMÁTICA
-- ================================================================================

CREATE OR REPLACE FUNCTION limpar_cache_explicacao_expirado()
RETURNS INTEGER AS $$
DECLARE
    v_removidos INTEGER := 0;
BEGIN
    -- Remover explicações expiradas
    DELETE FROM cache_explicacao
    WHERE expires_at < NOW();

    GET DIAGNOSTICS v_removidos = ROW_COUNT;

    -- Log
    IF v_removidos > 0 THEN
        RAISE NOTICE 'Removidas % explicações expiradas do cache', v_removidos;
    END IF;

    RETURN v_removidos;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION limpar_cache_explicacao_expirado IS
'Remove explicações expiradas do cache. Executar diariamente via CRON.';


-- ================================================================================
-- 4. ESTATÍSTICAS DE CACHE
-- ================================================================================

CREATE OR REPLACE FUNCTION estatisticas_cache_explicacao()
RETURNS TABLE (
    total_explicacoes BIGINT,
    explicacoes_ativas BIGINT,
    explicacoes_expiradas BIGINT,
    total_acessos BIGINT,
    hit_rate_estimado NUMERIC,
    explicacao_mais_usada TEXT,
    max_acessos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_explicacoes,
        COUNT(*) FILTER (WHERE expires_at > NOW())::BIGINT as explicacoes_ativas,
        COUNT(*) FILTER (WHERE expires_at <= NOW())::BIGINT as explicacoes_expiradas,
        SUM(acessos)::BIGINT as total_acessos,
        CASE
            WHEN COUNT(*) > 0 THEN
                ROUND((SUM(acessos - 1)::NUMERIC / NULLIF(SUM(acessos), 0)) * 100, 2)
            ELSE 0
        END as hit_rate_estimado,
        (
            SELECT LEFT(explicacao, 100)
            FROM cache_explicacao
            WHERE expires_at > NOW()
            ORDER BY acessos DESC
            LIMIT 1
        ) as explicacao_mais_usada,
        COALESCE(MAX(acessos), 0)::INTEGER as max_acessos
    FROM cache_explicacao;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION estatisticas_cache_explicacao IS
'Retorna estatísticas sobre o cache de explicações';


-- ================================================================================
-- 5. ÍNDICE PARCIAL PARA EXPLICAÇÕES ATIVAS
-- ================================================================================

-- Índice parcial apenas para explicações não expiradas (mais eficiente)
CREATE INDEX idx_cache_explicacao_ativas
ON cache_explicacao(cache_key)
WHERE expires_at > NOW();


-- ================================================================================
-- 6. VALIDAÇÕES
-- ================================================================================

-- Validar que cache_key tem exatamente 32 caracteres (MD5)
ALTER TABLE cache_explicacao
ADD CONSTRAINT check_cache_key_length
CHECK (LENGTH(cache_key) = 32);

-- Validar que expires_at está no futuro quando criado
ALTER TABLE cache_explicacao
ADD CONSTRAINT check_expires_at_future
CHECK (expires_at > created_at);


-- ================================================================================
-- 7. POLÍTICA DE RETENÇÃO
-- ================================================================================

COMMENT ON CONSTRAINT check_expires_at_future ON cache_explicacao IS
'Garantir que TTL é definido no futuro. Padrão: 30 dias a partir da criação.';


-- ================================================================================
-- FIM DA MIGRATION 007
-- ================================================================================
