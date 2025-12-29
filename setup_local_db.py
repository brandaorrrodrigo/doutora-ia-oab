"""
Setup Local Database for Testing
Creates database, user, and tables for local development
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError

# Database configuration for local PostgreSQL
POSTGRES_USER = "postgres"
DB_NAME = "juris_ia"
DB_USER = "juris_ia_user"
DB_PASSWORD = "changeme123"

def get_postgres_password():
    """Get PostgreSQL password from user"""
    import getpass
    print("\nEnter the password for PostgreSQL user 'postgres':")
    print("(This is the password you set when installing PostgreSQL)")
    return getpass.getpass("> ")

def create_database_and_user():
    """Create database and user if they don't exist"""

    # Try empty password first, then prompt if needed
    postgres_password = ""

    # Connect to default 'postgres' database to create new database
    try:
        engine = create_engine(f"postgresql://{POSTGRES_USER}:{postgres_password}@localhost:5432/postgres")
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError as e:
        if "password authentication failed" in str(e) or "no password supplied" in str(e):
            postgres_password = get_postgres_password()
            engine = create_engine(f"postgresql://{POSTGRES_USER}:{postgres_password}@localhost:5432/postgres")
        else:
            raise

    with engine.connect() as conn:
        # Set autocommit mode for database creation
        conn.execution_options(isolation_level="AUTOCOMMIT")

        # Check if database exists
        result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
        if not result.fetchone():
            print(f"Creating database '{DB_NAME}'...")
            conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
            print(f"[OK] Database '{DB_NAME}' created successfully")
        else:
            print(f"[INFO] Database '{DB_NAME}' already exists")

        # Check if user exists
        result = conn.execute(text(f"SELECT 1 FROM pg_roles WHERE rolname='{DB_USER}'"))
        if not result.fetchone():
            print(f"Creating user '{DB_USER}'...")
            conn.execute(text(f"CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}'"))
            print(f"[OK] User '{DB_USER}' created successfully")
        else:
            print(f"[INFO] User '{DB_USER}' already exists")

        # Grant privileges
        print("Granting privileges...")
        conn.execute(text(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER}"))
        print("[OK] Privileges granted")

def create_tables():
    """Create all tables using SQLAlchemy models"""
    print("\nCreating tables...")

    from database.connection import Base, engine

    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully")

        # List created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"\nCreated tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")

    except Exception as e:
        print(f"[ERROR] Failed to create tables: {e}")
        raise

def verify_setup():
    """Verify database setup"""
    print("\nVerifying setup...")

    from database.connection import get_db
    from database.models import Usuario, QuestaoOAB, PerfilJuridico

    try:
        db = next(get_db())

        # Count records
        usuarios_count = db.query(Usuario).count()
        questoes_count = db.query(QuestaoOAB).count()
        perfis_count = db.query(PerfilJuridico).count()

        print(f"[OK] Database connection successful")
        print(f"  - Usuarios: {usuarios_count}")
        print(f"  - Questoes: {questoes_count}")
        print(f"  - Perfis: {perfis_count}")

        db.close()
        return True

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print(" LOCAL DATABASE SETUP")
    print("="*60)

    try:
        # Step 1: Create database and user
        create_database_and_user()

        # Step 2: Create .env.local with localhost DATABASE_URL
        print("\nCreating .env.local file...")
        with open(".env.local", "w") as f:
            f.write(f"# Local development database\n")
            f.write(f"DATABASE_URL=postgresql://{DB_USER}:{DB_PASSWORD}@localhost:5432/{DB_NAME}\n")
        print("[OK] .env.local created")

        # Step 3: Create tables
        create_tables()

        # Step 4: Verify
        if verify_setup():
            print("\n" + "="*60)
            print(" SETUP COMPLETE!")
            print("="*60)
            print("\nYou can now run the integration tests:")
            print("  python test_integration.py")
        else:
            print("\n[WARNING] Setup completed but verification failed")
            sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
