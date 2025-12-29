# Testes de Performance e Carga

**Data**: 28/12/2025
**Objetivo**: Garantir que o sistema suporte carga de produção e tenha performance otimizada

---

## 📊 Métricas Alvo

### Frontend (Lighthouse)
- **Performance Score**: ≥ 90
- **First Contentful Paint (FCP)**: < 2.0s
- **Largest Contentful Paint (LCP)**: < 2.5s
- **Cumulative Layout Shift (CLS)**: < 0.1
- **Total Blocking Time (TBT)**: < 300ms
- **Speed Index**: < 3.0s
- **Time to Interactive (TTI)**: < 3.5s

### Backend (API)
- **Response Time (p95)**: < 500ms
- **Response Time (p99)**: < 1000ms
- **Throughput**: > 100 req/s
- **Error Rate**: < 1%
- **Uptime**: > 99.9%

### Database
- **Query Time (p95)**: < 100ms
- **Connection Pool**: 20-50 connections
- **CPU Usage**: < 70%
- **Memory Usage**: < 80%

---

## 🚀 1. Lighthouse CI (Frontend Performance)

### Instalação

```bash
cd D:\doutora-ia-oab-frontend

npm install -D @lhci/cli webpack-bundle-analyzer
```

### Configuração

Arquivo criado: `.lighthouserc.js`

### Executar Testes

```bash
# Build do projeto
npm run build

# Rodar Lighthouse CI
npx lhci autorun

# Com análise de bundle
ANALYZE=true npm run build
```

### Interpretar Resultados

**Performance Score: 90-100** ✅ Excelente
- FCP < 1.8s
- LCP < 2.5s
- CLS < 0.1

**Performance Score: 50-89** ⚠️ Precisa melhorar
- Identificar gargalos
- Otimizar imagens
- Code splitting

**Performance Score: 0-49** ❌ Crítico
- Revisar arquitetura
- Lazy loading obrigatório
- CDN necessário

### Otimizações Implementadas

**next.config.js**:
- ✅ Compression habilitado
- ✅ Image optimization (AVIF, WebP)
- ✅ Font optimization
- ✅ Remove console.log em produção
- ✅ Security headers
- ✅ CSP (Content Security Policy)
- ✅ Cache headers
- ✅ Bundle analyzer
- ✅ Optimize CSS
- ✅ Optimize package imports

**Checklist de Otimizações**:
- [ ] Imagens otimizadas (< 100KB cada)
- [ ] Lazy loading de componentes pesados
- [ ] Dynamic imports onde aplicável
- [ ] Tree shaking configurado
- [ ] Fonts otimizados (Google Fonts com display=swap)
- [ ] Code splitting por rota
- [ ] Prefetch de rotas críticas
- [ ] Service Worker (PWA) - opcional

---

## 🔥 2. Testes de Carga (Stress Test)

### 2.1. Artillery (Backend API)

#### Instalação

```bash
npm install -g artillery
```

#### Configuração

**Arquivo**: `D:\JURIS_IA_CORE_V1\artillery-config.yml`

```yaml
config:
  target: "http://localhost:8000"
  phases:
    # Warmup: 10 usuários por 30s
    - duration: 30
      arrivalRate: 10
      name: "Warmup"

    # Ramp up: 10 → 50 usuários em 2 min
    - duration: 120
      arrivalRate: 10
      rampTo: 50
      name: "Ramp up"

    # Sustained load: 50 usuários por 5 min
    - duration: 300
      arrivalRate: 50
      name: "Sustained load"

    # Spike: 100 usuários por 1 min
    - duration: 60
      arrivalRate: 100
      name: "Spike test"

  # Timeouts
  timeout: 30
  processor: "./artillery-processor.js"

scenarios:
  # Cenário 1: Health Check
  - name: "Health Check"
    weight: 10
    flow:
      - get:
          url: "/health"

  # Cenário 2: Login
  - name: "Login Flow"
    weight: 30
    flow:
      - post:
          url: "/admin/login"
          json:
            email: "teste@example.com"
            password: "senha123"
          capture:
            - json: "$.data.token"
              as: "authToken"

  # Cenário 3: Dashboard (autenticado)
  - name: "Dashboard Load"
    weight: 20
    flow:
      - post:
          url: "/admin/login"
          json:
            email: "teste@example.com"
            password: "senha123"
          capture:
            - json: "$.data.token"
              as: "authToken"
      - get:
          url: "/estudante/painel"
          headers:
            Authorization: "Bearer {{ authToken }}"

  # Cenário 4: Iniciar Estudo
  - name: "Study Session"
    weight: 25
    flow:
      - post:
          url: "/admin/login"
          json:
            email: "teste@example.com"
            password: "senha123"
          capture:
            - json: "$.data.token"
              as: "authToken"
      - post:
          url: "/estudo/iniciar"
          headers:
            Authorization: "Bearer {{ authToken }}"
          json:
            modo: "adaptativo"

  # Cenário 5: Gamificação
  - name: "Gamification Data"
    weight: 15
    flow:
      - post:
          url: "/admin/login"
          json:
            email: "teste@example.com"
            password: "senha123"
          capture:
            - json: "$.data.token"
              as: "authToken"
            - json: "$.data.user.id"
              as: "userId"
      - get:
          url: "/gamificacao/{{ userId }}"
          headers:
            Authorization: "Bearer {{ authToken }}"
```

#### Executar Testes

```bash
# Teste básico
artillery run artillery-config.yml

# Gerar relatório HTML
artillery run artillery-config.yml --output report.json
artillery report report.json

# Teste rápido (quick smoke test)
artillery quick --count 10 --num 100 http://localhost:8000/health
```

#### Interpretar Resultados

```
Summary report @ 15:30:45(+0000)
  Scenarios launched:  1500
  Scenarios completed: 1500
  Requests completed:  4500
  Mean response/sec: 75
  Response time (msec):
    min: 12
    max: 523
    median: 45
    p95: 250   ← Objetivo: < 500ms
    p99: 480   ← Objetivo: < 1000ms
  Scenario counts:
    Login Flow: 450 (30%)
    Dashboard Load: 300 (20%)
    Study Session: 375 (25%)
  Codes:
    200: 4450 (98.9%)
    500: 50 (1.1%)   ← Objetivo: < 1%
```

**Análise**:
- ✅ **p95 < 500ms**: Excelente
- ✅ **p99 < 1000ms**: Dentro do esperado
- ⚠️ **Error rate 1.1%**: Investigar logs de erro 500

---

### 2.2. Locust (Python - Alternativa)

#### Instalação

```bash
pip install locust
```

#### Configuração

**Arquivo**: `D:\JURIS_IA_CORE_V1\locustfile.py`

```python
from locust import HttpUser, task, between
import random

class JurisIAUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Login ao iniciar"""
        response = self.client.post("/admin/login", json={
            "email": "teste@example.com",
            "password": "senha123"
        })
        if response.status_code == 200:
            self.token = response.json()['data']['token']
            self.user_id = response.json()['data']['user']['id']

    @task(1)
    def health_check(self):
        """Health check"""
        self.client.get("/health")

    @task(3)
    def get_painel(self):
        """Carregar painel"""
        if self.token:
            self.client.get("/estudante/painel", headers={
                "Authorization": f"Bearer {self.token}"
            })

    @task(2)
    def iniciar_estudo(self):
        """Iniciar sessão de estudo"""
        if self.token:
            self.client.post("/estudo/iniciar", headers={
                "Authorization": f"Bearer {self.token}"
            }, json={
                "modo": "adaptativo"
            })

    @task(2)
    def get_gamificacao(self):
        """Buscar dados de gamificação"""
        if self.token and self.user_id:
            self.client.get(f"/gamificacao/{self.user_id}", headers={
                "Authorization": f"Bearer {self.token}"
            })

    @task(1)
    def get_conquistas(self):
        """Listar conquistas"""
        if self.token:
            self.client.get("/gamificacao/conquistas")
```

#### Executar Testes

```bash
# Web UI (recomendado)
locust -f locustfile.py --host=http://localhost:8000

# Abrir http://localhost:8089
# Configurar: 100 users, spawn rate 10/s

# Headless (CI/CD)
locust -f locustfile.py --host=http://localhost:8000 \
       --users 100 --spawn-rate 10 --run-time 5m --headless
```

---

### 2.3. K6 (Go-based - Recomendado para CI/CD)

#### Instalação

```bash
# Windows (Chocolatey)
choco install k6

# Linux
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

#### Configuração

**Arquivo**: `D:\JURIS_IA_CORE_V1\k6-load-test.js`

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Warmup
    { duration: '2m', target: 50 },    // Ramp up
    { duration: '5m', target: 50 },    // Sustained
    { duration: '1m', target: 100 },   // Spike
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'], // < 1% de erros
    errors: ['rate<0.01'],
  },
};

const BASE_URL = 'http://localhost:8000';

export default function () {
  // Login
  const loginRes = http.post(`${BASE_URL}/admin/login`, JSON.stringify({
    email: 'teste@example.com',
    password: 'senha123',
  }), {
    headers: { 'Content-Type': 'application/json' },
  });

  check(loginRes, {
    'login status 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  if (loginRes.status !== 200) return;

  const token = loginRes.json('data.token');
  const userId = loginRes.json('data.user.id');
  const headers = { Authorization: `Bearer ${token}` };

  sleep(1);

  // Dashboard
  const painelRes = http.get(`${BASE_URL}/estudante/painel`, { headers });
  check(painelRes, {
    'painel status 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);

  // Iniciar estudo
  const estudoRes = http.post(
    `${BASE_URL}/estudo/iniciar`,
    JSON.stringify({ modo: 'adaptativo' }),
    { headers: { ...headers, 'Content-Type': 'application/json' } }
  );
  check(estudoRes, {
    'estudo status 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(2);

  // Gamificação
  const gamifRes = http.get(`${BASE_URL}/gamificacao/${userId}`, { headers });
  check(gamifRes, {
    'gamificacao status 200': (r) => r.status === 200,
  }) || errorRate.add(1);

  sleep(1);
}
```

#### Executar Testes

```bash
# Rodar teste
k6 run k6-load-test.js

# Com output para InfluxDB (monitoramento)
k6 run --out influxdb=http://localhost:8086/k6 k6-load-test.js

# Cloud (K6 Cloud)
k6 cloud k6-load-test.js
```

---

## 🗄️ 3. Testes de Banco de Dados

### 3.1. pgbench (PostgreSQL)

```bash
# Inicializar banco de testes
pgbench -i -s 50 juris_ia_test

# Teste simples (10 clientes, 100 transações cada)
pgbench -c 10 -t 100 juris_ia_test

# Teste de 5 minutos (50 clientes)
pgbench -c 50 -T 300 juris_ia_test

# Teste com script customizado
pgbench -c 20 -T 60 -f custom-queries.sql juris_ia_test
```

**custom-queries.sql**:
```sql
-- Simular query do painel
SELECT
  e.nome,
  COUNT(DISTINCT sh.id) as sessoes,
  COUNT(DISTINCT rq.id) as questoes,
  ROUND(AVG(CASE WHEN rq.acertou THEN 100 ELSE 0 END), 2) as aproveitamento
FROM usuarios e
LEFT JOIN sessao_historico sh ON e.id = sh.estudante_id
LEFT JOIN respostas_questoes rq ON sh.id = rq.sessao_id
WHERE e.id = random_between(1, 1000)
GROUP BY e.id, e.nome;
```

### 3.2. Monitorar Queries Lentas

```sql
-- Habilitar log de queries lentas (PostgreSQL)
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1 segundo
SELECT pg_reload_conf();

-- Ver queries mais lentas
SELECT
  query,
  calls,
  total_time,
  mean_time,
  max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Identificar queries sem index
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY relname;
```

---

## 📈 4. Monitoramento em Produção

### 4.1. APM (Application Performance Monitoring)

**Opções**:
- **Sentry** (error tracking + performance)
- **New Relic** (APM completo)
- **Datadog** (infraestrutura + APM)
- **Prometheus + Grafana** (open source)

### 4.2. Métricas Essenciais

**Backend**:
```python
# Instrumentação com Prometheus
from prometheus_client import Counter, Histogram, Gauge
import time

REQUEST_COUNT = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'Request duration', ['endpoint'])
ACTIVE_SESSIONS = Gauge('active_study_sessions', 'Active study sessions')

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.labels(endpoint=request.url.path).observe(duration)

    return response
```

**Frontend** (Web Vitals):
```typescript
// lib/analytics.ts
import { getCLS, getFID, getFCP, getLCP, getTTFB } from 'web-vitals';

export function reportWebVitals() {
  getCLS(sendToAnalytics);
  getFID(sendToAnalytics);
  getFCP(sendToAnalytics);
  getLCP(sendToAnalytics);
  getTTFB(sendToAnalytics);
}

function sendToAnalytics(metric: any) {
  // Enviar para Google Analytics
  if (window.gtag) {
    window.gtag('event', metric.name, {
      value: Math.round(metric.value),
      event_category: 'Web Vitals',
      event_label: metric.id,
      non_interaction: true,
    });
  }

  // Enviar para backend
  fetch('/api/metrics', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metric),
  });
}
```

---

## ✅ Checklist de Testes

### Antes de Lançar

- [ ] Lighthouse score > 90 em todas as páginas principais
- [ ] Teste de carga com 100 usuários simultâneos (sem erros)
- [ ] p95 response time < 500ms
- [ ] Database queries otimizadas (< 100ms)
- [ ] Images otimizadas (< 100KB cada)
- [ ] Bundle size < 300KB (gzipped)
- [ ] Security headers configurados
- [ ] CSP (Content Security Policy) ativo
- [ ] Rate limiting funcionando
- [ ] Error tracking configurado (Sentry)
- [ ] Monitoramento ativo (uptime, performance)

### Pós-Lançamento (Primeira Semana)

- [ ] Monitorar p95/p99 response times
- [ ] Verificar error rate < 1%
- [ ] Analisar Web Vitals (CLS, LCP, FID)
- [ ] Revisar logs de erros
- [ ] Validar taxa de conversão
- [ ] Acompanhar feedback de usuários

---

## 🚨 Troubleshooting

### Performance Ruim (<60 score)

**Causas Comuns**:
1. Imagens muito grandes
2. JavaScript bundle gigante
3. Fonts não otimizados
4. Muitas requisições HTTP
5. Sem cache

**Soluções**:
1. Comprimir imagens (TinyPNG, Squoosh)
2. Code splitting + lazy loading
3. Google Fonts com `display=swap`
4. HTTP/2, combinar assets
5. Configurar cache headers

### API Lenta (>1s p95)

**Causas Comuns**:
1. Queries N+1
2. Falta de índices
3. Serialização lenta
4. Conexões de DB esgotadas

**Soluções**:
1. Eager loading, JOIN
2. CREATE INDEX
3. Otimizar serializers
4. Aumentar connection pool

### Database CPU Alto (>80%)

**Causas Comuns**:
1. Queries sem índice
2. Full table scans
3. Falta de VACUUM

**Soluções**:
```sql
-- Analisar query plan
EXPLAIN ANALYZE SELECT ...;

-- Criar índices
CREATE INDEX idx_name ON table(column);

-- VACUUM
VACUUM ANALYZE;
```

---

**Próximo**: Implementar otimizações e executar testes!
