"""
Initialize Database - Create all tables (Safe version com encoding fixes)
"""

import sys
import os
import locale

# Força locale UTF-8
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass

# Força encoding UTF-8 no Python
os.environ['PYTHONIOENCODING'] = 'utf-8'

from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

print("="*60)
print(" DATABASE INITIALIZATION (SAFE MODE)")
print("="*60)

try:
    print("\n[1/4] Configurando encoding...")
    # Força encoding na conexão psycopg2
    import psycopg2
    import psycopg2.extensions
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
    psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
    print("[OK] Encoding configurado")

    print("[2/4] Loading database connection...")
    from database.connection import DatabaseManager
    from database.models import Base

    db_manager = DatabaseManager()

    print("[3/4] Creating database engine...")
    engine = db_manager.create_engine()

    print("[4/4] Creating all tables...")
    Base.metadata.create_all(bind=engine)

    print("\n[OK] Database initialized successfully!")

    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\nCreated tables ({len(tables)}):")
    for table in sorted(tables):
        print(f"  - {table}")

    print("\n" + "="*60)
    print(" READY FOR TESTING")
    print("="*60)
    print("\nYou can now run: python test_integration.py")

except Exception as e:
    print(f"\n[ERROR] Failed to initialize database: {e}")
    print("\nTrying alternative approach...")

    # Tentar conexão direta sem pool
    try:
        import psycopg2
        from urllib.parse import urlparse

        db_url = os.getenv("DATABASE_URL")
        parsed = urlparse(db_url)

        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path[1:],
            user=parsed.username,
            password=parsed.password,
            client_encoding='UTF8'
        )

        print("[OK] Direct connection successful!")
        print("\nTrying to create tables with direct connection...")

        # Importar modelos e criar engine novamente
        from sqlalchemy import create_engine
        engine = create_engine(
            db_url,
            connect_args={'client_encoding': 'utf8'},
            isolation_level="AUTOCOMMIT"
        )

        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created!")

    except Exception as e2:
        print(f"[ERROR] Alternative approach also failed: {e2}")
        print("\nPlease use Railway database instead:")
        print("1. Get DATABASE_URL from Railway dashboard")
        print("2. Update .env.local with Railway URL")
        print("3. Run this script again")
        import traceback
        traceback.print_exc()
        sys.exit(1)
