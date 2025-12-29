"""
Recreate all tables - Drop and create fresh
"""

import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

print("="*60)
print(" RECREATING DATABASE TABLES")
print("="*60)

try:
    print("\n[1/3] Loading database connection...")
    from database.connection import DatabaseManager
    from database.models import Base

    db_manager = DatabaseManager()

    print("[2/3] Dropping all existing tables...")
    engine = db_manager.create_engine()
    Base.metadata.drop_all(bind=engine)
    print("[OK] All tables dropped")

    print("[3/3] Creating all tables with current schema...")
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables created")

    # List created tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\nRecreated tables ({len(tables)}):")
    for table in sorted(tables):
        print(f"  - {table}")

    print("\n" + "="*60)
    print(" SUCCESS! Ready for testing")
    print("="*60)
    print("\nRun: python test_integration.py")

except Exception as e:
    print(f"\n[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
