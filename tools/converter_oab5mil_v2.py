"""
Converte arquivo oab5mil.md para formato de importação (versão robusta)
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

# Remove todos os \n extras e junta em uma linha
conteudo_limpo = conteudo.replace('\n\n', '\n')
conteudo_limpo = conteudo_limpo.replace('\\[', '[')
conteudo_limpo = conteudo_limpo.replace('\\]', ']')

# Remove quebras de linha dentro de strings
linhas = conteudo_limpo.split('\n')
conteudo_json = ' '.join([linha.strip() for linha in linhas if linha.strip()])

print(f"Conteúdo limpo: {len(conteudo_json)} caracteres\n")

try:
    # Parseia JSON
    questoes_raw = json.loads(conteudo_json)

    print(f"Questões parseadas: {len(questoes_raw)}\n")

    # Converte para formato de importação
    questoes_importacao = []

    for q in questoes_raw:
        questao_convertida = {
            "disciplina": q.get('disciplina', 'Direito Geral'),
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
        if (questao_convertida['enunciado'] and
            len(questao_convertida['alternativas']) == 4 and
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
    for letra in ['A', 'B', 'C', 'D']:
        count = gabaritos.get(letra, 0)
        pct = (count / len(questoes_importacao) * 100) if questoes_importacao else 0
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

except Exception as e:
    print(f"ERRO ao processar: {e}")
    import traceback
    traceback.print_exc()
