import sys
from pathlib import Path
import subprocess

# Pasta com os PDFs
pasta_pdfs = Path(r"D:\doutora-ia\direito\20-material-oab")
pasta_saida = Path(r"D:\JURIS_IA_CORE_V1\tools\questoes_extraidas")

# Cria pasta de saida
pasta_saida.mkdir(exist_ok=True)

# Lista todos os PDFs
pdfs = sorted(pasta_pdfs.glob("*.pdf"))

print(f"\n{'='*60}")
print(f"PROCESSAMENTO EM MASSA - {len(pdfs)} PDFs")
print(f"{'='*60}\n")

total_questoes = 0
sucesso = 0
falhas = 0

resultados = []

for i, pdf in enumerate(pdfs, 1):
    print(f"\n[{i}/{len(pdfs)}] {pdf.name}")
    print("-" * 60)

    # Nome do arquivo de saida
    output_json = pasta_saida / f"q_{pdf.stem}.json"

    try:
        # Executa extrator
        result = subprocess.run(
            [
                "python",
                "extrator_inteligente.py",
                str(pdf),
                str(output_json)
            ],
            capture_output=True,
            text=True,
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )

        # Verifica quantas questoes foram extraidas
        import json
        if output_json.exists():
            with open(output_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                num_questoes = dados.get("total_questoes", 0)

                if num_questoes > 0:
                    total_questoes += num_questoes
                    sucesso += 1
                    print(f"  SUCESSO: {num_questoes} questoes extraidas")

                    resultados.append({
                        "arquivo": pdf.name,
                        "questoes": num_questoes,
                        "json": str(output_json)
                    })
                else:
                    falhas += 1
                    print(f"  FALHA: 0 questoes (formato nao suportado)")
        else:
            falhas += 1
            print(f"  ERRO: Nao gerou arquivo JSON")

    except subprocess.TimeoutExpired:
        falhas += 1
        print(f"  TIMEOUT: PDF muito grande")

    except Exception as e:
        falhas += 1
        print(f"  ERRO: {e}")

# Relatorio final
print(f"\n\n{'='*60}")
print("RELATORIO FINAL")
print(f"{'='*60}\n")

print(f"PDFs processados:     {len(pdfs)}")
print(f"Sucessos:             {sucesso}")
print(f"Falhas:               {falhas}")
print(f"\nTOTAL DE QUESTOES:    {total_questoes} questoes! 🎉\n")

print("\nTOP 10 PDFs com mais questoes:")
print("-" * 60)
for i, r in enumerate(sorted(resultados, key=lambda x: x['questoes'], reverse=True)[:10], 1):
    print(f"{i:2d}. {r['questoes']:4d} questoes - {r['arquivo'][:50]}")

# Salva relatorio
relatorio_path = pasta_saida / "RELATORIO_EXTRACAO.txt"
with open(relatorio_path, 'w', encoding='utf-8') as f:
    f.write(f"RELATORIO DE EXTRACAO - {len(pdfs)} PDFs processados\n")
    f.write("="*60 + "\n\n")
    f.write(f"Total de questoes extraidas: {total_questoes}\n")
    f.write(f"Sucessos: {sucesso}\n")
    f.write(f"Falhas: {falhas}\n\n")

    f.write("\nLista completa:\n")
    for r in sorted(resultados, key=lambda x: x['questoes'], reverse=True):
        f.write(f"{r['questoes']:5d} questoes - {r['arquivo']}\n")

print(f"\nRelatorio salvo em: {relatorio_path}")
print(f"Arquivos JSON em: {pasta_saida}\n")
