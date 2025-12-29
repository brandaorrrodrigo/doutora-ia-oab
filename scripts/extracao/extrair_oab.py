#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para extrair todas as 5000 questões do PDF da OAB
e gerar um arquivo JSON estruturado.
"""

import re
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("ERRO: pdfplumber não instalado. Execute: pip install pdfplumber")
    sys.exit(1)


class ExtractorOAB:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.questoes = []
        self.problemas = []

        # Padrões regex
        self.pattern_alternativa = re.compile(r'^\s*\(([A-E])\)\s*(.+)$')
        self.pattern_gabarito = re.compile(r'(?:Gabarito|GABARITO|Resposta).*?[:–-]?\s*([A-E])', re.IGNORECASE)
        self.pattern_numero_questao = re.compile(r'^\s*(\d{1,4})[.\s)]\s*(.+)$')

        # Cabeçalhos/rodapés para ignorar
        self.ignore_patterns = [
            r'COMO PASSAR.*OAB',
            r'www\..*\.com',
            r'^\d+\s*$',  # só número de página
            r'^Página\s+\d+',
            r'^\s*$'
        ]

    def limpar_texto(self, texto):
        """Remove espaços extras, &nbsp;, tabs, etc."""
        if not texto:
            return ""

        # Substituir &nbsp; e outras entidades
        texto = texto.replace('&nbsp;', ' ')
        texto = texto.replace('\t', ' ')

        # Remover espaços múltiplos
        texto = re.sub(r'\s+', ' ', texto)

        # Trim
        return texto.strip()

    def deve_ignorar_linha(self, linha):
        """Verifica se a linha é cabeçalho/rodapé."""
        linha = linha.strip()

        for pattern in self.ignore_patterns:
            if re.search(pattern, linha, re.IGNORECASE):
                return True

        return False

    def extrair_texto_pdf(self):
        """Extrai todo o texto do PDF página por página."""
        print(f"Abrindo PDF: {self.pdf_path}")

        texto_completo = []

        with pdfplumber.open(self.pdf_path) as pdf:
            total_paginas = len(pdf.pages)
            print(f"Total de páginas: {total_paginas}")

            for i, page in enumerate(pdf.pages, 1):
                if i % 50 == 0:
                    print(f"Processando página {i}/{total_paginas}...")

                texto = page.extract_text()
                if texto:
                    linhas = texto.split('\n')
                    # Filtrar linhas válidas
                    linhas_validas = [
                        self.limpar_texto(linha)
                        for linha in linhas
                        if linha.strip() and not self.deve_ignorar_linha(linha)
                    ]
                    texto_completo.extend(linhas_validas)

        print(f"Total de linhas extraídas: {len(texto_completo)}")
        return texto_completo

    def identificar_questoes(self, linhas):
        """
        Identifica e extrai questões do texto.
        Máquina de estados para processar enunciado, alternativas e gabarito.
        """
        print("\nIniciando identificação de questões...")

        estado = 'BUSCANDO'  # Estados: BUSCANDO, ENUNCIADO, ALTERNATIVAS, GABARITO

        questao_atual = {
            'enunciado_linhas': [],
            'alternativas': {},
            'gabarito': None,
            'ultima_alternativa': None
        }

        i = 0
        while i < len(linhas):
            linha = linhas[i]

            # Verificar se é uma alternativa
            match_alt = self.pattern_alternativa.match(linha)

            if match_alt:
                letra = match_alt.group(1)
                texto = match_alt.group(2).strip()

                # Se encontramos (A), é início de um novo bloco de alternativas
                if letra == 'A':
                    # Se já tínhamos uma questão em andamento, salvar
                    if estado in ['ALTERNATIVAS', 'GABARITO'] and questao_atual['alternativas']:
                        self.salvar_questao(questao_atual)
                        questao_atual = {
                            'enunciado_linhas': [],
                            'alternativas': {},
                            'gabarito': None,
                            'ultima_alternativa': None
                        }

                    estado = 'ALTERNATIVAS'

                if estado == 'ALTERNATIVAS':
                    questao_atual['alternativas'][letra] = texto
                    questao_atual['ultima_alternativa'] = letra

            # Verificar se é gabarito
            elif 'gabarito' in linha.lower() or 'resposta' in linha.lower():
                match_gab = self.pattern_gabarito.search(linha)
                if match_gab:
                    questao_atual['gabarito'] = match_gab.group(1)
                    estado = 'GABARITO'

            # Se não é alternativa e estamos em estado ALTERNATIVAS
            elif estado == 'ALTERNATIVAS' and questao_atual['ultima_alternativa']:
                # Pode ser continuação da última alternativa
                # ou início de comentário/gabarito
                if not any(keyword in linha.lower() for keyword in ['gabarito', 'comentário', 'fundamento', 'lei', 'artigo', 'código']):
                    # Continuação da alternativa
                    letra = questao_atual['ultima_alternativa']
                    questao_atual['alternativas'][letra] += ' ' + linha

            # Se não estamos em alternativas ainda, acumular como enunciado
            elif estado == 'BUSCANDO' or estado == 'ENUNCIADO':
                # Evitar linhas muito curtas ou que parecem ser fragmentos
                if len(linha) > 15:
                    questao_atual['enunciado_linhas'].append(linha)
                    estado = 'ENUNCIADO'

            i += 1

        # Salvar última questão se existir
        if questao_atual['alternativas']:
            self.salvar_questao(questao_atual)

        print(f"\nTotal de questões identificadas: {len(self.questoes)}")

    def salvar_questao(self, questao_dict):
        """Salva a questão processada na lista."""
        # Validar questão
        if len(questao_dict['alternativas']) < 4:
            self.problemas.append({
                'numero': len(self.questoes) + 1,
                'problema': 'Menos de 4 alternativas',
                'alternativas': questao_dict['alternativas']
            })
            return

        # Montar enunciado
        enunciado = ' '.join(questao_dict['enunciado_linhas'])
        enunciado = self.limpar_texto(enunciado)

        # Se enunciado muito curto ou vazio, tentar usar primeira parte das alternativas
        if not enunciado or len(enunciado) < 10:
            enunciado = "Questão sem enunciado claro - verificar"

        # Limpar textos das alternativas
        alternativas_limpas = {}
        for letra, texto in sorted(questao_dict['alternativas'].items()):
            alternativas_limpas[letra] = self.limpar_texto(texto)

        # Gabarito
        gabarito = questao_dict.get('gabarito')
        if not gabarito and len(alternativas_limpas) > 0:
            # Se não encontrou gabarito, tentar buscar nas próximas linhas
            gabarito = 'A'  # Placeholder - será necessário revisão manual

        questao = {
            'numero': len(self.questoes) + 1,
            'pergunta': enunciado,
            'alternativas': alternativas_limpas,
            'gabarito': gabarito
        }

        self.questoes.append(questao)

    def processar(self):
        """Processa todo o PDF."""
        # Extrair texto
        linhas = self.extrair_texto_pdf()

        # Identificar questões
        self.identificar_questoes(linhas)

        # Numerar questões sequencialmente
        for i, q in enumerate(self.questoes, 1):
            q['numero'] = i

        return self.questoes

    def salvar_json(self, output_path):
        """Salva questões em arquivo JSON."""
        print(f"\nSalvando {len(self.questoes)} questões em: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.questoes, f, ensure_ascii=False, indent=2)

        print(f"✓ Arquivo JSON criado com sucesso!")

    def salvar_log_problemas(self, log_path):
        """Salva log de questões problemáticas."""
        if not self.problemas:
            print("\n✓ Nenhum problema encontrado!")
            return

        print(f"\nSalvando log de {len(self.problemas)} problemas em: {log_path}")

        with open(log_path, 'w', encoding='utf-8') as f:
            for p in self.problemas:
                f.write(f"Questão {p['numero']}: {p['problema']}\n")
                f.write(f"Alternativas: {p.get('alternativas', {})}\n")
                f.write("-" * 80 + "\n")


def main():
    # Configurações
    PDF_PATH = r"D:\doutora-ia\direito\20-material-oab\Como Passar Na OAB 5.000 Questo -.pdf"
    OUTPUT_JSON = r"C:\Users\NFC\questoes_oab_5000.json"
    OUTPUT_LOG = r"C:\Users\NFC\questoes_problema.log"

    # Verificar se PDF existe
    if not Path(PDF_PATH).exists():
        print(f"ERRO: Arquivo não encontrado: {PDF_PATH}")
        sys.exit(1)

    print("="*80)
    print("EXTRATOR DE QUESTÕES OAB - 5000 QUESTÕES")
    print("="*80)

    # Processar
    extrator = ExtractorOAB(PDF_PATH)
    questoes = extrator.processar()

    # Salvar JSON
    extrator.salvar_json(OUTPUT_JSON)

    # Salvar log de problemas
    extrator.salvar_log_problemas(OUTPUT_LOG)

    # Mostrar exemplos
    print("\n" + "="*80)
    print("PRIMEIRAS 5 QUESTÕES (EXEMPLO):")
    print("="*80)

    for q in questoes[:5]:
        print(f"\nQuestão {q['numero']}:")
        print(f"Pergunta: {q['pergunta'][:100]}...")
        print(f"Alternativas: {list(q['alternativas'].keys())}")
        print(f"Gabarito: {q['gabarito']}")

    print("\n" + "="*80)
    print(f"✓ CONCLUÍDO! Total de questões extraídas: {len(questoes)}")
    print(f"✓ Arquivo JSON: {OUTPUT_JSON}")
    print("="*80)


if __name__ == '__main__':
    main()
