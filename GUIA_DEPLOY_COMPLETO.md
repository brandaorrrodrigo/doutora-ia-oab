# 🚀 Guia Completo de Deploy - Doutora IA OAB

**Objetivo**: Colocar o sistema completo no ar em produção
**Tempo estimado**: 2-4 horas
**Última atualização**: 28/12/2025

---

## 📋 Checklist Pré-Deploy

Antes de começar, certifique-se de ter:

- [ ] Conta GitHub (para repositórios)
- [ ] Conta Railway OU Render (backend)
- [ ] Conta Vercel (frontend)
- [ ] Conta Stripe (pagamentos)
- [ ] Conta SendGrid (emails)
- [ ] Domínio próprio (opcional, mas recomendado)
- [ ] Cartão de crédito para Stripe/SendGrid

---

## 🎯 Arquitetura de Deploy

```
┌─────────────────┐
│   USUÁRIO       │
└────────┬────────┘
         │
         │ HTTPS
         ▼
┌─────────────────┐
│   VERCEL        │ ← Frontend (Next.js)
│   doutoraia.com │
└────────┬────────┘
         │
         │ API Calls
         ▼
┌─────────────────┐
│   RAILWAY       │ ← Backend (FastAPI)
│ api.doutoraia   │
└────────┬────────┘
         │
         ├─────► PostgreSQL (Railway)
         ├─────► Stripe (Pagamentos)
         └─────► SendGrid (Emails)
```

---

## 📦 PARTE 1: Preparar Repositórios

### 1.1 Criar Repositório no GitHub

```bash
# Backend
cd D:\JURIS_IA_CORE_V1
git init
git add .
git commit -m "Initial commit - backend ready for deploy"
git branch -M main
git remote add origin https://github.com/seu-usuario/doutora-ia-backend.git
git push -u origin main
```

```bash
# Frontend
cd D:\doutora-ia-oab-frontend
git init
git add .
git commit -m "Initial commit - frontend ready for deploy"
git branch -M main
git remote add origin https://github.com/seu-usuario/doutora-ia-frontend.git
git push -u origin main
```

---

## 🗄️ PARTE 2: Deploy do Backend (Railway)

### 2.1 Criar Projeto no Railway

1. Acesse: https://railway.app/
2. Login com GitHub
3. Click "New Project"
4. Selecione "Deploy from GitHub repo"
5. Escolha `doutora-ia-backend`

### 2.2 Adicionar PostgreSQL

1. No projeto Railway, click "+ New"
2. Selecione "Database" → "PostgreSQL"
3. Aguarde provisionamento (1-2 minutos)
4. Copie a `DATABASE_URL` (Settings → Connect)

### 2.3 Configurar Variáveis de Ambiente

No Railway, vá em Settings → Variables e adicione:

```env
# Database (já estará configurada automaticamente)
DATABASE_URL=postgresql://...

# JWT
JWT_SECRET_KEY=<gerar com: python -c "import secrets; print(secrets.token_urlsafe(64))">
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# SendGrid
SENDGRID_API_KEY=SG.***
EMAIL_FROM=noreply@seudominio.com
EMAIL_FROM_NAME=Doutora IA OAB

# Stripe
STRIPE_API_KEY=sk_live_***
STRIPE_WEBHOOK_SECRET=whsec_***
STRIPE_PRICE_ID_PREMIUM=price_***
STRIPE_PRICE_ID_PRO=price_***

# URLs
FRONTEND_URL=https://seudominio.com
CHAT_API_URL=https://chat.seudominio.com

# Environment
ENVIRONMENT=production
PORT=8000
```

### 2.4 Executar Migrations

```bash
# Conectar ao banco Railway via CLI
railway login
railway link
railway run python scripts/run_migrations.py
```

**OU** usar psql direto:

```bash
psql postgresql://user:pass@host:5432/database -f database/migrations/001_initial_schema.sql
psql postgresql://user:pass@host:5432/database -f database/migrations/002_...sql
# ... executar todas as migrations em ordem
```

### 2.5 Verificar Deploy

1. Aguarde build completar (5-10 minutos)
2. Acesse a URL fornecida pelo Railway
3. Teste: `https://your-app.railway.app/docs`
4. Deve ver documentação Swagger da API

### 2.6 Configurar Domínio Personalizado (Opcional)

1. Em Settings → Domains
2. Click "Generate Domain" ou "Custom Domain"
3. Configurar DNS:
   - Tipo: CNAME
   - Nome: api
   - Valor: your-app.railway.app

---

## 🎨 PARTE 3: Deploy do Frontend (Vercel)

### 3.1 Importar Projeto

1. Acesse: https://vercel.com/
2. Login com GitHub
3. Click "Add New" → "Project"
4. Selecione `doutora-ia-frontend`
5. Framework: Next.js (detectado automaticamente)

### 3.2 Configurar Variáveis de Ambiente

Em Settings → Environment Variables:

```env
NEXT_PUBLIC_API_URL=https://api.seudominio.com
NEXT_PUBLIC_CHAT_URL=https://chat.seudominio.com
NEXT_PUBLIC_ENVIRONMENT=production
```

### 3.3 Deploy

1. Click "Deploy"
2. Aguarde build (3-5 minutos)
3. Acesse a URL fornecida: `https://your-app.vercel.app`

### 3.4 Configurar Domínio Personalizado

1. Em Settings → Domains
2. Add "seudominio.com"
3. Configurar DNS no seu provedor:
   - Tipo: A
   - Nome: @
   - Valor: 76.76.21.21
   - Tipo: CNAME
   - Nome: www
   - Valor: cname.vercel-dns.com

---

## 💳 PARTE 4: Configurar Stripe Produção

### 4.1 Ativar Modo Live

1. Acesse: https://dashboard.stripe.com/
2. Mude de "Test" para "Live" (switch no canto superior direito)
3. Complete o onboarding (informações da empresa, conta bancária)

### 4.2 Criar Produtos

1. Products → Create Product
2. **Plano Premium**:
   - Nome: "Plano Premium - Doutora IA OAB"
   - Preço: R$ 49,90/mês
   - Billing period: Monthly
   - Copiar `price_id`
3. **Plano Pro**:
   - Nome: "Plano Pro - Doutora IA OAB"
   - Preço: R$ 99,90/mês
   - Copiar `price_id`

### 4.3 Configurar Webhook

1. Developers → Webhooks → Add endpoint
2. URL: `https://api.seudominio.com/pagamento/webhook`
3. Events to send:
   - [x] checkout.session.completed
   - [x] customer.subscription.created
   - [x] customer.subscription.updated
   - [x] customer.subscription.deleted
   - [x] invoice.payment_succeeded
   - [x] invoice.payment_failed
4. Copiar `Signing secret` (whsec_***)

### 4.4 Atualizar Env Variables

Atualizar no Railway:
```env
STRIPE_API_KEY=sk_live_***
STRIPE_WEBHOOK_SECRET=whsec_***
STRIPE_PRICE_ID_PREMIUM=price_***
STRIPE_PRICE_ID_PRO=price_***
```

### 4.5 Testar Pagamento

1. Use cartão de teste: `4242 4242 4242 4242`
2. Verificar webhook recebido (Stripe Dashboard → Webhooks)
3. Confirmar assinatura criada no banco de dados

---

## 📧 PARTE 5: Configurar SendGrid

### 5.1 Criar Conta e API Key

1. Acesse: https://signup.sendgrid.com/
2. Complete verificação
3. Settings → API Keys → Create API Key
4. Permissões: Full Access
5. Copiar chave (SG.***)

### 5.2 Verificar Domínio (Sender Authentication)

1. Settings → Sender Authentication
2. Authenticate Your Domain
3. Escolher provedor DNS
4. Adicionar registros DNS fornecidos
5. Aguardar verificação (até 48h, geralmente minutos)

### 5.3 Criar Templates (Opcional)

1. Email API → Dynamic Templates
2. Criar templates para:
   - Boas-vindas
   - Recuperação de senha
   - Lembrete de estudos

### 5.4 Atualizar Env

```env
SENDGRID_API_KEY=SG.***
EMAIL_FROM=noreply@seudominio.com
EMAIL_FROM_NAME=Doutora IA OAB
```

---

## 🔒 PARTE 6: SSL e Segurança

### 6.1 Vercel (Frontend)

✅ SSL automático - nada a fazer!

### 6.2 Railway (Backend)

✅ SSL automático - nada a fazer!

### 6.3 Configurações de Segurança

1. **CORS**: Atualizar `api/api_server.py`
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://seudominio.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **Headers de Segurança**: Já configurados no `vercel.json`

3. **Rate Limiting**: Implementar se necessário

---

## 📊 PARTE 7: Monitoramento

### 7.1 Railway Logs

```bash
# Via CLI
railway logs

# Ou no dashboard: View Logs
```

### 7.2 Vercel Analytics

1. Ativar em Project Settings → Analytics
2. Visualizar tráfego, performance, erros

### 7.3 Sentry (Opcional - Error Tracking)

1. Criar conta: https://sentry.io/
2. Criar projeto Python (backend) e JavaScript (frontend)
3. Adicionar DSN às env variables
4. Instalar SDK:
   ```bash
   pip install sentry-sdk
   ```

5. Configurar em `api/api_server.py`:
   ```python
   import sentry_sdk
   sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))
   ```

---

## 🔄 PARTE 8: CI/CD Automático

### 8.1 Vercel (já configurado)

✅ Deploy automático a cada push no main

### 8.2 Railway (já configurado)

✅ Deploy automático a cada push no main

### 8.3 Branch Protection

1. GitHub → Settings → Branches
2. Add rule para `main`:
   - [x] Require pull request reviews
   - [x] Require status checks to pass
   - [x] Require branches to be up to date

---

## 🧪 PARTE 9: Testes em Produção

### 9.1 Smoke Tests

```bash
# Health check
curl https://api.seudominio.com/health

# API docs
open https://api.seudominio.com/docs

# Frontend
open https://seudominio.com
```

### 9.2 Fluxo Completo

1. ✅ Cadastro de usuário
2. ✅ Login
3. ✅ Ver planos
4. ✅ Escolher Premium (cartão de teste)
5. ✅ Verificar assinatura ativa
6. ✅ Iniciar sessão de estudo
7. ✅ Responder questões
8. ✅ Verificar limites funcionando
9. ✅ Chat com IA (se implementado)
10. ✅ Prática de peças (se implementado)

### 9.3 Testar Webhooks

1. Stripe Dashboard → Webhooks
2. Verificar eventos sendo recebidos
3. Testar cancelamento de assinatura
4. Verificar upgrade de plano

---

## 📈 PARTE 10: Go Live!

### 10.1 Checklist Final

- [ ] Backend rodando sem erros
- [ ] Frontend carregando corretamente
- [ ] SSL ativo em ambos
- [ ] Pagamentos funcionando
- [ ] Emails sendo enviados
- [ ] Webhooks Stripe funcionando
- [ ] Limites por plano aplicados
- [ ] Logs e monitoramento ativos
- [ ] Backup do banco configurado

### 10.2 Comunicação

- [ ] Anunciar lançamento nas redes sociais
- [ ] Email para beta testers
- [ ] Post no blog/site
- [ ] Google Analytics configurado

### 10.3 Suporte

- [ ] Configurar email de suporte
- [ ] Criar base de conhecimento/FAQ
- [ ] Configurar chatbot (opcional)

---

## 🔧 PARTE 11: Manutenção

### 11.1 Backup Diário

```bash
# Script de backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Upload para S3 (exemplo)
aws s3 cp backup_$(date +%Y%m%d).sql s3://juris-ia-backups/
```

### 11.2 Monitorar Métricas

- Uptime (usar UptimeRobot ou similar)
- Tempo de resposta da API
- Taxa de conversão de pagamentos
- Erros 500/400
- Uso de recursos (CPU/RAM/Disco)

### 11.3 Updates

```bash
# Atualizar dependências
pip list --outdated
npm outdated

# Criar branch de update
git checkout -b update-dependencies
```

---

## 🆘 Troubleshooting

### Problema: "500 Internal Server Error"

**Solução**:
1. Verificar logs: `railway logs`
2. Verificar variáveis de ambiente
3. Testar migrations: `railway run python scripts/run_migrations.py`

### Problema: "Webhook failed"

**Solução**:
1. Verificar `STRIPE_WEBHOOK_SECRET`
2. Testar endpoint: `curl -X POST https://api.seudominio.com/pagamento/webhook`
3. Verificar eventos no Stripe Dashboard

### Problema: "CORS error"

**Solução**:
1. Verificar `allow_origins` em `api_server.py`
2. Adicionar domínio correto da Vercel

### Problema: "Database connection failed"

**Solução**:
1. Verificar `DATABASE_URL`
2. Testar conexão: `railway run python -c "from database.connection import engine; print(engine)"`
3. Verificar se banco está rodando no Railway

---

## 📞 Suporte

- **Railway**: https://help.railway.app/
- **Vercel**: https://vercel.com/support
- **Stripe**: https://support.stripe.com/
- **SendGrid**: https://support.sendgrid.com/

---

## 🎉 Conclusão

Parabéns! Se você chegou até aqui, seu sistema está no ar em produção!

**Próximos passos**:
- Monitorar métricas de uso
- Coletar feedback de usuários
- Iterar baseado em dados
- Adicionar novos recursos

**Boa sorte com o lançamento!** 🚀
