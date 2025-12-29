# 📊 Guia de Monitoramento e Logs - Doutora IA OAB

**Objetivo**: Configurar monitoramento completo para detectar e resolver problemas rapidamente
**Última atualização**: 28/12/2025

---

## 🎯 Estratégia de Monitoramento

### Camadas de Monitoramento

1. **Infraestrutura**: Servidores, banco de dados, rede
2. **Aplicação**: API, frontend, performance
3. **Negócio**: Conversões, pagamentos, usuários ativos
4. **Segurança**: Ataques, tentativas de invasão, vulnerabilidades

---

## 📈 PARTE 1: Métricas Essenciais

### 1.1 Backend (API)

**Monitorar**:
- ✅ Uptime (deve ser > 99.9%)
- ✅ Tempo de resposta (deve ser < 500ms p95)
- ✅ Taxa de erros (deve ser < 1%)
- ✅ CPU/RAM usage
- ✅ Requisições por segundo

**Ferramentas**:
- Railway Dashboard (built-in)
- UptimeRobot (gratuito)
- New Relic (pago, completo)

### 1.2 Frontend

**Monitorar**:
- ✅ Core Web Vitals (LCP, FID, CLS)
- ✅ Tempo de carregamento
- ✅ Taxa de bounce
- ✅ Erros JavaScript

**Ferramentas**:
- Vercel Analytics (built-in)
- Google Analytics 4
- Sentry (error tracking)

### 1.3 Banco de Dados

**Monitorar**:
- ✅ Uso de disco (< 80%)
- ✅ Conexões ativas
- ✅ Query performance
- ✅ Locks e deadlocks

**Ferramentas**:
- Railway PostgreSQL Metrics
- pgAdmin
- pg_stat_statements

### 1.4 Pagamentos (Stripe)

**Monitorar**:
- ✅ Taxa de conversão
- ✅ Falhas de pagamento
- ✅ Chargebacks
- ✅ MRR (Monthly Recurring Revenue)

**Ferramentas**:
- Stripe Dashboard
- Stripe Radar (fraude)

---

## 🔧 PARTE 2: Configurar Monitoramento

### 2.1 UptimeRobot (Gratuito)

**Setup**:
1. Criar conta: https://uptimerobot.com/
2. Add New Monitor:
   - Monitor Type: HTTP(s)
   - URL: `https://api.seudominio.com/health`
   - Monitoring Interval: 5 minutes
   - Alert Contacts: seu-email@exemplo.com

3. Adicionar monitor para frontend:
   - URL: `https://seudominio.com`

4. Configurar alertas:
   - Email
   - SMS (opcional)
   - Slack/Discord (webhook)

**Benefícios**:
- Detecta downtime em 5 minutos
- Histórico de uptime 30 dias
- Status page público (opcional)

### 2.2 Sentry (Error Tracking)

**Backend Setup**:

1. Criar conta: https://sentry.io/signup/
2. Criar projeto: Python
3. Instalar SDK:
   ```bash
   pip install sentry-sdk[fastapi]
   ```

4. Configurar em `api/api_server.py`:
   ```python
   import sentry_sdk
   from sentry_sdk.integrations.fastapi import FastApiIntegration

   sentry_sdk.init(
       dsn=os.getenv('SENTRY_DSN'),
       environment=os.getenv('ENVIRONMENT', 'production'),
       traces_sample_rate=0.1,  # 10% das transações
       integrations=[FastApiIntegration()],
   )
   ```

5. Adicionar ao `.env.production`:
   ```env
   SENTRY_DSN=https://***@sentry.io/***
   ```

**Frontend Setup**:

1. Criar projeto: JavaScript → Next.js
2. Instalar SDK:
   ```bash
   npm install @sentry/nextjs
   ```

3. Executar wizard:
   ```bash
   npx @sentry/wizard@latest -i nextjs
   ```

4. Configurar env em Vercel:
   ```env
   NEXT_PUBLIC_SENTRY_DSN=https://***@sentry.io/***
   ```

**Benefícios**:
- Rastreamento de erros em tempo real
- Stack traces completos
- Contexto do usuário
- Alertas configuráveis

### 2.3 LogTail (Logs Centralizados)

**Setup**:

1. Criar conta: https://logtail.com/
2. Criar source: FastAPI
3. Instalar SDK:
   ```bash
   pip install logtail-python
   ```

4. Configurar em `api/api_server.py`:
   ```python
   from logtail import LogtailHandler
   import logging

   logger = logging.getLogger(__name__)

   if os.getenv('LOGTAIL_SOURCE_TOKEN'):
       handler = LogtailHandler(source_token=os.getenv('LOGTAIL_SOURCE_TOKEN'))
       logger.addHandler(handler)
   ```

5. Adicionar ao `.env.production`:
   ```env
   LOGTAIL_SOURCE_TOKEN=***
   ```

**Uso**:
```python
logger.info("Usuário criou conta", extra={
    'user_id': user.id,
    'email': user.email
})

logger.error("Erro ao processar pagamento", extra={
    'user_id': user.id,
    'amount': amount,
    'error': str(e)
})
```

**Benefícios**:
- Logs estruturados
- Busca avançada
- Alertas personalizados
- Retenção de 30 dias (free tier)

### 2.4 Google Analytics 4

**Setup**:

1. Criar conta: https://analytics.google.com/
2. Criar propriedade
3. Criar data stream (Web)
4. Copiar Measurement ID (G-***)

5. Adicionar ao frontend (`app/layout.tsx`):
   ```typescript
   import Script from 'next/script'

   export default function RootLayout({ children }) {
     return (
       <html>
         <head>
           <Script
             src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_ID}`}
             strategy="afterInteractive"
           />
           <Script id="google-analytics" strategy="afterInteractive">
             {`
               window.dataLayer = window.dataLayer || [];
               function gtag(){dataLayer.push(arguments);}
               gtag('js', new Date());
               gtag('config', '${process.env.NEXT_PUBLIC_GA_ID}');
             `}
           </Script>
         </head>
         <body>{children}</body>
       </html>
     )
   }
   ```

6. Adicionar ao Vercel:
   ```env
   NEXT_PUBLIC_GA_ID=G-***
   ```

**Métricas importantes**:
- Usuários ativos
- Taxa de conversão (cadastro → pagamento)
- Páginas mais visitadas
- Tempo médio de sessão
- Taxa de rejeição

---

## 📱 PARTE 3: Alertas Inteligentes

### 3.1 Configurar Alertas Críticos

**Eventos que devem gerar alerta IMEDIATO**:
- 🚨 API fora do ar (downtime)
- 🚨 Taxa de erro > 5%
- 🚨 Banco de dados fora do ar
- 🚨 Pagamento webhook falhando
- 🚨 CPU > 90% por 5min

**Eventos que devem gerar alerta em 15min**:
- ⚠️ Tempo de resposta > 2s
- ⚠️ Disco > 80%
- ⚠️ Taxa de erro > 1%
- ⚠️ Memória > 85%

**Canais de alerta**:
1. **Crítico**: SMS + Email + Slack
2. **Alto**: Email + Slack
3. **Médio**: Slack
4. **Baixo**: Dashboard apenas

### 3.2 Exemplo de Configuração Slack

1. Criar Incoming Webhook:
   - Slack → Apps → Incoming Webhooks
   - Add to Slack
   - Escolher canal (#alerts)
   - Copiar Webhook URL

2. Configurar em cada ferramenta:
   - UptimeRobot: Integrations → Slack
   - Sentry: Settings → Integrations → Slack
   - LogTail: Settings → Alerts → Slack

3. Testar:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"🚨 Teste de alerta!"}' \
     YOUR_WEBHOOK_URL
   ```

---

## 📊 PARTE 4: Dashboards

### 4.1 Dashboard de Infraestrutura

**Métricas**:
- Uptime última hora/dia/semana
- Tempo de resposta médio
- Requisições por minuto
- Taxa de erro (4xx, 5xx)
- CPU/RAM usage
- Conexões DB ativas

**Ferramenta**: Grafana (free, self-hosted)

### 4.2 Dashboard de Negócio

**Métricas**:
- Novos usuários/dia
- Conversão cadastro → pagamento
- MRR (Monthly Recurring Revenue)
- Churn rate
- LTV (Lifetime Value)
- Sessões de estudo/dia

**Ferramenta**: Google Analytics 4 + Google Data Studio

### 4.3 Dashboard Stripe

**Acessar**: https://dashboard.stripe.com/

**Métricas importantes**:
- Volume de transações
- Taxa de sucesso de pagamentos
- Chargebacks
- Novos assinantes
- Cancelamentos

---

## 🔍 PARTE 5: Logs Estruturados

### 5.1 Formato de Logs

**Padrão JSON**:
```json
{
  "timestamp": "2025-12-28T10:30:00Z",
  "level": "INFO",
  "service": "api",
  "endpoint": "/estudo/iniciar",
  "method": "POST",
  "user_id": "uuid",
  "duration_ms": 245,
  "status_code": 200,
  "message": "Sessão de estudo iniciada com sucesso"
}
```

### 5.2 Implementar no Backend

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'service': 'api',
            'message': record.getMessage(),
        }

        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data)

# Configurar
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### 5.3 Níveis de Log

**DEBUG**: Informação detalhada para debugging
```python
logger.debug("Query executada", extra={'query': sql, 'params': params})
```

**INFO**: Eventos importantes do sistema
```python
logger.info("Usuário criou conta", extra={'user_id': user.id})
```

**WARNING**: Situações incomuns mas não críticas
```python
logger.warning("Limite de sessões quase atingido", extra={'user_id': user.id, 'usado': 4, 'limite': 5})
```

**ERROR**: Erros que precisam atenção
```python
logger.error("Falha ao processar pagamento", extra={'user_id': user.id, 'error': str(e)})
```

**CRITICAL**: Sistema comprometido
```python
logger.critical("Banco de dados inacessível", extra={'error': str(e)})
```

---

## 🎯 PARTE 6: Métricas de Performance

### 6.1 Backend Performance

**Endpoint /health**:
```python
@app.get("/health")
async def health_check():
    start = time.time()

    # Verificar DB
    try:
        db.execute("SELECT 1")
        db_status = "healthy"
    except:
        db_status = "unhealthy"

    # Verificar Stripe
    try:
        stripe.Account.retrieve()
        stripe_status = "healthy"
    except:
        stripe_status = "unhealthy"

    duration = (time.time() - start) * 1000

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_status,
            "stripe": stripe_status
        },
        "duration_ms": round(duration, 2)
    }
```

### 6.2 Frontend Performance

**Core Web Vitals**:
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

**Monitorar**: Vercel Analytics → Speed Insights

---

## 📞 PARTE 7: Suporte e Escalação

### 7.1 Níveis de Severidade

**P0 - Crítico** (resolver em < 1h):
- Sistema fora do ar
- Pagamentos não funcionam
- Perda de dados

**P1 - Alto** (resolver em < 4h):
- Funcionalidade principal quebrada
- Performance degradada (> 5s)

**P2 - Médio** (resolver em < 24h):
- Bug em feature secundária
- UX ruim

**P3 - Baixo** (resolver em < 1 semana):
- Melhoria de feature
- Bug cosmético

### 7.2 Runbook para Incidentes

**Passos**:
1. **Detectar**: Alerta recebido
2. **Investigar**: Verificar logs, métricas
3. **Comunicar**: Avisar equipe e usuários (se necessário)
4. **Resolver**: Aplicar fix
5. **Verificar**: Confirmar que problema foi resolvido
6. **Documentar**: Post-mortem

**Template de Post-Mortem**:
```markdown
# Incidente: [Título]
Data: 2025-12-28
Duração: 30 minutos
Severidade: P0

## O que aconteceu?
[Descrição do problema]

## Impacto
- X usuários afetados
- Y transações perdidas
- Z% de downtime

## Causa Raiz
[Análise técnica]

## Resolução
[O que foi feito]

## Prevenção Futura
- [ ] Adicionar alerta para detectar antes
- [ ] Melhorar teste automatizado
- [ ] Documentar runbook
```

---

## ✅ Checklist de Monitoramento

- [ ] UptimeRobot configurado (API + Frontend)
- [ ] Sentry configurado (Backend + Frontend)
- [ ] Logs estruturados implementados
- [ ] Google Analytics 4 ativo
- [ ] Alertas Slack configurados
- [ ] Dashboard de métricas criado
- [ ] Health check endpoint testado
- [ ] Runbook de incidentes documentado
- [ ] Equipe treinada em procedimentos

---

## 🎓 Recursos Adicionais

- [Railway Monitoring Guide](https://docs.railway.app/reference/monitoring)
- [Vercel Analytics Docs](https://vercel.com/docs/analytics)
- [Sentry Best Practices](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Stripe Monitoring](https://stripe.com/docs/monitoring)

---

**Monitoramento não é opcional - é essencial para um sistema em produção!** 📊
