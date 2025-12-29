import sys
import json
import re
from pathlib import Path
import PyPDF2

def extrair_questoes(pdf_path, output_json):
    """Extrai questoes de PDF de forma simples"""

    questoes = []

    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            total_pag = len(pdf.pages)

            print(f"Total de paginas: {total_pag}")

            texto_completo = ""
            for i, pagina in enumerate(pdf.pages):
                if i % 50 == 0:
                    print(f"Processando pagina {i}/{total_pag}...")
                texto_completo += pagina.extract_text()

            print(f"Texto extraido: {len(texto_completo)} caracteres")

            # Busca padroes de questoes
            # Padrao: "QUESTAO 1" ou "1)" ou "Questao 01"
            padroes = [
                r'(?:QUEST[AÃ]O|Quest[aã]o)\s+(\d+)',
                r'^(\d+)\)',
                r'^(\d+)\.',
            ]

            questoes_encontradas = set()

            for padrao in padroes:
                matches = re.finditer(padrao, texto_completo, re.MULTILINE)
                for m in matches:
                    num = int(m.group(1))
                    if num <= 500:  # Limita a numeros razoaveis
                        questoes_encontradas.add(num)

            print(f"Questoes identificadas: {len(questoes_encontradas)}")

            # Cria estrutura basica
            for num in sorted(questoes_encontradas):
                questoes.append({
                    "codigo_questao": f"OAB_EXT_{num:04d}",
                    "numero": num,
                    "status": "EXTRAIDO - AGUARDANDO PROCESSAMENTO",
                    "arquivo_origem": str(Path(pdf_path).name)
                })

            # Salva
            with open(output_json, 'w', encoding='utf-8') as out:
                json.dump({
                    "total_questoes": len(questoes),
                    "arquivo_origem": str(Path(pdf_path).name),
                    "total_paginas": total_pag,
                    "questoes": questoes
                }, out, indent=2, ensure_ascii=False)

            print(f"\nSucesso! {len(questoes)} questoes extraidas")
            print(f"Salvo em: {output_json}")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python extrator_simples.py <pdf> <output.json>")
        sys.exit(1)

    extrair_questoes(sys.argv[1], sys.argv[2])
