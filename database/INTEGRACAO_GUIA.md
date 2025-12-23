# GUIA DE INTEGRAÇÃO - Database + Engines
## JURIS_IA_CORE_V1

**Data:** 2025-12-17
**Versão:** 1.0.0
**Autor:** Sistema JURIS_IA_CORE_V1

---

## ÍNDICE

1. [Visão Geral](#1-visão-geral)
2. [Instalação e Configuração](#2-instalação-e-configuração)
3. [Estrutura do Sistema](#3-estrutura-do-sistema)
4. [Uso das Camadas](#4-uso-das-camadas)
5. [Integração com Engines](#5-integração-com-engines)
6. [Exemplos Práticos](#6-exemplos-práticos)
7. [Migrações](#7-migrações)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. VISÃO GERAL

O sistema de banco de dados do JURIS_IA_CORE_V1 foi projetado com arquitetura em camadas:

```
┌─────────────────────────────────────────────┐
│         ENGINES (Business Logic)            │
│  explanation_engine, memory_engine, etc.    │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│      REPOSITORIES (Data Access Layer)       │
│  UserRepository, PerfilRepository, etc.     │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│     SQLALCHEMY MODELS (ORM)                 │
│  User, PerfilJuridico, InteracaoQuestao     │
└─────────────────────┬───────────────────────┘
                      │
┌─────────────────────▼───────────────────────┐
│        POSTGRESQL DATABASE                  │
│  Tables, Indices, Triggers, Constraints     │
└─────────────────────────────────────────────┘
```

### Princípios Arquiteturais

1. **Separação de Responsabilidades**: Cada camada tem função clara
2. **Repository Pattern**: Acesso aos dados abstraído
3. **Session Management**: Controle automático de transações
4. **LGPD by Design**: Governança de dados desde a concepção
5. **Persistência Cognitiva**: Perfil do aluno é fonte da verdade

---

## 2. INSTALAÇÃO E CONFIGURAÇÃO

### 2.1. Pré-requisitos

- Python 3.10+
- PostgreSQL 14+
- pip (gerenciador de pacotes Python)

### 2.2. Instalação de Dependências

```bash
# Navegar para o diretório do projeto
cd D:/JURIS_IA_CORE_V1

# Instalar dependências
pip install -r requirements.txt

# Dependências principais instaladas:
# - sqlalchemy>=2.0.23
# - psycopg2-binary>=2.9.9
# - alembic>=1.13.0
# - python-dotenv>=1.0.0
```

### 2.3. Configuração de Ambiente

1. **Copiar arquivo de exemplo:**

```bash
cp .env.example .env
```

2. **Editar `.env` com suas configurações:**

```env
# DATABASE
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=juris_ia
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha_aqui

# DATABASE POOL
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# DEBUG (desenvolvimento)
DB_ECHO=false
DEBUG=true
```

### 2.4. Criação do Banco de Dados

**Opção 1: Setup Completo (Recomendado)**

```bash
python database/setup.py --full-setup
```

Isto irá:
1. Criar banco de dados PostgreSQL
2. Criar extensões (uuid-ossp, pgcrypto)
3. Criar todas as tabelas
4. Popular dados de exemplo (questões, usuário teste)
5. Validar instalação

**Opção 2: Setup Manual**

```bash
# Apenas criar banco
python database/setup.py --create-db

# Apenas criar tabelas
python database/setup.py --tables-only

# Popular dados de exemplo
python database/setup.py --seed

# Validar instalação
python database/setup.py --validate
```

### 2.5. Verificação da Instalação

```bash
# Testar conexão
python database/connection.py

# Verificar saúde do banco
python -c "from database.connection import check_database_health; import json; print(json.dumps(check_database_health(), indent=2))"
```

---

## 3. ESTRUTURA DO SISTEMA

### 3.1. Arquivos Principais

```
database/
├── models.py              # Modelos SQLAlchemy (15 entidades)
├── connection.py          # Gerenciamento de conexões e sessões
├── repositories.py        # Camada de repositórios (DAOs)
├── setup.py               # Script de instalação
├── migrate.py             # Gerenciador de migrações
├── schema.sql             # DDL completo PostgreSQL
├── alembic.ini            # Configuração Alembic
├── requirements.txt       # Dependências específicas do DB
├── migrations/
│   ├── env.py             # Ambiente de migração
│   ├── script.py.mako     # Template de migração
│   └── versions/          # Histórico de migrações
└── README.md              # Documentação do banco

engines/
├── memory_engine.py       # Engine original (in-memory)
├── memory_engine_db.py    # Engine integrado com DB ✓
├── explanation_engine.py  # A integrar
├── decision_engine.py     # A integrar
├── question_engine.py     # A integrar
└── piece_engine.py        # A integrar
```

### 3.2. Entidades do Banco de Dados

#### Principais (14 tabelas)

1. **users** - Dados cadastrais
2. **perfil_juridico** - **CORE** - Perfil cognitivo (8 dimensões)
3. **progresso_disciplina** - Progresso por disciplina
4. **progresso_topico** - Progresso granular por tópico
5. **sessao_estudo** - Sessões de estudo
6. **interacao_questao** - **IMPORTANTE** - Cada resposta
7. **analise_erro** - Análise profunda de erros
8. **pratica_peca** - Prática 2ª Fase OAB
9. **erro_peca** - Erros em peças
10. **revisao_agendada** - Revisões espaçadas
11. **snapshot_cognitivo** - Snapshots temporais
12. **metricas_temporais** - Métricas pré-calculadas
13. **questoes_banco** - Banco de questões
14. **log_sistema** - Logs de auditoria
15. **consentimentos** - Consentimentos LGPD

---

## 4. USO DAS CAMADAS

### 4.1. Connection Layer

**Uso Básico com Context Manager:**

```python
from database.connection import get_db_session

# Commit automático
with get_db_session() as session:
    user = session.query(User).first()
    # ... operações ...
# Sessão automaticamente fechada e commitada

# Sem commit automático
from database.connection import get_db_session_no_commit

with get_db_session_no_commit() as session:
    user = session.query(User).first()
    # Controle manual
    session.commit()
```

**Decorator para Injeção de Sessão:**

```python
from database.connection import with_db_session

@with_db_session
def minha_funcao(session, user_id):
    user = session.query(User).get(user_id)
    return user

# Chamar função (sessão injetada automaticamente)
usuario = minha_funcao(user_id="...")
```

**Verificar Saúde do Banco:**

```python
from database.connection import check_database_health

health = check_database_health()
print(health)
# {
#   "database": "healthy",
#   "connection_test": True,
#   "tables_exist": True,
#   "table_count": 15,
#   "pool_status": {...}
# }
```

### 4.2. Repository Layer

**Factory Pattern (Recomendado):**

```python
from database.connection import get_db_session
from database.repositories import RepositoryFactory

with get_db_session() as session:
    repos = RepositoryFactory(session)

    # Acessar repositórios
    user = repos.users.get_by_email("teste@juris-ia.com")
    perfil = repos.perfis.get_by_user_id(user.id)
    questoes = repos.questoes.get_random_questions(count=10)
```

**Repositórios Disponíveis:**

- `repos.users` - UserRepository
- `repos.perfis` - PerfilJuridicoRepository
- `repos.progressos_disciplina` - ProgressoDisciplinaRepository
- `repos.progressos_topico` - ProgressoTopicoRepository
- `repos.interacoes` - InteracaoQuestaoRepository
- `repos.analises_erro` - AnaliseErroRepository
- `repos.snapshots` - SnapshotCognitivoRepository
- `repos.questoes` - QuestaoBancoRepository
- `repos.sessoes` - SessaoEstudoRepository

**Operações Comuns:**

```python
# CRIAR
user = repos.users.create(
    nome="João Silva",
    email="joao@example.com",
    cpf="12345678900",
    status=UserStatus.ATIVO
)

# LER
user = repos.users.get_by_id(user_id)
user = repos.users.get_by_email("joao@example.com")

# ATUALIZAR
repos.users.update(
    user_id,
    nome="João Silva Junior",
    telefone="11999999999"
)

# DELETAR
repos.users.delete(user_id)

# CONTAR
total = repos.users.count()
```

### 4.3. Model Layer

**Importação de Modelos:**

```python
from database.models import (
    User, PerfilJuridico, InteracaoQuestao,
    UserStatus, NivelDominio, TipoResposta
)

# Acesso direto via SQLAlchemy (quando necessário)
with get_db_session() as session:
    users = session.query(User).filter(
        User.status == UserStatus.ATIVO
    ).all()
```

**Enums Disponíveis:**

```python
from database.models import (
    UserStatus,              # ATIVO, INATIVO, ANONIMIZADO, etc.
    NivelDominio,            # INICIANTE -> EXPERT
    TipoResposta,            # CORRETA, INCORRETA, ANULADA
    TipoErro,                # 28 tipos de erros
    DificuldadeQuestao,      # FACIL, MEDIO, DIFICIL
    TipoTriggerSnapshot,     # FIM_SESSAO, MUDANCA_NIVEL, etc.
    TipoConsentimento        # DADOS_CADASTRAIS, etc.
)
```

---

## 5. INTEGRAÇÃO COM ENGINES

### 5.1. Memory Engine (Exemplo Completo)

O `memory_engine_db.py` foi criado como exemplo de integração completa.

**Comparação:**

| Aspecto | memory_engine.py (Original) | memory_engine_db.py (DB-Integrated) |
|---------|---------------------------|--------------------------------|
| Storage | In-memory (dicionários) | PostgreSQL (persistente) |
| Sessões | Python objects | SQLAlchemy sessions |
| Persistência | Não (perdido ao reiniciar) | Sim (banco de dados) |
| Escalabilidade | Limitada (RAM) | Alta (disco + indices) |
| LGPD | Não implementado | Completo (anonimização) |

**Uso do Memory Engine DB:**

```python
from engines.memory_engine_db import MemoryEngineDB
from uuid import UUID

# Criar engine
engine = MemoryEngineDB()

# Adicionar tópico à memória
resultado = engine.adicionar_topico_memoria(
    user_id=UUID("..."),
    disciplina="Direito Penal",
    topico="Legítima Defesa",
    acertou_na_introducao=True
)
# Retorna cronograma 1-24-7-30 dias

# Processar revisão
resultado = engine.processar_revisao(
    user_id=UUID("..."),
    disciplina="Direito Penal",
    topico="Legítima Defesa",
    acertou=True
)
# Atualiza fator de retenção, agenda próxima revisão

# Obter revisões pendentes
revisoes = engine.obter_revisoes_pendentes(
    user_id=UUID("..."),
    limite=10
)

# Analisar memória
analise = engine.analisar_memoria(user_id=UUID("..."))
# {
#   "total_topicos": 45,
#   "distribuicao_forca": {...},
#   "topicos_dominados": [...],
#   "taxa_retencao_media": 72.5
# }

# Detectar esquecimento
alertas = engine.detectar_esquecimento(user_id=UUID("..."))
# [{
#   "tipo": "regressao",
#   "topico": "Dolo eventual",
#   "gravidade": "ALTA",
#   "mensagem": "..."
# }]
```

### 5.2. Pattern para Integração de Outros Engines

**Template para integrar engines:**

```python
# 1. Importar dependências
from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import TipoResposta, NivelDominio
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

# 2. Criar classe do engine
class MinhaEngineDB:
    """Engine integrada com banco de dados"""

    def __init__(self):
        logger.info("MinhaEngineDB inicializada")

    def minha_funcao(self, user_id: UUID, parametro: str):
        """Função que usa banco de dados"""
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar dados
                user = repos.users.get_by_id(user_id)
                if not user:
                    return {"erro": "Usuário não encontrado"}

                perfil = repos.perfis.get_by_user_id(user_id)

                # Lógica do engine
                resultado = self._processar_logica(perfil, parametro)

                # Atualizar dados
                repos.perfis.increment_score(user_id, points=10)

                # Retornar resultado
                return {"status": "sucesso", "resultado": resultado}

        except Exception as e:
            logger.error(f"Erro: {e}")
            return {"erro": str(e)}

    def _processar_logica(self, perfil, parametro):
        """Lógica interna do engine"""
        # Implementar lógica
        return {}

# 3. Factory function
def criar_minha_engine_db():
    return MinhaEngineDB()
```

---

## 6. EXEMPLOS PRÁTICOS

### 6.1. Criar Novo Usuário com Perfil

```python
from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import UserStatus

with get_db_session() as session:
    repos = RepositoryFactory(session)

    # Criar usuário
    user = repos.users.create(
        nome="Maria Santos",
        email="maria@example.com",
        cpf="98765432100",
        status=UserStatus.ATIVO
    )

    # Criar perfil jurídico inicial
    perfil = repos.perfis.create_initial_profile(user.id)

    print(f"Usuário criado: {user.id}")
    print(f"Perfil criado: {perfil.id}")
    print(f"Nível inicial: {perfil.nivel_geral}")
```

### 6.2. Registrar Interação com Questão

```python
from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import TipoResposta, DificuldadeQuestao
from uuid import UUID

user_id = UUID("...")
questao_id = UUID("...")

with get_db_session() as session:
    repos = RepositoryFactory(session)

    # Registrar interação
    interacao = repos.interacoes.create_interaction(
        user_id=user_id,
        questao_id=questao_id,
        disciplina="Direito Civil",
        topico="Prescrição",
        tipo_resposta=TipoResposta.CORRETA,
        alternativa_escolhida="C",
        alternativa_correta="C",
        tempo_resposta_segundos=45,
        nivel_confianca=0.8
    )

    # Atualizar progresso da disciplina
    progresso = repos.progressos_disciplina.update_stats(
        user_id=user_id,
        disciplina="Direito Civil",
        acertou=True,
        tempo_minutos=1,
        dificuldade=DificuldadeQuestao.MEDIO
    )

    # Atualizar perfil
    perfil = repos.perfis.get_by_user_id(user_id)
    perfil.total_questoes_respondidas += 1
    perfil.total_questoes_corretas += 1

    repos.perfis.update_accuracy_rate(user_id)
    repos.perfis.increment_score(user_id, points=10)

    print(f"Interação registrada: {interacao.id}")
    print(f"Pontuação atualizada: {perfil.pontuacao_global}")
```

### 6.3. Criar Snapshot Cognitivo

```python
from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import TipoTriggerSnapshot
from uuid import UUID

user_id = UUID("...")

with get_db_session() as session:
    repos = RepositoryFactory(session)

    # Coletar dados para snapshot
    perfil = repos.perfis.get_by_user_id(user_id)
    progressos = repos.progressos_disciplina.get_all_by_user(user_id)
    interacoes_recentes = repos.interacoes.get_user_interactions(
        user_id, limit=50
    )

    # Criar snapshot
    snapshot = repos.snapshots.create_snapshot(
        user_id=user_id,
        tipo_trigger=TipoTriggerSnapshot.FIM_SESSAO,
        perfil_completo={
            "nivel": perfil.nivel_geral.value,
            "pontuacao": perfil.pontuacao_global,
            "taxa_acerto": float(perfil.taxa_acerto_global),
            "estado_emocional": perfil.estado_emocional
        },
        desempenho={
            "total_questoes": perfil.total_questoes_respondidas,
            "total_corretas": perfil.total_questoes_corretas,
            "tempo_estudo_minutos": perfil.total_tempo_estudo_minutos
        },
        padroes_erro={
            "distribuicao": repos.analises_erro.get_user_error_distribution(user_id)
        },
        estado_memoria={
            "topicos_em_revisao": len(progressos)
        },
        predicao={
            "probabilidade_aprovacao": 0.75  # Calcular baseado em dados
        },
        contexto_momento={
            "data": snapshot.momento.isoformat(),
            "motivo": "Fim de sessão de estudo"
        }
    )

    print(f"Snapshot criado: {snapshot.id}")
```

### 6.4. Análise de Desempenho

```python
from database.connection import get_db_session
from database.repositories import RepositoryFactory
from uuid import UUID

user_id = UUID("...")

with get_db_session() as session:
    repos = RepositoryFactory(session)

    # Taxa de acerto por disciplina
    taxas = repos.interacoes.get_accuracy_by_discipline(user_id)
    print("Taxas de acerto:")
    for disciplina, taxa in taxas:
        print(f"  {disciplina}: {taxa}%")

    # Disciplinas mais fracas
    fracas = repos.progressos_disciplina.get_weakest_disciplines(user_id, limit=3)
    print("\nDisciplinas para reforçar:")
    for prog in fracas:
        print(f"  {prog.disciplina}: {prog.taxa_acerto}% ({prog.total_questoes} questões)")

    # Erros não corrigidos
    erros = repos.analises_erro.get_uncorrected_errors(user_id, limit=5)
    print("\nErros pendentes de correção:")
    for erro in erros:
        print(f"  [{erro.tipo_erro.value}] Gravidade: {erro.nivel_gravidade}/10")
```

---

## 7. MIGRAÇÕES

### 7.1. Comandos Básicos

```bash
# Inicializar sistema de migrações
python database/migrate.py init

# Criar nova migração (auto-detecta mudanças nos models)
python database/migrate.py create -m "Adicionar campo X"

# Aplicar todas as migrações pendentes
python database/migrate.py upgrade

# Reverter última migração
python database/migrate.py downgrade

# Ver revisão atual
python database/migrate.py current

# Ver histórico
python database/migrate.py history
```

### 7.2. Fluxo de Desenvolvimento

1. **Modificar models.py**
2. **Criar migração:**
   ```bash
   python database/migrate.py create -m "Descrição da mudança"
   ```
3. **Revisar arquivo gerado** em `database/migrations/versions/`
4. **Aplicar migração:**
   ```bash
   python database/migrate.py upgrade
   ```

### 7.3. Marcar Banco Existente

Se você criou as tabelas manualmente (via `setup.py`) e quer começar a usar migrações:

```bash
# Marca o banco como na última revisão (sem executar migrações)
python database/migrate.py stamp head
```

---

## 8. TROUBLESHOOTING

### 8.1. Problemas Comuns

**Erro: "could not connect to server"**

```bash
# Verificar se PostgreSQL está rodando
# Windows:
services.msc  # Verificar serviço PostgreSQL

# Linux/Mac:
sudo systemctl status postgresql
```

**Erro: "database does not exist"**

```bash
# Criar banco de dados
python database/setup.py --create-db
```

**Erro: "relation does not exist"**

```bash
# Criar tabelas
python database/setup.py --tables-only
```

**Erro: "too many connections"**

Ajustar pool de conexões no `.env`:

```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=5
```

### 8.2. Debug Mode

Ativar logs SQL no `.env`:

```env
DB_ECHO=true
```

Ver todas as queries executadas:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

### 8.3. Limpeza e Reset

**CUIDADO: Operações destrutivas**

```bash
# Remover banco completamente
python database/setup.py --drop-db

# Recriar do zero
python database/setup.py --full-setup
```

---

## PRÓXIMOS PASSOS

1. ✅ Banco de dados configurado
2. ✅ Memory Engine integrado
3. ⏳ Integrar outros engines:
   - `explanation_engine_db.py`
   - `question_engine_db.py`
   - `decision_engine_db.py`
   - `piece_engine_db.py`
4. ⏳ Atualizar `juris_ia.py` orquestrador
5. ⏳ Atualizar `api_server.py` FastAPI
6. ⏳ Criar endpoints API RESTful
7. ⏳ Implementar autenticação JWT
8. ⏳ Deploy em produção

---

## DOCUMENTAÇÃO ADICIONAL

- **Schema SQL**: `database/schema.sql`
- **README Database**: `database/README.md`
- **Relatório Técnico**: `RELATORIO_TECNICO_ARQUITETURA_DADOS_COGNICAO.txt`
- **Documentação Arquitetura**: `database/01_ENTIDADES_PRINCIPAIS.txt` a `05_GOVERNANCA_DADOS_LGPD.txt`

---

## SUPORTE

Para dúvidas ou problemas:

1. Verificar logs: `logs/juris_ia.log`
2. Consultar documentação PostgreSQL: https://www.postgresql.org/docs/
3. Consultar documentação SQLAlchemy: https://docs.sqlalchemy.org/

---

**Fim do Guia de Integração**
