"""
Busca seções de GABARITO nos PDFs para verificar se existem respostas
"""
import PyPDF2
import re
from pathlib import Path

pdf_path = r"D:\doutora-ia\direito\20-material-oab\563839978-Simulados-OAB-de-800-Questoes.pdf"

print("\n" + "="*70)
print(f"BUSCANDO GABARITOS NO PDF")
print("="*70 + "\n")

print(f"PDF: {Path(pdf_path).name}\n")

try:
    with open(pdf_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        total_pag = len(pdf.pages)

        print(f"Total de páginas: {total_pag}\n")

        # Procura por padrões de gabarito
        gabaritos_encontrados = []

        # Analisa últimas 50 páginas (geralmente gabarito está no final)
        inicio = max(0, total_pag - 50)

        print(f"Analisando páginas {inicio} a {total_pag}...\n")

        for i in range(inicio, total_pag):
            try:
                texto = pdf.pages[i].extract_text()

                # Procura por "GABARITO" ou "RESPOSTA"
                if re.search(r'GABARITO|RESPOSTAS?|CORRECT', texto, re.IGNORECASE):
                    print(f"\n{'='*70}")
                    print(f"PAGINA {i}: Possível seção de gabarito encontrada!")
                    print(f"{'='*70}")

                    # Mostra trecho
                    linhas = texto.split('\n')
                    for idx, linha in enumerate(linhas):
                        if re.search(r'GABARITO|RESPOSTAS?', linha, re.IGNORECASE):
                            # Mostra contexto (10 linhas antes e depois)
                            inicio_contexto = max(0, idx - 5)
                            fim_contexto = min(len(linhas), idx + 20)

                            print("\nContexto:")
                            print("-" * 70)
                            for j in range(inicio_contexto, fim_contexto):
                                print(linhas[j])
                            print("-" * 70)

                            break

                # Procura padrões como: 1. B  2. A  3. C  ou  1-B  2-A
                padrao_gabarito = re.findall(r'(?:^|\n)(\d+)[.\-\s]+([A-D])', texto, re.MULTILINE)

                if len(padrao_gabarito) >= 10:  # Se encontrou 10+ respostas em sequência
                    print(f"\n{'='*70}")
                    print(f"PAGINA {i}: Padrão de gabaritos sequenciais encontrado!")
                    print(f"{'='*70}")
                    print(f"\nPrimeiros 20 gabaritos encontrados:")
                    for num, letra in padrao_gabarito[:20]:
                        print(f"  Questão {num}: {letra}")

                    gabaritos_encontrados.extend(padrao_gabarito)

            except:
                pass

        if gabaritos_encontrados:
            print(f"\n{'='*70}")
            print(f"TOTAL DE GABARITOS ENCONTRADOS: {len(gabaritos_encontrados)}")
            print(f"{'='*70}\n")

            # Mostra distribuição por resposta
            from collections import Counter
            distribuicao = Counter([letra for _, letra in gabaritos_encontrados])

            print("Distribuição das respostas:")
            for letra in ['A', 'B', 'C', 'D']:
                count = distribuicao.get(letra, 0)
                pct = (count / len(gabaritos_encontrados) * 100) if gabaritos_encontrados else 0
                print(f"  {letra}: {count:3d} ({pct:.1f}%)")

        else:
            print("\n" + "="*70)
            print("NENHUM GABARITO ENCONTRADO")
            print("="*70)
            print("\nPossibilidades:")
            print("1. PDF não contém gabaritos")
            print("2. Gabaritos estão em formato diferente")
            print("3. PDF é apenas para treino (sem respostas)")
            print()

except Exception as e:
    print(f"ERRO: {e}")
    import traceback
    traceback.print_exc()
