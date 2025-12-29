#!/usr/bin/env python3
import re
import json

print(f"\n{'='*70}")
print("📝 EXTRAINDO GABARITOS DO RAIOX")
print(f"{'='*70}\n")

with open('/tmp/raiox/raiox_mestres_questoes.md', 'r', encoding='utf-8') as f:
    texto = f.read()

# Extrair seções de gabarito
pattern_secao = r'## Seção (\d+)\s+((?:- Questão \d+: \*\*[A-E]\*\*\s*)+)'
secoes = re.findall(pattern_secao, texto)

# Mapear questão -> gabarito
gabaritos = {}
questao_id = 1

for num_secao, conteudo_secao in secoes:
    # Extrair questões da seção
    questoes_secao = re.findall(r'- Questão (\d+): \*\*([A-E])\*\*', conteudo_secao)

    for num_q, gabarito in questoes_secao:
        gabaritos[questao_id] = gabarito
        questao_id += 1

print(f"✅ Gabaritos extraídos: {len(gabaritos)}")

# Salvar mapeamento
with open('/tmp/gabaritos_raiox.json', 'w', encoding='utf-8') as f:
    json.dump(gabaritos, f, indent=2)

print(f"💾 Salvo em: /tmp/gabaritos_raiox.json")

# Mostrar amostra
print(f"\n📋 Amostra dos primeiros 10:")
for i in range(1, 11):
    if i in gabaritos:
        print(f"   Q{i:03d}: {gabaritos[i]}")

print(f"\n{'='*70}\n")
