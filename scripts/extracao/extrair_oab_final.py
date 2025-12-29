#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERSAO FINAL - Extrator otimizado de questões OAB
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


class ExtractorOABFinal:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.questoes = []

    def limpar_texto(self, texto):
        if not texto:
            return ""
        texto = texto.replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto)
        # Remover comentários inline comuns
        texto = re.sub(r'\s*(A:|B:|C:|D:|E:)\s*(correta|incorreta)[,;.].*', '', texto, flags=re.IGNORECASE)
        return texto.strip()

    def eh_cabecalho(self, linha):
        """Identifica cabeçalhos/rodapés."""
        padroes = [
            r'^\d+\s*$',
            r'^\d+\s+[A-Z\s]+\s+[A-Z\s]+$',
            r'ARTHUR TRIGUEIROS',
            r'ÉTICA PROFISSIONAL',
            r'COMO PASSAR',
            r'^\s*\d+\.\s*[A-Z]+.*$',  # Números de capítulo
        ]

        for p in padroes:
            if re.search(p, linha):
                return True
        return False

    def extrair_questoes(self):
        """Extrai questões do PDF."""
        print(f"Abrindo PDF: {self.pdf_path}\n")

        with pdfplumber.open(self.pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            print(f"Total de paginas: {total_paginas}\n")

            # Acumular todas as linhas do PDF
            todas_linhas = []

            for i in range(15, total_paginas):  # Pular índice/prefácio
                if (i - 15) % 100 == 0:
                    print(f"Lendo pagina {i + 1}/{total_paginas}...")

                texto = pdf.pages[i].extract_text()
                if texto:
                    linhas = texto.split('\n')
                    for linha in linhas:
                        linha_limpa = self.limpar_texto(linha)
                        if linha_limpa and not self.eh_cabecalho(linha_limpa):
                            todas_linhas.append(linha_limpa)

            print(f"\nProcessando {len(todas_linhas)} linhas...\n")
            self.processar_linhas(todas_linhas)

        print(f"Total de questoes extraidas: {len(self.questoes)}")

    def processar_linhas(self, linhas):
        """Processa linhas para extrair questões."""
        i = 0

        while i < len(linhas):
            questao = self.extrair_questao_em(linhas, i)

            if questao:
                self.questoes.append(questao)
                i += questao.get('_skip', 10)
            else:
                i += 1

            # Progresso
            if len(self.questoes) % 100 == 0 and len(self.questoes) > 0:
                print(f"  Questoes extraidas: {len(self.questoes)}")

    def extrair_questao_em(self, linhas, inicio):
        """Tenta extrair uma questão começando em 'inicio'."""

        # Procurar alternativas
        alternativas = {}
        indices_alt = {}

        # Procurar até 40 linhas à frente
        for offset in range(min(40, len(linhas) - inicio)):
            linha = linhas[inicio + offset]

            # Tentar match de alternativa
            match = re.match(r'^\(([A-E])\)\s+(.+)$', linha)
            if match:
                letra = match.group(1)
                texto_inicial = match.group(2)

                # Alternativa A = possível início
                if letra == 'A' and not alternativas:
                    alternativas[letra] = [texto_inicial]
                    indices_alt[letra] = inicio + offset

                # Outras alternativas em sequência
                elif letra in 'BCDE' and 'A' in alternativas:
                    alternativas[letra] = [texto_inicial]
                    indices_alt[letra] = inicio + offset

        # Precisa ter pelo menos 4 alternativas
        if len(alternativas) < 4:
            return None

        # Capturar continuações das alternativas
        self.capturar_continuacoes(linhas, indices_alt, alternativas)

        # Enunciado = linhas antes da alternativa A
        idx_a = indices_alt['A']
        enunciado_linhas = []

        # Pegar até 20 linhas antes de A
        for i in range(max(0, idx_a - 20), idx_a):
            linha = linhas[i]
            # Filtrar linhas curtas e referências a outras questões
            if len(linha) > 25 and 'OAB/Exame' not in linha:
                enunciado_linhas.append(linha)

        # Pegar últimas 8 linhas (geralmente o enunciado principal)
        enunciado = ' '.join(enunciado_linhas[-8:])
        enunciado = self.limpar_enunciado(enunciado)

        # Gabarito
        gabarito = self.buscar_gabarito(linhas, max(indices_alt.values()))

        # Validar
        if len(enunciado) < 40:
            return None

        # Limpar alternativas
        alt_limpar = {}
        for letra, textos in alternativas.items():
            texto_completo = ' '.join(textos)
            texto_limpo = self.limpar_alternativa(texto_completo)
            if len(texto_limpo) < 10:  # Alternativa muito curta
                return None
            alt_limpar[letra] = texto_limpo

        return {
            'numero': len(self.questoes) + 1,
            'pergunta': enunciado,
            'alternativas': alt_limpar,
            'gabarito': gabarito,
            '_skip': max(indices_alt.values()) - idx_a + 20
        }

    def capturar_continuacoes(self, linhas, indices_alt, alternativas):
        """Captura linhas de continuação das alternativas."""
        letras_ordenadas = sorted(indices_alt.keys())

        for i, letra in enumerate(letras_ordenadas):
            idx_inicio = indices_alt[letra]

            # Determinar onde essa alternativa termina
            if i + 1 < len(letras_ordenadas):
                proxima_letra = letras_ordenadas[i + 1]
                idx_fim = indices_alt[proxima_letra]
            else:
                idx_fim = min(idx_inicio + 10, len(linhas))

            # Capturar linhas de continuação
            for j in range(idx_inicio + 1, idx_fim):
                linha = linhas[j]

                # Parar se encontrar outra alternativa ou gabarito
                if re.match(r'^\([A-E]\)', linha):
                    break
                if 'otirabaG' in linha or 'Gabarito' in linha:
                    break
                if 'correta' in linha.lower() or 'incorreta' in linha.lower():
                    break

                # Se linha parece ser continuação, adicionar
                if len(linha) > 15 and not self.eh_cabecalho(linha):
                    alternativas[letra].append(linha)

    def limpar_enunciado(self, texto):
        """Limpa o enunciado removendo comentários."""
        # Remover padrões comuns de comentários
        texto = re.sub(r'(Nos termos|Como visto|Vamos|A:.*|B:.*|C:.*|D:.*).*', '', texto, flags=re.IGNORECASE)
        texto = re.sub(r'(correta|incorreta)[,;:].*', '', texto, flags=re.IGNORECASE)
        texto = re.sub(r'OAB/Exame Unificado.*?\)', '', texto)

        # Remover frases explicativas comuns
        texto = re.sub(r'(art\.|artigo|§)\s*\d+.*?(do|da|EAOAB|CED).*?[;.]', '', texto, flags=re.IGNORECASE)

        return self.limpar_texto(texto)

    def limpar_alternativa(self, texto):
        """Limpa o texto da alternativa."""
        # Remover comentários comuns
        texto = re.sub(r'\s+([A-E]:)\s*(correta|incorreta).*', '', texto, flags=re.IGNORECASE)
        texto = re.sub(r'(Nos termos|Como visto|Perceba).*', '', texto, flags=re.IGNORECASE)

        return self.limpar_texto(texto)

    def buscar_gabarito(self, linhas, idx_ultima_alt):
        """Busca o gabarito nas linhas após as alternativas."""
        for offset in range(1, min(25, len(linhas) - idx_ultima_alt)):
            linha = linhas[idx_ultima_alt + offset]

            # Padrões de gabarito
            patterns = [
                r'["""]([A-E])["""]?\s+otirabaG',
                r'Gabarito[:\s]+["""]?([A-E])["""]?',
                r'^([A-E]):\s*correta',
            ]

            for pattern in patterns:
                match = re.search(pattern, linha, re.IGNORECASE)
                if match:
                    return match.group(1).upper()

        return 'A'  # Default se não encontrar

    def salvar_json(self, output_path):
        """Salva em JSON."""
        # Remover campos internos
        questoes_finais = []
        for q in self.questoes:
            q_limpa = {
                'numero': q['numero'],
                'pergunta': q['pergunta'],
                'alternativas': q['alternativas'],
                'gabarito': q['gabarito']
            }
            questoes_finais.append(q_limpa)

        # Renumerar
        for i, q in enumerate(questoes_finais, 1):
            q['numero'] = i

        print(f"\nSalvando {len(questoes_finais)} questoes em: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questoes_finais, f, ensure_ascii=False, indent=2)

        print("Arquivo salvo com sucesso!")
        return questoes_finais


def main():
    PDF_PATH = r"D:\doutora-ia\direito\20-material-oab\Como Passar Na OAB 5.000 Questo -.pdf"
    OUTPUT_JSON = r"C:\Users\NFC\questoes_oab_completo.json"

    if not Path(PDF_PATH).exists():
        print("ERRO: Arquivo nao encontrado")
        sys.exit(1)

    print("="*80)
    print("EXTRATOR FINAL DE QUESTOES OAB")
    print("="*80 + "\n")

    extrator = ExtractorOABFinal(PDF_PATH)
    extrator.extrair_questoes()
    questoes = extrator.salvar_json(OUTPUT_JSON)

    # Exemplos
    print("\n" + "="*80)
    print("EXEMPLOS DE QUESTOES EXTRAIDAS:")
    print("="*80)

    for i in [0, len(questoes)//2, -1]:  # Primeira, do meio, última
        if i < len(questoes):
            q = questoes[i]
            print(f"\n--- Questao {q['numero']} ---")
            print(f"Pergunta: {q['pergunta'][:100]}...")
            print(f"Alt A: {q['alternativas']['A'][:70]}...")
            print(f"Gabarito: {q['gabarito']}")

    print("\n" + "="*80)
    print(f"CONCLUIDO!")
    print(f"Total de questoes: {len(questoes)}")
    print(f"Arquivo: {OUTPUT_JSON}")
    print("="*80)


if __name__ == '__main__':
    main()
