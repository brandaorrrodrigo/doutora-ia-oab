"""
Processa Apostila Com Gabarito
"""
import json
import sys
sys.path.insert(0, 'D:/JURIS_IA_CORE_V1/tools')
from extrator_gabaritos import extrair_gabarito_tabela
from pathlib import Path

print("\n" + "="*70)
print("PROCESSANDO: APOSTILA QUESTOES OAB COM GABARITO")
print("="*70 + "\n")

pdf_path = r"D:\doutora-ia\direito\20-material-oab\14846014-Apostila-Questoes-OAB-Com-Gabarito.pdf"
json_path = "questoes_extraidas/q_14846014-Apostila-Questoes-OAB-Com-Gabarito.json"

print(f"PDF: {Path(pdf_path).name}")
print(f"Tamanho: {Path(pdf_path).stat().st_size / (1024*1024):.1f} MB\n")

# Verificar se JSON existe
if not Path(json_path).exists():
    print(f"[ERRO] JSON nao encontrado: {json_path}")
    print("Execute o extrator de questoes primeiro!")
    sys.exit(1)

# Carregar questões extraídas
with open(json_path, 'r', encoding='utf-8') as f:
    dados = json.load(f)

questoes = dados.get('questoes', [])
print(f"Questoes extraidas previamente: {len(questoes)}\n")

# Extrair gabaritos do PDF
print("Extraindo gabaritos do PDF...")
gabaritos = extrair_gabarito_tabela(pdf_path)
print(f"Gabaritos encontrados: {len(gabaritos)}\n")

if len(gabaritos) > 0:
    # Mostrar amostra
    print("Primeiros 20 gabaritos:")
    for i in range(1, min(21, len(gabaritos) + 1)):
        if i in gabaritos:
            print(f"  Questao {i}: {gabaritos[i]}")

    # Associar gabaritos às questões
    print(f"\nAssociando gabaritos as {len(questoes)} questoes...")
    atualizadas = 0

    for q in questoes:
        num = q.get('numero')
        if num and num in gabaritos:
            q['alternativa_correta'] = gabaritos[num]
            atualizadas += 1

    print(f"Questoes atualizadas: {atualizadas}\n")

    # Salvar
    output_path = "questoes_extraidas/q_14846014-Apostila-Questoes-OAB-Com-Gabarito_COM_GABARITO.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"Arquivo salvo: {output_path}\n")

    # Distribuição
    from collections import Counter
    distribuicao = Counter(gabaritos.values())

    print("Distribuicao de gabaritos:")
    total_gab = sum(distribuicao.values())
    for letra in ['A', 'B', 'C', 'D']:
        count = distribuicao.get(letra, 0)
        pct = (count / total_gab * 100) if total_gab > 0 else 0
        print(f"  {letra}: {count:3d} ({pct:5.1f}%)")

    print("\n" + "="*70)
    print(f"SUCESSO: {atualizadas} questoes com gabarito!")
    print("="*70 + "\n")

else:
    print("[AVISO] Nenhum gabarito encontrado no PDF!")
    print("O PDF pode nao ter secao de gabaritos ou estar em formato nao reconhecido.\n")
