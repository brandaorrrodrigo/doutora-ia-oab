# 🚀 DEPLOY DOUTORA IA OAB - oab.doutoraia.com

## 📋 RESUMO DO DEPLOY

Vamos colocar o Doutora IA OAB no ar em **oab.doutoraia.com** usando:

- **Backend:** Railway (FastAPI + Python)
- **Banco de Dados:** Railway PostgreSQL
- **Cache:** Railway Redis
- **IA:** Chat Server Multi-Tenant (Ollama local + Cloudflare Tunnel)
- **Domínio:** oab.doutoraia.com

---

## ✅ STATUS ATUAL

- ✅ Projeto localizado: `D:\JURIS_IA_CORE_V1`
- ✅ Integração com chat server criada (`chat_server_client.py`)
- ✅ .env atualizado com API key
- ✅ Conexão com chat server testada
- ⏳ Próximo: Cloudflare Tunnel + Deploy

---

## 🎯 ARQUITETURA

```
┌─────────────────────────────┐
│      USUÁRIOS               │
│  oab.doutoraia.com          │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│   RAILWAY                   │
│  ┌────────────────────┐     │
│  │ FastAPI Backend    │     │
│  │ (Python)           │     │
│  └─────┬──────────────┘     │
│        │                     │
│  ┌─────┴──────┬──────────┐  │
│  │ PostgreSQL │ Redis    │  │
│  └────────────┴──────────┘  │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  CLOUDFLARE TUNNEL          │
│  chat.doutoraia.com         │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  CHAT SERVER (SEU PC)       │
│  http://localhost:3001      │
│  ┌───────────────────────┐  │
│  │ Multi-Tenant Server   │  │
│  └──────┬────────────────┘  │
└─────────┼────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│     OLLAMA (LOCAL)          │
│  llama3.1:8b                │
└─────────────────────────────┘
```

---

## 🚀 PASSO A PASSO - DEPLOY COMPLETO

### FASE 1: CLOUDFLARE TUNNEL (15-30 min)

#### 1.1 Instalar Cloudflared

**Se ainda não tem:**
```bash
# Windows:
winget install --id Cloudflare.cloudflared

# Ou baixe de:
# https://github.com/cloudflare/cloudflared/releases/latest
```

#### 1.2 Criar Tunnel Permanente

```bash
# 1. Login
cloudflared tunnel login

# 2. Criar tunnel
cloudflared tunnel create doutoraia-chat

# 3. Anotar o TUNNEL_ID que aparecer
```

#### 1.3 Configurar DNS

**Opção A - Se você tem domínio doutoraia.com:**
```bash
cloudflared tunnel route dns doutoraia-chat chat.doutoraia.com
```

**Opção B - Sem domínio (usar URL do Cloudflare):**
```bash
# O tunnel vai gerar uma URL tipo:
# https://<TUNNEL_ID>.cfargotunnel.com
```

#### 1.4 Criar Arquivo de Configuração

Criar: `C:\Users\SEU_USUARIO\.cloudflared\config.yml`

```yaml
tunnel: <SEU_TUNNEL_ID>
credentials-file: C:\Users\SEU_USUARIO\.cloudflared\<SEU_TUNNEL_ID>.json

ingress:
  # Chat Server
  - hostname: chat.doutoraia.com
    service: http://localhost:3001

  # Fallback
  - service: http_status:404
```

#### 1.5 Iniciar Tunnel

```bash
cloudflared tunnel run doutoraia-chat
```

Deve mostrar:
```
Your tunnel is now online!
https://chat.doutoraia.com
```

#### 1.6 Testar

```bash
curl https://chat.doutoraia.com/health
```

✅ Deve retornar status do chat server!

---

### FASE 2: ATUALIZAR .ENV PARA PRODUÇÃO (5 min)

Editar `D:\JURIS_IA_CORE_V1\.env`:

```bash
# Comentar a URL local:
# CHAT_SERVER_URL=http://localhost:3001

# Descomentar a URL de produção:
CHAT_SERVER_URL=https://chat.doutoraia.com
```

**Testar novamente:**
```bash
cd D:\JURIS_IA_CORE_V1
python chat_server_client.py
```

Deve conectar via HTTPS agora! 🎉

---

### FASE 3: PREPARAR PARA RAILWAY (10 min)

#### 3.1 Criar requirements.txt para Railway

Criar `D:\JURIS_IA_CORE_V1\requirements-railway.txt`:

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
psycopg2-binary==2.9.9
redis==5.0.1
requests==2.31.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
```

#### 3.2 Criar Procfile

Criar `D:\JURIS_IA_CORE_V1\Procfile`:

```
web: uvicorn api.api_server:app --host 0.0.0.0 --port $PORT
```

#### 3.3 Criar runtime.txt

Criar `D:\JURIS_IA_CORE_V1\runtime.txt`:

```
python-3.11
```

#### 3.4 Criar .gitignore

Criar/atualizar `D:\JURIS_IA_CORE_V1\.gitignore`:

```
__pycache__/
*.py[cod]
*$py.class
.env
.env.local
venv/
*.log
.DS_Store
postgres_data/
redis_data/
logs/
*.db
.dockerignore
docker-compose.yml
Dockerfile.backend
```

---

### FASE 4: GITHUB (10 min)

#### 4.1 Inicializar Git

```bash
cd D:\JURIS_IA_CORE_V1

git init
git add .
git commit -m "Initial commit - Doutora IA OAB"
```

#### 4.2 Criar Repositório GitHub

**Opção A - Usando GitHub CLI (gh):**
```bash
gh repo create doutora-ia-oab --public --source=. --push
```

**Opção B - Manual:**
1. Vá em https://github.com/new
2. Nome: `doutora-ia-oab`
3. Público ou Privado
4. Criar

Depois:
```bash
git remote add origin https://github.com/SEU_USUARIO/doutora-ia-oab.git
git branch -M main
git push -u origin main
```

---

### FASE 5: RAILWAY DEPLOY (20 min)

#### 5.1 Criar Projeto no Railway

1. Acesse: https://railway.app
2. Clique em **"New Project"**
3. Selecione **"Deploy from GitHub repo"**
4. Autorize o GitHub (se necessário)
5. Selecione o repositório **doutora-ia-oab**
6. Clique em **"Deploy Now"**

#### 5.2 Adicionar PostgreSQL

1. No projeto Railway, clique em **"New"**
2. Selecione **"Database"** → **"PostgreSQL"**
3. Railway cria automaticamente

#### 5.3 Adicionar Redis

1. Clique em **"New"** novamente
2. Selecione **"Database"** → **"Redis"**
3. Railway cria automaticamente

#### 5.4 Configurar Variáveis de Ambiente

No serviço da API, vá em **"Variables"** e adicione:

```env
# Node Environment
NODE_ENV=production
ENVIRONMENT=production

# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT
API_WORKERS=2

# Database (Railway fornece automaticamente)
DATABASE_URL=${{Postgres.DATABASE_URL}}
POSTGRES_PASSWORD=${{Postgres.POSTGRES_PASSWORD}}

# Redis (Railway fornece automaticamente)
REDIS_URL=${{Redis.REDIS_URL}}

# Chat Server Multi-Tenant
CHAT_SERVER_URL=https://chat.doutoraia.com
CHAT_API_KEY=doutoraia-oab-2025-secret-key-ultra-secure

# JWT Secrets (copiar do .env local)
JWT_SECRET_KEY=Pv2hq_89mtG-wdXLYPrFpi6eOUPGbiSyLNcWcFcNi0JfhLz8tKCFcKNrQizFRDW_QYjTo22OHx2MoEIn_aBMEA
JWT_REFRESH_SECRET=-mcPHH_AqeFp8Y-rxlfKSHMOfwlE6Ga3kDA9f4E6f7EFGd0DWRASsPtYewkqpkQQ8fTtdNWs11fKDjcSXDL0EA
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Feature Flags
MODO_OAB_ENABLED=true
MODO_PROFISSIONAL_ENABLED=false
PIECE_ENGINE_ENABLED=false

# Limits
SESSOES_POR_DIA=3
QUESTOES_POR_SESSAO=20
PECAS_POR_SEMANA=0
MAX_USUARIOS_CADASTRADOS=50

# Logging
LOG_LEVEL=INFO

# Pricing
PLANO_FREE_PRECO_MENSAL=0.00
PLANO_OAB_MENSAL_PRECO_MENSAL=49.90
PLANO_OAB_SEMESTRAL_PRECO_SEMESTRAL=247.00
PRICING_MOEDA=BRL

# PGAdmin (opcional, para debug)
PGADMIN_PASSWORD=${{Postgres.POSTGRES_PASSWORD}}
```

⚠️ **IMPORTANTE:** Troque os JWT secrets por novos em produção!

#### 5.5 Aguardar Deploy

Railway vai:
1. Detectar Python
2. Instalar dependências
3. Executar o Procfile
4. Expor a aplicação

---

### FASE 6: DOMÍNIO CUSTOMIZADO (10 min)

#### 6.1 No Railway

1. Acesse o serviço da API
2. Vá em **"Settings"** → **"Domains"**
3. Clique em **"Custom Domain"**
4. Adicione: `oab.doutoraia.com`
5. Railway vai mostrar um CNAME

#### 6.2 No Cloudflare (DNS)

1. Acesse https://dash.cloudflare.com
2. Selecione o domínio **doutoraia.com**
3. Vá em **DNS** → **Records**
4. Adicione registro CNAME:

```
Type: CNAME
Name: oab
Target: <valor-fornecido-pelo-railway>.up.railway.app
Proxy: On (ícone laranja)
```

5. Salvar

#### 6.3 Aguardar Propagação (2-5 min)

Teste:
```bash
curl https://oab.doutoraia.com/health
```

✅ Deve funcionar!

---

## 🧪 TESTE COMPLETO

### 1. Chat Server

```bash
curl https://chat.doutoraia.com/health
```

Deve retornar:
```json
{
  "status": "online",
  "service": "multi-tenant-chat-server",
  "projects": 7
}
```

### 2. API Backend

```bash
curl https://oab.doutoraia.com/health
```

### 3. Teste de Chat via API

```bash
curl -X POST https://chat.doutoraia.com/api/chat \
  -H "X-API-Key: doutoraia-oab-2025-secret-key-ultra-secure" \
  -H "Content-Type: application/json" \
  -d '{"userName":"Teste","message":"O que é LGPD?"}'
```

Deve retornar resposta da IA! 🎉

---

## 📊 MONITORAMENTO

### Dashboard do Chat Server

```
https://chat.doutoraia.com/dashboard
```

Mostra:
- Requisições do Doutora IA OAB
- Última requisição
- Erros (se houver)
- Tokens usados

### Logs do Railway

1. Acesse o projeto no Railway
2. Clique no serviço
3. Veja logs em tempo real

---

## ✅ CHECKLIST DE DEPLOY

### Cloudflare Tunnel:
- [ ] Cloudflared instalado
- [ ] Tunnel criado
- [ ] DNS configurado (chat.doutoraia.com)
- [ ] Tunnel rodando
- [ ] Testado e funcionando

### Projeto:
- [ ] .env atualizado para produção
- [ ] Chat server client testado
- [ ] requirements-railway.txt criado
- [ ] Procfile criado
- [ ] .gitignore configurado

### GitHub:
- [ ] Repositório criado
- [ ] Código commitado
- [ ] Push para origin main

### Railway:
- [ ] Projeto criado
- [ ] PostgreSQL adicionado
- [ ] Redis adicionado
- [ ] Variáveis de ambiente configuradas
- [ ] Deploy bem-sucedido
- [ ] Logs verificados

### Domínio:
- [ ] Custom domain adicionado no Railway
- [ ] CNAME configurado no Cloudflare
- [ ] DNS propagado
- [ ] HTTPS funcionando

### Testes:
- [ ] Chat server respondendo
- [ ] API backend respondendo
- [ ] Chat via API funcionando
- [ ] Dashboard acessível

---

## 💰 CUSTOS ESTIMADOS

| Item | Custo |
|------|-------|
| Cloudflare Tunnel | Grátis |
| Chat Server (seu PC) | Grátis |
| Railway - Backend | $5/mês |
| Railway - PostgreSQL | Incluído |
| Railway - Redis | Incluído |
| **TOTAL** | **$5/mês** |

**Muito mais barato que APIs pagas!** 💰

---

## 🆘 PROBLEMAS COMUNS

### 1. Chat server não conecta

✅ Verifique se o tunnel está rodando:
```bash
cloudflared tunnel info doutoraia-chat
```

✅ Teste o health check:
```bash
curl https://chat.doutoraia.com/health
```

### 2. Deploy falhou no Railway

✅ Verifique os logs no Railway
✅ Confirme que todos os arquivos foram criados (Procfile, requirements-railway.txt)
✅ Verifique variáveis de ambiente

### 3. Domínio não resolve

✅ Aguarde propagação DNS (até 5 min)
✅ Verifique CNAME no Cloudflare
✅ Teste com `nslookup oab.doutoraia.com`

### 4. API retorna 500

✅ Veja os logs no Railway
✅ Verifique DATABASE_URL
✅ Confirme CHAT_SERVER_URL

---

## 🎉 RESULTADO FINAL

Quando tudo estiver pronto:

✅ **Frontend:** https://oab.doutoraia.com
✅ **Chat Server:** https://chat.doutoraia.com
✅ **Dashboard:** https://chat.doutoraia.com/dashboard
✅ **IA:** llama3.1:8b via Ollama local
✅ **HTTPS:** Ativo em tudo
✅ **Custo:** $5/mês

**Doutora IA OAB no ar!** 🚀⚖️🎉

---

**Última atualização:** 2025-12-23
**Status:** Pronto para deploy!
