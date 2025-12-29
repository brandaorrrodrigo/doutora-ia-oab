# Backup Automatizado e Disaster Recovery

**Data**: 28/12/2025
**Objetivo**: Garantir recuperação de dados em caso de desastre

---

## 📦 Estratégia de Backup

### 1. Backup do Banco de Dados (PostgreSQL)

#### 1.1. Backup Automatizado Diário

**Script**: `scripts/backup_database.sh`

```bash
#!/bin/bash
# Backup automático do PostgreSQL

# Configurações
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="juris_ia"
RETENTION_DAYS=30

# Criar diretório se não existir
mkdir -p $BACKUP_DIR

# Fazer backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"

# Comprimir
gzip "$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql"

# Deletar backups antigos (> 30 dias)
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Upload para S3 (opcional)
if [ -n "$AWS_S3_BUCKET" ]; then
  aws s3 cp "$BACKUP_DIR/backup_${DB_NAME}_${DATE}.sql.gz" \
    "s3://$AWS_S3_BUCKET/backups/postgresql/"
fi

echo "Backup completed: backup_${DB_NAME}_${DATE}.sql.gz"
```

**Cron Job** (Railway/Render):

```bash
# Executar diariamente às 3h da manhã
0 3 * * * /app/scripts/backup_database.sh
```

**GitHub Actions** (alternativa):

```yaml
# .github/workflows/database-backup.yml
name: Database Backup

on:
  schedule:
    - cron: '0 3 * * *'  # Diariamente às 3h UTC
  workflow_dispatch:  # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install PostgreSQL Client
        run: sudo apt-get install -y postgresql-client

      - name: Create Backup
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          DATE=$(date +%Y%m%d_%H%M%S)
          pg_dump $DATABASE_URL | gzip > backup_$DATE.sql.gz

      - name: Upload to S3
        uses: jakejarvis/s3-sync-action@v0.5.1
        with:
          args: --follow-symlinks
        env:
          AWS_S3_BUCKET: ${{ secrets.AWS_S3_BUCKET }}
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          SOURCE_DIR: 'backup_*.sql.gz'
          DEST_DIR: 'backups/postgresql/'
```

#### 1.2. Backup Incremental (Point-in-Time Recovery)

**Railway/Render**: Ativam automaticamente backups contínuos
- **Retenção**: 7-30 dias (dependendo do plano)
- **Recovery Point Objective (RPO)**: < 5 minutos
- **Recovery Time Objective (RTO)**: < 30 minutos

**Verificar Backups**:
```bash
# Railway
railway run pg:info

# Render
# Dashboard → Database → Backups
```

---

### 2. Backup de Arquivos Estáticos

#### 2.1. Uploads de Usuários

**Localização**: `static/uploads/perfil/`

**Script**: `scripts/backup_uploads.sh`

```bash
#!/bin/bash
# Backup de uploads

BACKUP_DIR="/backups/uploads"
DATE=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="/app/static/uploads"

# Criar backup
tar -czf "$BACKUP_DIR/uploads_${DATE}.tar.gz" $SOURCE_DIR

# Upload para S3
aws s3 cp "$BACKUP_DIR/uploads_${DATE}.tar.gz" \
  "s3://$AWS_S3_BUCKET/backups/uploads/"

# Deletar backups locais antigos
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

**Alternativa**: Usar S3 diretamente para uploads (recomendado)

```python
# services/upload_service.py
import boto3

s3 = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def upload_to_s3(file, filename):
    s3.upload_fileobj(
        file,
        AWS_S3_BUCKET,
        f'uploads/perfil/{filename}',
        ExtraArgs={'ACL': 'private'}
    )
    return f"https://{AWS_S3_BUCKET}.s3.amazonaws.com/uploads/perfil/{filename}"
```

---

### 3. Backup de Código

#### 3.1. Git Repository

- ✅ Código versionado no GitHub
- ✅ Branches protegidas (main)
- ✅ Tags de release
- [ ] Mirror repository (GitLab/Bitbucket) - opcional

**Proteção de Branches**:
```
GitHub → Settings → Branches → Branch protection rules

[x] Require pull request reviews (1)
[x] Require status checks to pass
[x] Require branches to be up to date
[x] Include administrators
```

#### 3.2. Environment Variables

**Backup Manual** (a cada mudança):

```bash
# Exportar secrets do Railway
railway variables > .env.backup.$(date +%Y%m%d)

# Criptografar
gpg -c .env.backup.YYYYMMDD

# Armazenar em local seguro (1Password, AWS Secrets Manager)
```

---

### 4. Backup de Configurações

#### 4.1. Configurações de Infraestrutura

**Armazenar em Git**:
- `railway.json`
- `render.yaml`
- `vercel.json`
- `docker-compose.yml`
- `Dockerfile`
- `.env.example`

#### 4.2. Configurações de Terceiros

**Documentar**:
- SendGrid templates (export JSON)
- Stripe products/prices (IDs em .env)
- Google Analytics views
- Sentry projects

---

## 🚨 Disaster Recovery Plan

### Cenário 1: Perda de Banco de Dados

**Impacto**: CRÍTICO
**RTO**: 30 minutos
**RPO**: 5 minutos

**Procedimento**:

```bash
# 1. Provisionar novo banco de dados
railway add postgresql

# 2. Restaurar do backup mais recente
gunzip -c backup_YYYYMMDD_HHMMSS.sql.gz | psql $NEW_DATABASE_URL

# 3. Verificar integridade
psql $NEW_DATABASE_URL
\dt  # Listar tabelas
SELECT COUNT(*) FROM usuarios;
SELECT COUNT(*) FROM questoes;

# 4. Atualizar DATABASE_URL no Railway
railway variables set DATABASE_URL=$NEW_DATABASE_URL

# 5. Reiniciar aplicação
railway up --detach
```

**Validação**:
- [ ] Aplicação inicia sem erros
- [ ] Login funciona
- [ ] Dados de usuários visíveis
- [ ] Questões carregam

**Tempo Estimado**: 15-30 minutos

---

### Cenário 2: Perda de Backend (Railway)

**Impacto**: CRÍTICO
**RTO**: 1 hora
**RPO**: 0 (código em Git)

**Procedimento**:

```bash
# 1. Criar novo projeto Railway
railway init

# 2. Adicionar PostgreSQL
railway add postgresql

# 3. Restaurar banco de dados
# (seguir Cenário 1)

# 4. Configurar variáveis de ambiente
railway variables set JWT_SECRET_KEY=...
railway variables set STRIPE_SECRET_KEY=...
# (todas as outras do .env.production.example)

# 5. Deploy do código
git push railway main

# 6. Atualizar DNS (se domínio custom)
# Apontar api.doutoraia.com para novo endpoint Railway
```

**Validação**:
- [ ] Health check responde (GET /health)
- [ ] Login funciona
- [ ] API endpoints respondem
- [ ] Webhooks Stripe configurados

**Tempo Estimado**: 30-60 minutos

---

### Cenário 3: Perda de Frontend (Vercel)

**Impacto**: ALTO
**RTO**: 30 minutos
**RPO**: 0 (código em Git)

**Procedimento**:

```bash
# 1. Criar novo projeto Vercel
vercel

# 2. Configurar variáveis de ambiente
vercel env add NEXT_PUBLIC_API_URL production
vercel env add NEXT_PUBLIC_CHAT_URL production
# (todas as outras)

# 3. Deploy
vercel --prod

# 4. Atualizar DNS
# Apontar doutoraia.com para novo deployment Vercel
```

**Validação**:
- [ ] Página inicial carrega
- [ ] Login funciona
- [ ] Dashboard acessível
- [ ] Imagens e assets carregam

**Tempo Estimado**: 15-30 minutos

---

### Cenário 4: Comprometimento de Secrets

**Impacto**: CRÍTICO
**RTO**: 2 horas
**RPO**: N/A

**Procedimento**:

```bash
# 1. Rotacionar imediatamente:

# JWT Secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
railway variables set JWT_SECRET_KEY=<novo-secret>

# Stripe (se comprometido)
# - Criar novas keys no Stripe Dashboard
# - Deletar keys antigas
railway variables set STRIPE_SECRET_KEY=<novo-secret>

# SendGrid
# - Gerar nova API key no SendGrid
railway variables set SENDGRID_API_KEY=<novo-secret>

# Database Password (se comprometido)
# - Criar novo usuário no PostgreSQL
# - Atualizar DATABASE_URL

# 2. Invalidar todos os tokens JWT
# (adicionar data de invalidação na DB)

# 3. Notificar usuários
# (se dados de usuários foram comprometidos - LGPD)

# 4. Audit logs
# - Verificar acessos suspeitos
# - Identificar escopo do comprometimento

# 5. Post-mortem
# - Documentar incidente
# - Implementar medidas preventivas
```

**Tempo Estimado**: 1-4 horas

---

### Cenário 5: DDoS / Rate Limit Overwhelmed

**Impacto**: MÉDIO
**RTO**: 1 hora
**RPO**: N/A

**Procedimento**:

```bash
# 1. Identificar origem do ataque
# - Verificar logs (Railway/Render)
# - Identificar IPs maliciosos

# 2. Ativar Cloudflare (se não ativo)
# - DNS proxy habilitado
# - Under Attack mode

# 3. Aumentar rate limits temporariamente
# (ou diminuir se for ataque)

# 4. Escalar recursos
railway scale --replicas 3

# 5. Bloquear IPs maliciosos
# (Cloudflare Firewall Rules ou rate limiter)
```

---

## 🧪 Teste de Recovery (DR Drill)

### Mensal: Teste de Backup

```bash
# 1. Fazer backup manual
./scripts/backup_database.sh

# 2. Criar DB temporário
createdb juris_ia_test

# 3. Restaurar backup
gunzip -c backup_latest.sql.gz | psql juris_ia_test

# 4. Validar dados
psql juris_ia_test
SELECT COUNT(*) FROM usuarios;

# 5. Deletar DB temporário
dropdb juris_ia_test
```

**Documentar**:
- Data do teste
- Tempo de restauração
- Problemas encontrados
- Ações corretivas

### Trimestral: DR Drill Completo

Simular perda completa do ambiente de produção:
1. Provisionar novos serviços (Railway/Vercel)
2. Restaurar backups
3. Configurar DNS temporário
4. Validar funcionalidade
5. Medir RTO real

**Meta**: RTO < 2 horas

---

## 📊 Monitoramento de Backups

### Alertas Configurar

- [ ] Backup falhou (erro no script)
- [ ] Backup > 24h sem executar
- [ ] Espaço de armazenamento < 10%
- [ ] Restore test falhou

### Dashboard

**Métricas**:
- Último backup: `2025-12-28 03:00:00`
- Tamanho: `450 MB`
- Status: ✅ Sucesso
- Próximo backup: `2025-12-29 03:00:00`
- Retenção: `30 dias (30 backups)`

---

## 📋 Checklist Pré-Lançamento

### Backups
- [ ] Backup automático de DB configurado (diário)
- [ ] Teste de restore realizado com sucesso
- [ ] Backup de uploads configurado (se aplicável)
- [ ] Environment variables backup criado e criptografado
- [ ] S3 bucket configurado (ou alternativa)
- [ ] Retention policy definida (30 dias)

### Disaster Recovery
- [ ] DR plan documentado
- [ ] Procedimentos de recovery testados
- [ ] RTO/RPO definidos
- [ ] Contatos de emergência documentados
- [ ] Post-mortem template criado

### Monitoramento
- [ ] Alertas de backup configurados
- [ ] UptimeRobot monitorando uptime
- [ ] Sentry capturando erros
- [ ] Logs sendo armazenados (Railway/Render)

---

## 🔐 Compliance

### LGPD
- [ ] Backup de dados pessoais criptografado
- [ ] Acesso a backups restrito
- [ ] Data retention policy aplicada (deletar após 30 dias)
- [ ] Procedimento de data breach notification

### PCI DSS (Stripe)
- ✅ Não armazenamos dados de cartão
- ✅ Stripe gerencia compliance

---

**Próximo**: Criar checklist final de lançamento e documentação do Dia 5!
