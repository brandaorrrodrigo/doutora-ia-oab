# Relatório de Vulnerabilidades de Segurança

**Data**: 2025-12-28
**Ferramenta**: pip-audit 2.10.0
**Total de vulnerabilidades**: 46 em 17 pacotes

---

## 🚨 Resumo Executivo

### Status Atual
- ❌ **46 vulnerabilidades conhecidas** identificadas
- ⚠️ **Pacotes críticos afetados**: FastAPI, Starlette, Requests, Transformers, Torch
- 🔴 **Risco**: ALTO - Múltiplas vulnerabilidades críticas (CVE)

### Prioridade de Ação
- 🔴 **CRÍTICO (P0)**: 12 vulnerabilidades - Corrigir IMEDIATAMENTE
- 🟠 **ALTO (P1)**: 22 vulnerabilidades - Corrigir em 1 semana
- 🟡 **MÉDIO (P2)**: 12 vulnerabilidades - Corrigir em 1 mês

---

## 🔴 CRÍTICO (P0) - Corrigir HOJE

### 1. FastAPI (Servidor Web Principal)
**Pacote**: `fastapi==0.108.0`
**Vulnerabilidade**: PYSEC-2024-38
**Risco**: Servidor web vulnerável pode permitir ataques
**Correção**:
```bash
pip install --upgrade fastapi==0.115.0
```

### 2. Starlette (Framework ASGI)
**Pacote**: `starlette==0.32.0.post1`
**Vulnerabilidades**: CVE-2024-47874, CVE-2025-54121
**Risco**: Ataques de DoS, bypass de autenticação
**Correção**:
```bash
pip install --upgrade starlette==0.47.2
```

### 3. Python-Multipart (Upload de arquivos)
**Pacote**: `python-multipart==0.0.6`
**Vulnerabilidades**: CVE-2024-24762, CVE-2024-53981
**Risco**: DoS via upload malicioso
**Correção**:
```bash
pip install --upgrade python-multipart==0.0.18
```

### 4. Requests (Cliente HTTP)
**Pacote**: `requests==2.31.0`
**Vulnerabilidades**: CVE-2024-35195, CVE-2024-47081
**Risco**: Vazamento de credenciais, SSRF
**Correção**:
```bash
pip install --upgrade requests==2.32.4
```

### 5. urllib3 (Cliente HTTP baixo nível)
**Pacote**: `urllib3==1.26.20`
**Vulnerabilidades**: CVE-2025-50181, CVE-2025-66418, CVE-2025-66471
**Risco**: SSRF, bypass de validação SSL
**Correção**:
```bash
pip install --upgrade "urllib3>=2.6.0"
```

### 6. Werkzeug (Utilidades WSGI)
**Pacote**: `werkzeug==3.1.3`
**Vulnerabilidade**: CVE-2025-66221
**Risco**: Bypass de segurança
**Correção**:
```bash
pip install --upgrade werkzeug==3.1.4
```

---

## 🟠 ALTO (P1) - Corrigir em 1 semana

### 7. Transformers (Hugging Face - IA)
**Pacote**: `transformers==4.35.2`
**Vulnerabilidades**: 15 CVEs (CVE-2024-3568, CVE-2024-12720, CVE-2025-1194, etc.)
**Risco**: Code execution, model poisoning, DoS
**Correção**:
```bash
pip install --upgrade transformers==4.53.0
```

### 8. Torch (PyTorch)
**Pacote**: `torch==2.1.0`
**Vulnerabilidades**: 7 CVEs (CVE-2025-2953, CVE-2025-3730, etc.)
**Risco**: Code execution, buffer overflow
**Correção**:
```bash
pip install --upgrade torch==2.8.0
```

### 9. Langchain-Core (LLM Framework)
**Pacote**: `langchain-core==0.3.80`
**Vulnerabilidade**: CVE-2025-68664
**Risco**: Injection attacks
**Correção**:
```bash
pip install --upgrade langchain-core==1.2.5
```

### 10. Scikit-Learn (ML)
**Pacote**: `scikit-learn==1.3.2`
**Vulnerabilidade**: PYSEC-2024-110
**Risco**: Code execution via deserialization
**Correção**:
```bash
pip install --upgrade scikit-learn==1.5.0
```

### 11. Qdrant-Client (Vector DB)
**Pacote**: `qdrant-client==1.7.0`
**Vulnerabilidade**: CVE-2024-3829
**Risco**: Unauthorized access
**Correção**:
```bash
pip install --upgrade qdrant-client==1.9.0
```

---

## 🟡 MÉDIO (P2) - Corrigir em 1 mês

### 12. Pillow (Processamento de imagens)
**Pacote**: `pillow==10.1.0`
**Vulnerabilidades**: CVE-2023-50447, CVE-2024-28219
**Risco**: Buffer overflow em arquivos maliciosos
**Correção**:
```bash
pip install --upgrade Pillow==10.3.0
```

### 13. PyPDF (Leitura de PDFs)
**Pacote**: `pypdf==6.2.0`
**Vulnerabilidade**: CVE-2025-66019
**Risco**: DoS via PDF malicioso
**Correção**:
```bash
pip install --upgrade pypdf==6.4.0
```

### 14. PDFMiner-Six (Extração de PDFs)
**Pacote**: `pdfminer-six==20221105`
**Vulnerabilidades**: CVE-2025-64512, GHSA-f83h-ghpp-7wcc
**Risco**: Code execution, DoS
**Correção**:
```bash
pip install --upgrade pdfminer.six==20251107
```

### 15. TQDM (Progress bars)
**Pacote**: `tqdm==4.66.1`
**Vulnerabilidade**: CVE-2024-34062
**Risco**: CLI injection
**Correção**:
```bash
pip install --upgrade tqdm==4.66.3
```

### 16. Marshmallow (Serialization)
**Pacote**: `marshmallow==3.26.1`
**Vulnerabilidade**: CVE-2025-68480
**Risco**: Validation bypass
**Correção**:
```bash
pip install --upgrade marshmallow==4.1.2
```

### 17. ECDSA (Criptografia)
**Pacote**: `ecdsa==0.19.1`
**Vulnerabilidade**: CVE-2024-23342
**Risco**: Timing attack
**Correção**:
```bash
pip install --upgrade ecdsa==0.20.0
```

---

## 🛠️ Plano de Ação Recomendado

### Opção A: Upgrade Conservador (Recomendado para HOJE)

Atualizar apenas os pacotes **CRÍTICOS (P0)** que não afetam funcionalidades core:

```bash
# Backend - D:\JURIS_IA_CORE_V1

# 1. Web framework (CRÍTICO)
pip install --upgrade fastapi==0.115.0
pip install --upgrade starlette==0.47.2
pip install --upgrade python-multipart==0.0.18

# 2. HTTP clients (CRÍTICO)
pip install --upgrade requests==2.32.4
pip install --upgrade "urllib3>=2.6.0"

# 3. Utilidades (CRÍTICO)
pip install --upgrade werkzeug==3.1.4

# 4. Testar API
python api/api_server.py

# 5. Se tudo funcionar, gerar novo requirements.txt
pip freeze > requirements_updated.txt
```

**Tempo estimado**: 30 minutos
**Risco**: BAIXO (pacotes estáveis)
**Benefício**: Elimina 12 vulnerabilidades críticas

---

### Opção B: Upgrade Completo (Recomendado para 1 semana)

Atualizar TODOS os pacotes vulneráveis:

```bash
# Criar backup do ambiente
pip freeze > requirements_backup.txt

# Atualizar CRÍTICOS (P0)
pip install --upgrade fastapi==0.115.0 starlette==0.47.2 python-multipart==0.0.18
pip install --upgrade requests==2.32.4 "urllib3>=2.6.0" werkzeug==3.1.4

# Atualizar ALTOS (P1) - ML/AI (ATENÇÃO: pode quebrar modelos!)
pip install --upgrade transformers==4.53.0
pip install --upgrade torch==2.8.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install --upgrade langchain-core==1.2.5
pip install --upgrade scikit-learn==1.5.0
pip install --upgrade qdrant-client==1.9.0

# Atualizar MÉDIOS (P2)
pip install --upgrade Pillow==10.3.0 pypdf==6.4.0 pdfminer.six==20251107
pip install --upgrade tqdm==4.66.3 marshmallow==4.1.2 ecdsa==0.20.0

# Testar TUDO
python -m pytest tests/
python api/api_server.py

# Gerar novo requirements.txt
pip freeze > requirements.txt
```

**Tempo estimado**: 4-6 horas (inclui testes)
**Risco**: MÉDIO (PyTorch e Transformers podem ter breaking changes)
**Benefício**: Elimina TODAS as 46 vulnerabilidades

---

### Opção C: Ambiente Virtual Novo (Mais Seguro)

Criar ambiente limpo com versões atualizadas:

```bash
# 1. Criar novo ambiente
python -m venv venv_secure
venv_secure\Scripts\activate

# 2. Instalar versões seguras
pip install --upgrade pip setuptools wheel

# 3. Instalar dependências atualizadas
pip install -r requirements.txt --upgrade

# 4. Testar
python api/api_server.py

# 5. Se funcionar, substituir ambiente antigo
```

---

## ⚠️ Avisos Importantes

### 1. Breaking Changes Esperados

#### PyTorch (2.1.0 → 2.8.0)
- ⚠️ Mudanças na API de modelos
- ⚠️ Compatibilidade com CUDA pode mudar
- ⚠️ Requer reteste de todos os modelos

#### Transformers (4.35.2 → 4.53.0)
- ⚠️ Novos parâmetros em pipelines
- ⚠️ Mudanças em tokenizers
- ⚠️ Modelos salvos podem precisar re-download

#### urllib3 (1.26.20 → 2.6.0)
- ⚠️ API mudou para v2.x (major version)
- ⚠️ Algumas funções deprecadas removidas

### 2. Testes Necessários

Após atualizar, testar:

- [ ] API inicia sem erros
- [ ] Endpoints de autenticação (/login, /cadastro)
- [ ] Endpoints de estudo (/estudo/iniciar, /estudo/responder)
- [ ] Endpoints de peças (/pecas/avaliar)
- [ ] Chat com IA (/chat/message)
- [ ] Geração de embeddings
- [ ] Modelos de IA carregam corretamente
- [ ] Banco de dados conecta

---

## 📋 Checklist de Execução

### Hoje (Opção A - CRÍTICOS):
- [ ] Backup do ambiente: `pip freeze > requirements_backup.txt`
- [ ] Atualizar FastAPI, Starlette, python-multipart
- [ ] Atualizar requests, urllib3
- [ ] Atualizar werkzeug
- [ ] Testar API: `python api/api_server.py`
- [ ] Testar endpoints principais (Postman/curl)
- [ ] Commit: `git commit -am "fix: atualizar pacotes críticos (P0)"`

### Semana 1 (Opção B - COMPLETO):
- [ ] Criar branch: `git checkout -b fix/security-vulnerabilities`
- [ ] Executar Opção A primeiro
- [ ] Atualizar PyTorch e Transformers
- [ ] Testar modelos de IA
- [ ] Atualizar outros pacotes P1 e P2
- [ ] Testar suite completa
- [ ] Atualizar requirements.txt
- [ ] Pull request para main
- [ ] Deploy em staging para validação

---

## 🎯 Recomendação Final

**HOJE**: Executar **Opção A** (CRÍTICOS apenas)
- ✅ Elimina 12 vulnerabilidades críticas
- ✅ Risco baixo de quebrar funcionalidades
- ✅ Tempo: 30 minutos

**Próxima Semana**: Executar **Opção B** (COMPLETO)
- ✅ Elimina TODAS as 46 vulnerabilidades
- ⚠️ Requer testes extensivos
- ⏱️ Tempo: 4-6 horas

**Alternativa**: Se não puder testar PyTorch/Transformers agora:
- Executar Opção A HOJE
- Criar issue para rastrear P1/P2
- Planejar upgrade de ML/AI para próximo sprint

---

## 📊 Comandos de Auditoria

### Verificar vulnerabilidades:
```bash
pip-audit
```

### Verificar versões instaladas:
```bash
pip list --outdated
```

### Verificar dependências:
```bash
pip check
```

---

**Ação Imediata Recomendada**: Executar Opção A (CRÍTICOS) nos próximos 30 minutos.
