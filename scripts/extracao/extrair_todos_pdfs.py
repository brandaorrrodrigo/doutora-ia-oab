#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXTRATOR UNIVERSAL - Processa TODOS os PDFs de questões OAB
Gera um banco consolidado com milhares de questões
"""

import json
import re
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber não instalado. Execute: pip install pdfplumber")
    import sys
    sys.exit(1)


class ExtratorUniversal:
    def __init__(self, pasta_pdfs):
        self.pasta_pdfs = Path(pasta_pdfs)
        self.questoes_por_arquivo = {}
        self.questoes_consolidadas = []
        self.estatisticas = {}

    def listar_pdfs_questoes(self):
        """Lista PDFs que contêm questões."""
        pdfs_questoes = []

        # Padrões que indicam PDF com questões
        padroes = [
            r'questao|questoes|questo',
            r'simulado',
            r'exercicio',
            r'prova',
            r'exame',
        ]

        for pdf in self.pasta_pdfs.glob('*.pdf'):
            nome = pdf.name.lower()

            # Ignorar PDFs de outros tipos
            if any(x in nome for x in ['peticao', 'modelo', 'peca', 'legislacao', 'apostila-professor']):
                continue

            # Verificar se contém questões
            for padrao in padroes:
                if re.search(padrao, nome, re.IGNORECASE):
                    pdfs_questoes.append(pdf)
                    break

        return sorted(pdfs_questoes)

    def extrair_questoes_pdf(self, pdf_path, max_paginas=500):
        """Extrai questões de um PDF específico."""
        print(f"\n{'='*80}")
        print(f"Processando: {pdf_path.name}")
        print(f"{'='*80}")

        questoes = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_paginas = min(len(pdf.pages), max_paginas)
                print(f"Total de páginas: {total_paginas}")

                todas_linhas = []

                # Extrair texto
                for i, page in enumerate(pdf.pages[:total_paginas], 1):
                    if i % 50 == 0:
                        print(f"  Lendo página {i}/{total_paginas}...")

                    texto = page.extract_text()
                    if texto:
                        linhas = texto.split('\n')
                        todas_linhas.extend([self.limpar_texto(l) for l in linhas if l.strip()])

                # Processar questões
                print(f"  Processando {len(todas_linhas)} linhas...")
                questoes = self.identificar_questoes(todas_linhas)

                print(f"  [OK] Extraidas {len(questoes)} questoes")

        except Exception as e:
            print(f"  [ERRO] ao processar: {str(e)}")

        return questoes

    def limpar_texto(self, texto):
        """Limpa texto."""
        if not texto:
            return ""
        texto = texto.replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def identificar_questoes(self, linhas):
        """Identifica questões nas linhas."""
        questoes = []
        i = 0

        while i < len(linhas):
            # Procurar por bloco de alternativas
            bloco = self.encontrar_bloco_alternativas(linhas, i)

            if bloco:
                questao = self.montar_questao(linhas, bloco)
                if questao:
                    questoes.append(questao)
                    i = bloco['fim'] + 15
                else:
                    i += 1
            else:
                i += 1

        return questoes

    def encontrar_bloco_alternativas(self, linhas, inicio):
        """Encontra um bloco de alternativas."""
        # Procurar (A)
        idx_a = None

        for offset in range(min(30, len(linhas) - inicio)):
            linha = linhas[inicio + offset]
            if re.match(r'^\(A\)\s+.{10,}', linha):
                idx_a = inicio + offset
                break

        if idx_a is None:
            return None

        # Coletar alternativas
        alternativas = {}
        indices = {}

        i = idx_a
        letras = ['A', 'B', 'C', 'D', 'E']
        letra_idx = 0

        while i < len(linhas) and letra_idx < len(letras):
            linha = linhas[i]
            letra = letras[letra_idx]

            match = re.match(rf'^\({letra}\)\s+(.+)$', linha)
            if match:
                alternativas[letra] = match.group(1)
                indices[letra] = i
                letra_idx += 1

            i += 1
            if i > idx_a + 30:
                break

        if len(alternativas) < 4:
            return None

        return {
            'inicio': idx_a,
            'fim': max(indices.values()) if indices else idx_a,
            'alternativas': alternativas
        }

    def montar_questao(self, linhas, bloco):
        """Monta questão completa."""
        # Enunciado
        enunciado_linhas = []
        inicio = max(0, bloco['inicio'] - 15)

        for i in range(inicio, bloco['inicio']):
            linha = linhas[i]
            if len(linha) > 20 and not self.eh_cabecalho(linha):
                enunciado_linhas.append(linha)

        enunciado = ' '.join(enunciado_linhas[-8:])
        enunciado = self.limpar_enunciado(enunciado)

        if len(enunciado) < 30:
            return None

        # Gabarito
        gabarito = self.buscar_gabarito(linhas, bloco['fim'])

        # Limpar alternativas
        alternativas_limpas = {}
        for letra, texto in bloco['alternativas'].items():
            texto_limpo = self.limpar_alternativa(texto)
            if len(texto_limpo) < 10:
                return None
            alternativas_limpas[letra] = texto_limpo

        return {
            'pergunta': enunciado,
            'alternativas': alternativas_limpas,
            'gabarito': gabarito
        }

    def eh_cabecalho(self, linha):
        """Verifica se é cabeçalho."""
        padroes = [
            r'^\d+\s*$',
            r'OAB.*QUESTAO',
            r'SIMULADO',
            r'PROVA',
        ]
        return any(re.search(p, linha, re.IGNORECASE) for p in padroes)

    def limpar_enunciado(self, texto):
        """Limpa enunciado."""
        texto = re.sub(r'\(OAB[^)]*\)', '', texto)
        texto = re.sub(r'([A-E]):\s*(correta|incorreta)[^.]*\.', '', texto, flags=re.IGNORECASE)
        return self.limpar_texto(texto)

    def limpar_alternativa(self, texto):
        """Limpa alternativa."""
        texto = re.sub(r'\s+([A-E]):\s*(correta|incorreta).*', '', texto, flags=re.IGNORECASE)
        return self.limpar_texto(texto)

    def buscar_gabarito(self, linhas, idx_ultima_alt):
        """Busca gabarito."""
        for offset in range(1, min(25, len(linhas) - idx_ultima_alt)):
            linha = linhas[idx_ultima_alt + offset]

            # Padrões
            match = re.search(r'["""]([A-E])["""]?\s+otirabaG', linha, re.IGNORECASE)
            if not match:
                match = re.search(r'Gabarito[:\s]+["""]?([A-E])["""]?', linha, re.IGNORECASE)
            if not match:
                match = re.search(r'^([A-E]):\s*correta', linha, re.IGNORECASE)

            if match:
                return match.group(1).upper()

        return 'A'  # Default

    def processar_todos(self):
        """Processa todos os PDFs."""
        pdfs = self.listar_pdfs_questoes()

        print("="*80)
        print("EXTRAÇÃO UNIVERSAL - TODOS OS PDFs OAB")
        print("="*80)
        print(f"\nEncontrados {len(pdfs)} PDFs com questões\n")

        for i, pdf in enumerate(pdfs, 1):
            print(f"\n[{i}/{len(pdfs)}]")

            questoes = self.extrair_questoes_pdf(pdf)

            if questoes:
                self.questoes_por_arquivo[pdf.name] = questoes
                self.estatisticas[pdf.name] = len(questoes)

        # Consolidar
        self.consolidar_questoes()

    def consolidar_questoes(self):
        """Consolida todas as questões em um único array."""
        print("\n" + "="*80)
        print("CONSOLIDANDO QUESTÕES")
        print("="*80 + "\n")

        numero = 1

        for arquivo, questoes in self.questoes_por_arquivo.items():
            for q in questoes:
                questao_consolidada = {
                    'numero': numero,
                    'fonte': arquivo,
                    'pergunta': q['pergunta'],
                    'alternativas': q['alternativas'],
                    'gabarito': q['gabarito']
                }
                self.questoes_consolidadas.append(questao_consolidada)
                numero += 1

        print(f"Total consolidado: {len(self.questoes_consolidadas)} questões")

    def salvar_resultados(self, pasta_saida):
        """Salva resultados."""
        pasta_saida = Path(pasta_saida)
        pasta_saida.mkdir(exist_ok=True)

        # 1. Banco consolidado
        arquivo_consolidado = pasta_saida / 'questoes_oab_consolidado.json'
        print(f"\nSalvando banco consolidado: {arquivo_consolidado}")

        with open(arquivo_consolidado, 'w', encoding='utf-8') as f:
            json.dump(self.questoes_consolidadas, f, ensure_ascii=False, indent=2)

        # 2. Por arquivo (separado)
        pasta_separados = pasta_saida / 'por_arquivo'
        pasta_separados.mkdir(exist_ok=True)

        for arquivo, questoes in self.questoes_por_arquivo.items():
            # Renumerar
            for i, q in enumerate(questoes, 1):
                q['numero'] = i

            nome_json = arquivo.replace('.pdf', '.json').replace('.PDF', '.json')
            caminho = pasta_separados / nome_json

            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(questoes, f, ensure_ascii=False, indent=2)

        # 3. Relatório
        self.gerar_relatorio(pasta_saida / 'relatorio_extracao.txt')

        print("\n[OK] Todos os arquivos salvos!")

    def gerar_relatorio(self, arquivo):
        """Gera relatório de extração."""
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("RELATORIO DE EXTRACAO - BANCO CONSOLIDADO OAB\n")
            f.write("="*80 + "\n\n")

            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")

            f.write("RESUMO GERAL\n")
            f.write("-"*80 + "\n")
            f.write(f"Total de PDFs processados: {len(self.questoes_por_arquivo)}\n")
            f.write(f"Total de questoes extraidas: {len(self.questoes_consolidadas)}\n\n")

            f.write("DETALHAMENTO POR ARQUIVO\n")
            f.write("-"*80 + "\n\n")

            for arquivo, qtd in sorted(self.estatisticas.items(), key=lambda x: x[1], reverse=True):
                f.write(f"{arquivo}\n")
                f.write(f"  Questoes: {qtd}\n\n")

        print(f"Relatorio salvo: {arquivo}")


def main():
    PASTA_PDFS = r"D:\doutora-ia\direito\20-material-oab"
    PASTA_SAIDA = r"C:\Users\NFC\questoes_oab_todos"

    extrator = ExtratorUniversal(PASTA_PDFS)
    extrator.processar_todos()
    extrator.salvar_resultados(PASTA_SAIDA)

    # Mostrar estatísticas
    print("\n" + "="*80)
    print("ESTATISTICAS FINAIS")
    print("="*80 + "\n")

    for arquivo, qtd in sorted(extrator.estatisticas.items(), key=lambda x: x[1], reverse=True):
        print(f"{qtd:4d} questoes - {arquivo}")

    print(f"\n{'='*80}")
    print(f"TOTAL CONSOLIDADO: {len(extrator.questoes_consolidadas)} QUESTOES")
    print("="*80)


if __name__ == '__main__':
    main()
