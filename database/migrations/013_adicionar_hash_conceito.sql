-- ================================================================================
-- MIGRATION 013: HASH DE CONCEITO PARA QUESTÕES
-- ================================================================================
-- Objetivo: Permitir importação de variações de questões sem duplicatas falsas
-- Data: 2025-12-25
-- Prioridade: P0 (CRÍTICA)
-- ================================================================================
--
-- CONTEXTO:
-- OAB cria variações anuais de questões (mesmo conceito, enunciado diferente).
-- Sistema atual rejeita 91% das questões como duplicatas.
--
-- SOLUÇÃO:
-- - codigo_questao: Único por variação (permite importar todas)
-- - hash_conceito: Agrupa variações (evita mostrar mesma questão para aluno)
--
-- ================================================================================

-- ================================================================================
-- 1. ADICIONAR CAMPO HASH_CONCEITO
-- ================================================================================

ALTER TABLE questoes_banco
ADD COLUMN IF NOT EXISTS hash_conceito VARCHAR(32);

-- Comentário
COMMENT ON COLUMN questoes_banco.hash_conceito IS
'MD5 hash para agrupar variações da mesma questão. Calculo: MD5(disciplina + topico + gabarito). Questões com mesmo hash_conceito são variações do mesmo conceito e não devem ser mostradas ao mesmo aluno.';


-- ================================================================================
-- 2. ÍNDICE PARA BUSCA EFICIENTE
-- ================================================================================

CREATE INDEX IF NOT EXISTS idx_questao_hash_conceito
ON questoes_banco(hash_conceito);

COMMENT ON INDEX idx_questao_hash_conceito IS
'Índice para agrupar variações de questões e evitar mostrar conceitos repetidos ao aluno.';


-- ================================================================================
-- 3. VALIDAÇÃO DE FORMATO
-- ================================================================================

-- Validar que hash_conceito tem exatamente 32 caracteres (MD5) quando não é NULL
ALTER TABLE questoes_banco
ADD CONSTRAINT check_hash_conceito_length
CHECK (hash_conceito IS NULL OR LENGTH(hash_conceito) = 32);


-- ================================================================================
-- 4. ESTATÍSTICAS DE VARIAÇÕES
-- ================================================================================

CREATE OR REPLACE FUNCTION estatisticas_variacoes_questoes()
RETURNS TABLE (
    total_questoes BIGINT,
    total_conceitos BIGINT,
    conceitos_com_variacoes BIGINT,
    max_variacoes_por_conceito INTEGER,
    media_variacoes_por_conceito NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_questoes,
        COUNT(DISTINCT hash_conceito)::BIGINT as total_conceitos,
        COUNT(*) FILTER (WHERE variacoes > 1)::BIGINT as conceitos_com_variacoes,
        MAX(variacoes)::INTEGER as max_variacoes_por_conceito,
        ROUND(AVG(variacoes), 2) as media_variacoes_por_conceito
    FROM (
        SELECT hash_conceito, COUNT(*) as variacoes
        FROM questoes_banco
        WHERE hash_conceito IS NOT NULL
        GROUP BY hash_conceito
    ) subquery;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION estatisticas_variacoes_questoes IS
'Retorna estatísticas sobre questões e suas variações agrupadas por hash_conceito.';


-- ================================================================================
-- 5. VIEW DE VARIAÇÕES
-- ================================================================================

CREATE OR REPLACE VIEW view_questoes_variacoes AS
SELECT
    hash_conceito,
    COUNT(*) as total_variacoes,
    MIN(disciplina) as disciplina,
    MIN(topico) as topico,
    MIN(alternativa_correta) as gabarito,
    ARRAY_AGG(codigo_questao ORDER BY created_at) as codigos_variacoes,
    MIN(created_at) as primeira_criacao,
    MAX(created_at) as ultima_criacao
FROM questoes_banco
WHERE hash_conceito IS NOT NULL
GROUP BY hash_conceito
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;

COMMENT ON VIEW view_questoes_variacoes IS
'Mostra questões agrupadas por conceito (hash_conceito), destacando conceitos com múltiplas variações.';


-- ================================================================================
-- 6. FUNÇÃO PARA BUSCAR VARIAÇÕES DE UMA QUESTÃO
-- ================================================================================

CREATE OR REPLACE FUNCTION buscar_variacoes_questao(p_codigo_questao VARCHAR)
RETURNS TABLE (
    codigo_questao VARCHAR,
    enunciado TEXT,
    alternativa_correta VARCHAR,
    created_at TIMESTAMP
) AS $$
DECLARE
    v_hash_conceito VARCHAR(32);
BEGIN
    -- Buscar hash_conceito da questão informada
    SELECT q.hash_conceito INTO v_hash_conceito
    FROM questoes_banco q
    WHERE q.codigo_questao = p_codigo_questao;

    -- Se não encontrou ou não tem hash_conceito, retornar vazio
    IF v_hash_conceito IS NULL THEN
        RETURN;
    END IF;

    -- Retornar todas as variações deste conceito
    RETURN QUERY
    SELECT
        q.codigo_questao,
        q.enunciado,
        q.alternativa_correta,
        q.created_at
    FROM questoes_banco q
    WHERE q.hash_conceito = v_hash_conceito
    ORDER BY q.created_at;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION buscar_variacoes_questao IS
'Busca todas as variações de uma questão (mesmo conceito, enunciados diferentes).';


-- ================================================================================
-- FIM DA MIGRATION 013
-- ================================================================================
