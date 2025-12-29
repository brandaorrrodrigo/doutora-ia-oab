"""
Importação com commits parciais - solução definitiva
"""
from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".env.local", override=True)

import json
from database.connection import get_db_session
from database.models import QuestaoBanco, DificuldadeQuestao
import hashlib
import re

print("\n" + "="*70)
print("IMPORTACAO FINAL - APOSTILA (commits parciais)")
print("="*70 + "\n")

# Carregar questões
arquivo = "tools/QUESTOES_APOSTILA_IMPORTACAO.json"

with open(arquivo, 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total questoes: {len(questoes)}\n")

importadas_total = 0
duplicadas_total = 0
erros_total = 0

BATCH_SIZE = 50  # Commit a cada 50 questões

# Processar em lotes
for lote_inicio in range(0, len(questoes), BATCH_SIZE):
    lote_fim = min(lote_inicio + BATCH_SIZE, len(questoes))
    lote = questoes[lote_inicio:lote_fim]

    importadas_lote = 0
    duplicadas_lote = 0

    with get_db_session() as session:
        for i, q in enumerate(lote):
            try:
                idx_global = lote_inicio + i + 1

                # Gerar codigo_questao
                fonte_limpa = re.sub(r'[^a-zA-Z0-9]', '', arquivo.split('/')[-1].split('\\')[-1].replace('.json', ''))
                numero_orig = q.get('numero_original', idx_global)
                texto_unico = f"{fonte_limpa}{numero_orig}{q.get('enunciado')[:100]}"
                hash_unico = hashlib.md5(texto_unico.encode()).hexdigest()[:8]
                codigo = f"OAB_{fonte_limpa}_{numero_orig}_{hash_unico}"

                # Verificar duplicata
                existe = session.query(QuestaoBanco).filter_by(codigo_questao=codigo).first()
                if existe:
                    duplicadas_lote += 1
                    continue

                # Gerar hash_conceito
                topico_simples = re.sub(r'\s+', '', q.get('topico', 'geral')).lower()
                texto_conceito = f"{q['disciplina']}{topico_simples}{q['gabarito']}"
                hash_conceito = hashlib.md5(texto_conceito.encode()).hexdigest()

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
                importadas_lote += 1

            except Exception as e:
                erros_total += 1
                print(f"  [ERRO] Questao {idx_global}: {str(e)[:50]}")

        # Commit do lote
        try:
            session.commit()
            importadas_total += importadas_lote
            duplicadas_total += duplicadas_lote
            print(f"  Lote {lote_inicio+1}-{lote_fim}: {importadas_lote} importadas, {duplicadas_lote} duplicadas")
        except Exception as e:
            print(f"  [ERRO] Ao commitar lote {lote_inicio+1}-{lote_fim}: {str(e)[:80]}")
            session.rollback()

print(f"\n{'='*70}")
print("RELATORIO FINAL")
print(f"{'='*70}")
print(f"Total no arquivo:  {len(questoes)}")
print(f"Importadas:        {importadas_total}")
print(f"Duplicadas:        {duplicadas_total}")
print(f"Erros:             {erros_total}")
print(f"{'='*70}\n")
