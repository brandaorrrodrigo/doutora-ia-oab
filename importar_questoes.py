"""
Script de Importação de Questões OAB
Importa questões de arquivos JSON para o banco de dados
"""

import json
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

# Load environment variables
load_dotenv(".env")
load_dotenv(".env.local", override=True)

from database.connection import get_db_session
from database.models import QuestaoBanco

def validar_questao(questao_dict):
    """Valida se a questão tem todos os campos obrigatórios"""
    campos_obrigatorios = [
        'disciplina', 'topico', 'enunciado', 'alternativas',
        'gabarito', 'explicacao', 'fundamentacao'
    ]

    for campo in campos_obrigatorios:
        if campo not in questao_dict:
            return False, f"Campo obrigatório ausente: {campo}"

    # Validar alternativas
    if not isinstance(questao_dict['alternativas'], dict):
        return False, "Alternativas devem ser um dicionário"

    if questao_dict['gabarito'] not in questao_dict['alternativas']:
        return False, f"Gabarito '{questao_dict['gabarito']}' não está nas alternativas"

    return True, "OK"


def criar_questao_oab(questao_dict, index=1, arquivo_fonte=""):
    """Cria objeto QuestaoBanco a partir do dicionário"""
    import hashlib
    import re
    from database.models import DificuldadeQuestao

    # Extrair nome do arquivo fonte (sem caminho e extensão)
    fonte_limpa = re.sub(r'[^a-zA-Z0-9]', '', arquivo_fonte.split('/')[-1].split('\\')[-1].replace('.json', ''))

    # Gerar código ÚNICO para esta variação específica
    # Usa: fonte + numero_original + hash_curto
    numero_orig = questao_dict.get('numero_original', index)
    texto_unico = f"{fonte_limpa}{numero_orig}{questao_dict['enunciado'][:100]}"
    hash_unico = hashlib.md5(texto_unico.encode()).hexdigest()[:8]
    codigo = f"OAB_{fonte_limpa}_{numero_orig}_{hash_unico}"

    # Gerar hash de CONCEITO para agrupar variações
    # Usa: disciplina + gabarito (sem o enunciado!)
    # Questões com mesmo conceito terão mesmo hash_conceito
    topico_simples = re.sub(r'\s+', '', questao_dict.get('topico', 'geral')).lower()
    texto_conceito = f"{questao_dict['disciplina']}{topico_simples}{questao_dict['gabarito']}"
    hash_conceito = hashlib.md5(texto_conceito.encode()).hexdigest()

    # Mapear dificuldade
    dif_map = {
        'facil': DificuldadeQuestao.FACIL,
        'medio': DificuldadeQuestao.MEDIO,
        'dificil': DificuldadeQuestao.DIFICIL
    }

    return QuestaoBanco(
        codigo_questao=codigo,
        hash_conceito=hash_conceito,
        disciplina=questao_dict['disciplina'],
        topico=questao_dict.get('topico', 'Geral'),
        enunciado=questao_dict['enunciado'],
        alternativas=questao_dict['alternativas'],  # JSONB direto
        alternativa_correta=questao_dict['gabarito'],
        dificuldade=dif_map.get(questao_dict.get('dificuldade', 'medio'), DificuldadeQuestao.MEDIO),
        ano_prova=questao_dict.get('ano_prova'),
        numero_exame=questao_dict.get('exame', 'OAB'),
        explicacao_detalhada=questao_dict.get('explicacao', ''),
        fundamentacao_legal={'texto': questao_dict.get('fundamentacao', '')},
        tags=questao_dict.get('tags', []),
        ativa=True
    )


def importar_questoes_json(arquivo_json):
    """Importa questões de um arquivo JSON"""

    print("="*60)
    print(" IMPORTAÇÃO DE QUESTÕES OAB")
    print("="*60)
    print(f"\nArquivo: {arquivo_json}")

    try:
        # Ler arquivo JSON
        print("\n[1/4] Lendo arquivo JSON...")
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)

        questoes = data.get('questoes', [])
        print(f"[OK] {len(questoes)} questões encontradas no arquivo")

        # Validar questões
        print("\n[2/4] Validando questões...")
        questoes_validas = []
        erros = []

        for i, questao in enumerate(questoes, 1):
            valido, msg = validar_questao(questao)
            if valido:
                questoes_validas.append(questao)
            else:
                erros.append(f"Questão {i}: {msg}")

        print(f"[OK] {len(questoes_validas)} questões válidas")
        if erros:
            print(f"[AVISO] {len(erros)} questões com erros (serão ignoradas)")
            for erro in erros[:5]:  # Mostrar apenas os primeiros 5 erros
                print(f"  - {erro}")

        # Importar para o banco
        print("\n[3/4] Importando para o banco de dados...")
        importadas = 0
        duplicadas = 0
        erros_bd = 0

        with get_db_session() as session:
            for i, questao_dict in enumerate(questoes_validas, 1):
                try:
                    questao_obj = criar_questao_oab(questao_dict, index=i, arquivo_fonte=arquivo_json)
                    session.add(questao_obj)
                    session.flush()  # Flush para detectar duplicatas de codigo_questao
                    importadas += 1

                    if i % 10 == 0:
                        print(f"  Progresso: {i}/{len(questoes_validas)} questões...")

                except IntegrityError as e:
                    session.rollback()
                    duplicadas += 1
                    # Opcional: descomentar para debug
                    # print(f"  [DUPLICADA] Questão {i}: {questao_dict.get('numero_original', i)}")
                except Exception as e:
                    session.rollback()
                    erros_bd += 1
                    print(f"  [ERRO] Questão {i}: {str(e)[:80]}")

            # Commit final
            session.commit()

        print(f"[OK] Importação concluída!")

        # Relatório final
        print("\n[4/4] Relatório Final:")
        print("="*60)
        print(f"  Questões no arquivo:    {len(questoes)}")
        print(f"  Questões válidas:       {len(questoes_validas)}")
        print(f"  Importadas com sucesso: {importadas}")
        print(f"  Duplicadas (ignoradas): {duplicadas}")
        print(f"  Erros no banco:         {erros_bd}")
        print("="*60)

        if importadas > 0:
            print(f"\n✓ {importadas} novas questões adicionadas ao banco!")

        return importadas

    except FileNotFoundError:
        print(f"\n[ERRO] Arquivo não encontrado: {arquivo_json}")
        return 0
    except json.JSONDecodeError as e:
        print(f"\n[ERRO] Arquivo JSON inválido: {e}")
        return 0
    except Exception as e:
        print(f"\n[ERRO] Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return 0


def verificar_banco():
    """Verifica quantas questões existem no banco"""
    try:
        with get_db_session() as session:
            from sqlalchemy import func
            total = session.query(func.count(QuestaoBanco.id)).scalar()
            return total
    except:
        return 0


if __name__ == "__main__":
    print("\n")

    # Verificar estado atual do banco
    total_antes = verificar_banco()
    print(f"Questões no banco antes da importação: {total_antes}\n")

    # Verificar argumento
    if len(sys.argv) > 1:
        arquivo = sys.argv[1]
    else:
        arquivo = "data/questoes_oab_100.json"
        print(f"Usando arquivo padrão: {arquivo}\n")

    # Importar
    importadas = importar_questoes_json(arquivo)

    # Verificar estado final
    if importadas > 0:
        total_depois = verificar_banco()
        print(f"\nQuestões no banco após importação: {total_depois}")
        print(f"Aumento: +{total_depois - total_antes}\n")

    print("\n" + "="*60)
    print(" IMPORTAÇÃO FINALIZADA")
    print("="*60)
    print("\nPara adicionar mais questões:")
    print("  1. Crie um arquivo JSON no formato:")
    print("     { \"questoes\": [ ... ] }")
    print("  2. Execute: python importar_questoes.py seu_arquivo.json")
    print("\n")
