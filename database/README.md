# JURIS_IA_CORE_V1 - Database Module

Sistema de banco de dados para preparação OAB com IA adaptativa.

## 📋 Visão Geral

Este módulo contém a arquitetura completa de dados do JURIS_IA, incluindo:

- **14 entidades principais** com ~350 campos
- **8 dimensões de perfil cognitivo** jurídico
- **28 tipos de erros jurídicos** classificados
- **Sistema de snapshots** para análise temporal
- **Conformidade LGPD** nativa

## 📁 Estrutura de Arquivos

```
database/
├── README.md                                  # Este arquivo
├── schema.sql                                 # Schema completo PostgreSQL
├── 01_ENTIDADES_PRINCIPAIS.txt               # Documentação: 14 entidades
├── 02_PERFIL_COGNITIVO_JURIDICO.txt          # Documentação: 8 dimensões cognitivas
├── 03_CLASSIFICACAO_ERROS_JURIDICOS.txt      # Documentação: 28 tipos de erros
├── 04_SNAPSHOTS_COGNITIVOS.txt               # Documentação: Snapshots temporais
└── 05_GOVERNANCA_DADOS_LGPD.txt              # Documentação: Governança e LGPD
```

## 🗄️ Tabelas do Banco

### Tabelas Principais (14)

| # | Tabela | Descrição | Registros Esperados |
|---|--------|-----------|---------------------|
| 1 | `users` | Usuários do sistema | ~10.000 |
| 2 | `perfil_juridico` | **CORE** - Perfil cognitivo completo | ~10.000 (1:1 com users) |
| 3 | `progresso_disciplina` | Progresso por disciplina | ~150.000 (15 disc x 10k users) |
| 4 | `progresso_topico` | Progresso granular por tópico | ~500.000 |
| 5 | `sessao_estudo` | Sessões de estudo | ~500.000 |
| 6 | `interacao_questao` | **MAIS VOLUMOSA** - Cada resposta | ~20.000.000 |
| 7 | `analise_erro` | Análise profunda de erros | ~5.000.000 |
| 8 | `pratica_peca` | Prática de peças (2ª fase) | ~50.000 |
| 9 | `erro_peca` | Erros em peças | ~200.000 |
| 10 | `revisao_agendada` | Revisões espaçadas | ~1.000.000 |
| 11 | `snapshot_cognitivo` | Snapshots temporais | ~500.000 |
| 12 | `metricas_temporais` | Métricas pré-calculadas | ~2.000.000 |
| 13 | `questoes_banco` | Banco de questões OAB | ~5.000 |
| 14 | `log_sistema` | Logs auditoria/segurança | ~10.000.000 |
| 15 | `consentimentos` | Consentimentos LGPD | ~10.000 |

**Total estimado**: ~40 milhões de registros com 10.000 usuários ativos

### Tabelas Auxiliares

- **ENUMs**: 7 tipos enumerados para consistência de dados
- **VIEWs**: 2 views (dashboard_estudante, dashboard_governanca)

## 🚀 Instalação

### Pré-requisitos

- PostgreSQL 14+ (recomendado 15+)
- ~100 GB de espaço em disco (para 10k usuários ativos)
- 8 GB RAM mínimo (recomendado 16 GB)

### Passo 1: Criar Database

```bash
# Criar database
createdb juris_ia_db -U postgres

# Ou via SQL
psql -U postgres -c "CREATE DATABASE juris_ia_db ENCODING 'UTF8';"
```

### Passo 2: Aplicar Schema

```bash
# Aplicar schema completo
psql -U postgres -d juris_ia_db -f schema.sql

# Verificar criação
psql -U postgres -d juris_ia_db -c "\dt"
```

### Passo 3: Verificar Instalação

```sql
-- Conectar ao banco
psql -U postgres -d juris_ia_db

-- Verificar tabelas
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Verificar índices
SELECT
    tablename,
    COUNT(*) as total_indices
FROM pg_indexes
WHERE schemaname = 'public'
GROUP BY tablename
ORDER BY total_indices DESC;

-- Verificar views
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public';
```

Resultado esperado:
```
Tabelas: 15
Índices: ~50
Views: 2
Triggers: 10
```

## 📊 Estrutura de Dados

### Perfil Cognitivo (8 Dimensões)

```jsonb
{
  "nivel_geral": "INTERMEDIARIO",
  "pontuacao_global": 450,
  "taxa_acerto_global": 68.5,

  "estado_emocional": {
    "confianca": 0.72,
    "stress": 0.45,
    "motivacao": 0.83,
    "fadiga": 0.30
  },

  "maturidade_juridica": {
    "pensamento_sistemico": 0.65,
    "capacidade_abstracao": 0.58,
    "dominio_terminologia": 0.71,
    "raciocinio_analogico": 0.62,
    "interpretacao_juridica": 0.69
  },

  "padroes_aprendizagem": {
    "estilo_predominante": "VISUAL_PRATICO",
    "velocidade_leitura_wpm": 185,
    "nivel_explicacao_preferido": 2,
    "necessita_analogias": true
  },

  "riscos": {
    "risco_evasao": 0.12,
    "risco_burnout": 0.25,
    "dias_streak_atual": 14
  }
}
```

### Classificação de Erros (7 Categorias, 28 Tipos)

```sql
-- Categorias principais
ERRO_CONCEITUAL          -- 42% dos erros
ERRO_INTERPRETACAO       -- 23%
CONFUSAO_INSTITUTOS      -- 18%
ERRO_LEITURA_ATENCAO     -- 12%
FALTA_BASE_JURIDICA      -- 8%
ERRO_ESTRATEGICO_2FASE   -- 5%
ERRO_TRAP                -- 4%
```

## 🔍 Queries Úteis

### Dashboard do Estudante

```sql
-- Usar view pronta
SELECT * FROM dashboard_estudante WHERE user_id = '<uuid>';

-- Ou query manual
SELECT
    u.nome,
    p.nivel_geral,
    p.pontuacao_global,
    p.taxa_acerto_global,
    COUNT(iq.id) as total_questoes,
    COUNT(iq.id) FILTER (WHERE iq.resultado = 'ACERTO') as acertos
FROM users u
JOIN perfil_juridico p ON p.user_id = u.id
LEFT JOIN interacao_questao iq ON iq.user_id = u.id
WHERE u.id = '<uuid>'
GROUP BY u.id, u.nome, p.nivel_geral, p.pontuacao_global, p.taxa_acerto_global;
```

### Evolução Temporal (Snapshots)

```sql
-- Evolução da taxa de acerto últimos 3 meses
SELECT
    momento::date as data,
    tipo_trigger,
    desempenho->>'taxa_acerto_geral' as taxa_acerto,
    perfil_completo->'estado_emocional'->>'confianca' as confianca
FROM snapshot_cognitivo
WHERE user_id = '<uuid>'
  AND momento >= NOW() - INTERVAL '3 months'
ORDER BY momento;
```

### Top 10 Erros do Aluno

```sql
SELECT
    tipo_erro_especifico,
    COUNT(*) as ocorrencias,
    STRING_AGG(DISTINCT disciplina, ', ') as disciplinas_afetadas
FROM analise_erro
WHERE user_id = '<uuid>'
GROUP BY tipo_erro_especifico
ORDER BY ocorrencias DESC
LIMIT 10;
```

### Revisões Pendentes

```sql
SELECT
    topico,
    disciplina,
    data_revisao,
    CURRENT_DATE - data_revisao as dias_atrasado,
    forca_memoria_antes
FROM revisao_agendada
WHERE user_id = '<uuid>'
  AND revisado = FALSE
  AND data_revisao <= CURRENT_DATE
ORDER BY data_revisao;
```

## ⚡ Performance

### Índices Críticos

Os índices mais importantes para performance:

```sql
-- Interação questão (tabela mais volumosa)
CREATE INDEX idx_interacao_user ON interacao_questao(user_id);
CREATE INDEX idx_interacao_user_disciplina ON interacao_questao(user_id, disciplina);
CREATE INDEX idx_interacao_erros ON interacao_questao(user_id, questao_id, respondido_em)
    WHERE resultado = 'ERRO';

-- Snapshots (queries temporais)
CREATE INDEX idx_snapshot_user_momento ON snapshot_cognitivo(user_id, momento DESC);

-- Revisões (busca diária)
CREATE INDEX idx_revisao_pendente ON revisao_agendada(user_id, data_revisao)
    WHERE revisado = FALSE;
```

### Particionamento (Para Grande Escala)

Quando `interacao_questao` atingir ~1 milhão de registros:

```sql
-- 1. Criar tabela particionada
CREATE TABLE interacao_questao_part (
    LIKE interacao_questao INCLUDING ALL
) PARTITION BY RANGE (respondido_em);

-- 2. Criar partições mensais
CREATE TABLE interacao_questao_2025_01 PARTITION OF interacao_questao_part
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE interacao_questao_2025_02 PARTITION OF interacao_questao_part
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- ... etc

-- 3. Migrar dados (em janela de manutenção)
INSERT INTO interacao_questao_part SELECT * FROM interacao_questao;
```

### Tuning PostgreSQL

`postgresql.conf` recomendado:

```ini
# Memória
shared_buffers = 4GB             # 25% da RAM
effective_cache_size = 12GB      # 75% da RAM
work_mem = 128MB
maintenance_work_mem = 1GB

# Conexões
max_connections = 200

# Checkpoints
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9

# WAL
wal_buffers = 16MB
wal_compression = on

# Query planner
random_page_cost = 1.1           # SSD
effective_io_concurrency = 200   # SSD

# Autovacuum
autovacuum = on
autovacuum_max_workers = 4
```

## 🔒 Segurança e LGPD

### Criptografia

**Em repouso**:
```bash
# Habilitar criptografia de disco (filesystem level)
# OU usar PostgreSQL com extensão pgcrypto
```

**Em trânsito**:
```ini
# postgresql.conf
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
```

### Anonimização

```sql
-- Função de anonimização já documentada
-- Ver arquivo: 05_GOVERNANCA_DADOS_LGPD.txt seção 3.2

-- Testar anonimização
SELECT * FROM users WHERE email = 'teste@example.com';
-- Executar anonimização
-- SELECT anonimizar_dados_usuario('<uuid>', 'SOLICITACAO_USUARIO');
-- Verificar
SELECT * FROM users WHERE hash_anonimo = '<hash>';
```

### Auditoria

Todos os acessos a dados pessoais são logados:

```sql
-- Ver acessos a dados pessoais últimos 30 dias
SELECT
    criado_em,
    metadata->>'user_id_acessado' as usuario_acessado,
    metadata->>'admin_id' as admin,
    metadata->>'motivo' as motivo
FROM log_sistema
WHERE tipo = 'ACESSO_DADOS_PESSOAIS'
  AND criado_em >= NOW() - INTERVAL '30 days'
ORDER BY criado_em DESC;
```

## 💾 Backup e Recuperação

### Backup Diário (Automático)

```bash
#!/bin/bash
# backup_diario.sh

BACKUP_DIR="/backups/daily"
DATE=$(date +%Y%m%d)
DB_NAME="juris_ia_db"

# Dump completo
pg_dump -Fc $DB_NAME > $BACKUP_DIR/juris_ia_$DATE.dump

# Manter apenas últimos 30 dias
find $BACKUP_DIR -name "juris_ia_*.dump" -mtime +30 -delete

# Log
echo "$(date): Backup $DATE criado" >> /var/log/juris_backup.log
```

### Backup WAL (PITR - Point-in-Time Recovery)

`postgresql.conf`:
```ini
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/wal_archive/%f'
archive_timeout = 300  # 5 minutos
```

### Restauração

```bash
# Restaurar backup completo
pg_restore -d juris_ia_db /backups/daily/juris_ia_20250115.dump

# Restaurar para ponto específico no tempo
# (requer configuração de WAL)
```

## 📈 Monitoramento

### Métricas Importantes

```sql
-- 1. Tamanho das tabelas
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 2. Índices não utilizados
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname !~ '^pg_toast'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 3. Queries lentas (> 1s)
SELECT
    query,
    calls,
    total_exec_time / 1000 as total_seconds,
    mean_exec_time / 1000 as mean_seconds,
    max_exec_time / 1000 as max_seconds
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC
LIMIT 20;

-- 4. Cache hit ratio (deve ser > 95%)
SELECT
    sum(heap_blks_read) as heap_read,
    sum(heap_blks_hit) as heap_hit,
    sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as cache_hit_ratio
FROM pg_statio_user_tables;
```

### Alertas Recomendados

- ✅ Backup diário falhou
- ✅ Disco > 80% cheio
- ✅ Queries lentas > 5s
- ✅ Cache hit ratio < 90%
- ✅ Conexões > 80% do max
- ✅ Replication lag > 10s (se houver réplica)

## 🧪 Testes

### 1. Teste de Integridade Referencial

```sql
-- Verificar FKs orfãs (não deveria retornar nada)
SELECT 'perfil_juridico' as tabela, COUNT(*) as orfaos
FROM perfil_juridico p
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p.user_id)

UNION ALL

SELECT 'interacao_questao', COUNT(*)
FROM interacao_questao iq
WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = iq.user_id)
   OR NOT EXISTS (SELECT 1 FROM questoes_banco q WHERE q.id = iq.questao_id);
```

### 2. Teste de Performance

```sql
-- Benchmark: buscar dashboard de aluno (deve ser < 200ms)
EXPLAIN ANALYZE
SELECT * FROM dashboard_estudante WHERE user_id = '<uuid>';

-- Benchmark: gerar snapshot (deve ser < 500ms)
-- (Executar via aplicação)
```

### 3. Teste de Anonimização

```sql
-- 1. Criar usuário de teste
INSERT INTO users (nome, email, password_hash)
VALUES ('Teste Anonimização', 'anon_test@test.local', 'hash');

-- 2. Executar anonimização
-- SELECT anonimizar_dados_usuario(...);

-- 3. Verificar não-reidentificação
-- SELECT verificar_qualidade_anonimizacao(...);
```

## 📚 Documentação Adicional

- `01_ENTIDADES_PRINCIPAIS.txt` - Estrutura detalhada das 14 tabelas
- `02_PERFIL_COGNITIVO_JURIDICO.txt` - Algoritmos de perfil cognitivo
- `03_CLASSIFICACAO_ERROS_JURIDICOS.txt` - Taxonomia de 28 tipos de erros
- `04_SNAPSHOTS_COGNITIVOS.txt` - Sistema de snapshots temporais
- `05_GOVERNANCA_DADOS_LGPD.txt` - Políticas de governança e LGPD

## 🚨 Troubleshooting

### Problema: Queries lentas em `interacao_questao`

**Solução**: Verificar índices e considerar particionamento

```sql
-- Verificar se índices estão sendo usados
EXPLAIN ANALYZE
SELECT * FROM interacao_questao WHERE user_id = '<uuid>';

-- Se Seq Scan → criar índice missing
-- Se Bitmap Heap Scan → OK
```

### Problema: Disco cheio

**Solução**: Arquivar snapshots antigos e compactar

```sql
-- Identificar tabelas grandes
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Vacuum e reindex
VACUUM FULL ANALYZE interacao_questao;
REINDEX TABLE interacao_questao;
```

### Problema: Conexões esgotadas

**Solução**: Usar connection pooling

```bash
# Instalar PgBouncer
sudo apt-get install pgbouncer

# Configurar (pgbouncer.ini)
[databases]
juris_ia_db = host=localhost port=5432 dbname=juris_ia_db

[pgbouncer]
listen_port = 6432
listen_addr = *
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

## 🔄 Migrations (Futuras)

Estrutura recomendada:

```
database/
├── migrations/
│   ├── 0001_criar_schema_inicial.sql       (schema.sql)
│   ├── 0002_adicionar_campo_x.sql
│   ├── 0003_criar_indice_y.sql
│   └── ...
└── rollbacks/
    ├── 0001_rollback.sql
    ├── 0002_rollback.sql
    └── ...
```

## 📞 Suporte

Para questões sobre o banco de dados:

- **Documentação**: Arquivos `.txt` nesta pasta
- **Issues**: GitHub do projeto
- **DBA**: dba@juris-ia.com.br (se existir)

---

**Versão**: 1.0.0
**Última atualização**: 2025-12-17
**PostgreSQL mínimo**: 14
**PostgreSQL recomendado**: 15+
