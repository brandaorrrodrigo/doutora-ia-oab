"""
Extrator de Questões OAB de PDFs
Extrai automaticamente questões de provas OAB em PDF
"""

import re
import json
import sys
from pathlib import Path

def extrair_texto_pdf(pdf_path):
    """Extrai texto de um PDF"""
    try:
        import pdfplumber
    except ImportError:
        print("[ERRO] pdfplumber não instalado. Execute: pip install pdfplumber")
        return None

    texto_completo = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"[OK] PDF aberto: {len(pdf.pages)} páginas")

            for i, pagina in enumerate(pdf.pages, 1):
                texto = pagina.extract_text()
                if texto:
                    texto_completo.append(texto)
                    if i % 5 == 0:
                        print(f"  Processando página {i}/{len(pdf.pages)}...")

        return "\n".join(texto_completo)

    except Exception as e:
        print(f"[ERRO] Falha ao ler PDF: {e}")
        return None


def identificar_disciplina(texto):
    """Identifica a disciplina pela presença de palavras-chave"""
    disciplinas_keywords = {
        'Direito Constitucional': ['constitucion', 'direitos fundamentais', 'CF/88', 'supremo tribunal'],
        'Direito Civil': ['código civil', 'cc/02', 'obrigações', 'contratos', 'família'],
        'Direito Penal': ['código penal', 'crime', 'pena', 'imputab', 'dolo'],
        'Direito Processual Civil': ['cpc', 'processo civil', 'petição inicial', 'sentença'],
        'Direito Processual Penal': ['cpp', 'processo penal', 'inquérito', 'flagrante'],
        'Direito do Trabalho': ['clt', 'trabalho', 'empregado', 'jornada', 'fgts'],
        'Direito Empresarial': ['empresa', 'sociedade', 'falência', 'recuperação judicial'],
        'Direito Tributário': ['tributo', 'imposto', 'ctn', 'icms', 'iss'],
        'Direito Administrativo': ['administração pública', 'licitação', 'servidor público'],
        'Ética Profissional': ['estatuto da oab', 'advogado', 'ética', 'disciplina']
    }

    texto_lower = texto.lower()
    pontuacoes = {}

    for disciplina, keywords in disciplinas_keywords.items():
        pontuacao = sum(1 for kw in keywords if kw in texto_lower)
        if pontuacao > 0:
            pontuacoes[disciplina] = pontuacao

    if pontuacoes:
        return max(pontuacoes, key=pontuacoes.get)
    return "Direito Geral"


def extrair_questoes(texto):
    """Extrai questões do texto"""
    questoes = []

    # Padrão para identificar questões
    # Ex: "QUESTÃO 1", "01.", "1)", "Questão 01"
    padrao_inicio = r'(?:QUESTÃO|QUESTAO|Questão|Questao|Q\.?)\s*(\d{1,2})|^(\d{1,2})[\.\)]'

    # Dividir texto em blocos por questão
    linhas = texto.split('\n')
    questao_atual = None
    buffer = []

    for linha in linhas:
        # Detectar início de questão
        match = re.search(padrao_inicio, linha, re.IGNORECASE)

        if match:
            # Salvar questão anterior
            if buffer:
                questao_texto = '\n'.join(buffer)
                questao_processada = processar_questao(questao_texto, questao_atual)
                if questao_processada:
                    questoes.append(questao_processada)

            # Iniciar nova questão
            numero = match.group(1) or match.group(2)
            questao_atual = int(numero)
            buffer = [linha]
        else:
            buffer.append(linha)

    # Processar última questão
    if buffer:
        questao_texto = '\n'.join(buffer)
        questao_processada = processar_questao(questao_texto, questao_atual or len(questoes) + 1)
        if questao_processada:
            questoes.append(questao_processada)

    return questoes


def processar_questao(texto, numero):
    """Processa uma questão individual"""

    # Extrair enunciado (tudo antes das alternativas)
    match_alt = re.search(r'\n\s*[A-D][\.\)]', texto)
    if not match_alt:
        return None

    enunciado_bruto = texto[:match_alt.start()].strip()

    # Limpar número da questão do enunciado
    enunciado = re.sub(r'^(?:QUESTÃO|QUESTAO|Questão|Questao|Q\.?)\s*\d{1,2}[\.\)]?\s*', '', enunciado_bruto, flags=re.IGNORECASE)

    # Extrair alternativas
    alternativas_texto = texto[match_alt.start():]
    alternativas = {}

    for letra in ['A', 'B', 'C', 'D']:
        padrao = rf'{letra}[\.\)]\s*(.+?)(?=\n\s*[A-D][\.\)]|\n\n|$)'
        match = re.search(padrao, alternativas_texto, re.DOTALL)
        if match:
            alternativas[letra] = match.group(1).strip()

    # Validar se tem 4 alternativas
    if len(alternativas) != 4:
        return None

    # Identificar disciplina
    disciplina = identificar_disciplina(texto)

    return {
        'numero': numero,
        'disciplina': disciplina,
        'topico': 'A definir',
        'enunciado': enunciado,
        'alternativas': alternativas,
        'gabarito': 'A',  # Precisa do gabarito separado
        'explicacao': 'Consultar gabarito oficial',
        'fundamentacao': 'A definir',
        'dificuldade': 'medio',
        'ano_prova': 2024
    }


def extrair_gabarito(texto):
    """Extrai gabarito do PDF (se disponível)"""
    gabaritos = {}

    # Procurar padrões de gabarito
    # Ex: "1 - A", "01. B", "Questão 1: C"
    padroes = [
        r'(?:QUESTÃO|Questão|Q\.?)\s*(\d{1,2})\s*[:\-\.]?\s*([A-D])',
        r'(\d{1,2})\s*[\.\-]\s*([A-D])',
    ]

    for padrao in padroes:
        matches = re.findall(padrao, texto, re.IGNORECASE)
        for num, resp in matches:
            gabaritos[int(num)] = resp.upper()

    return gabaritos


def processar_pdf(pdf_path, gabarito_path=None):
    """Processa um PDF completo e extrai todas as questões"""

    print("="*60)
    print(f" PROCESSANDO: {Path(pdf_path).name}")
    print("="*60)

    # Extrair texto
    print("\n[1/4] Extraindo texto do PDF...")
    texto = extrair_texto_pdf(pdf_path)
    if not texto:
        print("[ERRO] Não foi possível extrair texto")
        return []

    print(f"[OK] {len(texto)} caracteres extraídos")

    # Extrair questões
    print("\n[2/4] Identificando questões...")
    questoes = extrair_questoes(texto)
    print(f"[OK] {len(questoes)} questões encontradas")

    # Extrair gabarito
    print("\n[3/4] Processando gabarito...")
    if gabarito_path:
        texto_gabarito = extrair_texto_pdf(gabarito_path)
        gabaritos = extrair_gabarito(texto_gabarito)
    else:
        # Tentar extrair gabarito do mesmo PDF
        gabaritos = extrair_gabarito(texto)

    # Aplicar gabaritos
    for questao in questoes:
        num = questao['numero']
        if num in gabaritos:
            questao['gabarito'] = gabaritos[num]

    print(f"[OK] {len(gabaritos)} gabaritos aplicados")

    # Relatório
    print("\n[4/4] Relatório:")
    print(f"  Total de questões: {len(questoes)}")
    print(f"  Com gabarito: {sum(1 for q in questoes if q['gabarito'] != 'A')}")
    print(f"  Sem gabarito: {sum(1 for q in questoes if q['gabarito'] == 'A')}")

    return questoes


def salvar_json(questoes, arquivo_saida):
    """Salva questões em arquivo JSON"""
    data = {'questoes': questoes}

    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Questões salvas em: {arquivo_saida}")


if __name__ == "__main__":
    print("\n")
    print("="*60)
    print(" EXTRATOR DE QUESTÕES OAB - PDF")
    print("="*60)
    print("\n")

    if len(sys.argv) < 2:
        print("USO: python extrair_questoes_pdf.py <arquivo.pdf> [gabarito.pdf]")
        print("\nEXEMPLOS:")
        print("  python extrair_questoes_pdf.py prova_oab_41.pdf")
        print("  python extrair_questoes_pdf.py prova.pdf gabarito.pdf")
        print("\nOU processar pasta inteira:")
        print("  python extrair_questoes_pdf.py --pasta provas/")
        sys.exit(1)

    # Modo pasta
    if sys.argv[1] == '--pasta' and len(sys.argv) > 2:
        pasta = Path(sys.argv[2])
        pdfs = list(pasta.glob('*.pdf'))

        print(f"Encontrados {len(pdfs)} PDFs na pasta\n")

        todas_questoes = []
        for pdf in pdfs:
            questoes = processar_pdf(str(pdf))
            todas_questoes.extend(questoes)

        # Salvar todas
        saida = "data/questoes_extraidas_lote.json"
        salvar_json(todas_questoes, saida)

        print(f"\n{'='*60}")
        print(f" TOTAL: {len(todas_questoes)} questões extraídas!")
        print(f"{'='*60}\n")

    # Modo arquivo único
    else:
        pdf_path = sys.argv[1]
        gabarito_path = sys.argv[2] if len(sys.argv) > 2 else None

        questoes = processar_pdf(pdf_path, gabarito_path)

        if questoes:
            # Nome do arquivo de saída
            nome_base = Path(pdf_path).stem
            saida = f"data/questoes_{nome_base}.json"

            salvar_json(questoes, saida)

            print(f"\n{'='*60}")
            print(" PRÓXIMOS PASSOS:")
            print(f"{'='*60}")
            print(f"\n1. Revisar questões em: {saida}")
            print(f"2. Corrigir gabaritos se necessário")
            print(f"3. Importar: python importar_questoes.py {saida}")
            print("\n")
