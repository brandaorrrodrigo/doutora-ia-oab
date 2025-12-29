"""
Extrator Formato 1: Numeracao com ponto + alternativas minusculas
Exemplo: 1. (OAB/DF – 2005) Texto... a) alt b) alt c) alt d) alt
"""
import sys
import json
import re
from pathlib import Path
import PyPDF2

def extrair_formato1(pdf_path, output_json):
    """Extrai questoes com formato: numero. texto a) b) c) d)"""

    print(f"Processando (Formato 1): {Path(pdf_path).name}\n")

    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            texto_completo = ""

            for i, pagina in enumerate(pdf.pages):
                if i % 50 == 0:
                    print(f"Pagina {i}/{len(pdf.pages)}...")
                try:
                    texto_completo += "\n" + pagina.extract_text()
                except:
                    pass

            print(f"Texto extraido: {len(texto_completo)} caracteres\n")

            # Padrao: numero. (opcional OAB info) texto questao a) b) c) d)
            padrao = re.compile(
                r'(?:^|\n)(\d+)\.\s*(?:\(OAB[^)]*\))?\s*'  # Numero + info OAB opcional
                r'(.*?)'  # Enunciado
                r'\n?[aA]\)(.*?)'  # Alternativa a
                r'\n?[bB]\)(.*?)'  # Alternativa b
                r'\n?[cC]\)(.*?)'  # Alternativa c
                r'\n?[dD]\)(.*?)'  # Alternativa d
                r'(?=\n\d+\.|$)',  # Ate proxima ou fim
                re.DOTALL | re.IGNORECASE
            )

            questoes = []
            for match in padrao.finditer(texto_completo):
                numero = match.group(1)
                enunciado = match.group(2).strip()
                alt_a = match.group(3).strip()
                alt_b = match.group(4).strip()
                alt_c = match.group(5).strip()
                alt_d = match.group(6).strip()

                # Valida tamanho minimo
                if len(enunciado) > 30 and len(alt_a) > 5:
                    questoes.append({
                        "codigo_questao": f"OAB_F1_{Path(pdf_path).stem}_{numero}",
                        "numero": int(numero),
                        "enunciado": enunciado[:600],
                        "alternativas": {
                            "A": alt_a[:300],
                            "B": alt_b[:300],
                            "C": alt_c[:300],
                            "D": alt_d[:300],
                        },
                        "alternativa_correta": "REVISAR",
                        "disciplina": "REVISAR",
                        "status": "EXTRAIDO_FORMATO1"
                    })

            print(f"Questoes encontradas: {len(questoes)}\n")

            # Salva
            with open(output_json, 'w', encoding='utf-8') as out:
                json.dump({
                    "total_questoes": len(questoes),
                    "formato": "Formato 1 - numero. a) b) c) d)",
                    "arquivo_origem": str(Path(pdf_path).name),
                    "questoes": questoes
                }, out, indent=2, ensure_ascii=False)

            print(f"Salvo: {output_json}")
            return len(questoes)

    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python extrator_formato1.py <pdf> <output.json>")
        sys.exit(1)

    total = extrair_formato1(sys.argv[1], sys.argv[2])
    print(f"\n{'='*50}")
    print(f"CONCLUIDO: {total} questoes!")
    print(f"{'='*50}")
