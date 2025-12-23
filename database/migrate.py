"""
JURIS_IA_CORE_V1 - Utilitário de Migração de Banco de Dados
============================================================

Script para gerenciar migrações do banco de dados usando Alembic.

Comandos disponíveis:
    python database/migrate.py init        - Inicializa sistema de migrações
    python database/migrate.py create      - Cria nova migração (autogenerate)
    python database/migrate.py upgrade     - Aplica todas as migrações pendentes
    python database/migrate.py downgrade   - Reverte última migração
    python database/migrate.py current     - Mostra revisão atual
    python database/migrate.py history     - Mostra histórico de migrações

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 1.0.0
"""

import sys
import os
from alembic.config import Config
from alembic import command
import argparse

# Adicionar path do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import DatabaseConfig, init_database


def get_alembic_config() -> Config:
    """Retorna configuração do Alembic"""
    # Path para alembic.ini
    ini_path = os.path.join(os.path.dirname(__file__), "alembic.ini")

    # Criar config
    alembic_cfg = Config(ini_path)

    # Sobrescrever database URL com variáveis de ambiente
    db_config = DatabaseConfig()
    alembic_cfg.set_main_option("sqlalchemy.url", db_config.get_database_url())

    return alembic_cfg


def init_migrations():
    """Inicializa o sistema de migrações"""
    print("Inicializando sistema de migrações...")

    alembic_cfg = get_alembic_config()

    # Criar diretório de migrações se não existir
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations", "versions")
    os.makedirs(migrations_dir, exist_ok=True)

    print("✓ Sistema de migrações inicializado")
    print(f"  Diretório: {migrations_dir}")


def create_migration(message: str = None, autogenerate: bool = True):
    """
    Cria nova migração

    Args:
        message: Mensagem descritiva da migração
        autogenerate: Se True, gera migração automaticamente baseada nos models
    """
    if not message:
        message = input("Digite a mensagem da migração: ").strip()
        if not message:
            message = "auto_migration"

    print(f"Criando migração: {message}")

    alembic_cfg = get_alembic_config()

    # Criar revisão
    command.revision(
        alembic_cfg,
        message=message,
        autogenerate=autogenerate
    )

    print("✓ Migração criada com sucesso")
    print("  Revise o arquivo gerado em database/migrations/versions/")
    print("  Execute 'python database/migrate.py upgrade' para aplicar")


def upgrade_database(revision: str = "head"):
    """
    Aplica migrações pendentes

    Args:
        revision: Revisão alvo (default: 'head' = última)
    """
    print(f"Aplicando migrações até: {revision}")

    alembic_cfg = get_alembic_config()

    try:
        command.upgrade(alembic_cfg, revision)
        print("✓ Migrações aplicadas com sucesso")
    except Exception as e:
        print(f"✗ Erro ao aplicar migrações: {e}")
        sys.exit(1)


def downgrade_database(revision: str = "-1"):
    """
    Reverte migrações

    Args:
        revision: Revisão alvo (default: '-1' = reverter uma)
    """
    print(f"Revertendo migração para: {revision}")

    alembic_cfg = get_alembic_config()

    confirm = input("ATENÇÃO: Isto pode causar perda de dados. Continuar? (s/N): ")
    if confirm.lower() != 's':
        print("Operação cancelada")
        return

    try:
        command.downgrade(alembic_cfg, revision)
        print("✓ Migração revertida com sucesso")
    except Exception as e:
        print(f"✗ Erro ao reverter migração: {e}")
        sys.exit(1)


def show_current():
    """Mostra revisão atual do banco"""
    print("Revisão atual do banco de dados:")

    alembic_cfg = get_alembic_config()
    command.current(alembic_cfg, verbose=True)


def show_history():
    """Mostra histórico de migrações"""
    print("Histórico de migrações:")

    alembic_cfg = get_alembic_config()
    command.history(alembic_cfg, verbose=True)


def stamp_database(revision: str = "head"):
    """
    Marca o banco de dados com uma revisão específica sem executar migrações.
    Útil quando você criou as tabelas manualmente e quer iniciar o controle de versão.

    Args:
        revision: Revisão para marcar (default: 'head')
    """
    print(f"Marcando banco de dados com revisão: {revision}")

    alembic_cfg = get_alembic_config()

    confirm = input("Isto marcará o banco sem executar migrações. Continuar? (s/N): ")
    if confirm.lower() != 's':
        print("Operação cancelada")
        return

    try:
        command.stamp(alembic_cfg, revision)
        print("✓ Banco de dados marcado com sucesso")
    except Exception as e:
        print(f"✗ Erro ao marcar banco: {e}")
        sys.exit(1)


def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description="Gerenciador de Migrações - JURIS_IA_CORE_V1"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: init
    subparsers.add_parser("init", help="Inicializa sistema de migrações")

    # Comando: create
    create_parser = subparsers.add_parser("create", help="Cria nova migração")
    create_parser.add_argument("-m", "--message", help="Mensagem da migração")
    create_parser.add_argument(
        "--no-autogenerate",
        action="store_true",
        help="Não gerar migração automaticamente"
    )

    # Comando: upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Aplica migrações")
    upgrade_parser.add_argument(
        "-r", "--revision",
        default="head",
        help="Revisão alvo (default: head)"
    )

    # Comando: downgrade
    downgrade_parser = subparsers.add_parser("downgrade", help="Reverte migrações")
    downgrade_parser.add_argument(
        "-r", "--revision",
        default="-1",
        help="Revisão alvo (default: -1 = reverter uma)"
    )

    # Comando: current
    subparsers.add_parser("current", help="Mostra revisão atual")

    # Comando: history
    subparsers.add_parser("history", help="Mostra histórico de migrações")

    # Comando: stamp
    stamp_parser = subparsers.add_parser("stamp", help="Marca revisão sem executar")
    stamp_parser.add_argument(
        "-r", "--revision",
        default="head",
        help="Revisão para marcar (default: head)"
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Executar comando
    try:
        if args.command == "init":
            init_migrations()

        elif args.command == "create":
            create_migration(
                message=args.message,
                autogenerate=not args.no_autogenerate
            )

        elif args.command == "upgrade":
            upgrade_database(revision=args.revision)

        elif args.command == "downgrade":
            downgrade_database(revision=args.revision)

        elif args.command == "current":
            show_current()

        elif args.command == "history":
            show_history()

        elif args.command == "stamp":
            stamp_database(revision=args.revision)

    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
