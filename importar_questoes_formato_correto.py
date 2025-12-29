#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Importa questões convertendo para o formato correto da tabela questoes_banco
"""

import json
import subprocess
import hashlib

print("="*70)
print("IMPORTACAO - FORMATO CORRETO")
print("="*70)

# Ler arquivo consolidado
print("\n[1/3] Lendo questoes consolidadas...")
with open('questoes_consolidadas_20251228_142350.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questoes = data['questoes']
print(f"Total: {len(questoes)} questoes")

# Converter para formato SQL
print("\n[2/3] Convertendo para formato da tabela...")

sql_file = 'import_correto.sql'
importadas = 0
puladas = 0

with open(sql_file, 'w', encoding='utf-8') as f:
    for i, q in enumerate(questoes, 1):
        try:
            # Extrair alternativas
            alts = q.get('alternativas', {})
            alt_a = alts.get('A', alts.get('a', ''))
            alt_b = alts.get('B', alts.get('b', ''))
            alt_c = alts.get('C', alts.get('c', ''))
            alt_d = alts.get('D', alts.get('d', ''))

            # Pular se não tiver todas as alternativas
            if not (alt_a and alt_b and alt_c and alt_d):
                puladas += 1
                continue

            # Escapar aspas simples
            def escape(text):
                if not text:
                    return ''
                return str(text).replace("'", "''").replace("\\", "\\\\")

            enunciado = escape(q['enunciado'])
            alt_a = escape(alt_a)
            alt_b = escape(alt_b)
            alt_c = escape(alt_c)
            alt_d = escape(alt_d)
            disciplina = escape(q['disciplina'])
            topico = escape(q['topico'])
            explicacao = escape(q.get('explicacao', ''))
            gabarito = q['gabarito'].upper()

            # Gerar código único baseado no hash
            codigo = f"CONS_{q['hash'][:12]}"

            sql = f"""
INSERT INTO questoes_banco (
    codigo_externo,
    disciplina,
    topico,
    enunciado,
    alternativa_a,
    alternativa_b,
    alternativa_c,
    alternativa_d,
    alternativa_correta,
    explicacao_nivel1_tecnico,
    dificuldade,
    ano,
    ativa
) VALUES (
    '{codigo}',
    '{disciplina}',
    '{topico}',
    '{enunciado}',
    '{alt_a}',
    '{alt_b}',
    '{alt_c}',
    '{alt_d}',
    '{gabarito}',
    '{explicacao}',
    '{q.get('dificuldade', 'media')}',
    {q.get('ano_prova') if q.get('ano_prova') else 'NULL'},
    true
) ON CONFLICT (codigo_externo) DO NOTHING;
"""
            f.write(sql)
            importadas += 1

            if i % 500 == 0:
                print(f"  Processadas: {i}/{len(questoes)} ({importadas} validas, {puladas} puladas)")

        except Exception as e:
            puladas += 1
            if puladas < 5:
                print(f"  Erro questao {i}: {str(e)[:100]}")

print(f"\nTotal processadas: {importadas}")
print(f"Total puladas: {puladas}")
print(f"Arquivo SQL: {sql_file}")

# Copiar e executar
print("\n[3/3] Executando no PostgreSQL...")

subprocess.run(['docker', 'cp', sql_file, 'juris_ia_postgres:/tmp/import_correto.sql'])

result = subprocess.run([
    'docker-compose', 'exec', '-T', 'postgres',
    'psql', '-U', 'juris_ia_user', '-d', 'juris_ia',
    '-f', '/tmp/import_correto.sql'
], capture_output=True, text=True, cwd='D:\\JURIS_IA_CORE_V1')

if result.returncode == 0:
    print("SUCESSO!")
else:
    print(f"ERRO: {result.stderr[:500]}")

# Verificar total
print("\nVerificando total...")
result = subprocess.run([
    'docker-compose', 'exec', '-T', 'postgres',
    'psql', '-U', 'juris_ia_user', '-d', 'juris_ia',
    '-c', 'SELECT COUNT(*) as total FROM questoes_banco;'
], capture_output=True, text=True, cwd='D:\\JURIS_IA_CORE_V1')

print(result.stdout)

print("="*70)
print("CONCLUIDO!")
print("="*70)
