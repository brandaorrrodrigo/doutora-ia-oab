#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para consolidar todas as questes de todos os arquivos JSON
e importar para o banco de dados, removendo duplicatas.
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

print("="*70)
print("CONSOLIDAO E IMPORTAO DE QUESTES OAB")
print("="*70)
print()

# Configurao do banco de dados
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/juris_ia')

# Criar engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def gerar_hash(enunciado):
    """Gera hash nico baseado no enunciado"""
    texto_limpo = enunciado.lower().strip()
    return hashlib.md5(texto_limpo.encode('utf-8')).hexdigest()

def coletar_questoes():
    """Coleta todas as questes de todos os arquivos JSON"""
    print("[1/5] Coletando questoes de todos os arquivos JSON...")

    questoes_coletadas = []
    arquivos_processados = 0

    for root, dirs, files in os.walk('.'):
        # Pular venv e node_modules
        dirs[:] = [d for d in dirs if d not in ['venv', 'node_modules', '.git', '__pycache__']]

        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                        # Extrair questes do JSON
                        if isinstance(data, dict):
                            questoes = data.get('questoes', data.get('questions', []))
                        else:
                            questoes = data

                        if isinstance(questoes, list) and len(questoes) > 0:
                            # Verificar se  uma lista de questes vlida
                            if isinstance(questoes[0], dict):
                                # Verificar se tem campos de questo
                                primeiro = questoes[0]
                                if 'enunciado' in primeiro or 'texto' in primeiro or 'pergunta' in primeiro:
                                    questoes_coletadas.extend(questoes)
                                    arquivos_processados += 1
                                    print(f"    {filepath}: {len(questoes)} questes")
                except Exception as e:
                    pass

    print(f"\nTotal coletado: {len(questoes_coletadas)} questes de {arquivos_processados} arquivos")
    return questoes_coletadas

def remover_duplicatas(questoes):
    """Remove duplicatas baseado em hash do enunciado"""
    print("\n2[2/5] Removendo duplicatas...")

    questoes_unicas = {}
    duplicatas = 0

    for q in questoes:
        # Extrair enunciado (pode ter nomes diferentes)
        enunciado = q.get('enunciado') or q.get('texto') or q.get('pergunta') or q.get('question', '')

        if not enunciado or len(enunciado.strip()) < 20:
            continue

        hash_questao = gerar_hash(enunciado)

        if hash_questao not in questoes_unicas:
            # Normalizar campos
            questao_normalizada = {
                'disciplina': q.get('disciplina') or q.get('materia') or 'No especificada',
                'topico': q.get('topico') or q.get('assunto') or 'Geral',
                'enunciado': enunciado,
                'alternativas': q.get('alternativas') or q.get('opcoes') or {},
                'gabarito': q.get('gabarito') or q.get('resposta_correta') or q.get('alternativa_correta', ''),
                'explicacao': q.get('explicacao') or q.get('comentario') or '',
                'fundamentacao': q.get('fundamentacao') or q.get('base_legal') or '',
                'dificuldade': q.get('dificuldade', 'medio'),
                'ano_prova': q.get('ano_prova') or q.get('ano'),
                'tags': q.get('tags', []),
                'hash': hash_questao
            }

            # Validar campos obrigatrios
            if (questao_normalizada['enunciado'] and
                questao_normalizada['alternativas'] and
                questao_normalizada['gabarito']):
                questoes_unicas[hash_questao] = questao_normalizada
        else:
            duplicatas += 1

    print(f"    Questes nicas: {len(questoes_unicas)}")
    print(f"   Duplicatas removidas: {duplicatas}")

    return list(questoes_unicas.values())

def salvar_consolidado(questoes):
    """Salva arquivo consolidado"""
    print("\n3[3/5] Salvando arquivo consolidado...")

    arquivo_saida = f'questoes_consolidadas_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'total_questoes': len(questoes),
                'data_consolidacao': datetime.now().isoformat(),
                'versao': '1.0'
            },
            'questoes': questoes
        }, f, ensure_ascii=False, indent=2)

    print(f"   Arquivo salvo: {arquivo_saida}")
    return arquivo_saida

def importar_para_banco(questoes):
    """Importa questes para o banco de dados"""
    print("\n4[4/5] Importando para o banco de dados...")

    session = Session()
    importadas = 0
    ja_existentes = 0
    erros = 0

    try:
        for i, q in enumerate(questoes, 1):
            try:
                # Verificar se j existe
                result = session.execute(
                    text("SELECT id FROM questoes_banco WHERE hash_conceito = :hash"),
                    {'hash': q['hash']}
                ).fetchone()

                if result:
                    ja_existentes += 1
                    continue

                # Inserir questo
                session.execute(text("""
                    INSERT INTO questoes_banco (
                        disciplina, topico, enunciado, alternativas,
                        alternativa_correta, explicacao, fundamentacao_legal,
                        dificuldade, ano_prova, tags, hash_conceito, created_at
                    ) VALUES (
                        :disciplina, :topico, :enunciado, :alternativas::jsonb,
                        :gabarito, :explicacao, :fundamentacao,
                        :dificuldade, :ano_prova, :tags::jsonb, :hash, NOW()
                    )
                """), {
                    'disciplina': q['disciplina'],
                    'topico': q['topico'],
                    'enunciado': q['enunciado'],
                    'alternativas': json.dumps(q['alternativas']),
                    'gabarito': q['gabarito'],
                    'explicacao': q['explicacao'],
                    'fundamentacao': q['fundamentacao'],
                    'dificuldade': q['dificuldade'],
                    'ano_prova': q.get('ano_prova'),
                    'tags': json.dumps(q.get('tags', [])),
                    'hash': q['hash']
                })

                importadas += 1

                if i % 100 == 0:
                    session.commit()
                    print(f"   Progresso: {i}/{len(questoes)} ({importadas} importadas, {ja_existentes} j existiam)")

            except Exception as e:
                erros += 1
                if erros < 5:  # Mostrar apenas os primeiros erros
                    print(f"     Erro ao importar questo {i}: {str(e)[:100]}")

        session.commit()

        print(f"\n Importao concluda!")
        print(f"   Importadas: {importadas}")
        print(f"    J existiam: {ja_existentes}")
        print(f"   Erros: {erros}")

    except Exception as e:
        session.rollback()
        print(f"\n Erro na importao: {e}")
        raise
    finally:
        session.close()

    return importadas, ja_existentes, erros

def verificar_total_banco():
    """Verifica total de questes no banco"""
    print("\n5[5/5] Verificando total no banco de dados...")

    session = Session()
    try:
        result = session.execute(text("SELECT COUNT(*) FROM questoes_banco")).fetchone()
        total = result[0]
        print(f"    Total de questes no banco: {total}")
        return total
    finally:
        session.close()

def main():
    try:
        # 1. Coletar questes
        questoes_coletadas = coletar_questoes()

        if not questoes_coletadas:
            print("\n Nenhuma questo encontrada!")
            return

        # 2. Remover duplicatas
        questoes_unicas = remover_duplicatas(questoes_coletadas)

        # 3. Salvar consolidado
        arquivo_consolidado = salvar_consolidado(questoes_unicas)

        # 4. Importar para banco
        importadas, ja_existentes, erros = importar_para_banco(questoes_unicas)

        # 5. Verificar total
        total_final = verificar_total_banco()

        print("\n" + "="*70)
        print(" PROCESSO CONCLUDO COM SUCESSO!")
        print("="*70)
        print(f" Questes coletadas: {len(questoes_coletadas)}")
        print(f" Questes nicas: {len(questoes_unicas)}")
        print(f"Arquivo consolidado: {arquivo_consolidado}")
        print(f"Importadas agora: {importadas}")
        print(f"  J existiam: {ja_existentes}")
        print(f" Total no banco: {total_final}")
        print("="*70)

    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
