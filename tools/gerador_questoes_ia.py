"""
Gerador Automatico de Questoes OAB usando IA
Le conteudo juridico e gera questoes no estilo OAB
"""
import json
import sys
from pathlib import Path
from typing import List, Dict
import PyPDF2

# Template de prompt para gerar questoes
PROMPT_TEMPLATE = """Você é um especialista em elaboração de questões OAB. Com base no texto jurídico abaixo, crie {num_questoes} questão(ões) objetiva(s) no estilo OAB.

TEXTO JURÍDICO:
{texto}

Para cada questão, retorne um objeto JSON com:
- codigo_questao: código único (ex: "OAB_GEN_001")
- disciplina: área do direito
- topico: tópico específico
- enunciado: texto da questão
- alternativas: objeto com A, B, C, D
- alternativa_correta: letra da alternativa correta
- explicacao_detalhada: explicação completa
- fundamentacao_legal: artigos de lei citados
- dificuldade: "facil", "medio" ou "dificil"
- tags: array de tags relevantes

IMPORTANTE:
- As alternativas devem ser plausíveis
- A explicação deve ser didática
- Cite os artigos de lei corretos
- Varie a dificuldade

Retorne apenas um JSON válido com array "questoes".
"""


class GeradorQuestoesIA:
    """Gera questões usando IA a partir de textos jurídicos"""

    def __init__(self, api_key: str = None):
        """
        Inicializa gerador
        api_key: chave da API OpenAI (ou None para modo local)
        """
        self.api_key = api_key
        self.questoes_geradas = []

    def ler_pdf(self, caminho_pdf: str, max_paginas: int = 10) -> str:
        """Lê conteúdo de um PDF"""
        texto = ""
        try:
            with open(caminho_pdf, 'rb') as arquivo:
                leitor = PyPDF2.PdfReader(arquivo)
                total_pag = min(len(leitor.pages), max_paginas)

                for i in range(total_pag):
                    texto += leitor.pages[i].extract_text()

        except Exception as e:
            print(f"Erro ao ler PDF: {e}")

        return texto

    def gerar_questoes_openai(self, texto: str, num_questoes: int = 5) -> List[Dict]:
        """Gera questões usando OpenAI GPT"""
        try:
            import openai

            if not self.api_key:
                print("[!] API key do OpenAI não fornecida")
                return []

            openai.api_key = self.api_key

            prompt = PROMPT_TEMPLATE.format(
                texto=texto[:4000],  # Limita texto
                num_questoes=num_questoes
            )

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Você é um especialista em elaboração de questões OAB."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )

            resposta = response.choices[0].message.content

            # Parse JSON
            dados = json.loads(resposta)
            questoes = dados.get("questoes", [])

            return questoes

        except Exception as e:
            print(f"Erro ao gerar questões: {e}")
            return []

    def gerar_questoes_local(self, texto: str, num_questoes: int = 5) -> List[Dict]:
        """
        Gera questões usando modelo local (Ollama)
        Requer Ollama instalado com modelo jurídico
        """
        try:
            import requests

            prompt = PROMPT_TEMPLATE.format(
                texto=texto[:4000],
                num_questoes=num_questoes
            )

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral",  # ou outro modelo
                    "prompt": prompt,
                    "stream": False,
                }
            )

            if response.status_code == 200:
                resposta = response.json().get("response", "")
                dados = json.loads(resposta)
                return dados.get("questoes", [])

        except Exception as e:
            print(f"Erro ao gerar com Ollama: {e}")

        return []

    def salvar_questoes(self, arquivo_saida: str):
        """Salva questões geradas em JSON"""
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump({
                "questoes": self.questoes_geradas,
                "total": len(self.questoes_geradas)
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[+] {len(self.questoes_geradas)} questões salvas em: {arquivo_saida}")


def gerar_de_pdf(caminho_pdf: str, num_questoes: int = 10, output: str = "questoes_geradas.json"):
    """Gera questões a partir de um PDF"""

    print(f"\n[*] Gerando {num_questoes} questões de: {caminho_pdf}")

    gerador = GeradorQuestoesIA()

    # Lê PDF
    texto = gerador.ler_pdf(caminho_pdf, max_paginas=20)

    if not texto:
        print("[!] Não foi possível extrair texto")
        return

    print(f"[+] Texto extraído: {len(texto)} caracteres")

    # Gera questões (tenta Ollama local primeiro)
    print("[*] Gerando questões com IA...")
    questoes = gerador.gerar_questoes_local(texto, num_questoes)

    if not questoes:
        print("[!] Falha ao gerar questões")
        print("[!] Certifique-se que Ollama está rodando: ollama serve")
        return

    gerador.questoes_geradas = questoes
    gerador.salvar_questoes(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso: python gerador_questoes_ia.py <pdf> [num_questoes] [arquivo_saida]")
        print("\nExemplo:")
        print("  python gerador_questoes_ia.py livro_direito_civil.pdf 20 questoes_civil.json")
        sys.exit(1)

    pdf_path = sys.argv[1]
    num_q = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    output = sys.argv[3] if len(sys.argv) > 3 else "questoes_geradas.json"

    gerar_de_pdf(pdf_path, num_q, output)
