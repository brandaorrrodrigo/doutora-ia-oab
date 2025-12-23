# ETAPA 18.4 - PLANO DE TESTES ALPHA (7-10 DIAS)

**Data de Criação**: 2025-12-19
**Responsável**: Engenheiro de Release e Qualidade
**Duração**: 7-10 dias
**Status**: 📋 PLANEJADO

---

## 🎯 OBJETIVO DOS TESTES ALPHA

Validar o sistema de A/B Testing em ambiente controlado com perfis de usuários diversos, identificar bugs críticos, validar métricas e garantir estabilidade antes do lançamento Beta público.

---

## 👥 PERFIS DE USUÁRIOS ALPHA

### Perfil 1: Admin / Desenvolvedor
**Quantidade**: 2 usuários
**Responsabilidade**:
- Testar funcionalidades administrativas
- Validar queries de configuração
- Testar habilitar/desabilitar experimentos
- Monitorar logs e performance
- Reportar bugs técnicos

**Acesso**:
- Database direto (read-only queries)
- Dashboard de admin (quando disponível)
- Logs de sistema

---

### Perfil 2: Heavy User Simulado
**Quantidade**: 3 usuários
**Comportamento Esperado**:
- Uso diário intenso (4-5 sessões/dia)
- Atingir limites diários regularmente
- Simular padrão de heavy user para testar escape valve (quando implementado)
- Testar fluxos completos de estudo

**Plano**:
- OAB_MENSAL: 1 usuário no grupo Control, 1 no grupo Variant
- OAB_SEMESTRAL: 1 usuário (para comparação)

**Tarefas Diárias**:
- Iniciar 3-5 sessões de estudo
- Completar questões até atingir limite
- Reportar bloqueios inesperados
- Validar mensagens pedagógicas

---

### Perfil 3: Usuário Médio
**Quantidade**: 5 usuários
**Comportamento Esperado**:
- Uso moderado (1-2 sessões/dia)
- Não atingir limites frequentemente
- Padrão real de estudante OAB

**Distribuição**:
- FREE: 2 usuários
- OAB_MENSAL: 2 usuários (1 Control, 1 Variant)
- OAB_SEMESTRAL: 1 usuário

**Tarefas Diárias**:
- Uso natural do sistema
- Reportar UX issues
- Validar que limites não afetam uso normal

---

### Perfil 4: Advogado Avaliador (Modo OAB)
**Quantidade**: 2 usuários
**Responsabilidade**:
- Validar qualidade das questões
- Testar conteúdo jurídico
- Avaliar relevância das mensagens pedagógicas
- Feedback sobre tom das mensagens de bloqueio

**Plano**:
- OAB_MENSAL: 1 usuário
- OAB_SEMESTRAL: 1 usuário

**Tarefas Semanais**:
- Resolver 50-100 questões
- Avaliar correção das respostas
- Reportar questões de baixa qualidade

---

## 📅 ROTEIRO DIÁRIO DE VALIDAÇÃO

### Dia 1-2: Setup e Onboarding
**Objetivo**: Preparar ambiente e usuários

**Tarefas**:
- [x] Criar usuários Alpha no banco (script)
- [ ] Atribuir planos corretos
- [ ] Habilitar experimento `oab_mensal_limite_ajustado_2025_q1`
- [ ] Enviar instruções aos participantes
- [ ] Configurar canal de comunicação (ex: Slack #alpha-testing)

**Entregáveis**:
- Lista de usuários criados
- Credenciais distribuídas
- Canal de comunicação ativo

---

### Dia 3-4: Testes Básicos
**Objetivo**: Validar funcionalidades core

**Validações**:
- [ ] Todos os usuários conseguem fazer login
- [ ] Sessões de estudo iniciam corretamente
- [ ] Questões são apresentadas
- [ ] Respostas são registradas
- [ ] Bloqueios ocorrem nos limites corretos

**Métricas a Coletar**:
- Taxa de login bem-sucedido
- Tempo médio de resposta da API
- Número de sessões iniciadas por usuário
- Número de bloqueios por plano

---

### Dia 5-6: Testes de Limites e Bloqueios
**Objetivo**: Validar enforcement de limites

**Cenários**:
1. **FREE - 1 sessão/dia**
   - [ ] Usuário consegue iniciar 1ª sessão
   - [ ] Usuário é bloqueado na 2ª sessão
   - [ ] Mensagem pedagógica é exibida
   - [ ] Próximo reset está correto

2. **MENSAL Control - 3 sessões/dia**
   - [ ] Usuário consegue iniciar 3 sessões
   - [ ] Usuário é bloqueado na 4ª sessão
   - [ ] Mensagem padrão é exibida

3. **MENSAL Variant - 4 sessões/dia**
   - [ ] Usuário consegue iniciar 4 sessões
   - [ ] Usuário é bloqueado na 5ª sessão
   - [ ] Mensagem de destaque Semestral é exibida

4. **SEMESTRAL - 5 sessões/dia**
   - [ ] Usuário consegue iniciar 5 sessões
   - [ ] Usuário é bloqueado na 6ª sessão (se escape não ativo)

**Dados a Registrar**:
- Hora do bloqueio
- Mensagem exibida
- Reação do usuário (feedback)

---

### Dia 7-8: Testes de A/B Testing
**Objetivo**: Validar coleta de métricas e diferenciação de grupos

**Validações**:
- [ ] Usuários Mensal Control têm limite de 3 sessões
- [ ] Usuários Mensal Variant têm limite de 4 sessões
- [ ] Mensagens de upsell são diferentes entre grupos
- [ ] Atribuição de grupo é consistente (não muda entre dias)

**Métricas a Coletar**:
- sessions_per_day: Média de sessões por usuário por dia
- blocks_per_day: Média de bloqueios por usuário por dia
- upgrade_click: Quantos clicaram em "Upgrade" (se houver botão)
- retention_7d: Quantos usuários retornaram após 7 dias

**Queries para Análise**:
```sql
-- Média de sessões por grupo
SELECT
    aug.group_name,
    AVG(metric_value) as avg_sessions
FROM ab_experiment_metrics aem
JOIN ab_user_groups aug ON aem.user_id = aug.user_id
WHERE metric_name = 'sessions_per_day'
GROUP BY aug.group_name;

-- Taxa de bloqueio por grupo
SELECT
    aug.group_name,
    AVG(metric_value) as avg_blocks
FROM ab_experiment_metrics aem
JOIN ab_user_groups aug ON aem.user_id = aug.user_id
WHERE metric_name = 'blocks_per_day'
GROUP BY aug.group_name;
```

---

### Dia 9-10: Testes de Estresse e Edge Cases
**Objetivo**: Identificar bugs em cenários extremos

**Cenários**:
1. **Reset Diário**
   - [ ] Limites resetam corretamente às 00:00
   - [ ] Usuários conseguem iniciar sessões após reset
   - [ ] Contadores voltam a zero

2. **Múltiplas Sessões Simultâneas**
   - [ ] Sistema lida com múltiplas sessões abertas
   - [ ] Bloqueios não são duplicados

3. **Mudança de Plano**
   - [ ] Usuário que faz upgrade tem limites atualizados
   - [ ] Grupo de A/B Testing permanece o mesmo (ou é tratado)

4. **Desabilitar Experimento**
   - [ ] Experimento desabilitado não afeta usuários existentes
   - [ ] Novos usuários não são atribuídos

**Dados a Registrar**:
- Bugs identificados
- Comportamentos inesperados
- Sugestões de melhoria

---

## 📊 MÉTRICAS A MONITORAR DIARIAMENTE

### Métricas de Sistema
- **Uptime**: % de tempo online
- **Latência**: Tempo médio de resposta da API
- **Erros**: Número de erros HTTP 500
- **Logs**: Warnings e errors no log

**Alerta Vermelho se**:
- Uptime < 95%
- Latência média > 500ms
- Erros 500 > 10/dia
- Qualquer erro crítico de banco de dados

---

### Métricas de Uso
- **Sessões por dia**: Total e por usuário
- **Bloqueios por dia**: Total e por plano
- **Taxa de engajamento**: % de usuários que retornam diariamente
- **Tempo médio de sessão**: Duração média

**Alerta Amarelo se**:
- Sessões/dia < 50% do esperado
- Bloqueios/dia > 80% dos usuários
- Engajamento < 60%

---

### Métricas de A/B Testing
- **Distribuição de grupos**: % Control vs Variant
- **sessions_per_day**: Média por grupo
- **blocks_per_day**: Média por grupo
- **upgrade_click**: Total de clicks por grupo
- **retention_7d**: % de retenção por grupo

**Meta de Sucesso**:
- Variant deve ter sessions_per_day > Control
- Variant deve ter blocks_per_day < Control
- Variant deve ter upgrade_click >= Control
- Diferença estatisticamente significativa (p < 0.10 para Alpha)

---

## ✅ CRITÉRIOS DE SUCESSO ALPHA

### Técnicos
- [x] Migration 012 executada com sucesso
- [x] Zero erros críticos de banco de dados
- [ ] Uptime > 95% durante 7 dias
- [ ] Latência < 300ms (p95)
- [ ] Zero corruption de dados

### Funcionais
- [ ] Todos os 4 perfis de usuários testaram sistema
- [ ] 100% dos bloqueios ocorreram corretamente
- [ ] 100% das mensagens pedagógicas exibidas
- [ ] A/B Testing atribuindo usuários corretamente
- [ ] Métricas sendo coletadas corretamente

### UX
- [ ] Mensagens pedagógicas recebem feedback positivo
- [ ] Bloqueios não causam frustração excessiva
- [ ] Usuários entendem limites de seus planos
- [ ] Nenhum bloqueio injusto reportado

### Negócio
- [ ] Variant mostra tendência de mais sessões/dia (mesmo que não significativa)
- [ ] Nenhum usuário reportou "quero cancelar"
- [ ] Feedback geral positivo sobre pricing

---

## 🚨 CRITÉRIOS DE PARADA (Red Flags)

Interromper testes Alpha imediatamente se:
- ❌ **Bug crítico** que impede uso do sistema
- ❌ **Corruption de dados** em qualquer tabela
- ❌ **Bloqueios injustos** (usuário bloqueado sem atingir limite)
- ❌ **Performance degradada** (latência > 2s consistente)
- ❌ **Feedback negativo majoritário** (> 50% dos usuários insatisfeitos)

Se parada ocorrer:
1. Desabilitar experimento imediatamente
2. Executar rollback se necessário
3. Documentar incidente
4. Corrigir problema antes de retomar

---

## 📝 RELATÓRIO DIÁRIO (Template)

```markdown
# ALPHA DAY X - YYYY-MM-DD

## Métricas
- Usuários ativos: X/12
- Sessões iniciadas: X
- Bloqueios: X
- Erros: X

## Eventos Notáveis
- Descrição de qualquer bug ou comportamento inesperado

## Feedback de Usuários
- Comentários positivos: X
- Comentários negativos: X
- Sugestões: X

## Ações Necessárias
- [ ] Ação 1
- [ ] Ação 2
```

---

## 📦 ENTREGÁVEIS FINAIS (Dia 10)

### 1. Relatório Alpha
Documento `RELATORIO_ALPHA_PRICING.txt` contendo:
- Sumário executivo
- Resultados dos testes por perfil
- Métricas consolidadas
- Bugs identificados e resolvidos
- Feedback dos usuários
- Análise de A/B Testing (preliminar)
- Recomendação: Liberar Beta ou Ajustes Mínimos

### 2. Dataset de Testes
- Backup do banco pós-Alpha
- Logs de sistema (última semana)
- Screenshots de mensagens (para documentação)

### 3. Checklist de Pronto para Beta
- [ ] Zero bugs críticos em aberto
- [ ] Uptime > 95% validado
- [ ] Métricas estáveis
- [ ] Feedback majoritariamente positivo
- [ ] A/B Testing funcionando 100%

---

## 👨‍💻 SCRIPT DE CRIAÇÃO DE USUÁRIOS ALPHA

```sql
-- Script para criar usuários Alpha
-- Executar antes de iniciar testes

BEGIN;

-- Admin 1
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'a1111111-1111-1111-1111-111111111111'::UUID,
    'admin1@alpha.test',
    'Admin Alpha 1',
    NULL
);

-- Admin 2
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'a2222222-2222-2222-2222-222222222222'::UUID,
    'admin2@alpha.test',
    'Admin Alpha 2',
    NULL
);

-- Heavy User 1 (MENSAL Control)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'h1111111-1111-1111-1111-111111111111'::UUID,
    'heavy1@alpha.test',
    'Heavy User 1 Mensal',
    'OAB_MENSAL'
);

-- Heavy User 2 (MENSAL Variant)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'h2222222-2222-2222-2222-222222222222'::UUID,
    'heavy2@alpha.test',
    'Heavy User 2 Mensal',
    'OAB_MENSAL'
);

-- Heavy User 3 (SEMESTRAL)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'h3333333-3333-3333-3333-333333333333'::UUID,
    'heavy3@alpha.test',
    'Heavy User 3 Semestral',
    'OAB_SEMESTRAL'
);

-- Usuário Médio 1 (FREE)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'u1111111-1111-1111-1111-111111111111'::UUID,
    'user1@alpha.test',
    'User Médio 1 Free',
    'FREE'
);

-- Usuário Médio 2 (FREE)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'u2222222-2222-2222-2222-222222222222'::UUID,
    'user2@alpha.test',
    'User Médio 2 Free',
    'FREE'
);

-- Usuário Médio 3 (MENSAL Control)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'u3333333-3333-3333-3333-333333333333'::UUID,
    'user3@alpha.test',
    'User Médio 3 Mensal',
    'OAB_MENSAL'
);

-- Usuário Médio 4 (MENSAL Variant)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'u4444444-4444-4444-4444-444444444444'::UUID,
    'user4@alpha.test',
    'User Médio 4 Mensal',
    'OAB_MENSAL'
);

-- Usuário Médio 5 (SEMESTRAL)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'u5555555-5555-5555-5555-555555555555'::UUID,
    'user5@alpha.test',
    'User Médio 5 Semestral',
    'OAB_SEMESTRAL'
);

-- Advogado Avaliador 1 (MENSAL)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'e1111111-1111-1111-1111-111111111111'::UUID,
    'eval1@alpha.test',
    'Avaliador 1 Mensal',
    'OAB_MENSAL'
);

-- Advogado Avaliador 2 (SEMESTRAL)
INSERT INTO usuario (id, email, nome, tipo_plano)
VALUES (
    'e2222222-2222-2222-2222-222222222222'::UUID,
    'eval2@alpha.test',
    'Avaliador 2 Semestral',
    'OAB_SEMESTRAL'
);

COMMIT;

-- Atribuir usuários MENSAL ao experimento
SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'h1111111-1111-1111-1111-111111111111'::UUID
);  -- Forçar Control se necessário

SELECT atribuir_grupo_experimento(
    'oab_mensal_limite_ajustado_2025_q1',
    'h2222222-2222-2222-2222-222222222222'::UUID
);  -- Forçar Variant se necessário

-- Verificar atribuições
SELECT user_id, group_name FROM ab_user_groups
WHERE experiment_id = (
    SELECT id FROM ab_experiments
    WHERE experiment_name = 'oab_mensal_limite_ajustado_2025_q1'
);
```

---

## 🎯 CONCLUSÃO

Este plano de testes Alpha de 7-10 dias validará:
- ✅ Sistema de A/B Testing funcionando corretamente
- ✅ Enforcement de limites (quando implementado)
- ✅ Mensagens pedagógicas bem recebidas
- ✅ Performance e estabilidade
- ✅ Coleta de métricas precisa

**Critério de sucesso**: Zero bugs críticos + Feedback positivo > 70% + Métricas estáveis

---

**Responsável**: Engenheiro de Release e Qualidade
**Data de Início Prevista**: A definir
**Data de Término Prevista**: A definir + 10 dias
**Próxima Etapa Após Alpha**: ETAPA 18.5 - Monitoramento Durante Alpha
