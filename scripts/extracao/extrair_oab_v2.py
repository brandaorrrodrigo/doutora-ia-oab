#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script MELHORADO para extrair todas as questões do PDF da OAB
"""

import re
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber nao instalado. Execute: pip install pdfplumber")
    sys.exit(1)


class ExtractorOABV2:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.questoes = []

        # Padrões mais precisos
        self.pattern_alternativa = re.compile(r'^\s*\(([A-E])\)\s+(.+)$')
        self.pattern_gabarito = re.compile(r'["""]([A-E])["""]?\s+otirabaG', re.IGNORECASE)
        self.pattern_gabarito_alt = re.compile(r'Gabarito[:\s]+["""]?([A-E])["""]?', re.IGNORECASE)

    def limpar_texto(self, texto):
        """Remove espaços extras e caracteres problemáticos."""
        if not texto:
            return ""
        texto = texto.replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto)
        return texto.strip()

    def extrair_texto_pdf(self):
        """Extrai todo o texto do PDF."""
        print(f"Abrindo PDF: {self.pdf_path}")

        texto_completo = []

        with pdfplumber.open(self.pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            print(f"Total de paginas: {total_paginas}")

            for i, page in enumerate(pdf.pages, 1):
                if i % 50 == 0:
                    print(f"Processando pagina {i}/{total_paginas}...")

                texto = page.extract_text()
                if texto:
                    linhas = texto.split('\n')
                    for linha in linhas:
                        linha_limpa = self.limpar_texto(linha)
                        if linha_limpa:
                            texto_completo.append(linha_limpa)

        print(f"Total de linhas extraidas: {len(texto_completo)}")
        return texto_completo

    def identificar_questoes(self, linhas):
        """Identifica questões usando uma abordagem baseada em gabarito."""
        print("\nIdentificando questoes...")

        i = 0
        questao_buffer = []

        while i < len(linhas):
            linha = linhas[i]
            questao_buffer.append(linha)

            # Verificar se encontramos um gabarito (fim de questão)
            match_gab = self.pattern_gabarito.search(linha)
            if not match_gab:
                match_gab = self.pattern_gabarito_alt.search(linha)

            if match_gab:
                gabarito = match_gab.group(1)

                # Processar o buffer como uma questão
                self.processar_questao(questao_buffer, gabarito)

                # Limpar buffer para próxima questão
                questao_buffer = []

            i += 1

        # Processar última questão se houver buffer
        if questao_buffer:
            self.processar_questao(questao_buffer, 'A')  # placeholder

        print(f"Total de questoes identificadas: {len(self.questoes)}")

    def processar_questao(self, buffer, gabarito):
        """Processa um buffer de linhas como uma questão."""
        if len(buffer) < 5:  # Questão muito curta, ignorar
            return

        # Encontrar onde começam as alternativas
        alternativas = {}
        idx_primeira_alternativa = -1

        for i, linha in enumerate(buffer):
            match = self.pattern_alternativa.match(linha)
            if match:
                letra = match.group(1)
                texto = match.group(2)

                if letra == 'A' and idx_primeira_alternativa == -1:
                    idx_primeira_alternativa = i

                if idx_primeira_alternativa != -1:
                    alternativas[letra] = texto

        # Se não encontrou alternativas válidas, ignorar
        if len(alternativas) < 4 or idx_primeira_alternativa == -1:
            return

        # Enunciado: tudo antes da primeira alternativa
        enunciado_linhas = buffer[:idx_primeira_alternativa]

        # Filtrar cabeçalhos, números de página, etc
        enunciado_filtrado = []
        for linha in enunciado_linhas:
            # Ignorar linhas que parecem ser cabeçalhos
            if any(x in linha for x in ['ARTHUR TRIGUEIROS', 'ÉTICA PROFISSIONAL',
                                        'OAB/Exame', 'Unificado', 'COMO PASSAR']):
                continue
            # Ignorar linhas muito curtas
            if len(linha) > 20:
                enunciado_filtrado.append(linha)

        # Montar enunciado
        enunciado = ' '.join(enunciado_filtrado)
        enunciado = self.limpar_texto(enunciado)

        # Limpar comentários do enunciado (geralmente começam com palavras-chave)
        enunciado = re.sub(r'(A:|B:|C:|D:|incorreta|correta|Nos termos|Como visto).*', '',
                          enunciado, flags=re.IGNORECASE)
        enunciado = self.limpar_texto(enunciado)

        # Limpar alternativas de continuações indesejadas
        for letra in list(alternativas.keys()):
            alt_texto = alternativas[letra]
            # Remover comentários que possam estar nas alternativas
            alt_texto = re.sub(r'\s+(A:|B:|C:|D:|incorreta|correta).*', '', alt_texto)
            alternativas[letra] = self.limpar_texto(alt_texto)

        # Validar questão
        if not enunciado or len(enunciado) < 30:
            return

        # Criar questão
        questao = {
            'numero': len(self.questoes) + 1,
            'pergunta': enunciado,
            'alternativas': alternativas,
            'gabarito': gabarito.upper()
        }

        self.questoes.append(questao)

    def processar(self):
        """Processa todo o PDF."""
        linhas = self.extrair_texto_pdf()
        self.identificar_questoes(linhas)

        # Renumerar
        for i, q in enumerate(self.questoes, 1):
            q['numero'] = i

        return self.questoes

    def salvar_json(self, output_path):
        """Salva questões em JSON."""
        print(f"\nSalvando {len(self.questoes)} questoes em: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.questoes, f, ensure_ascii=False, indent=2)

        print(f"Arquivo JSON criado!")

    def salvar_estatisticas(self, stats_path):
        """Salva estatísticas da extração."""
        print(f"\nGerando estatisticas em: {stats_path}")

        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(f"Estatisticas da Extracao\n")
            f.write(f"="*80 + "\n\n")
            f.write(f"Total de questoes extraidas: {len(self.questoes)}\n\n")

            # Contar gabaritos
            gabaritos_count = {}
            for q in self.questoes:
                gab = q.get('gabarito', 'N/A')
                gabaritos_count[gab] = gabaritos_count.get(gab, 0) + 1

            f.write("Distribuicao de gabaritos:\n")
            for letra in sorted(gabaritos_count.keys()):
                f.write(f"  {letra}: {gabaritos_count[letra]}\n")


def main():
    PDF_PATH = r"D:\doutora-ia\direito\20-material-oab\Como Passar Na OAB 5.000 Questo -.pdf"
    OUTPUT_JSON = r"C:\Users\NFC\questoes_oab_5000.json"
    OUTPUT_STATS = r"C:\Users\NFC\questoes_stats.txt"

    if not Path(PDF_PATH).exists():
        print(f"ERRO: Arquivo nao encontrado: {PDF_PATH}")
        sys.exit(1)

    print("="*80)
    print("EXTRATOR DE QUESTOES OAB - VERSAO 2")
    print("="*80)

    extrator = ExtractorOABV2(PDF_PATH)
    questoes = extrator.processar()

    extrator.salvar_json(OUTPUT_JSON)
    extrator.salvar_estatisticas(OUTPUT_STATS)

    # Mostrar exemplos
    print("\n" + "="*80)
    print("PRIMEIRAS 5 QUESTOES:")
    print("="*80)

    for q in questoes[:5]:
        print(f"\nQuestao {q['numero']}:")
        print(f"Pergunta: {q['pergunta'][:150]}...")
        print(f"Alternativas: {list(q['alternativas'].keys())}")
        print(f"Gabarito: {q['gabarito']}")

    print("\n" + "="*80)
    print(f"CONCLUIDO! Total: {len(questoes)} questoes")
    print(f"Arquivo: {OUTPUT_JSON}")
    print("="*80)


if __name__ == '__main__':
    main()
