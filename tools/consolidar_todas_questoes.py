"""
Consolida todas as questoes extraidas em um unico arquivo master
"""
import json
from pathlib import Path
from datetime import datetime

base_dir = Path(".")

# Pastas com questoes
pastas = [
    "questoes_extraidas",
    "questoes_reprocessadas"
]

# Arquivos individuais gigantes
arquivos_gigantes = list(base_dir.glob("gigante_*.json"))

print(f"\n{'='*70}")
print("CONSOLIDANDO TODAS AS QUESTOES")
print(f"{'='*70}\n")

todas_questoes = []
questoes_por_fonte = {}
codigos_vistos = set()
duplicatas = 0

# Processa pastas
for pasta_nome in pastas:
    pasta = Path(pasta_nome)
    if not pasta.exists():
        continue

    print(f"\nProcessando pasta: {pasta_nome}")

    for arquivo_json in pasta.glob("*.json"):
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                questoes = dados.get('questoes', [])

                fonte = arquivo_json.stem
                questoes_por_fonte[fonte] = len(questoes)

                for q in questoes:
                    codigo = q.get('codigo_questao')

                    # Evita duplicatas
                    if codigo and codigo in codigos_vistos:
                        duplicatas += 1
                        continue

                    if codigo:
                        codigos_vistos.add(codigo)

                    todas_questoes.append(q)

                print(f"  + {len(questoes):4d} questoes de {arquivo_json.name}")

        except Exception as e:
            print(f"  ERRO em {arquivo_json.name}: {e}")

# Processa arquivos gigantes
print(f"\nProcessando PDFs gigantes:")
for arquivo_json in arquivos_gigantes:
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            questoes = dados.get('questoes', [])

            fonte = arquivo_json.stem
            questoes_por_fonte[fonte] = len(questoes)

            for q in questoes:
                codigo = q.get('codigo_questao')

                if codigo and codigo in codigos_vistos:
                    duplicatas += 1
                    continue

                if codigo:
                    codigos_vistos.add(codigo)

                todas_questoes.append(q)

            print(f"  + {len(questoes):4d} questoes de {arquivo_json.name}")

    except Exception as e:
        print(f"  ERRO em {arquivo_json.name}: {e}")

# Remove questoes sem campos essenciais
questoes_validas = []
questoes_invalidas = 0

for q in todas_questoes:
    if (q.get('enunciado') and
        len(q.get('enunciado', '')) > 20 and
        q.get('alternativas') and
        len(q.get('alternativas', {})) >= 4):
        questoes_validas.append(q)
    else:
        questoes_invalidas += 1

print(f"\n{'='*70}")
print("ESTATISTICAS")
print(f"{'='*70}")
print(f"\nQuestoes brutas extraidas:  {len(todas_questoes)}")
print(f"Duplicatas removidas:       {duplicatas}")
print(f"Questoes invalidas:         {questoes_invalidas}")
print(f"Questoes VALIDAS:           {len(questoes_validas)}")

# Salva arquivo consolidado
output_file = "QUESTOES_OAB_CONSOLIDADAS.json"

dados_consolidados = {
    "metadata": {
        "data_consolidacao": datetime.now().isoformat(),
        "total_questoes": len(questoes_validas),
        "fontes": len(questoes_por_fonte),
        "duplicatas_removidas": duplicatas,
        "invalidas_removidas": questoes_invalidas
    },
    "questoes_por_fonte": questoes_por_fonte,
    "questoes": questoes_validas
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(dados_consolidados, f, indent=2, ensure_ascii=False)

print(f"\n{'='*70}")
print(f"ARQUIVO CONSOLIDADO SALVO: {output_file}")
print(f"{'='*70}")
print(f"\nTotal: {len(questoes_validas)} questoes prontas para importacao!\n")

# TOP 10 fontes
print("\nTOP 10 Fontes com mais questoes:")
print("-"*70)
top_fontes = sorted(questoes_por_fonte.items(), key=lambda x: x[1], reverse=True)[:10]
for i, (fonte, qtd) in enumerate(top_fontes, 1):
    print(f"{i:2d}. {qtd:4d} questoes - {fonte[:55]}")
