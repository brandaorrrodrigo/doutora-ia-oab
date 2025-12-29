"""
Limpa todas as questões do banco para reimportação
"""
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import get_db_session
from database.models import QuestaoBanco
from sqlalchemy import func

print("\n" + "="*70)
print("LIMPANDO BANCO DE DADOS")
print("="*70 + "\n")

with get_db_session() as session:
    # Contar questões atuais
    total_antes = session.query(func.count(QuestaoBanco.id)).scalar()
    print(f"Questoes no banco atualmente: {total_antes}")

    if total_antes > 0:
        print(f"\nRemovendo {total_antes} questoes...")
        session.query(QuestaoBanco).delete()
        session.commit()
        print("[OK] Banco limpo!")
    else:
        print("[INFO] Banco ja esta vazio.")

    # Verificar
    total_depois = session.query(func.count(QuestaoBanco.id)).scalar()
    print(f"\nQuestoes no banco apos limpeza: {total_depois}")

print("\n" + "="*70)
print("BANCO PRONTO PARA REIMPORTACAO")
print("="*70 + "\n")
