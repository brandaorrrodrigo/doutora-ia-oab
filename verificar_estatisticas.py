"""
Verifica estatísticas das questões importadas
"""
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import DatabaseManager
import sqlalchemy as sa

print("\n" + "="*70)
print("ESTATISTICAS DAS QUESTOES IMPORTADAS")
print("="*70 + "\n")

# Criar engine
db_manager = DatabaseManager()
engine = db_manager.create_engine()

with engine.connect() as conn:
    # Total de questões
    print("1. TOTAIS")
    print("-"*70)
    result = conn.execute(sa.text("SELECT COUNT(*) FROM questoes_banco")).fetchone()
    total_questoes = result[0]
    print(f"Total de questoes: {total_questoes}")

    # Questões com hash_conceito
    result = conn.execute(sa.text("SELECT COUNT(*) FROM questoes_banco WHERE hash_conceito IS NOT NULL")).fetchone()
    com_hash = result[0]
    print(f"Questoes com hash_conceito: {com_hash}")

    # Estatísticas de variações
    print("\n2. ESTATISTICAS DE VARIACOES (usando funcao do banco)")
    print("-"*70)
    try:
        result = conn.execute(sa.text("SELECT * FROM estatisticas_variacoes_questoes()")).fetchone()
        print(f"Total de questoes: {result[0]}")
        print(f"Total de conceitos unicos: {result[1]}")
        print(f"Conceitos com variacoes: {result[2]}")
        print(f"Max variacoes por conceito: {result[3]}")
        print(f"Media variacoes por conceito: {result[4]}")
    except Exception as e:
        print(f"[AVISO] Erro ao executar funcao: {e}")

    # Top 10 conceitos com mais variações
    print("\n3. TOP 10 CONCEITOS COM MAIS VARIACOES")
    print("-"*70)
    query = sa.text("""
        SELECT
            hash_conceito,
            COUNT(*) as variacoes,
            MIN(disciplina) as disciplina,
            MIN(topico) as topico
        FROM questoes_banco
        WHERE hash_conceito IS NOT NULL
        GROUP BY hash_conceito
        ORDER BY COUNT(*) DESC
        LIMIT 10
    """)
    results = conn.execute(query).fetchall()
    for i, row in enumerate(results, 1):
        hash_conceito, variacoes, disciplina, topico = row
        print(f"{i:2d}. {variacoes} variacoes - {disciplina[:30]} - {topico[:40]}")

    # Distribuição de gabaritos
    print("\n4. DISTRIBUICAO DE GABARITOS")
    print("-"*70)
    query = sa.text("""
        SELECT alternativa_correta, COUNT(*) as total
        FROM questoes_banco
        GROUP BY alternativa_correta
        ORDER BY alternativa_correta
    """)
    results = conn.execute(query).fetchall()
    for letra, total in results:
        pct = (total / total_questoes * 100) if total_questoes > 0 else 0
        print(f"{letra}: {total:4d} ({pct:5.1f}%)")

    # Distribuição por disciplina
    print("\n5. DISTRIBUICAO POR DISCIPLINA")
    print("-"*70)
    query = sa.text("""
        SELECT disciplina, COUNT(*) as total
        FROM questoes_banco
        GROUP BY disciplina
        ORDER BY COUNT(*) DESC
    """)
    results = conn.execute(query).fetchall()
    for disciplina, total in results:
        pct = (total / total_questoes * 100) if total_questoes > 0 else 0
        print(f"{disciplina[:50]:50s}: {total:4d} ({pct:5.1f}%)")

print("\n" + "="*70)
print("RELATORIO CONCLUIDO")
print("="*70 + "\n")
