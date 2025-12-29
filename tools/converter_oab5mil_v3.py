"""
Converte arquivo oab5mil.md para formato de importação (versão 3 - robusta)
"""
import json
import re

input_file = r"C:\Users\NFC\Downloads\oab5mil.md"
output_file = "QUESTOES_OAB5MIL_IMPORTACAO.json"

print("\n" + "="*70)
print("CONVERSAO OAB5MIL.MD PARA FORMATO DE IMPORTACAO")
print("="*70 + "\n")

# Lê arquivo
with open(input_file, 'r', encoding='utf-8') as f:
    conteudo = f.read()

print(f"Arquivo lido: {len(conteudo)} caracteres\n")

# Extrai todos os objetos JSON (tanto formato {numero:1...} quanto {"numero":1...})
# Procura por padrões de objeto JSON
questoes_raw = []

# Padrão 1: Busca todos os blocos {...} que contêm "numero" ou "pergunta"
objetos = re.finditer(r'\{[^}]+\}', conteudo, re.DOTALL)

for match in objetos:
    obj_str = match.group(0)

    # Remove asteriscos
    obj_str = obj_str.replace('**', '')

    # Remove quebras de linha extras
    obj_str = ' '.join(obj_str.split())

    try:
        # Tenta parsear
        obj = json.loads(obj_str)

        # Valida se tem campos essenciais
        if ('numero' in obj and
            ('questao' in obj or 'pergunta' in obj) and
            'alternativas' in obj and
            'gabarito' in obj):

            # Normaliza campo questao/pergunta
            if 'pergunta' in obj and 'questao' not in obj:
                obj['questao'] = obj['pergunta']

            questoes_raw.append(obj)

    except:
        pass

print(f"Questões extraídas: {len(questoes_raw)}\n")

# Converte para formato de importação
questoes_importacao = []

for q in questoes_raw:
    questao_convertida = {
        "disciplina": q.get('disciplina', 'Ética Profissional'),  # Maioria parece ser Ética
        "topico": "OAB - Banco 5000 Questões",
        "enunciado": q.get('questao', ''),
        "alternativas": q.get('alternativas', {}),
        "gabarito": q.get('gabarito', ''),
        "explicacao": "Questão do banco 5000 Questões OAB - aguardando explicação detalhada",
        "fundamentacao": "A revisar",
        "dificuldade": "medio",
        "ano_prova": None,
        "numero_original": q.get('numero')
    }

    # Valida
    alt = questao_convertida['alternativas']

    if (questao_convertida['enunciado'] and
        len(questao_convertida['enunciado']) > 10 and
        isinstance(alt, dict) and
        len(alt) >= 4 and
        questao_convertida['gabarito'] in ['A', 'B', 'C', 'D']):
        questoes_importacao.append(questao_convertida)
    else:
        print(f"[AVISO] Questão {q.get('numero')} inválida - pulando")

print(f"\nQuestões válidas convertidas: {len(questoes_importacao)}\n")

# Estatísticas por disciplina
from collections import Counter

disciplinas = Counter([q['disciplina'] for q in questoes_importacao])

print("Distribuição por disciplina:")
print("-"*70)
for disc, count in sorted(disciplinas.items(), key=lambda x: x[1], reverse=True):
    print(f"{count:3d} questões - {disc}")

# Distribuição de gabaritos
gabaritos = Counter([q['gabarito'] for q in questoes_importacao])

print("\nDistribuição de gabaritos:")
print("-"*70)
total_gab = sum(gabaritos.values())
for letra in ['A', 'B', 'C', 'D']:
    count = gabaritos.get(letra, 0)
    pct = (count / total_gab * 100) if total_gab > 0 else 0
    print(f"{letra}: {count:3d} ({pct:.1f}%)")

# Salva
dados_saida = {
    "metadata": {
        "fonte": "oab5mil.md - Banco de 5000 Questões OAB",
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
print(f"\nTotal: {len(questoes_importacao)} questões PRONTAS para importação!")
print("Todas com gabarito validado!")
print()
