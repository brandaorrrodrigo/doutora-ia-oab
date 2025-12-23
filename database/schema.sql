-- ═══════════════════════════════════════════════════════════════════════════
-- JURIS_IA_CORE_V1 - SCHEMA COMPLETO DO BANCO DE DADOS
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Sistema de preparação para OAB com IA adaptativa
-- Database: PostgreSQL 14+
-- Encoding: UTF8
-- Author: ARQUITETO DE DADOS E COGNIÇÃO JURÍDICA
-- Date: 2025-12-17
-- Version: 1.0.0
--
-- TABELAS:
--   1. users                    - Usuários do sistema
--   2. perfil_juridico          - Perfil cognitivo jurídico (CORE)
--   3. progresso_disciplina     - Progresso por disciplina
--   4. progresso_topico         - Progresso granular por tópico
--   5. sessao_estudo            - Sessões de estudo
--   6. interacao_questao        - Interações com questões (MAIS IMPORTANTE)
--   7. analise_erro             - Análise de erros cometidos
--   8. pratica_peca             - Prática de peças processuais (2ª fase)
--   9. erro_peca                - Erros em peças
--   10. revisao_agendada        - Revisões espaçadas (spaced repetition)
--   11. snapshot_cognitivo      - Snapshots do estado cognitivo
--   12. metricas_temporais      - Métricas pré-calculadas
--   13. questoes_banco          - Banco de questões OAB
--   14. log_sistema             - Logs de auditoria e segurança
--   15. consentimentos          - Consentimentos LGPD
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ═══════════════════════════════════════════════════════════════════════════
-- ENUMS (Tipos Enumerados)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TYPE user_status AS ENUM (
    'ATIVO',
    'INATIVO',
    'INATIVO_LONGO_PRAZO',
    'EXCLUSAO_SOLICITADA',
    'ANONIMIZADO',
    'APROVADO_OAB'
);

CREATE TYPE nivel_dominio AS ENUM (
    'INICIANTE',
    'BASICO',
    'INTERMEDIARIO',
    'AVANCADO',
    'EXPERT'
);

CREATE TYPE tipo_sessao AS ENUM (
    'drill',
    'simulado',
    'revisao',
    'prova_completa'
);

CREATE TYPE resultado_questao AS ENUM (
    'ACERTO',
    'ERRO',
    'PULOU',
    'TIMEOUT'
);

CREATE TYPE categoria_erro AS ENUM (
    'ERRO_CONCEITUAL',
    'ERRO_INTERPRETACAO',
    'CONFUSAO_INSTITUTOS',
    'ERRO_LEITURA_ATENCAO',
    'FALTA_BASE_JURIDICA',
    'ERRO_ESTRATEGICO_2FASE',
    'ERRO_TRAP'
);

CREATE TYPE tipo_peca AS ENUM (
    'PETICAO_INICIAL_CIVEL',
    'PETICAO_INICIAL_TRABALHISTA',
    'CONTESTACAO',
    'RECURSO_APELACAO',
    'RECURSO_ESPECIAL',
    'RECURSO_EXTRAORDINARIO',
    'HABEAS_CORPUS',
    'MANDADO_SEGURANCA',
    'PARECER_JURIDICO'
);

CREATE TYPE gravidade_erro_peca AS ENUM (
    'FATAL',      -- Zera a peça
    'GRAVE',      -- -20 a -30 pontos
    'MEDIO',      -- -10 a -15 pontos
    'LEVE'        -- -5 pontos
);

CREATE TYPE log_gravidade AS ENUM (
    'DEBUG',
    'INFO',
    'WARNING',
    'ERROR',
    'CRITICAL'
);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 1: users
-- ═══════════════════════════════════════════════════════════════════════════
-- Armazena dados de identificação e autenticação dos usuários

CREATE TABLE users (
    -- Identificação
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Dados pessoais (LGPD Art. 5º, I)
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    telefone VARCHAR(20),
    cpf VARCHAR(14) UNIQUE,

    -- Autenticação
    password_hash VARCHAR(255) NOT NULL,
    email_verificado BOOLEAN DEFAULT FALSE,

    -- Status e controle
    status user_status DEFAULT 'ATIVO',
    ultimo_acesso TIMESTAMPTZ,

    -- LGPD - Controle de privacidade
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,
    motivo_anonimizacao TEXT,
    hash_anonimo VARCHAR(64),  -- SHA256 para rastreamento científico

    data_solicitacao_exclusao TIMESTAMPTZ,
    data_anonimizacao_prevista TIMESTAMPTZ,
    motivo_exclusao TEXT,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE users IS 'Usuários do sistema - dados de identificação e autenticação';
COMMENT ON COLUMN users.hash_anonimo IS 'Hash SHA256 não-reversível para manter dados científicos após anonimização';
COMMENT ON COLUMN users.status IS 'ATIVO: < 180d | INATIVO: 180-365d | INATIVO_LONGO_PRAZO: > 365d | EXCLUSAO_SOLICITADA: aguardando 90d | ANONIMIZADO: dados removidos | APROVADO_OAB: aprovado na prova';

-- Índices
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status) WHERE anonimizado = FALSE;
CREATE INDEX idx_users_ultimo_acesso ON users(ultimo_acesso) WHERE status = 'ATIVO';
CREATE INDEX idx_users_hash_anonimo ON users(hash_anonimo) WHERE hash_anonimo IS NOT NULL;


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 2: perfil_juridico
-- ═══════════════════════════════════════════════════════════════════════════
-- CORE DO SISTEMA - Perfil cognitivo jurídico completo do estudante
-- 8 dimensões: nível geral, pontuação, taxa acerto, estado emocional,
-- maturidade jurídica, padrões aprendizagem, riscos, metas

CREATE TABLE perfil_juridico (
    -- Identificação
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- DIMENSÃO 1: Nível geral de domínio
    nivel_geral nivel_dominio DEFAULT 'INICIANTE',

    -- DIMENSÃO 2: Pontuação global (gamificação)
    pontuacao_global INTEGER DEFAULT 0 CHECK (pontuacao_global >= 0 AND pontuacao_global <= 1000),

    -- DIMENSÃO 3: Taxa de acerto global (ponderada)
    taxa_acerto_global DECIMAL(5,2) DEFAULT 0.0 CHECK (taxa_acerto_global >= 0 AND taxa_acerto_global <= 100),

    -- DIMENSÃO 4: Estado cognitivo-emocional (LGPD Art. 11 - Dado Sensível)
    estado_emocional JSONB DEFAULT '{
        "confianca": 0.50,
        "stress": 0.50,
        "motivacao": 0.70,
        "fadiga": 0.20
    }'::jsonb,

    -- DIMENSÃO 5: Maturidade jurídica (5 sub-dimensões)
    maturidade_juridica JSONB DEFAULT '{
        "pensamento_sistemico": 0.30,
        "capacidade_abstracao": 0.30,
        "dominio_terminologia": 0.30,
        "raciocinio_analogico": 0.30,
        "interpretacao_juridica": 0.30
    }'::jsonb,

    -- DIMENSÃO 6: Padrões de aprendizagem
    padroes_aprendizagem JSONB DEFAULT '{
        "estilo_predominante": "HIBRIDO",
        "velocidade_leitura_wpm": 180,
        "nivel_explicacao_preferido": 2,
        "necessita_analogias": true
    }'::jsonb,

    -- DIMENSÃO 7: Riscos e alertas
    riscos JSONB DEFAULT '{
        "risco_evasao": 0.10,
        "risco_burnout": 0.10,
        "dias_streak_atual": 0
    }'::jsonb,

    -- DIMENSÃO 8: Metas e metacognição
    metas JSONB,
    data_prova_agendada DATE,

    -- Competências específicas 2ª fase
    competencias_2fase JSONB DEFAULT '{
        "formalizacao_tese": 0.0,
        "fundamentacao_juridica": 0.0,
        "tecnica_redacional": 0.0,
        "estruturacao_peca": 0.0,
        "persuasao": 0.0
    }'::jsonb,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    -- Constraint: 1 perfil por usuário
    CONSTRAINT unique_perfil_por_usuario UNIQUE (user_id)
);

COMMENT ON TABLE perfil_juridico IS 'CORE: Perfil cognitivo jurídico completo - 8 dimensões de análise';
COMMENT ON COLUMN perfil_juridico.estado_emocional IS 'LGPD Art. 11: Dado sensível - requer consentimento específico';
COMMENT ON COLUMN perfil_juridico.maturidade_juridica IS '5 dimensões: pensamento sistêmico, abstração, terminologia, raciocínio analógico, interpretação';

-- Índices
CREATE UNIQUE INDEX idx_perfil_user ON perfil_juridico(user_id);
CREATE INDEX idx_perfil_nivel ON perfil_juridico(nivel_geral);
CREATE INDEX idx_perfil_pontuacao ON perfil_juridico(pontuacao_global DESC);

-- Índices GIN para busca em JSONB
CREATE INDEX idx_perfil_estado_emocional_gin ON perfil_juridico USING gin(estado_emocional);
CREATE INDEX idx_perfil_maturidade_gin ON perfil_juridico USING gin(maturidade_juridica);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 3: progresso_disciplina
-- ═══════════════════════════════════════════════════════════════════════════
-- Progresso do estudante por disciplina jurídica

CREATE TABLE progresso_disciplina (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Disciplina
    disciplina VARCHAR(100) NOT NULL,  -- Ex: "Direito Penal", "Direito Civil"

    -- Métricas de desempenho
    questoes_resolvidas INTEGER DEFAULT 0,
    questoes_acertadas INTEGER DEFAULT 0,
    taxa_acerto DECIMAL(5,2) DEFAULT 0.0,

    -- Nível de domínio
    nivel_dominio nivel_dominio DEFAULT 'INICIANTE',

    -- Tempo investido
    tempo_total_minutos INTEGER DEFAULT 0,

    -- Última atividade
    ultima_questao_em TIMESTAMPTZ,
    ultima_revisao_em TIMESTAMPTZ,

    -- Predição
    probabilidade_aprovacao DECIMAL(5,2),  -- 0-100%

    -- Disciplina priorizada?
    prioridade INTEGER DEFAULT 50 CHECK (prioridade >= 0 AND prioridade <= 100),

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    -- Constraint: 1 registro por (user_id, disciplina)
    CONSTRAINT unique_user_disciplina UNIQUE (user_id, disciplina)
);

COMMENT ON TABLE progresso_disciplina IS 'Progresso do estudante por disciplina (Penal, Civil, etc)';

-- Índices
CREATE INDEX idx_prog_disc_user ON progresso_disciplina(user_id);
CREATE INDEX idx_prog_disc_disciplina ON progresso_disciplina(disciplina);
CREATE INDEX idx_prog_disc_taxa ON progresso_disciplina(taxa_acerto DESC);
CREATE INDEX idx_prog_disc_nivel ON progresso_disciplina(nivel_dominio);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 4: progresso_topico
-- ═══════════════════════════════════════════════════════════════════════════
-- Progresso granular por tópico jurídico específico

CREATE TABLE progresso_topico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Hierarquia: Disciplina → Tópico
    disciplina VARCHAR(100) NOT NULL,
    topico VARCHAR(255) NOT NULL,  -- Ex: "Dos Crimes contra o Patrimônio"

    -- Métricas
    questoes_resolvidas INTEGER DEFAULT 0,
    questoes_acertadas INTEGER DEFAULT 0,
    taxa_acerto DECIMAL(5,2) DEFAULT 0.0,

    -- Memória (spaced repetition)
    forca_memoria DECIMAL(3,2) DEFAULT 0.0 CHECK (forca_memoria >= 0 AND forca_memoria <= 1),
    ultima_revisao TIMESTAMPTZ,
    proxima_revisao TIMESTAMPTZ,

    -- Exposição
    primeira_exposicao TIMESTAMPTZ,
    total_exposicoes INTEGER DEFAULT 0,

    -- Conceitos relacionados
    conceitos_chave TEXT[],  -- Array de conceitos importantes
    artigos_lei TEXT[],      -- Array de artigos de lei relacionados

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_user_topico UNIQUE (user_id, disciplina, topico)
);

COMMENT ON TABLE progresso_topico IS 'Progresso granular por tópico específico com memória espaçada';
COMMENT ON COLUMN progresso_topico.forca_memoria IS 'Força da memória 0-1 (spaced repetition)';

-- Índices
CREATE INDEX idx_prog_top_user ON progresso_topico(user_id);
CREATE INDEX idx_prog_top_disciplina ON progresso_topico(disciplina);
CREATE INDEX idx_prog_top_forca_memoria ON progresso_topico(forca_memoria);
CREATE INDEX idx_prog_top_proxima_revisao ON progresso_topico(proxima_revisao) WHERE proxima_revisao IS NOT NULL;


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 5: sessao_estudo
-- ═══════════════════════════════════════════════════════════════════════════
-- Cada sessão de estudo do aluno

CREATE TABLE sessao_estudo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Tipo de sessão
    tipo tipo_sessao NOT NULL,
    disciplina VARCHAR(100),
    topico VARCHAR(255),

    -- Configuração da sessão
    configuracao JSONB,  -- Ex: {"quantidade_questoes": 20, "dificuldade": "media", "tempo_limite": 3600}

    -- Métricas da sessão
    total_questoes INTEGER DEFAULT 0,
    total_acertos INTEGER DEFAULT 0,
    taxa_acerto DECIMAL(5,2),

    -- Tempo
    iniciado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizado_em TIMESTAMPTZ,
    duracao_minutos INTEGER,

    -- Simulado específico
    aprovado BOOLEAN,  -- Para simulados: atingiu nota mínima?
    nota_final DECIMAL(5,2),  -- 0-100

    -- Estado emocional pós-sessão
    estado_emocional_pos JSONB,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE sessao_estudo IS 'Cada sessão de estudo (drill, simulado, revisão)';

-- Índices
CREATE INDEX idx_sessao_user ON sessao_estudo(user_id);
CREATE INDEX idx_sessao_tipo ON sessao_estudo(tipo);
CREATE INDEX idx_sessao_iniciado ON sessao_estudo(iniciado_em DESC);
CREATE INDEX idx_sessao_finalizado ON sessao_estudo(finalizado_em DESC) WHERE finalizado_em IS NOT NULL;
CREATE INDEX idx_sessao_disciplina ON sessao_estudo(disciplina) WHERE disciplina IS NOT NULL;


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 6: interacao_questao
-- ═══════════════════════════════════════════════════════════════════════════
-- MAIS IMPORTANTE: Cada interação do aluno com uma questão
-- Esta é a tabela com maior volume e mais análises

CREATE TABLE interacao_questao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    questao_id UUID NOT NULL,  -- FK para questoes_banco (criada depois)
    sessao_id UUID REFERENCES sessao_estudo(id) ON DELETE SET NULL,

    -- Contexto da questão no momento
    disciplina VARCHAR(100) NOT NULL,
    topico VARCHAR(255),
    dificuldade VARCHAR(20),  -- facil, media, dificil

    -- Resposta do aluno
    alternativa_escolhida VARCHAR(1),  -- A, B, C, D, E
    alternativa_correta VARCHAR(1) NOT NULL,
    resultado resultado_questao NOT NULL,

    -- Tempo
    tempo_resposta_segundos INTEGER,
    respondido_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Perfil cognitivo no momento (snapshot leve)
    nivel_confianca DECIMAL(3,2),  -- Confiança antes de responder
    nivel_fadiga DECIMAL(3,2),     -- Fadiga acumulada na sessão

    -- Explicação fornecida
    nivel_explicacao_fornecido INTEGER,  -- 1=Técnico, 2=Didático, 3=Analogia, 4=Prático
    visualizou_explicacao BOOLEAN DEFAULT FALSE,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE interacao_questao IS 'CORE: Cada resposta de questão - base para toda análise de aprendizagem';
COMMENT ON COLUMN interacao_questao.tempo_resposta_segundos IS 'Tempo em segundos - usado para detectar pressa/dúvida';

-- Índices (CRÍTICOS para performance)
CREATE INDEX idx_interacao_user ON interacao_questao(user_id);
CREATE INDEX idx_interacao_questao ON interacao_questao(questao_id);
CREATE INDEX idx_interacao_sessao ON interacao_questao(sessao_id);
CREATE INDEX idx_interacao_resultado ON interacao_questao(resultado);
CREATE INDEX idx_interacao_respondido ON interacao_questao(respondido_em DESC);
CREATE INDEX idx_interacao_disciplina ON interacao_questao(disciplina);
CREATE INDEX idx_interacao_user_disciplina ON interacao_questao(user_id, disciplina);
CREATE INDEX idx_interacao_user_resultado ON interacao_questao(user_id, resultado);

-- Índice parcial: só erros (para análise de erro)
CREATE INDEX idx_interacao_erros ON interacao_questao(user_id, questao_id, respondido_em)
    WHERE resultado = 'ERRO';

-- ⚠️  PARTICIONAMENTO RECOMENDADO (para grande volume)
-- Descomentar quando atingir ~1 milhão de registros:
-- ALTER TABLE interacao_questao PARTITION BY RANGE (respondido_em);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 7: analise_erro
-- ═══════════════════════════════════════════════════════════════════════════
-- Análise profunda de cada erro cometido

CREATE TABLE analise_erro (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    interacao_id UUID NOT NULL REFERENCES interacao_questao(id) ON DELETE CASCADE,

    -- Classificação do erro
    categoria_erro categoria_erro NOT NULL,
    tipo_erro_especifico VARCHAR(100) NOT NULL,  -- Ex: "CONCEITO_NAO_COMPREENDIDO"

    -- Contexto
    disciplina VARCHAR(100) NOT NULL,
    topico VARCHAR(255),
    conceitos_deficientes TEXT[],  -- Array de conceitos que o aluno não domina

    -- Gravidade (impacto no aprendizado)
    gravidade VARCHAR(20),  -- BAIXA, MEDIA, ALTA

    -- Ação pedagógica recomendada
    intervencao_recomendada TEXT,
    intervencao_aplicada BOOLEAN DEFAULT FALSE,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    analisado_em TIMESTAMPTZ DEFAULT NOW(),
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE analise_erro IS 'Análise profunda de erros - classificação em 28 tipos específicos';

-- Índices
CREATE INDEX idx_analise_user ON analise_erro(user_id);
CREATE INDEX idx_analise_interacao ON analise_erro(interacao_id);
CREATE INDEX idx_analise_categoria ON analise_erro(categoria_erro);
CREATE INDEX idx_analise_tipo ON analise_erro(tipo_erro_especifico);
CREATE INDEX idx_analise_disciplina ON analise_erro(disciplina);
CREATE INDEX idx_analise_analisado ON analise_erro(analisado_em DESC);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 8: pratica_peca
-- ═══════════════════════════════════════════════════════════════════════════
-- Prática de peças processuais (2ª fase OAB)

CREATE TABLE pratica_peca (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Tipo e contexto
    tipo_peca tipo_peca NOT NULL,
    enunciado TEXT NOT NULL,

    -- Conteúdo da peça escrita pelo aluno
    conteudo_peca TEXT,  -- Será removido se anonimizado (pode conter dados pessoais fictícios)

    -- Avaliação
    nota_final DECIMAL(5,2),  -- 0-10
    aprovado BOOLEAN,  -- >= 6.0

    -- Detalhamento da nota
    nota_formalizacao_tese DECIMAL(5,2),
    nota_fundamentacao DECIMAL(5,2),
    nota_tecnica_redacional DECIMAL(5,2),
    nota_estrutura DECIMAL(5,2),

    -- Erros encontrados
    total_erros_fatais INTEGER DEFAULT 0,
    total_erros_graves INTEGER DEFAULT 0,
    total_erros_medios INTEGER DEFAULT 0,
    total_erros_leves INTEGER DEFAULT 0,

    -- Tempo
    iniciado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finalizado_em TIMESTAMPTZ,
    tempo_minutos INTEGER,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE pratica_peca IS 'Prática de peças processuais (2ª fase OAB)';
COMMENT ON COLUMN pratica_peca.conteudo_peca IS 'Removido na anonimização (pode conter dados pessoais fictícios)';

-- Índices
CREATE INDEX idx_peca_user ON pratica_peca(user_id);
CREATE INDEX idx_peca_tipo ON pratica_peca(tipo_peca);
CREATE INDEX idx_peca_nota ON pratica_peca(nota_final DESC);
CREATE INDEX idx_peca_iniciado ON pratica_peca(iniciado_em DESC);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 9: erro_peca
-- ═══════════════════════════════════════════════════════════════════════════
-- Erros específicos identificados em peças

CREATE TABLE erro_peca (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pratica_id UUID NOT NULL REFERENCES pratica_peca(id) ON DELETE CASCADE,

    -- Tipo de erro
    tipo_erro VARCHAR(100) NOT NULL,
    descricao TEXT NOT NULL,
    gravidade gravidade_erro_peca NOT NULL,

    -- Localização do erro na peça
    secao VARCHAR(100),  -- Ex: "PEDIDOS", "FUNDAMENTAÇÃO"

    -- Impacto na nota
    pontos_perdidos DECIMAL(4,2),

    -- Explicação e correção
    explicacao TEXT,
    exemplo_correcao TEXT,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE erro_peca IS 'Erros específicos identificados em peças processuais';

-- Índices
CREATE INDEX idx_erro_peca_pratica ON erro_peca(pratica_id);
CREATE INDEX idx_erro_peca_gravidade ON erro_peca(gravidade);
CREATE INDEX idx_erro_peca_tipo ON erro_peca(tipo_erro);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 10: revisao_agendada
-- ═══════════════════════════════════════════════════════════════════════════
-- Sistema de revisão espaçada (spaced repetition: 1-24-7-30)

CREATE TABLE revisao_agendada (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Item a revisar
    topico VARCHAR(255) NOT NULL,
    disciplina VARCHAR(100) NOT NULL,
    conceitos TEXT[],
    artigos_lei TEXT[],

    -- Ciclo de revisão
    ciclo INTEGER NOT NULL CHECK (ciclo >= 1 AND ciclo <= 4),  -- 1=1h, 2=24h, 3=7d, 4=30d
    data_revisao DATE NOT NULL,

    -- Status
    revisado BOOLEAN DEFAULT FALSE,
    revisado_em TIMESTAMPTZ,
    resultado_revisao resultado_questao,  -- ACERTO, ERRO

    -- Força da memória ajustada
    forca_memoria_antes DECIMAL(3,2),
    forca_memoria_depois DECIMAL(3,2),

    -- Próxima revisão
    proxima_revisao_id UUID,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE revisao_agendada IS 'Sistema de revisão espaçada (1h-24h-7d-30d)';
COMMENT ON COLUMN revisao_agendada.ciclo IS '1=1h, 2=24h, 3=7d, 4=30d após aprendizado inicial';

-- Índices
CREATE INDEX idx_revisao_user ON revisao_agendada(user_id);
CREATE INDEX idx_revisao_data ON revisao_agendada(data_revisao);
CREATE INDEX idx_revisao_pendente ON revisao_agendada(user_id, data_revisao)
    WHERE revisado = FALSE;
CREATE INDEX idx_revisao_disciplina ON revisao_agendada(disciplina);
CREATE INDEX idx_revisao_topico ON revisao_agendada(topico);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 11: snapshot_cognitivo
-- ═══════════════════════════════════════════════════════════════════════════
-- Snapshots do estado cognitivo completo em momentos-chave

CREATE TABLE snapshot_cognitivo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Temporalidade
    momento TIMESTAMPTZ NOT NULL,
    tipo_trigger VARCHAR(50) NOT NULL,  -- Ex: "pos_sessao", "semanal", "pre_prova"
    contexto_trigger JSONB,

    -- Metadados
    versao_snapshot VARCHAR(10) DEFAULT '1.0',

    -- BLOCO 1: Perfil cognitivo completo (cópia do perfil_juridico)
    perfil_completo JSONB NOT NULL,

    -- BLOCO 2: Desempenho consolidado
    desempenho JSONB NOT NULL,

    -- BLOCO 3: Padrões de erro
    padroes_erro JSONB NOT NULL,

    -- BLOCO 4: Memória e retenção
    estado_memoria JSONB NOT NULL,

    -- BLOCO 5: Predição e prognóstico
    predicao JSONB NOT NULL,

    -- BLOCO 6: Contexto do momento
    contexto_momento JSONB NOT NULL,

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE snapshot_cognitivo IS 'Snapshots IMUTÁVEIS do estado cognitivo em momentos-chave';
COMMENT ON COLUMN snapshot_cognitivo.tipo_trigger IS 'pos_sessao | semanal | pre_prova | pos_prova_real | mudanca_nivel | milestone_volume | regressao | breakthrough';

-- Índices
CREATE INDEX idx_snapshot_user_momento ON snapshot_cognitivo(user_id, momento DESC);
CREATE INDEX idx_snapshot_tipo ON snapshot_cognitivo(tipo_trigger);
CREATE INDEX idx_snapshot_momento ON snapshot_cognitivo(momento DESC);

-- Índices GIN para busca em JSONB
CREATE INDEX idx_snapshot_perfil_gin ON snapshot_cognitivo USING gin(perfil_completo);
CREATE INDEX idx_snapshot_desempenho_gin ON snapshot_cognitivo USING gin(desempenho);
CREATE INDEX idx_snapshot_predicao_gin ON snapshot_cognitivo USING gin(predicao);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 12: metricas_temporais
-- ═══════════════════════════════════════════════════════════════════════════
-- Métricas pré-calculadas por período (dia, semana, mês)

CREATE TABLE metricas_temporais (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Período
    tipo_periodo VARCHAR(20) NOT NULL,  -- dia, semana, mes
    periodo DATE NOT NULL,  -- Data de início do período

    -- Métricas de atividade
    questoes_resolvidas INTEGER DEFAULT 0,
    questoes_acertadas INTEGER DEFAULT 0,
    taxa_acerto DECIMAL(5,2),

    tempo_estudo_minutos INTEGER DEFAULT 0,
    sessoes_realizadas INTEGER DEFAULT 0,

    -- Disciplinas estudadas
    disciplinas_estudadas TEXT[],
    disciplina_mais_praticada VARCHAR(100),

    -- Evolução
    evolucao_taxa_acerto DECIMAL(5,2),  -- Comparado com período anterior

    -- Badges e conquistas
    badges_conquistados TEXT[],

    -- LGPD
    anonimizado BOOLEAN DEFAULT FALSE,
    anonimizado_em TIMESTAMPTZ,

    -- Metadados
    calculado_em TIMESTAMPTZ DEFAULT NOW(),
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT unique_user_periodo UNIQUE (user_id, tipo_periodo, periodo)
);

COMMENT ON TABLE metricas_temporais IS 'Métricas pré-calculadas por dia/semana/mês para dashboards';

-- Índices
CREATE INDEX idx_metricas_user ON metricas_temporais(user_id);
CREATE INDEX idx_metricas_periodo ON metricas_temporais(periodo DESC);
CREATE INDEX idx_metricas_tipo ON metricas_temporais(tipo_periodo);
CREATE INDEX idx_metricas_user_periodo ON metricas_temporais(user_id, tipo_periodo, periodo DESC);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 13: questoes_banco
-- ═══════════════════════════════════════════════════════════════════════════
-- Banco de questões OAB com metadados completos

CREATE TABLE questoes_banco (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificação
    codigo_externo VARCHAR(50) UNIQUE,  -- Ex: "OAB-XXXIII-2021-Q15"

    -- Classificação
    disciplina VARCHAR(100) NOT NULL,
    topico VARCHAR(255) NOT NULL,
    subtopico VARCHAR(255),

    -- Dificuldade (calculada por taxa de acerto)
    dificuldade VARCHAR(20) DEFAULT 'media',  -- facil, media, dificil
    taxa_acerto_geral DECIMAL(5,2),  -- Taxa global de acerto

    -- Conteúdo
    enunciado TEXT NOT NULL,
    alternativa_a TEXT NOT NULL,
    alternativa_b TEXT NOT NULL,
    alternativa_c TEXT NOT NULL,
    alternativa_d TEXT NOT NULL,
    alternativa_e TEXT,  -- Opcional (algumas questões têm só 4)
    alternativa_correta VARCHAR(1) NOT NULL CHECK (alternativa_correta IN ('A', 'B', 'C', 'D', 'E')),

    -- Explicações (4 níveis)
    explicacao_nivel1_tecnico TEXT,
    explicacao_nivel2_didatico TEXT,
    explicacao_nivel3_analogia TEXT,
    explicacao_nivel4_pratico TEXT,

    -- Explicação de alternativas erradas
    explicacao_alternativas JSONB,  -- {A: "Errada porque...", B: "Errada porque..."}

    -- Metadados jurídicos
    artigos_lei TEXT[],
    jurisprudencia TEXT[],
    doutrina TEXT[],
    conceitos_chave TEXT[],

    -- Tags e características
    tags TEXT[],
    eh_trap BOOLEAN DEFAULT FALSE,  -- É pegadinha?
    exige_calculo BOOLEAN DEFAULT FALSE,
    exige_jurisprudencia BOOLEAN DEFAULT FALSE,

    -- Origem
    exame VARCHAR(50),  -- Ex: "XXXIII Exame"
    ano INTEGER,
    numero_questao INTEGER,

    -- Estatísticas de uso
    total_resolucoes INTEGER DEFAULT 0,
    total_acertos INTEGER DEFAULT 0,

    -- Ativa?
    ativa BOOLEAN DEFAULT TRUE,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE questoes_banco IS 'Banco de questões OAB com 4 níveis de explicação';
COMMENT ON COLUMN questoes_banco.eh_trap IS 'Questão é pegadinha/trap (texto similar inverso, exceção, etc)';

-- Índices
CREATE INDEX idx_questao_disciplina ON questoes_banco(disciplina);
CREATE INDEX idx_questao_topico ON questoes_banco(topico);
CREATE INDEX idx_questao_dificuldade ON questoes_banco(dificuldade);
CREATE INDEX idx_questao_exame ON questoes_banco(exame, ano);
CREATE INDEX idx_questao_ativa ON questoes_banco(ativa) WHERE ativa = TRUE;

-- Índice GIN para busca por tags
CREATE INDEX idx_questao_tags_gin ON questoes_banco USING gin(tags);

-- FK atrasada (agora que questoes_banco existe)
ALTER TABLE interacao_questao
    ADD CONSTRAINT fk_interacao_questao
    FOREIGN KEY (questao_id) REFERENCES questoes_banco(id);


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 14: log_sistema
-- ═══════════════════════════════════════════════════════════════════════════
-- Logs de auditoria, segurança e compliance

CREATE TABLE log_sistema (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Tipo de log
    tipo VARCHAR(50) NOT NULL,  -- ACESSO_DADOS_PESSOAIS, ANONIMIZACAO_DADOS, etc
    gravidade log_gravidade DEFAULT 'INFO',

    -- Conteúdo
    descricao TEXT NOT NULL,
    metadata JSONB,  -- Dados adicionais em JSON

    -- Contexto
    user_id UUID,  -- Usuário que causou o log (pode ser NULL para logs de sistema)
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE log_sistema IS 'Logs de auditoria, segurança e compliance LGPD';
COMMENT ON COLUMN log_sistema.tipo IS 'ACESSO_DADOS_PESSOAIS | ANONIMIZACAO_DADOS | EXPORTACAO_DADOS | INCIDENTE_SEGURANCA | etc';

-- Índices
CREATE INDEX idx_log_tipo ON log_sistema(tipo);
CREATE INDEX idx_log_gravidade ON log_sistema(gravidade);
CREATE INDEX idx_log_criado ON log_sistema(criado_em DESC);
CREATE INDEX idx_log_user ON log_sistema(user_id) WHERE user_id IS NOT NULL;

-- Índice GIN para busca em metadata
CREATE INDEX idx_log_metadata_gin ON log_sistema USING gin(metadata);

-- Índice parcial: só logs críticos
CREATE INDEX idx_log_criticos ON log_sistema(criado_em DESC)
    WHERE gravidade IN ('ERROR', 'CRITICAL');


-- ═══════════════════════════════════════════════════════════════════════════
-- TABELA 15: consentimentos
-- ═══════════════════════════════════════════════════════════════════════════
-- Registro de consentimentos LGPD

CREATE TABLE consentimentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Tipos de consentimento
    servico_basico BOOLEAN DEFAULT TRUE,  -- Execução do serviço (sempre true)
    personalizacao BOOLEAN DEFAULT FALSE,  -- Usar dados para personalizar
    dados_emocionais BOOLEAN DEFAULT FALSE,  -- LGPD Art. 11 - Dado sensível
    pesquisa_anonimizada BOOLEAN DEFAULT FALSE,  -- Usar dados anonimizados em pesquisa
    comunicacao_marketing BOOLEAN DEFAULT FALSE,  -- Receber emails promocionais

    -- Metadados do consentimento
    versao_politica VARCHAR(20) NOT NULL,  -- Ex: "1.2.0"
    data_consentimento TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ip_address INET,

    -- Consentimento ativo?
    ativo BOOLEAN DEFAULT TRUE,
    revogado_em TIMESTAMPTZ,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE consentimentos IS 'Registro de consentimentos LGPD (granular por finalidade)';
COMMENT ON COLUMN consentimentos.dados_emocionais IS 'LGPD Art. 11: Consentimento específico para dados sensíveis (estado emocional)';

-- Índices
CREATE INDEX idx_consent_user ON consentimentos(user_id);
CREATE INDEX idx_consent_ativo ON consentimentos(ativo) WHERE ativo = TRUE;
CREATE INDEX idx_consent_data ON consentimentos(data_consentimento DESC);


-- ═══════════════════════════════════════════════════════════════════════════
-- TRIGGERS AUTOMÁTICOS
-- ═══════════════════════════════════════════════════════════════════════════

-- Função genérica para atualizar updated_at
CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger em todas as tabelas com updated_at
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_perfil_updated_at
    BEFORE UPDATE ON perfil_juridico
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_prog_disc_updated_at
    BEFORE UPDATE ON progresso_disciplina
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_prog_top_updated_at
    BEFORE UPDATE ON progresso_topico
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_sessao_updated_at
    BEFORE UPDATE ON sessao_estudo
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_peca_updated_at
    BEFORE UPDATE ON pratica_peca
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_revisao_updated_at
    BEFORE UPDATE ON revisao_agendada
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_metricas_updated_at
    BEFORE UPDATE ON metricas_temporais
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_questoes_updated_at
    BEFORE UPDATE ON questoes_banco
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();

CREATE TRIGGER trigger_consent_updated_at
    BEFORE UPDATE ON consentimentos
    FOR EACH ROW
    EXECUTE FUNCTION atualizar_updated_at();


-- ═══════════════════════════════════════════════════════════════════════════
-- VIEWS ÚTEIS
-- ═══════════════════════════════════════════════════════════════════════════

-- VIEW: Dashboard do Estudante (dados em tempo real)
CREATE OR REPLACE VIEW dashboard_estudante AS
SELECT
    u.id as user_id,
    u.nome,
    u.email,
    u.status,
    u.ultimo_acesso,

    -- Perfil cognitivo
    p.nivel_geral,
    p.pontuacao_global,
    p.taxa_acerto_global,
    p.estado_emocional,
    p.maturidade_juridica,
    p.riscos,

    -- Estatísticas gerais
    (SELECT COUNT(*) FROM interacao_questao iq WHERE iq.user_id = u.id) as total_questoes,
    (SELECT COUNT(*) FROM interacao_questao iq WHERE iq.user_id = u.id AND iq.resultado = 'ACERTO') as total_acertos,

    -- Sessões
    (SELECT COUNT(*) FROM sessao_estudo se WHERE se.user_id = u.id) as total_sessoes,
    (SELECT MAX(iniciado_em) FROM sessao_estudo se WHERE se.user_id = u.id) as ultima_sessao,

    -- Revisões pendentes
    (SELECT COUNT(*) FROM revisao_agendada ra
     WHERE ra.user_id = u.id
       AND ra.revisado = FALSE
       AND ra.data_revisao <= CURRENT_DATE) as revisoes_pendentes,

    -- Último snapshot
    (SELECT momento FROM snapshot_cognitivo sc
     WHERE sc.user_id = u.id
     ORDER BY momento DESC LIMIT 1) as ultimo_snapshot

FROM users u
LEFT JOIN perfil_juridico p ON p.user_id = u.id
WHERE u.anonimizado = FALSE;

COMMENT ON VIEW dashboard_estudante IS 'Dashboard em tempo real do estudante';


-- VIEW: Dashboard de Governança (compliance LGPD)
CREATE OR REPLACE VIEW dashboard_governanca AS
WITH stats AS (
    SELECT
        COUNT(*) FILTER (WHERE status = 'ATIVO') as usuarios_ativos,
        COUNT(*) FILTER (WHERE status = 'EXCLUSAO_SOLICITADA') as exclusoes_pendentes,
        COUNT(*) FILTER (WHERE anonimizado = TRUE) as usuarios_anonimizados,
        COUNT(*) FILTER (
            WHERE status = 'EXCLUSAO_SOLICITADA'
              AND data_anonimizacao_prevista < NOW() + INTERVAL '7 days'
        ) as exclusoes_proxima_semana
    FROM users
)
SELECT
    NOW() as gerado_em,
    s.usuarios_ativos,
    s.exclusoes_pendentes,
    s.usuarios_anonimizados,
    s.exclusoes_proxima_semana,

    -- Incidentes recentes
    (SELECT COUNT(*) FROM log_sistema
     WHERE tipo = 'INCIDENTE_SEGURANCA'
       AND criado_em >= NOW() - INTERVAL '30 days') as incidentes_30d,

    -- Status compliance
    CASE
        WHEN s.exclusoes_proxima_semana > 0 THEN 'ATENÇÃO: Exclusões pendentes'
        ELSE 'OK'
    END as status_compliance
FROM stats s;

COMMENT ON VIEW dashboard_governanca IS 'Dashboard de compliance e governança LGPD';


-- ═══════════════════════════════════════════════════════════════════════════
-- GRANTS E PERMISSÕES
-- ═══════════════════════════════════════════════════════════════════════════

-- Role para aplicação (read/write normal)
-- CREATE ROLE juris_ia_app WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO juris_ia_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO juris_ia_app;

-- Role para analytics (somente leitura)
-- CREATE ROLE juris_ia_analytics WITH LOGIN PASSWORD 'CHANGE_ME_IN_PRODUCTION';
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO juris_ia_analytics;

-- Revogar DELETE de dados pessoais (usar anonimização, não deleção)
-- REVOKE DELETE ON users, perfil_juridico FROM juris_ia_app;


-- ═══════════════════════════════════════════════════════════════════════════
-- SEED DATA (OPCIONAL - Dados iniciais para testes)
-- ═══════════════════════════════════════════════════════════════════════════

-- Exemplo de usuário de teste (descomentar para usar)
/*
INSERT INTO users (nome, email, password_hash, email_verificado)
VALUES (
    'Estudante Teste',
    'teste@juris-ia.local',
    crypt('senha123', gen_salt('bf')),  -- Bcrypt hash
    TRUE
);

-- Criar perfil para o usuário de teste
INSERT INTO perfil_juridico (user_id, nivel_geral, pontuacao_global)
SELECT id, 'INTERMEDIARIO', 350
FROM users WHERE email = 'teste@juris-ia.local';
*/


-- ═══════════════════════════════════════════════════════════════════════════
-- FIM DO SCHEMA
-- ═══════════════════════════════════════════════════════════════════════════

-- Estatísticas finais
DO $$
DECLARE
    total_tabelas INTEGER;
    total_indices INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_tabelas
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

    SELECT COUNT(*) INTO total_indices
    FROM pg_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE '═══════════════════════════════════════════════════════════';
    RAISE NOTICE 'JURIS_IA_CORE_V1 - SCHEMA CRIADO COM SUCESSO';
    RAISE NOTICE '═══════════════════════════════════════════════════════════';
    RAISE NOTICE 'Tabelas criadas: %', total_tabelas;
    RAISE NOTICE 'Índices criados: %', total_indices;
    RAISE NOTICE 'Views criadas: 2 (dashboard_estudante, dashboard_governanca)';
    RAISE NOTICE 'Triggers criados: 10 (updated_at)';
    RAISE NOTICE '═══════════════════════════════════════════════════════════';
    RAISE NOTICE 'Próximo passo: Executar migrations e seed data';
    RAISE NOTICE '═══════════════════════════════════════════════════════════';
END $$;
