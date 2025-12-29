import sys
import json
import re
from pathlib import Path
import PyPDF2

def extrair_questoes_completas(pdf_path, output_json):
    """
    Extrator inteligente que identifica questoes completas
    Procura por: numero + texto + alternativas (A)(B)(C)(D)
    """

    print(f"Processando: {Path(pdf_path).name}\n")

    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            total_pag = len(pdf.pages)

            print(f"Total de paginas: {total_pag}")

            # Extrai texto de todas as paginas
            texto_completo = ""
            for i, pagina in enumerate(pdf.pages):
                if i % 100 == 0:
                    print(f"Lendo pagina {i}/{total_pag}...")
                try:
                    texto_completo += "\n" + pagina.extract_text()
                except:
                    pass

            print(f"Texto extraido: {len(texto_completo)} caracteres\n")

            # Padrão para identificar questões
            # Numero seguido de alternativas A, B, C, D
            padrao_questao = re.compile(
                r'(?:^|\n)(\d+)\s*\n(.*?)'  # Numero e enunciado
                r'\(A\)(.*?)'  # Alternativa A
                r'\(B\)(.*?)'  # Alternativa B
                r'\(C\)(.*?)'  # Alternativa C
                r'\(D\)(.*?)'  # Alternativa D
                r'(?=\n\d+\s*\n|\Z)',  # Até proxima questao
                re.DOTALL
            )

            questoes = []
            matches = padrao_questao.finditer(texto_completo)

            for match in matches:
                numero = match.group(1)
                enunciado = match.group(2).strip()
                alt_a = match.group(3).strip()
                alt_b = match.group(4).strip()
                alt_c = match.group(5).strip()
                alt_d = match.group(6).strip()

                # Valida se tem conteudo minimo
                if len(enunciado) > 20:
                    questoes.append({
                        "codigo_questao": f"OAB_{Path(pdf_path).stem}_{numero}",
                        "numero": int(numero),
                        "enunciado": enunciado[:500],  # Primeiros 500 chars
                        "alternativas": {
                            "A": alt_a[:200] if len(alt_a) > 10 else "REVISAR",
                            "B": alt_b[:200] if len(alt_b) > 10 else "REVISAR",
                            "C": alt_c[:200] if len(alt_c) > 10 else "REVISAR",
                            "D": alt_d[:200] if len(alt_d) > 10 else "REVISAR",
                        },
                        "alternativa_correta": "REVISAR",
                        "disciplina": "REVISAR",
                        "topico": "REVISAR",
                        "status": "EXTRAIDO - NECESSITA REVISAO"
                    })

            print(f"Questoes completas encontradas: {len(questoes)}\n")

            # Salva
            with open(output_json, 'w', encoding='utf-8') as out:
                json.dump({
                    "total_questoes": len(questoes),
                    "arquivo_origem": str(Path(pdf_path).name),
                    "questoes": questoes
                }, out, indent=2, ensure_ascii=False)

            print(f"Salvo em: {output_json}")
            print(f"\nResumo:")
            print(f"  Total extraido: {len(questoes)} questoes")
            if questoes:
                print(f"  Primeira questao: #{questoes[0]['numero']}")
                print(f"  Ultima questao: #{questoes[-1]['numero']}")

            return len(questoes)

    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python extrator_inteligente.py <pdf> <output.json>")
        sys.exit(1)

    total = extrair_questoes_completas(sys.argv[1], sys.argv[2])
    print(f"\n{'='*50}")
    print(f"CONCLUIDO: {total} questoes extraidas!")
    print(f"{'='*50}")
