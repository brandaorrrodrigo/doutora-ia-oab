"""
Extrator para PDFs GIGANTES (1000+ paginas)
Processa em blocos de 100 paginas por vez
"""
import sys
import json
import re
from pathlib import Path
import PyPDF2

def extrair_bloco_paginas(pdf_reader, inicio, fim):
    """Extrai texto de um bloco de paginas"""
    texto = ""
    for i in range(inicio, min(fim, len(pdf_reader.pages))):
        try:
            texto += "\n" + pdf_reader.pages[i].extract_text()
        except:
            pass
    return texto

def extrair_questoes_texto(texto, offset_numero=0):
    """Extrai questoes de um bloco de texto"""
    questoes = []

    # Tenta multiplos padroes
    padroes = [
        # Padrao 1: numero. (OAB) a) b) c) d)
        re.compile(
            r'(?:^|\n)(\d+)\.\s*(?:\(OAB[^)]*\))?\s*(.*?)'
            r'\n?[aA]\)(.*?)\n?[bB]\)(.*?)\n?[cC]\)(.*?)\n?[dD]\)(.*?)'
            r'(?=\n\d+\.|$)',
            re.DOTALL
        ),
        # Padrao 2: QUESTAO numero A) B) C) D)
        re.compile(
            r'QUEST[AÃ]O\s+(\d+)\s*(.*?)'
            r'[A-D]\)(.*?)'
            r'(?=QUEST[AÃ]O\s+\d+|GABARITO|$)',
            re.DOTALL | re.IGNORECASE
        ),
        # Padrao 3: numero) a) b) c) d)
        re.compile(
            r'(?:^|\n)(\d+)\)\s*(.*?)'
            r'\n?[aA]\)(.*?)\n?[bB]\)(.*?)\n?[cC]\)(.*?)\n?[dD]\)(.*?)'
            r'(?=\n\d+\)|$)',
            re.DOTALL
        ),
    ]

    for padrao_idx, padrao in enumerate(padroes):
        matches = list(padrao.finditer(texto))

        if len(matches) > len(questoes):
            # Este padrao encontrou mais questoes
            questoes = []

            for match in matches:
                try:
                    numero = int(match.group(1)) + offset_numero

                    if padrao_idx == 0 or padrao_idx == 2:
                        # Padroes com alternativas a) b) c) d)
                        enunciado = match.group(2).strip()
                        alt_a = match.group(3).strip() if len(match.groups()) > 2 else ""
                        alt_b = match.group(4).strip() if len(match.groups()) > 3 else ""
                        alt_c = match.group(5).strip() if len(match.groups()) > 4 else ""
                        alt_d = match.group(6).strip() if len(match.groups()) > 5 else ""

                        if len(enunciado) > 30 and len(alt_a) > 5:
                            questoes.append({
                                "numero": numero,
                                "enunciado": enunciado[:600],
                                "alternativas": {
                                    "A": alt_a[:300],
                                    "B": alt_b[:300],
                                    "C": alt_c[:300],
                                    "D": alt_d[:300],
                                }
                            })

                    elif padrao_idx == 1:
                        # Padrao QUESTAO com extração de alternativas
                        enunciado = match.group(2).strip()
                        bloco = match.group(3)

                        padrao_alt = re.compile(r'([A-D])\)\s*([^A-D\n]*(?:\n(?![A-D]\))[^\n]*)*)')
                        alternativas = {}

                        for alt_match in padrao_alt.finditer(bloco):
                            letra = alt_match.group(1)
                            texto_alt = alt_match.group(2).strip()
                            alternativas[letra] = texto_alt[:300]

                        if len(enunciado) > 30 and len(alternativas) >= 4:
                            questoes.append({
                                "numero": numero,
                                "enunciado": enunciado[:600],
                                "alternativas": alternativas
                            })

                except:
                    pass

    return questoes

def extrair_pdf_gigante(pdf_path, output_json, tamanho_bloco=100):
    """Extrai questoes de PDF gigante processando em blocos"""

    print(f"Processando PDF GIGANTE: {Path(pdf_path).name}\n")

    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            total_pag = len(pdf.pages)

            print(f"Total de paginas: {total_pag}")
            print(f"Processando em blocos de {tamanho_bloco} paginas\n")

            todas_questoes = []
            questoes_por_bloco = {}

            # Processa em blocos
            for inicio in range(0, total_pag, tamanho_bloco):
                fim = min(inicio + tamanho_bloco, total_pag)

                print(f"Bloco {inicio}-{fim} ({fim-inicio} paginas)...", end=" ")

                # Extrai texto do bloco
                texto_bloco = extrair_bloco_paginas(pdf, inicio, fim)

                # Extrai questoes
                questoes_bloco = extrair_questoes_texto(texto_bloco, offset_numero=inicio)

                if questoes_bloco:
                    questoes_por_bloco[f"pag_{inicio}-{fim}"] = len(questoes_bloco)
                    todas_questoes.extend(questoes_bloco)
                    print(f"{len(questoes_bloco)} questoes")
                else:
                    print("0 questoes")

            # Remove duplicatas por numero
            questoes_unicas = {}
            for q in todas_questoes:
                questoes_unicas[q['numero']] = q

            questoes_final = []
            for num in sorted(questoes_unicas.keys()):
                q = questoes_unicas[num]
                questoes_final.append({
                    "codigo_questao": f"OAB_GIG_{Path(pdf_path).stem}_{num}",
                    "numero": num,
                    "enunciado": q['enunciado'],
                    "alternativas": q['alternativas'],
                    "alternativa_correta": "REVISAR",
                    "disciplina": "REVISAR",
                    "status": "EXTRAIDO_PDF_GIGANTE"
                })

            print(f"\n{'='*60}")
            print(f"Total de questoes UNICAS: {len(questoes_final)}")
            print(f"{'='*60}\n")

            # Salva
            with open(output_json, 'w', encoding='utf-8') as out:
                json.dump({
                    "total_questoes": len(questoes_final),
                    "total_paginas": total_pag,
                    "blocos_processados": len(questoes_por_bloco),
                    "questoes_por_bloco": questoes_por_bloco,
                    "arquivo_origem": str(Path(pdf_path).name),
                    "questoes": questoes_final
                }, out, indent=2, ensure_ascii=False)

            print(f"Salvo em: {output_json}\n")
            return len(questoes_final)

    except Exception as e:
        print(f"ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python extrator_gigante.py <pdf> <output.json> [tamanho_bloco]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output = sys.argv[2]
    bloco = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    total = extrair_pdf_gigante(pdf_path, output, bloco)

    print(f"\n{'='*60}")
    print(f"CONCLUIDO: {total} questoes extraidas!")
    print(f"{'='*60}\n")
