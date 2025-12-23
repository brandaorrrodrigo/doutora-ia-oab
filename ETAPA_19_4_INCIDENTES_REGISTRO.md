# ETAPA 19.4 — INCIDENTES E REGISTRO

**Data**: 2025-12-19
**Responsável**: Gerente de Operação de Alpha Testing
**Status**: 📋 CONFIGURADO

---

## 🎯 OBJETIVO

Estabelecer política clara de classificação, resposta e registro de incidentes durante o Alpha Testing, garantindo:
- Resposta adequada à severidade
- Decisões consistentes de abort/continue
- Histórico completo para análise
- Aprendizados documentados

---

## 🚨 CLASSIFICAÇÃO DE INCIDENTES

### 🔴 CRÍTICO - Abortar Alpha Imediatamente

**Critérios**:
- Corrupção de dados
- Perda de dados de usuários
- Vazamento de informações sensíveis
- Downtime completo > 1 hora
- Bug que impede uso do sistema
- Erro que afeta todos os usuários

**Ação**:
1. **ABORTAR ALPHA IMEDIATAMENTE**
2. Desabilitar experimento: `UPDATE ab_experiments SET enabled = false`
3. Notificar stakeholders
4. Criar incident report completo
5. Restaurar backup se necessário
6. Investigar causa raiz
7. **NÃO retomar até correção e re-teste**

**Registro**:
```markdown
# INCIDENTE CRÍTICO - YYYY-MM-DD-XXX

**Status**: 🔴 ALPHA ABORTADO
**Data/Hora**: YYYY-MM-DD HH:MM
**Severidade**: CRÍTICA

## Descrição
[Descrição detalhada do incidente crítico]

## Impacto
- Usuários afetados: [X/5]
- Dados perdidos: [Sim/Não]
- Tempo de indisponibilidade: [X] horas
- Operações afetadas: [Lista]

## Causa Raiz
[Análise detalhada da causa]

## Ações Tomadas
1. Alpha abortado em [HH:MM]
2. Experimento desabilitado
3. [Outras ações]

## Decisão
❌ ALPHA ABORTADO - Correção necessária antes de retomar

## Responsável
[Nome]
```

---

### 🟡 MÉDIO - Registrar e Monitorar

**Critérios**:
- Bug não-bloqueante
- Erro em funcionalidade secundária
- Inconsistência de dados não-crítica
- Performance degradada (mas usável)
- Downtime parcial < 30 min
- Afeta 1-2 usuários apenas

**Ação**:
1. **CONTINUAR ALPHA**
2. Registrar incident report
3. Adicionar item de correção para pós-Alpha
4. Monitorar recorrência
5. Coletar logs e evidências
6. Se recorrente (>3x) → escalar para CRÍTICO

**Registro**:
```markdown
# INCIDENTE MÉDIO - YYYY-MM-DD-XXX

**Status**: 🟡 REGISTRADO E MONITORANDO
**Data/Hora**: YYYY-MM-DD HH:MM
**Severidade**: MÉDIA

## Descrição
[Descrição do incidente]

## Impacto
- Usuários afetados: [X/5]
- Funcionalidade afetada: [Nome]
- Workaround disponível: [Sim/Não]

## Evidências
- Logs: [Link ou trecho]
- Screenshots: [Se aplicável]

## Ações Imediatas
1. Registrado em [HH:MM]
2. [Outras ações]

## Decisão
⚠️ CONTINUAR ALPHA - Monitorar recorrência
✅ Item criado para correção pós-Alpha

## Responsável
[Nome]
```

---

### 🟢 BAIXO - Feedback Subjetivo

**Critérios**:
- Feedback subjetivo de usuário
- Sugestão de melhoria
- Preferência pessoal
- Bug cosmético (não afeta funcionalidade)
- Mensagem confusa mas não incorreta
- Erro de digitação em texto

**Ação**:
1. **CONTINUAR ALPHA**
2. Classificar feedback
3. Registrar em log de sugestões
4. **NÃO agir durante Alpha**
5. Avaliar para roadmap futuro

**Registro**:
```markdown
# FEEDBACK - YYYY-MM-DD-XXX

**Status**: 🟢 REGISTRADO PARA ANÁLISE FUTURA
**Data/Hora**: YYYY-MM-DD HH:MM
**Tipo**: SUGESTÃO/COSMÉTICO/PREFERÊNCIA

## Descrição
[Descrição do feedback]

## Usuário
[Nome do usuário Alpha]

## Classificação
- [ ] Sugestão de feature
- [ ] Melhoria de UX
- [ ] Correção cosmética
- [ ] Preferência pessoal

## Decisão
✅ CONTINUAR ALPHA - Registrado para avaliação futura

## Responsável
[Nome]
```

---

## 📋 LOG ESTRUTURADO DE INCIDENTES

### Tabela de Incidentes

```sql
CREATE TABLE IF NOT EXISTS alpha_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_code VARCHAR(50) UNIQUE NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'MEDIUM', 'LOW')),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    impact JSONB,
    users_affected INTEGER,
    status VARCHAR(50) DEFAULT 'OPEN',
    resolution TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB
);

CREATE INDEX idx_alpha_incidents_severity ON alpha_incidents(severity, created_at);
CREATE INDEX idx_alpha_incidents_status ON alpha_incidents(status);

COMMENT ON TABLE alpha_incidents IS 'Registro de incidentes durante Alpha Testing';

-- Inserir incidente
INSERT INTO alpha_incidents (
    incident_code,
    severity,
    title,
    description,
    users_affected,
    impact
) VALUES (
    'ALPHA-2025-12-19-001',
    'MEDIUM',
    'Exemplo de incidente médio',
    'Descrição detalhada do problema',
    1,
    '{"downtime_minutes": 5, "data_lost": false}'::JSONB
);
```

---

## 🔍 QUERIES DE ANÁLISE

### Resumo de Incidentes

```sql
-- Total de incidentes por severidade
SELECT
    severity,
    COUNT(*) as total,
    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as abertos,
    COUNT(CASE WHEN status = 'RESOLVED' THEN 1 END) as resolvidos
FROM alpha_incidents
GROUP BY severity
ORDER BY FIELD(severity, 'CRITICAL', 'MEDIUM', 'LOW');

-- Incidentes críticos em aberto
SELECT
    incident_code,
    title,
    users_affected,
    created_at
FROM alpha_incidents
WHERE severity = 'CRITICAL'
  AND status = 'OPEN'
ORDER BY created_at DESC;

-- Timeline de incidentes
SELECT
    DATE(created_at) as dia,
    severity,
    COUNT(*) as total
FROM alpha_incidents
GROUP BY DATE(created_at), severity
ORDER BY dia DESC, severity;
```

---

## 🎯 CRITÉRIOS DE DECISÃO

### Abortar Alpha SE:

- [x] **1 ou mais incidentes CRÍTICOS** não resolvidos
- [x] **Downtime total > 4 horas** durante os 7 dias
- [x] **Corrupção de dados** detectada
- [x] **Vazamento de segurança** confirmado
- [x] **Bug bloqueante** afetando todos os usuários
- [x] **Taxa de erros > 50%** das operações

### Continuar Alpha SE:

- [x] **Zero incidentes CRÍTICOS**
- [x] **Incidentes MÉDIOS < 10** durante os 7 dias
- [x] **Todos os incidentes MÉDIOS** têm workaround
- [x] **Uptime > 95%**
- [x] **Feedback geral positivo** (>60%)

---

## 📊 TEMPLATE DE INCIDENT REPORT

**Arquivo**: `incidents/ALPHA-YYYY-MM-DD-XXX.md`

```markdown
# INCIDENT REPORT - ALPHA-YYYY-MM-DD-XXX

## Informações Básicas

| Campo | Valor |
|-------|-------|
| **Código** | ALPHA-YYYY-MM-DD-XXX |
| **Severidade** | [CRÍTICO/MÉDIO/BAIXO] |
| **Data/Hora** | YYYY-MM-DD HH:MM:SS |
| **Detectado por** | [Nome/Sistema] |
| **Status** | [OPEN/INVESTIGATING/RESOLVED/CLOSED] |

---

## Descrição do Incidente

[Descrição detalhada do que aconteceu]

---

## Impacto

### Usuários Afetados
- Total: [X/5]
- Nomes: [Lista de usuários]

### Funcionalidades Afetadas
- [Funcionalidade 1]: [Severidade do impacto]
- [Funcionalidade 2]: [Severidade do impacto]

### Dados
- Dados perdidos: [Sim/Não]
- Dados corrompidos: [Sim/Não]
- Backup disponível: [Sim/Não]

### Tempo
- Início: [HH:MM]
- Detecção: [HH:MM]
- Resolução: [HH:MM]
- Duração total: [X] minutos

---

## Causa Raiz

### Análise Inicial
[Análise preliminar]

### Investigação
[Passos de investigação realizados]

### Causa Confirmada
[Causa raiz identificada]

---

## Cronologia

| Horário | Evento |
|---------|--------|
| HH:MM | Incidente iniciado |
| HH:MM | Primeira detecção |
| HH:MM | Investigação iniciada |
| HH:MM | Causa identificada |
| HH:MM | Correção aplicada |
| HH:MM | Resolução confirmada |

---

## Resolução

### Ações Tomadas
1. [Ação 1]
2. [Ação 2]
3. [Ação 3]

### Workaround (se aplicável)
[Descrição do workaround temporário]

### Correção Definitiva
[Descrição da correção permanente]

---

## Prevenção Futura

### Como Evitar Recorrência
1. [Medida preventiva 1]
2. [Medida preventiva 2]

### Melhorias de Monitoramento
1. [Melhoria de alerta 1]
2. [Melhoria de log 2]

---

## Decisão de Continuidade

- [ ] 🔴 ABORTAR ALPHA
- [ ] 🟡 CONTINUAR COM RESSALVAS
- [ ] 🟢 CONTINUAR NORMALMENTE

**Justificativa**: [Justificativa da decisão]

---

## Evidências

### Logs
```
[Trechos relevantes de logs]
```

### Screenshots
- [Link para screenshot 1]
- [Link para screenshot 2]

### Queries de Análise
```sql
[Queries SQL usadas para investigação]
```

---

## Aprovações

**Registrado por**: [Nome]
**Data**: YYYY-MM-DD HH:MM

**Revisado por**: [Nome do Tech Lead]
**Data**: YYYY-MM-DD HH:MM

**Decisão aprovada por**: [Nome do Product Owner]
**Data**: YYYY-MM-DD HH:MM

---

**Status Final**: [RESOLVIDO/EM ANDAMENTO/ABORTADO]
```

---

## ✅ CONCLUSÃO

Sistema de gestão de incidentes configurado com:
- ✅ 3 níveis de severidade claramente definidos
- ✅ Critérios objetivos para abort/continue
- ✅ Template padronizado de incident report
- ✅ Tabela de registro estruturado
- ✅ Queries de análise e monitoramento

**Objetivo**: Garantir respostas consistentes e decisões baseadas em critérios claros durante o Alpha.

---

**Próxima Etapa**: ETAPA 19.5 — Relatório Final do Alpha
