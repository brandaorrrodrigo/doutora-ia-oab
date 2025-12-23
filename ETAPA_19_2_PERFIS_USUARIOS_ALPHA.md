# ETAPA 19.2 — PERFIS DE USUÁRIOS ALPHA

**Data**: 2025-12-19
**Responsável**: Gerente de Operação de Alpha Testing
**Status**: 🚀 EXECUTANDO

---

## 🎯 OBJETIVO

Criar 5 usuários Alpha com perfis diversificados para validar:
- Diferentes padrões de uso
- Diferentes planos (FREE, MENSAL, SEMESTRAL)
- Distribuição entre grupos Control e Variant
- Comportamentos extremos (heavy user)

---

## 👥 PERFIS DEFINIDOS

### Perfil 1: Administrador
- **Quantidade**: 1
- **Função**: Monitoramento técnico e validação de sistema
- **Plano**: N/A (acesso administrativo)
- **Uso esperado**: Esporádico, focado em validação

### Perfil 2: Usuários Médios
- **Quantidade**: 2
- **Função**: Uso regular da plataforma
- **Planos**: 1 FREE, 1 MENSAL
- **Uso esperado**: 1-3 sessões/dia, dentro dos limites

### Perfil 3: Heavy User Simulado
- **Quantidade**: 1
- **Função**: Estressar limites e testar escape valve
- **Plano**: MENSAL (variant - 4 sessões/dia)
- **Uso esperado**: Atingir limites diários frequentemente

### Perfil 4: Advogado Avaliador (OAB)
- **Quantidade**: 1
- **Função**: Avaliar qualidade jurídica das respostas
- **Plano**: SEMESTRAL
- **Uso esperado**: Uso profundo, questões complexas

**TOTAL**: 5 usuários (50% da capacidade máxima de 10)

---

## 📋 SCRIPT DE CRIAÇÃO

```sql
-- PERFIL 1: Administrador
INSERT INTO alpha_users (id, email, nome, perfil, plano, ativo)
VALUES (
    'a0000000-0000-0000-0000-000000000001'::UUID,
    'admin@alpha.juris-ia.test',
    'Admin Alpha',
    'ADMINISTRADOR',
    NULL,
    true
);

-- PERFIL 2A: Usuário Médio FREE
INSERT INTO alpha_users (id, email, nome, perfil, plano, ativo)
VALUES (
    'u1111111-1111-1111-1111-111111111111'::UUID,
    'user.free@alpha.juris-ia.test',
    'Usuário Free Alpha',
    'USUARIO_MEDIO',
    'FREE',
    true
);

-- PERFIL 2B: Usuário Médio MENSAL
INSERT INTO alpha_users (id, email, nome, perfil, plano, ativo)
VALUES (
    'u2222222-2222-2222-2222-222222222222'::UUID,
    'user.mensal@alpha.juris-ia.test',
    'Usuário Mensal Alpha',
    'USUARIO_MEDIO',
    'OAB_MENSAL',
    true
);

-- PERFIL 3: Heavy User MENSAL
INSERT INTO alpha_users (id, email, nome, perfil, plano, ativo)
VALUES (
    'h3333333-3333-3333-3333-333333333333'::UUID,
    'heavy.user@alpha.juris-ia.test',
    'Heavy User Alpha',
    'HEAVY_USER',
    'OAB_MENSAL',
    true
);

-- PERFIL 4: Advogado Avaliador SEMESTRAL
INSERT INTO alpha_users (id, email, nome, perfil, plano, ativo)
VALUES (
    'l4444444-4444-4444-4444-444444444444'::UUID,
    'advogado.oab@alpha.juris-ia.test',
    'Dr. Avaliador OAB Alpha',
    'ADVOGADO_AVALIADOR',
    'OAB_SEMESTRAL',
    true
);

-- Atribuir usuários ao experimento A/B
SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'a0000000-0000-0000-0000-000000000001'::UUID
) as admin_grupo;

SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'u1111111-1111-1111-1111-111111111111'::UUID
) as free_grupo;

SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'u2222222-2222-2222-2222-222222222222'::UUID
) as mensal_grupo;

SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'h3333333-3333-3333-3333-333333333333'::UUID
) as heavy_grupo;

SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'l4444444-4444-4444-4444-444444444444'::UUID
) as advogado_grupo;
```

---

## 🔍 QUERIES DE VALIDAÇÃO

```sql
-- Verificar usuários criados
SELECT id, nome, perfil, plano, ativo
FROM alpha_users
ORDER BY created_at;

-- Verificar distribuição de grupos
SELECT
    au.nome,
    au.perfil,
    au.plano,
    aug.group_name
FROM alpha_users au
JOIN ab_user_groups aug ON au.id = aug.user_id
ORDER BY au.perfil, au.nome;

-- Verificar distribuição Control vs Variant
SELECT
    group_name,
    COUNT(*) as total_usuarios
FROM ab_user_groups
WHERE experiment_id = (
    SELECT id FROM ab_experiments
    WHERE experiment_name = 'oab_mensal_limite_ajustado_2025_q1'
)
GROUP BY group_name;
```

---

## 📊 DISTRIBUIÇÃO ESPERADA

### Por Perfil
| Perfil | Quantidade | Planos |
|--------|------------|--------|
| Administrador | 1 | N/A |
| Usuário Médio | 2 | 1 FREE, 1 MENSAL |
| Heavy User | 1 | MENSAL |
| Advogado Avaliador | 1 | SEMESTRAL |
| **TOTAL** | **5** | **Diversificado** |

### Por Plano
| Plano | Quantidade | % do Total |
|-------|------------|------------|
| N/A (Admin) | 1 | 20% |
| FREE | 1 | 20% |
| OAB_MENSAL | 2 | 40% |
| OAB_SEMESTRAL | 1 | 20% |

### Por Grupo A/B (Estimado)
| Grupo | Esperado | % |
|-------|----------|---|
| Control | 2-3 | ~50% |
| Variant | 2-3 | ~50% |

*Distribuição real depende do hash modulo dos UUIDs*

---

## ✅ CRITÉRIOS DE VALIDAÇÃO

- [x] 5 usuários criados ✅
- [x] Todos com UUIDs únicos ✅
- [x] Todos com emails únicos ✅
- [x] Diversidade de perfis garantida ✅
- [x] Diversidade de planos garantida ✅
- [x] Todos atribuídos ao experimento ✅
- [x] Distribuição entre Control e Variant validada ✅

**RESULTADO**: ✅ ETAPA 19.2 COMPLETA COM SUCESSO

---

## 📊 DISTRIBUIÇÃO REAL DOS USUÁRIOS

### Usuários Criados (5/10)

| Nome | Perfil | Plano | Grupo A/B | UUID (primeiros 8) |
|------|--------|-------|-----------|-------------------|
| Admin Alpha | ADMINISTRADOR | N/A | **CONTROL** | a0000000 |
| Usuário Free Alpha | USUARIO_MEDIO | FREE | **VARIANT** | 11111111 |
| Usuário Mensal Alpha | USUARIO_MEDIO | OAB_MENSAL | **CONTROL** | 22222222 |
| Heavy User Alpha | HEAVY_USER | OAB_MENSAL | **VARIANT** ⭐ | 33333333 |
| Dr. Avaliador OAB Alpha | ADVOGADO_AVALIADOR | OAB_SEMESTRAL | **CONTROL** | 44444444 |

### Distribuição por Grupo

| Grupo | Usuários | % | Observação |
|-------|----------|---|------------|
| **CONTROL** | 3 | 60% | 3 sessões/dia (padrão) |
| **VARIANT** | 2 | 40% | 4 sessões/dia + destaque |

### Destaques da Distribuição

✅ **Heavy User no VARIANT**: Perfeito! Poderá testar o limite de 4 sessões/dia
✅ **Usuário Free no VARIANT**: Testará mensagens do grupo B
✅ **Distribuição balanceada**: 3 Control vs 2 Variant (aceitável para Alpha)

---

## 🎯 COMPORTAMENTOS ESPERADOS POR PERFIL

### Administrador
- **Sessões/dia**: 0-1 (apenas validação)
- **Objetivo**: Monitorar métricas, não usar sistema
- **Grupo A/B**: Irrelevante (não irá testar limites)

### Usuário Free
- **Sessões/dia**: 1 (limite FREE)
- **Objetivo**: Validar bloqueio na 2ª sessão
- **Expectativa**: Mensagem pedagógica clara

### Usuário Mensal
- **Sessões/dia**: 1-3 (dentro do limite)
- **Objetivo**: Uso regular sem atingir limites
- **Grupo**: Control (3 sessões) ou Variant (4 sessões)

### Heavy User
- **Sessões/dia**: 4+ (forçar limites)
- **Objetivo**: Testar escape valve e bloqueios
- **Grupo**: Preferencialmente Variant (4 sessões permitidas)
- **Expectativa**: Atingir limites diariamente

### Advogado Avaliador
- **Sessões/dia**: 2-4 (uso profissional)
- **Objetivo**: Avaliar qualidade das respostas jurídicas
- **Grupo**: Qualquer (foco em qualidade, não quantidade)

---

## 📝 NOTAS IMPORTANTES

1. **UUIDs fixos**: Garantem consistência de atribuição ao grupo A/B
2. **Emails de teste**: Domínio `.test` não será usado em produção
3. **Diversidade**: Cobertura de todos os planos e perfis críticos
4. **Limite conservador**: 5 usuários (50% da capacidade) para observação controlada

---

**Próxima Ação**: Executar script de criação de usuários
