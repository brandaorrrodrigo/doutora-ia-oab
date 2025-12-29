#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
import re

def analisar_cobertura_qualitativa(base_path):
    """Analisa a qualidade da cobertura por temas específicos"""

    print("=" * 80)
    print("ANALISE QUALITATIVA - COBERTURA POR TEMAS ESPECIFICOS")
    print("=" * 80)
    print()

    # Temas específicos a verificar
    temas = {
        'Direito de Família': ['família', 'familia', 'alimentos', 'divórcio', 'divorcio', 'guarda', 'adoção', 'adocao'],
        'Direito das Sucessões': ['sucessões', 'sucessoes', 'herança', 'heranca', 'inventário', 'inventario', 'testamento'],
        'Contratos': ['contratos', 'contrato'],
        'Responsabilidade Civil': ['responsabilidade civil', 'dano moral', 'indenização', 'indenizacao'],
        'Posse e Propriedade': ['posse', 'propriedade', 'usucapião', 'usucapiao'],
        'Direito do Consumidor': ['consumidor', 'cdc'],
        'Locação e Inquilinato': ['locação', 'locacao', 'inquilinato', 'despejo'],
        'Direito Penal - Parte Geral': ['penal parte geral', 'teoria do crime', 'teoria da pena'],
        'Direito Penal - Parte Especial': ['penal parte especial', 'crimes em espécie'],
        'Crimes Ambientais': ['crimes ambientais', 'fauna'],
        'Processo Penal': ['processo penal', 'processual penal'],
        'CLT e Reforma Trabalhista': ['clt', 'reforma trabalhista', 'consolidação trabalhista'],
        'Direito Societário': ['societário', 'societario', 'sociedades', 's.a.', 's/a'],
        'Títulos de Crédito': ['títulos de crédito', 'titulos de credito', 'cheque', 'nota promissória'],
        'Falência e Recuperação': ['falência', 'falencia', 'recuperação judicial', 'recuperacao judicial'],
        'Direito Tributário Específico': ['icms', 'iss', 'ipi', 'ir', 'simples nacional'],
        'Execução Fiscal': ['execução fiscal', 'execucao fiscal'],
        'Licitações e Contratos Administrativos': ['licitações', 'licitacoes', 'contratos administrativos', 'pregão'],
        'Servidores Públicos': ['servidores públicos', 'servidores publicos', 'estatutário'],
        'LGPD e Proteção de Dados': ['lgpd', 'proteção de dados', 'protecao de dados'],
        'Marco Civil da Internet': ['marco civil', 'internet'],
        'Direitos Humanos': ['direitos humanos'],
        'Direito Internacional Público': ['internacional público', 'internacional publico', 'tratados'],
        'Direito Internacional Privado': ['internacional privado'],
        'Registros Públicos': ['registros públicos', 'registros publicos', 'registro de imóveis', 'registro de imoveis'],
        'Cartórios e Tabelionato': ['cartório', 'cartorio', 'tabelionato', 'notarial'],
        'Direito da Criança e Adolescente': ['criança', 'crianca', 'adolescente', 'eca'],
        'Direito do Idoso': ['idoso'],
        'Direito Previdenciário - Benefícios': ['benefícios previdenciários', 'beneficios previdenciarios', 'aposentadoria'],
        'Direito Processual Civil - Procedimentos Especiais': ['procedimentos especiais', 'ações possessórias', 'acoes possessorias'],
        'Recursos': ['recursos', 'agravo', 'apelação', 'apelacao', 'recurso especial'],
        'Execução': ['execução', 'execucao', 'cumprimento de sentença'],
        'Ação Rescisória': ['ação rescisória', 'acao rescisoria'],
        'Mandado de Segurança': ['mandado de segurança', 'mandado de seguranca'],
        'Ações Constitucionais': ['adin', 'adc', 'adpf', 'habeas corpus', 'habeas data'],
        'Direito Eleitoral': ['eleitoral', 'eleições', 'eleicoes'],
        'Direito Urbanístico': ['urbanístico', 'urbanistico', 'plano diretor'],
        'Direito Agrário': ['agrário', 'agrario', 'reforma agrária']
    }

    # Buscar em todas as pastas
    todos_arquivos = []

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
            for arquivo in os.listdir(caminho):
                if arquivo.lower().endswith('.pdf'):
                    todos_arquivos.append(arquivo)

    # Novos downloads
    caminho_novos = os.path.join(base_path, "novos-downloads")
    if os.path.exists(caminho_novos):
        for arquivo in os.listdir(caminho_novos):
            if arquivo.lower().endswith('.pdf'):
                todos_arquivos.append(arquivo)

    # Analisar cobertura de cada tema
    cobertura = {}

    for tema, palavras_chave in temas.items():
        encontrados = []
        for arquivo in todos_arquivos:
            arquivo_lower = arquivo.lower()
            for palavra in palavras_chave:
                if palavra.lower() in arquivo_lower:
                    encontrados.append(arquivo)
                    break

        cobertura[tema] = {
            'quantidade': len(set(encontrados)),
            'arquivos': list(set(encontrados))[:3]  # Primeiros 3 exemplos
        }

    # Ordenar por quantidade (crescente)
    cobertura_ordenada = sorted(cobertura.items(), key=lambda x: x[1]['quantidade'])

    print("COBERTURA POR TEMAS ESPECIFICOS:")
    print()
    print(f"{'TEMA':<50} {'PDFs':>8} {'EXEMPLOS'}")
    print("-" * 80)

    for tema, dados in cobertura_ordenada:
        qtd = dados['quantidade']
        status = "[!]" if qtd == 0 else "[*]" if qtd < 3 else "[OK]"
        print(f"{status} {tema:<46} {qtd:>4}")

        if dados['arquivos']:
            for arquivo in dados['arquivos'][:2]:
                # Truncar nome do arquivo se muito longo
                nome_curto = arquivo[:70] + "..." if len(arquivo) > 70 else arquivo
                print(f"    -> {nome_curto}")
        print()

    print("=" * 80)
    print()
    print("RESUMO DAS AREAS MAIS CARENTES:")
    print("-" * 80)
    print()

    sem_cobertura = [tema for tema, dados in cobertura_ordenada if dados['quantidade'] == 0]
    cobertura_baixa = [tema for tema, dados in cobertura_ordenada if 0 < dados['quantidade'] < 3]

    if sem_cobertura:
        print("[!] TEMAS SEM NENHUM PDF (PRIORIDADE CRITICA):")
        for i, tema in enumerate(sem_cobertura, 1):
            print(f"  {i}. {tema}")
        print()

    if cobertura_baixa:
        print("[*] TEMAS COM COBERTURA INSUFICIENTE (1-2 PDFs):")
        for i, tema in enumerate(cobertura_baixa, 1):
            qtd = cobertura[tema]['quantidade']
            print(f"  {i}. {tema} ({qtd} PDF{'s' if qtd > 1 else ''})")
        print()

    print("=" * 80)

if __name__ == "__main__":
    base_path = r"D:\doutora-ia\direito"
    analisar_cobertura_qualitativa(base_path)
