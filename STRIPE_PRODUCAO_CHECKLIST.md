# 💳 Checklist Completo - Stripe em Produção

**Objetivo**: Garantir que os pagamentos funcionem perfeitamente em produção
**Tempo estimado**: 2-3 horas
**Última atualização**: 28/12/2025

---

## ⚠️ IMPORTANTE

**NUNCA use chaves de teste em produção!**
- Chaves de teste começam com `sk_test_` e `pk_test_`
- Chaves de produção começam com `sk_live_` e `pk_live_`

---

## 📋 PARTE 1: Ativação da Conta Stripe

### 1.1 Informações da Empresa

- [ ] Razão social completa
- [ ] CNPJ
- [ ] Endereço completo
- [ ] Telefone de contato
- [ ] Email de contato
- [ ] Website/domínio

### 1.2 Representante Legal

- [ ] Nome completo
- [ ] CPF
- [ ] Data de nascimento
- [ ] Endereço residencial
- [ ] Email pessoal
- [ ] Telefone pessoal

### 1.3 Conta Bancária

- [ ] Banco
- [ ] Agência
- [ ] Conta corrente
- [ ] Titular da conta (deve ser a empresa)
- [ ] Comprovante de conta (PDF)

### 1.4 Documentação

- [ ] Contrato social ou estatuto
- [ ] Última alteração contratual
- [ ] Cartão CNPJ
- [ ] Comprovante de endereço da empresa
- [ ] RG/CNH do representante legal
- [ ] CPF do representante legal

### 1.5 Análise Stripe

- [ ] Aguardar aprovação (geralmente 1-3 dias úteis)
- [ ] Responder a solicitações adicionais se houver
- [ ] Confirmar ativação por email

---

## 🛍️ PARTE 2: Criar Produtos

### 2.1 Plano Premium

**Configuração**:
1. Products → Create Product
2. Preencher:
   ```
   Nome: Plano Premium - Doutora IA OAB
   Descrição: Acesso completo à plataforma com chat IA, peças processuais e relatórios avançados

   Pricing:
   - Modelo: Recurring
   - Preço: R$ 49,90
   - Período: Mensal
   - Moeda: BRL

   Billing:
   - Charge automatically
   - Collect payment method for future usage

   Free trial:
   - Trial period: 7 days
   ```

3. Save product
4. Copiar `price_id` (price_***)

**Metadados** (opcional mas recomendado):
```json
{
  "plano": "PREMIUM",
  "sessoes_por_dia": "15",
  "questoes_por_sessao": "30",
  "acesso_chat_ia": "true",
  "acesso_pecas": "true"
}
```

### 2.2 Plano Pro

**Configuração**:
```
Nome: Plano Pro - Doutora IA OAB
Descrição: Acesso ilimitado a todos os recursos da plataforma

Pricing:
- Preço: R$ 99,90
- Período: Mensal
- Trial: 7 days
```

Copiar `price_id`

### 2.3 Cupons de Desconto (Opcional)

**Criar cupom de lançamento**:
1. Products → Coupons → New
2. Configuração:
   ```
   Nome: LANCAMENTO2025
   Tipo: Percentage
   Desconto: 20%
   Duração: Once / Repeating (3 months)
   Redemption: Unlimited
   ```

---

## 🔗 PARTE 3: Webhooks

### 3.1 Criar Endpoint

1. Developers → Webhooks → Add endpoint
2. URL: `https://api.seudominio.com/pagamento/webhook`
3. Description: "Webhook de produção para Doutora IA OAB"

### 3.2 Selecionar Eventos

**Obrigatórios**:
- [x] `checkout.session.completed` - Checkout concluído
- [x] `customer.subscription.created` - Assinatura criada
- [x] `customer.subscription.updated` - Assinatura atualizada
- [x] `customer.subscription.deleted` - Assinatura cancelada
- [x] `invoice.payment_succeeded` - Pagamento bem-sucedido
- [x] `invoice.payment_failed` - Pagamento falhou

**Recomendados**:
- [x] `customer.subscription.trial_will_end` - Trial ending soon (3 dias antes)
- [x] `payment_intent.succeeded` - Intenção de pagamento sucedida
- [x] `payment_intent.payment_failed` - Intenção de pagamento falhou
- [x] `charge.refunded` - Reembolso processado
- [x] `charge.dispute.created` - Disputa criada (chargeback)

### 3.3 Copiar Signing Secret

- [ ] Copiar `whsec_***`
- [ ] Adicionar ao Railway/Render: `STRIPE_WEBHOOK_SECRET`
- [ ] **NUNCA** commitar este secret no código

### 3.4 Testar Webhook

**Usar Stripe CLI**:
```bash
# Instalar Stripe CLI
brew install stripe/stripe-cli/stripe  # macOS
choco install stripe-cli               # Windows

# Login
stripe login

# Escutar eventos
stripe listen --forward-to https://api.seudominio.com/pagamento/webhook

# Trigger evento de teste
stripe trigger checkout.session.completed
```

**Verificar**:
- [ ] Evento recebido no endpoint
- [ ] Status 200 retornado
- [ ] Assinatura criada no banco de dados
- [ ] Logs mostram processamento correto

---

## 🔐 PARTE 4: Segurança

### 4.1 API Keys

**Proteção**:
- [ ] Usar variáveis de ambiente (NUNCA hardcode)
- [ ] Diferentes keys para test/production
- [ ] Rotacionar keys periodicamente (a cada 90 dias)
- [ ] Limitar acesso (apenas backend, nunca frontend)

**Test Keys** (desenvolvimento):
```env
STRIPE_API_KEY=sk_test_***
STRIPE_PUBLISHABLE_KEY=pk_test_***  # Se usar checkout client-side
```

**Live Keys** (produção):
```env
STRIPE_API_KEY=sk_live_***
STRIPE_PUBLISHABLE_KEY=pk_live_***
```

### 4.2 Webhook Signature Verification

**Validar SEMPRE** no backend:
```python
# CORRETO ✅
webhook_result = stripe_service.processar_webhook(payload, signature)
if not webhook_result['success']:
    raise HTTPException(status_code=400, detail="Invalid signature")

# ERRADO ❌ - NUNCA faça isso
# Processar webhook sem validar assinatura
```

### 4.3 HTTPS Obrigatório

- [ ] Todos os endpoints são HTTPS
- [ ] Certificado SSL válido
- [ ] Redirecionamento HTTP → HTTPS ativo

### 4.4 Rate Limiting

**Implementar**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/pagamento/criar-checkout")
@limiter.limit("10/minute")  # Máximo 10 checkouts por minuto por IP
async def criar_checkout(request: Request):
    ...
```

---

## 💰 PARTE 5: Configurações de Pagamento

### 5.1 Métodos de Pagamento

**Habilitar** em Settings → Payment methods:
- [x] Cartões de crédito (Visa, Mastercard, Amex, Elo)
- [x] Cartões de débito
- [ ] Pix (opcional - requer integração adicional)
- [ ] Boleto (opcional - ciclo de 3 dias)

### 5.2 Moeda

- [x] Brazilian Real (BRL)
- [ ] Configurar multi-moeda (se quiser aceitar USD, EUR, etc.)

### 5.3 Emails Stripe

**Configurar** em Settings → Emails:
- [x] Payment confirmations
- [x] Receipts
- [x] Failed payments
- [x] Subscription reminders
- [ ] Customize email template (logo, cores)

### 5.4 Customer Portal

**Ativar** em Settings → Customer portal:
- [x] Allow customers to:
  - Update payment methods
  - View invoices
  - Cancel subscriptions
  - Update billing information
- [x] Set business branding (logo, cores)
- [x] Configure cancellation flow
  - [x] Ask cancellation reason
  - [x] Offer discount to retain (opcional)

---

## 🛡️ PARTE 6: Prevenção de Fraude (Radar)

### 6.1 Configurar Radar

**Regras recomendadas**:
1. Block if CVC check fails
2. Block if postal code check fails
3. Block if IP is from high-risk country
4. Require 3D Secure for high-value payments (> R$ 500)

**Threshold**:
- Risk score > 75: Bloquear
- Risk score 50-75: Review manual
- Risk score < 50: Aprovar

### 6.2 Lista de Bloqueio

- [ ] Bloquear emails descartáveis (mailinator.com, etc.)
- [ ] Bloquear IPs de VPN/Proxy (opcional)
- [ ] Bloquear países de alto risco (opcional)

### 6.3 3D Secure

- [ ] Habilitar SCA (Strong Customer Authentication)
- [ ] Configurar threshold: > R$ 500 requer 3DS

---

## 📊 PARTE 7: Relatórios e Reconciliação

### 7.1 Dashboard Stripe

**Monitorar diariamente**:
- Volume de vendas
- Taxa de conversão
- Falhas de pagamento
- Chargebacks
- Novos assinantes
- Cancelamentos

### 7.2 Exportar Dados

**Configurar exports automáticos**:
1. Reports → Create report
2. Tipo: Payments
3. Frequência: Daily
4. Formato: CSV
5. Destino: Email ou SFTP

### 7.3 Reconciliação Bancária

**Processo**:
1. Exportar transações Stripe (diário)
2. Comparar com extrato bancário
3. Verificar match:
   - Data do pagamento
   - Valor líquido (após fees)
   - Status
4. Investigar discrepâncias

---

## 🧪 PARTE 8: Testes em Produção

### 8.1 Cartões de Teste

**NÃO usar em produção!**

Em produção, use cartão real mas:
- Pequeno valor (R$ 1,00)
- Cancelar assinatura imediatamente após
- Reembolsar se necessário

### 8.2 Fluxo Completo de Teste

**Checklist**:
- [ ] 1. Criar conta de teste no site
- [ ] 2. Ir para /planos
- [ ] 3. Escolher Premium
- [ ] 4. Preencher dados de pagamento (cartão real)
- [ ] 5. Confirmar que R$ 0,00 é cobrado (trial de 7 dias)
- [ ] 6. Verificar assinatura ativa no banco
- [ ] 7. Verificar webhook recebido
- [ ] 8. Testar acesso a features premium
- [ ] 9. Cancelar assinatura
- [ ] 10. Verificar webhook de cancelamento
- [ ] 11. Confirmar acesso até fim do período

### 8.3 Simular Falha de Pagamento

**Após trial period**:
1. No Stripe Dashboard, ir em customer
2. Update payment method → Use test card `4000000000000341` (declined)
3. Trigger invoice payment
4. Verificar que:
   - [ ] Webhook `invoice.payment_failed` recebido
   - [ ] Assinatura marcada como `PAUSADO` no banco
   - [ ] Email enviado ao usuário
   - [ ] Acesso bloqueado no sistema

---

## 📧 PARTE 9: Comunicação com Clientes

### 9.1 Templates de Email

**Criar** em Settings → Email → Templates:

**1. Boas-vindas (Trial)**:
```
Assunto: Bem-vindo à Doutora IA OAB! 🎉

Olá {{customer_name}},

Sua assinatura Premium foi ativada com sucesso!

Você tem 7 dias de teste grátis. Explore todos os recursos:
- Chat com IA jurídica
- Prática de peças processuais
- Relatórios avançados de desempenho

Após o período de teste, sua assinatura será renovada automaticamente por R$ 49,90/mês.

Bons estudos!
Equipe Doutora IA
```

**2. Falha de Pagamento**:
```
Assunto: Problema com seu pagamento ⚠️

Olá {{customer_name}},

Não conseguimos processar seu pagamento de R$ {{amount}}.

Por favor, atualize sua forma de pagamento em:
{{update_payment_link}}

Seu acesso será mantido até {{access_end_date}}.

Dúvidas? Responda este email.
```

**3. Cancelamento**:
```
Assunto: Sua assinatura foi cancelada

Olá {{customer_name}},

Sua assinatura foi cancelada conforme solicitado.

Você terá acesso até {{access_end_date}}.

Sentiremos sua falta! Se mudar de ideia:
{{reactivate_link}}

Obrigado por usar a Doutora IA OAB.
```

### 9.2 Webhook Notifications

**Implementar no backend**:
```python
async def _processar_pagamento_falha(data: Dict, db: Session):
    # Enviar email via SendGrid
    user = get_user_by_stripe_customer(data['customer'])

    email_service.enviar_email_personalizado(
        para=user.email,
        assunto="Problema com seu pagamento",
        template_id="d-***",  # Template SendGrid
        dados={
            'customer_name': user.nome,
            'amount': data['amount'] / 100,
            'update_payment_link': f'{FRONTEND_URL}/assinatura'
        }
    )
```

---

## ✅ CHECKLIST FINAL - Produção

### Conta Stripe
- [ ] Conta ativada e verificada
- [ ] Informações bancárias cadastradas
- [ ] Modo Live ativado

### Produtos
- [ ] Plano Premium criado (price_id copiado)
- [ ] Plano Pro criado (price_id copiado)
- [ ] Preços em BRL corretos
- [ ] Trial de 7 dias configurado
- [ ] Metadados adicionados

### Webhooks
- [ ] Endpoint criado em produção
- [ ] Todos os eventos essenciais selecionados
- [ ] Signing secret copiado e configurado
- [ ] Webhook testado e funcionando
- [ ] Logs mostram eventos recebidos

### Segurança
- [ ] API keys em variáveis de ambiente
- [ ] HTTPS em todos os endpoints
- [ ] Signature validation implementada
- [ ] Rate limiting ativo
- [ ] Radar configurado

### Pagamentos
- [ ] Métodos de pagamento habilitados
- [ ] Emails configurados
- [ ] Customer Portal ativo
- [ ] 3D Secure configurado

### Testes
- [ ] Fluxo completo testado em produção
- [ ] Checkout funcionando
- [ ] Webhooks sendo processados
- [ ] Assinaturas criadas corretamente
- [ ] Cancelamento funcionando

### Monitoramento
- [ ] Dashboard Stripe configurado
- [ ] Alertas de falha de pagamento
- [ ] Relatórios automáticos configurados
- [ ] Reconciliação bancária planejada

---

## 🚨 Problemas Comuns

### "Webhook signature verification failed"

**Causa**: Signing secret incorreto
**Solução**:
1. Verificar `STRIPE_WEBHOOK_SECRET` no env
2. Regenerar secret no Stripe Dashboard
3. Atualizar env e redeployar

### "Payment declined"

**Causas**:
- Cartão sem saldo
- Bandeira não aceita
- Fraude detectada (Radar)
- CVC incorreto

**Solução**: Pedir ao usuário para:
1. Verificar dados do cartão
2. Entrar em contato com banco
3. Usar outro cartão

### "Customer already exists"

**Causa**: Tentando criar customer duplicado
**Solução**: Buscar customer por email antes de criar

---

## 📞 Suporte Stripe

- **Dashboard**: https://dashboard.stripe.com/
- **Documentação**: https://stripe.com/docs
- **Suporte**: https://support.stripe.com/
- **Status**: https://status.stripe.com/

---

**Pronto para processar pagamentos em produção! 💰**
