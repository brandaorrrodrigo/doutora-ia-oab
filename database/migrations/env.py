"""
JURIS_IA_CORE_V1 - Alembic Migration Environment
=================================================

Configura o ambiente de migração Alembic.
Este arquivo é executado toda vez que uma migração é rodada.

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 1.0.0
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Adicionar path do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Importar models
from database.models import Base
from database.connection import DatabaseConfig

# Configuração do Alembic
config = context.config

# Interpretar o arquivo de configuração para logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata do SQLAlchemy
target_metadata = Base.metadata

# Sobrescrever sqlalchemy.url com variáveis de ambiente
db_config = DatabaseConfig()
config.set_main_option("sqlalchemy.url", db_config.get_database_url())


def run_migrations_offline() -> None:
    """
    Executa migrações em modo 'offline'.

    Não conecta ao banco de dados, apenas gera o SQL.
    Útil para gerar scripts SQL para executar manualmente.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executa migrações em modo 'online'.

    Conecta ao banco de dados e executa as migrações diretamente.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=False,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
