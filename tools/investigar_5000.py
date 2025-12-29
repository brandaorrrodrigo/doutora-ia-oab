import PyPDF2
import re

pdf_path = r"D:\doutora-ia\direito\20-material-oab\Como Passar Na OAB 5.000 Questo -.pdf"

print("\n" + "="*70)
print("INVESTIGACAO: PDF 5.000 QUESTOES")
print("="*70 + "\n")

with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)

    total_pag = len(pdf.pages)
    print(f"Total de paginas: {total_pag}\n")

    # Analisa amostras
    paginas_teste = [5, 50, 100, 200, 500, 800, 1000]

    for pag_num in paginas_teste:
        if pag_num < total_pag:
            print("\n" + "="*70)
            print(f"PAGINA {pag_num}:")
            print("="*70)

            texto = pdf.pages[pag_num].extract_text()

            # Mostra primeiros 800 caracteres
            print(texto[:800])

            # Detecta padroes
            print("\n--- ANALISE DE PADROES ---")

            # Conta diferentes padroes de numeracao
            nums_ponto = len(re.findall(r'^\d+\.', texto, re.MULTILINE))
            nums_questao = len(re.findall(r'QUEST[AÃ]O\s+\d+', texto, re.IGNORECASE))
            nums_paren = len(re.findall(r'^\d+\)', texto, re.MULTILINE))
            alt_maiusc = len(re.findall(r'\n[A-D]\)', texto))
            alt_minusc = len(re.findall(r'\n[a-d]\)', texto))

            print(f"Padroes encontrados:")
            print(f"  - Numero com ponto (123.): {nums_ponto}")
            print(f"  - QUESTAO numero: {nums_questao}")
            print(f"  - Numero com parentese (123)): {nums_paren}")
            print(f"  - Alternativas A) B) C) D): {alt_maiusc}")
            print(f"  - Alternativas a) b) c) d): {alt_minusc}")

            # Verifica se tem imagens (pode ser PDF escaneado)
            if len(texto.strip()) < 100:
                print("\n  [ALERTA] Pagina com muito pouco texto - pode ser imagem!")

            print()

# Analisa estrutura geral
print("\n" + "="*70)
print("ANALISE GERAL DO PDF")
print("="*70 + "\n")

# Extrai todo o texto para analise
with open(pdf_path, 'rb') as f:
    pdf = PyPDF2.PdfReader(f)

    # Amostra de 20 paginas espalhadas
    texto_total = ""
    for i in range(0, min(total_pag, 1000), 50):
        try:
            texto_total += pdf.pages[i].extract_text()
        except:
            pass

print(f"Texto amostrado: {len(texto_total)} caracteres\n")

# Busca todos os numeros de questoes
questoes_encontradas = set()

padroes_busca = [
    r'(?:^|\n)(\d+)\.(?:\s|\n)',  # 1. 2. 3.
    r'(?:^|\n)(\d+)\)(?:\s|\n)',  # 1) 2) 3)
    r'QUEST[AÃ]O\s+(\d+)',        # QUESTAO 123
]

for padrao in padroes_busca:
    matches = re.finditer(padrao, texto_total, re.MULTILINE | re.IGNORECASE)
    for m in matches:
        num = int(m.group(1))
        if num <= 6000:  # Limite razoavel
            questoes_encontradas.add(num)

questoes_ordenadas = sorted(list(questoes_encontradas))

print(f"Numeros de questoes identificados na amostra: {len(questoes_ordenadas)}")

if questoes_ordenadas:
    print(f"Primeira questao: {questoes_ordenadas[0]}")
    print(f"Ultima questao: {questoes_ordenadas[-1]}")
    print(f"\nPrimeiras 20: {questoes_ordenadas[:20]}")
    print(f"Ultimas 20: {questoes_ordenadas[-20:]}")

    # Verifica se sao sequenciais
    gaps = []
    for i in range(len(questoes_ordenadas)-1):
        diff = questoes_ordenadas[i+1] - questoes_ordenadas[i]
        if diff > 1:
            gaps.append((questoes_ordenadas[i], questoes_ordenadas[i+1], diff))

    if gaps:
        print(f"\nGaps encontrados (possiveis questoes faltando): {len(gaps)}")
        if len(gaps) < 20:
            for g in gaps:
                print(f"  Gap de {g[0]} para {g[1]} (diferenca: {g[2]})")

print("\n" + "="*70)
print("CONCLUSAO")
print("="*70)
print("\nPossibilidades:")
print("1. PDF tem questoes em formato nao detectado pelo extrator")
print("2. PDF e escaneado (imagens) sem OCR")
print("3. Questoes estao em tabelas ou formato especial")
print("4. Nome do PDF e enganoso (nao tem 5000 questoes)")
print("\n")
