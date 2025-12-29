"""
Cria todas as tabelas do banco de dados
"""
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import DatabaseManager
from database.models import Base

print("\n" + "="*70)
print("CRIANDO TABELAS DO BANCO DE DADOS")
print("="*70 + "\n")

# Criar engine
db_manager = DatabaseManager()
engine = db_manager.create_engine()

print("Conectado ao banco de dados!")
print(f"URL: {db_manager.config.get_database_url()[:50]}...\n")

# Criar todas as tabelas
print("Criando tabelas...")
Base.metadata.create_all(engine)

print("\nTabelas criadas com sucesso!")
print("\nTabelas no banco:")

# Listar tabelas criadas
from sqlalchemy import inspect
inspector = inspect(engine)
tabelas = inspector.get_table_names()

for i, tabela in enumerate(sorted(tabelas), 1):
    print(f"  {i:2d}. {tabela}")

print("\n" + "="*70)
print(f"TOTAL: {len(tabelas)} tabelas criadas")
print("="*70 + "\n")
