-- Seed database com usuários e progresso de exemplo
-- Para popular banco de dados rapidamente

-- Limpar dados antigos de teste (opcional)
-- DELETE FROM users WHERE email LIKE '%@exemplo.com';

-- Inserir usuários fake
INSERT INTO users (id, nome, email, password_hash, plano, criado_em, ativo) VALUES
('11111111-1111-1111-1111-111111111111', 'Maria Silva', 'maria.silva@exemplo.com', '$2b$12$dummy_hash', 'GRATUITO', NOW() - INTERVAL '60 days', true),
('22222222-2222-2222-2222-222222222222', 'João Santos', 'joao.santos@exemplo.com', '$2b$12$dummy_hash', 'GRATUITO', NOW() - INTERVAL '45 days', true),
('33333333-3333-3333-3333-333333333333', 'Ana Costa', 'ana.costa@exemplo.com', '$2b$12$dummy_hash', 'PREMIUM', NOW() - INTERVAL '80 days', true),
('44444444-4444-4444-4444-444444444444', 'Pedro Oliveira', 'pedro.oliveira@exemplo.com', '$2b$12$dummy_hash', 'GRATUITO', NOW() - INTERVAL '30 days', true),
('55555555-5555-5555-5555-555555555555', 'Juliana Souza', 'juliana.souza@exemplo.com', '$2b$12$dummy_hash', 'PREMIUM', NOW() - INTERVAL '90 days', true)
ON CONFLICT (email) DO NOTHING;

-- Inserir perfis jurídicos
INSERT INTO perfil_juridico (id, user_id, nivel_geral, total_questoes_respondidas, taxa_acerto_geral, tempo_total_estudo_minutos, streak_atual, streak_maximo, xp_total, nivel_xp) VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'INTERMEDIARIO', 250, 68.5, 1200, 5, 15, 2500, 5),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'INICIANTE', 80, 52.3, 400, 2, 8, 800, 2),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'AVANCADO', 450, 82.1, 2800, 12, 25, 4500, 9),
(gen_random_uuid(), '44444444-4444-4444-4444-444444444444', 'INTERMEDIARIO', 150, 64.8, 750, 0, 10, 1500, 4),
(gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 'AVANCADO', 380, 78.9, 2200, 18, 22, 3800, 8)
ON CONFLICT DO NOTHING;

-- Inserir progresso em disciplinas (Direito Civil)
INSERT INTO progresso_disciplina (id, user_id, disciplina, nivel_dominio, taxa_acerto, total_questoes, questoes_corretas, tempo_total_minutos, peso_prova_oab, prioridade_estudo, distribuicao_dificuldade, ultima_questao_em) VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'Direito Civil', 'INTERMEDIARIO', 70.5, 50, 35, 180, 1.0, 5, '{"FACIL": {"total": 15, "acertos": 14}, "MEDIO": {"total": 25, "acertos": 16}, "DIFICIL": {"total": 10, "acertos": 5}}'::jsonb, NOW() - INTERVAL '2 days'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'Direito Civil', 'INICIANTE', 48.2, 30, 14, 120, 1.0, 8, '{"FACIL": {"total": 10, "acertos": 8}, "MEDIO": {"total": 15, "acertos": 5}, "DIFICIL": {"total": 5, "acertos": 1}}'::jsonb, NOW() - INTERVAL '1 day'),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'Direito Civil', 'AVANCADO', 85.0, 80, 68, 300, 1.0, 3, '{"FACIL": {"total": 20, "acertos": 19}, "MEDIO": {"total": 40, "acertos": 35}, "DIFICIL": {"total": 20, "acertos": 14}}'::jsonb, NOW()),
(gen_random_uuid(), '44444444-4444-4444-4444-444444444444', 'Direito Civil', 'INTERMEDIARIO', 62.0, 40, 25, 150, 1.0, 6, '{"FACIL": {"total": 12, "acertos": 11}, "MEDIO": {"total": 20, "acertos": 11}, "DIFICIL": {"total": 8, "acertos": 3}}'::jsonb, NOW() - INTERVAL '3 days'),
(gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 'Direito Civil', 'AVANCADO', 80.0, 70, 56, 260, 1.0, 2, '{"FACIL": {"total": 18, "acertos": 17}, "MEDIO": {"total": 35, "acertos": 29}, "DIFICIL": {"total": 17, "acertos": 10}}'::jsonb, NOW() - INTERVAL '1 day')
ON CONFLICT DO NOTHING;

-- Direito Penal
INSERT INTO progresso_disciplina (id, user_id, disciplina, nivel_dominio, taxa_acerto, total_questoes, questoes_corretas, tempo_total_minutos, peso_prova_oab, prioridade_estudo, distribuicao_dificuldade, ultima_questao_em) VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'Direito Penal', 'INTERMEDIARIO', 65.0, 40, 26, 140, 1.0, 6, '{"FACIL": {"total": 12, "acertos": 11}, "MEDIO": {"total": 20, "acertos": 12}, "DIFICIL": {"total": 8, "acertos": 3}}'::jsonb, NOW() - INTERVAL '1 day'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'Direito Penal', 'INICIANTE', 45.0, 20, 9, 80, 1.0, 9, '{"FACIL": {"total": 8, "acertos": 6}, "MEDIO": {"total": 10, "acertos": 3}, "DIFICIL": {"total": 2, "acertos": 0}}'::jsonb, NOW() - INTERVAL '2 days'),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'Direito Penal', 'AVANCADO', 82.5, 60, 49, 220, 1.0, 4, '{"FACIL": {"total": 15, "acertos": 14}, "MEDIO": {"total": 30, "acertos": 26}, "DIFICIL": {"total": 15, "acertos": 9}}'::jsonb, NOW()),
(gen_random_uuid(), '44444444-4444-4444-4444-444444444444', 'Direito Penal', 'INTERMEDIARIO', 58.0, 35, 20, 130, 1.0, 7, '{"FACIL": {"total": 10, "acertos": 9}, "MEDIO": {"total": 18, "acertos": 9}, "DIFICIL": {"total": 7, "acertos": 2}}'::jsonb, NOW() - INTERVAL '4 days'),
(gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 'Direito Penal', 'AVANCADO', 77.0, 55, 42, 200, 1.0, 3, '{"FACIL": {"total": 14, "acertos": 13}, "MEDIO": {"total": 28, "acertos": 22}, "DIFICIL": {"total": 13, "acertos": 7}}'::jsonb, NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;

-- Direito Constitucional
INSERT INTO progresso_disciplina (id, user_id, disciplina, nivel_dominio, taxa_acerto, total_questoes, questoes_corretas, tempo_total_minutos, peso_prova_oab, prioridade_estudo, distribuicao_dificuldade, ultima_questao_em) VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'Direito Constitucional', 'AVANCADO', 75.0, 60, 45, 220, 1.0, 4, '{"FACIL": {"total": 18, "acertos": 17}, "MEDIO": {"total": 30, "acertos": 22}, "DIFICIL": {"total": 12, "acertos": 6}}'::jsonb, NOW() - INTERVAL '1 day'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'Direito Constitucional', 'INICIANTE', 50.0, 30, 15, 110, 1.0, 7, '{"FACIL": {"total": 10, "acertos": 8}, "MEDIO": {"total": 15, "acertos": 6}, "DIFICIL": {"total": 5, "acertos": 1}}'::jsonb, NOW() - INTERVAL '3 days'),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'Direito Constitucional', 'AVANCADO', 88.0, 75, 66, 280, 1.0, 2, '{"FACIL": {"total": 20, "acertos": 19}, "MEDIO": {"total": 38, "acertos": 35}, "DIFICIL": {"total": 17, "acertos": 12}}'::jsonb, NOW()),
(gen_random_uuid(), '44444444-4444-4444-4444-444444444444', 'Direito Constitucional', 'INTERMEDIARIO', 68.0, 45, 31, 170, 1.0, 5, '{"FACIL": {"total": 13, "acertos": 12}, "MEDIO": {"total": 22, "acertos": 15}, "DIFICIL": {"total": 10, "acertos": 4}}'::jsonb, NOW() - INTERVAL '2 days'),
(gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 'Direito Constitucional', 'AVANCADO', 81.0, 65, 53, 240, 1.0, 3, '{"FACIL": {"total": 17, "acertos": 16}, "MEDIO": {"total": 32, "acertos": 28}, "DIFICIL": {"total": 16, "acertos": 9}}'::jsonb, NOW() - INTERVAL '1 day')
ON CONFLICT DO NOTHING;

-- Ética Profissional
INSERT INTO progresso_disciplina (id, user_id, disciplina, nivel_dominio, taxa_acerto, total_questoes, questoes_corretas, tempo_total_minutos, peso_prova_oab, prioridade_estudo, distribuicao_dificuldade, ultima_questao_em) VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'Ética Profissional', 'INTERMEDIARIO', 72.0, 45, 32, 160, 1.0, 5, '{"FACIL": {"total": 15, "acertos": 14}, "MEDIO": {"total": 22, "acertos": 15}, "DIFICIL": {"total": 8, "acertos": 3}}'::jsonb, NOW() - INTERVAL '2 days'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'Ética Profissional', 'INICIANTE', 55.0, 25, 14, 90, 1.0, 6, '{"FACIL": {"total": 10, "acertos": 9}, "MEDIO": {"total": 12, "acertos": 5}, "DIFICIL": {"total": 3, "acertos": 0}}'::jsonb, NOW() - INTERVAL '4 days'),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'Ética Profissional', 'AVANCADO', 86.0, 55, 47, 200, 1.0, 3, '{"FACIL": {"total": 16, "acertos": 15}, "MEDIO": {"total": 28, "acertos": 25}, "DIFICIL": {"total": 11, "acertos": 7}}'::jsonb, NOW()),
(gen_random_uuid(), '44444444-4444-4444-4444-444444444444', 'Ética Profissional', 'INTERMEDIARIO', 70.0, 38, 27, 140, 1.0, 5, '{"FACIL": {"total": 12, "acertos": 11}, "MEDIO": {"total": 19, "acertos": 13}, "DIFICIL": {"total": 7, "acertos": 3}}'::jsonb, NOW() - INTERVAL '1 day'),
(gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 'Ética Profissional', 'AVANCADO', 79.0, 50, 40, 180, 1.0, 4, '{"FACIL": {"total": 14, "acertos": 13}, "MEDIO": {"total": 25, "acertos": 21}, "DIFICIL": {"total": 11, "acertos": 6}}'::jsonb, NOW() - INTERVAL '2 days')
ON CONFLICT DO NOTHING;

-- Sessões de estudo
INSERT INTO sessao_estudo (id, user_id, tipo_sessao, disciplina_foco, quantidade_questoes, iniciada_em, finalizada_em, concluida) VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'drill', 'Direito Civil', 20, NOW() - INTERVAL '5 days', NOW() - INTERVAL '5 days' + INTERVAL '1 hour', true),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'drill', 'Direito Penal', 15, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '45 minutes', true),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'drill', 'Direito Civil', 10, NOW() - INTERVAL '7 days', NOW() - INTERVAL '7 days' + INTERVAL '30 minutes', true),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'simulado', NULL, 80, NOW() - INTERVAL '10 days', NOW() - INTERVAL '10 days' + INTERVAL '3 hours', true),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'drill', 'Direito Constitucional', 25, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days' + INTERVAL '1 hour 15 minutes', true),
(gen_random_uuid(), '55555555-5555-5555-5555-555555555555', 'simulado', NULL, 40, NOW() - INTERVAL '15 days', NOW() - INTERVAL '15 days' + INTERVAL '2 hours', true)
ON CONFLICT DO NOTHING;

SELECT 'Seed database concluído com sucesso!' as resultado;
SELECT COUNT(*) as total_usuarios FROM users WHERE email LIKE '%@exemplo.com';
SELECT COUNT(*) as total_perfis FROM perfil_juridico;
SELECT COUNT(*) as total_progresso FROM progresso_disciplina;
SELECT COUNT(*) as total_sessoes FROM sessao_estudo;
