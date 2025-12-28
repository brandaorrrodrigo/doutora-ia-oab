# 💳 GUIA DE CONFIGURAÇÃO DO STRIPE

## 📋 VISÃO GERAL

Este guia detalha como ativar o sistema de pagamentos Stripe para monetização da Doutora IA OAB.

**Status Atual:** ❌ STRIPE INATIVO (`STRIPE_AVAILABLE = False`)

**Tempo Estimado:** 2-3 dias de implementação + testes

---

## 🎯 PLANOS E PREÇOS

### Estrutura de Pricing (definido em .env):

```
PLANO FREE:
- Preço: R$ 0,00
- Limites: 1 sessão/dia, 0 peças

PLANO OAB MENSAL:
- Preço: R$ 49,90/mês
- Limites: 3 sessões/dia, 3 peças/mês
- ID Stripe: price_oab_mensal (a criar)

PLANO OAB SEMESTRAL:
- Preço: R$ 247,00/semestre (economiza R$ 52,40)
- Limites: 5 sessões/dia, 10 peças/mês
- ID Stripe: price_oab_semestral (a criar)
```

---

## 📦 FASE 1: SETUP INICIAL (1-2 horas)

### 1.1 Criar Conta Stripe

1. Acesse: https://dashboard.stripe.com/register
2. Crie conta com email corporativo
3. Complete verificação de identidade (CPF/CNPJ)
4. Ative conta para Brasil (BRL)

### 1.2 Configurar Webhooks

1. Acesse: https://dashboard.stripe.com/webhooks
2. Criar endpoint:
   - **URL:** `https://api.doutoraia.com/webhooks/stripe`
   - **Eventos:**
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

3. Copiar **Webhook Secret** (começará com `whsec_...`)

### 1.3 Obter API Keys

**Modo Test (desenvolvimento):**
```bash
# Dashboard > Developers > API keys (Test mode)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Modo Production (após testes):**
```bash
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 🛠️ FASE 2: CRIAR PRODUTOS E PREÇOS (30 minutos)

### 2.1 Via Dashboard Stripe

1. Acesse: https://dashboard.stripe.com/products
2. Clicar em **"+ Add product"**

#### Produto 1: OAB Mensal

```
Nome: Doutora IA OAB - Plano Mensal
Descrição: Acesso completo à plataforma com 3 sessões diárias e prática de peças
Preço: R$ 49,90
Cobrança: Mensal (recurring)
ID do Preço: price_oab_mensal (anotar!)
```

#### Produto 2: OAB Semestral

```
Nome: Doutora IA OAB - Plano Semestral
Descrição: 6 meses de acesso com desconto + heavy user escape valve
Preço: R$ 247,00
Cobrança: A cada 6 meses (recurring)
ID do Preço: price_oab_semestral (anotar!)
```

### 2.2 Configurar Trial Period (opcional)

Se quiser oferecer período de teste:
```
Trial Period: 7 dias
```

---

## 💻 FASE 3: IMPLEMENTAÇÃO NO BACKEND (1 dia)

### 3.1 Instalar Stripe Python SDK

```bash
cd D:\JURIS_IA_CORE_V1
pip install stripe==10.0.0
echo "stripe==10.0.0" >> requirements.txt
```

### 3.2 Configurar Variáveis de Ambiente

Adicionar em `.env`:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_AVAILABLE=true

# Price IDs (copiar do Stripe Dashboard)
STRIPE_PRICE_OAB_MENSAL=price_...
STRIPE_PRICE_OAB_SEMESTRAL=price_...
```

### 3.3 Ativar Stripe no Código

#### Passo 1: Modificar `auth/billing_service.py`

```python
# Linha 19 - MUDAR DE False PARA True
STRIPE_AVAILABLE = os.getenv("STRIPE_AVAILABLE", "false").lower() == "true"
```

#### Passo 2: Verificar Implementação

Arquivo `auth/billing_service.py` já tem:
- ✅ `criar_checkout_session()` - Cria sessão de pagamento
- ✅ `processar_webhook_stripe()` - Processa eventos do webhook
- ✅ `criar_assinatura()` - Cria assinatura
- ✅ `cancelar_assinatura()` - Cancela assinatura
- ✅ `atualizar_metodo_pagamento()` - Atualiza cartão

**Implementação está pronta!** Apenas precisa de configuração.

### 3.4 Criar Endpoint de Checkout

Adicionar em `api/api_server_with_enforcement.py`:

```python
# Novo modelo de request
class CheckoutRequest(BaseModel):
    """Request para criar checkout Stripe"""
    user_id: str = Field(..., description="ID do usuário")
    price_id: str = Field(..., description="ID do preço no Stripe")

# Novo endpoint
@app.post("/checkout/create", response_model=Response)
async def criar_checkout(request_body: CheckoutRequest):
    """
    Cria sessão de checkout Stripe.

    Redireciona usuário para página de pagamento segura.
    """
    try:
        from auth.billing_service import criar_checkout_session

        # Obter email do usuário
        user = await obter_usuario_por_id(request_body.user_id)

        session = criar_checkout_session(
            user_id=request_body.user_id,
            user_email=user.email,
            price_id=request_body.price_id,
            success_url=f"{os.getenv('FRONTEND_URL')}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/checkout/cancel"
        )

        return Response(
            success=True,
            data={
                "checkout_url": session.url,
                "session_id": session.id
            },
            message="Sessão de checkout criada"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro ao criar checkout",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )
```

### 3.5 Webhook Endpoint (já implementado)

Verificar que existe em `api/endpoints/admin.py` ou criar:

```python
@app.post("/webhooks/stripe")
async def webhook_stripe(request: Request):
    """
    Webhook do Stripe para processar eventos de pagamento.
    """
    from auth.billing_service import processar_webhook_stripe

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = processar_webhook_stripe(payload, sig_header)

        # Processar diferentes tipos de eventos
        if event.type == 'checkout.session.completed':
            # Ativar assinatura do usuário
            session = event.data.object
            user_id = session.metadata.get('user_id')
            # Atualizar plano no banco

        elif event.type == 'customer.subscription.deleted':
            # Cancelar assinatura do usuário
            subscription = event.data.object
            # Downgrade para FREE

        return {"status": "success"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

---

## 🎨 FASE 4: IMPLEMENTAÇÃO NO FRONTEND (1 dia)

### 4.1 Criar Página de Planos

Criar `app/planos/page.tsx`:

```tsx
'use client';

import { useState } from 'react';
import { api } from '@/lib/api';

export default function PlanosPage() {
  const [loading, setLoading] = useState(false);

  const planos = [
    {
      nome: 'FREE',
      preco: 'R$ 0',
      periodo: '/mês',
      recursos: ['1 sessão/dia', '0 peças', 'Chat básico'],
      priceId: null,
      destaque: false
    },
    {
      nome: 'OAB MENSAL',
      preco: 'R$ 49,90',
      periodo: '/mês',
      recursos: ['3 sessões/dia', '3 peças/mês', 'Chat ilimitado', 'Relatórios'],
      priceId: 'price_oab_mensal',
      destaque: true
    },
    {
      nome: 'OAB SEMESTRAL',
      preco: 'R$ 247',
      periodo: '/semestre',
      recursos: ['5 sessões/dia', '10 peças/mês', 'Chat ilimitado', 'Relatórios', 'Heavy user valve'],
      priceId: 'price_oab_semestral',
      destaque: false
    }
  ];

  const handleSubscribe = async (priceId: string) => {
    setLoading(true);
    try {
      const userId = localStorage.getItem('user_id');
      const result = await api.createCheckout(userId, priceId);

      // Redirecionar para Stripe Checkout
      window.location.href = result.data.checkout_url;
    } catch (error) {
      alert('Erro ao processar pagamento');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-12">
          Escolha seu Plano
        </h1>

        <div className="grid md:grid-cols-3 gap-8">
          {planos.map((plano) => (
            <div
              key={plano.nome}
              className={`bg-white rounded-lg shadow-lg p-8 ${
                plano.destaque ? 'ring-4 ring-purple-900' : ''
              }`}
            >
              {plano.destaque && (
                <span className="bg-purple-900 text-white px-3 py-1 rounded-full text-sm">
                  Mais Popular
                </span>
              )}

              <h2 className="text-2xl font-bold mt-4">{plano.nome}</h2>
              <div className="mt-4">
                <span className="text-4xl font-bold">{plano.preco}</span>
                <span className="text-gray-600">{plano.periodo}</span>
              </div>

              <ul className="mt-6 space-y-3">
                {plano.recursos.map((recurso) => (
                  <li key={recurso} className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    {recurso}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => plano.priceId && handleSubscribe(plano.priceId)}
                disabled={!plano.priceId || loading}
                className={`w-full mt-8 py-3 rounded-lg font-bold ${
                  plano.priceId
                    ? 'bg-purple-900 text-white hover:bg-purple-800'
                    : 'bg-gray-300 text-gray-600 cursor-not-allowed'
                }`}
              >
                {plano.priceId ? 'Assinar Agora' : 'Plano Atual'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 4.2 Adicionar Método no API Client

Em `lib/api.ts`:

```typescript
async createCheckout(userId: string, priceId: string) {
  return this.request('/checkout/create', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, price_id: priceId })
  });
}
```

### 4.3 Páginas de Sucesso/Cancelamento

`app/checkout/success/page.tsx` e `app/checkout/cancel/page.tsx`

---

## 🧪 FASE 5: TESTES (1 dia)

### 5.1 Testes com Cartões de Teste do Stripe

```
Sucesso: 4242 4242 4242 4242
Falha: 4000 0000 0000 0002
Requer autenticação: 4000 0025 0000 3155

Data de validade: Qualquer data futura
CVC: Qualquer 3 dígitos
CEP: Qualquer
```

### 5.2 Checklist de Testes

- [ ] Criar checkout para plano mensal
- [ ] Completar pagamento com cartão de teste
- [ ] Verificar que webhook foi recebido
- [ ] Confirmar que plano foi atualizado no banco
- [ ] Verificar que limites mudaram
- [ ] Testar cancelamento de assinatura
- [ ] Testar downgrade FREE → PAGO → FREE
- [ ] Testar upgrade MENSAL → SEMESTRAL
- [ ] Simular pagamento falho
- [ ] Testar webhook de renovação

---

## 🚀 FASE 6: PRODUÇÃO (30 minutos)

### 6.1 Ativar Modo Live no Stripe

1. Dashboard > Developers > API keys
2. Mudar para **Live mode**
3. Completar checklist de ativação:
   - ✅ Verificação de identidade
   - ✅ Conta bancária configurada
   - ✅ Termos aceitos
   - ✅ Compliance LGPD

### 6.2 Atualizar Variáveis de Ambiente

```bash
# Railway - Production
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_live_...
STRIPE_AVAILABLE=true
```

### 6.3 Testar em Produção

- Fazer transação real de R$ 1,00
- Verificar recebimento
- Cancelar e verificar reembolso

---

## 📊 MONITORAMENTO

### Métricas Importantes:

1. **Taxa de Conversão:** FREE → PAGO
2. **Churn Rate:** Cancelamentos/Total
3. **MRR:** Monthly Recurring Revenue
4. **Failed Payments:** Pagamentos falhados

### Dashboard Stripe:
- https://dashboard.stripe.com/dashboard
- Monitorar diariamente primeiros 30 dias

---

## ⚠️ TROUBLESHOOTING

### Webhook não está sendo recebido:

```bash
# Testar localmente com Stripe CLI
stripe listen --forward-to localhost:8000/webhooks/stripe
stripe trigger checkout.session.completed
```

### Pagamento aparece como "incompleto":

- Verificar se webhook está configurado corretamente
- Checar logs no Dashboard Stripe
- Verificar signature do webhook

### Assinatura não foi ativada:

- Verificar logs do webhook
- Confirmar que user_id está nos metadados
- Checar se banco foi atualizado

---

## 📞 SUPORTE STRIPE

- Documentação: https://stripe.com/docs
- Support: https://support.stripe.com
- Community: https://github.com/stripe

---

**Status:** 📝 Documentado - Pronto para implementação

**Próximos Passos:**
1. Criar conta Stripe
2. Configurar produtos e preços
3. Ativar no código (3 linhas!)
4. Testar com cartões de teste

**Última atualização:** 2025-12-28
