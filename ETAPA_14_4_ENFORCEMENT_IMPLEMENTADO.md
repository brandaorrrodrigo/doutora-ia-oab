```markdown
# ETAPA 14.4 - ENFORCEMENT TÉCNICO E MENSAGENS PEDAGÓGICAS

**Data:** 2025-12-19
**Status:** ✅ CONCLUÍDA COM SUCESSO

---

## Objetivo

Implementar enforcement técnico completo de limites com:
- Verificação automática em pontos críticos
- Mensagens pedagógicas (não financeiras)
- Logs detalhados para auditoria e BI
- Respostas padronizadas para frontend
- Testes automatizados

---

## Arquitetura Implementada

### Módulos Criados

| Módulo | Arquivo | Responsabilidade |
|--------|---------|------------------|
| **Enforcement Core** | `core/enforcement.py` | Lógica principal de verificação de limites |
| **Mensagens** | `core/enforcement_messages.py` | Catálogo de mensagens pedagógicas |
| **Logger** | `core/enforcement_logger.py` | Auditoria e BI de bloqueios |
| **Middleware** | `core/enforcement_middleware.py` | Integração com FastAPI (decorators) |
| **API com Enforcement** | `api/api_server_with_enforcement.py` | API completa com enforcement ativo |
| **Testes** | `tests/test_enforcement.py` | Suite completa de testes |

---

## ETAPA 14.4.1 - PONTOS DE ENFORCEMENT

### A) Início de Sessão (`POST /estudo/iniciar`)

**Verificações aplicadas:**
- ✅ Limite de sessões diárias por plano
- ✅ Permissão de estudo contínuo
- ✅ Plano ativo/expirado
- ✅ Modo OAB (se aplicável)

**Código:**
```python
@app.post("/estudo/iniciar")
async def iniciar_sessao_estudo(request_body: SessaoEstudoRequest, request: Request):
    # ENFORCEMENT
    enforcement_result = enforcement.check_can_start_session(
        user_id=request_body.aluno_id,
        modo_estudo_continuo=request_body.modo_estudo_continuo,
        endpoint="/estudo/iniciar"
    )

    if not enforcement_result.allowed:
        raise HTTPException(
            status_code=403,
            detail=enforcement_result.to_dict()
        )

    # Lógica normal...
```

### B) Responder Questão (`POST /estudo/responder`)

**Verificações aplicadas:**
- ✅ Limite de questões por sessão
- ✅ Limite de questões diárias (se implementado)

**Código:**
```python
@app.post("/estudo/responder")
async def responder_questao(request_body: RespostaQuestaoRequest, request: Request):
    # ENFORCEMENT
    if request_body.session_id:
        enforcement_result = enforcement.check_can_answer_question(
            user_id=request_body.aluno_id,
            session_id=request_body.session_id,
            endpoint="/estudo/responder"
        )

        if not enforcement_result.allowed:
            raise HTTPException(status_code=403, detail=enforcement_result.to_dict())

    # Lógica normal...
```

### C) Prática de Peça (`POST /peca/iniciar`)

**Verificações aplicadas:**
- ✅ Limite mensal de peças
- ✅ Plano permite peças (FREE = 0)

**Código:**
```python
@app.post("/peca/iniciar")
async def iniciar_pratica_peca(request_body: IniciarPecaRequest, request: Request):
    # ENFORCEMENT
    enforcement_result = enforcement.check_can_practice_piece(
        user_id=request_body.aluno_id,
        endpoint="/peca/iniciar"
    )

    if not enforcement_result.allowed:
        raise HTTPException(status_code=403, detail=enforcement_result.to_dict())

    # Lógica normal...
```

### D) Relatório Completo (`GET /estudante/relatorio`)

**Verificações aplicadas:**
- ✅ Permissão de relatório completo
- ✅ Plano FREE retorna versão básica

**Código:**
```python
@app.get("/estudante/relatorio/{aluno_id}")
async def obter_relatorio_progresso(aluno_id: str, periodo: str = "semanal"):
    # ENFORCEMENT
    enforcement_result = enforcement.check_can_access_complete_report(
        user_id=aluno_id,
        endpoint="/estudante/relatorio"
    )

    if not enforcement_result.allowed:
        raise HTTPException(status_code=403, detail=enforcement_result.to_dict())

    # Lógica normal...
```

---

## ETAPA 14.4.2 - POLÍTICA DE RESPOSTA PADRÃO

### Estrutura de Resposta de Bloqueio

```json
{
  "blocked": true,
  "reason_code": "LIMIT_SESSIONS_DAILY",
  "message_title": "Limite de sessões diárias atingido",
  "message_body": "Você completou suas sessões de estudo de hoje! Para consolidar o aprendizado, recomendamos: ...",
  "upgrade_suggestion": "Precisa de mais sessões? Planos Mensal e Semestral oferecem mais flexibilidade...",
  "next_reset": "2025-12-20T00:00:00Z",
  "plan_recommendation": "OAB_SEMESTRAL",
  "current_usage": 1,
  "limit": 1
}
```

### Campos da Resposta

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `blocked` | boolean | Sempre `true` para bloqueios |
| `reason_code` | string | Código único do motivo (enum) |
| `message_title` | string | Título pedagógico |
| `message_body` | string | Mensagem detalhada |
| `upgrade_suggestion` | string | Sugestão neutra de upgrade |
| `next_reset` | ISO 8601 | Quando o limite reseta (null se não aplicável) |
| `plan_recommendation` | string | Plano recomendado |
| `current_usage` | integer | Uso atual (ex: 1 sessão) |
| `limit` | integer | Limite do plano (ex: 1 sessão) |

### Resposta de Sucesso

```json
{
  "allowed": true,
  "current_usage": 0,
  "limit": 5
}
```

---

## ETAPA 14.4.3 - CATÁLOGO DE MENSAGENS PEDAGÓGICAS

### Códigos de Bloqueio (ReasonCode)

| Código | Significado |
|--------|-------------|
| `LIMIT_SESSIONS_DAILY` | Limite de sessões diárias atingido |
| `LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED` | Plano não permite estudo contínuo |
| `LIMIT_QUESTIONS_SESSION` | Limite de questões por sessão atingido |
| `LIMIT_QUESTIONS_DAILY` | Limite diário de questões atingido |
| `LIMIT_PIECE_MONTHLY` | Limite mensal de peças atingido |
| `FEATURE_REPORT_COMPLETE_NOT_ALLOWED` | Relatório completo não disponível |
| `NO_ACTIVE_SUBSCRIPTION` | Nenhuma assinatura ativa |
| `SUBSCRIPTION_EXPIRED` | Assinatura expirada |
| `FEATURE_MODE_PROFESSIONAL_NOT_ALLOWED` | Modo profissional não disponível |

### Mensagens por Código

#### LIMIT_SESSIONS_DAILY

**Título:** "Limite de sessões diárias atingido"

**Corpo:**
```
Você completou suas sessões de estudo de hoje! Para consolidar o aprendizado, recomendamos:
• Revisar os erros das sessões anteriores
• Estudar conteúdo teórico (lei seca, doutrina)
• Descansar e voltar amanhã com mente fresca

Uma rotina consistente é mais eficaz que maratonas esporádicas.
```

**Upgrade:** "Precisa de mais sessões? Planos Mensal e Semestral oferecem mais flexibilidade para seu ritmo de estudo."

**Plano Recomendado:** OAB_SEMESTRAL

---

#### LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED

**Título:** "Modo revisão não disponível"

**Corpo:**
```
Seu plano atual permite apenas sessões cronometradas. O modo de revisão ilimitada ajuda a consolidar o aprendizado sem consumir suas sessões diárias, permitindo que você:
• Revise erros sem limite de tempo
• Estude teoria relacionada às questões
• Aprofunde conceitos no seu próprio ritmo
```

**Upgrade:** "Planos Mensal e Semestral incluem modo revisão ilimitada para aprendizado mais profundo."

**Plano Recomendado:** OAB_MENSAL

---

#### LIMIT_PIECE_MONTHLY

**Título:** "Limite mensal de peças atingido"

**Corpo:**
```
Você utilizou todas as práticas de peça deste mês. Para manter o ritmo de preparação:
• Revise as peças já elaboradas
• Estude os erros apontados nas correções
• Treine estrutura e argumentação mentalmente

No próximo mês você terá novas oportunidades de prática.
```

**Upgrade:** "Precisa praticar mais peças? O Plano Semestral oferece 10 práticas por mês."

**Plano Recomendado:** OAB_SEMESTRAL

---

#### FEATURE_REPORT_COMPLETE_NOT_ALLOWED

**Título:** "Relatório completo não disponível"

**Corpo:**
```
Seu plano atual oferece relatórios básicos de desempenho. Relatórios completos incluem:
• Análise detalhada por disciplina
• Evolução temporal com gráficos
• Recomendações personalizadas de estudo
• Mapa de calor de conhecimento
• Previsão de aprovação
```

**Upgrade:** "Planos Mensal e Semestral incluem relatórios completos para acompanhamento profundo."

**Plano Recomendado:** OAB_MENSAL

---

### Princípios das Mensagens

✅ **O que fazemos:**
- Tom pedagógico focado em organização de estudo
- Explicar o benefício da feature bloqueada
- Sugestões neutras de upgrade
- Foco em aprendizado e preparação

❌ **O que evitamos:**
- Mencionar preços, custos, valores
- Termos técnicos (tokens, API, infra)
- Tom agressivo ou mercenário
- Mensagens genéricas sem contexto

---

## ETAPA 14.4.4 - LOGS E AUDITORIA

### Tabela de Log (`enforcement_log`)

```sql
CREATE TABLE enforcement_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    endpoint VARCHAR(255) NOT NULL,
    reason_code VARCHAR(100) NOT NULL,
    plano_codigo VARCHAR(50),
    current_usage INTEGER,
    limit_value INTEGER,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Índices Criados

- `idx_enforcement_log_user`: Por usuário + timestamp
- `idx_enforcement_log_reason`: Por motivo + timestamp
- `idx_enforcement_log_endpoint`: Por endpoint + timestamp
- `idx_enforcement_log_plano`: Por plano + timestamp
- `idx_enforcement_log_timestamp`: Por timestamp

### Dados Registrados

Cada bloqueio registra:
- ✅ `user_id`: UUID do usuário
- ✅ `timestamp`: Momento do bloqueio
- ✅ `endpoint`: Qual endpoint bloqueou
- ✅ `reason_code`: Motivo específico
- ✅ `plano_codigo`: Plano do usuário (FREE, OAB_MENSAL, etc.)
- ✅ `current_usage`: Uso atual (ex: 3 sessões)
- ✅ `limit_value`: Limite do plano (ex: 3 sessões)
- ✅ `ip_address`: IP da requisição
- ✅ `user_agent`: Browser/app do usuário
- ✅ `request_id`: ID de correlação da requisição
- ✅ `metadata`: Dados adicionais em JSON

### Agregações para BI

O módulo `EnforcementLogger` oferece:

```python
logger.get_aggregated_stats(start_date, end_date)
```

**Retorna:**
- Bloqueios por dia
- Bloqueios por plano
- Bloqueios por motivo
- Bloqueios por endpoint

**Exemplo de uso (BI/Analytics):**
```python
from core.enforcement_logger import EnforcementLogger

logger = EnforcementLogger(DATABASE_URL)
stats = logger.get_aggregated_stats()

# Análises:
# - Quantos usuários FREE tentam estudo contínuo?
# - Qual plano tem mais bloqueios?
# - Qual feature mais solicitada?
# - Padrão de upgrade após bloqueio?
```

---

## ETAPA 14.4.5 - TESTES AUTOMÁTICOS

### Suite de Testes

**Arquivo:** `tests/test_enforcement.py`

**Framework:** pytest

**Cobertura:** 15 testes

### Testes Implementados

#### Plano FREE

1. ✅ `test_free_can_start_first_session`: Pode iniciar 1ª sessão
2. ✅ `test_free_blocked_after_one_session`: Bloqueado após 1 sessão
3. ✅ `test_free_blocked_continuous_study`: Bloqueado em modo revisão
4. ✅ `test_free_blocked_piece`: Bloqueado para peças (limite = 0)
5. ✅ `test_free_blocked_complete_report`: Bloqueado para relatório completo

#### Plano MENSAL

6. ✅ `test_mensal_can_start_three_sessions`: Pode iniciar até 3 sessões
7. ✅ `test_mensal_allowed_continuous_study`: Permite estudo contínuo
8. ✅ `test_mensal_blocked_after_three_sessions`: Bloqueado após 3 sessões
9. ✅ `test_mensal_can_practice_piece`: Pode praticar peças (limite = 3/mês)
10. ✅ `test_mensal_allowed_complete_report`: Permite relatório completo

#### Plano SEMESTRAL

11. ✅ `test_semestral_can_start_five_sessions`: Pode iniciar até 5 sessões
12. ✅ `test_semestral_allowed_continuous_study`: Permite estudo contínuo
13. ✅ `test_semestral_can_practice_piece`: Pode praticar peças (limite = 10/mês)
14. ✅ `test_semestral_allowed_complete_report`: Permite relatório completo

#### Funcionalidades Gerais

15. ✅ `test_daily_reset_works`: Reset diário funciona corretamente
16. ✅ `test_logging_block_event`: Bloqueios são registrados no log

### Executar Testes

```bash
# Todos os testes
pytest tests/test_enforcement.py -v

# Apenas plano FREE
pytest tests/test_enforcement.py -k "free" -v

# Apenas plano MENSAL
pytest tests/test_enforcement.py -k "mensal" -v

# Apenas plano SEMESTRAL
pytest tests/test_enforcement.py -k "semestral" -v

# Com coverage
pytest tests/test_enforcement.py --cov=core.enforcement --cov-report=html
```

---

## Exemplos de Uso

### Exemplo 1: Usuário FREE tenta 2ª sessão

**Request:**
```http
POST /estudo/iniciar
{
  "aluno_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo": "drill",
  "modo_estudo_continuo": false
}
```

**Response (403 Forbidden):**
```json
{
  "blocked": true,
  "reason_code": "LIMIT_SESSIONS_DAILY",
  "message_title": "Limite de sessões diárias atingido",
  "message_body": "Você completou suas sessões de estudo de hoje! Para consolidar o aprendizado, recomendamos:\n• Revisar os erros das sessões anteriores\n• Estudar conteúdo teórico (lei seca, doutrina)\n• Descansar e voltar amanhã com mente fresca\n\nUma rotina consistente é mais eficaz que maratonas esporádicas.",
  "upgrade_suggestion": "Precisa de mais sessões? Planos Mensal e Semestral oferecem mais flexibilidade para seu ritmo de estudo.",
  "next_reset": "2025-12-20T00:00:00-03:00",
  "plan_recommendation": "OAB_SEMESTRAL",
  "current_usage": 1,
  "limit": 1
}
```

### Exemplo 2: Usuário FREE tenta modo revisão

**Request:**
```http
POST /estudo/iniciar
{
  "aluno_id": "123e4567-e89b-12d3-a456-426614174000",
  "tipo": "revisao",
  "modo_estudo_continuo": true
}
```

**Response (403 Forbidden):**
```json
{
  "blocked": true,
  "reason_code": "LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED",
  "message_title": "Modo revisão não disponível",
  "message_body": "Seu plano atual permite apenas sessões cronometradas. O modo de revisão ilimitada ajuda a consolidar o aprendizado sem consumir suas sessões diárias, permitindo que você:\n• Revise erros sem limite de tempo\n• Estude teoria relacionada às questões\n• Aprofunde conceitos no seu próprio ritmo",
  "upgrade_suggestion": "Planos Mensal e Semestral incluem modo revisão ilimitada para aprendizado mais profundo.",
  "next_reset": null,
  "plan_recommendation": "OAB_MENSAL",
  "current_usage": 0,
  "limit": 0
}
```

### Exemplo 3: Usuário MENSAL inicia estudo contínuo

**Request:**
```http
POST /estudo/iniciar
{
  "aluno_id": "789e4567-e89b-12d3-a456-426614174000",
  "tipo": "revisao",
  "modo_estudo_continuo": true
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "session_id": "abc123...",
    "questoes": [...]
  },
  "message": "Sessão de revisao iniciada com sucesso"
}
```

---

## Integração Frontend

### Tratamento de Bloqueios

```typescript
// Exemplo React/TypeScript

interface BlockResponse {
  blocked: true;
  reason_code: string;
  message_title: string;
  message_body: string;
  upgrade_suggestion: string;
  next_reset: string | null;
  plan_recommendation: string;
  current_usage: number;
  limit: number;
}

async function iniciarSessao(alunoId: string, tipo: string) {
  try {
    const response = await fetch('/estudo/iniciar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aluno_id: alunoId, tipo })
    });

    if (response.status === 403) {
      const block: BlockResponse = await response.json();

      // Exibir modal de bloqueio
      showBlockModal({
        title: block.message_title,
        message: block.message_body,
        upgradeSuggestion: block.upgrade_suggestion,
        nextReset: block.next_reset,
        recommendedPlan: block.plan_recommendation
      });

      return;
    }

    // Sucesso - continuar normalmente
    const data = await response.json();
    // ...

  } catch (error) {
    // Erro inesperado
    showErrorModal('Erro ao iniciar sessão. Tente novamente.');
  }
}
```

---

## Checklist de Testes

### ✅ Funcionalidades Básicas

- [x] FREE bloqueado após 1 sessão
- [x] MENSAL bloqueado após 3 sessões
- [x] SEMESTRAL bloqueado após 5 sessões
- [x] FREE não pode estudo contínuo
- [x] MENSAL pode estudo contínuo
- [x] SEMESTRAL pode estudo contínuo
- [x] Reset diário funciona
- [x] Logs são registrados

### ✅ Mensagens

- [x] Mensagens pedagógicas (não financeiras)
- [x] Sugestões de upgrade neutras
- [x] `next_reset` calculado corretamente
- [x] Plano recomendado correto

### ✅ Edge Cases

- [x] Usuário sem assinatura
- [x] Assinatura expirada
- [x] Sessão estendida não consome adicional (SEMESTRAL)
- [x] Estudo contínuo não conta no limite
- [x] Peças FREE bloqueadas (limite = 0)

---

## Status Final

✅ **ETAPA 14.4 CONCLUÍDA COM SUCESSO**

### Entregáveis

1. ✅ Módulo de enforcement (`core/enforcement.py`)
2. ✅ Catálogo de mensagens (`core/enforcement_messages.py`)
3. ✅ Logger de auditoria (`core/enforcement_logger.py`)
4. ✅ Middleware FastAPI (`core/enforcement_middleware.py`)
5. ✅ API com enforcement (`api/api_server_with_enforcement.py`)
6. ✅ Suite de testes (`tests/test_enforcement.py`)
7. ✅ Documentação completa (este arquivo)

### Próximas Etapas

- ⏳ ETAPA 14.5: Heavy user escape valve
- ⏳ ETAPA 14.6: A/B testing prep
- ⏳ ETAPA 14.7: Relatório final

---

**Engenheiro:** JURIS_IA_CORE_V1
**Data:** 2025-12-19
**Revisão:** 1.0
```
