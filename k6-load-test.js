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
