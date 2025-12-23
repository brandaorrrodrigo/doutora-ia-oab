# ETAPA 14.5 - HEAVY USER ESCAPE VALVE

**Status**: ✅ IMPLEMENTADO
**Data**: 2025-12-19
**Autor**: JURIS_IA_CORE_V1 - Arquiteto de Pricing Avançado

---

## 📋 SUMÁRIO EXECUTIVO

A **Heavy User Escape Valve** é uma válvula de escape automática para usuários do plano **OAB SEMESTRAL** que demonstram padrão de uso intenso e consistente. Quando detectado comportamento de "heavy user" (uso ≥80% da capacidade nos últimos 7 dias), o sistema libera automaticamente **+1 sessão extra** para o dia atual.

### Objetivos:
- ✅ Recompensar usuários engajados
- ✅ Reduzir frustração de power users
- ✅ Não criar precedente de limites infinitos
- ✅ Manter controle de custos
- ✅ Ser 100% reversível via feature flag

---

## 🎯 CRITÉRIO DE ATIVAÇÃO

### Critério: **80% de Uso em 7 Dias**

O escape é ativado quando TODAS as condições são atendidas:

1. **Plano**: Usuário possui assinatura ativa do plano `OAB_SEMESTRAL`
2. **Uso intenso**: Sessões nos últimos 7 dias ≥ 80% da capacidade
   - Cálculo: `sessões_7dias >= (limite_sessoes_dia * 7 * 0.8)`
   - Exemplo: SEMESTRAL tem limite de 5 sessões/dia
   - Critério 80%: `5 * 7 * 0.8 = 28 sessões` nos últimos 7 dias
3. **Limite atingido hoje**: Usuário já usou todas as sessões do dia atual
4. **Não ativado hoje**: Escape ainda não foi ativado hoje (máximo 1x por dia)
5. **Feature habilitada**: Flag `heavy_user_escape_valve` está `enabled = true`

### Exemplo Prático:

**Usuário do Plano Semestral** (limite: 5 sessões/dia, +1 extra condicional):

| Dia       | Sessões | Total 7 dias |
|-----------|---------|--------------|
| Segunda   | 5       | 5            |
| Terça     | 5       | 10           |
| Quarta    | 5       | 15           |
| Quinta    | 4       | 19           |
| Sexta     | 5       | 24           |
| Sábado    | 5       | 29           |
| Domingo   | 5       | **34**       |

- Critério 80%: 28 sessões em 7 dias
- Usuário tem: **34 sessões** ✅
- No domingo, ao tentar 6ª sessão (após esgotar limite de 5):
  - ✅ Escape **ATIVADO**
  - ✅ +1 sessão extra liberada
  - ✅ Mensagem celebratória exibida

---

## 🔧 IMPLEMENTAÇÃO TÉCNICA

### 1. Estrutura do Banco de Dados

#### Tabela: `heavy_user_escape_log`

Registra todas as ativações do escape para auditoria e análise.

```sql
CREATE TABLE heavy_user_escape_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    plano_codigo VARCHAR(50) NOT NULL,
    data_ativacao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    criterio_atendido VARCHAR(255),           -- '80%_uso_7dias'
    sessoes_ultimos_7_dias INTEGER,
    sessoes_extras_concedidas INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_heavy_user_escape_user
ON heavy_user_escape_log(user_id, data_ativacao DESC);

CREATE INDEX idx_heavy_user_escape_data
ON heavy_user_escape_log(data_ativacao DESC);
```

#### Tabela: `feature_flags`

Controla ativação/desativação global da feature.

```sql
CREATE TABLE feature_flags (
    flag_name VARCHAR(100) PRIMARY KEY,
    enabled BOOLEAN DEFAULT true,
    description TEXT,
    metadata JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO feature_flags (flag_name, enabled, description, metadata)
VALUES (
    'heavy_user_escape_valve',
    true,
    'Válvula de escape automática para heavy users do plano Semestral',
    jsonb_build_object(
        'criterio', '80% uso em 7 dias',
        'planos_aplicaveis', ARRAY['OAB_SEMESTRAL'],
        'sessoes_extras', 1,
        'reversivel', true
    )
);
```

### 2. Funções PostgreSQL

#### `verificar_heavy_user_escape(p_user_id UUID)`

Verifica se usuário atende critérios e ativa escape.

**Retorna**:
- `escape_ativado` (BOOLEAN): True se ativou, False caso contrário
- `motivo` (TEXT): Mensagem explicativa
- `sessoes_extras` (INTEGER): Quantidade de sessões extras concedidas
- `sessoes_7dias` (INTEGER): Total de sessões nos últimos 7 dias

**Lógica**:
1. Busca plano ativo do usuário
2. Valida se é `OAB_SEMESTRAL` e permite extras
3. Verifica se já ativou hoje
4. Conta sessões dos últimos 7 dias
5. Calcula critério 80%
6. Verifica se atingiu limite diário hoje
7. Se todas condições atendidas, registra em `heavy_user_escape_log` e retorna sucesso

#### `pode_usar_sessao_extra_heavy_user(p_user_id UUID)`

Verifica se usuário pode usar sessão extra de heavy user hoje.

**Retorna**: BOOLEAN

**Lógica**: Verifica se existe registro em `heavy_user_escape_log` para hoje.

### 3. Módulo Python: `core/enforcement_heavy_user.py`

Classe **HeavyUserEscapeValve** com métodos:

- **`is_enabled()`**: Verifica se feature está globalmente habilitada
- **`check_and_activate(user_id)`**: Verifica e ativa escape se critérios atendidos
- **`can_use_extra_session(user_id)`**: Verifica se pode usar sessão extra hoje
- **`get_activations_log(user_id, limit)`**: Obtém log de ativações
- **`get_statistics()`**: Retorna estatísticas de uso do escape
- **`enable()`**: Habilita feature globalmente
- **`disable()`**: Desabilita feature globalmente

### 4. Integração com Enforcement

No módulo `core/enforcement.py`, método `check_can_start_session()`:

```python
# HEAVY USER ESCAPE VALVE
# Se bloqueio é por limite diário, tentar ativar escape para heavy users
if reason == ReasonCode.LIMIT_SESSIONS_DAILY:
    escape_result = self.heavy_user_escape.check_and_activate(user_id)

    if escape_result["activated"]:
        # Escape ativado! Permitir sessão com mensagem especial
        msg = self.messages.get_message(ReasonCode.HEAVY_USER_EXTRA_SESSION_GRANTED)

        return EnforcementResult(
            allowed=True,
            current_usage=sessoes_usadas,
            limit=sessoes_usadas + sessoes_disponiveis + escape_result["extra_sessions"],
            metadata={
                "heavy_user_escape_activated": True,
                "escape_reason": escape_result["reason"],
                "extra_sessions_granted": escape_result["extra_sessions"],
                "sessions_last_7_days": escape_result["sessions_last_7_days"],
                "message_title": msg["title"],
                "message_body": msg["body"]
            }
        )
```

---

## 📝 MENSAGEM PEDAGÓGICA

Quando o escape é ativado, o usuário recebe uma mensagem celebratória:

**Título**: 🎯 Sessão extra liberada!

**Corpo**:
> Parabéns pelo uso consistente! Detectamos seu ritmo intenso de estudos nos últimos 7 dias e liberamos +1 sessão extra para hoje.
>
> 💪 Continue aproveitando esse momento de alta produtividade!
>
> ✨ Este benefício é renovado automaticamente quando você mantém seu padrão de estudo consistente.
>
> Observação: Esta sessão extra não altera seu plano permanentemente. É um reconhecimento do seu engajamento excepcional.

---

## 📊 ESTATÍSTICAS E MONITORAMENTO

### Método: `get_statistics()`

Retorna:
```json
{
  "total_activations": 1247,
  "activations_today": 34,
  "activations_last_7_days": 189,
  "unique_users": 421,
  "avg_sessions_7days": 31,
  "feature_enabled": true
}
```

### Queries de Análise

**Top 10 heavy users do mês**:
```sql
SELECT
    user_id,
    COUNT(*) as ativacoes,
    AVG(sessoes_ultimos_7_dias) as media_sessoes
FROM heavy_user_escape_log
WHERE data_ativacao >= DATE_TRUNC('month', CURRENT_DATE)
GROUP BY user_id
ORDER BY ativacoes DESC
LIMIT 10;
```

**Taxa de ativação diária**:
```sql
SELECT
    DATE(data_ativacao AT TIME ZONE 'America/Sao_Paulo') as dia,
    COUNT(*) as ativacoes,
    COUNT(DISTINCT user_id) as usuarios_unicos
FROM heavy_user_escape_log
WHERE data_ativacao >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY dia
ORDER BY dia DESC;
```

---

## 🛡️ CONTROLE DE CUSTOS

### Proteções Implementadas:

1. **Máximo 1x por dia**: Escape só ativa 1 vez por dia por usuário
2. **Apenas Semestral**: Limitado ao plano mais caro
3. **Critério exigente**: 80% de uso consistente em 7 dias
4. **+1 sessão apenas**: Não libera sessões ilimitadas
5. **Feature flag global**: Pode ser desabilitada instantaneamente

### Impacto Estimado:

- **% de usuários Semestral que são heavy users**: ~15-20%
- **% destes que ativam escape**: ~30-40%
- **Impacto final**: 5-8% dos usuários Semestral (~1-2% da base total)
- **Custo adicional**: Marginal (usuários já engajados, alta retenção)

---

## ⚙️ HABILITAÇÃO E DESABILITAÇÃO

### Desabilitar Globalmente

**SQL direto**:
```sql
UPDATE feature_flags
SET enabled = false, updated_at = NOW()
WHERE flag_name = 'heavy_user_escape_valve';
```

**Python**:
```python
escape_valve = HeavyUserEscapeValve(database_url)
escape_valve.disable()
```

### Habilitar Novamente

**SQL**:
```sql
UPDATE feature_flags
SET enabled = true, updated_at = NOW()
WHERE flag_name = 'heavy_user_escape_valve';
```

**Python**:
```python
escape_valve.enable()
```

---

## 🧪 CENÁRIOS DE TESTE

### Teste 1: Ativação com Sucesso

**Setup**:
- Usuário: Plano Semestral
- Sessões últimos 7 dias: 34 (critério: 28)
- Sessões hoje: 5 (limite: 5)

**Ação**: Tentar iniciar 6ª sessão

**Resultado Esperado**:
- ✅ Escape ativado
- ✅ Sessão permitida
- ✅ Mensagem celebratória
- ✅ Registro em `heavy_user_escape_log`

### Teste 2: Critério Não Atingido

**Setup**:
- Usuário: Plano Semestral
- Sessões últimos 7 dias: 20 (critério: 28)
- Sessões hoje: 5

**Ação**: Tentar iniciar 6ª sessão

**Resultado Esperado**:
- ❌ Escape NÃO ativado
- ❌ Sessão bloqueada
- ❌ Mensagem padrão de limite diário

### Teste 3: Plano Incorreto

**Setup**:
- Usuário: Plano Mensal
- Sessões últimos 7 dias: 21 (atingiria critério se fosse Semestral)
- Sessões hoje: 3

**Ação**: Tentar iniciar 4ª sessão

**Resultado Esperado**:
- ❌ Escape NÃO ativado (plano não aplicável)
- ❌ Sessão bloqueada
- ❌ Mensagem padrão

### Teste 4: Já Ativado Hoje

**Setup**:
- Usuário: Plano Semestral
- Escape já ativado hoje
- Sessões hoje: 6 (usou a extra)

**Ação**: Tentar iniciar 7ª sessão

**Resultado Esperado**:
- ❌ Escape NÃO ativado novamente
- ❌ Sessão bloqueada
- ❌ Mensagem padrão

### Teste 5: Feature Desabilitada

**Setup**:
- `heavy_user_escape_valve` enabled = false
- Usuário atende todos os critérios

**Ação**: Tentar iniciar sessão além do limite

**Resultado Esperado**:
- ❌ Escape NÃO ativado (feature desabilitada)
- ❌ Sessão bloqueada
- ❌ Mensagem padrão

---

## 📦 ARQUIVOS RELACIONADOS

| Arquivo | Descrição |
|---------|-----------|
| `database/migrations/011_heavy_user_escape_valve.sql` | Migration com tabelas e funções |
| `core/enforcement_heavy_user.py` | Módulo Python da válvula de escape |
| `core/enforcement.py` | Integração no enforcement principal |
| `core/enforcement_messages.py` | Mensagem `HEAVY_USER_EXTRA_SESSION_GRANTED` |
| `tests/test_enforcement.py` | Testes automatizados (a expandir) |

---

## ✅ CHECKLIST DE IMPLEMENTAÇÃO

- [x] Migration 011 criada
- [x] Tabela `heavy_user_escape_log` criada
- [x] Tabela `feature_flags` criada
- [x] Função `verificar_heavy_user_escape()` implementada
- [x] Função `pode_usar_sessao_extra_heavy_user()` implementada
- [x] Módulo Python `HeavyUserEscapeValve` criado
- [x] Integração em `enforcement.py` completa
- [x] Mensagem pedagógica adicionada
- [x] ReasonCode `HEAVY_USER_EXTRA_SESSION_GRANTED` criado
- [x] Migration executada no banco
- [x] Documentação completa gerada

---

## 🚀 PRÓXIMOS PASSOS

1. **Testes Automatizados**: Expandir `test_enforcement.py` com cenários de escape
2. **Monitoramento**: Dashboard com estatísticas de ativação
3. **A/B Testing**: Comparar comportamento de heavy users com/sem escape
4. **Ajuste de Critério**: Avaliar se 80% é o threshold ideal (pode testar 70%, 75%, 85%)
5. **Variações**: Considerar critérios adicionais (ex: streak de 5 dias consecutivos)

---

## 📌 CONCLUSÃO

A **Heavy User Escape Valve** é uma estratégia elegante para:
- ✅ Recompensar engajamento sem criar precedente perigoso
- ✅ Reduzir frustração de power users
- ✅ Manter controle total de custos
- ✅ Ser 100% reversível e auditável
- ✅ Criar incentivo para uso consistente (gamificação sutil)

**Benefício estratégico**: Heavy users são os mais propensos a renovar, recomendar e tolerar aumentos de preço. Mantê-los satisfeitos tem ROI exponencial.

---

**Autor**: JURIS_IA_CORE_V1 - Arquiteto de Pricing Avançado
**Data**: 2025-12-19
**Versão**: 1.0
**Status**: ✅ IMPLEMENTADO E DOCUMENTADO
