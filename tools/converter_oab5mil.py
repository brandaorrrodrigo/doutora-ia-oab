"""
Converte arquivo oab5mil.md (270 questões com gabarito) para formato de importação
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

# Remove quebras de linha extras e formata como JSON válido
# O arquivo parece ter formatação Markdown, vou extrair os objetos JSON

# Primeiro, tenta fazer parse direto como JSON
try:
    # Remove caracteres extras antes do array
    conteudo_limpo = conteudo.strip()

    # Se começar com \[, remove
    if conteudo_limpo.startswith('\\['):
        conteudo_limpo = conteudo_limpo[2:]

    # Se terminar com \], remove
    if conteudo_limpo.endswith('\\]'):
        conteudo_limpo = conteudo_limpo[:-2]

    # Adiciona colchetes de array
    if not conteudo_limpo.startswith('['):
        conteudo_limpo = '[' + conteudo_limpo

    if not conteudo_limpo.endswith(']'):
        conteudo_limpo = conteudo_limpo + ']'

    # Tenta parsear
    questoes_raw = json.loads(conteudo_limpo)

    print(f"Questões parseadas: {len(questoes_raw)}\n")

    # Converte para formato de importação
    questoes_importacao = []

    for q in questoes_raw:
        questao_convertida = {
            "disciplina": q.get('disciplina', 'Direito Geral'),
            "topico": "OAB - 5000 Questões",
            "enunciado": q.get('questao', ''),
            "alternativas": q.get('alternativas', {}),
            "gabarito": q.get('gabarito', ''),
            "explicacao": "Questão do banco 5000 Questões OAB - revisar explicação",
            "fundamentacao": "A revisar",
            "dificuldade": "medio",
            "ano_prova": None,
            "numero_original": q.get('numero')
        }

        # Valida
        if (questao_convertida['enunciado'] and
            len(questao_convertida['alternativas']) == 4 and
            questao_convertida['gabarito'] in ['A', 'B', 'C', 'D']):
            questoes_importacao.append(questao_convertida)

    print(f"Questões válidas convertidas: {len(questoes_importacao)}\n")

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
    for letra in ['A', 'B', 'C', 'D']:
        count = gabaritos.get(letra, 0)
        pct = (count / len(questoes_importacao) * 100) if questoes_importacao else 0
        print(f"{letra}: {count:3d} ({pct:.1f}%)")

    # Salva
    dados_saida = {
        "metadata": {
            "fonte": "oab5mil.md - Banco de 5000 Questões OAB",
            "total_questoes": len(questoes_importacao),
            "data_conversao": "2025-12-25"
        },
        "questoes": questoes_importacao
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dados_saida, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"ARQUIVO SALVO: {output_file}")
    print(f"{'='*70}")
    print(f"\nTotal: {len(questoes_importacao)} questões prontas para importação!")
    print("Todas com gabarito e validadas!")
    print()

except Exception as e:
    print(f"ERRO ao parsear JSON: {e}")
    import traceback
    traceback.print_exc()
