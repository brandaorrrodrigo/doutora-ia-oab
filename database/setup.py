"""
JURIS_IA_CORE_V1 - Script de Inicialização do Banco de Dados
=============================================================

Script completo para configurar o banco de dados do zero.

Funcionalidades:
1. Cria banco de dados PostgreSQL
2. Cria extensões necessárias
3. Cria todas as tabelas
4. Cria índices e triggers
5. Popula dados iniciais (questões, etc)
6. Valida instalação

Uso:
    python database/setup.py --create-db     # Cria banco e tabelas
    python database/setup.py --drop-db       # CUIDADO: Remove tudo
    python database/setup.py --seed          # Popula dados de exemplo
    python database/setup.py --validate      # Valida instalação

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 1.0.0
"""

import sys
import os
import argparse
import logging
from typing import List

# Adicionar path do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import (
    DatabaseManager, DatabaseConfig, get_db_session,
    init_database, check_database_health
)
from database.models import (
    User, PerfilJuridico, QuestaoBanco,
    UserStatus, NivelDominio, DificuldadeQuestao
)
from database.repositories import RepositoryFactory

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError, OperationalError

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# CRIAÇÃO DO BANCO DE DADOS
# ============================================================================

def create_database():
    """
    Cria o banco de dados PostgreSQL e extensões necessárias.
    Conecta ao banco 'postgres' para criar o novo banco.
    """
    config = DatabaseConfig()

    logger.info(f"Criando banco de dados: {config.database}")

    # Conectar ao banco 'postgres' padrão para criar novo banco
    admin_url = f"postgresql+psycopg2://{config.user}:{config.password}@{config.host}:{config.port}/postgres"

    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

        with admin_engine.connect() as conn:
            # Verificar se banco já existe
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{config.database}'")
            ).scalar()

            if result:
                logger.warning(f"Banco de dados '{config.database}' já existe")
                return False

            # Criar banco
            conn.execute(text(f"CREATE DATABASE {config.database}"))
            logger.info(f"✓ Banco de dados '{config.database}' criado com sucesso")

        admin_engine.dispose()

        # Conectar ao novo banco para criar extensões
        app_engine = create_engine(config.get_database_url())

        with app_engine.connect() as conn:
            # Criar extensão UUID
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\""))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\""))
            conn.commit()
            logger.info("✓ Extensões PostgreSQL criadas")

        app_engine.dispose()

        return True

    except OperationalError as e:
        logger.error(f"✗ Erro ao conectar no PostgreSQL: {e}")
        logger.error("  Verifique se PostgreSQL está rodando e credenciais estão corretas")
        return False

    except Exception as e:
        logger.error(f"✗ Erro ao criar banco de dados: {e}")
        return False


def drop_database():
    """
    CUIDADO: Remove completamente o banco de dados.
    Use apenas em desenvolvimento.
    """
    config = DatabaseConfig()

    logger.warning(f"ATENÇÃO: Removendo banco de dados: {config.database}")

    confirm = input(f"Confirmar remoção do banco '{config.database}'? (digite 'CONFIRMAR'): ")
    if confirm != "CONFIRMAR":
        logger.info("Operação cancelada")
        return False

    # Conectar ao banco 'postgres' padrão
    admin_url = f"postgresql+psycopg2://{config.user}:{config.password}@{config.host}:{config.port}/postgres"

    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

        with admin_engine.connect() as conn:
            # Terminar conexões existentes
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{config.database}'
                  AND pid <> pg_backend_pid()
            """))

            # Remover banco
            conn.execute(text(f"DROP DATABASE IF EXISTS {config.database}"))
            logger.info(f"✓ Banco de dados '{config.database}' removido")

        admin_engine.dispose()
        return True

    except Exception as e:
        logger.error(f"✗ Erro ao remover banco de dados: {e}")
        return False


def create_tables():
    """Cria todas as tabelas do schema"""
    logger.info("Criando tabelas do banco de dados...")

    try:
        db_manager = DatabaseManager()
        db_manager.create_all_tables()
        logger.info("✓ Todas as tabelas criadas com sucesso")
        return True

    except Exception as e:
        logger.error(f"✗ Erro ao criar tabelas: {e}")
        return False


# ============================================================================
# POPULAÇÃO DE DADOS INICIAIS (SEED)
# ============================================================================

def seed_sample_questions():
    """Popula banco com questões de exemplo"""
    logger.info("Populando questões de exemplo...")

    sample_questions = [
        {
            "codigo_questao": "DIR_CONST_001",
            "disciplina": "Direito Constitucional",
            "topico": "Direitos Fundamentais",
            "subtopico": "Direitos Sociais",
            "enunciado": "De acordo com a Constituição Federal, são direitos sociais, EXCETO:",
            "alternativas": {
                "A": "A educação",
                "B": "A saúde",
                "C": "O trabalho",
                "D": "A propriedade privada"
            },
            "alternativa_correta": "D",
            "dificuldade": DificuldadeQuestao.FACIL,
            "explicacao_detalhada": "Os direitos sociais estão previstos no art. 6º da CF/88. A propriedade privada é um direito fundamental individual (art. 5º, XXII), não um direito social.",
            "fundamentacao_legal": {
                "artigos": ["CF/88, art. 6º", "CF/88, art. 5º, XXII"],
                "jurisprudencia": []
            },
            "tags": ["direitos_fundamentais", "direitos_sociais", "CF88"],
            "eh_trap": False,
            "ativa": True
        },
        {
            "codigo_questao": "DIR_PENAL_001",
            "disciplina": "Direito Penal",
            "topico": "Parte Geral",
            "subtopico": "Teoria do Crime",
            "enunciado": "Sobre o crime tentado, é CORRETO afirmar:",
            "alternativas": {
                "A": "A pena da tentativa é sempre reduzida de 1/3 a 2/3",
                "B": "Na tentativa branca, o bem jurídico não é atingido",
                "C": "A tentativa é punível em todos os crimes",
                "D": "Tentativa e consumação têm a mesma pena"
            },
            "alternativa_correta": "B",
            "dificuldade": DificuldadeQuestao.MEDIO,
            "explicacao_detalhada": "Tentativa branca (ou incruenta) é quando o bem jurídico não chega a ser lesionado. A pena é reduzida de 1/3 a 2/3 (alternativa A está incompleta, pois não menciona que pode não haver redução em alguns casos). Nem todos os crimes admitem tentativa (C incorreta). Penas são diferentes (D incorreta).",
            "fundamentacao_legal": {
                "artigos": ["CP, art. 14, II", "CP, art. 14, parágrafo único"],
                "jurisprudencia": []
            },
            "tags": ["teoria_crime", "tentativa", "parte_geral"],
            "eh_trap": True,
            "tipo_trap": "alternativa_incompleta",
            "ativa": True
        },
        {
            "codigo_questao": "DIR_CIVIL_001",
            "disciplina": "Direito Civil",
            "topico": "Parte Geral",
            "subtopico": "Prescrição e Decadência",
            "enunciado": "A respeito da prescrição, assinale a alternativa INCORRETA:",
            "alternativas": {
                "A": "A prescrição pode ser alegada em qualquer grau de jurisdição",
                "B": "O juiz pode reconhecer de ofício a prescrição",
                "C": "A prescrição atinge o direito de ação",
                "D": "A prescrição não corre contra os absolutamente incapazes"
            },
            "alternativa_correta": "C",
            "dificuldade": DificuldadeQuestao.DIFICIL,
            "explicacao_detalhada": "A prescrição atinge a PRETENSÃO (direito de exigir), não o direito de ação em si. Esta é uma confusão conceitual comum. O CC/2002 adotou a teoria de que prescrição extingue a pretensão (art. 189), não o direito de ação.",
            "fundamentacao_legal": {
                "artigos": ["CC, art. 189", "CC, art. 198, I"],
                "jurisprudencia": ["STJ - Teoria da actio nata"]
            },
            "tags": ["prescricao", "parte_geral", "conceitos"],
            "eh_trap": True,
            "tipo_trap": "confusao_conceitual",
            "ativa": True
        },
    ]

    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            for q_data in sample_questions:
                # Verificar se questão já existe
                existing = repos.questoes.get_by_codigo(q_data["codigo_questao"])
                if existing:
                    logger.debug(f"Questão {q_data['codigo_questao']} já existe, pulando")
                    continue

                # Criar questão
                repos.questoes.create(**q_data)
                logger.debug(f"✓ Questão {q_data['codigo_questao']} criada")

        logger.info(f"✓ {len(sample_questions)} questões de exemplo criadas")
        return True

    except Exception as e:
        logger.error(f"✗ Erro ao popular questões: {e}")
        return False


def seed_test_user():
    """Cria usuário de teste"""
    logger.info("Criando usuário de teste...")

    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # Verificar se usuário já existe
            existing = repos.users.get_by_email("teste@juris-ia.com")
            if existing:
                logger.info("Usuário de teste já existe")
                return True

            # Criar usuário
            user = repos.users.create(
                nome="Usuário Teste",
                email="teste@juris-ia.com",
                cpf="12345678900",
                status=UserStatus.ATIVO
            )

            # Criar perfil jurídico inicial
            perfil = repos.perfis.create_initial_profile(user.id)

            logger.info(f"✓ Usuário de teste criado: {user.email}")
            logger.info(f"  ID: {user.id}")
            logger.info(f"  Perfil ID: {perfil.id}")

        return True

    except Exception as e:
        logger.error(f"✗ Erro ao criar usuário de teste: {e}")
        return False


def seed_all():
    """Popula todos os dados de exemplo"""
    logger.info("Populando todos os dados de exemplo...")

    success = True
    success = seed_sample_questions() and success
    success = seed_test_user() and success

    if success:
        logger.info("✓ Todos os dados de exemplo criados com sucesso")
    else:
        logger.warning("⚠ Alguns dados não foram criados (verifique logs acima)")

    return success


# ============================================================================
# VALIDAÇÃO
# ============================================================================

def validate_installation():
    """Valida se banco foi instalado corretamente"""
    logger.info("Validando instalação do banco de dados...")

    try:
        # 1. Verificar saúde do banco
        health = check_database_health()

        if health["database"] != "healthy":
            logger.error("✗ Banco de dados não está saudável")
            logger.error(f"  Erro: {health.get('error', 'Desconhecido')}")
            return False

        logger.info("✓ Banco de dados está saudável")

        # 2. Verificar se tabelas existem
        if not health.get("tables_exist"):
            logger.error("✗ Tabelas não foram criadas")
            return False

        table_count = health.get("table_count", 0)
        logger.info(f"✓ {table_count} tabelas criadas")

        # 3. Verificar pool de conexões
        pool_status = health.get("pool_status")
        if pool_status:
            logger.info(f"✓ Pool de conexões: {pool_status}")

        # 4. Contar registros
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            user_count = repos.users.count()
            questao_count = repos.questoes.count()

            logger.info(f"  Usuários: {user_count}")
            logger.info(f"  Questões: {questao_count}")

        logger.info("✓ Validação concluída com sucesso")
        return True

    except Exception as e:
        logger.error(f"✗ Erro na validação: {e}")
        return False


# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="Setup do Banco de Dados - JURIS_IA_CORE_V1"
    )

    parser.add_argument(
        "--create-db",
        action="store_true",
        help="Cria banco de dados e tabelas"
    )

    parser.add_argument(
        "--drop-db",
        action="store_true",
        help="CUIDADO: Remove completamente o banco de dados"
    )

    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="Cria apenas as tabelas (banco já existe)"
    )

    parser.add_argument(
        "--seed",
        action="store_true",
        help="Popula dados de exemplo"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Valida instalação do banco"
    )

    parser.add_argument(
        "--full-setup",
        action="store_true",
        help="Setup completo: criar banco + tabelas + seed + validação"
    )

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        sys.exit(1)

    success = True

    try:
        # Full setup
        if args.full_setup:
            logger.info("=== SETUP COMPLETO DO BANCO DE DADOS ===\n")

            logger.info("1/4: Criando banco de dados...")
            if not create_database():
                logger.warning("Banco já existe, continuando...")

            logger.info("\n2/4: Criando tabelas...")
            if not create_tables():
                success = False

            logger.info("\n3/4: Populando dados de exemplo...")
            if not seed_all():
                logger.warning("Alguns dados não foram criados")

            logger.info("\n4/4: Validando instalação...")
            if not validate_installation():
                success = False

            if success:
                logger.info("\n✓ Setup completo concluído com sucesso!")
                logger.info("\nPróximos passos:")
                logger.info("1. Configure as variáveis de ambiente (POSTGRES_*)")
                logger.info("2. Teste a conexão: python database/connection.py")
                logger.info("3. Inicie o sistema: python engines/juris_ia.py")
            else:
                logger.error("\n✗ Setup completado com erros (verifique logs acima)")

            sys.exit(0 if success else 1)

        # Comandos individuais
        if args.drop_db:
            success = drop_database() and success

        if args.create_db:
            success = create_database() and success
            success = create_tables() and success

        if args.tables_only:
            success = create_tables() and success

        if args.seed:
            success = seed_all() and success

        if args.validate:
            success = validate_installation() and success

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\nOperação cancelada pelo usuário")
        sys.exit(1)

    except Exception as e:
        logger.error(f"\n✗ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
