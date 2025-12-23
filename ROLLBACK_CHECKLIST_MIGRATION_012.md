# CHECKLIST DE ROLLBACK - MIGRATION 012

**Data de Criação**: 2025-12-19
**Responsável**: Engenheiro de Release e Qualidade
**Banco**: juris_ia (PostgreSQL 15.4)
**Backup**: `backups/backup_pre_migration_012_20251219.sql` (39KB)

---

## ⚠️ QUANDO EXECUTAR ROLLBACK

Execute rollback se:
- [ ] Migration 012 falhar durante execução
- [ ] Constraints violadas após migration
- [ ] Testes Alpha identificarem bugs críticos
- [ ] Performance degradada > 50%
- [ ] Dados corrompidos detectados

---

## 📋 PROCEDIMENTO DE ROLLBACK

### OPÇÃO 1: Rollback Automatizado (RECOMENDADO)

Se a migration 012 foi executada dentro de uma transação (BEGIN/COMMIT):

```sql
-- Conectar ao banco
psql -U juris_ia_user -d juris_ia

-- Executar rollback da transação
ROLLBACK;
```

**Nota**: Apenas funciona se a migration ainda estiver em transação ativa.

### OPÇÃO 2: Rollback Manual (Drop Tables)

Se a migration foi commitada, reverter manualmente:

```sql
-- Conectar ao banco
psql -U juris_ia_user -d juris_ia

BEGIN;

-- Dropar tabelas criadas pela migration 012
DROP TABLE IF EXISTS ab_experiment_metrics CASCADE;
DROP TABLE IF EXISTS ab_user_groups CASCADE;
DROP TABLE IF EXISTS ab_experiments CASCADE;

-- Dropar funções criadas
DROP FUNCTION IF EXISTS atribuir_grupo_experimento(VARCHAR, UUID);
DROP FUNCTION IF EXISTS registrar_metrica_experimento(VARCHAR, UUID, VARCHAR, DECIMAL, JSONB);
DROP FUNCTION IF EXISTS obter_config_experimento(VARCHAR, UUID);

-- Remover experimento exemplo se foi inserido
-- (Não precisa, pois será deletado em CASCADE)

COMMIT;
```

**Verificação pós-rollback**:
```sql
SELECT tablename FROM pg_tables WHERE schemaname = 'public'
AND tablename LIKE 'ab_%';
-- Deve retornar 0 linhas
```

### OPÇÃO 3: Restauração Completa do Backup

Se rollback manual falhar ou houver corrupção de dados:

```bash
# 1. Parar aplicações que usam o banco
docker stop <api_container>

# 2. Conectar ao banco
docker exec -it juris_ia_postgres psql -U juris_ia_user -d postgres

# 3. Desconectar todos os usuários e dropar banco
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'juris_ia';
DROP DATABASE juris_ia;
CREATE DATABASE juris_ia;
\q

# 4. Restaurar backup
docker exec -i juris_ia_postgres psql -U juris_ia_user -d juris_ia < /mnt/d/JURIS_IA_CORE_V1/backups/backup_pre_migration_012_20251219.sql

# 5. Verificar integridade
docker exec juris_ia_postgres psql -U juris_ia_user -d juris_ia -c "SELECT count(*) FROM plano;"

# 6. Reiniciar aplicações
docker start <api_container>
```

---

## ✅ VALIDAÇÃO PÓS-ROLLBACK

Após executar rollback, validar:

### 1. Estrutura do Banco
```sql
-- Verificar que tabelas ab_* não existem
SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE 'ab_%';
-- Esperado: 0
```

### 2. Dados Essenciais
```sql
-- Verificar planos
SELECT codigo, preco_mensal, limite_sessoes_dia FROM plano ORDER BY preco_mensal;
-- Esperado: FREE (0), OAB_MENSAL (49.90), OAB_SEMESTRAL (247/6)

-- Verificar assinaturas
SELECT count(*) FROM assinatura WHERE status = 'active';
-- Esperado: número de assinaturas ativas antes da migration
```

### 3. Feature Flags (se existirem)
```sql
-- Verificar se feature_flags ainda existe (criada na migration 011)
SELECT count(*) FROM feature_flags;
-- Esperado: 1 (heavy_user_escape_valve)
```

### 4. Funções Essenciais
```sql
-- Verificar funções de enforcement (migration 010)
SELECT proname FROM pg_proc WHERE proname LIKE 'pode_iniciar_sessao';
-- Esperado: pode_iniciar_sessao

SELECT proname FROM pg_proc WHERE proname LIKE 'verificar_heavy_user_escape';
-- Esperado: verificar_heavy_user_escape (migration 011)
```

---

## 📊 LOGS E EVIDÊNCIAS

### Pré-Rollback
- [ ] Log de erro que motivou o rollback
- [ ] Timestamp do início do rollback
- [ ] Quem solicitou o rollback

### Durante Rollback
- [ ] Backup restaurado com sucesso (se OPÇÃO 3)
- [ ] Tabelas dropadas com sucesso (se OPÇÃO 2)
- [ ] Sem erros durante execução

### Pós-Rollback
- [ ] Todas as validações passaram
- [ ] Aplicação reiniciada e funcional
- [ ] Usuários conseguem acessar normalmente
- [ ] Sem warnings no log do PostgreSQL

---

## 🚨 COMUNICAÇÃO

### Notificar Imediatamente
- [ ] **Time de Desenvolvimento**: Migration revertida
- [ ] **Usuários Alpha** (se aplicável): Indisponibilidade temporária
- [ ] **Stakeholders**: Impacto e próximos passos

### Relatório de Incidente
Criar `INCIDENTE_ROLLBACK_MIGRATION_012.md` com:
- Motivo do rollback
- Hora de início e fim
- Impacto aos usuários
- Lições aprendidas
- Ações corretivas

---

## 📝 NOTAS IMPORTANTES

1. **Backup é crítico**: Sempre validar que backup existe e está íntegro ANTES de executar migration
2. **Transações são amigas**: Migrations complexas devem usar BEGIN/COMMIT para permitir ROLLBACK
3. **Testes locais primeiro**: Sempre testar migration em ambiente de dev antes de produção
4. **Janela de manutenção**: Executar migrations em horário de baixo tráfego
5. **Comunicação prévia**: Avisar usuários sobre possível indisponibilidade

---

## ✅ APROVAÇÃO

- [ ] Checklist revisado por: _______________
- [ ] Backup validado por: _______________
- [ ] Procedimento testado em dev: [ ] Sim [ ] Não

---

**Última Atualização**: 2025-12-19
**Versão**: 1.0
