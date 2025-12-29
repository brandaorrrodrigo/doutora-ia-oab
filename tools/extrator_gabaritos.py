"""
Extrai gabaritos de PDFs e associa às questões extraídas
"""
import PyPDF2
import re
import json
from pathlib import Path

def extrair_gabarito_tabela(pdf_path):
    """Extrai gabarito em formato de tabela (ex: 1 2 3... / A B C...)"""

    gabaritos = {}

    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            total_pag = len(pdf.pages)

            # Procura nas últimas 100 páginas
            inicio = max(0, total_pag - 100)

            for i in range(inicio, total_pag):
                try:
                    texto = pdf.pages[i].extract_text()

                    # Procura por "GABARITO"
                    if re.search(r'GABARITO', texto, re.IGNORECASE):
                        # Padrão 1: Formato tabela (1 2 3 4... / A B C D...)
                        linhas = texto.split('\n')

                        numeros_linha = []
                        respostas_linha = []

                        for linha in linhas:
                            # Linha com números sequenciais
                            nums = re.findall(r'\b(\d+)\b', linha)
                            if len(nums) >= 5:  # Linha com vários números
                                numeros_linha.extend([int(n) for n in nums])

                            # Linha com letras A-D sequenciais
                            letras = re.findall(r'\b([A-D])\b', linha)
                            if len(letras) >= 5:  # Linha com várias letras
                                respostas_linha.extend(letras)

                        # Associa números com letras
                        if len(numeros_linha) > 0 and len(respostas_linha) > 0:
                            # Assume que estão na mesma ordem
                            for idx, num in enumerate(numeros_linha):
                                if idx < len(respostas_linha):
                                    gabaritos[num] = respostas_linha[idx]

                        # Padrão 2: Formato "1. B  2. A  3. C"
                        matches = re.findall(r'(\d+)[.\-\s:]+([A-D])', texto)
                        for num_str, letra in matches:
                            num = int(num_str)
                            gabaritos[num] = letra

                except:
                    pass

    except Exception as e:
        print(f"Erro ao extrair gabarito: {e}")

    return gabaritos


# Testa com o PDF de 800 questões
pdf_path = r"D:\doutora-ia\direito\20-material-oab\563839978-Simulados-OAB-de-800-Questoes.pdf"
json_path = "questoes_extraidas/q_563839978-Simulados-OAB-de-800-Questoes.json"

print("\n" + "="*70)
print("EXTRAINDO E ASSOCIANDO GABARITOS")
print("="*70 + "\n")

print(f"PDF: {Path(pdf_path).name}")
print(f"JSON: {json_path}\n")

# Extrai gabaritos
gabaritos = extrair_gabarito_tabela(pdf_path)

print(f"Gabaritos extraídos: {len(gabaritos)}\n")

if gabaritos:
    # Mostra primeiros 20
    print("Primeiros 20 gabaritos:")
    for i in range(1, min(21, len(gabaritos) + 1)):
        if i in gabaritos:
            print(f"  Questão {i}: {gabaritos[i]}")

    # Carrega JSON das questões
    with open(json_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    questoes = dados['questoes']

    print(f"\n{len(questoes)} questões no JSON\n")

    # Associa gabaritos
    atualizadas = 0

    for q in questoes:
        num = q.get('numero')
        if num and num in gabaritos:
            q['alternativa_correta'] = gabaritos[num]
            atualizadas += 1

    print(f"Questões atualizadas com gabarito: {atualizadas}\n")

    # Salva atualizado
    output_json = "questoes_extraidas/q_563839978-Simulados-OAB-de-800-Questoes_COM_GABARITO.json"

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"Arquivo salvo: {output_json}")

    # Estatísticas
    from collections import Counter
    distribuicao = Counter(gabaritos.values())

    print(f"\nDistribuição das respostas:")
    for letra in ['A', 'B', 'C', 'D']:
        count = distribuicao.get(letra, 0)
        pct = (count / len(gabaritos) * 100) if gabaritos else 0
        print(f"  {letra}: {count:3d} ({pct:.1f}%)")

    print()

else:
    print("Nenhum gabarito encontrado!\n")
