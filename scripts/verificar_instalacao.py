#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador de Instalação
Verifica todos os arquivos criados e mostra status
"""

import os
import json
from pathlib import Path


def verificar_arquivos():
    """Verifica todos os arquivos criados."""

    print("="*80)
    print("VERIFICACAO DE ARQUIVOS - BANCO DE QUESTOES OAB")
    print("="*80 + "\n")

    base_path = r"C:\Users\NFC"

    # Arquivos de dados
    dados = {
        'questoes_oab_final.json': 'ARQUIVO PRINCIPAL - Use este',
        'questoes_oab_limpo.json': 'Versão limpa (backup)',
        'questoes_oab_completo.json': 'Versão completa (backup)',
        'questoes_oab_ultra.json': 'Versão ultra (alternativa)',
        'questoes_oab.csv': 'Formato CSV para Excel',
        'questoes_oab.txt': 'Formato texto legível',
    }

    # Scripts
    scripts = {
        'extrair_oab_final.py': 'Extração principal',
        'limpar_questoes.py': 'Pós-processamento',
        'corrigir_encoding.py': 'Correção de encoding',
        'exportar_csv.py': 'Exportador CSV/TXT',
        'testar_questoes.py': 'Testador interativo',
        'analisar_questoes.py': 'Gerador de estatísticas',
        'verificar_instalacao.py': 'Este script',
    }

    # Documentação
    docs = {
        'README_QUESTOES_OAB.md': 'Documentação completa',
    }

    # Verificar dados
    print("1. ARQUIVOS DE DADOS")
    print("-"*80)

    dados_ok = 0
    for arquivo, descricao in dados.items():
        caminho = os.path.join(base_path, arquivo)
        existe = os.path.exists(caminho)
        status = "OK" if existe else "FALTANDO"

        if existe:
            tamanho = os.path.getsize(caminho) / (1024 * 1024)
            print(f"   [{status}] {arquivo:<30} {descricao}")
            print(f"          Tamanho: {tamanho:.2f} MB")
            dados_ok += 1

            # Se for JSON, contar questões
            if arquivo.endswith('.json'):
                try:
                    with open(caminho, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"          Questoes: {len(data)}")
                except:
                    print(f"          Erro ao ler arquivo")
        else:
            print(f"   [{status}] {arquivo:<30} {descricao}")

        print()

    # Verificar scripts
    print("\n2. SCRIPTS PYTHON")
    print("-"*80)

    scripts_ok = 0
    for arquivo, descricao in scripts.items():
        caminho = os.path.join(base_path, arquivo)
        existe = os.path.exists(caminho)
        status = "OK" if existe else "FALTANDO"

        if existe:
            scripts_ok += 1

        print(f"   [{status}] {arquivo:<30} {descricao}")

    # Verificar documentação
    print("\n3. DOCUMENTACAO")
    print("-"*80)

    docs_ok = 0
    for arquivo, descricao in docs.items():
        caminho = os.path.join(base_path, arquivo)
        existe = os.path.exists(caminho)
        status = "OK" if existe else "FALTANDO"

        if existe:
            tamanho = os.path.getsize(caminho) / 1024
            print(f"   [{status}] {arquivo:<30} {descricao}")
            print(f"          Tamanho: {tamanho:.1f} KB")
            docs_ok += 1
        else:
            print(f"   [{status}] {arquivo:<30} {descricao}")

    # Resumo
    print("\n" + "="*80)
    print("RESUMO")
    print("="*80)
    print(f"Arquivos de dados: {dados_ok}/{len(dados)}")
    print(f"Scripts Python: {scripts_ok}/{len(scripts)}")
    print(f"Documentacao: {docs_ok}/{len(docs)}")

    total_ok = dados_ok + scripts_ok + docs_ok
    total = len(dados) + len(scripts) + len(docs)

    print(f"\nTotal: {total_ok}/{total} arquivos encontrados")

    if total_ok == total:
        print("\nStatus: COMPLETO - Todos os arquivos estao presentes!")
    else:
        print(f"\nStatus: INCOMPLETO - {total - total_ok} arquivo(s) faltando")

    # Recomendações
    print("\n" + "="*80)
    print("PROXIMOS PASSOS")
    print("="*80)
    print("\n1. Leia a documentacao completa:")
    print("   README_QUESTOES_OAB.md")
    print("\n2. Teste o arquivo principal:")
    print("   python testar_questoes.py")
    print("\n3. Exporte para outros formatos:")
    print("   python exportar_csv.py")
    print("\n4. Use em seu projeto:")
    print("   import json")
    print("   with open('questoes_oab_final.json', encoding='utf-8') as f:")
    print("       questoes = json.load(f)")
    print()


if __name__ == '__main__':
    verificar_arquivos()
