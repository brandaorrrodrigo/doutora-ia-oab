"""
Extrator Formato 2: QUESTAO numero + GABARITO/RESPOSTA LETRA
Exemplo: QUESTÃO 32 ... A) B) C) D) ... RESPOSTA LETRA: A
"""
import sys
import json
import re
from pathlib import Path
import PyPDF2

def extrair_formato2(pdf_path, output_json):
    """Extrai questoes com formato: QUESTAO numero + gabarito"""

    print(f"Processando (Formato 2): {Path(pdf_path).name}\n")

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

            # Padrao 1: QUESTAO numero + alternativas + RESPOSTA LETRA
            padrao_questao = re.compile(
                r'QUEST[AÃ]O\s+(\d+)\s*(.*?)'  # Numero e enunciado
                r'(?:Alternativas|A\))(.*?)'  # Alternativas
                r'(?:RESPOSTA LETRA:\s*([A-D])|GABARITO)',  # Gabarito
                re.DOTALL | re.IGNORECASE
            )

            # Padrao 2: Extrai alternativas individuais
            padrao_alt = re.compile(r'([A-D])\)\s*([^A-D\n]*(?:\n(?![A-D]\))[^\n]*)*)', re.MULTILINE)

            questoes = []

            for match in padrao_questao.finditer(texto_completo):
                numero = match.group(1)
                enunciado = match.group(2).strip()
                bloco_alternativas = match.group(3)
                gabarito = match.group(4) if match.group(4) else "REVISAR"

                # Extrai alternativas
                alternativas = {}
                for alt_match in padrao_alt.finditer(bloco_alternativas):
                    letra = alt_match.group(1)
                    texto_alt = alt_match.group(2).strip()
                    alternativas[letra] = texto_alt[:300]

                # Valida
                if len(enunciado) > 30 and len(alternativas) >= 4:
                    questoes.append({
                        "codigo_questao": f"OAB_F2_{Path(pdf_path).stem}_{numero}",
                        "numero": int(numero),
                        "enunciado": enunciado[:600],
                        "alternativas": alternativas,
                        "alternativa_correta": gabarito,
                        "disciplina": "REVISAR",
                        "status": "EXTRAIDO_FORMATO2"
                    })

            # Se nao encontrou com RESPOSTA LETRA, tenta padrao simples
            if len(questoes) == 0:
                padrao_simples = re.compile(
                    r'QUEST[AÃ]O\s+(\d+)\s*(.*?)'
                    r'[A-D]\)(.*?)'
                    r'(?=QUEST[AÃ]O\s+\d+|GABARITO|$)',
                    re.DOTALL | re.IGNORECASE
                )

                for match in padrao_simples.finditer(texto_completo):
                    numero = match.group(1)
                    enunciado = match.group(2).strip()
                    bloco = match.group(3)

                    alternativas = {}
                    for alt_match in padrao_alt.finditer(match.group(0)):
                        letra = alt_match.group(1)
                        texto_alt = alt_match.group(2).strip()
                        alternativas[letra] = texto_alt[:300]

                    if len(enunciado) > 30 and len(alternativas) >= 4:
                        questoes.append({
                            "codigo_questao": f"OAB_F2_{Path(pdf_path).stem}_{numero}",
                            "numero": int(numero),
                            "enunciado": enunciado[:600],
                            "alternativas": alternativas,
                            "alternativa_correta": "REVISAR",
                            "disciplina": "REVISAR",
                            "status": "EXTRAIDO_FORMATO2_SIMPLES"
                        })

            print(f"Questoes encontradas: {len(questoes)}\n")

            # Salva
            with open(output_json, 'w', encoding='utf-8') as out:
                json.dump({
                    "total_questoes": len(questoes),
                    "formato": "Formato 2 - QUESTAO numero + GABARITO",
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
        print("Uso: python extrator_formato2.py <pdf> <output.json>")
        sys.exit(1)

    total = extrair_formato2(sys.argv[1], sys.argv[2])
    print(f"\n{'='*50}")
    print(f"CONCLUIDO: {total} questoes!")
    print(f"{'='*50}")
