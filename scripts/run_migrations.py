"""
Script de Execução de Migrations
=================================

Executa todas as migrations SQL em ordem sequencial.
Usado para inicializar o banco de dados em produção.

Uso:
    python scripts/run_migrations.py

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-28
"""

import os
import sys
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL não configurada!")
    print("Configure a variável de ambiente DATABASE_URL")
    sys.exit(1)

# Diretório de migrations
MIGRATIONS_DIR = Path(__file__).parent.parent / 'database' / 'migrations'


def get_migration_files():
    """Retorna lista de arquivos .sql em ordem"""
    migrations = []

    if not MIGRATIONS_DIR.exists():
        print(f"❌ ERROR: Diretório de migrations não encontrado: {MIGRATIONS_DIR}")
        sys.exit(1)

    for file in sorted(MIGRATIONS_DIR.glob('*.sql')):
        migrations.append(file)

    return migrations


def create_migrations_table(conn):
    """Cria tabela de controle de migrations"""
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
        """)
    conn.commit()
    print("✓ Tabela schema_migrations criada/verificada")


def get_applied_migrations(conn):
    """Retorna lista de migrations já aplicadas"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        return {row[0] for row in cursor.fetchall()}


def apply_migration(conn, migration_file):
    """Aplica uma migration"""
    version = migration_file.stem  # Nome do arquivo sem extensão

    print(f"\n📄 Aplicando migration: {version}")

    try:
        # Ler conteúdo do arquivo
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Executar SQL
        with conn.cursor() as cursor:
            cursor.execute(sql)

            # Registrar migration
            cursor.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s)",
                (version,)
            )

        conn.commit()
        print(f"✓ Migration {version} aplicada com sucesso!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ ERRO ao aplicar migration {version}:")
        print(f"   {str(e)}")
        return False


def run_migrations():
    """Executa todas as migrations pendentes"""
    print("=" * 70)
    print("JURIS_IA - Executar Migrations")
    print("=" * 70)

    # Conectar ao banco
    print(f"\n🔌 Conectando ao banco de dados...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("✓ Conectado com sucesso!")
    except Exception as e:
        print(f"❌ ERRO ao conectar ao banco:")
        print(f"   {str(e)}")
        sys.exit(1)

    try:
        # Criar tabela de controle
        create_migrations_table(conn)

        # Obter migrations
        migration_files = get_migration_files()
        applied_migrations = get_applied_migrations(conn)

        print(f"\n📊 Status:")
        print(f"   Total de migrations: {len(migration_files)}")
        print(f"   Já aplicadas: {len(applied_migrations)}")
        print(f"   Pendentes: {len(migration_files) - len(applied_migrations)}")

        # Aplicar migrations pendentes
        pending_count = 0
        success_count = 0

        for migration_file in migration_files:
            version = migration_file.stem

            if version in applied_migrations:
                print(f"⏭️  Pulando {version} (já aplicada)")
                continue

            pending_count += 1
            if apply_migration(conn, migration_file):
                success_count += 1
            else:
                print(f"\n❌ Parando execução devido a erro em {version}")
                break

        # Resumo
        print("\n" + "=" * 70)
        print("RESUMO")
        print("=" * 70)
        print(f"✓ Migrations aplicadas com sucesso: {success_count}/{pending_count}")

        if success_count == pending_count:
            print("\n🎉 Todas as migrations foram aplicadas com sucesso!")
            return True
        else:
            print("\n⚠️  Algumas migrations falharam. Verifique os erros acima.")
            return False

    finally:
        conn.close()
        print("\n🔌 Conexão fechada")


if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)
