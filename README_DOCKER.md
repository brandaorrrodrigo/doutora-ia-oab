# 🚀 JURIS_IA_CORE_V1 - Docker + Ollama + RTX 3090

Sistema completo de IA jurídica para preparação OAB usando **IA local** (Ollama/Llama) com **GPU NVIDIA RTX 3090**.

## ⚡ Quick Start (1 comando!)

```bash
make quick-start
```

Pronto! Sistema rodando em ~10 minutos com:
- ✅ PostgreSQL + pgvector
- ✅ Redis
- ✅ Ollama com modelos baixados
- ✅ Backend FastAPI
- ✅ 100 embeddings de teste

## 📋 Stack Completa

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| **Backend** | 8000 | API FastAPI |
| **PostgreSQL** | 5432 | Banco de dados + pgvector |
| **Redis** | 6379 | Cache |
| **Ollama** | 11434 | IA local (GPU) |
| **pgAdmin** | 5050 | Interface DB (opcional) |
| **Redis Commander** | 8081 | Interface Redis (opcional) |

## 🎯 Modelos de IA (RTX 3090)

### Embeddings (768 dims)
```bash
nomic-embed-text
Performance: 50-70 questões/seg
Tamanho: 1.5GB
```

### LLM (8B parâmetros)
```bash
llama3.1:8b-instruct-q8_0
Performance: 100-150 tokens/seg (~1-2s por explicação)
Tamanho: 8.5GB
Qualidade: Muito boa
```

### Opção Premium: LLM 70B
```bash
llama3:70b-q4_K_M
Performance: 30-50 tokens/seg (~4-6s por explicação)
Tamanho: 40GB
Qualidade: Excelente (próximo GPT-4)

# Baixar (RTX 3090 aguenta!)
make ollama-pull-70b
```

## 🛠️ Comandos Essenciais

### Gerenciamento
```bash
make up          # Iniciar
make down        # Parar
make restart     # Reiniciar
make logs        # Ver logs
make health      # Verificar saúde
```

### Embeddings
```bash
make populate-embeddings      # Popular TODAS questões (~2 min)
make populate-embeddings-test # Popular 100 (teste)
```

### Ollama
```bash
make ollama-models    # Listar modelos
make ollama-pull-llm  # Baixar LLM 8B
make ollama-pull-70b  # Baixar LLM 70B (máxima qualidade)
```

### Banco de Dados
```bash
make db-shell    # Shell PostgreSQL
make backup-db   # Fazer backup
make restore-db FILE=backup.sql  # Restaurar
```

### Monitoramento
```bash
make nvidia-smi  # Monitorar GPU
make stats       # Estatísticas containers
```

## 📊 Performance Esperada (RTX 3090)

| Operação | Performance |
|----------|-------------|
| **Embeddings** | 50-70 questões/seg |
| **Popular 5K questões** | ~2 minutos |
| **Explicação LLM 8B** | 1-2 segundos |
| **Explicação LLM 70B** | 4-6 segundos |
| **Via cache** | < 50ms |
| **Busca vetorial** | < 50ms |

## 💰 Custos

| Item | OpenAI | **Ollama (você)** |
|------|--------|-------------------|
| Setup embeddings | $0.20 | **$0** |
| Explicações/mês | $1-3 | **$0** |
| Infraestrutura | N/A | Servidor existente |
| **TOTAL** | $1-3/mês | **$0/mês** |

## 🔧 Arquitetura

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   PostgreSQL    │     │    Redis     │     │     Ollama      │
│   (pgvector)    │     │   (cache)    │     │ (GPU/RTX 3090)  │
│   Port: 5432    │     │  Port: 6379  │     │  Port: 11434    │
└────────┬────────┘     └──────┬───────┘     └────────┬────────┘
         │                     │                       │
         │                     │                       │
         └────────────┬────────┴───────────┬──────────┘
                      │                    │
                ┌─────▼────────────────────▼─────┐
                │        Backend (FastAPI)       │
                │          Port: 8000            │
                └────────────────────────────────┘
```

## 📁 Arquivos Importantes

| Arquivo | Descrição |
|---------|-----------|
| `docker-compose.yml` | Configuração completa da stack |
| `Makefile` | Comandos simplificados |
| `.env.docker` | Variáveis de ambiente (copiar para `.env`) |
| `Dockerfile.backend` | Build do backend |
| `GUIA_DEPLOY_DOCKER_RTX3090.txt` | Guia completo |

## 🚀 Deploy

### Desenvolvimento
```bash
make quick-start
make health
make logs
```

### Produção
```bash
# 1. Configurar .env (mudar senhas!)
cp .env.docker .env
nano .env

# 2. Iniciar
make up

# 3. Baixar modelos
make ollama-pull-all

# 4. Popular embeddings
make populate-embeddings

# 5. Backup automático (cron)
0 3 * * * cd /path/to/project && make backup-db
```

## 🔍 Troubleshooting

### GPU não detectada
```bash
# Verificar
nvidia-smi

# Testar no Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Ollama não responde
```bash
docker-compose logs ollama
docker-compose restart ollama
```

### Backend não conecta
```bash
docker-compose logs backend
make health
```

## 📚 Documentação Completa

- `GUIA_SETUP_OLLAMA.txt` - Setup Ollama standalone
- `GUIA_SETUP_RTX3090.txt` - Otimizações RTX 3090
- `GUIA_DEPLOY_DOCKER_RTX3090.txt` - **Guia completo Docker** ⭐
- `RESUMO_IMPLEMENTACAO_P0_OLLAMA.txt` - Visão geral features

## ✅ Checklist

- [ ] Docker + Docker Compose instalados
- [ ] NVIDIA drivers atualizados
- [ ] `make quick-start` executado
- [ ] `make health` retorna tudo OK
- [ ] Acessar http://localhost:8000
- [ ] `make populate-embeddings` concluído
- [ ] Testar explicações via API

## 🎁 Bônus: Ferramentas Admin

```bash
make tools-up
```

Acessar:
- **pgAdmin**: http://localhost:5050
- **Redis Commander**: http://localhost:8081

## 💪 Com sua RTX 3090:

✅ **50-70 embeddings/seg** (3x mais rápido que RTX 3060)
✅ **Popular 5K questões em ~2 min**
✅ **Rodar modelos 70B** (qualidade GPT-4)
✅ **100% privado e sem custos**
✅ **24GB VRAM de sobra**

---

## 🚀 TL;DR

```bash
# Setup completo em 1 comando
make quick-start

# Acessar
open http://localhost:8000

# Monitorar GPU
make nvidia-smi

# Pronto! 🎉
```

**Tempo total: ~10 minutos**
**Custo: R$ 0,00**
**Performance: 🚀🚀🚀**
