# 🔒 CONFIGURAÇÃO DE SEGURANÇA - CHECKLIST PRÉ-DEPLOY

## ⚠️ IMPORTANTE: NÃO COMMITAR SECRETS

Antes de fazer deploy em produção, siga este checklist rigorosamente.

---

## 1. VARIÁVEIS DE AMBIENTE SENSÍVEIS

### Backend (Railway/Heroku)

Configure estas variáveis no painel da plataforma de hosting:

```bash
# JWT Secrets (GERAR NOVOS!)
JWT_SECRET_KEY=<gerar_com_openssl_rand_base64_64>
JWT_REFRESH_SECRET=<gerar_com_openssl_rand_base64_64>

# Database (fornecido automaticamente pelo Railway)
DATABASE_URL=<fornecido_pelo_railway>
POSTGRES_PASSWORD=<fornecido_pelo_railway>

# Chat Server
CHAT_SERVER_URL=https://chat.doutoraia.com
CHAT_API_KEY=<sua_api_key_segura>

# CORS (CRÍTICO!)
ALLOWED_ORIGINS=https://oab.doutoraia.com

# Environment
ENVIRONMENT=production
DEBUG=false
```

### Frontend (Vercel)

```bash
NEXT_PUBLIC_API_URL=https://api.doutoraia.com
# NÃO colocar secrets aqui - tudo que começa com NEXT_PUBLIC_ é exposto ao client!
```

---

## 2. GERAR NOVOS SECRETS

### JWT Secrets:

```bash
# No terminal (Linux/Mac/WSL):
openssl rand -base64 64

# PowerShell (Windows):
-join (1..64 | ForEach-Object { Get-Random -Maximum 256 | ForEach-Object { [char]$_ } })
```

Gerar **DOIS** secrets diferentes:
- Um para `JWT_SECRET_KEY`
- Outro para `JWT_REFRESH_SECRET`

### Chat API Key:

```bash
# Gerar string aleatória segura
openssl rand -hex 32
```

---

## 3. VERIFICAR SE .ENV NÃO ESTÁ NO GIT

```bash
# No diretório do projeto:
git ls-files | grep "\.env$"

# Se aparecer algo, REMOVER IMEDIATAMENTE:
git rm --cached .env
git commit -m "chore: remover .env do versionamento"
```

---

## 4. CORS CONFIGURADO CORRETAMENTE

✅ **Produção:**
```python
ALLOWED_ORIGINS=https://oab.doutoraia.com
```

❌ **NUNCA em produção:**
```python
allow_origins=["*"]  # PERIGO!
```

---

## 5. ROTACIONAR SECRETS APÓS VAZAMENTO

Se secrets foram commitados por engano:

### Passo 1: Remover do histórico
```bash
# ATENÇÃO: Isso reescreve o histórico do git!
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (cuidado!)
git push origin --force --all
```

### Passo 2: Rotacionar TODOS os secrets
- Gerar novos JWT secrets
- Atualizar no Railway/Vercel
- Invalidar sessões antigas (usuários precisarão fazer login novamente)

---

## 6. CHECKLIST FINAL PRÉ-DEPLOY

- [ ] `.env` está no `.gitignore`
- [ ] `.env` NÃO está commitado no git
- [ ] Novos JWT secrets gerados
- [ ] CORS configurado com domínio específico
- [ ] Chat API key configurada no backend
- [ ] DEBUG=false em produção
- [ ] ENVIRONMENT=production
- [ ] Todas as variáveis configuradas no Railway/Vercel
- [ ] Testado localmente com .env.local

---

## 7. BOAS PRÁTICAS CONTÍNUAS

1. **Nunca** commitar `.env`, `.env.local`, `.env.production`
2. **Sempre** usar `.env.example` para documentar variáveis necessárias
3. **Rotacionar** secrets a cada 90 dias
4. **Auditar** logs de acesso regularmente
5. **Manter** secrets diferentes entre dev/staging/production

---

## 8. O QUE FAZER SE SECRETS VAZAREM

### Imediato (1 hora):
1. Rotacionar todos os secrets imediatamente
2. Invalidar sessões ativas
3. Revisar logs de acesso suspeito
4. Notificar equipe

### Curto prazo (24 horas):
1. Investigar escopo do vazamento
2. Determinar se dados de usuários foram comprometidos
3. Preparar comunicado (se necessário)

### Longo prazo (1 semana):
1. Implementar secrets manager (AWS Secrets Manager, HashiCorp Vault)
2. Configurar alertas de segurança
3. Revisar políticas de acesso
4. Treinamento de equipe

---

## 📞 CONTATO DE EMERGÊNCIA

Em caso de incidente de segurança:
- Email: security@doutoraia.com
- WhatsApp: [número de emergência]

**Última atualização:** 2025-12-28
