"""
Debug da importação da Apostila
"""
from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".env.local", override=True)

import json
from database.connection import get_db_session
from database.models import QuestaoBanco, DificuldadeQuestao
import hashlib
import re
from sqlalchemy.exc import IntegrityError

print("\n" + "="*70)
print("DEBUG IMPORTACAO APOSTILA")
print("="*70 + "\n")

# Carregar questões
with open('tools/QUESTOES_APOSTILA_IMPORTACAO.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total questoes no arquivo: {len(questoes)}\n")

# Tentar importar questão 1
q1 = questoes[0]

print("Testando questao 1:")
print(f"  Numero: {q1.get('numero_original')}")
print(f"  Disciplina: {q1.get('disciplina')}")
print(f"  Topico: {q1.get('topico')}")
print(f"  Gabarito: {q1.get('gabarito')}")
print(f"  Enunciado: {q1.get('enunciado')[:80]}...")

# Gerar codigo_questao como o importador faz
arquivo_fonte = "tools/QUESTOES_APOSTILA_IMPORTACAO.json"
fonte_limpa = re.sub(r'[^a-zA-Z0-9]', '', arquivo_fonte.split('/')[-1].split('\\')[-1].replace('.json', ''))
numero_orig = q1.get('numero_original', 1)
texto_unico = f"{fonte_limpa}{numero_orig}{q1.get('enunciado')[:100]}"
hash_unico = hashlib.md5(texto_unico.encode()).hexdigest()[:8]
codigo = f"OAB_{fonte_limpa}_{numero_orig}_{hash_unico}"

print(f"\nCodigo gerado: {codigo}")

# Verificar se já existe
with get_db_session() as session:
    existe = session.query(QuestaoBanco).filter_by(codigo_questao=codigo).first()
    if existe:
        print(f"[DUPLICADA] Questao ja existe no banco!")
        print(f"  ID: {existe.id}")
        print(f"  Codigo: {existe.codigo_questao}")
    else:
        print(f"[OK] Questao NAO existe no banco")

    # Contar quantas questões da Apostila existem
    total_apostila = session.query(QuestaoBanco).filter(
        QuestaoBanco.topico.like('%Apostila%')
    ).count()
    print(f"\nTotal de questoes da Apostila no banco: {total_apostila}")

print("\n" + "="*70)
