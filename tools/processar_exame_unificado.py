"""
Processa Exame OAB Unificado
"""
import json
import sys
sys.path.insert(0, 'D:/JURIS_IA_CORE_V1/tools')
from extrator_gabaritos import extrair_gabarito_tabela
from pathlib import Path

print("\n" + "="*70)
print("PROCESSANDO: EXAME OAB UNIFICADO")
print("="*70 + "\n")

pdf_path = r"D:\doutora-ia\direito\20-material-oab\EXAME DA OAB UNIFICADO 1ª FASE.PDF"
json_path = "gigante_exame_unificado.json"

print(f"PDF: {Path(pdf_path).name}")
print(f"Tamanho: {Path(pdf_path).stat().st_size / (1024*1024):.1f} MB\n")

# Carregar questões extraídas
with open(json_path, 'r', encoding='utf-8') as f:
    dados = json.load(f)

questoes = dados.get('questoes', [])
print(f"Questoes extraidas previamente: {len(questoes)}\n")

# Extrair gabaritos do PDF
print("Extraindo gabaritos do PDF...")
gabaritos = extrair_gabarito_tabela(pdf_path)
print(f"Gabaritos encontrados: {len(gabaritos)}\n")

# Tentar busca mais agressiva se poucos gabaritos
if len(gabaritos) < 50:
    print("Poucos gabaritos. Tentando busca completa em todas as paginas...")
    import PyPDF2
    import re

    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        total_pags = len(pdf.pages)

        # Buscar em TODAS as páginas
        for i in range(total_pags):
            if i % 100 == 0:
                print(f"  Processando pagina {i}/{total_pags}...")

            try:
                texto = pdf.pages[i].extract_text()

                # Diversos padrões de gabarito
                patterns = [
                    r'(\d+)\s*[.:\-]\s*([A-D])',  # 1. A  ou  1: B
                    r'Quest[ãa]o\s+(\d+)\s*[:\-]\s*([A-D])',  # Questão 1: A
                    r'(\d+)\)\s*([A-D])',  # 1) A
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, texto, re.IGNORECASE)
                    for num_str, letra in matches:
                        num = int(num_str)
                        if num not in gabaritos and num <= 200:  # Limitar a números razoáveis
                            gabaritos[num] = letra.upper()

            except:
                pass

    print(f"Total gabaritos apos busca completa: {len(gabaritos)}\n")

if gabaritos:
    # Associar
    atualizadas = 0
    for q in questoes:
        num = q.get('numero')
        if num and num in gabaritos:
            q['alternativa_correta'] = gabaritos[num]
            atualizadas += 1

    print(f"Questoes atualizadas: {atualizadas}")
    print(f"Questoes sem gabarito: {len(questoes) - atualizadas}\n")

    # Salvar
    output_path = "gigante_exame_unificado_COM_GABARITO.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"Arquivo salvo: {output_path}\n")

    # Estatísticas
    from collections import Counter
    gab_usados = [q['alternativa_correta'] for q in questoes if q.get('alternativa_correta') in ['A', 'B', 'C', 'D']]

    if gab_usados:
        dist = Counter(gab_usados)
        print("Distribuicao de gabaritos:")
        total = sum(dist.values())
        for letra in ['A', 'B', 'C', 'D']:
            count = dist.get(letra, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {letra}: {count:3d} ({pct:5.1f}%)")

    print("\n" + "="*70)
    if atualizadas > 0:
        print(f"SUCESSO: {atualizadas} questoes com gabarito!")
    else:
        print("AVISO: Nenhuma questao associada")
    print("="*70 + "\n")

else:
    print("[ERRO] Nenhum gabarito encontrado no PDF!\n")
