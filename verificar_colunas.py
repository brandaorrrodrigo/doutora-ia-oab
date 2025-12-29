"""
Verifica colunas da tabela questoes_banco
"""
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import get_db_session
from database.models import QuestaoBanco
from sqlalchemy import inspect

print("\n" + "="*70)
print("VERIFICANDO COLUNAS DA TABELA questoes_banco")
print("="*70 + "\n")

with get_db_session() as session:
    inspector = inspect(session.bind)
    columns = inspector.get_columns('questoes_banco')

    print("Colunas existentes:")
    for i, col in enumerate(columns, 1):
        tipo = col['type']
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        print(f"  {i:2d}. {col['name']:30s} {str(tipo):20s} {nullable}")

    print(f"\nTotal: {len(columns)} colunas")

    # Verificar hash_conceito
    col_names = [col['name'] for col in columns]
    if 'hash_conceito' in col_names:
        print("\n[OK] Campo hash_conceito JA EXISTE!")
    else:
        print("\n[AVISO] Campo hash_conceito NAO existe - precisa migração")

print("\n" + "="*70 + "\n")
