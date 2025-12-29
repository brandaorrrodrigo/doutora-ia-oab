#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from collections import defaultdict
import re

def contar_arquivos_por_pasta(base_path):
    """Conta arquivos PDF em cada subpasta"""
    resultado = {}

    # Pastas organizadas
    pastas = [
        "01-direito-civil",
        "02-direito-processual-civil",
        "03-direito-penal",
        "04-direito-imobiliario",
        "05-direito-previdenciario",
        "06-direito-trabalho",
        "07-direito-empresarial",
        "08-direito-consumidor",
        "09-direito-notarial-registral",
        "10-jurisprudencia-sumulas",
        "11-outros",
        "12-direito-ambiental",
        "13-direito-administrativo",
        "14-direito-tributario",
        "15-direito-constitucional"
    ]

    for pasta in pastas:
        caminho = os.path.join(base_path, pasta)
        if os.path.exists(caminho):
            pdfs = [f for f in os.listdir(caminho) if f.lower().endswith('.pdf')]
            resultado[pasta] = len(pdfs)
        else:
            resultado[pasta] = 0

    return resultado

def analisar_novos_downloads(path_novos):
    """Analisa e classifica arquivos da pasta novos-downloads"""
    classificacao = defaultdict(list)

    if not os.path.exists(path_novos):
        return classificacao

    for arquivo in os.listdir(path_novos):
        if not arquivo.lower().endswith('.pdf'):
            continue

        nome_lower = arquivo.lower()

        # Classificação por palavras-chave
        if any(x in nome_lower for x in ['civil', 'família', 'familia', 'alimentos', 'sucessoes', 'sucessão', 'adoção', 'adocao', 'guarda']):
            classificacao['Direito Civil'].append(arquivo)
        elif any(x in nome_lower for x in ['processual-civil', 'processo-civil', 'cpc', 'agravo', 'execução', 'execucao']):
            classificacao['Direito Processual Civil'].append(arquivo)
        elif any(x in nome_lower for x in ['penal', 'criminal', 'codigo-penal', 'crimes']):
            classificacao['Direito Penal'].append(arquivo)
        elif any(x in nome_lower for x in ['imobiliário', 'imobiliario', 'imoveis', 'locação', 'locacao', 'inquilinato', 'despejo', 'condomínio', 'condominio']):
            classificacao['Direito Imobiliário'].append(arquivo)
        elif any(x in nome_lower for x in ['previdenciário', 'previdenciario', 'previdência', 'previdencia', 'inss']):
            classificacao['Direito Previdenciário'].append(arquivo)
        elif any(x in nome_lower for x in ['trabalho', 'trabalhista', 'clt', 'reforma-trabalhista', 'tst']):
            classificacao['Direito do Trabalho'].append(arquivo)
        elif any(x in nome_lower for x in ['empresarial', 'societário', 'societario', 'empresa', 'mei', 'startup', 'títulos', 'titulos', 'crédito', 'credito']):
            classificacao['Direito Empresarial'].append(arquivo)
        elif any(x in nome_lower for x in ['consumidor', 'consumerista']):
            classificacao['Direito do Consumidor'].append(arquivo)
        elif any(x in nome_lower for x in ['notarial', 'registral', 'registro', 'cartório', 'cartorio', 'irib']):
            classificacao['Direito Notarial e Registral'].append(arquivo)
        elif any(x in nome_lower for x in ['sumula', 'súmula', 'jurisprudência', 'jurisprudencia']):
            classificacao['Jurisprudência e Súmulas'].append(arquivo)
        elif any(x in nome_lower for x in ['ambiental', 'meio-ambiente', 'fauna', 'sustentabilidade']):
            classificacao['Direito Ambiental'].append(arquivo)
        elif any(x in nome_lower for x in ['administrativo', 'administração', 'administracao']):
            classificacao['Direito Administrativo'].append(arquivo)
        elif any(x in nome_lower for x in ['tributário', 'tributario', 'tributo', 'fiscal', 'simples-nacional', 'tributação', 'tributacao']):
            classificacao['Direito Tributário'].append(arquivo)
        elif any(x in nome_lower for x in ['constitucional', 'constituição', 'constituicao', 'fundamental', 'direitos-humanos']):
            classificacao['Direito Constitucional'].append(arquivo)
        elif any(x in nome_lower for x in ['bancário', 'bancario']):
            classificacao['Direito Bancário'].append(arquivo)
        elif any(x in nome_lower for x in ['digital', 'lgpd', 'proteção-dados', 'protecao-dados', 'marco-civil', 'internet']):
            classificacao['Direito Digital'].append(arquivo)
        elif any(x in nome_lower for x in ['internacional']):
            classificacao['Direito Internacional'].append(arquivo)
        else:
            classificacao['Outros'].append(arquivo)

    return classificacao

def gerar_relatorio(base_path):
    """Gera relatório completo"""
    print("=" * 80)
    print("ANÁLISE COMPLETA - BIBLIOTECA JURÍDICA")
    print("=" * 80)
    print()

    # Análise das pastas organizadas
    print("1. CONTEÚDO DAS PASTAS ORGANIZADAS:")
    print("-" * 80)

    organizados = contar_arquivos_por_pasta(base_path)
    total_organizados = 0

    for pasta, qtd in sorted(organizados.items()):
        nome_area = pasta.split('-', 1)[1].replace('-', ' ').title()
        print(f"  {nome_area:.<50} {qtd:>4} PDFs")
        total_organizados += qtd

    print(f"\n  {'TOTAL DE PDFs ORGANIZADOS':.<50} {total_organizados:>4} PDFs")
    print()

    # Análise dos novos downloads
    print("2. ANÁLISE DOS NOVOS DOWNLOADS:")
    print("-" * 80)

    path_novos = os.path.join(base_path, "novos-downloads")
    classificacao_novos = analisar_novos_downloads(path_novos)

    total_novos = sum(len(arquivos) for arquivos in classificacao_novos.values())

    for area, arquivos in sorted(classificacao_novos.items()):
        print(f"  {area:.<50} {len(arquivos):>4} PDFs")

    print(f"\n  {'TOTAL DE PDFs EM NOVOS-DOWNLOADS':.<50} {total_novos:>4} PDFs")
    print()

    # Análise comparativa
    print("3. ANÁLISE COMPARATIVA E ÁREAS CARENTES:")
    print("-" * 80)
    print()

    # Mapeamento de áreas
    mapeamento = {
        'Direito Civil': '01-direito-civil',
        'Direito Processual Civil': '02-direito-processual-civil',
        'Direito Penal': '03-direito-penal',
        'Direito Imobiliário': '04-direito-imobiliario',
        'Direito Previdenciário': '05-direito-previdenciario',
        'Direito do Trabalho': '06-direito-trabalho',
        'Direito Empresarial': '07-direito-empresarial',
        'Direito do Consumidor': '08-direito-consumidor',
        'Direito Notarial e Registral': '09-direito-notarial-registral',
        'Jurisprudência e Súmulas': '10-jurisprudencia-sumulas',
        'Direito Ambiental': '12-direito-ambiental',
        'Direito Administrativo': '13-direito-administrativo',
        'Direito Tributário': '14-direito-tributario',
        'Direito Constitucional': '15-direito-constitucional'
    }

    analise = []
    for area, pasta in mapeamento.items():
        qtd_organizada = organizados.get(pasta, 0)
        qtd_novos = len(classificacao_novos.get(area, []))
        total_area = qtd_organizada + qtd_novos

        analise.append({
            'area': area,
            'organizada': qtd_organizada,
            'novos': qtd_novos,
            'total': total_area
        })

    # Adicionar áreas que só existem em novos downloads
    for area in classificacao_novos:
        if area not in mapeamento:
            qtd_novos = len(classificacao_novos[area])
            analise.append({
                'area': area,
                'organizada': 0,
                'novos': qtd_novos,
                'total': qtd_novos
            })

    # Ordenar por total (crescente - áreas mais carentes primeiro)
    analise.sort(key=lambda x: x['total'])

    print("RANKING DAS ÁREAS (das mais carentes para as mais completas):")
    print()
    print(f"{'ÁREA':<35} {'Organizados':>12} {'Novos':>8} {'TOTAL':>10}")
    print("-" * 80)

    for item in analise:
        print(f"{item['area']:<35} {item['organizada']:>12} {item['novos']:>8} {item['total']:>10}")

    print()
    print("=" * 80)
    print()
    print("4. RECOMENDAÇÕES - ÁREAS PRIORITÁRIAS PARA COMPLETAR:")
    print("-" * 80)
    print()

    # Identificar áreas com menos de 10 PDFs
    areas_carentes = [item for item in analise if item['total'] < 10]

    if areas_carentes:
        print("[!] AREAS COM MENOS DE 10 PDFs (PRIORIDADE ALTA):")
        print()
        for i, item in enumerate(areas_carentes, 1):
            print(f"  {i}. {item['area']} ({item['total']} PDFs)")
            print(f"     > Recomendacao: Buscar mais {10 - item['total']} PDFs sobre esta area")
            print()

    # Identificar áreas com 10-20 PDFs
    areas_moderadas = [item for item in analise if 10 <= item['total'] < 20]

    if areas_moderadas:
        print("[*] AREAS COM 10-20 PDFs (PRIORIDADE MEDIA):")
        print()
        for i, item in enumerate(areas_moderadas, 1):
            print(f"  {i}. {item['area']} ({item['total']} PDFs)")
            print()

    # Áreas bem cobertas
    areas_boas = [item for item in analise if item['total'] >= 20]

    if areas_boas:
        print("[OK] AREAS BEM COBERTAS (20+ PDFs):")
        print()
        for item in areas_boas:
            print(f"  - {item['area']} ({item['total']} PDFs)")
        print()

    print("=" * 80)

if __name__ == "__main__":
    base_path = r"D:\doutora-ia\direito"
    gerar_relatorio(base_path)
