"""
Script de Migracao: questoes (legado) -> questoes_banco (ORM)
=============================================================

Migra as 37.462 questoes da tabela 'questoes' (IDs inteiros, psycopg2)
para a tabela 'questoes_banco' (UUIDs, SQLAlchemy ORM).

Mapeamento:
  questoes.enunciado        -> questoes_banco.enunciado
  questoes.alternativa_a/b/c/d -> questoes_banco.alternativas (JSONB)
  questoes.gabarito         -> questoes_banco.alternativa_correta
  questoes.disciplina       -> questoes_banco.disciplina
  questoes.fonte            -> questoes_banco.numero_exame / tags
  questoes.numero_original  -> parte do codigo_questao
  questoes.id               -> codigo_questao = "LEG_{id:06d}"

Execucao:
  cd D:\\JURIS_IA_CORE_V1
  python scripts/migrate_questoes.py
"""
import sys
import os

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.exc import IntegrityError
from database.connection import DatabaseManager
from database.models import QuestaoBanco, DificuldadeQuestao

# Configuracao
BATCH_SIZE = 500


def get_legacy_connection():
    """Obtem conexao psycopg2 para a tabela legada 'questoes'"""
    from database.connection import DatabaseConfig
    config = DatabaseConfig()
    return psycopg2.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        cursor_factory=RealDictCursor
    )


def count_legacy_questions(conn):
    """Conta total de questoes na tabela legada"""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total FROM questoes")
    result = cursor.fetchone()
    cursor.close()
    return result['total']


def fetch_legacy_batch(conn, offset, limit):
    """Busca um batch de questoes da tabela legada"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, enunciado, alternativa_a, alternativa_b,
               alternativa_c, alternativa_d, gabarito,
               disciplina, fonte, numero_original
        FROM questoes
        ORDER BY id
        LIMIT %s OFFSET %s
    """, (limit, offset))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def map_disciplina_to_topico(disciplina):
    """Mapeia disciplina para um topico generico"""
    topicos = {
        "Direito Penal": "Parte Geral",
        "Direito Civil": "Parte Geral",
        "Direito Constitucional": "Principios Fundamentais",
        "Direito Processual Civil": "Processo de Conhecimento",
        "Direito Processual Penal": "Procedimentos",
        "Direito Tributario": "Principios",
        "Direito Administrativo": "Atos Administrativos",
        "Direito do Trabalho": "Contrato de Trabalho",
        "Direito Empresarial": "Sociedades",
        "Etica Profissional": "Deveres do Advogado",
        "Direitos Humanos": "Sistema Interamericano",
        "Direito Ambiental": "Responsabilidade Ambiental",
        "Direito do Consumidor": "Relacao de Consumo",
    }
    # Tentar match parcial
    for key, value in topicos.items():
        if key.lower() in disciplina.lower():
            return value
    return "Geral"


def migrate():
    """Executa a migracao em batches"""
    print("=" * 70)
    print("MIGRACAO: questoes (legado) -> questoes_banco (ORM)")
    print("=" * 70)

    # Conexao legada (psycopg2)
    legacy_conn = get_legacy_connection()
    total = count_legacy_questions(legacy_conn)
    print(f"\nTotal de questoes na tabela 'questoes': {total}")

    if total == 0:
        print("Nenhuma questao para migrar. Abortando.")
        legacy_conn.close()
        return

    # Conexao ORM (SQLAlchemy)
    db_manager = DatabaseManager()
    SessionFactory = db_manager.get_session_factory()

    migradas = 0
    duplicadas = 0
    erros = 0
    offset = 0

    print(f"Processando em batches de {BATCH_SIZE}...\n")

    while offset < total:
        batch = fetch_legacy_batch(legacy_conn, offset, BATCH_SIZE)

        if not batch:
            break

        db = SessionFactory()

        try:
            for row in batch:
                codigo = f"LEG_{row['id']:06d}"

                # Verificar se ja foi migrada
                existing = db.query(QuestaoBanco).filter(
                    QuestaoBanco.codigo_questao == codigo
                ).first()
                if existing:
                    duplicadas += 1
                    continue

                # Montar alternativas JSONB
                alternativas = {}
                if row.get('alternativa_a'):
                    alternativas['A'] = row['alternativa_a']
                if row.get('alternativa_b'):
                    alternativas['B'] = row['alternativa_b']
                if row.get('alternativa_c'):
                    alternativas['C'] = row['alternativa_c']
                if row.get('alternativa_d'):
                    alternativas['D'] = row['alternativa_d']

                # Mapear gabarito
                gabarito = row.get('gabarito', 'A')
                if gabarito and len(gabarito) == 1 and gabarito.upper() in 'ABCD':
                    alternativa_correta = gabarito.upper()
                else:
                    alternativa_correta = 'A'  # Fallback

                disciplina = row.get('disciplina', 'Multidisciplinar')
                topico = map_disciplina_to_topico(disciplina)
                fonte = row.get('fonte', '')

                # Criar registro no questoes_banco
                questao = QuestaoBanco(
                    codigo_questao=codigo,
                    disciplina=disciplina,
                    topico=topico,
                    enunciado=row['enunciado'],
                    alternativas=alternativas,
                    alternativa_correta=alternativa_correta,
                    dificuldade=DificuldadeQuestao.MEDIO,
                    numero_exame=fonte[:20] if fonte else None,
                    explicacao_detalhada=None,
                    tags=[disciplina.lower(), "legado"],
                    ativa=True,
                    total_respostas=0
                )

                db.add(questao)
                migradas += 1

            db.commit()

        except Exception as e:
            db.rollback()
            erros += len(batch)
            print(f"  ERRO no batch offset={offset}: {str(e)[:100]}")
        finally:
            db.close()

        offset += BATCH_SIZE
        pct = min(100, round((offset / total) * 100, 1))
        print(f"  Progresso: {min(offset, total)}/{total} ({pct}%) | Migradas: {migradas} | Duplicadas: {duplicadas} | Erros: {erros}")

    legacy_conn.close()

    print("\n" + "=" * 70)
    print("MIGRACAO CONCLUIDA")
    print("=" * 70)
    print(f"  Total na tabela legada:  {total}")
    print(f"  Migradas com sucesso:    {migradas}")
    print(f"  Ja existentes (skip):    {duplicadas}")
    print(f"  Erros:                   {erros}")
    print("=" * 70)


if __name__ == "__main__":
    migrate()
