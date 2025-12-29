import PyPDF2
from pathlib import Path

pasta = Path(r"D:\doutora-ia\direito\20-material-oab")

# PDFs para analisar
pdfs_analisar = [
    '14846014-Apostila-Questoes-OAB-Com-Gabarito.pdf',
    '862725909-LIVRO-09-QUESTOES.pdf',
    '660781026-300-Questoes-Comentadas-Para-OAB.pdf',
    '518189454-RESUMAPAS-OAB-XXXII.pdf',
    '781921960-3-E-book-Treinamento-de-Questo-es.pdf'
]

for pdf_nome in pdfs_analisar:
    print('\n' + '='*70)
    print(f'ANALISANDO: {pdf_nome}')
    print('='*70)

    try:
        caminho = pasta / pdf_nome
        with open(caminho, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)

            total_pag = len(pdf.pages)
            print(f'Total de paginas: {total_pag}')

            # Analisa paginas 5, 10, 15
            for pag_num in [5, 10, 15]:
                if pag_num < total_pag:
                    print(f'\n--- Amostra Pagina {pag_num} ---')
                    texto = pdf.pages[pag_num].extract_text()

                    # Mostra primeiros 800 caracteres
                    print(texto[:800])
                    print('\n[... resto da pagina omitido ...]')

                    # Analisa padroes
                    if '(A)' in texto and '(B)' in texto:
                        print('\n[!] FORMATO: Tem alternativas (A)(B) detectadas!')
                    if 'QUESTAO' in texto.upper():
                        print('[!] FORMATO: Palavra QUESTAO detectada!')

                    # Procura por numeracao simples
                    import re
                    nums = re.findall(r'^\d+[\.\)]', texto, re.MULTILINE)
                    if nums:
                        print(f'[!] FORMATO: Numeracao encontrada: {nums[:5]}')

    except Exception as e:
        print(f'ERRO: {e}')

print('\n' + '='*70)
print('ANALISE CONCLUIDA')
print('='*70)
