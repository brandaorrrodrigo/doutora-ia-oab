"""
Verifica quais arquivos extraídos têm gabaritos
"""
import json
from pathlib import Path

pastas = ['questoes_reprocessadas', 'questoes_extraidas']
pastas += ['.']  # Arquivos gigantes

total_com_gab = 0
total_sem_gab = 0

print("\n" + "="*70)
print("VERIFICACAO DE GABARITOS NOS ARQUIVOS EXTRAIDOS")
print("="*70 + "\n")

for pasta_nome in pastas:
    pasta = Path(pasta_nome)
    if not pasta.exists():
        continue

    for arquivo in pasta.glob("*.json"):
        if 'CONSOLIDADAS' in arquivo.name or 'IMPORTACAO' in arquivo.name or 'REVISAO' in arquivo.name:
            continue

        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            questoes = dados.get('questoes', [])

            com_gab = [q for q in questoes if q.get('alternativa_correta') not in ['REVISAR', None, '']]
            sem_gab = [q for q in questoes if q.get('alternativa_correta') in ['REVISAR', None, '']]

            if com_gab:
                print(f"[OK] {arquivo.name}: {len(com_gab)} questões COM gabarito")
                total_com_gab += len(com_gab)

            total_sem_gab += len(sem_gab)

        except Exception as e:
            pass

print(f"\n{'='*70}")
print("TOTAIS")
print(f"{'='*70}")
print(f"\nQuestões COM gabarito: {total_com_gab}")
print(f"Questões SEM gabarito: {total_sem_gab}\n")

if total_com_gab == 0:
    print("PROBLEMA IDENTIFICADO:")
    print("Nenhuma questão foi extraída com gabarito!")
    print("\nPossíveis causas:")
    print("1. PDFs têm gabarito em seção separada (fim do documento)")
    print("2. Padrões de extração não capturaram a resposta correta")
    print("3. PDFs são apenas questões, sem gabaritos incluídos")
    print("\nSOLUCOES:")
    print("A) Procurar PDFs oficiais FGV com questões + gabaritos juntos")
    print("B) Extrair gabaritos manualmente dos PDFs")
    print("C) Usar serviços de questões online com APIs")
    print()
