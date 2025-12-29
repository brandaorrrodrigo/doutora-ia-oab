#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Importa questões consolidadas via Docker PostgreSQL
"""

import json
import subprocess
import sys

print("="*70)
print("IMPORTACAO VIA DOCKER - QUESTOES OAB")
print("="*70)

# 1. Verificar se Docker está rodando
print("\n[1/4] Verificando Docker...")
try:
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if result.returncode != 0:
        print("ERRO: Docker nao esta rodando!")
        print("Por favor, inicie o Docker Desktop e execute este script novamente.")
        sys.exit(1)
    print("OK: Docker esta rodando")
except FileNotFoundError:
    print("ERRO: Docker nao encontrado!")
    print("Por favor, instale o Docker Desktop.")
    sys.exit(1)

# 2. Verificar container PostgreSQL
print("\n[2/4] Verificando container PostgreSQL...")
result = subprocess.run(
    ['docker-compose', 'ps', 'postgres'],
    capture_output=True,
    text=True,
    cwd='D:\\JURIS_IA_CORE_V1'
)

if 'Up' not in result.stdout:
    print("Container PostgreSQL nao esta rodando.")
    print("Iniciando containers...")
    subprocess.run(['docker-compose', 'up', '-d', 'postgres'], cwd='D:\\JURIS_IA_CORE_V1')
    print("Aguardando PostgreSQL iniciar...")
    import time
    time.sleep(10)
else:
    print("OK: PostgreSQL esta rodando")

# 3. Ler arquivo consolidado
print("\n[3/4] Lendo arquivo consolidado...")
arquivo = 'questoes_consolidadas_20251228_142350.json'

with open(arquivo, 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total de questoes a importar: {len(questoes)}")

# 4. Importar via Docker exec
print("\n[4/4] Importando questoes...")

# Criar arquivo SQL temporário
sql_file = 'temp_import.sql'
with open(sql_file, 'w', encoding='utf-8') as f:
    for i, q in enumerate(questoes, 1):
        # Escapar aspas simples
        enunciado = q['enunciado'].replace("'", "''")
        explicacao = q.get('explicacao', '').replace("'", "''")
        fundamentacao = q.get('fundamentacao', '').replace("'", "''")
        disciplina = q['disciplina'].replace("'", "''")
        topico = q['topico'].replace("'", "''")

        # Converter alternativas para JSON string
        alternativas_json = json.dumps(q['alternativas']).replace("'", "''")
        tags_json = json.dumps(q.get('tags', [])).replace("'", "''")

        sql = f"""
INSERT INTO questoes_banco (
    disciplina, topico, enunciado, alternativas,
    alternativa_correta, explicacao, fundamentacao_legal,
    dificuldade, ano_prova, tags, hash_conceito, created_at
) VALUES (
    '{disciplina}',
    '{topico}',
    '{enunciado}',
    '{alternativas_json}'::jsonb,
    '{q['gabarito']}',
    '{explicacao}',
    '{fundamentacao}',
    '{q.get('dificuldade', 'medio')}',
    {q.get('ano_prova') if q.get('ano_prova') else 'NULL'},
    '{tags_json}'::jsonb,
    '{q['hash']}',
    NOW()
) ON CONFLICT (hash_conceito) DO NOTHING;
"""
        f.write(sql)

        if i % 100 == 0:
            print(f"  Preparado: {i}/{len(questoes)}")

print(f"\nArquivo SQL criado: {sql_file}")
print("Executando no PostgreSQL via Docker...")

# Copiar arquivo para container
subprocess.run([
    'docker', 'cp',
    sql_file,
    'juris_ia_postgres:/tmp/import.sql'
])

# Executar SQL
result = subprocess.run([
    'docker-compose', 'exec', '-T', 'postgres',
    'psql', '-U', 'juris_ia_user', '-d', 'juris_ia',
    '-f', '/tmp/import.sql'
], capture_output=True, text=True, cwd='D:\\JURIS_IA_CORE_V1')

if result.returncode == 0:
    print("\nSUCESSO: Questoes importadas!")
else:
    print(f"\nERRO ao importar:")
    print(result.stderr)

# Verificar total
print("\nVerificando total no banco...")
result = subprocess.run([
    'docker-compose', 'exec', '-T', 'postgres',
    'psql', '-U', 'juris_ia_user', '-d', 'juris_ia',
    '-c', 'SELECT COUNT(*) FROM questoes_banco;'
], capture_output=True, text=True, cwd='D:\\JURIS_IA_CORE_V1')

print(result.stdout)

print("\n" + "="*70)
print("PROCESSO CONCLUIDO!")
print("="*70)
