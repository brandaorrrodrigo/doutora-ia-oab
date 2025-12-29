"""
Importador em Massa de Questões OAB
Importa questões de arquivos JSON para o banco Railway
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import get_db_session
from database.models import QuestaoBanco, DificuldadeQuestao
from sqlalchemy.exc import IntegrityError


class ImportadorQuestoes:
    """Importa questões de JSON para o banco de dados"""

    MAPA_DIFICULDADE = {
        "facil": DificuldadeQuestao.FACIL,
        "fácil": DificuldadeQuestao.FACIL,
        "medio": DificuldadeQuestao.MEDIO,
        "médio": DificuldadeQuestao.MEDIO,
        "dificil": DificuldadeQuestao.DIFICIL,
        "difícil": DificuldadeQuestao.DIFICIL,
    }

    def __init__(self):
        self.questoes_importadas = 0
        self.questoes_duplicadas = 0
        self.questoes_erro = 0
        self.erros = []

    def validar_questao(self, questao: Dict) -> tuple[bool, str]:
        """Valida se a questão tem todos os campos obrigatórios"""

        campos_obrigatorios = [
            "codigo_questao",
            "disciplina",
            "enunciado",
            "alternativas",
            "alternativa_correta",
        ]

        for campo in campos_obrigatorios:
            if campo not in questao:
                return False, f"Campo obrigatório ausente: {campo}"

        # Valida alternativas
        alternativas = questao.get("alternativas", {})
        if not isinstance(alternativas, dict):
            return False, "Alternativas devem ser um dicionário"

        if len(alternativas) < 4:
            return False, f"Mínimo 4 alternativas necessário, encontrado: {len(alternativas)}"

        # Valida gabarito
        gabarito = questao.get("alternativa_correta")
        if gabarito not in alternativas:
            return False, f"Gabarito '{gabarito}' não está entre as alternativas"

        return True, ""

    def converter_dificuldade(self, dificuldade_str: str) -> DificuldadeQuestao:
        """Converte string de dificuldade para enum"""
        dificuldade_lower = dificuldade_str.lower() if dificuldade_str else "medio"
        return self.MAPA_DIFICULDADE.get(dificuldade_lower, DificuldadeQuestao.MEDIO)

    def importar_questao(self, questao: Dict, db_session) -> bool:
        """Importa uma única questão para o banco"""

        # Valida
        valida, erro = self.validar_questao(questao)
        if not valida:
            self.erros.append({
                "codigo": questao.get("codigo_questao", "DESCONHECIDO"),
                "erro": erro
            })
            self.questoes_erro += 1
            return False

        try:
            # Cria objeto QuestaoBanco
            nova_questao = QuestaoBanco(
                codigo_questao=questao["codigo_questao"],
                disciplina=questao["disciplina"],
                topico=questao.get("topico"),
                subtopico=questao.get("subtopico"),
                enunciado=questao["enunciado"],
                alternativas=questao["alternativas"],
                alternativa_correta=questao["alternativa_correta"],
                dificuldade=self.converter_dificuldade(questao.get("dificuldade")),
                ano_prova=questao.get("ano_prova"),
                numero_exame=questao.get("numero_exame"),
                explicacao_detalhada=questao.get("explicacao_detalhada"),
                fundamentacao_legal=questao.get("fundamentacao_legal", {}),
                tags=questao.get("tags", []),
                eh_trap=questao.get("eh_trap", False),
                tipo_trap=questao.get("tipo_trap"),
            )

            db_session.add(nova_questao)
            db_session.commit()

            self.questoes_importadas += 1
            return True

        except IntegrityError:
            db_session.rollback()
            self.questoes_duplicadas += 1
            return False

        except Exception as e:
            db_session.rollback()
            self.erros.append({
                "codigo": questao.get("codigo_questao", "DESCONHECIDO"),
                "erro": str(e)
            })
            self.questoes_erro += 1
            return False

    def importar_de_json(self, caminho_json: str, modo_verbose: bool = True):
        """Importa todas as questões de um arquivo JSON"""

        if not Path(caminho_json).exists():
            print(f"[!] Arquivo não encontrado: {caminho_json}")
            return

        print(f"\n[*] Carregando questões de: {caminho_json}")

        # Carrega JSON
        with open(caminho_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        questoes = dados.get("questoes", [])
        total = len(questoes)

        print(f"[+] Total de questões no arquivo: {total}\n")

        # Conecta ao banco
        db = next(get_db_session())

        # Importa cada questão
        for i, questao in enumerate(questoes, 1):
            codigo = questao.get("codigo_questao", f"Q{i}")

            if modo_verbose:
                print(f"[{i}/{total}] Importando {codigo}...", end=" ")

            sucesso = self.importar_questao(questao, db)

            if modo_verbose:
                if sucesso:
                    print("✓ OK")
                elif questao.get("codigo_questao") in [e["codigo"] for e in self.erros]:
                    print("✗ ERRO")
                else:
                    print("⊗ DUPLICADA")

        db.close()

        # Relatório final
        self.imprimir_relatorio(total)

    def imprimir_relatorio(self, total: int):
        """Imprime relatório de importação"""
        print("\n" + "="*60)
        print("RELATÓRIO DE IMPORTAÇÃO")
        print("="*60)
        print(f"\nTotal de questões no arquivo: {total}")
        print(f"✓ Importadas com sucesso:     {self.questoes_importadas}")
        print(f"⊗ Duplicadas (ignoradas):     {self.questoes_duplicadas}")
        print(f"✗ Erros:                      {self.questoes_erro}")

        if self.erros:
            print(f"\n--- DETALHES DOS ERROS ---")
            for erro in self.erros[:10]:  # Mostra primeiros 10 erros
                print(f"  {erro['codigo']}: {erro['erro']}")
            if len(self.erros) > 10:
                print(f"  ... e mais {len(self.erros) - 10} erros")

        print("\n" + "="*60 + "\n")


def importar_arquivo(caminho_json: str, verbose: bool = True):
    """Função auxiliar para importar um arquivo JSON"""
    importador = ImportadorQuestoes()
    importador.importar_de_json(caminho_json, verbose)
    return importador


def importar_diretorio(caminho_dir: str, padrao: str = "*.json"):
    """Importa todos os arquivos JSON de um diretório"""
    diretorio = Path(caminho_dir)

    if not diretorio.exists():
        print(f"[!] Diretório não encontrado: {caminho_dir}")
        return

    arquivos = list(diretorio.glob(padrao))

    if not arquivos:
        print(f"[!] Nenhum arquivo {padrao} encontrado em {caminho_dir}")
        return

    print(f"\n[*] Encontrados {len(arquivos)} arquivo(s) JSON")

    importador_total = ImportadorQuestoes()

    for arquivo in arquivos:
        print(f"\n{'='*60}")
        print(f"Processando: {arquivo.name}")
        print(f"{'='*60}")

        importador = importar_arquivo(str(arquivo), verbose=False)

        # Acumula estatísticas
        importador_total.questoes_importadas += importador.questoes_importadas
        importador_total.questoes_duplicadas += importador.questoes_duplicadas
        importador_total.questoes_erro += importador.questoes_erro
        importador_total.erros.extend(importador.erros)

    # Relatório consolidado
    print(f"\n{'='*60}")
    print("RELATÓRIO CONSOLIDADO - TODOS OS ARQUIVOS")
    print(f"{'='*60}")
    print(f"\nArquivos processados:         {len(arquivos)}")
    print(f"✓ Questões importadas:        {importador_total.questoes_importadas}")
    print(f"⊗ Duplicadas:                 {importador_total.questoes_duplicadas}")
    print(f"✗ Erros:                      {importador_total.questoes_erro}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUso:")
        print("  python importador_massa.py <arquivo.json>")
        print("  python importador_massa.py <diretorio> --dir")
        print("\nExemplos:")
        print("  python importador_massa.py questoes_oab_38.json")
        print("  python importador_massa.py ./questoes_exportadas --dir")
        sys.exit(1)

    caminho = sys.argv[1]

    # Modo diretório
    if "--dir" in sys.argv or Path(caminho).is_dir():
        importar_diretorio(caminho)
    else:
        # Modo arquivo único
        importar_arquivo(caminho)
