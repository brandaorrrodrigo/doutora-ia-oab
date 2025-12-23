# ETAPA 19.1 — ATIVAÇÃO DO ALPHA

**Data de Início**: 2025-12-19
**Responsável**: Gerente de Operação de Alpha Testing
**Status**: 🚀 EM EXECUÇÃO

---

## 📊 ESTADO INICIAL DO SISTEMA

### Tabelas Existentes
- ✅ ab_experiments (1 experimento criado)
- ✅ ab_user_groups (4 usuários de teste dos smoke tests)
- ✅ ab_experiment_metrics
- ✅ feature_flags
- ✅ heavy_user_escape_log

### Estado do Experimento
- **Nome**: oab_mensal_limite_ajustado_2025_q1
- **Status**: DESABILITADO (enabled = false)
- **Start Date**: NULL
- **End Date**: NULL

### Usuários Pré-Existentes
- **Total em experimentos**: 4 (dados de smoke tests)
- **Ação**: Serão limpos antes de iniciar Alpha

---

## 🎯 PROCEDIMENTOS DE ATIVAÇÃO

### 1. Configuração do Alpha Mode

Criando tabela de configuração do Alpha Mode:

```sql
CREATE TABLE IF NOT EXISTS alpha_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alpha_mode BOOLEAN DEFAULT false,
    max_users INTEGER DEFAULT 10,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    duration_days INTEGER DEFAULT 7,
    logs_enhanced BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Inserir configuração inicial do Alpha
INSERT INTO alpha_config (
    alpha_mode,
    max_users,
    start_date,
    end_date,
    duration_days,
    logs_enhanced
) VALUES (
    true,
    10,
    NOW(),
    NOW() + INTERVAL '7 days',
    7,
    true
);
```

### 2. Limpeza de Dados de Teste

Remover dados dos smoke tests anteriores:

```sql
-- Limpar dados de teste
DELETE FROM ab_experiment_metrics;
DELETE FROM ab_user_groups;
```

### 3. Ativação do Experimento

Habilitar experimento com datas definidas:

```sql
UPDATE ab_experiments
SET
    enabled = true,
    start_date = NOW(),
    end_date = NOW() + INTERVAL '7 days',
    updated_at = NOW()
WHERE experiment_name = 'oab_mensal_limite_ajustado_2025_q1';
```

### 4. Criação de Tabela de Usuários Alpha

Criar estrutura mínima para usuários Alpha:

```sql
CREATE TABLE IF NOT EXISTS alpha_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    perfil VARCHAR(50) NOT NULL,
    plano VARCHAR(50),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE alpha_users IS 'Usuários participantes do Alpha Testing (temporário)';
```

### 5. Ativação de Logs Ampliados

Criar tabela de logs de observação:

```sql
CREATE TABLE IF NOT EXISTS alpha_observation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    session_id UUID,
    metadata JSONB
);

CREATE INDEX idx_alpha_logs_user ON alpha_observation_logs(user_id, timestamp);
CREATE INDEX idx_alpha_logs_event ON alpha_observation_logs(event_type, timestamp);

COMMENT ON TABLE alpha_observation_logs IS 'Logs ampliados de observação durante Alpha Testing';
```

---

## ✅ STATUS DA ATIVAÇÃO

- [x] Tabela alpha_config criada ✅
- [x] Alpha Mode habilitado (alpha_mode = true) ✅
- [x] Limite de usuários definido (max_users = 10) ✅
- [x] Duração configurada (7 dias) ✅
- [x] Dados de teste limpos (1 metric, 4 user_groups deletados) ✅
- [x] Experimento ativado ✅
- [x] Tabela alpha_users criada ✅
- [x] Logs ampliados ativados ✅
- [x] Índices de performance criados ✅

**RESULTADO**: ✅ ETAPA 19.1 COMPLETA COM SUCESSO

---

## 📋 PARÂMETROS DO ALPHA (CONFIRMADOS)

| Parâmetro | Valor | Status |
|-----------|-------|--------|
| **Alpha Mode** | TRUE | ✅ ATIVO |
| **Máximo de Usuários** | 10 | ✅ CONFIGURADO |
| **Data de Início** | 2025-12-19 14:19 | ✅ REGISTRADO |
| **Data de Término** | 2025-12-26 14:19 | ✅ REGISTRADO |
| **Duração** | 7 dias | ✅ CONFIGURADO |
| **Logs Ampliados** | TRUE | ✅ ATIVO |
| **Experimento** | oab_mensal_limite_ajustado_2025_q1 | ✅ HABILITADO |
| **Status do Experimento** | enabled = true | ✅ ATIVO |

---

## 🗄️ ESTRUTURA CRIADA

### Tabelas Novas (3)
1. **alpha_config** - Configuração global do Alpha Mode
2. **alpha_users** - Usuários participantes do Alpha
3. **alpha_observation_logs** - Logs ampliados de observação

### Índices Criados (2)
1. **idx_alpha_logs_user** - (user_id, timestamp)
2. **idx_alpha_logs_event** - (event_type, timestamp)

### Total de Tabelas no Sistema
- ab_experiment_metrics
- ab_experiments
- ab_user_groups
- alpha_config ⭐ NOVA
- alpha_observation_logs ⭐ NOVA
- alpha_users ⭐ NOVA
- feature_flags
- heavy_user_escape_log

**Total**: 8 tabelas

---

## 🔍 QUERIES DE VERIFICAÇÃO

```sql
-- Verificar configuração do Alpha
SELECT * FROM alpha_config ORDER BY created_at DESC LIMIT 1;

-- Verificar estado do experimento
SELECT experiment_name, enabled, start_date, end_date
FROM ab_experiments
WHERE experiment_name = 'oab_mensal_limite_ajustado_2025_q1';

-- Verificar usuários Alpha
SELECT COUNT(*) as total_usuarios FROM alpha_users;

-- Verificar logs ampliados
SELECT COUNT(*) as total_logs FROM alpha_observation_logs;
```

---

**Próxima Etapa**: ETAPA 19.2 — PERFIS DE USUÁRIOS ALPHA
