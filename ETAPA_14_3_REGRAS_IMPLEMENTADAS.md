# ETAPA 14.3 - REGRAS DE SESSÃO LONGA E ESTUDO CONTÍNUO

**Data:** 2025-12-19
**Status:** ✅ CONCLU�DA COM SUCESSO

## Objetivo

Implementar as regras técnicas para:
1. Sessões longas que não consomem múltiplas sessões (Plano Semestral)
2. Modo de estudo contínuo que não conta no limite diário (Planos Mensal e Semestral)
3. Sessões extras condicionais para heavy users (Plano Semestral)

---

## Implementações Realizadas

### 1. Migration 009 - Campos de Sessão Especial

**Arquivo:** `database/migrations/009_adicionar_campos_sessao_especial.sql`

**Novos campos na tabela `sessao_estudo`:**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `modo_estudo_continuo` | BOOLEAN | Se true, é uma sessão de revisão que não consome limite diário |
| `sessao_estendida` | BOOLEAN | Se true, é uma sessão longa que não conta como múltiplas sessões |
| `sessao_principal_id` | UUID | FK para a sessão principal (quando em modo estudo contínuo) |
| `conta_limite_diario` | BOOLEAN | Se true, conta no limite diário de sessões |

**Índices criados:**
- `idx_sessao_principal`: Para buscar sessões relacionadas
- `idx_sessao_conta_limite`: Para filtrar sessões que contam no limite

---

### 2. Migration 010 - Funções de Controle

**Arquivo:** `database/migrations/010_funcoes_controle_sessao_v2.sql`

#### Função: `pode_iniciar_sessao(user_id, modo_estudo_continuo)`

**Retorna:**
```sql
TABLE(
    pode_iniciar BOOLEAN,
    motivo TEXT,
    sessoes_usadas INTEGER,
    sessoes_disponiveis INTEGER
)
```

**Lógica:**
1. Se não tem assinatura ativa → Nega com mensagem
2. Se `modo_estudo_continuo = true` E plano permite → Sempre permite (não conta limite)
3. Se `modo_estudo_continuo = true` E plano NÃO permite → Nega com mensagem de upgrade
4. Conta sessões do dia que `conta_limite_diario = true`
5. Se ultrapassou `limite_sessoes_dia + sessoes_extras_condicionais` → Nega com mensagem pedagógica
6. Caso contrário → Permite

**Mensagens pedagógicas (não financeiras):**
- ✅ "Estudo contínuo permitido (não conta no limite)"
- ❌ "Limite de sessões diárias atingido. Continue amanhã ou estude conteúdo teórico!"
- ❌ "Seu plano não permite estudo contínuo. Faça upgrade!"

#### Função: `estatisticas_uso_diario(user_id, data)`

**Retorna:**
```sql
TABLE(
    sessoes_total INTEGER,
    sessoes_que_contam INTEGER,
    sessoes_estudo_continuo INTEGER,
    questoes_total INTEGER,
    limite_sessoes INTEGER,
    limite_questoes INTEGER,
    sessoes_disponiveis INTEGER,
    questoes_disponiveis INTEGER,
    permite_estudo_continuo BOOLEAN,
    permite_sessao_estendida BOOLEAN
)
```

**Uso:** Dashboard do usuário e controle de limites em tempo real

---

## Regras de Negócio Implementadas

### Regra 1: Estudo Contínuo (Mensal e Semestral)

**Quando aplicar:**
- Usuário completou uma sessão de questões
- Quer revisar erros ou estudar teoria relacionada
- Plano permite estudo contínuo (`permite_estudo_continuo = true`)

**Como funciona:**
1. Backend chama `pode_iniciar_sessao(user_id, modo_estudo_continuo=true)`
2. Se permitido, cria sessão com:
   - `modo_estudo_continuo = true`
   - `conta_limite_diario = false`
   - `sessao_principal_id = <id da sessão anterior>`
3. Sessão NÃO conta no limite diário
4. Usuário pode revisar, ler lei seca, assistir vídeos teóricos

**Planos que permitem:**
- ❌ FREE: Não permite
- ✅ OAB MENSAL: Permite
- ✅ OAB SEMESTRAL: Permite

---

### Regra 2: Sessão Estendida (Apenas Semestral)

**Quando aplicar:**
- Usuário está em uma sessão que ultrapassou `duracao_maxima_sessao_minutos`
- Plano permite sessão estendida (`permite_sessao_estendida = true`)

**Como funciona:**
1. Backend monitora duração da sessão em tempo real
2. Se `duracao > duracao_maxima_sessao_minutos`:
   - Marca `sessao_estendida = true`
   - Sessão CONTINUA contando como 1 sessão apenas
   - Não incrementa contador de sessões
3. Usuário pode estudar 3h seguidas contando como 1 sessão

**Exemplo prático:**
- Plano Semestral: limite = 180min (3h)
- Usuário estuda por 4h ininterruptas
- Sistema marca `sessao_estendida = true`
- Conta como 1 sessão, não 2

**Planos que permitem:**
- ❌ FREE: Não permite (30min hard limit)
- ❌ OAB MENSAL: Não permite (90min hard limit)
- ✅ OAB SEMESTRAL: Permite (180min soft limit)

---

### Regra 3: Sessões Extras Condicionais (Heavy Users - Semestral)

**Quando aplicar:**
- Usuário é "heavy user" (usou 80%+ do limite nos últimos 7 dias)
- Já atingiu limite padrão do dia
- Plano tem `sessoes_extras_condicionais > 0`

**Como funciona:**
1. Sistema detecta que usuário atingiu limite diário
2. Verifica uso dos últimos 7 dias
3. Se `sessoes_7dias >= (limite_sessoes_dia * 7 * 0.8)`:
   - Libera automaticamente +1 sessão extra
   - Mensagem: "Heavy user! Sessão extra liberada por uso consistente."
4. Sessão extra conta normalmente (`conta_limite_diario = true`)

**Exemplo:**
- Plano Semestral: 5 sessões/dia
- Heavy user = 28+ sessões nos últimos 7 dias (80% de 35)
- Usuário faz 5 sessões num dia → sistema libera 6ª sessão automaticamente

**Planos que permitem:**
- ❌ FREE: 0 sessões extras
- ❌ OAB MENSAL: 0 sessões extras
- ✅ OAB SEMESTRAL: +1 sessão extra condicional

---

## Fluxo de Uso no Backend

### 1. Iniciar Nova Sessão

```typescript
// Verificar se pode iniciar
const permissao = await db.pode_iniciar_sessao(userId, false);

if (!permissao.pode_iniciar) {
    return {
        error: permissao.motivo,
        sessoes_usadas: permissao.sessoes_usadas,
        sessoes_disponiveis: permissao.sessoes_disponiveis
    };
}

// Criar sessão
const sessao = await db.sessao_estudo.create({
    user_id: userId,
    tipo: 'questoes',
    conta_limite_diario: true,  // Conta no limite
    modo_estudo_continuo: false,
    // ... outros campos
});
```

### 2. Iniciar Estudo Contínuo

```typescript
// Usuário acabou de finalizar uma sessão e quer revisar erros
const sessaoPrincipalId = ultimaSessaoId;

// Verificar se pode estudo contínuo
const permissao = await db.pode_iniciar_sessao(userId, true);  // modo_estudo_continuo = true

if (!permissao.pode_iniciar) {
    return { error: permissao.motivo };  // "Seu plano não permite..."
}

// Criar sessão de estudo contínuo
const sessao = await db.sessao_estudo.create({
    user_id: userId,
    tipo: 'revisao',
    conta_limite_diario: false,  // NÃO conta no limite
    modo_estudo_continuo: true,
    sessao_principal_id: sessaoPrincipalId,
    // ... outros campos
});
```

### 3. Monitorar Sessão Estendida

```typescript
// Durante a sessão, a cada 5 minutos
const duracao = calcularDuracaoMinutos(sessao.iniciado_em);
const limiteMaximo = plano.duracao_maxima_sessao_minutos;

if (duracao > limiteMaximo && plano.permite_sessao_estendida && !sessao.sessao_estendida) {
    // Marcar como estendida
    await db.sessao_estudo.update({
        where: { id: sessaoId },
        data: { sessao_estendida: true }
    });

    console.log('Sessão marcada como estendida - não consome sessão adicional');
}
```

### 4. Dashboard - Mostrar Estatísticas

```typescript
// Obter estatísticas para dashboard
const stats = await db.estatisticas_uso_diario(userId);

return {
    hoje: {
        sessoes: `${stats.sessoes_que_contam}/${stats.limite_sessoes}`,
        sessoes_estudo_continuo: stats.sessoes_estudo_continuo,
        questoes: `${stats.questoes_total}/${stats.limite_questoes}`,
        sessoes_disponiveis: stats.sessoes_disponiveis,
        questoes_disponiveis: stats.questoes_disponiveis
    },
    plano: {
        permite_estudo_continuo: stats.permite_estudo_continuo,
        permite_sessao_estendida: stats.permite_sessao_estendida
    }
};
```

---

## Mensagens ao Usuário (Pedagógicas)

### Quando permite

| Situação | Mensagem |
|----------|----------|
| Sessão normal | "Sessão iniciada! Você tem X questões disponíveis" |
| Estudo contínuo | "Modo revisão ativado! Estude sem limite de tempo" |
| Sessão estendida | "Continue estudando! Esta sessão não conta como adicional" |
| Heavy user extra | "Parabéns pelo uso consistente! +1 sessão extra liberada" |

### Quando bloqueia

| Situação | Mensagem |
|----------|----------|
| Limite atingido (FREE) | "Limite diário atingido! Continue amanhã ou faça upgrade para mais sessões" |
| Limite atingido (Mensal/Semestral) | "Limite de sessões diárias atingido. Continue amanhã ou estude conteúdo teórico!" |
| Estudo contínuo bloqueado | "Seu plano não permite modo revisão ilimitado. Faça upgrade!" |

**Importante:** Mensagens focam em pedagogia e hábitos de estudo, não em dinheiro ou pagamento.

---

## Diferenças Entre Planos

### FREE
- ❌ Não permite estudo contínuo
- ❌ Não permite sessão estendida
- ❌ 0 sessões extras
- **Hard limits:** 1 sessão/dia, 30min

### OAB MENSAL
- ✅ Permite estudo contínuo
- ❌ Não permite sessão estendida
- ❌ 0 sessões extras
- **Limits:** 3 sessões/dia, 90min cada

### OAB SEMESTRAL (PLANO ÂNCORA)
- ✅ Permite estudo contínuo
- ✅ Permite sessão estendida
- ✅ +1 sessão extra para heavy users
- **Soft limits:** 5 sessões/dia, 180min (pode estender)

---

## Casos de Uso

### Caso 1: Usuário FREE tenta revisar erros

```
User: "Quero revisar os erros da última sessão"
System: Chama pode_iniciar_sessao(user_id, modo_estudo_continuo=true)
Result: pode_iniciar = false, motivo = "Seu plano não permite estudo contínuo. Faça upgrade!"
UI: Mostra mensagem + botão "Fazer Upgrade"
```

### Caso 2: Usuário MENSAL revisa erros

```
User: "Quero revisar os erros da última sessão"
System: Chama pode_iniciar_sessao(user_id, modo_estudo_continuo=true)
Result: pode_iniciar = true, motivo = "Estudo contínuo permitido (não conta no limite)"
System: Cria sessão com modo_estudo_continuo=true, conta_limite_diario=false
UI: Mostra interface de revisão ilimitada
```

### Caso 3: Usuário SEMESTRAL estuda 4h seguidas

```
13:00 - Inicia sessão de questões
14:00 - Sistema monitora: duracao = 60min < 180min → OK
15:00 - Sistema monitora: duracao = 120min < 180min → OK
16:00 - Sistema monitora: duracao = 180min = 180min → OK
17:00 - Sistema monitora: duracao = 240min > 180min
       - Marca sessao_estendida = true
       - Log: "Sessão estendida ativada"
       - Não incrementa contador de sessões
UI: Usuário continua estudando normalmente
```

### Caso 4: Heavy user do SEMESTRAL atingiu limite

```
User fez 5 sessões hoje (limite = 5)
System verifica: sessoes_7dias = 32 (>= 28 = 80% de 35)
System: Heavy user detectado!
User tenta 6ª sessão:
- pode_iniciar_sessao retorna pode_iniciar = true
- motivo = "Heavy user! Sessão extra liberada por uso consistente."
System: Cria 6ª sessão normalmente
UI: Mostra badge "Heavy User" + mensagem de incentivo
```

---

## Testes Recomendados

### Teste 1: Estudo Contínuo FREE
```sql
-- Simular usuário FREE
SELECT * FROM pode_iniciar_sessao(
    '...user_id...',
    true  -- modo_estudo_continuo
);
-- Esperado: pode_iniciar = false, motivo contém "upgrade"
```

### Teste 2: Estudo Contínuo MENSAL
```sql
-- Simular usuário MENSAL
SELECT * FROM pode_iniciar_sessao(
    '...user_id...',
    true
);
-- Esperado: pode_iniciar = true, motivo contém "não conta no limite"
```

### Teste 3: Estatísticas
```sql
-- Ver estatísticas de um usuário
SELECT * FROM estatisticas_uso_diario('...user_id...');
-- Verificar todos os contadores
```

---

## Próximos Passos

✅ ETAPA 14.1 - Preços e planos definidos
✅ ETAPA 14.2 - Limites operacionais configurados
✅ ETAPA 14.3 - Regras de sessão implementadas
⏳ ETAPA 14.4 - Enforcement técnico e mensagens
⏳ ETAPA 14.5 - Heavy user escape valve
⏳ ETAPA 14.6 - A/B testing prep
⏳ ETAPA 14.7 - Relatório final

---

**Status Final:** ✅ ETAPA 14.3 CONCLUÍDA COM SUCESSO

Todas as regras de sessão longa e estudo contínuo foram implementadas no banco de dados.
Backend precisa integrar as funções SQL criadas nas APIs de sessão.
