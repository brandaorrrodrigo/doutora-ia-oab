# Dia 2: Pagamentos e Monetização - COMPLETO ✅

**Data**: 28/12/2025
**Status**: Implementação completa do sistema de assinaturas e pagamentos

---

## 📋 Resumo Executivo

Implementação completa do sistema de assinaturas com integração Stripe, incluindo:
- ✅ Modelos de banco de dados para assinaturas e pagamentos
- ✅ Serviço de integração com Stripe
- ✅ Endpoints de API para gestão de pagamentos
- ✅ Frontend completo (planos, checkout, gerenciamento)
- ✅ Sistema de enforcement de limites por plano
- ✅ Processamento de webhooks do Stripe

---

## 🗄️ 1. Banco de Dados

### Novos Modelos Criados

#### **Assinatura** (assinaturas)
```python
- id (UUID)
- user_id (UUID) - FK para users
- plano (GRATUITO, PREMIUM, PRO)
- status (ATIVO, CANCELADO, EXPIRADO, TRIAL, PAUSADO)
- preco_mensal (DECIMAL)

# Limites do plano
- sessoes_por_dia (INT) - -1 = ilimitado
- questoes_por_sessao (INT) - -1 = ilimitado
- acesso_chat_ia (BOOLEAN)
- acesso_pecas (BOOLEAN)
- acesso_relatorios (BOOLEAN)
- acesso_simulados (BOOLEAN)

# Integração Stripe
- stripe_customer_id
- stripe_subscription_id
- stripe_price_id

# Datas
- data_inicio
- data_fim
- proxima_cobranca
- cancelado_em
```

#### **Pagamento** (pagamentos)
```python
- id (UUID)
- assinatura_id (UUID) - FK para assinaturas
- user_id (UUID) - FK para users
- valor (DECIMAL)
- moeda (BRL)
- status (PENDENTE, PROCESSANDO, PAGO, FALHOU, REEMBOLSADO, CANCELADO)
- metodo_pagamento
- stripe_payment_intent_id
- stripe_charge_id
- stripe_invoice_id
- data_pagamento
- metadata (JSONB)
```

### Migration SQL
**Arquivo**: `database/migrations/015_adicionar_assinaturas_pagamentos.sql`

- Cria tabelas `assinaturas` e `pagamentos`
- Indexes otimizados para consultas rápidas
- Triggers para `updated_at` automático
- Cria assinatura GRATUITA para usuários existentes

---

## 💳 2. Integração Stripe

### Serviço Stripe
**Arquivo**: `engines/stripe_service.py`

#### Métodos Implementados:

1. **criar_cliente()** - Cria cliente no Stripe
2. **criar_checkout_session()** - Cria sessão de checkout
3. **obter_assinatura()** - Obtém detalhes da assinatura
4. **cancelar_assinatura()** - Cancela assinatura
5. **reativar_assinatura()** - Reativa assinatura cancelada
6. **processar_webhook()** - Processa eventos do Stripe
7. **criar_portal_cliente()** - Cria portal de gerenciamento
8. **obter_plano_info()** - Retorna info do plano
9. **listar_todos_planos()** - Lista todos os planos

#### Planos Configurados:

| Plano | Preço | Sessões/Dia | Questões/Sessão | Chat IA | Peças | Relatórios |
|-------|-------|-------------|-----------------|---------|-------|------------|
| GRATUITO | R$ 0 | 5 | 10 | ❌ | ❌ | ❌ |
| PREMIUM | R$ 49.90 | 15 | 30 | ✅ | ✅ | ✅ |
| PRO | R$ 99.90 | ∞ | ∞ | ✅ | ✅ | ✅ |

**Todos os planos pagos incluem 7 dias de teste grátis**

---

## 🔌 3. API Endpoints

### Endpoints de Pagamento
**Arquivo**: `api/payment_endpoints.py`

#### **POST /pagamento/criar-checkout**
Cria sessão de checkout do Stripe
```json
Request:
{
  "user_id": "uuid",
  "plano": "PREMIUM",
  "metadata": {}
}

Response:
{
  "success": true,
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_..."
}
```

#### **POST /pagamento/webhook**
Processa webhooks do Stripe
- `checkout.session.completed` - Assinatura criada
- `customer.subscription.updated` - Assinatura atualizada
- `customer.subscription.deleted` - Assinatura cancelada
- `invoice.payment_succeeded` - Pagamento bem-sucedido
- `invoice.payment_failed` - Pagamento falhou

#### **GET /pagamento/assinatura/{user_id}**
Retorna assinatura do usuário
```json
{
  "success": true,
  "data": {
    "plano": "PREMIUM",
    "status": "ATIVO",
    "preco_mensal": 49.90,
    "sessoes_por_dia": 15,
    "questoes_por_sessao": 30,
    "acesso_chat_ia": true,
    "proxima_cobranca": "2025-02-01T00:00:00"
  }
}
```

#### **POST /pagamento/cancelar**
Cancela assinatura
```json
Request:
{
  "user_id": "uuid",
  "imediatamente": false
}
```

#### **POST /pagamento/reativar**
Reativa assinatura cancelada

#### **POST /pagamento/portal**
Retorna URL do portal Stripe (gerenciar pagamento, ver faturas)

#### **GET /pagamento/planos**
Lista todos os planos disponíveis

#### **GET /usuario/limites/{user_id}**
Retorna limites e uso atual do usuário
```json
{
  "plano": "PREMIUM",
  "status": "ATIVO",
  "limites": {
    "sessoes_por_dia": {
      "limite": 15,
      "usado_hoje": 3,
      "restante": 12
    }
  },
  "acessos": {
    "chat_ia": true,
    "pecas": true
  }
}
```

---

## 🎨 4. Frontend - Páginas Criadas

### 4.1 Página de Planos (/planos)
**Arquivo**: `app/planos/page.tsx`

**Recursos**:
- Grid de 3 planos com comparação visual
- Badge "Mais Popular" no plano Premium
- Lista de features com checkmarks
- FAQ com 4 perguntas comuns
- Integração automática com checkout
- Redirecionamento para login se não autenticado

### 4.2 Página de Sucesso (/pagamento/sucesso)
**Arquivo**: `app/pagamento/sucesso/page.tsx`

**Recursos**:
- Confirmação visual com ícone de sucesso
- Lista de recursos desbloqueados
- Informação sobre período de teste
- Countdown automático (5s) para dashboard
- Links para dashboard e gerenciamento

### 4.3 Gerenciamento de Assinatura (/assinatura)
**Arquivo**: `app/assinatura/page.tsx`

**Recursos**:
- Visualização completa da assinatura
- Status colorido (ATIVO/CANCELADO/etc)
- Informações de cobrança
- Lista de recursos do plano
- Botões para:
  - Ver outros planos (upgrade/downgrade)
  - Abrir portal Stripe
  - Reativar assinatura
  - Cancelar assinatura
- Modal de confirmação de cancelamento
- Proteção de rota (requer autenticação)

---

## 🛡️ 5. Sistema de Enforcement

### Serviço de Enforcement
**Arquivo**: `engines/plan_enforcement.py`

#### Classe **PlanEnforcementService**

**Métodos de Verificação**:

1. **verificar_sessoes_diarias(user_id)**
   - Verifica se pode iniciar nova sessão hoje
   - Retorna uso atual e restante
   - Lança `EnforcementError` se limite atingido

2. **verificar_questoes_por_sessao(user_id, questoes_respondidas)**
   - Verifica limite de questões na sessão
   - Suporta planos ilimitados (-1)

3. **verificar_acesso_chat_ia(user_id)**
   - Valida acesso ao chat com IA
   - Bloqueia se plano não permitir

4. **verificar_acesso_pecas(user_id)**
   - Valida acesso à prática de peças

5. **verificar_acesso_relatorios(user_id)**
   - Valida acesso a relatórios detalhados

6. **obter_limites_usuario(user_id)**
   - Retorna todos os limites e uso atual
   - Usado para exibir no dashboard

#### Exceção Customizada
```python
class EnforcementError(Exception):
    - message: Mensagem de erro
    - limit_type: Tipo de limite violado
    - current: Uso atual
    - limit: Limite máximo
    - plano: Plano do usuário
```

---

## ⚙️ 6. Configuração Necessária

### Variáveis de Ambiente
Adicionar ao `.env`:

```env
# Stripe Configuration
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PREMIUM=price_...
STRIPE_PRICE_ID_PRO=price_...

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Como Obter as Chaves Stripe:

1. **Criar conta no Stripe**: https://dashboard.stripe.com/register
2. **Modo Test**: Use as chaves de teste durante desenvolvimento
3. **Criar Produtos**:
   - Ir em Products → Create Product
   - Criar "Plano Premium" (R$ 49,90/mês)
   - Criar "Plano Pro" (R$ 99,90/mês)
   - Copiar os `price_id` de cada um

4. **Webhook Secret**:
   - Developers → Webhooks → Add endpoint
   - URL: `http://seu-servidor:8000/pagamento/webhook`
   - Eventos: Selecionar todos os eventos de checkout, subscription e invoice
   - Copiar o `whsec_...`

---

## 🧪 7. Como Testar

### 7.1 Rodar Migration
```bash
# Conectar ao PostgreSQL e executar:
psql -U postgres -d juris_ia -f database/migrations/015_adicionar_assinaturas_pagamentos.sql
```

### 7.2 Iniciar Backend
```bash
cd D:\JURIS_IA_CORE_V1
python -m uvicorn api.api_server:app --reload --port 8000
```

### 7.3 Iniciar Frontend
```bash
cd D:\doutora-ia-oab-frontend
npm run dev
```

### 7.4 Fluxo de Teste

1. **Criar conta** em `/cadastro`
2. **Fazer login** em `/login`
3. **Ver planos** em `/planos`
4. **Clicar em "Começar Teste Grátis"** no plano Premium
5. **Preencher dados de cartão de teste**:
   - Número: `4242 4242 4242 4242`
   - Data: Qualquer data futura
   - CVC: Qualquer 3 dígitos
6. **Confirmar pagamento**
7. **Verificar redirecionamento** para `/pagamento/sucesso`
8. **Verificar assinatura** em `/assinatura`

### 7.5 Testar Webhooks (Local)

Usar Stripe CLI:
```bash
stripe listen --forward-to localhost:8000/pagamento/webhook
stripe trigger checkout.session.completed
```

---

## 📊 8. Integração com Sistema Existente

### 8.1 models.py
- Adicionados modelos `Assinatura` e `Pagamento`
- Atualizado `get_all_models()` para incluir novos modelos

### 8.2 api_server.py
- Importado e registrado `payment_router`
- Endpoint `/usuario/limites/{user_id}` disponível

---

## 🚀 9. Próximos Passos (Dia 3)

### Deploy e Infraestrutura
- [ ] Configurar servidor de produção
- [ ] Deploy do backend (Railway/Heroku/AWS)
- [ ] Deploy do frontend (Vercel)
- [ ] Configurar domínio personalizado
- [ ] SSL/HTTPS
- [ ] Monitoramento e logs
- [ ] Backup automático do banco de dados

### Stripe Produção
- [ ] Ativar modo produção no Stripe
- [ ] Configurar webhook de produção
- [ ] Configurar produtos reais
- [ ] Testar fluxo completo em produção

---

## 📝 10. Notas Importantes

### Segurança
✅ Validação de assinatura em webhooks do Stripe
✅ Tokens JWT para autenticação
✅ Enforcementde limites no backend (não apenas frontend)
✅ Validação de status da assinatura antes de permitir acesso

### Performance
✅ Indexes otimizados nas tabelas
✅ Queries eficientes com SQLAlchemy
✅ Cache de informações de assinatura possível (implementar se necessário)

### UX
✅ Feedback claro de limites atingidos
✅ Sugestão de upgrade quando limite bloqueado
✅ 7 dias de teste grátis em todos os planos pagos
✅ Cancelamento sem complicações
✅ Portal Stripe para gerenciamento self-service

---

## ✅ Status Final - Dia 2

**TODOS OS OBJETIVOS CUMPRIDOS**

- ✅ Modelos de banco criados e migrados
- ✅ Integração Stripe completa
- ✅ Endpoints de API funcionais
- ✅ Frontend completo e responsivo
- ✅ Sistema de enforcement robusto
- ✅ Processamento de webhooks
- ✅ Documentação completa

**O sistema está pronto para testes e configuração das chaves Stripe!**

---

**Próxima etapa**: Dia 3 - Deploy e Infraestrutura
