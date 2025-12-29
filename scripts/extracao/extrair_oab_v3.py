#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script V3 - Abordagem baseada em identificação de blocos de alternativas
"""

import re
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber nao instalado")
    sys.exit(1)


class ExtractorOABV3:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.questoes = []

    def limpar_texto(self, texto):
        if not texto:
            return ""
        texto = texto.replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def eh_cabecalho_rodape(self, linha):
        """Identifica linhas de cabeçalho/rodapé para ignorar."""
        padroes_ignorar = [
            r'^\d+\s*$',  # Só número
            r'^[A-Z\s]{30,}$',  # Linha toda maiúscula
            r'ARTHUR TRIGUEIROS',
            r'ÉTICA PROFISSIONAL',
            r'COMO PASSAR',
            r'^\s*\d+\s+[A-Z]+\s+[A-Z]+\s*$',  # Padrão de cabeçalho
        ]

        for padrao in padroes_ignorar:
            if re.search(padrao, linha):
                return True
        return False

    def extrair_questoes(self):
        """Extrai questões do PDF."""
        print(f"Abrindo PDF: {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            print(f"Total de paginas: {total_paginas}\n")

            # Começar da página 15 (pular prefácio, índice, etc.)
            for i in range(15, total_paginas):
                if (i - 15) % 100 == 0:
                    print(f"Processando pagina {i + 1}/{total_paginas}... (Questoes: {len(self.questoes)})")

                texto = pdf.pages[i].extract_text()
                if texto:
                    self.processar_pagina(texto)

        print(f"\nTotal de questoes encontradas: {len(self.questoes)}")

    def processar_pagina(self, texto):
        """Processa uma página em busca de questões."""
        linhas = texto.split('\n')
        linhas_limpas = [self.limpar_texto(l) for l in linhas if l.strip()]

        i = 0
        while i < len(linhas_limpas):
            # Procurar por sequência de alternativas
            questao = self.tentar_extrair_questao(linhas_limpas, i)

            if questao:
                self.questoes.append(questao)
                # Pular as linhas da questão processada
                i += questao.get('_linhas_processadas', 10)
            else:
                i += 1

    def tentar_extrair_questao(self, linhas, inicio):
        """Tenta extrair uma questão começando do índice 'inicio'."""

        # Procurar sequência de alternativas (A), (B), (C), (D)
        alternativas = {}
        idx_alternativas = {}

        # Procurar para frente até encontrar alternativas
        for offset in range(min(30, len(linhas) - inicio)):
            linha = linhas[inicio + offset]

            # Verificar se é uma alternativa
            match = re.match(r'^\s*\(([A-E])\)\s+(.+)$', linha)
            if match:
                letra = match.group(1)
                texto = match.group(2)

                # Se é a alternativa A, pode ser início de um bloco
                if letra == 'A' and not alternativas:
                    alternativas[letra] = texto
                    idx_alternativas[letra] = inicio + offset

                # Se já temos A, aceitar B, C, D em sequência
                elif letra in 'BCDE' and alternativas:
                    alternativas[letra] = texto
                    idx_alternativas[letra] = inicio + offset

        # Verificar se temos pelo menos 4 alternativas
        if len(alternativas) < 4:
            return None

        # Pegar o enunciado (linhas antes da alternativa A)
        idx_primeira_alt = idx_alternativas.get('A', inicio)
        enunciado_linhas = []

        for i in range(max(0, idx_primeira_alt - 15), idx_primeira_alt):
            linha = linhas[i]
            if not self.eh_cabecalho_rodape(linha) and len(linha) > 15:
                enunciado_linhas.append(linha)

        enunciado = ' '.join(enunciado_linhas[-5:])  # Pegar últimas 5 linhas antes das alternativas
        enunciado = self.limpar_texto(enunciado)

        # Procurar gabarito nas próximas linhas
        gabarito = 'A'  # Default
        idx_ultima_alt = max(idx_alternativas.values())

        for offset in range(1, min(20, len(linhas) - idx_ultima_alt)):
            linha = linhas[idx_ultima_alt + offset]

            # Procurar por padrões de gabarito
            # Padrão: "X" otirabaG ou Gabarito X ou similar
            match_gab = re.search(r'["""]([A-E])["""]?\s+otirabaG', linha, re.IGNORECASE)
            if not match_gab:
                match_gab = re.search(r'Gabarito[:\s]+["""]?([A-E])["""]?', linha, re.IGNORECASE)
            if not match_gab:
                match_gab = re.search(r'^([A-E]):\s*(correta|incorreta)', linha, re.IGNORECASE)

            if match_gab:
                gabarito = match_gab.group(1).upper()
                break

        # Limpar enunciado de fragmentos
        enunciado = re.sub(r'(OAB/Exame Unificado|Unificado|–|—)', '', enunciado)
        enunciado = self.limpar_texto(enunciado)

        if len(enunciado) < 30:
            return None

        # Limpar alternativas
        for letra in list(alternativas.keys()):
            alt_texto = alternativas[letra]
            # Remover comentários
            alt_texto = re.sub(r'\s+([A-E]:|correta|incorreta).*', '', alt_texto)
            alternativas[letra] = self.limpar_texto(alt_texto)

            # Se alternativa ficou muito curta, pode ter problema
            if len(alternativas[letra]) < 5:
                return None

        questao = {
            'numero': len(self.questoes) + 1,
            'pergunta': enunciado,
            'alternativas': alternativas,
            'gabarito': gabarito,
            '_linhas_processadas': idx_ultima_alt - idx_primeira_alt + 15
        }

        return questao

    def salvar_json(self, output_path):
        """Salva em JSON."""
        # Remover campo interno _linhas_processadas
        questoes_limpar = []
        for q in self.questoes:
            q_copy = q.copy()
            q_copy.pop('_linhas_processadas', None)
            questoes_limpar.append(q_copy)

        # Renumerar
        for i, q in enumerate(questoes_limpar, 1):
            q['numero'] = i

        print(f"\nSalvando {len(questoes_limpar)} questoes em: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questoes_limpar, f, ensure_ascii=False, indent=2)

        print("Arquivo JSON criado!")
        return questoes_limpar


def main():
    PDF_PATH = r"D:\doutora-ia\direito\20-material-oab\Como Passar Na OAB 5.000 Questo -.pdf"
    OUTPUT_JSON = r"C:\Users\NFC\questoes_oab_5000.json"

    if not Path(PDF_PATH).exists():
        print(f"ERRO: Arquivo nao encontrado")
        sys.exit(1)

    print("="*80)
    print("EXTRATOR DE QUESTOES OAB - VERSAO 3")
    print("="*80 + "\n")

    extrator = ExtractorOABV3(PDF_PATH)
    extrator.extrair_questoes()
    questoes = extrator.salvar_json(OUTPUT_JSON)

    # Mostrar exemplos
    print("\n" + "="*80)
    print("PRIMEIRAS 3 QUESTOES:")
    print("="*80)

    for q in questoes[:3]:
        print(f"\nQuestao {q['numero']}:")
        print(f"Pergunta: {q['pergunta'][:120]}...")
        print(f"Alt A: {q['alternativas'].get('A', '')[:80]}...")
        print(f"Gabarito: {q['gabarito']}")

    print("\n" + "="*80)
    print(f"CONCLUIDO! Total: {len(questoes)} questoes")
    print(f"Arquivo: {OUTPUT_JSON}")
    print("="*80)


if __name__ == '__main__':
    main()
