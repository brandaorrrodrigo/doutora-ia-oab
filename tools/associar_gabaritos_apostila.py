"""
Associa gabaritos extraídos às questões da Apostila
"""
import json
import sys
sys.path.insert(0, 'D:/JURIS_IA_CORE_V1/tools')
from extrator_gabaritos import extrair_gabarito_tabela

print("\n" + "="*70)
print("ASSOCIANDO GABARITOS - APOSTILA")
print("="*70 + "\n")

# Carregar questões reextraídas
with open('questoes_extraidas/q_14846014-Apostila-REEXTRAIDO.json', 'r', encoding='utf-8') as f:
    dados = json.load(f)

questoes = dados['questoes']
print(f"Questoes carregadas: {len(questoes)}\n")

# Extrair gabaritos do PDF
pdf_path = r"D:\doutora-ia\direito\20-material-oab\14846014-Apostila-Questoes-OAB-Com-Gabarito.pdf"
print("Extraindo gabaritos do PDF...")
gabaritos = extrair_gabarito_tabela(pdf_path)
print(f"Gabaritos encontrados: {len(gabaritos)}\n")

# Tentar extrair mais gabaritos procurando em outras páginas
if len(gabaritos) < 100:
    print("Poucos gabaritos encontrados. Tentando extração manual...")
    import PyPDF2
    import re

    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)

        # Procurar em TODAS as páginas por padrões de gabarito
        for i in range(len(pdf.pages)):
            try:
                texto = pdf.pages[i].extract_text()

                # Padrão: "1. B  2. A  3. C"
                matches = re.findall(r'(\d+)\s*[.:\-]\s*([A-D])', texto)
                for num_str, letra in matches:
                    num = int(num_str)
                    if num not in gabaritos:
                        gabaritos[num] = letra

            except:
                pass

    print(f"Total de gabaritos após busca completa: {len(gabaritos)}\n")

if gabaritos:
    # Associar
    atualizadas = 0
    for q in questoes:
        num = q.get('numero')
        if num and num in gabaritos:
            q['alternativa_correta'] = gabaritos[num]
            atualizadas += 1

    print(f"Questoes atualizadas com gabarito: {atualizadas}")
    print(f"Questoes sem gabarito: {len(questoes) - atualizadas}\n")

    # Salvar
    dados['questoes'] = questoes

    with open('questoes_extraidas/q_14846014-Apostila_COM_GABARITO.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    # Estatísticas
    from collections import Counter
    gab_usados = [q['alternativa_correta'] for q in questoes if q['alternativa_correta'] in ['A', 'B', 'C', 'D']]

    if gab_usados:
        dist = Counter(gab_usados)
        print("Distribuicao de gabaritos (questoes com gabarito):")
        for letra in ['A', 'B', 'C', 'D']:
            count = dist.get(letra, 0)
            pct = (count / len(gab_usados) * 100) if gab_usados else 0
            print(f"  {letra}: {count:3d} ({pct:5.1f}%)")

    print("\n" + "="*70)
    if atualizadas > 0:
        print(f"SUCESSO: {atualizadas} questoes com gabarito!")
    else:
        print("AVISO: Nenhum gabarito encontrado")
    print("="*70 + "\n")

else:
    print("[ERRO] Nenhum gabarito encontrado!")
    print("O PDF pode nao conter secao de gabaritos ou estar em formato diferente.\n")
