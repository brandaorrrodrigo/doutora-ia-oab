# ETAPA 19.3 — ROTINA DIÁRIA DE MONITORAMENTO

**Data**: 2025-12-19
**Responsável**: Gerente de Operação de Alpha Testing
**Status**: 📋 CONFIGURADO
**Duração**: 7 dias (19/12/2025 - 26/12/2025)

---

## 🎯 OBJETIVO

Estabelecer procedimentos sistemáticos para monitoramento diário durante o Alpha Testing, garantindo:
- Detecção precoce de problemas
- Coleta consistente de métricas
- Registro estruturado de eventos
- Decisões baseadas em dados

---

## 📋 CHECKLIST DIÁRIO (09:00 AM)

### ✅ Fase 1: Coleta de Métricas (15 min)

```sql
-- 1. Sessões por usuário (últimas 24h)
SELECT
    au.nome,
    au.plano,
    aug.group_name,
    COUNT(DISTINCT aol.session_id) as sessoes_ontem,
    COALESCE(SUM(CASE WHEN aol.event_type = 'SESSION_BLOCKED' THEN 1 ELSE 0 END), 0) as bloqueios
FROM alpha_users au
JOIN ab_user_groups aug ON au.id = aug.user_id
LEFT JOIN alpha_observation_logs aol ON au.id = aol.user_id
    AND aol.timestamp >= CURRENT_DATE - INTERVAL '1 day'
    AND aol.timestamp < CURRENT_DATE
GROUP BY au.nome, au.plano, aug.group_name
ORDER BY sessoes_ontem DESC;

-- 2. Bloqueios ocorridos (últimas 24h)
SELECT
    au.nome,
    aol.event_type,
    aol.event_data->>'reason_code' as motivo,
    COUNT(*) as total
FROM alpha_observation_logs aol
JOIN alpha_users au ON aol.user_id = au.id
WHERE aol.timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND aol.event_type IN ('SESSION_BLOCKED', 'QUESTION_BLOCKED', 'MONTHLY_LIMIT_REACHED')
GROUP BY au.nome, aol.event_type, aol.event_data->>'reason_code'
ORDER BY total DESC;

-- 3. Mensagens exibidas (últimas 24h)
SELECT
    event_data->>'message_type' as tipo_mensagem,
    COUNT(*) as total_exibicoes,
    COUNT(DISTINCT user_id) as usuarios_unicos
FROM alpha_observation_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND event_type = 'MESSAGE_DISPLAYED'
GROUP BY event_data->>'message_type'
ORDER BY total_exibicoes DESC;

-- 4. Ativações de escape valve (últimas 24h)
SELECT
    au.nome,
    COUNT(*) as total_ativacoes,
    MAX(aol.timestamp) as ultima_ativacao
FROM alpha_observation_logs aol
JOIN alpha_users au ON aol.user_id = au.id
WHERE aol.timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND aol.event_type = 'ESCAPE_VALVE_ACTIVATED'
GROUP BY au.nome
ORDER BY total_ativacoes DESC;

-- 5. Tempo médio de sessão (últimas 24h)
SELECT
    au.nome,
    au.plano,
    ROUND(AVG(EXTRACT(EPOCH FROM (aol.event_data->>'duration_seconds')::INTERVAL))::numeric, 2) as tempo_medio_sessao_seg
FROM alpha_observation_logs aol
JOIN alpha_users au ON aol.user_id = au.id
WHERE aol.timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND aol.event_type = 'SESSION_COMPLETED'
GROUP BY au.nome, au.plano
ORDER BY tempo_medio_sessao_seg DESC;

-- 6. Custo médio estimado (placeholder - depende de integração com LLM)
SELECT
    au.nome,
    au.plano,
    COUNT(*) as questoes_feitas,
    0.05 * COUNT(*) as custo_estimado_usd
FROM alpha_observation_logs aol
JOIN alpha_users au ON aol.user_id = au.id
WHERE aol.timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND aol.event_type = 'QUESTION_ASKED'
GROUP BY au.nome, au.plano
ORDER BY questoes_feitas DESC;
```

---

### ✅ Fase 2: Verificação de Saúde do Sistema (5 min)

```sql
-- 7. Uptime e disponibilidade
SELECT
    COUNT(DISTINCT DATE(timestamp)) as dias_com_atividade,
    MIN(timestamp) as primeira_atividade,
    MAX(timestamp) as ultima_atividade
FROM alpha_observation_logs;

-- 8. Erros e exceções (últimas 24h)
SELECT
    event_data->>'error_type' as tipo_erro,
    event_data->>'error_message' as mensagem,
    COUNT(*) as ocorrencias
FROM alpha_observation_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND event_type = 'ERROR'
GROUP BY event_data->>'error_type', event_data->>'error_message'
ORDER BY ocorrencias DESC;

-- 9. Performance de queries (últimas 24h)
SELECT
    event_data->>'query_name' as query,
    ROUND(AVG((event_data->>'duration_ms')::numeric), 2) as avg_duration_ms,
    MAX((event_data->>'duration_ms')::numeric) as max_duration_ms
FROM alpha_observation_logs
WHERE timestamp >= CURRENT_DATE - INTERVAL '1 day'
  AND event_type = 'QUERY_EXECUTED'
GROUP BY event_data->>'query_name'
HAVING AVG((event_data->>'duration_ms')::numeric) > 100
ORDER BY avg_duration_ms DESC;
```

---

### ✅ Fase 3: Análise Comparativa Control vs Variant (10 min)

```sql
-- 10. Comparação de métricas Control vs Variant
SELECT
    aug.group_name,
    COUNT(DISTINCT au.id) as usuarios,
    ROUND(AVG(sessions_per_user.total_sessions), 2) as avg_sessions_per_day,
    ROUND(AVG(blocks_per_user.total_blocks), 2) as avg_blocks_per_day
FROM ab_user_groups aug
JOIN alpha_users au ON aug.user_id = au.id
LEFT JOIN LATERAL (
    SELECT COUNT(DISTINCT session_id) as total_sessions
    FROM alpha_observation_logs
    WHERE user_id = au.id
      AND timestamp >= CURRENT_DATE - INTERVAL '1 day'
) sessions_per_user ON true
LEFT JOIN LATERAL (
    SELECT COUNT(*) as total_blocks
    FROM alpha_observation_logs
    WHERE user_id = au.id
      AND timestamp >= CURRENT_DATE - INTERVAL '1 day'
      AND event_type LIKE '%BLOCKED%'
) blocks_per_user ON true
GROUP BY aug.group_name;
```

---

### ✅ Fase 4: Registro e Documentação (5 min)

**Template de Registro Diário**: `logs/daily_report_YYYY-MM-DD.md`

```markdown
# RELATÓRIO DIÁRIO ALPHA - [DATA]

## Métricas do Dia

### Sessões
- Total de sessões: [X]
- Usuários ativos: [X/5]
- Média de sessões/usuário: [X.X]

### Bloqueios
- Total de bloqueios: [X]
- Motivo principal: [MOTIVO]
- Usuários afetados: [X]

### Mensagens
- Total de mensagens exibidas: [X]
- Tipo mais comum: [TIPO]

### Performance
- Tempo médio de sessão: [XX]s
- Erros registrados: [X]
- Escape valves ativados: [X]

## Comparação Control vs Variant
- Control: [X.X] sessões/dia, [X.X] bloqueios/dia
- Variant: [X.X] sessões/dia, [X.X] bloqueios/dia

## Observações
- [Observação 1]
- [Observação 2]

## Ações Tomadas
- [ ] Ação 1
- [ ] Ação 2

## Status: [🟢 Normal | 🟡 Atenção | 🔴 Crítico]
```

---

## 🚨 ALERTAS E THRESHOLDS

### 🔴 Crítico (Ação Imediata)
| Condição | Threshold | Ação |
|----------|-----------|------|
| Erro crítico | Qualquer ERROR_CRITICAL | Abortar Alpha, investigar |
| Uptime < 80% | Últimas 24h | Abortar Alpha, verificar infra |
| Taxa de bloqueios > 80% | Por usuário/dia | Investigar configuração |
| Escape valve > 5 ativações | Por usuário/dia | Revisar limites |

### 🟡 Atenção (Monitorar)
| Condição | Threshold | Ação |
|----------|-----------|------|
| Taxa de bloqueios > 50% | Por usuário/dia | Coletar feedback |
| Tempo de sessão < 30s | Média do dia | Verificar UX |
| Erros não-críticos > 10 | Últimas 24h | Registrar para análise |
| Usuários inativos | > 2 dias consecutivos | Contatar usuário |

### 🟢 Normal (Documentar)
| Condição | Threshold | Ação |
|----------|-----------|------|
| Variant > Control | sessions_per_day | Documentar sucesso |
| Feedback positivo | Qualquer | Registrar |
| Performance estável | Todas métricas OK | Continuar monitoramento |

---

## 📊 REGISTRO DE EVENTOS

### Função de Logging Padronizada

```sql
CREATE OR REPLACE FUNCTION log_alpha_event(
    p_user_id UUID,
    p_event_type VARCHAR(100),
    p_event_data JSONB DEFAULT '{}'::JSONB,
    p_session_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO alpha_observation_logs (
        user_id,
        event_type,
        event_data,
        session_id,
        metadata
    ) VALUES (
        p_user_id,
        p_event_type,
        p_event_data,
        p_session_id,
        jsonb_build_object(
            'logged_at', NOW(),
            'alpha_mode', true
        )
    ) RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

-- Exemplo de uso
-- SELECT log_alpha_event(
--     '11111111-1111-1111-1111-111111111111'::UUID,
--     'SESSION_STARTED',
--     '{"session_number": 1, "plan": "FREE"}'::JSONB,
--     gen_random_uuid()
-- );
```

---

## 📅 CRONOGRAMA DE REVISÕES

### Diária (09:00 AM)
- Executar checklist completo
- Registrar relatório diário
- Identificar e escalar problemas

### A Cada 3 Dias (09:00 AM)
- Análise de tendências
- Comparação Control vs Variant (tendência)
- Revisar feedback qualitativo
- Atualizar stakeholders

### Ao Final (Dia 7)
- Consolidar todas as métricas
- Gerar relatório final completo
- Recomendação para Beta

---

## 🗂️ ESTRUTURA DE ARQUIVOS

```
D:\JURIS_IA_CORE_V1\
├── logs/
│   ├── daily_report_2025-12-19.md
│   ├── daily_report_2025-12-20.md
│   ├── daily_report_2025-12-21.md
│   ├── daily_report_2025-12-22.md
│   ├── daily_report_2025-12-23.md
│   ├── daily_report_2025-12-24.md
│   ├── daily_report_2025-12-25.md
│   └── daily_report_2025-12-26.md
├── incidents/
│   └── [incident_YYYY-MM-DD_XXX.md se necessário]
└── final_report/
    └── RELATORIO_ALPHA_FINAL.md (gerado ao final)
```

---

## ✅ CONCLUSÃO

Sistema de monitoramento diário configurado com:
- ✅ Checklist completo de métricas (6 categorias)
- ✅ Verificações de saúde do sistema
- ✅ Análise comparativa Control vs Variant
- ✅ Sistema de alertas em 3 níveis
- ✅ Função de logging padronizada
- ✅ Template de relatório diário

**Objetivo**: Garantir visibilidade total e resposta rápida durante os 7 dias de Alpha.

---

**Próxima Etapa**: ETAPA 19.4 — Incidentes e Registro
