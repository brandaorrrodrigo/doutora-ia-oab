# ================================================================================
# MAKEFILE: JURIS_IA_CORE_V1 (DOCKER + OLLAMA + RTX 3090)
# ================================================================================

.PHONY: help setup up down restart logs ps clean ollama-models db-migrate populate-embeddings test health

# Cores para output
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
RESET  := $(shell tput -Txterm sgr0)

## help: Exibe esta mensagem de ajuda
help:
	@echo ''
	@echo 'Comandos disponíveis:'
	@echo ''
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## /  /'
	@echo ''

## setup: Configuração inicial (primeira vez)
setup:
	@echo "$(GREEN)Configurando ambiente...$(RESET)"
	cp .env.docker .env
	docker network create juris_ia_network || true
	@echo "$(GREEN)✓ Ambiente configurado!$(RESET)"
	@echo ""
	@echo "Próximo passo: make up"

## up: Inicia todos os containers
up:
	@echo "$(GREEN)Iniciando containers...$(RESET)"
	docker-compose up -d
	@echo ""
	@echo "$(GREEN)✓ Containers iniciados!$(RESET)"
	@echo ""
	@echo "Aguardando serviços ficarem prontos..."
	sleep 10
	@make health

## up-build: Rebuilda e inicia containers
up-build:
	@echo "$(GREEN)Rebuildando e iniciando containers...$(RESET)"
	docker-compose up -d --build

## down: Para todos os containers
down:
	@echo "$(YELLOW)Parando containers...$(RESET)"
	docker-compose down

## down-volumes: Para containers e remove volumes (CUIDADO!)
down-volumes:
	@echo "$(YELLOW)⚠ CUIDADO: Isso vai remover TODOS os dados!$(RESET)"
	@read -p "Tem certeza? (s/n) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Ss]$$ ]]; then \
		docker-compose down -v; \
	fi

## restart: Reinicia todos os containers
restart:
	@echo "$(YELLOW)Reiniciando containers...$(RESET)"
	docker-compose restart
	@echo "$(GREEN)✓ Containers reiniciados!$(RESET)"

## logs: Exibe logs de todos os containers
logs:
	docker-compose logs -f

## logs-backend: Logs apenas do backend
logs-backend:
	docker-compose logs -f backend

## logs-ollama: Logs apenas do Ollama
logs-ollama:
	docker-compose logs -f ollama

## ps: Lista containers em execução
ps:
	docker-compose ps

## health: Verifica saúde dos serviços
health:
	@echo "$(GREEN)Verificando saúde dos serviços...$(RESET)"
	@echo ""
	@echo "PostgreSQL:"
	@docker-compose exec -T postgres pg_isready -U juris_ia_user -d juris_ia && echo "  ✓ OK" || echo "  ✗ FALHOU"
	@echo ""
	@echo "Redis:"
	@docker-compose exec -T redis redis-cli ping && echo "  ✓ OK" || echo "  ✗ FALHOU"
	@echo ""
	@echo "Ollama:"
	@curl -s http://localhost:11434/api/tags > /dev/null && echo "  ✓ OK" || echo "  ✗ FALHOU"
	@echo ""
	@echo "Backend:"
	@curl -s http://localhost:8000/health > /dev/null && echo "  ✓ OK" || echo "  ✗ FALHOU"

## ollama-models: Verifica modelos Ollama instalados
ollama-models:
	@echo "$(GREEN)Modelos Ollama instalados:$(RESET)"
	@docker-compose exec ollama ollama list

## ollama-pull-embedding: Baixa modelo de embedding
ollama-pull-embedding:
	@echo "$(GREEN)Baixando modelo de embedding: nomic-embed-text$(RESET)"
	docker-compose exec ollama ollama pull nomic-embed-text

## ollama-pull-llm: Baixa modelo LLM (8b)
ollama-pull-llm:
	@echo "$(GREEN)Baixando modelo LLM: llama3.1:8b-instruct-q8_0$(RESET)"
	docker-compose exec ollama ollama pull llama3.1:8b-instruct-q8_0

## ollama-pull-70b: Baixa modelo LLM grande (70b - RTX 3090)
ollama-pull-70b:
	@echo "$(GREEN)Baixando modelo LLM 70B: llama3:70b-q4_K_M$(RESET)"
	@echo "$(YELLOW)⚠ Isso vai baixar ~40GB. Tem certeza? (Ctrl+C para cancelar)$(RESET)"
	@sleep 5
	docker-compose exec ollama ollama pull llama3:70b-q4_K_M

## ollama-pull-all: Baixa todos os modelos recomendados
ollama-pull-all: ollama-pull-embedding ollama-pull-llm

## db-shell: Acessa shell do PostgreSQL
db-shell:
	docker-compose exec postgres psql -U juris_ia_user -d juris_ia

## db-migrate: Executa migrações do banco
db-migrate:
	@echo "$(GREEN)Executando migrações...$(RESET)"
	docker-compose exec backend python -c "from database import run_migrations; run_migrations()"
	@echo "$(GREEN)✓ Migrações concluídas!$(RESET)"

## populate-embeddings: Popula embeddings das questões
populate-embeddings:
	@echo "$(GREEN)Populando embeddings...$(RESET)"
	docker-compose exec backend python scripts/popular_embeddings_ollama.py --modelo nomic-embed-text
	@echo "$(GREEN)✓ Embeddings populados!$(RESET)"

## populate-embeddings-test: Popula apenas 100 questões (teste)
populate-embeddings-test:
	@echo "$(GREEN)Populando 100 embeddings de teste...$(RESET)"
	docker-compose exec backend python scripts/popular_embeddings_ollama.py --modelo nomic-embed-text --limite 100

## test: Executa testes
test:
	docker-compose exec backend pytest tests/ -v

## shell-backend: Acessa shell do container backend
shell-backend:
	docker-compose exec backend bash

## shell-ollama: Acessa shell do container Ollama
shell-ollama:
	docker-compose exec ollama bash

## nvidia-smi: Monitora GPU (RTX 3090)
nvidia-smi:
	watch -n 1 nvidia-smi

## clean: Remove containers parados e images não usadas
clean:
	@echo "$(YELLOW)Limpando containers e images...$(RESET)"
	docker-compose down
	docker system prune -f
	@echo "$(GREEN)✓ Limpeza concluída!$(RESET)"

## tools-up: Inicia ferramentas administrativas (pgAdmin + Redis Commander)
tools-up:
	@echo "$(GREEN)Iniciando ferramentas administrativas...$(RESET)"
	docker-compose --profile tools up -d pgadmin redis_commander
	@echo ""
	@echo "$(GREEN)✓ Ferramentas disponíveis:$(RESET)"
	@echo "  pgAdmin:         http://localhost:5050"
	@echo "  Redis Commander: http://localhost:8081"

## tools-down: Para ferramentas administrativas
tools-down:
	docker-compose --profile tools down pgadmin redis_commander

## backup-db: Faz backup do banco de dados
backup-db:
	@echo "$(GREEN)Fazendo backup do banco...$(RESET)"
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U juris_ia_user juris_ia > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup salvo em backups/$(RESET)"

## restore-db: Restaura backup do banco (especificar FILE=backup.sql)
restore-db:
	@if [ -z "$(FILE)" ]; then \
		echo "$(YELLOW)Uso: make restore-db FILE=backups/backup.sql$(RESET)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)⚠ Isso vai substituir o banco atual!$(RESET)"
	@read -p "Tem certeza? (s/n) " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Ss]$$ ]]; then \
		docker-compose exec -T postgres psql -U juris_ia_user juris_ia < $(FILE); \
		echo "$(GREEN)✓ Backup restaurado!$(RESET)"; \
	fi

## stats: Exibe estatísticas dos containers
stats:
	docker stats --no-stream

## quick-start: Setup completo automatizado (PRIMEIRA VEZ)
quick-start: setup up ollama-pull-all db-migrate populate-embeddings-test
	@echo ""
	@echo "$(GREEN)================================$(RESET)"
	@echo "$(GREEN)✓ Setup completo!$(RESET)"
	@echo "$(GREEN)================================$(RESET)"
	@echo ""
	@echo "Serviços disponíveis:"
	@echo "  Backend API:  http://localhost:8000"
	@echo "  Ollama API:   http://localhost:11434"
	@echo ""
	@echo "Próximos passos:"
	@echo "  1. make logs           - Ver logs em tempo real"
	@echo "  2. make health         - Verificar saúde dos serviços"
	@echo "  3. make populate-embeddings - Popular todas as questões"
	@echo ""
