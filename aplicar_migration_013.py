"""
Aplica migration 013 - Adicionar hash_conceito
"""
import sqlalchemy as sa
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import DatabaseManager

print("\n" + "="*70)
print("APLICANDO MIGRATION 013: HASH_CONCEITO")
print("="*70 + "\n")

# Criar engine
db_manager = DatabaseManager()
engine = db_manager.create_engine()

# Ler arquivo de migration
with open('database/migrations/013_adicionar_hash_conceito.sql', 'r', encoding='utf-8') as f:
    migration_sql = f.read()

# Aplicar migration
try:
    with engine.connect() as conn:
        # Executar migration em uma transação
        trans = conn.begin()
        try:
            conn.execute(sa.text(migration_sql))
            trans.commit()
            print("[OK] Migration 013 aplicada com sucesso!")
            print("\nNovos recursos adicionados:")
            print("  - Campo hash_conceito na tabela questoes_banco")
            print("  - Indice idx_questao_hash_conceito")
            print("  - Funcao estatisticas_variacoes_questoes()")
            print("  - View view_questoes_variacoes")
            print("  - Funcao buscar_variacoes_questao()")
        except Exception as e:
            trans.rollback()
            print(f"[ERRO] Ao aplicar migration: {e}")
            raise
except Exception as e:
    print(f"[ERRO] De conexao: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("MIGRATION CONCLUÍDA")
print("="*70 + "\n")
