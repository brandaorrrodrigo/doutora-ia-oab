"""
Sistema de Extração de Questões OAB de PDFs
Extrai questões de provas OAB em PDF e converte para formato estruturado
"""
import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import PyPDF2

class ExtratorQuestoesOAB:
    """Extrai questões de PDFs de provas OAB"""

    # Padrões regex para identificar questões
    PADRAO_NUMERO_QUESTAO = r"(?:QUESTÃO|Questão|QUESTAO)\s+(\d+)"
    PADRAO_ALTERNATIVA = r"^([A-E])\)\s*(.+?)(?=\n[A-E]\)|$)"
    PADRAO_GABARITO = r"(?:GABARITO|Gabarito|Resposta):\s*([A-E])"

    # Disciplinas OAB 1ª Fase
    DISCIPLINAS = {
        "constitucional": "Direito Constitucional",
        "administrativo": "Direito Administrativo",
        "civil": "Direito Civil",
        "penal": "Direito Penal",
        "processual civil": "Direito Processual Civil",
        "processual penal": "Direito Processual Penal",
        "trabalho": "Direito do Trabalho",
        "tributario": "Direito Tributário",
        "empresarial": "Direito Empresarial",
        "etica": "Ética Profissional",
    }

    def __init__(self, caminho_pdf: str):
        self.caminho_pdf = Path(caminho_pdf)
        self.questoes = []

    def extrair_texto_pdf(self) -> str:
        """Extrai todo o texto do PDF"""
        texto_completo = ""

        try:
            with open(self.caminho_pdf, 'rb') as arquivo:
                leitor = PyPDF2.PdfReader(arquivo)
                for pagina in leitor.pages:
                    texto_completo += pagina.extract_text() + "\n"
        except Exception as e:
            print(f"Erro ao ler PDF: {e}")
            return ""

        return texto_completo

    def identificar_disciplina(self, texto_questao: str) -> str:
        """Identifica a disciplina baseada em palavras-chave"""
        texto_lower = texto_questao.lower()

        # Mapeamento de palavras-chave para disciplinas
        palavras_chave = {
            "Direito Constitucional": ["constituição", "constitucional", "direitos fundamentais", "emenda constitucional"],
            "Direito Civil": ["código civil", "contrato", "propriedade", "posse", "obrigações"],
            "Direito Penal": ["código penal", "crime", "pena", "dolo", "culpa"],
            "Direito Processual Civil": ["cpc", "petição inicial", "sentença", "recurso", "apelação"],
            "Direito do Trabalho": ["clt", "trabalhador", "empregado", "rescisão"],
            "Direito Tributário": ["tributo", "imposto", "taxa", "contribuição"],
            "Ética Profissional": ["ética", "advogado", "oab", "estatuto"],
        }

        for disciplina, palavras in palavras_chave.items():
            if any(palavra in texto_lower for palavra in palavras):
                return disciplina

        return "Não identificada"

    def extrair_questoes_simples(self, texto: str) -> List[Dict]:
        """
        Extração simples - separa por numeração de questões
        Retorna lista de questões brutas para revisão manual
        """
        questoes_brutas = []

        # Divide o texto em blocos por número de questão
        partes = re.split(self.PADRAO_NUMERO_QUESTAO, texto)

        for i in range(1, len(partes), 2):
            if i + 1 < len(partes):
                numero = partes[i]
                conteudo = partes[i + 1]

                questoes_brutas.append({
                    "numero": int(numero),
                    "texto_completo": conteudo.strip(),
                    "disciplina": self.identificar_disciplina(conteudo),
                    "extraido": True,
                })

        return questoes_brutas

    def parsear_questao_estruturada(self, texto_questao: str, numero: int) -> Optional[Dict]:
        """
        Tenta parsear uma questão em formato estruturado
        """
        # Separa enunciado de alternativas
        linhas = texto_questao.split('\n')

        enunciado_linhas = []
        alternativas = {}
        gabarito = None

        modo_alternativa = False
        alternativa_atual = None
        texto_alternativa = ""

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Verifica se é uma alternativa (A) a E))
            match_alt = re.match(r'^([A-E])\)\s*(.+)', linha)
            if match_alt:
                # Salva alternativa anterior se existir
                if alternativa_atual:
                    alternativas[alternativa_atual] = texto_alternativa.strip()

                alternativa_atual = match_alt.group(1)
                texto_alternativa = match_alt.group(2)
                modo_alternativa = True
            elif modo_alternativa and alternativa_atual:
                # Continua texto da alternativa atual
                texto_alternativa += " " + linha
            else:
                # É parte do enunciado
                enunciado_linhas.append(linha)

        # Salva última alternativa
        if alternativa_atual:
            alternativas[alternativa_atual] = texto_alternativa.strip()

        # Se não encontrou 4 alternativas, retorna None
        if len(alternativas) < 4:
            return None

        enunciado = " ".join(enunciado_linhas).strip()

        return {
            "numero": numero,
            "enunciado": enunciado,
            "alternativas": alternativas,
            "gabarito": gabarito,  # Será preenchido depois
            "disciplina": self.identificar_disciplina(enunciado),
        }

    def gerar_template_json(self, questoes_brutas: List[Dict], arquivo_saida: str):
        """Gera template JSON para revisão manual"""

        questoes_template = []

        for q in questoes_brutas:
            # Tenta parsear
            questao_parseada = self.parsear_questao_estruturada(
                q["texto_completo"],
                q["numero"]
            )

            if questao_parseada:
                questoes_template.append({
                    "codigo_questao": f"OAB_IMPORT_{q['numero']:03d}",
                    "disciplina": questao_parseada["disciplina"],
                    "topico": "REVISAR",
                    "subtopico": "REVISAR",
                    "enunciado": questao_parseada["enunciado"],
                    "alternativas": questao_parseada["alternativas"],
                    "alternativa_correta": "REVISAR",
                    "dificuldade": "medio",
                    "ano_prova": 2024,
                    "numero_exame": "REVISAR",
                    "explicacao_detalhada": "REVISAR - Adicionar explicação",
                    "fundamentacao_legal": {},
                    "tags": [],
                    "eh_trap": False,
                })
            else:
                # Questão não parseada - adiciona como template bruto
                questoes_template.append({
                    "codigo_questao": f"OAB_IMPORT_{q['numero']:03d}",
                    "disciplina": q["disciplina"],
                    "topico": "REVISAR",
                    "TEXTO_COMPLETO_PARA_REVISAO": q["texto_completo"],
                    "STATUS": "NAO_PARSEADO - REVISAR MANUALMENTE"
                })

        # Salva JSON
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump({
                "questoes": questoes_template,
                "total": len(questoes_template),
                "arquivo_origem": str(self.caminho_pdf),
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[+] Template JSON gerado: {arquivo_saida}")
        print(f"[+] Total de questoes: {len(questoes_template)}")
        print(f"[!] IMPORTANTE: Revise o JSON antes de importar!")

        return arquivo_saida


def extrair_de_pdf(caminho_pdf: str, arquivo_saida: str = None):
    """Função auxiliar para extrair questões de um PDF"""

    if not arquivo_saida:
        nome_base = Path(caminho_pdf).stem
        arquivo_saida = f"questoes_{nome_base}.json"

    print(f"\n[*] Extraindo questoes de: {caminho_pdf}")

    extrator = ExtratorQuestoesOAB(caminho_pdf)
    texto = extrator.extrair_texto_pdf()

    if not texto:
        print("[!] Nao foi possivel extrair texto do PDF")
        return None

    print(f"[+] Texto extraido: {len(texto)} caracteres")

    questoes_brutas = extrator.extrair_questoes_simples(texto)
    print(f"[+] Questoes identificadas: {len(questoes_brutas)}")

    arquivo_json = extrator.gerar_template_json(questoes_brutas, arquivo_saida)

    return arquivo_json


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("\nUso: python extrator_questoes_pdf.py <caminho_pdf> [arquivo_saida.json]")
        print("\nExemplo:")
        print("  python extrator_questoes_pdf.py prova_oab_38.pdf questoes_oab_38.json")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    extrair_de_pdf(pdf_path, output)
