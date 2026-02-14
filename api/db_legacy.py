"""Conexão e operações com o banco de dados PostgreSQL"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator
from config import get_settings

settings = get_settings()


@contextmanager
def get_db_connection() -> Generator:
    """Context manager para conexão com o banco de dados"""
    conn = None
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            cursor_factory=RealDictCursor  # Retorna resultados como dicionários
        )
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def get_db():
    """Dependency para FastAPI - retorna conexão do banco"""
    with get_db_connection() as conn:
        yield conn
