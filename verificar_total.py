"""
Verifica total de questões no banco
"""
from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import get_db_session
from database.models import QuestaoBanco
from sqlalchemy import func

with get_db_session() as session:
    total = session.query(func.count(QuestaoBanco.id)).scalar()
    print(f"\nTotal de questoes no banco: {total}\n")
