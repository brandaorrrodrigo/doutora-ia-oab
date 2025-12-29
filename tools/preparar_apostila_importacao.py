"""
Prepara questões da Apostila para importação
"""
import json
from collections import Counter

print("\n" + "="*70)
print("PREPARANDO APOSTILA PARA IMPORTACAO")
print("="*70 + "\n")

# Carregar questões com gabarito
with open('questoes_extraidas/q_14846014-Apostila_COM_GABARITO.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total de questoes: {len(questoes)}")

# Filtrar apenas com gabarito válido
questoes_validas = [q for q in questoes
                    if q.get('alternativa_correta') in ['A', 'B', 'C', 'D']
                    and q.get('enunciado')
                    and len(q.get('enunciado', '')) > 30
                    and isinstance(q.get('alternativas'), dict)
                    and len(q.get('alternativas', {})) >= 4]

print(f"Questoes com gabarito valido: {len(questoes_validas)}\n")

# Converter para formato de importação
questoes_importacao = []

for q in questoes_validas:
    questao_convertida = {
        "disciplina": "Direito - OAB",
        "topico": "Apostila Questões OAB com Gabarito (2007)",
        "enunciado": q.get('enunciado', ''),
        "alternativas": q.get('alternativas', {}),
        "gabarito": q.get('alternativa_correta', ''),
        "explicacao": "Questão da Apostila OAB 2007 - aguardando explicação",
        "fundamentacao": "A revisar",
        "dificuldade": "medio",
        "ano_prova": 2007,
        "numero_original": q.get('numero')
    }

    questoes_importacao.append(questao_convertida)

print(f"Questoes prontas para importacao: {len(questoes_importacao)}\n")

# Estatísticas
print("Distribuicao de gabaritos:")
print("-"*70)
gabaritos = Counter([q['gabarito'] for q in questoes_importacao])
total = len(questoes_importacao)
for letra in ['A', 'B', 'C', 'D']:
    count = gabaritos.get(letra, 0)
    pct = (count / total * 100) if total > 0 else 0
    print(f"{letra}: {count:3d} ({pct:5.1f}%)")

# Salvar
output_file = "QUESTOES_APOSTILA_IMPORTACAO.json"

dados_saida = {
    "metadata": {
        "fonte": "Apostila Questões OAB com Gabarito (2007)",
        "total_questoes": len(questoes_importacao),
        "data_conversao": "2025-12-25",
        "todas_com_gabarito": True,
        "validadas": True,
        "ano_prova": 2007
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
