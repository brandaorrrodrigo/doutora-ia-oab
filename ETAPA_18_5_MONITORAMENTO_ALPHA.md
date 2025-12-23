# ETAPA 18.5 - MONITORAMENTO DURANTE ALPHA

**Data**: 2025-12-19
**Responsável**: Engenheiro de Release e Qualidade
**Status**: 📋 CONFIGURADO

---

## 📊 DASHBOARDS DE MONITORAMENTO

### Dashboard 1: Saúde do Sistema
**Atualização**: Tempo real

**Métricas**:
- ✅ Uptime (target: > 95%)
- ✅ Latência p50, p95, p99 (target: < 300ms)
- ✅ Taxa de erro HTTP 500 (target: < 0.1%)
- ✅ Conexões ativas ao banco
- ✅ CPU e memória do container

**Query PostgreSQL**:
```sql
-- Conexões ativas
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE state = 'active';

-- Tempo médio de queries
SELECT
    ROUND(AVG(total_time)::numeric, 2) as avg_ms
FROM pg_stat_statements
WHERE total_time > 0
LIMIT 1;
```

---

### Dashboard 2: Métricas de Uso
**Atualização**: A cada hora

**Métricas**:
- Sessões por dia (total e por usuário)
- Bloqueios por motivo
- Tempo médio de sessão
- Taxa de engajamento diário

**Query PostgreSQL**:
```sql
-- Sessões por dia (últimos 7 dias)
SELECT
    DATE(created_at) as dia,
    COUNT(*) as total_sessoes,
    COUNT(DISTINCT user_id) as usuarios_unicos
FROM sessao_estudo
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY dia DESC;

-- Bloqueios por motivo (hoje)
SELECT
    reason_code,
    COUNT(*) as total,
    COUNT(DISTINCT user_id) as usuarios_afetados
FROM enforcement_log
WHERE DATE(blocked_at) = CURRENT_DATE
GROUP BY reason_code
ORDER BY total DESC;
```

---

### Dashboard 3: A/B Testing Metrics
**Atualização**: A cada 6 horas

**Métricas por Grupo**:
- sessions_per_day: Média de sessões/dia
- blocks_per_day: Média de bloqueios/dia
- upgrade_click: Total de clicks em upgrade
- retention_7d: % de usuários que retornaram após 7 dias

**Query PostgreSQL**:
```sql
-- Comparação Control vs Variant (sessions_per_day)
SELECT
    aug.group_name,
    COUNT(DISTINCT aem.user_id) as usuarios,
    ROUND(AVG(aem.metric_value)::numeric, 2) as avg_sessions_per_day,
    ROUND(STDDEV(aem.metric_value)::numeric, 2) as stddev
FROM ab_experiment_metrics aem
JOIN ab_user_groups aug ON aem.user_id = aug.user_id
WHERE aem.metric_name = 'sessions_per_day'
  AND aem.metric_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY aug.group_name;

-- Comparação Control vs Variant (blocks_per_day)
SELECT
    aug.group_name,
    COUNT(DISTINCT aem.user_id) as usuarios,
    ROUND(AVG(aem.metric_value)::numeric, 2) as avg_blocks_per_day
FROM ab_experiment_metrics aem
JOIN ab_user_groups aug ON aem.user_id = aug.user_id
WHERE aem.metric_name = 'blocks_per_day'
  AND aem.metric_date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY aug.group_name;
```

---

## 🚨 ALERTAS CONFIGURADOS

### Alerta Crítico (Vermelho)
**Ação**: Notificação imediata + Parar testes se necessário

| Condição | Threshold | Ação |
|----------|-----------|------|
| Uptime < 90% | Últimas 24h | Investigar infra imediatamente |
| Latência p95 > 1s | Últimas 1h | Otimizar queries/infra |
| Erro 500 > 50 | Últimas 1h | Rollback se necessário |
| Corruption de dados | Qualquer | ROLLBACK IMEDIATO |

---

### Alerta Atenção (Amarelo)
**Ação**: Revisar durante daily

| Condição | Threshold | Ação |
|----------|-----------|------|
| Uptime < 95% | Últimas 24h | Monitorar próximas 24h |
| Latência p95 > 500ms | Últimas 6h | Investigar queries lentas |
| Bloqueios/usuário > 5 | Por dia | Revisar limites |
| Engajamento < 60% | Últimos 3 dias | Coletar feedback |

---

### Alerta Informativo (Verde)
**Ação**: Documentar para relatório final

| Condição | Threshold | Ação |
|----------|-----------|------|
| Variant > Control | sessions_per_day | Documentar sucesso |
| Variant < Control | blocks_per_day | Documentar sucesso |
| Feedback positivo > 70% | Geral | Documentar para Beta |

---

## 📈 COLETA AUTOMÁTICA DE MÉTRICAS

### Script Diário (Cron: 01:00 AM)
**Arquivo**: `scripts/daily_metrics.sql`

```sql
-- Calcular sessions_per_day para cada usuário
INSERT INTO ab_experiment_metrics (
    experiment_id,
    user_id,
    group_name,
    metric_name,
    metric_value,
    metric_date
)
SELECT
    ae.id as experiment_id,
    aug.user_id,
    aug.group_name,
    'sessions_per_day' as metric_name,
    COUNT(se.id)::DECIMAL as metric_value,
    CURRENT_DATE - 1 as metric_date
FROM ab_user_groups aug
CROSS JOIN ab_experiments ae
LEFT JOIN sessao_estudo se ON se.user_id = aug.user_id
    AND DATE(se.created_at) = CURRENT_DATE - 1
WHERE ae.enabled = true
GROUP BY ae.id, aug.user_id, aug.group_name;

-- Calcular blocks_per_day para cada usuário
INSERT INTO ab_experiment_metrics (
    experiment_id,
    user_id,
    group_name,
    metric_name,
    metric_value,
    metric_date
)
SELECT
    ae.id as experiment_id,
    aug.user_id,
    aug.group_name,
    'blocks_per_day' as metric_name,
    COUNT(el.id)::DECIMAL as metric_value,
    CURRENT_DATE - 1 as metric_date
FROM ab_user_groups aug
CROSS JOIN ab_experiments ae
LEFT JOIN enforcement_log el ON el.user_id = aug.user_id
    AND DATE(el.blocked_at) = CURRENT_DATE - 1
WHERE ae.enabled = true
GROUP BY ae.id, aug.user_id, aug.group_name;
```

---

### Script Semanal (Cron: Segunda 02:00 AM)
**Arquivo**: `scripts/weekly_metrics.sql`

```sql
-- Calcular retention_7d para usuários com 7+ dias
INSERT INTO ab_experiment_metrics (
    experiment_id,
    user_id,
    group_name,
    metric_name,
    metric_value,
    metric_date
)
SELECT
    ae.id as experiment_id,
    aug.user_id,
    aug.group_name,
    'retention_7d' as metric_name,
    CASE
        WHEN COUNT(DISTINCT DATE(se.created_at)) >= 2 THEN 1.0
        ELSE 0.0
    END as metric_value,
    CURRENT_DATE as metric_date
FROM ab_user_groups aug
CROSS JOIN ab_experiments ae
LEFT JOIN sessao_estudo se ON se.user_id = aug.user_id
    AND se.created_at >= aug.assigned_at + INTERVAL '7 days'
    AND se.created_at < aug.assigned_at + INTERVAL '14 days'
WHERE ae.enabled = true
  AND aug.assigned_at <= CURRENT_DATE - INTERVAL '14 days'
GROUP BY ae.id, aug.user_id, aug.group_name;
```

---

## 📊 ANÁLISE ESTATÍSTICA

### Teste de Hipótese (Dia 7+)
**Objetivo**: Verificar se diferença entre Control e Variant é significativa

**Query**:
```sql
WITH control_data AS (
    SELECT
        metric_value
    FROM ab_experiment_metrics aem
    JOIN ab_user_groups aug ON aem.user_id = aug.user_id
    WHERE aug.group_name = 'control'
      AND aem.metric_name = 'sessions_per_day'
      AND aem.metric_date >= CURRENT_DATE - INTERVAL '7 days'
),
variant_data AS (
    SELECT
        metric_value
    FROM ab_experiment_metrics aem
    JOIN ab_user_groups aug ON aem.user_id = aug.user_id
    WHERE aug.group_name = 'variant'
      AND aem.metric_name = 'sessions_per_day'
      AND aem.metric_date >= CURRENT_DATE - INTERVAL '7 days'
)
SELECT
    'control' as group_name,
    COUNT(*) as n,
    ROUND(AVG(metric_value)::numeric, 2) as mean,
    ROUND(STDDEV(metric_value)::numeric, 2) as stddev,
    ROUND(MIN(metric_value)::numeric, 2) as min,
    ROUND(MAX(metric_value)::numeric, 2) as max
FROM control_data
UNION ALL
SELECT
    'variant' as group_name,
    COUNT(*) as n,
    ROUND(AVG(metric_value)::numeric, 2) as mean,
    ROUND(STDDEV(metric_value)::numeric, 2) as stddev,
    ROUND(MIN(metric_value)::numeric, 2) as min,
    ROUND(MAX(metric_value)::numeric, 2) as max
FROM variant_data;
```

**Interpretação**:
- Se mean_variant > mean_control + 0.3 → Sucesso provável
- Se stddev muito alto → Aumentar tempo de teste
- Se n < 30 por grupo → Dados insuficientes para conclusão

---

## 📝 REGISTRO DE INCIDENTES

### Template de Incidente
```markdown
# INCIDENTE ALPHA - YYYY-MM-DD-XXX

**Data/Hora**: YYYY-MM-DD HH:MM
**Severidade**: [CRÍTICO | ALTO | MÉDIO | BAIXO]
**Componente**: [API | Banco | Frontend | Infra]

## Descrição
Descrição detalhada do problema observado.

## Impacto
- Usuários afetados: X/12
- Tempo de indisponibilidade: X minutos
- Dados perdidos: Sim/Não

## Causa Raiz
Análise da causa do problema.

## Resolução
Passos tomados para resolver.

## Prevenção Futura
Como evitar que isso aconteça novamente.
```

---

## ✅ CHECKLIST DE MONITORAMENTO DIÁRIO

**Daily Review (09:00 AM)**:
- [ ] Verificar uptime últimas 24h
- [ ] Verificar latência p95 últimas 24h
- [ ] Verificar erros 500
- [ ] Revisar logs de erro
- [ ] Verificar métricas de uso
- [ ] Responder feedback de usuários
- [ ] Atualizar relatório diário

**Weekly Review (Segunda 10:00 AM)**:
- [ ] Analisar tendências de métricas
- [ ] Comparar Control vs Variant
- [ ] Revisar todos os incidentes da semana
- [ ] Atualizar previsão de conclusão
- [ ] Preparar sumário para stakeholders

---

## 📦 FERRAMENTAS

### 1. Logs Centralizados
**Localização**: `/var/log/juris_api/`
**Retenção**: 30 dias

**Filtros Úteis**:
```bash
# Erros últimas 24h
grep "ERROR" /var/log/juris_api/app.log | tail -100

# Bloqueios hoje
grep "BLOCKED" /var/log/juris_api/enforcement.log | wc -l

# Latência > 1s
grep "SLOW_QUERY" /var/log/juris_api/db.log
```

---

### 2. pgAdmin/DBeaver
**Acesso**: Read-only para queries de análise
**Usuário**: `alpha_readonly`

**Queries Salvas**:
- Dashboard_1_System_Health.sql
- Dashboard_2_Usage_Metrics.sql
- Dashboard_3_AB_Testing.sql

---

### 3. Scripts de Automação
**Diretório**: `/scripts/alpha_monitoring/`

- `daily_metrics.sql` - Cálculo de métricas diárias (cron 01:00)
- `weekly_metrics.sql` - Cálculo de métricas semanais (cron Segunda 02:00)
- `health_check.sh` - Verificação de saúde do sistema (cron */5 min)
- `backup_db.sh` - Backup diário do banco (cron 03:00)

---

## 🎯 CONCLUSÃO

Sistema de monitoramento configurado com:
- ✅ 3 dashboards principais
- ✅ Alertas em 3 níveis (Crítico, Atenção, Informativo)
- ✅ Coleta automática de métricas diárias e semanais
- ✅ Análise estatística para conclusão
- ✅ Registro estruturado de incidentes

**Objetivo**: Garantir visibilidade completa durante testes Alpha e detectar problemas rapidamente.

---

**Responsável**: Engenheiro de Release e Qualidade
**Data**: 2025-12-19
**Próxima Etapa**: ETAPA 18.6 - Relatório Final Alpha
