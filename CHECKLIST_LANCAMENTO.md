# Checklist Final de Lançamento 🚀

**Data**: 28/12/2025
**Sistema**: Doutora IA OAB
**Objetivo**: Verificação completa antes do go-live

---

## 🎯 Status Geral

**Dias Completados**: 5/5
**Progresso**: 100%
**Status**: PRONTO PARA LANÇAR ✅

---

## 📋 Checklist por Categoria

### 🔧 1. Infraestrutura e Deploy (Dia 3)

#### Backend (Railway/Render)
- [ ] Conta criada e verificada
- [ ] PostgreSQL provisionado
- [ ] Variáveis de ambiente configuradas (30+ vars)
- [ ] Dockerfile testado localmente
- [ ] Deploy realizado com sucesso
- [ ] Health check respondendo (GET /health → 200 OK)
- [ ] Migrations aplicadas (15/15)
- [ ] Logs sem erros críticos
- [ ] Domínio custom configurado (api.doutoraia.com) - opcional
- [ ] SSL/TLS ativo (HTTPS)

#### Frontend (Vercel)
- [ ] Conta criada e verificada
- [ ] Repositório conectado
- [ ] Variáveis de ambiente configuradas
- [ ] Build realizado com sucesso
- [ ] Deploy em produção
- [ ] Página inicial carregando
- [ ] Domínio custom configurado (doutoraia.com) - opcional
- [ ] SSL/TLS ativo (HTTPS)

#### Database
- [ ] PostgreSQL em produção
- [ ] Migrations aplicadas
- [ ] Dados consolidados (8,261 questões)
- [ ] Índices criados
- [ ] Connection pool configurado (20-50 connections)
- [ ] Backup automatizado ativo

---

### 💳 2. Pagamentos e Monetização (Dia 2)

#### Stripe
- [ ] Conta ativada (modo live)
- [ ] Produtos criados (Gratuito, Premium R$ 49,90, Pro R$ 99,90)
- [ ] Price IDs configurados nas env vars
- [ ] Webhooks configurados
  - [ ] URL: https://api.doutoraia.com/webhooks/stripe
  - [ ] Events: customer.subscription.*, invoice.*, payment_intent.*
  - [ ] Signature validation funcionando
- [ ] Teste de pagamento real realizado (R$ 1,00)
- [ ] Radar (fraud detection) ativado
- [ ] Emails de confirmação configurados

#### Assinaturas
- [ ] Trial de 7 dias funcionando
- [ ] Renovação automática ativa
- [ ] Cancelamento funcionando
- [ ] Upgrade/downgrade funcionando
- [ ] Limites por plano aplicados
- [ ] Teste completo do fluxo de pagamento

---

### 📧 3. Email e Comunicação (Dia 1 + 4)

#### SendGrid
- [ ] Conta criada e verificada
- [ ] API key configurada
- [ ] Domínio autenticado (SPF, DKIM)
- [ ] Template de boas-vindas criado
- [ ] Template de recuperação de senha criado
- [ ] Templates de drip campaigns criados (12 campanhas)
- [ ] Teste de envio realizado

#### Emails Transacionais
- [ ] Cadastro → Email de boas-vindas
- [ ] Recuperação de senha funcionando
- [ ] Trial ending (3 dias antes)
- [ ] Trial ending (1 dia antes)
- [ ] Pagamento confirmado
- [ ] Assinatura cancelada

---

### ⚖️ 4. Compliance e Legal (Dia 4)

#### LGPD
- [ ] Política de privacidade publicada (/politica-privacidade)
- [ ] Termos de uso publicados (/termos-de-uso)
- [ ] Cookie consent implementado
- [ ] DPO identificado (dpo@doutoraia.com)
- [ ] 8 direitos do titular documentados
- [ ] Processo de data breach notification documentado

#### Cookies
- [ ] Banner de consentimento exibindo
- [ ] 4 categorias (essencial, funcional, analytics, marketing)
- [ ] Preferências salvas no localStorage
- [ ] Google Analytics consent mode funcionando
- [ ] Links para política de privacidade

---

### 🎨 5. UX e Conteúdo (Dia 4)

#### Landing Page
- [ ] Hero section com CTAs
- [ ] Features (3 cards)
- [ ] Stats (4 métricas)
- [ ] Testimonials (3 depoimentos)
- [ ] Pricing preview (3 planos)
- [ ] Final CTA
- [ ] Footer completo (4 colunas)
- [ ] Mobile responsive

#### Onboarding
- [ ] Wizard de 5 passos criado
- [ ] Persistência no localStorage
- [ ] Integrado ao dashboard
- [ ] Skip option funcionando
- [ ] Completo em < 5 minutos

#### FAQ
- [ ] 24 perguntas respondidas
- [ ] 6 categorias
- [ ] Filtro por categoria
- [ ] Acordeão interativo
- [ ] CTA para contato

#### Feedback
- [ ] Botão flutuante visível
- [ ] Modal de 3 tipos (elogio, reclamação, sugestão)
- [ ] Rating com estrelas
- [ ] Persistência no localStorage
- [ ] (Opcional) Integração com API

---

### 🔍 6. SEO e Marketing (Dia 4)

#### SEO On-Page
- [ ] Meta title otimizado
- [ ] Meta description (160 caracteres)
- [ ] Keywords relevantes (11+)
- [ ] Open Graph tags completos
- [ ] Twitter Cards
- [ ] Structured Data (JSON-LD)
- [ ] Sitemap.xml gerado (/sitemap.xml)
- [ ] Robots.txt configurado (/robots.txt)
- [ ] Canonical URLs
- [ ] Alt text em imagens principais

#### Analytics
- [ ] Google Analytics 4 configurado
- [ ] Google Search Console configurado
- [ ] Sentry (error tracking) configurado - opcional
- [ ] Conversion tracking configurado

---

### 🚀 7. Performance (Dia 5)

#### Frontend (Lighthouse)
- [ ] Performance Score ≥ 90
- [ ] First Contentful Paint < 2.0s
- [ ] Largest Contentful Paint < 2.5s
- [ ] Cumulative Layout Shift < 0.1
- [ ] Total Blocking Time < 300ms
- [ ] Accessibility Score ≥ 95
- [ ] Best Practices Score ≥ 90
- [ ] SEO Score ≥ 95

#### Backend (API)
- [ ] Response Time (p95) < 500ms
- [ ] Response Time (p99) < 1000ms
- [ ] Error Rate < 1%
- [ ] Rate limiting funcionando
  - [ ] Login: 5 tentativas/minuto
  - [ ] Cadastro: 3 tentativas/minuto
  - [ ] Endpoints: 100 req/min por usuário

#### Database
- [ ] Query Time (p95) < 100ms
- [ ] Índices criados (questoes, usuarios, sessoes)
- [ ] Connection pool otimizado
- [ ] VACUUM executado

---

### 🔒 8. Segurança (Dia 5)

#### Autenticação
- [ ] Senhas com bcrypt (rounds ≥ 12)
- [ ] JWT com secret forte (256-bit)
- [ ] JWT expiration configurado (7 dias)
- [ ] Rate limiting em login/cadastro

#### Proteção
- [ ] HTTPS obrigatório
- [ ] Security headers configurados
  - [ ] Strict-Transport-Security
  - [ ] X-Frame-Options: SAMEORIGIN
  - [ ] X-Content-Type-Options: nosniff
  - [ ] X-XSS-Protection
  - [ ] Content-Security-Policy
- [ ] CORS configurado
- [ ] SQL injection protection (ORM)
- [ ] XSS protection (React + CSP)

#### Secrets
- [ ] .env não commitado (.gitignore)
- [ ] Secrets em variáveis de ambiente
- [ ] Diferentes secrets para dev/prod
- [ ] Stripe webhook signature validation

#### Scans
- [ ] npm audit (sem vulnerabilidades high/critical)
- [ ] pip-audit (sem vulnerabilidades high/critical)
- [ ] OWASP ZAP scan - opcional
- [ ] SSL Labs grade A - opcional

---

### 💾 9. Backup e Recovery (Dia 5)

#### Backups
- [ ] Backup automático de DB configurado (diário às 3h)
- [ ] Teste de restore realizado com sucesso
- [ ] S3 bucket configurado (ou alternativa) - opcional
- [ ] Retention policy: 30 dias
- [ ] Environment variables backup criado

#### Disaster Recovery
- [ ] DR plan documentado
- [ ] RTO definido: < 2 horas
- [ ] RPO definido: < 5 minutos
- [ ] Procedimentos de recovery testados

---

### 📊 10. Monitoramento (Dia 3 + 5)

#### Uptime
- [ ] UptimeRobot configurado
  - [ ] https://api.doutoraia.com/health (1 min)
  - [ ] https://doutoraia.com (1 min)
- [ ] Alertas configurados (email/SMS)

#### Performance
- [ ] Sentry configurado - opcional
- [ ] LogTail configurado - opcional
- [ ] Railway/Render metrics ativos

#### Business Metrics
- [ ] Google Analytics 4
- [ ] Stripe Dashboard
- [ ] User registration tracking
- [ ] Conversion tracking

---

### 🧪 11. Testes Funcionais

#### Fluxos Críticos
- [ ] **Cadastro**: Usuário consegue se cadastrar
- [ ] **Login**: Usuário consegue fazer login
- [ ] **Dashboard**: Dashboard carrega corretamente
- [ ] **Estudo**: Iniciar sessão de estudo funciona
- [ ] **Questões**: Responder questão com feedback
- [ ] **Peças**: Avaliar peça processual
- [ ] **Chat**: Enviar mensagem para IA
- [ ] **Gamificação**: FP sendo ganho, níveis subindo
- [ ] **Perfil**: Alterar dados do perfil
- [ ] **Senha**: Recuperar senha funciona
- [ ] **Pagamento**: Assinar plano Premium
- [ ] **Cancelamento**: Cancelar assinatura

#### Testes de Integração
- [ ] API → Database
- [ ] Frontend → API
- [ ] Stripe webhooks → Backend
- [ ] SendGrid → Email delivery
- [ ] Google Analytics → Tracking

---

### 🌐 12. DNS e Domínio

#### Domínio Principal
- [ ] Domínio registrado (doutoraia.com) - opcional
- [ ] DNS configurado
  - [ ] A record @ → Vercel IP
  - [ ] CNAME www → cname.vercel-dns.com
  - [ ] CNAME api → seu-projeto.railway.app
- [ ] SSL certificate válido (Vercel provê automaticamente)
- [ ] Redirecionamento www → non-www

---

## 🎬 Go-Live Sequence

### T-24h (Dia antes do lançamento)

1. **Freeze de código**
   - [ ] Último commit marcado como release tag
   - [ ] Changelog atualizado

2. **Smoke tests completos**
   - [ ] Todos os fluxos críticos testados
   - [ ] Performance validada (Lighthouse)
   - [ ] Security scan executado

3. **Backup final**
   - [ ] Backup manual de DB
   - [ ] Environment variables backup
   - [ ] Código em Git atualizado

4. **Comunicação**
   - [ ] Equipe notificada do lançamento
   - [ ] Plano de rollback documentado

### T-4h (4 horas antes)

1. **Verificação de infraestrutura**
   - [ ] Railway/Render health check: OK
   - [ ] Vercel deployment: OK
   - [ ] Database connection: OK
   - [ ] Stripe webhook: OK

2. **Último teste de pagamento**
   - [ ] Teste real com R$ 1,00
   - [ ] Webhook recebido e processado

3. **Ativar monitoramento**
   - [ ] UptimeRobot ativo
   - [ ] Sentry ativo (se configurado)
   - [ ] Alertas testados

### T-0 (GO LIVE!)

1. **DNS Cutover** (se domínio custom)
   - [ ] Alterar DNS para apontar para produção
   - [ ] Aguardar propagação (5-30 min)
   - [ ] Verificar HTTPS funcionando

2. **Validação imediata**
   - [ ] Acessar https://doutoraia.com
   - [ ] Fazer login de teste
   - [ ] Registrar usuário novo
   - [ ] Iniciar sessão de estudo

3. **Monitoramento ativo**
   - [ ] Verificar logs em tempo real
   - [ ] Monitorar error rate
   - [ ] Acompanhar response times

### T+1h (1 hora após)

- [ ] Verificar métricas de uptime (deve ser 100%)
- [ ] Verificar cadastros de novos usuários
- [ ] Verificar erros no Sentry (deve ser 0 critical)
- [ ] Testar fluxo completo novamente

### T+24h (1 dia após)

- [ ] Revisar logs de 24h
- [ ] Verificar taxa de conversão
- [ ] Analisar feedback de usuários
- [ ] Ajustes de urgência (se necessário)

---

## 🚨 Plano de Rollback

### Se algo der errado:

**Opção 1: Rollback de Deploy**
```bash
# Railway
railway rollback

# Vercel
vercel rollback
```

**Opção 2: Reverter DNS**
```bash
# Apontar de volta para ambiente de teste
# Ou exibir página de manutenção
```

**Opção 3: Restaurar Database**
```bash
# Restaurar backup mais recente
gunzip -c backup_latest.sql.gz | psql $DATABASE_URL
```

---

## 📊 Métricas de Sucesso (Primeira Semana)

### Técnicas
- **Uptime**: > 99.5%
- **Response Time (p95)**: < 500ms
- **Error Rate**: < 1%
- **Lighthouse Score**: > 90

### Negócio
- **Cadastros**: Meta de 100+ usuários
- **Conversão (Cadastro → Trial)**: > 20%
- **Conversão (Trial → Paid)**: > 10%
- **Churn Rate**: < 5%
- **NPS**: > 50

---

## ✅ Aprovação Final

**Responsável**: ___________________________
**Data**: _____/_____/2025
**Hora**: _____:_____

**Checklist Completo**: ☐ SIM ☐ NÃO

**Autorizado para Lançamento**: ☐ SIM ☐ NÃO

**Observações**:
_______________________________________________
_______________________________________________
_______________________________________________

---

## 🎉 Pós-Lançamento

### Semana 1
- [ ] Monitorar métricas diariamente
- [ ] Responder feedback de usuários
- [ ] Ajustes de UX baseados em comportamento real
- [ ] Blog post de lançamento (opcional)
- [ ] Social media announcement (opcional)

### Mês 1
- [ ] Análise de conversão
- [ ] A/B tests de landing page
- [ ] Otimizações de SEO
- [ ] Melhorias baseadas em dados

### Futuro
- [ ] Features novas baseadas em feedback
- [ ] Expansão de conteúdo (mais questões)
- [ ] Marketing e aquisição
- [ ] Parcerias estratégicas

---

**SISTEMA PRONTO PARA LANÇAR! 🚀**

**Boa sorte e sucesso na jornada da Doutora IA OAB!**
