"""
Importação corrigida - sem rollback por questão
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
print("IMPORTACAO CORRIGIDA - APOSTILA")
print("="*70 + "\n")

# Carregar questões
arquivo = "tools/QUESTOES_APOSTILA_IMPORTACAO.json"

with open(arquivo, 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total questoes: {len(questoes)}\n")

importadas = 0
duplicadas = 0
erros = 0

with get_db_session() as session:
    for i, q in enumerate(questoes, 1):
        try:
            # Gerar codigo_questao
            fonte_limpa = re.sub(r'[^a-zA-Z0-9]', '', arquivo.split('/')[-1].split('\\')[-1].replace('.json', ''))
            numero_orig = q.get('numero_original', i)
            texto_unico = f"{fonte_limpa}{numero_orig}{q.get('enunciado')[:100]}"
            hash_unico = hashlib.md5(texto_unico.encode()).hexdigest()[:8]
            codigo = f"OAB_{fonte_limpa}_{numero_orig}_{hash_unico}"

            # Gerar hash_conceito
            topico_simples = re.sub(r'\s+', '', q.get('topico', 'geral')).lower()
            texto_conceito = f"{q['disciplina']}{topico_simples}{q['gabarito']}"
            hash_conceito = hashlib.md5(texto_conceito.encode()).hexdigest()

            # Verificar se já existe (ANTES de adicionar)
            existe = session.query(QuestaoBanco).filter_by(codigo_questao=codigo).first()
            if existe:
                duplicadas += 1
                if i % 100 == 0:
                    print(f"  {i}/{len(questoes)} - {duplicadas} duplicadas...")
                continue

            # Criar questão
            dif_map = {
                'facil': DificuldadeQuestao.FACIL,
                'medio': DificuldadeQuestao.MEDIO,
                'dificil': DificuldadeQuestao.DIFICIL
            }

            questao_obj = QuestaoBanco(
                codigo_questao=codigo,
                hash_conceito=hash_conceito,
                disciplina=q['disciplina'],
                topico=q.get('topico', 'Geral'),
                enunciado=q['enunciado'],
                alternativas=q['alternativas'],
                alternativa_correta=q['gabarito'],
                dificuldade=dif_map.get(q.get('dificuldade', 'medio'), DificuldadeQuestao.MEDIO),
                ano_prova=q.get('ano_prova'),
                numero_exame=q.get('exame', 'OAB'),
                explicacao_detalhada=q.get('explicacao', ''),
                fundamentacao_legal={'texto': q.get('fundamentacao', '')},
                tags=q.get('tags', []),
                ativa=True
            )

            session.add(questao_obj)
            importadas += 1

            if i % 100 == 0:
                print(f"  {i}/{len(questoes)} - {importadas} importadas...")

        except Exception as e:
            erros += 1
            print(f"  [ERRO] Questao {i}: {str(e)[:60]}")

    # Commit UMA VEZ no final
    print(f"\nCommitando {importadas} questoes...")
    session.commit()
    print(f"[OK] Commit concluido!")

print(f"\n{'='*70}")
print("RELATORIO FINAL")
print(f"{'='*70}")
print(f"Total no arquivo:  {len(questoes)}")
print(f"Importadas:        {importadas}")
print(f"Duplicadas:        {duplicadas}")
print(f"Erros:             {erros}")
print(f"{'='*70}\n")
