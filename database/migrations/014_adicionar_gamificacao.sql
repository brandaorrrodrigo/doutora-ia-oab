-- Migration 014: Sistema de Gamificação
-- Adiciona campos de XP, níveis, streaks e conquistas

-- 1. Adicionar campos de gamificação ao perfil_juridico
ALTER TABLE perfil_juridico
ADD COLUMN IF NOT EXISTS nivel INTEGER DEFAULT 1 NOT NULL,
ADD COLUMN IF NOT EXISTS total_xp INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS conquistas JSONB DEFAULT '[]'::jsonb NOT NULL,
ADD COLUMN IF NOT EXISTS ultima_atividade TIMESTAMP,
ADD COLUMN IF NOT EXISTS streak_maximo INTEGER DEFAULT 0 NOT NULL;

-- 2. Adicionar constraints
ALTER TABLE perfil_juridico
ADD CONSTRAINT check_nivel_range CHECK (nivel >= 1 AND nivel <= 100),
ADD CONSTRAINT check_xp_positivo CHECK (total_xp >= 0),
ADD CONSTRAINT check_streak_maximo CHECK (streak_maximo >= 0);

-- 3. Criar índices para performance
CREATE INDEX IF NOT EXISTS idx_perfil_nivel ON perfil_juridico(nivel);
CREATE INDEX IF NOT EXISTS idx_perfil_xp ON perfil_juridico(total_xp);
CREATE INDEX IF NOT EXISTS idx_perfil_streak ON perfil_juridico(sequencia_dias_consecutivos);
CREATE INDEX IF NOT EXISTS idx_perfil_conquistas_gin ON perfil_juridico USING gin(conquistas);

-- 4. Atualizar registros existentes
UPDATE perfil_juridico
SET
    nivel = CASE
        WHEN pontuacao_global < 100 THEN 1
        WHEN pontuacao_global < 300 THEN 2
        WHEN pontuacao_global < 600 THEN 3
        WHEN pontuacao_global < 1000 THEN 4
        ELSE 5
    END,
    total_xp = pontuacao_global,
    ultima_atividade = COALESCE(data_ultima_atualizacao_perfil, NOW())
WHERE nivel IS NULL OR total_xp IS NULL;

-- 5. Criar tabela de conquistas disponíveis
CREATE TABLE IF NOT EXISTS conquistas_catalogo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT NOT NULL,
    icone VARCHAR(20) NOT NULL,
    categoria VARCHAR(50) NOT NULL,
    xp_recompensa INTEGER DEFAULT 0,
    criterio JSONB NOT NULL,
    raridade VARCHAR(20) DEFAULT 'COMUM',
    ativa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

-- 6. Inserir conquistas padrão
INSERT INTO conquistas_catalogo (codigo, nome, descricao, icone, categoria, xp_recompensa, criterio, raridade) VALUES
-- Conquistas de Início
('PRIMEIRA_QUESTAO', 'Primeira Questão', 'Respondeu sua primeira questão', '🎯', 'inicio', 10, '{"tipo": "questoes_respondidas", "minimo": 1}', 'COMUM'),
('PRIMEIRA_SESSAO', 'Primeira Sessão', 'Completou sua primeira sessão de estudo', '📚', 'inicio', 20, '{"tipo": "sessoes_completas", "minimo": 1}', 'COMUM'),
('PRIMEIRA_PECA', 'Primeira Peça', 'Escreveu sua primeira peça processual', '⚖️', 'inicio', 30, '{"tipo": "pecas_concluidas", "minimo": 1}', 'COMUM'),

-- Conquistas de Questões
('10_QUESTOES', 'Estudante Dedicado', 'Respondeu 10 questões', '📖', 'questoes', 50, '{"tipo": "questoes_respondidas", "minimo": 10}', 'COMUM'),
('50_QUESTOES', 'Praticante', 'Respondeu 50 questões', '📝', 'questoes', 100, '{"tipo": "questoes_respondidas", "minimo": 50}', 'INCOMUM'),
('100_QUESTOES', 'Dedicado', 'Respondeu 100 questões', '📚', 'questoes', 200, '{"tipo": "questoes_respondidas", "minimo": 100}', 'INCOMUM'),
('500_QUESTOES', 'Expert', 'Respondeu 500 questões', '🎓', 'questoes', 500, '{"tipo": "questoes_respondidas", "minimo": 500}', 'RARA'),
('1000_QUESTOES', 'Mestre', 'Respondeu 1000 questões', '👨‍⚖️', 'questoes', 1000, '{"tipo": "questoes_respondidas", "minimo": 1000}', 'EPICA'),

-- Conquistas de Acertos
('ACERTO_70', 'Bom Desempenho', 'Atingiu 70% de taxa de acerto', '✅', 'acertos', 150, '{"tipo": "taxa_acerto", "minimo": 70}', 'INCOMUM'),
('ACERTO_80', 'Ótimo Desempenho', 'Atingiu 80% de taxa de acerto', '🌟', 'acertos', 300, '{"tipo": "taxa_acerto", "minimo": 80}', 'RARA'),
('ACERTO_90', 'Desempenho Excepcional', 'Atingiu 90% de taxa de acerto', '⭐', 'acertos', 500, '{"tipo": "taxa_acerto", "minimo": 90}', 'EPICA'),

-- Conquistas de Streak
('STREAK_3', 'Comprometido', '3 dias consecutivos de estudo', '🔥', 'streak', 50, '{"tipo": "streak", "minimo": 3}', 'COMUM'),
('STREAK_7', 'Disciplinado', '7 dias consecutivos de estudo', '🔥🔥', 'streak', 100, '{"tipo": "streak", "minimo": 7}', 'INCOMUM'),
('STREAK_15', 'Determinado', '15 dias consecutivos de estudo', '🔥🔥🔥', 'streak', 200, '{"tipo": "streak", "minimo": 15}', 'RARA'),
('STREAK_30', 'Imparável', '30 dias consecutivos de estudo', '🔥🔥🔥🔥', 'streak', 500, '{"tipo": "streak", "minimo": 30}', 'EPICA'),

-- Conquistas de Peças
('5_PECAS', 'Redator Iniciante', 'Escreveu 5 peças processuais', '📄', 'pecas', 100, '{"tipo": "pecas_concluidas", "minimo": 5}', 'COMUM'),
('10_PECAS', 'Redator Competente', 'Escreveu 10 peças processuais', '📋', 'pecas', 200, '{"tipo": "pecas_concluidas", "minimo": 10}', 'INCOMUM'),
('20_PECAS', 'Redator Expert', 'Escreveu 20 peças processuais', '📜', 'pecas', 400, '{"tipo": "pecas_concluidas", "minimo": 20}', 'RARA'),

-- Conquistas de Níveis
('NIVEL_5', 'Aprendiz', 'Atingiu o nível 5', '🎯', 'niveis', 100, '{"tipo": "nivel", "minimo": 5}', 'COMUM'),
('NIVEL_10', 'Intermediário', 'Atingiu o nível 10', '🎯🎯', 'niveis', 250, '{"tipo": "nivel", "minimo": 10}', 'INCOMUM'),
('NIVEL_20', 'Avançado', 'Atingiu o nível 20', '🎯🎯🎯', 'niveis', 500, '{"tipo": "nivel", "minimo": 20}', 'RARA'),
('NIVEL_50', 'Lendário', 'Atingiu o nível 50', '👑', 'niveis', 2000, '{"tipo": "nivel", "minimo": 50}', 'LENDARIA')

ON CONFLICT (codigo) DO NOTHING;

-- 7. Criar tabela de histórico de XP (para tracking)
CREATE TABLE IF NOT EXISTS historico_xp (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    xp_ganho INTEGER NOT NULL,
    motivo VARCHAR(100) NOT NULL,
    detalhes JSONB,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_historico_xp_user ON historico_xp(user_id);
CREATE INDEX IF NOT EXISTS idx_historico_xp_created ON historico_xp(created_at DESC);

-- Comentários
COMMENT ON COLUMN perfil_juridico.nivel IS 'Nível do usuário baseado em XP (1-100)';
COMMENT ON COLUMN perfil_juridico.total_xp IS 'Total de XP acumulado pelo usuário';
COMMENT ON COLUMN perfil_juridico.conquistas IS 'Array de códigos de conquistas desbloqueadas';
COMMENT ON COLUMN perfil_juridico.ultima_atividade IS 'Data da última atividade para cálculo de streak';
COMMENT ON COLUMN perfil_juridico.streak_maximo IS 'Maior sequência de dias consecutivos atingida';
COMMENT ON TABLE conquistas_catalogo IS 'Catálogo de todas as conquistas disponíveis no sistema';
COMMENT ON TABLE historico_xp IS 'Histórico de ganho de XP por ação do usuário';
