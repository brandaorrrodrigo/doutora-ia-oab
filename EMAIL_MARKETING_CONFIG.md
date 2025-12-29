# Email Marketing - Drip Campaigns

**Data**: 28/12/2025
**Objetivo**: Configurar campanhas de email automatizadas para engajamento e conversão

---

## 📧 Overview

Sistema de email marketing com campanhas automatizadas (drip campaigns) usando SendGrid para:
- Boas-vindas a novos usuários
- Onboarding e primeiros passos
- Engajamento e reativação
- Conversão de plano gratuito para pago
- Retenção de assinantes

---

## 📋 Campanhas Configuradas

### 1. **Campanha de Boas-Vindas** (3 emails)

#### Email 1: Boas-vindas Imediato
- **Trigger**: Cadastro confirmado
- **Delay**: Imediato
- **Assunto**: "Bem-vindo à Doutora IA OAB! 🎉"
- **Objetivo**: Confirmação e primeiro login

**Conteúdo**:
```
Olá {{nome}},

Seja muito bem-vindo à Doutora IA OAB! 🎓

Sua conta foi criada com sucesso. Agora você tem acesso a:

✅ 8.261 questões da OAB comentadas
✅ Sistema de estudo adaptativo com IA
✅ Simulados e revisão espaçada
✅ Sistema de gamificação com FP (Functional Points)

👉 COMECE AGORA: [Fazer Primeiro Login]

Dica: Complete seu perfil para personalizar ainda mais sua experiência!

--
Equipe Doutora IA OAB
Sua aprovação é nossa missão!
```

#### Email 2: Tutorial e Primeiros Passos
- **Trigger**: 1 dia após cadastro
- **Delay**: 24 horas
- **Assunto**: "Como aproveitar 100% da plataforma"
- **Objetivo**: Educação e engajamento

**Conteúdo**:
```
Olá {{nome}},

Já fez sua primeira sessão de estudo? Se não, não se preocupe!

Aqui estão 3 passos simples para começar:

1️⃣ **Inicie uma Sessão de Estudo**
   • Clique em "Iniciar Estudo" no dashboard
   • Responda 10 questões
   • Receba feedback imediato da IA

2️⃣ **Explore o Sistema de Gamificação**
   • Ganhe FP (Functional Points) estudando
   • Desbloqueie conquistas
   • Suba de nível

3️⃣ **Use a Revisão Espaçada**
   • Revisão científica baseada no SuperMemo
   • Melhore sua retenção em até 80%

👉 [Começar a Estudar Agora]

Dúvidas? Responda este email!

--
Equipe Doutora IA OAB
```

#### Email 3: Benefícios Premium
- **Trigger**: 3 dias após cadastro
- **Delay**: 72 horas
- **Assunto**: "Experimente Premium GRÁTIS por 7 dias 🎁"
- **Objetivo**: Conversão para plano pago

**Conteúdo**:
```
Olá {{nome}},

Você está aproveitando o plano Gratuito, mas sabia que pode fazer MUITO MAIS?

Com o **Plano Premium** (7 dias grátis):

✨ 15 sessões por dia (vs 5 no gratuito)
✨ 30 questões por sessão (vs 10)
✨ Chat ilimitado com IA jurídica
✨ Prática de peças processuais
✨ Relatórios avançados de desempenho
✨ Análise comparativa com outros estudantes

💰 Apenas R$ 49,90/mês após o teste grátis
🔒 Cancele quando quiser, sem compromisso

👉 [COMEÇAR TESTE GRÁTIS AGORA]

--
Equipe Doutora IA OAB
```

---

### 2. **Campanha de Engajamento** (4 emails)

#### Email 4: Estatísticas de Progresso
- **Trigger**: 7 dias de uso ativo
- **Delay**: Após 7 dias
- **Assunto**: "Seu progresso esta semana 📊"

**Conteúdo**:
```
Olá {{nome}},

Parabéns! Você completou 7 dias na plataforma! 🎉

📊 Seus números esta semana:
• Sessões realizadas: {{sessoes}}
• Questões respondidas: {{questoes}}
• Aproveitamento: {{aproveitamento}}%
• FP ganho: {{fp}}

{{#if aproveitamento > 70}}
🌟 Você está indo MUITO BEM! Continue assim!
{{else}}
💪 Continue praticando! A consistência é a chave!
{{/if}}

👉 [Ver Relatório Completo]

--
Equipe Doutora IA OAB
```

#### Email 5: Conquista Desbloqueada
- **Trigger**: Primeira conquista desbloqueada
- **Delay**: Imediato
- **Assunto**: "🏆 Parabéns! Você desbloqueou uma conquista"

**Conteúdo**:
```
🎉 CONQUISTA DESBLOQUEADA! 🎉

{{nome}}, você acaba de conquistar:

🏆 {{nome_conquista}}
{{descricao_conquista}}

+{{xp_recompensa}} FP ganhos!

Continue estudando para desbloquear mais conquistas e subir de nível!

👉 [Ver Todas as Conquistas]

--
Equipe Doutora IA OAB
```

#### Email 6: Lembrete de Streak
- **Trigger**: 3 dias sem atividade
- **Delay**: Após 72h de inatividade
- **Assunto**: "Sentimos sua falta! Não perca sua sequência 🔥"

**Conteúdo**:
```
Olá {{nome}},

Notamos que você não estuda há 3 dias... 😢

⚠️ Sua sequência de {{streak}} dias está em risco!

A consistência é FUNDAMENTAL para aprovação na OAB. Estudos mostram que:
• 30 minutos por dia é melhor que 3 horas em 1 dia
• Sequências longas aumentam retenção em 60%
• 95% dos aprovados estudaram todos os dias

👉 [Continuar Estudando Agora]

Não deixe para amanhã!

--
Equipe Doutora IA OAB
```

#### Email 7: Novo Conteúdo
- **Trigger**: Nova feature lançada
- **Delay**: Imediato (manual)
- **Assunto**: "🚀 Novidade: {{feature_name}}"

**Conteúdo**:
```
Olá {{nome}},

Temos uma NOVIDADE incrível para você!

🚀 {{feature_name}}

{{feature_description}}

Essa nova funcionalidade vai te ajudar a:
• {{beneficio_1}}
• {{beneficio_2}}
• {{beneficio_3}}

👉 [Experimentar Agora]

Esperamos seu feedback!

--
Equipe Doutora IA OAB
```

---

### 3. **Campanha de Conversão** (3 emails)

#### Email 8: Trial Ending (3 dias antes)
- **Trigger**: 4 dias após início do trial
- **Delay**: Trial day 4 de 7
- **Assunto**: "Seu teste grátis termina em 3 dias"

**Conteúdo**:
```
Olá {{nome}},

Seu teste grátis do Plano Premium termina em 3 dias.

Nos últimos dias você:
• Respondeu {{questoes}} questões
• Completou {{sessoes}} sessões
• Ganhou {{fp}} FP

Continue aproveitando até o final do teste!

Para manter todos esses benefícios, não precisa fazer nada - a renovação é automática.

Quer cancelar? Sem problemas! [Cancelar Assinatura]

--
Equipe Doutora IA OAB
```

#### Email 9: Trial Ending (1 dia antes)
- **Trigger**: 6 dias após início do trial
- **Delay**: Trial day 6 de 7
- **Assunto**: "⏰ Última chance de teste grátis"

**Conteúdo**:
```
Olá {{nome}},

Amanhã seu teste grátis termina!

Se você não fizer nada, sua assinatura Premium será renovada automaticamente por R$ 49,90/mês.

💳 Sua cobrança será processada em: {{data_cobranca}}

Deseja cancelar? [Cancelar Agora]
Deseja alterar o plano? [Ver Planos]

--
Equipe Doutora IA OAB
```

#### Email 10: Upgrade Incentivo
- **Trigger**: 30 dias no plano gratuito
- **Delay**: Após 30 dias
- **Assunto**: "Acelere sua aprovação com Premium"

**Conteúdo**:
```
Olá {{nome}},

Você está há 30 dias no plano Gratuito!

Veja o que você conseguiria com Premium:

📈 Seu progresso potencial:
Gratuito: 5 sessões/dia = 150 questões/mês
Premium: 15 sessões/dia = 450 questões/mês (+300%)

💡 Recursos Premium que você está perdendo:
• Chat IA para tirar dúvidas
• Prática de peças processuais
• Análise de desempenho avançada

🎁 OFERTA ESPECIAL: 7 dias grátis + 20% OFF no primeiro mês

👉 [GARANTIR DESCONTO AGORA]

Oferta válida por 48 horas!

--
Equipe Doutora IA OAB
```

---

### 4. **Campanha de Retenção** (2 emails)

#### Email 11: Churn Prevention
- **Trigger**: Cancelamento da assinatura
- **Delay**: Imediato
- **Assunto**: "Antes de ir, podemos ajudar? 💙"

**Conteúdo**:
```
Olá {{nome}},

Notamos que você cancelou sua assinatura Premium. 😢

Podemos saber o motivo? Sua opinião é muito importante!

[ ] Muito caro
[ ] Não estou usando o suficiente
[ ] Falta de funcionalidades
[ ] Problemas técnicos
[ ] Outro: _______________

👉 [Responder Pesquisa] (leva 30 segundos)

🎁 QUER FICAR? Ofertas especiais:
• 50% OFF nos próximos 3 meses
• Downgrade para plano básico
• Pausa temporária (até 60 dias)

👉 [Reativar com Desconto]

Sua assinatura permanece ativa até {{data_fim}}.

--
Equipe Doutora IA OAB
```

#### Email 12: Win-back
- **Trigger**: 30 dias após cancelamento
- **Delay**: 30 dias
- **Assunto**: "Sentimos sua falta! Volte com desconto 💚"

**Conteúdo**:
```
Olá {{nome}},

Você faz falta aqui na Doutora IA OAB!

Desde que você saiu, adicionamos:
• 2.000+ novas questões
• {{nova_feature_1}}
• {{nova_feature_2}}

🎁 OFERTA EXCLUSIVA DE RETORNO:
40% OFF nos primeiros 3 meses
De R$ 49,90 por apenas R$ 29,90/mês

👉 [VOLTAR COM DESCONTO]

Código: BEMDEVOLTA40
Válido até {{data_expiracao}}

Esperamos você de volta!

--
Equipe Doutora IA OAB
```

---

## 🛠️ Configuração no SendGrid

### 1. Criar Templates

```bash
# Acessar SendGrid Dashboard
https://app.sendgrid.com/

# Navegação:
Email API → Dynamic Templates → Create Template
```

### 2. Design de Template Base

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{subject}}</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
      line-height: 1.6;
      color: #333;
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f5f5f5;
    }
    .container {
      background-color: white;
      border-radius: 8px;
      padding: 40px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .header {
      text-align: center;
      margin-bottom: 30px;
    }
    .logo {
      font-size: 24px;
      font-weight: bold;
      color: #7c3aed;
    }
    .content {
      margin: 20px 0;
    }
    .cta-button {
      display: inline-block;
      background-color: #7c3aed;
      color: white !important;
      text-decoration: none;
      padding: 14px 28px;
      border-radius: 6px;
      font-weight: 600;
      margin: 20px 0;
      text-align: center;
    }
    .stats {
      background-color: #f3f4f6;
      border-radius: 8px;
      padding: 20px;
      margin: 20px 0;
    }
    .footer {
      text-align: center;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #e5e7eb;
      font-size: 12px;
      color: #6b7280;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="logo">⚖️ Doutora IA OAB</div>
    </div>

    <div class="content">
      {{{body}}}
    </div>

    <div class="footer">
      <p>
        Doutora IA OAB<br>
        suporte@doutoraia.com
      </p>
      <p>
        <a href="{{unsubscribe_url}}">Cancelar inscrição</a> |
        <a href="{{preferences_url}}">Preferências de email</a>
      </p>
    </div>
  </div>
</body>
</html>
```

### 3. Configurar Automações

**Arquivo**: `backend/services/email_campaigns.py`

```python
import sendgrid
from sendgrid.helpers.mail import Mail, Personalization
from datetime import datetime, timedelta
import os

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

# Template IDs (obter do SendGrid)
TEMPLATES = {
    'welcome': 'd-xxx-welcome',
    'tutorial': 'd-xxx-tutorial',
    'premium_offer': 'd-xxx-premium',
    'weekly_stats': 'd-xxx-stats',
    'achievement': 'd-xxx-achievement',
    'streak_reminder': 'd-xxx-streak',
    'new_feature': 'd-xxx-feature',
    'trial_ending_3d': 'd-xxx-trial-3d',
    'trial_ending_1d': 'd-xxx-trial-1d',
    'upgrade_incentive': 'd-xxx-upgrade',
    'churn_prevention': 'd-xxx-churn',
    'winback': 'd-xxx-winback',
}

def send_campaign_email(user, template_key, dynamic_data=None):
    """Enviar email de campanha"""
    message = Mail(
        from_email=('noreply@doutoraia.com', 'Doutora IA OAB'),
        to_emails=user.email
    )

    message.template_id = TEMPLATES[template_key]

    # Dados dinâmicos
    personalization = Personalization()
    personalization.add_to(user.email)
    personalization.dynamic_template_data = {
        'nome': user.nome,
        **(dynamic_data or {})
    }

    message.add_personalization(personalization)

    try:
        response = sg.send(message)
        print(f'Email {template_key} enviado para {user.email}: {response.status_code}')
        return True
    except Exception as e:
        print(f'Erro ao enviar email: {str(e)}')
        return False

# Triggers de campanha
def trigger_welcome_sequence(user):
    """Iniciar sequência de boas-vindas"""
    # Email 1: Imediato
    send_campaign_email(user, 'welcome')

    # Email 2: Agendar para 24h
    schedule_email(user, 'tutorial', delay_hours=24)

    # Email 3: Agendar para 72h
    schedule_email(user, 'premium_offer', delay_hours=72)

def trigger_weekly_stats(user, stats):
    """Enviar estatísticas semanais"""
    dynamic_data = {
        'sessoes': stats['sessoes'],
        'questoes': stats['questoes'],
        'aproveitamento': stats['aproveitamento'],
        'fp': stats['fp'],
    }
    send_campaign_email(user, 'weekly_stats', dynamic_data)

def trigger_achievement_email(user, achievement):
    """Enviar email de conquista desbloqueada"""
    dynamic_data = {
        'nome_conquista': achievement.nome,
        'descricao_conquista': achievement.descricao,
        'xp_recompensa': achievement.xp_recompensa,
    }
    send_campaign_email(user, 'achievement', dynamic_data)

# ... mais triggers
```

### 4. Cron Jobs (Scheduler)

**Arquivo**: `backend/tasks/email_scheduler.py`

```python
from apscheduler.schedulers.background import BackgroundScheduler
from database.connection import get_db_connection
from services.email_campaigns import *

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=9)  # Diariamente às 9h
def check_inactive_users():
    """Verificar usuários inativos há 3+ dias"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT u.id, u.nome, u.email, g.streak_atual
        FROM usuarios u
        LEFT JOIN gamificacao g ON u.id = g.estudante_id
        WHERE u.ultimo_acesso < NOW() - INTERVAL '3 days'
          AND u.email_preferences->>'streak_reminders' = 'true'
    """

    cursor.execute(query)
    users = cursor.fetchall()

    for user in users:
        send_campaign_email(user, 'streak_reminder', {
            'streak': user.streak_atual or 0
        })

    cursor.close()
    conn.close()

@scheduler.scheduled_job('cron', hour=10, day_of_week='mon')  # Segunda às 10h
def send_weekly_stats():
    """Enviar estatísticas semanais"""
    # ... lógica

@scheduler.scheduled_job('cron', hour=12)  # Diariamente às 12h
def check_trial_endings():
    """Verificar trials terminando"""
    # ... lógica

scheduler.start()
```

---

## 📊 Métricas para Acompanhar

### SendGrid Dashboard
- **Open Rate**: > 25% (objetivo)
- **Click Rate**: > 5% (objetivo)
- **Unsubscribe Rate**: < 0.5%
- **Bounce Rate**: < 2%

### Conversão
- **Trial → Paid**: > 20%
- **Gratuito → Paid** (30 dias): > 10%
- **Churn Recovery**: > 15%

---

## 🔧 Comandos Úteis

```bash
# Testar envio de email
python scripts/test_email.py --template=welcome --email=teste@example.com

# Ver estatísticas de campanha
python scripts/campaign_stats.py --campaign=welcome_sequence

# Exportar lista de usuários para remarketing
python scripts/export_email_list.py --segment=inactive_30d
```

---

## ✅ Checklist de Implementação

- [ ] Criar conta SendGrid
- [ ] Configurar domínio e autenticação (SPF, DKIM)
- [ ] Criar 12 templates dinâmicos
- [ ] Implementar triggers em `email_campaigns.py`
- [ ] Configurar scheduler para emails recorrentes
- [ ] Adicionar preferências de email no perfil do usuário
- [ ] Implementar unsubscribe functionality
- [ ] Testar todos os emails
- [ ] Monitorar métricas nas primeiras semanas
- [ ] A/B test subject lines

---

**Próximo passo**: Implementar código Python no backend e criar templates no SendGrid!
