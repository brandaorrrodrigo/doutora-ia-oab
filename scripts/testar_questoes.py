#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testador Interativo de Questões OAB
Permite visualizar e testar questões aleatórias
"""

import json
import random
from pathlib import Path


class TestadorQuestoes:
    def __init__(self, arquivo):
        self.arquivo = arquivo
        self.questoes = []
        self.acertos = 0
        self.erros = 0

    def carregar(self):
        """Carrega questões."""
        with open(self.arquivo, 'r', encoding='utf-8') as f:
            self.questoes = json.load(f)
        print(f"Carregadas {len(self.questoes)} questoes\n")

    def mostrar_questao(self, questao):
        """Mostra uma questão formatada."""
        print("\n" + "="*80)
        print(f"QUESTAO {questao['numero']}")
        print("="*80 + "\n")

        print(questao['pergunta'])
        print()

        for letra in sorted(questao['alternativas'].keys()):
            print(f"({letra}) {questao['alternativas'][letra]}")
            print()

    def testar_questao(self, questao):
        """Testa uma questão com o usuário."""
        self.mostrar_questao(questao)

        resposta = input("Sua resposta (A/B/C/D/E ou 'q' para sair): ").upper().strip()

        if resposta == 'Q':
            return False

        if resposta == questao['gabarito']:
            print("\n*** CORRETO! ***")
            self.acertos += 1
        else:
            print(f"\n*** INCORRETO! A resposta correta e: {questao['gabarito']} ***")
            self.erros += 1

        input("\nPressione ENTER para continuar...")
        return True

    def modo_teste_aleatorio(self, quantidade=10):
        """Modo de teste com questões aleatórias."""
        print("="*80)
        print(f"MODO TESTE - {quantidade} QUESTOES ALEATORIAS")
        print("="*80)

        questoes_selecionadas = random.sample(self.questoes, min(quantidade, len(self.questoes)))

        for i, questao in enumerate(questoes_selecionadas, 1):
            print(f"\n>>> Questao {i} de {quantidade}\n")

            if not self.testar_questao(questao):
                break

        self.mostrar_resultado()

    def modo_visualizacao(self):
        """Modo de visualização de questões."""
        print("="*80)
        print("MODO VISUALIZACAO")
        print("="*80)
        print("\nOpcoes:")
        print("  1 - Ver questao especifica (digite o numero)")
        print("  2 - Ver questao aleatoria")
        print("  3 - Ver primeiras 5 questoes")
        print("  4 - Voltar ao menu")
        print()

        opcao = input("Escolha: ").strip()

        if opcao == '1':
            try:
                num = int(input("Numero da questao: "))
                if 1 <= num <= len(self.questoes):
                    questao = self.questoes[num - 1]
                    self.mostrar_questao(questao)
                    print(f"GABARITO: {questao['gabarito']}")
                else:
                    print("Numero invalido!")
            except:
                print("Entrada invalida!")

        elif opcao == '2':
            questao = random.choice(self.questoes)
            self.mostrar_questao(questao)
            print(f"GABARITO: {questao['gabarito']}")

        elif opcao == '3':
            for questao in self.questoes[:5]:
                self.mostrar_questao(questao)
                print(f"GABARITO: {questao['gabarito']}")
                print()

        input("\nPressione ENTER para continuar...")

    def mostrar_resultado(self):
        """Mostra resultado final."""
        total = self.acertos + self.erros
        if total == 0:
            return

        print("\n" + "="*80)
        print("RESULTADO FINAL")
        print("="*80)
        print(f"\nTotal de questoes: {total}")
        print(f"Acertos: {self.acertos}")
        print(f"Erros: {self.erros}")
        print(f"Percentual de acerto: {(self.acertos/total)*100:.1f}%")
        print()

    def menu_principal(self):
        """Menu principal."""
        while True:
            print("\n" + "="*80)
            print("TESTADOR DE QUESTOES OAB")
            print("="*80)
            print(f"\nBanco de dados: {len(self.questoes)} questoes")
            print(f"Acertos ate agora: {self.acertos} | Erros: {self.erros}")
            print("\nOpcoes:")
            print("  1 - Teste rapido (10 questoes)")
            print("  2 - Teste medio (20 questoes)")
            print("  3 - Teste longo (50 questoes)")
            print("  4 - Modo visualizacao")
            print("  5 - Resetar contador")
            print("  0 - Sair")
            print()

            opcao = input("Escolha uma opcao: ").strip()

            if opcao == '0':
                print("\nAte logo!")
                break
            elif opcao == '1':
                self.modo_teste_aleatorio(10)
            elif opcao == '2':
                self.modo_teste_aleatorio(20)
            elif opcao == '3':
                self.modo_teste_aleatorio(50)
            elif opcao == '4':
                self.modo_visualizacao()
            elif opcao == '5':
                self.acertos = 0
                self.erros = 0
                print("\nContador resetado!")
            else:
                print("\nOpcao invalida!")


def main():
    ARQUIVO = r"C:\Users\NFC\questoes_oab_final.json"

    if not Path(ARQUIVO).exists():
        print(f"ERRO: Arquivo nao encontrado: {ARQUIVO}")
        return

    testador = TestadorQuestoes(ARQUIVO)
    testador.carregar()
    testador.menu_principal()


if __name__ == '__main__':
    main()
