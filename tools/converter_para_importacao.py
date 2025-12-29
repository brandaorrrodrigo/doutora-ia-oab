"""
Converte QUESTOES_OAB_CONSOLIDADAS.json para formato de importação
"""
import json
from pathlib import Path

# Le arquivo consolidado
with open('QUESTOES_OAB_CONSOLIDADAS.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

questoes_consolidadas = dados['questoes']

print(f"\n{'='*70}")
print("CONVERSAO PARA FORMATO DE IMPORTACAO")
print(f"{'='*70}\n")

print(f"Total de questoes consolidadas: {len(questoes_consolidadas)}\n")

# Filtra questoes que parecem ser de direito (exclui português/matematica)
questoes_direito = []
questoes_nao_direito = []

palavras_chave_direito = [
    'advogad', 'lei', 'juridic', 'codigo', 'tribunal', 'juiz', 'processo',
    'constituição', 'art.', 'direito', 'penal', 'civil', 'trabalhista',
    'administrativo', 'criminal', 'contrato', 'sentença', 'recurso',
    'licita', 'orgao publico', 'órgão público', 'CF', 'CC', 'CP', 'CPC',
    'CLT', 'STF', 'STJ', 'OAB', 'advocacia', 'cliente', 'poder publico'
]

for q in questoes_consolidadas:
    enunciado_lower = q.get('enunciado', '').lower()

    # Verifica se é questão de direito
    e_direito = any(palavra in enunciado_lower for palavra in palavras_chave_direito)

    if e_direito:
        questoes_direito.append(q)
    else:
        questoes_nao_direito.append(q)

print(f"Questoes de DIREITO identificadas: {len(questoes_direito)}")
print(f"Questoes de outras areas (portugues, etc): {len(questoes_nao_direito)}\n")

# Converte para formato de importação
questoes_importacao = []

for q in questoes_direito:
    # Determina disciplina (se possível)
    disciplina = q.get('disciplina', 'REVISAR')
    if disciplina == 'REVISAR':
        # Tenta inferir pela fonte
        codigo = q.get('codigo_questao', '')
        if 'trabalhista' in codigo.lower():
            disciplina = 'Direito do Trabalho'
        elif 'penal' in codigo.lower():
            disciplina = 'Direito Penal'
        elif 'civil' in codigo.lower():
            disciplina = 'Direito Civil'
        else:
            disciplina = 'Direito Geral'

    # Monta questão no formato de importação
    questao_importacao = {
        "disciplina": disciplina,
        "topico": q.get('topico', 'Questões Gerais OAB'),
        "enunciado": q.get('enunciado', ''),
        "alternativas": q.get('alternativas', {}),
        "gabarito": q.get('alternativa_correta', 'REVISAR'),
        "explicacao": "Questão extraída de material OAB - requer revisão e inclusão de explicação",
        "fundamentacao": "A revisar",
        "dificuldade": "medio",
        "ano_prova": None,
        "codigo_original": q.get('codigo_questao', ''),
        "status_extracao": q.get('status', '')
    }

    questoes_importacao.append(questao_importacao)

# Separa questões prontas vs que precisam revisão
questoes_prontas = [q for q in questoes_importacao if q['gabarito'] not in ['REVISAR', None, '']]
questoes_revisar = [q for q in questoes_importacao if q['gabarito'] in ['REVISAR', None, '']]

print(f"Questoes com GABARITO pronto: {len(questoes_prontas)}")
print(f"Questoes que PRECISAM REVISAO (sem gabarito): {len(questoes_revisar)}\n")

# Salva arquivo para importação (só as prontas)
output_file = "QUESTOES_PRONTAS_IMPORTACAO.json"

dados_saida = {
    "metadata": {
        "total_questoes": len(questoes_prontas),
        "questoes_com_gabarito": len(questoes_prontas),
        "questoes_sem_gabarito": len(questoes_revisar),
        "fonte": "Extração de PDFs OAB - Material Consolidado"
    },
    "questoes": questoes_prontas
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(dados_saida, f, indent=2, ensure_ascii=False)

print(f"{'='*70}")
print(f"ARQUIVO PRONTO: {output_file}")
print(f"{'='*70}")
print(f"\nQuestoes prontas para importacao: {len(questoes_prontas)}")

if len(questoes_revisar) > 0:
    # Salva questões que precisam revisão separadamente
    revisao_file = "QUESTOES_NECESSITAM_REVISAO.json"

    dados_revisao = {
        "metadata": {
            "total_questoes": len(questoes_revisar),
            "observacao": "Estas questões não têm gabarito definido e precisam revisão manual"
        },
        "questoes": questoes_revisar
    }

    with open(revisao_file, 'w', encoding='utf-8') as f:
        json.dump(dados_revisao, f, indent=2, ensure_ascii=False)

    print(f"\nQuestoes para revisao salvas em: {revisao_file}\n")

# Estatísticas por disciplina
print("\nDistribuição por disciplina (questões prontas):")
print("-"*70)

disciplinas_count = {}
for q in questoes_prontas:
    disc = q['disciplina']
    disciplinas_count[disc] = disciplinas_count.get(disc, 0) + 1

for disc, count in sorted(disciplinas_count.items(), key=lambda x: x[1], reverse=True):
    print(f"{count:4d} questões - {disc}")

print()
