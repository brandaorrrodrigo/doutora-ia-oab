# Checklist de Testes Manuais - Doutora IA OAB

**Versão**: 1.0
**Data**: 2025-12-28
**Objetivo**: Validar funcionalidades críticas antes do lançamento em produção

---

## 📋 Instruções Gerais

### Pré-requisitos
- [ ] Frontend rodando: `https://doutoraia.com` (ou `http://localhost:3000` em dev)
- [ ] Backend rodando: `https://api.doutoraia.com` (ou `http://localhost:8000` em dev)
- [ ] Chat IA rodando: `https://chat.doutoraia.com` (ou `http://localhost:8001` em dev)
- [ ] Banco de dados PostgreSQL acessível
- [ ] Navegadores: Chrome, Firefox, Safari (testar em todos)
- [ ] Dispositivos: Desktop + Mobile (responsividade)

### Como usar este checklist
1. ✅ Marcar checkbox quando teste passar
2. ❌ Adicionar nota se falhar com descrição do erro
3. ⚠️ Adicionar warning para comportamentos inesperados
4. 📝 Screenshots para bugs visuais

### Severidade
- 🔴 **BLOCKER**: Impede uso crítico, deve corrigir ANTES de lançar
- 🟠 **CRITICAL**: Funcionalidade importante quebrada, corrigir em 24h
- 🟡 **MEDIUM**: Bug menor, corrigir em 1 semana
- 🟢 **LOW**: Melhoria/refinamento, pode lançar com isso

---

## 🧪 FLUXO 1: Autenticação e Cadastro

### 1.1 Cadastro de Novo Usuário

#### Cenário Feliz (Happy Path)
- [ ] **1.1.1** Acessar `/cadastro`
- [ ] **1.1.2** Preencher nome: "João Teste"
- [ ] **1.1.3** Preencher email: "joao.teste.{TIMESTAMP}@gmail.com"
- [ ] **1.1.4** Preencher senha: "SenhaSegura123!"
- [ ] **1.1.5** Clicar em "Cadastrar"
- [ ] **1.1.6** ✅ Verificar redirecionamento para `/dashboard`
- [ ] **1.1.7** ✅ Verificar mensagem de boas-vindas: "Olá, João Teste!"
- [ ] **1.1.8** ✅ Verificar cookie `auth_token` criado (DevTools → Application → Cookies)

**Resultado Esperado**: Usuário cadastrado e autenticado automaticamente

#### Cenário de Erro: Email Duplicado
- [ ] **1.1.9** Tentar cadastrar novamente com mesmo email
- [ ] **1.1.10** ✅ Verificar mensagem de erro: "Email já cadastrado"
- [ ] **1.1.11** ✅ Não redirecionar para dashboard

#### Cenário de Erro: Validação de Campos
- [ ] **1.1.12** Tentar cadastrar com senha curta (< 6 caracteres)
- [ ] **1.1.13** ✅ Verificar mensagem: "Senha deve ter pelo menos 6 caracteres"
- [ ] **1.1.14** Tentar cadastrar com email inválido: "teste@invalido"
- [ ] **1.1.15** ✅ Verificar validação de email

---

### 1.2 Login

#### Cenário Feliz
- [ ] **1.2.1** Fazer logout (se logado)
- [ ] **1.2.2** Acessar `/login`
- [ ] **1.2.3** Preencher email cadastrado anteriormente
- [ ] **1.2.4** Preencher senha correta
- [ ] **1.2.5** Clicar em "Entrar"
- [ ] **1.2.6** ✅ Verificar redirecionamento para `/dashboard`
- [ ] **1.2.7** ✅ Verificar cookie `auth_token` criado

#### Cenário de Erro: Credenciais Inválidas
- [ ] **1.2.8** Tentar login com senha errada
- [ ] **1.2.9** ✅ Verificar mensagem: "Credenciais inválidas"
- [ ] **1.2.10** Tentar login com email inexistente
- [ ] **1.2.11** ✅ Verificar mensagem: "Credenciais inválidas" (não revelar se email existe!)

---

### 1.3 Recuperação de Senha

#### Cenário Feliz
- [ ] **1.3.1** Fazer logout
- [ ] **1.3.2** Acessar `/login`
- [ ] **1.3.3** Clicar em "Esqueci minha senha"
- [ ] **1.3.4** Preencher email cadastrado
- [ ] **1.3.5** Clicar em "Enviar link de recuperação"
- [ ] **1.3.6** ✅ Verificar mensagem: "Se o email existir, você receberá instruções..."
- [ ] **1.3.7** ✅ Verificar email recebido (inbox do email de teste)
- [ ] **1.3.8** ✅ Clicar no link do email
- [ ] **1.3.9** ✅ Verificar redirecionamento para `/recuperar-senha?token=...`
- [ ] **1.3.10** Preencher nova senha
- [ ] **1.3.11** Clicar em "Redefinir senha"
- [ ] **1.3.12** ✅ Verificar mensagem: "Senha redefinida com sucesso!"
- [ ] **1.3.13** ✅ Fazer login com nova senha

#### Cenário de Erro: Token Expirado
- [ ] **1.3.14** Aguardar 1 hora (ou alterar `expires_at` no DB para simular)
- [ ] **1.3.15** Tentar usar link de recuperação
- [ ] **1.3.16** ✅ Verificar mensagem: "Token inválido ou expirado"

#### Cenário de Erro: Token Usado
- [ ] **1.3.17** Tentar usar mesmo token duas vezes
- [ ] **1.3.18** ✅ Verificar mensagem: "Token inválido ou expirado"

---

### 1.4 Logout

- [ ] **1.4.1** Estando logado, clicar em "Sair" (menu/header)
- [ ] **1.4.2** ✅ Verificar redirecionamento para `/login`
- [ ] **1.4.3** ✅ Verificar cookie `auth_token` removido
- [ ] **1.4.4** ✅ Tentar acessar `/dashboard` → deve redirecionar para `/login`

---

## 🔒 FLUXO 2: Proteção de Rotas

### 2.1 Rotas Protegidas (Requerem Autenticação)

- [ ] **2.1.1** Fazer logout
- [ ] **2.1.2** Tentar acessar `/dashboard` → ✅ Redirecionar para `/login?redirect=/dashboard`
- [ ] **2.1.3** Tentar acessar `/estudo` → ✅ Redirecionar para `/login?redirect=/estudo`
- [ ] **2.1.4** Tentar acessar `/pecas` → ✅ Redirecionar para `/login?redirect=/pecas`
- [ ] **2.1.5** Tentar acessar `/chat` → ✅ Redirecionar para `/login?redirect=/chat`
- [ ] **2.1.6** Fazer login → ✅ Redirecionar para página original (redirect query param)

### 2.2 Rotas Públicas (Não Requerem Autenticação)

- [ ] **2.2.1** Acessar `/` (landing page) → ✅ Carrega normalmente
- [ ] **2.2.2** Acessar `/sobre` → ✅ Carrega normalmente
- [ ] **2.2.3** Acessar `/termos-de-uso` → ✅ Carrega normalmente
- [ ] **2.2.4** Acessar `/politica-privacidade` → ✅ Carrega normalmente

### 2.3 Redirect após Login

- [ ] **2.3.1** Estando logado, tentar acessar `/login` → ✅ Redirecionar para `/dashboard`
- [ ] **2.3.2** Estando logado, tentar acessar `/cadastro` → ✅ Redirecionar para `/dashboard`

---

## 📊 FLUXO 3: Painel do Estudante (Dashboard)

- [ ] **3.1** Fazer login e acessar `/dashboard`
- [ ] **3.2** ✅ Verificar nome do usuário exibido: "Olá, {nome}!"
- [ ] **3.3** ✅ Verificar estatísticas carregam:
  - [ ] Sessões Realizadas: número
  - [ ] Questões Respondidas: número
  - [ ] Aproveitamento: porcentagem
  - [ ] Peças Concluídas: número
- [ ] **3.4** ✅ Verificar limites do plano (se GRATUITO):
  - [ ] Sessões restantes: X/5 por dia
  - [ ] Questões por sessão: 10
- [ ] **3.5** ✅ Verificar botões de navegação funcionam:
  - [ ] "Iniciar Estudo" → `/estudo`
  - [ ] "Praticar Peças" → `/pecas`
  - [ ] "Chat com IA" → `/chat`

### Cenário de Erro: API Falha

- [ ] **3.6** Parar backend (simular erro 500)
- [ ] **3.7** Recarregar dashboard
- [ ] **3.8** ✅ Verificar mensagem de erro amigável
- [ ] **3.9** ✅ Não quebrar interface (graceful degradation)

---

## 📚 FLUXO 4: Sessão de Estudo

### 4.1 Iniciar Sessão (Sem Filtros)

- [ ] **4.1.1** Acessar `/estudo`
- [ ] **4.1.2** Clicar em "Iniciar Estudo"
- [ ] **4.1.3** ✅ Verificar questão carrega:
  - [ ] Enunciado visível
  - [ ] 4 alternativas (A, B, C, D)
  - [ ] Área do direito exibida
  - [ ] Dificuldade exibida
- [ ] **4.1.4** ✅ Verificar botão "Confirmar Resposta" está DESABILITADO inicialmente

### 4.2 Responder Questão Corretamente

- [ ] **4.2.1** Selecionar uma alternativa (clicar em "A)")
- [ ] **4.2.2** ✅ Verificar alternativa fica marcada (highlight)
- [ ] **4.2.3** ✅ Verificar botão "Confirmar Resposta" agora está HABILITADO
- [ ] **4.2.4** Clicar em "Confirmar Resposta"
- [ ] **4.2.5** ✅ Verificar feedback de acerto:
  - [ ] Mensagem: "✅ Correto!"
  - [ ] Explicação da IA exibida
  - [ ] Alternativas ficam DESABILITADAS
- [ ] **4.2.6** ✅ Verificar botão "Próxima Questão" aparece
- [ ] **4.2.7** Clicar em "Próxima Questão"
- [ ] **4.2.8** ✅ Verificar nova questão carrega

### 4.3 Responder Questão Incorretamente

- [ ] **4.3.1** Selecionar alternativa errada
- [ ] **4.3.2** Clicar em "Confirmar Resposta"
- [ ] **4.3.3** ✅ Verificar feedback de erro:
  - [ ] Mensagem: "❌ Incorreto"
  - [ ] Alternativa correta destacada em verde
  - [ ] Alternativa errada destacada em vermelho
  - [ ] Explicação da IA exibida
- [ ] **4.3.4** ✅ Verificar estatísticas atualizam (aproveitamento diminui)

### 4.4 Finalizar Sessão

- [ ] **4.4.1** Completar 10 questões (limite do plano gratuito)
- [ ] **4.4.2** ✅ Verificar tela de resumo:
  - [ ] Total de questões: 10
  - [ ] Acertos: X
  - [ ] Erros: Y
  - [ ] Aproveitamento: Z%
- [ ] **4.4.3** ✅ Verificar botão "Voltar ao Dashboard"
- [ ] **4.4.4** Clicar em "Voltar ao Dashboard"
- [ ] **4.4.5** ✅ Verificar estatísticas atualizadas no dashboard

### 4.5 Limites do Plano Gratuito

- [ ] **4.5.1** Completar 5 sessões no mesmo dia
- [ ] **4.5.2** Tentar iniciar 6ª sessão
- [ ] **4.5.3** ✅ Verificar mensagem: "Limite diário atingido (5 sessões)"
- [ ] **4.5.4** ✅ Verificar botão de upgrade para plano premium

---

## 📝 FLUXO 5: Prática de Peças Processuais

### 5.1 Avaliar Peça

- [ ] **5.1.1** Acessar `/pecas`
- [ ] **5.1.2** Selecionar tipo de peça: "Petição Inicial"
- [ ] **5.1.3** ✅ Verificar template pré-preenche o editor
- [ ] **5.1.4** Escrever ou colar peça processual (mínimo 100 caracteres)
- [ ] **5.1.5** Clicar em "Avaliar Peça"
- [ ] **5.1.6** ✅ Verificar loading spinner durante análise
- [ ] **5.1.7** ✅ Verificar feedback da IA:
  - [ ] Nota geral (0-10)
  - [ ] Pontos fortes (lista)
  - [ ] Pontos a melhorar (lista)
  - [ ] Sugestões detalhadas
- [ ] **5.1.8** ✅ Verificar botão "Nova Peça" limpa o formulário

### 5.2 Trocar Tipo de Peça

- [ ] **5.2.1** Selecionar tipo diferente: "Recurso de Apelação"
- [ ] **5.2.2** ✅ Verificar template atualiza automaticamente
- [ ] **5.2.3** ✅ Verificar editor limpa conteúdo anterior

### 5.3 Validações

- [ ] **5.3.1** Tentar avaliar peça vazia
- [ ] **5.3.2** ✅ Verificar botão "Avaliar" está desabilitado
- [ ] **5.3.3** Escrever menos de 100 caracteres
- [ ] **5.3.4** ✅ Verificar mensagem: "Mínimo de 100 caracteres"

---

## 💬 FLUXO 6: Chat com IA Jurídica

### 6.1 Enviar Mensagem

- [ ] **6.1.1** Acessar `/chat`
- [ ] **6.1.2** ✅ Verificar histórico vazio (primeira vez)
- [ ] **6.1.3** Digitar mensagem: "O que é prescrição no direito civil?"
- [ ] **6.1.4** Clicar em "Enviar" (ou pressionar Enter)
- [ ] **6.1.5** ✅ Verificar mensagem do usuário aparece no chat
- [ ] **6.1.6** ✅ Verificar loading indicator durante resposta da IA
- [ ] **6.1.7** ✅ Verificar resposta da IA aparece:
  - [ ] Formatação markdown (negrito, listas, etc.)
  - [ ] Conteúdo relevante e jurídico
- [ ] **6.1.8** ✅ Verificar scroll automático para última mensagem

### 6.2 Múltiplas Mensagens (Contexto)

- [ ] **6.2.1** Enviar pergunta: "Qual o prazo de prescrição para dívidas de cartão de crédito?"
- [ ] **6.2.2** ✅ Verificar IA mantém contexto da conversa anterior
- [ ] **6.2.3** Enviar 5 mensagens seguidas
- [ ] **6.2.4** ✅ Verificar histórico mantém ordem cronológica

### 6.3 Validações

- [ ] **6.3.1** Tentar enviar mensagem vazia
- [ ] **6.3.2** ✅ Verificar botão "Enviar" está desabilitado
- [ ] **6.3.3** Digitar texto e clicar em "Limpar Chat"
- [ ] **6.3.4** ✅ Verificar histórico é limpo
- [ ] **6.3.5** ✅ Verificar campo de texto é limpo

---

## 📧 FLUXO 7: Email de Boas-Vindas

### 7.1 Cadastro → Email Automático

- [ ] **7.1.1** Cadastrar novo usuário
- [ ] **7.1.2** ✅ Aguardar até 2 minutos
- [ ] **7.1.3** ✅ Verificar email de boas-vindas recebido:
  - [ ] Assunto: "Bem-vindo à Doutora IA OAB! 🎉"
  - [ ] Nome do usuário correto no corpo
  - [ ] Link "Fazer Primeiro Login" funciona
  - [ ] Design responsivo (abrir no mobile)
  - [ ] Versão HTML renderiza corretamente
  - [ ] Versão texto plano legível (se HTML falhar)

---

## 🎨 FLUXO 8: UX e Design

### 8.1 Responsividade

- [ ] **8.1.1** Testar em **Desktop** (1920x1080):
  - [ ] Layout não quebra
  - [ ] Elementos bem espaçados
- [ ] **8.1.2** Testar em **Tablet** (768x1024):
  - [ ] Menu hamburger funciona (se aplicável)
  - [ ] Cards se reorganizam em grid
- [ ] **8.1.3** Testar em **Mobile** (375x667):
  - [ ] Textos legíveis (não muito pequenos)
  - [ ] Botões tocáveis (mínimo 44x44px)
  - [ ] Scroll funciona suavemente

### 8.2 Performance

- [ ] **8.2.1** Abrir DevTools → Network → Limpar cache
- [ ] **8.2.2** Recarregar página inicial `/`
- [ ] **8.2.3** ✅ Verificar tempo de carregamento < 3 segundos (4G)
- [ ] **8.2.4** ✅ Verificar First Contentful Paint (FCP) < 1.8s
- [ ] **8.2.5** ✅ Verificar Largest Contentful Paint (LCP) < 2.5s

### 8.3 Acessibilidade Básica

- [ ] **8.3.1** Navegar com Tab (teclado)
- [ ] **8.3.2** ✅ Verificar elementos focáveis na ordem lógica
- [ ] **8.3.3** ✅ Verificar indicadores de foco visíveis
- [ ] **8.3.4** Pressionar Enter em botões
- [ ] **8.3.5** ✅ Verificar ações funcionam via teclado
- [ ] **8.3.6** Usar leitor de tela (NVDA/JAWS/VoiceOver)
- [ ] **8.3.7** ✅ Verificar textos alternativos em imagens
- [ ] **8.3.8** ✅ Verificar labels em formulários

---

## 🔍 FLUXO 9: SEO e Metadados

### 9.1 Open Graph (Social Sharing)

- [ ] **9.1.1** Abrir https://www.opengraph.xyz/
- [ ] **9.1.2** Inserir URL: `https://doutoraia.com`
- [ ] **9.1.3** ✅ Verificar preview carrega:
  - [ ] Título: "Doutora IA OAB - Sua Aprovação é Nossa Missão"
  - [ ] Descrição presente
  - [ ] Imagem og-image.png carrega (1200x630)
- [ ] **9.1.4** Enviar link no WhatsApp
- [ ] **9.1.5** ✅ Verificar preview bonito com imagem

### 9.2 Favicon e Apple Touch Icon

- [ ] **9.2.1** Abrir site em nova aba
- [ ] **9.2.2** ✅ Verificar favicon ⚖️ aparece na aba do navegador
- [ ] **9.2.3** Adicionar aos favoritos
- [ ] **9.2.4** ✅ Verificar ícone aparece nos bookmarks
- [ ] **9.2.5** (iOS) Adicionar à tela inicial
- [ ] **9.2.6** ✅ Verificar Apple Touch Icon aparece

---

## 🍪 FLUXO 10: Cookies e LGPD

### 10.1 Cookie Consent

- [ ] **10.1.1** Limpar cookies do navegador
- [ ] **10.1.2** Acessar site pela primeira vez
- [ ] **10.1.3** ✅ Verificar banner de cookies aparece
- [ ] **10.1.4** ✅ Verificar link "Política de Privacidade" funciona
- [ ] **10.1.5** Clicar em "Aceitar todos os cookies"
- [ ] **10.1.6** ✅ Verificar banner fecha
- [ ] **10.1.7** ✅ Verificar cookie de consentimento criado
- [ ] **10.1.8** Recarregar página
- [ ] **10.1.9** ✅ Verificar banner NÃO aparece novamente

### 10.2 Páginas LGPD

- [ ] **10.2.1** Acessar `/termos-de-uso`
- [ ] **10.2.2** ✅ Verificar conteúdo carrega
- [ ] **10.2.3** Acessar `/politica-privacidade`
- [ ] **10.2.4** ✅ Verificar seções: Coleta de Dados, Uso, Compartilhamento, Segurança

---

## 📊 FLUXO 11: Google Analytics (Se Configurado)

- [ ] **11.1** Abrir DevTools → Network → Filtrar por "google"
- [ ] **11.2** Navegar entre páginas
- [ ] **11.3** ✅ Verificar requisições para `googletagmanager.com`
- [ ] **11.4** Fazer login
- [ ] **11.5** ✅ Verificar evento `login` enviado (Network → Payload)
- [ ] **11.6** Responder questão
- [ ] **11.7** ✅ Verificar evento `responder_questao` enviado
- [ ] **11.8** Acessar Google Analytics (https://analytics.google.com/)
- [ ] **11.9** Realtime → Events
- [ ] **11.10** ✅ Verificar eventos aparecem em tempo real

---

## 🐛 FLUXO 12: Tratamento de Erros

### 12.1 Erro 404 (Página Não Encontrada)

- [ ] **12.1.1** Acessar `/pagina-que-nao-existe`
- [ ] **12.1.2** ✅ Verificar página 404 customizada
- [ ] **12.1.3** ✅ Verificar link "Voltar ao início" funciona

### 12.2 Erro 500 (Servidor)

- [ ] **12.2.1** Parar backend
- [ ] **12.2.2** Tentar iniciar sessão de estudo
- [ ] **12.2.3** ✅ Verificar mensagem de erro amigável: "Erro ao conectar com servidor"
- [ ] **12.2.4** ✅ Verificar botão "Tentar novamente"

### 12.3 Erro de Rede (Offline)

- [ ] **12.3.1** Desabilitar internet (airplane mode)
- [ ] **12.3.2** Tentar fazer login
- [ ] **12.3.3** ✅ Verificar mensagem: "Sem conexão com internet"

### 12.4 Token Expirado

- [ ] **12.4.1** Alterar token no cookie para inválido
- [ ] **12.4.2** Tentar acessar `/dashboard`
- [ ] **12.4.3** ✅ Verificar redirecionamento para `/login`
- [ ] **12.4.4** ✅ Verificar mensagem: "Sessão expirada. Faça login novamente."

---

## 🔐 FLUXO 13: Segurança (Básico)

### 13.1 XSS (Cross-Site Scripting)

- [ ] **13.1.1** Tentar cadastrar usuário com nome: `<script>alert('XSS')</script>`
- [ ] **13.1.2** ✅ Verificar script NÃO executa (texto renderiza como string)
- [ ] **13.1.3** Tentar enviar mensagem no chat com HTML malicioso
- [ ] **13.1.4** ✅ Verificar sanitização funciona

### 13.2 SQL Injection (Básico)

- [ ] **13.2.1** Tentar login com email: `admin' OR '1'='1`
- [ ] **13.2.2** ✅ Verificar login falha (credenciais inválidas)
- [ ] **13.2.3** ✅ Backend usa prepared statements (verificar logs)

### 13.3 HTTPS

- [ ] **13.3.1** Acessar site em produção: `https://doutoraia.com`
- [ ] **13.3.2** ✅ Verificar cadeado SSL no navegador
- [ ] **13.3.3** Clicar no cadeado → Ver certificado
- [ ] **13.3.4** ✅ Verificar certificado válido e não expirado

---

## 📱 FLUXO 14: Cross-Browser Testing

### 14.1 Chrome (Desktop)
- [ ] Todos os fluxos 1-13 passam

### 14.2 Firefox (Desktop)
- [ ] Todos os fluxos 1-13 passam

### 14.3 Safari (macOS/iOS)
- [ ] Todos os fluxos 1-13 passam
- [ ] ✅ Verificar bugs específicos do Safari (date inputs, etc.)

### 14.4 Edge (Desktop)
- [ ] Todos os fluxos 1-13 passam

### 14.5 Chrome Mobile (Android)
- [ ] Fluxos críticos 1-6 passam
- [ ] ✅ Touch events funcionam

### 14.6 Safari Mobile (iOS)
- [ ] Fluxos críticos 1-6 passam
- [ ] ✅ Scroll suave sem bugs

---

## 📋 Resumo de Execução

### Tempo Estimado
- ⏱️ **Completo**: 4-6 horas (todos os fluxos, todos os browsers)
- ⏱️ **Mínimo crítico**: 1-2 horas (fluxos 1-6, apenas Chrome)

### Priorização

#### 🔴 P0 - OBRIGATÓRIO antes de lançar
- [ ] Fluxo 1: Autenticação e Cadastro
- [ ] Fluxo 2: Proteção de Rotas
- [ ] Fluxo 3: Dashboard
- [ ] Fluxo 4: Sessão de Estudo
- [ ] Fluxo 12: Tratamento de Erros (básico)

#### 🟠 P1 - Recomendado antes de lançar
- [ ] Fluxo 5: Prática de Peças
- [ ] Fluxo 6: Chat com IA
- [ ] Fluxo 8: Responsividade
- [ ] Fluxo 10: LGPD

#### 🟡 P2 - Pode testar pós-lançamento
- [ ] Fluxo 7: Email de Boas-Vindas (validar em staging)
- [ ] Fluxo 9: SEO
- [ ] Fluxo 11: Google Analytics
- [ ] Fluxo 13: Segurança avançada
- [ ] Fluxo 14: Cross-browser completo

---

## 🐛 Template de Reporte de Bug

```markdown
### Bug #{número}

**Severidade**: 🔴 BLOCKER / 🟠 CRITICAL / 🟡 MEDIUM / 🟢 LOW

**Fluxo**: {número do fluxo}
**Passo**: {número do passo}

**Descrição**:
{O que aconteceu}

**Esperado**:
{O que deveria acontecer}

**Reproduzir**:
1. {Passo 1}
2. {Passo 2}
3. {Passo 3}

**Ambiente**:
- Browser: {Chrome 120.0.0}
- OS: {Windows 11}
- URL: {https://doutoraia.com/estudo}

**Screenshot**:
{Anexar se possível}

**Console Errors**:
{Copiar do DevTools → Console}
```

---

## ✅ Assinatura de Conclusão

**Testador**: ___________________________
**Data**: ___/___/2025
**Versão Testada**: v1.0.0
**Ambiente**: ☐ Staging  ☐ Production

**Resultado Geral**:
- Total de testes executados: ___ / 200+
- Testes passaram: ___
- Bugs encontrados: ___
  - 🔴 Blockers: ___
  - 🟠 Critical: ___
  - 🟡 Medium: ___
  - 🟢 Low: ___

**Recomendação**:
☐ **APROVAR** para produção
☐ **REJEITAR** - corrigir bugs blockers
☐ **APROVAR COM RESSALVAS** - corrigir bugs críticos em 24h

---

**Última atualização**: 2025-12-28
