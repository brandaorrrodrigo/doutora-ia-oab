"""
Initialize Database - Create all tables
Run this after creating the database and user
"""

import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

print("="*60)
print(" DATABASE INITIALIZATION")
print("="*60)

try:
    print("\n[1/3] Loading database connection...")
    from database.connection import DatabaseManager
    from database.models import Base

    db_manager = DatabaseManager()

    print("[2/3] Creating database engine...")
    engine = db_manager.create_engine()

    print("[3/3] Creating all tables...")
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
    print("\nMake sure you have:")
    print("  1. Created the database: juris_ia")
    print("  2. Created the user: juris_ia_user (password: changeme123)")
    print("  3. Granted privileges")
    print("\nSee .env.local file for manual SQL commands")
    import traceback
    traceback.print_exc()
    sys.exit(1)
