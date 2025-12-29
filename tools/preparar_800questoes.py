"""
Prepara questões do PDF 800 para importação
Remove duplicatas e lixo, mantém apenas questões válidas
"""
import json
from collections import Counter

print("\n" + "="*70)
print("PREPARANDO QUESTOES DO PDF 800 PARA IMPORTACAO")
print("="*70 + "\n")

# Ler arquivo com gabarito
with open('questoes_extraidas/q_563839978-Simulados-OAB-de-800-Questoes_COM_GABARITO.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total de entradas brutas: {len(questoes)}")

# Filtrar apenas questões válidas
questoes_validas = []
numeros_vistos = set()

for q in questoes:
    # Validações
    if not q.get('enunciado'):
        continue

    if len(q.get('enunciado', '')) < 50:  # Enunciado muito curto
        continue

    if not q.get('alternativas'):
        continue

    if not isinstance(q.get('alternativas'), dict):
        continue

    if len(q.get('alternativas', {})) < 4:  # Precisa ter A, B, C, D
        continue

    if not q.get('alternativa_correta') or q['alternativa_correta'] not in ['A', 'B', 'C', 'D']:
        continue

    # Remover duplicatas por número
    num = q.get('numero')
    if num in numeros_vistos:
        continue

    if num:
        numeros_vistos.add(num)

    questoes_validas.append(q)

print(f"Questoes validas apos filtragem: {len(questoes_validas)}")

# Converter para formato de importação
questoes_importacao = []

for q in questoes_validas:
    questao_convertida = {
        "disciplina": "Direito Geral",  # Precisa identificar disciplina
        "topico": "Simulados OAB - 800 Questões",
        "enunciado": q.get('enunciado', ''),
        "alternativas": q.get('alternativas', {}),
        "gabarito": q.get('alternativa_correta', ''),
        "explicacao": "Questão do Simulado OAB 800 Questões - aguardando explicação",
        "fundamentacao": "A revisar",
        "dificuldade": "medio",
        "ano_prova": None,
        "numero_original": q.get('numero')
    }

    # Validação final
    if (questao_convertida['enunciado'] and
        len(questao_convertida['enunciado']) > 50 and
        isinstance(questao_convertida['alternativas'], dict) and
        len(questao_convertida['alternativas']) >= 4 and
        questao_convertida['gabarito'] in ['A', 'B', 'C', 'D']):
        questoes_importacao.append(questao_convertida)

print(f"Questoes prontas para importacao: {len(questoes_importacao)}")

# Estatísticas
print("\nDistribuicao de gabaritos:")
print("-"*70)
gabaritos = Counter([q['gabarito'] for q in questoes_importacao])
for letra in ['A', 'B', 'C', 'D']:
    count = gabaritos.get(letra, 0)
    pct = (count / len(questoes_importacao) * 100) if questoes_importacao else 0
    print(f"{letra}: {count:3d} ({pct:5.1f}%)")

# Salvar
output_file = "QUESTOES_800_IMPORTACAO.json"

dados_saida = {
    "metadata": {
        "fonte": "Simulados OAB - 800 Questões (PDF)",
        "total_questoes": len(questoes_importacao),
        "data_conversao": "2025-12-25",
        "todas_com_gabarito": True,
        "validadas": True
    },
    "questoes": questoes_importacao
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(dados_saida, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"ARQUIVO SALVO: {output_file}")
print(f"{'='*70}")
print(f"\nTotal: {len(questoes_importacao)} questoes PRONTAS para importacao!")
print("Todas com gabarito validado!")
print()
