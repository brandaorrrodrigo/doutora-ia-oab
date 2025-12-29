"""
Verifica questões extraídas dos PDFs
"""
import json
from collections import Counter

print("\n" + "="*70)
print("QUESTOES EXTRAIDAS DOS PDFs")
print("="*70 + "\n")

# Ler arquivo consolidado
with open('tools/QUESTOES_OAB_CONSOLIDADAS.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data.get('questoes', [])
metadata = data.get('metadata', {})

print("1. TOTAIS")
print("-"*70)
print(f"Total de questoes: {len(questoes)}")

# Contar com/sem gabarito
com_gabarito = sum(1 for q in questoes if q.get('gabarito') and q['gabarito'] != 'REVISAR')
sem_gabarito = sum(1 for q in questoes if not q.get('gabarito') or q['gabarito'] == 'REVISAR')

print(f"Com gabarito: {com_gabarito}")
print(f"Sem gabarito: {sem_gabarito}")

# Metadata
print("\n2. METADATA")
print("-"*70)
for key, value in metadata.items():
    print(f"{key}: {value}")

# Distribuição por fonte
print("\n3. DISTRIBUICAO POR FONTE")
print("-"*70)
fontes = Counter([q.get('fonte', 'Desconhecido') for q in questoes])
for fonte, total in sorted(fontes.items(), key=lambda x: x[1], reverse=True):
    print(f"{total:4d} - {fonte[:60]}")

# Distribuição por disciplina
print("\n4. DISTRIBUICAO POR DISCIPLINA")
print("-"*70)
disciplinas = Counter([q.get('disciplina', 'Desconhecido') for q in questoes])
for disc, total in sorted(disciplinas.items(), key=lambda x: x[1], reverse=True):
    print(f"{total:4d} - {disc[:60]}")

# Amostra de questão sem gabarito
print("\n5. AMOSTRA DE QUESTAO SEM GABARITO")
print("-"*70)
for q in questoes[:3]:
    if not q.get('gabarito') or q['gabarito'] == 'REVISAR':
        print(f"\nFonte: {q.get('fonte', 'N/A')[:50]}")
        print(f"Disciplina: {q.get('disciplina', 'N/A')}")
        print(f"Enunciado: {q.get('enunciado', 'N/A')[:100]}...")
        print(f"Gabarito: {q.get('gabarito', 'VAZIO')}")
        break

print("\n" + "="*70)
print("ANALISE CONCLUIDA")
print("="*70 + "\n")
