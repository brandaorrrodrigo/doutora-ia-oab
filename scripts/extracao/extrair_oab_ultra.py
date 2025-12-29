#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERSÃO ULTRA - Extração de alta qualidade
Foco em limpeza e precisão
"""

import re
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber não instalado")
    sys.exit(1)


class ExtractorOABUltra:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.questoes = []

    def limpar_texto(self, texto):
        """Limpeza avançada de texto."""
        if not texto:
            return ""

        # Substituir tabs e múltiplos espaços
        texto = texto.replace('\t', ' ')
        texto = re.sub(r'\s+', ' ', texto)

        return texto.strip()

    def eh_linha_ignorar(self, linha):
        """Identifica linhas que devem ser ignoradas."""
        if not linha or len(linha.strip()) < 3:
            return True

        padroes_ignorar = [
            r'^\d+\s*$',  # Só número
            r'^[A-Z\s]{40,}$',  # Linha toda maiúscula longa
            r'ARTHUR TRIGUEIROS',
            r'ÉTICA PROFISSIONAL',
            r'DIREITO (CIVIL|PENAL|CONSTITUCIONAL)',
            r'COMO PASSAR.*OAB',
            r'^\d+\.\s+[A-Z]+.*$',  # Numeração de capítulo
            r'www\.',
            r'^Página\s+\d+',
        ]

        for padrao in padroes_ignorar:
            if re.search(padrao, linha, re.IGNORECASE):
                return True

        return False

    def eh_comentario(self, linha):
        """Identifica se linha é comentário/explicação."""
        padroes_comentario = [
            r'^(A|B|C|D|E):\s*(correta|incorreta)',
            r'^Nos termos',
            r'^Como visto',
            r'^Vamos',
            r'^Perceba',
            r'^Destaque-se',
            r'^Trata-se',
            r'^A alternativa',
            r'^\d+\s+[A-Z\s]+\s+[A-Z\s]+$',  # Cabeçalho estranho
        ]

        for padrao in padroes_comentario:
            if re.search(padrao, linha, re.IGNORECASE):
                return True

        return False

    def extrair_questoes(self):
        """Extrai questões do PDF."""
        print(f"Abrindo PDF: {self.pdf_path}\n")

        with pdfplumber.open(self.pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            print(f"Total de páginas: {total_paginas}\n")

            # Processar página por página
            for i in range(15, total_paginas):
                if (i - 15) % 100 == 0:
                    print(f"Processando página {i + 1}/{total_paginas}... (Questões: {len(self.questoes)})")

                texto = pdf.pages[i].extract_text()
                if texto:
                    self.processar_pagina_melhorada(texto)

        print(f"\nTotal de questões extraídas: {len(self.questoes)}")

    def processar_pagina_melhorada(self, texto):
        """Processa uma página com algoritmo melhorado."""
        linhas = texto.split('\n')
        linhas_limpas = []

        for linha in linhas:
            linha_limpa = self.limpar_texto(linha)
            if linha_limpa and not self.eh_linha_ignorar(linha_limpa):
                linhas_limpas.append(linha_limpa)

        # Buscar blocos de questões
        i = 0
        while i < len(linhas_limpas):
            resultado = self.extrair_questao_melhorada(linhas_limpas, i)

            if resultado:
                questao, linhas_usadas = resultado
                self.questoes.append(questao)
                i += linhas_usadas
            else:
                i += 1

    def extrair_questao_melhorada(self, linhas, inicio):
        """Extração melhorada de questão."""
        # Fase 1: Encontrar bloco de alternativas
        bloco_alternativas = self.encontrar_bloco_alternativas(linhas, inicio)

        if not bloco_alternativas:
            return None

        idx_inicio_alt = bloco_alternativas['inicio']
        idx_fim_alt = bloco_alternativas['fim']
        alternativas = bloco_alternativas['alternativas']

        # Fase 2: Extrair enunciado (linhas antes das alternativas)
        enunciado = self.extrair_enunciado_limpo(linhas, idx_inicio_alt)

        if not enunciado or len(enunciado) < 40:
            return None

        # Fase 3: Buscar gabarito (linhas depois das alternativas)
        gabarito = self.buscar_gabarito_preciso(linhas, idx_fim_alt)

        # Fase 4: Limpar alternativas
        alternativas_limpas = self.limpar_alternativas(alternativas)

        # Validação final
        if len(alternativas_limpas) < 4:
            return None

        for letra, texto in alternativas_limpas.items():
            if len(texto) < 10:
                return None

        questao = {
            'numero': len(self.questoes) + 1,
            'pergunta': enunciado,
            'alternativas': alternativas_limpas,
            'gabarito': gabarito
        }

        linhas_usadas = idx_fim_alt - inicio + 25

        return questao, linhas_usadas

    def encontrar_bloco_alternativas(self, linhas, inicio):
        """Encontra um bloco completo de alternativas."""
        # Procurar alternativa (A)
        idx_a = None

        for offset in range(min(30, len(linhas) - inicio)):
            linha = linhas[inicio + offset]

            if re.match(r'^\(A\)\s+.{10,}', linha):
                idx_a = inicio + offset
                break

        if idx_a is None:
            return None

        # A partir de (A), coletar alternativas em sequência
        alternativas = {}
        indices = {}

        i = idx_a
        letras_esperadas = ['A', 'B', 'C', 'D', 'E']
        letra_atual_idx = 0

        while i < len(linhas) and letra_atual_idx < len(letras_esperadas):
            linha = linhas[i]

            letra_esperada = letras_esperadas[letra_atual_idx]
            pattern = rf'^\({letra_esperada}\)\s+(.+)$'
            match = re.match(pattern, linha)

            if match:
                texto = match.group(1)
                alternativas[letra_esperada] = [texto]
                indices[letra_esperada] = i
                letra_atual_idx += 1
            elif letra_atual_idx > 0:
                # Já começamos a capturar, pode ser continuação
                letra_anterior = letras_esperadas[letra_atual_idx - 1]

                # Verificar se não é início de outra alternativa ou comentário
                if not re.match(r'^\([A-E]\)', linha) and not self.eh_comentario(linha):
                    if len(linha) > 15:
                        alternativas[letra_anterior].append(linha)

            i += 1

            # Parar se encontrar gabarito
            if 'otirabaG' in linha or re.search(r'Gabarito', linha, re.IGNORECASE):
                break

            # Limite de busca
            if i > idx_a + 40:
                break

        # Precisa ter pelo menos A, B, C, D
        if len(alternativas) < 4:
            return None

        # Juntar textos das alternativas
        alternativas_texto = {}
        for letra, textos in alternativas.items():
            alternativas_texto[letra] = ' '.join(textos)

        return {
            'inicio': idx_a,
            'fim': max(indices.values()),
            'alternativas': alternativas_texto
        }

    def extrair_enunciado_limpo(self, linhas, idx_primeira_alternativa):
        """Extrai enunciado sem comentários."""
        # Coletar linhas antes da primeira alternativa
        candidatas = []

        inicio = max(0, idx_primeira_alternativa - 25)

        for i in range(inicio, idx_primeira_alternativa):
            linha = linhas[i]

            # Ignorar comentários e linhas muito curtas
            if self.eh_comentario(linha):
                continue

            if len(linha) < 20:
                continue

            # Ignorar linhas com referências a OAB/Exame se houver outras
            if 'OAB/Exame' in linha and len(candidatas) > 3:
                continue

            candidatas.append(linha)

        # Pegar últimas 10 linhas (enunciado geralmente está no final)
        enunciado_linhas = candidatas[-10:]

        # Juntar
        enunciado = ' '.join(enunciado_linhas)

        # Limpeza profunda
        enunciado = self.limpar_enunciado_profundo(enunciado)

        return enunciado

    def limpar_enunciado_profundo(self, texto):
        """Limpeza profunda do enunciado."""
        # Remover referências OAB/Exame
        texto = re.sub(r'\(OAB/Exame[^)]*\)', '', texto)

        # Remover comentários inline
        texto = re.sub(r'(A|B|C|D|E):\s*(correta|incorreta)[^.]*\.', '', texto, flags=re.IGNORECASE)

        # Remover citações legais longas
        texto = re.sub(r'(art\.|artigo|§)\s*\d+[^.]{30,}?\.', '', texto, flags=re.IGNORECASE)

        # Remover frases começando com palavras-chave de comentário
        texto = re.sub(r'(Nos termos|Como visto|Vamos|Perceba|Destaque-se)[^.]*\.', '', texto, flags=re.IGNORECASE)

        # Remover menções a outras questões
        texto = re.sub(r'(alternativa|questão)\s+["""]?[A-E]["""]?[^.]*\.', '', texto, flags=re.IGNORECASE)

        return self.limpar_texto(texto)

    def limpar_alternativas(self, alternativas_dict):
        """Limpa textos das alternativas."""
        limpas = {}

        for letra, texto in alternativas_dict.items():
            # Remover comentários
            texto = re.sub(r'\s+(A|B|C|D|E):\s*(correta|incorreta).*', '', texto, flags=re.IGNORECASE)

            # Remover frases de comentário
            texto = re.sub(r'(Nos termos|Como visto|Perceba|Destaque-se).*', '', texto, flags=re.IGNORECASE)

            # Remover citações muito longas
            texto = re.sub(r'\([^)]{100,}\)', '', texto)

            # Se encontrar início de nova questão dentro da alternativa, cortar
            if 'OAB/Exame Unificado' in texto:
                partes = texto.split('OAB/Exame Unificado')
                texto = partes[0]

            texto_limpo = self.limpar_texto(texto)
            limpas[letra] = texto_limpo

        return limpas

    def buscar_gabarito_preciso(self, linhas, idx_ultima_alt):
        """Busca gabarito com precisão."""
        for offset in range(1, min(30, len(linhas) - idx_ultima_alt)):
            linha = linhas[idx_ultima_alt + offset]

            # Padrão: "X" otirabaG
            match = re.search(r'["""]([A-E])["""]?\s+otirabaG', linha, re.IGNORECASE)
            if match:
                return match.group(1).upper()

            # Padrão: Gabarito "X" ou Gabarito: X
            match = re.search(r'Gabarito[:\s]+["""]?([A-E])["""]?', linha, re.IGNORECASE)
            if match:
                return match.group(1).upper()

            # Padrão: X: correta
            match = re.search(r'^([A-E]):\s*correta', linha, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        # Default
        return 'A'

    def salvar_json(self, output_path):
        """Salva em JSON."""
        # Renumerar
        for i, q in enumerate(self.questoes, 1):
            q['numero'] = i

        print(f"\nSalvando {len(self.questoes)} questões em: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.questoes, f, ensure_ascii=False, indent=2)

        print("✓ Arquivo salvo com sucesso!")
        return self.questoes


def main():
    PDF_PATH = r"D:\doutora-ia\direito\20-material-oab\Como Passar Na OAB 5.000 Questo -.pdf"
    OUTPUT_JSON = r"C:\Users\NFC\questoes_oab_ultra.json"

    if not Path(PDF_PATH).exists():
        print("ERRO: Arquivo não encontrado")
        sys.exit(1)

    print("="*80)
    print("EXTRATOR ULTRA - ALTA QUALIDADE")
    print("="*80 + "\n")

    extrator = ExtractorOABUltra(PDF_PATH)
    extrator.extrair_questoes()
    questoes = extrator.salvar_json(OUTPUT_JSON)

    # Mostrar exemplos
    print("\n" + "="*80)
    print("EXEMPLOS DE QUESTÕES EXTRAÍDAS:")
    print("="*80)

    exemplos_idx = [0, 10, 50, len(questoes)//2, -10]

    for idx in exemplos_idx[:3]:  # Mostrar 3 exemplos
        if 0 <= idx < len(questoes) or idx == -10:
            q = questoes[idx]
            print(f"\n{'─'*80}")
            print(f"QUESTÃO {q['numero']}")
            print('─'*80)
            print(f"\nPERGUNTA:\n{q['pergunta'][:200]}...")
            print(f"\nALTERNATIVAS:")
            for letra in sorted(q['alternativas'].keys()):
                print(f"  ({letra}) {q['alternativas'][letra][:80]}...")
            print(f"\nGABARITO: {q['gabarito']}")

    print("\n" + "="*80)
    print(f"✓ CONCLUÍDO!")
    print(f"Total de questões: {len(questoes)}")
    print(f"Arquivo: {OUTPUT_JSON}")
    print("="*80)


if __name__ == '__main__':
    main()
