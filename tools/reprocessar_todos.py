import subprocess
import json
from pathlib import Path

pasta_pdfs = Path(r"D:\doutora-ia\direito\20-material-oab")
pasta_saida = Path(r"D:\JURIS_IA_CORE_V1\tools\questoes_reprocessadas")
pasta_saida.mkdir(exist_ok=True)

# PDFs para tentar com Formato 1 (numero. a) b) c) d))
pdfs_formato1 = [
    '14846014-Apostila-Questoes-OAB-Com-Gabarito.pdf',
    '518189454-RESUMAPAS-OAB-XXXII.pdf',
    '660781026-300-Questoes-Comentadas-Para-OAB.pdf',
    '663632334-Apostila-Professor-Resende.pdf',
    '651924283-CADERNO-DE-ESTRUTURACAO-Oab.pdf',
    '652703739-Caderno-de-Questoes-Padroes-de-Respostas.pdf',
    '608615214-Caderno-de-Dicas-e-Questoes-PartiuConcurseiro.pdf',
    '701419187-Resumao-1a-Fase-Da-OAB-40.pdf',
]

# PDFs para tentar com Formato 2 (QUESTAO numero)
pdfs_formato2 = [
    '862725909-LIVRO-09-QUESTOES.pdf',
    '781921960-3-E-book-Treinamento-de-Questo-es.pdf',
    '658346596-Material-de-Revisao-OAB-XXXIII-2�-Edicao.pdf',
]

print(f"\n{'='*70}")
print("REPROCESSAMENTO COM EXTRATORES ESPECIALIZADOS")
print(f"{'='*70}\n")

total_questoes = 0
sucesso = 0

# Processa Formato 1
print(f"\n--- FORMATO 1: {len(pdfs_formato1)} PDFs ---\n")
for pdf_nome in pdfs_formato1:
    print(f"Processando: {pdf_nome[:50]}...")

    try:
        pdf_path = pasta_pdfs / pdf_nome
        output = pasta_saida / f"f1_{pdf_path.stem}.json"

        result = subprocess.run(
            ["python", "extrator_formato1.py", str(pdf_path), str(output)],
            capture_output=True,
            timeout=180,
            encoding='utf-8',
            errors='replace'
        )

        if output.exists():
            with open(output, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                num = dados.get('total_questoes', 0)

                if num > 0:
                    total_questoes += num
                    sucesso += 1
                    print(f"  SUCESSO: {num} questoes\n")
                else:
                    print(f"  FALHA: 0 questoes\n")

    except Exception as e:
        print(f"  ERRO: {e}\n")

# Processa Formato 2
print(f"\n--- FORMATO 2: {len(pdfs_formato2)} PDFs ---\n")
for pdf_nome in pdfs_formato2:
    print(f"Processando: {pdf_nome[:50]}...")

    try:
        pdf_path = pasta_pdfs / pdf_nome
        output = pasta_saida / f"f2_{pdf_path.stem}.json"

        result = subprocess.run(
            ["python", "extrator_formato2.py", str(pdf_path), str(output)],
            capture_output=True,
            timeout=180,
            encoding='utf-8',
            errors='replace'
        )

        if output.exists():
            with open(output, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                num = dados.get('total_questoes', 0)

                if num > 0:
                    total_questoes += num
                    sucesso += 1
                    print(f"  SUCESSO: {num} questoes\n")
                else:
                    print(f"  FALHA: 0 questoes\n")

    except Exception as e:
        print(f"  ERRO: {e}\n")

print(f"\n{'='*70}")
print(f"TOTAL REPROCESSADO: {total_questoes} questoes!")
print(f"Sucessos: {sucesso}/{len(pdfs_formato1) + len(pdfs_formato2)}")
print(f"{'='*70}\n")
