#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Importa questões do arquivo consolidado para o banco"""

import json
import sys
import os
from dotenv import load_dotenv

# Carregar .env.import
load_dotenv('.env.import')

from database.connection import get_db_session
from database.models import QuestaoBanco
from sqlalchemy import func

print("="*70)
print("IMPORTACAO DE QUESTOES CONSOLIDADAS")
print("="*70)

# Ler arquivo consolidado
arquivo = 'questoes_consolidadas_20251228_142350.json'
print(f"\nLendo arquivo: {arquivo}")

with open(arquivo, 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total de questoes no arquivo: {len(questoes)}")

# Conectar ao banco
print("\nConectando ao banco de dados...")
with get_db_session() as db:
    # Verificar total atual
    total_antes = db.query(func.count(QuestaoBanco.id)).scalar()
    print(f"Questoes no banco ANTES: {total_antes}")

    # Importar
    print("\nImportando questoes...")
    importadas = 0
    ja_existentes = 0
    erros = 0

    for i, q in enumerate(questoes, 1):
        try:
            # Verificar se ja existe (por hash)
            existe = db.query(QuestaoBanco).filter(
                QuestaoBanco.hash_conceito == q['hash']
            ).first()

            if existe:
                ja_existentes += 1
                continue

            # Criar nova questao
            nova = QuestaoBanco(
                disciplina=q['disciplina'],
                topico=q['topico'],
                enunciado=q['enunciado'],
                alternativas=q['alternativas'],
                alternativa_correta=q['gabarito'],
                explicacao=q.get('explicacao', ''),
                fundamentacao_legal=q.get('fundamentacao', ''),
                dificuldade=q.get('dificuldade', 'medio'),
                ano_prova=q.get('ano_prova'),
                tags=q.get('tags', []),
                hash_conceito=q['hash']
            )

            db.add(nova)
            importadas += 1

            # Commit a cada 100
            if i % 100 == 0:
                db.commit()
                print(f"  Progresso: {i}/{len(questoes)} ({importadas} novas, {ja_existentes} existentes)")

        except Exception as e:
            erros += 1
            if erros < 5:
                print(f"  Erro questao {i}: {str(e)[:100]}")

    # Commit final
    db.commit()

    # Verificar total final
    total_depois = db.query(func.count(QuestaoBanco.id)).scalar()

    print("\n" + "="*70)
    print("RESULTADO")
    print("="*70)
    print(f"Importadas: {importadas}")
    print(f"Ja existiam: {ja_existentes}")
    print(f"Erros: {erros}")
    print(f"Total no banco ANTES: {total_antes}")
    print(f"Total no banco DEPOIS: {total_depois}")
    print(f"Diferenca: +{total_depois - total_antes}")
    print("="*70)
