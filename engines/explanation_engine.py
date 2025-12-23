"""
JURIS_IA_CORE_V1 - EXPLANATION ENGINE
Motor de Explicação Multinível para Conteúdo Jurídico

Este módulo gera explicações adaptativas em 4 níveis de profundidade:
- Nível 1: TÉCNICA (para quem domina)
- Nível 2: DIDÁTICA (explicação simples)
- Nível 3: ANALOGIA (compreensão intuitiva)
- Nível 4: EXEMPLO PRÁTICO (aplicação real)

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
import re
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, asdict
from enum import Enum


# ============================================================
# TIPOS E ENUMS
# ============================================================

class ExplanationLevel(Enum):
    """Níveis de explicação disponíveis"""
    TECNICA = 1      # Técnico, para quem domina
    DIDATICA = 2     # Didático, explicação simples
    ANALOGIA = 3     # Analogia, compreensão intuitiva
    PRATICA = 4      # Exemplo prático, aplicação real


class StudentProfile(Enum):
    """Perfil do estudante baseado em desempenho"""
    INICIANTE = "iniciante"          # < 40% acertos
    INTERMEDIARIO = "intermediario"  # 40-70% acertos
    AVANCADO = "avancado"           # > 70% acertos


@dataclass
class Explanation:
    """Estrutura de uma explicação"""
    nivel: int
    tipo: str
    conteudo: str
    conceitos_chave: List[str]
    artigos_relacionados: List[str]
    jurisprudencia: Optional[List[str]] = None
    analogia: Optional[str] = None
    exemplo_pratico: Optional[str] = None


@dataclass
class MultiLevelExplanation:
    """Conjunto completo de explicações multinível"""
    topico: str
    disciplina: str
    nivel_1_tecnica: Explanation
    nivel_2_didatica: Explanation
    nivel_3_analogia: Explanation
    nivel_4_pratica: Explanation
    pegadinhas_comuns: List[str]
    dicas_oab: List[str]


# ============================================================
# EXPLANATION ENGINE
# ============================================================

class ExplanationEngine:
    """
    Motor de geração de explicações multinível para conteúdo jurídico.

    Funcionalidades:
    - Gera explicações adaptadas ao nível do estudante
    - Identifica conceitos-chave necessários
    - Relaciona artigos de lei pertinentes
    - Cria analogias pedagógicas
    - Fornece exemplos práticos
    """

    def __init__(self, ontologia_path: str = None, lei_seca_path: str = None):
        """
        Inicializa o motor de explicação.

        Args:
            ontologia_path: Caminho para base de ontologia jurídica
            lei_seca_path: Caminho para base de lei seca estruturada
        """
        self.ontologia_path = ontologia_path
        self.lei_seca_path = lei_seca_path
        self.conceitos_cache: Dict = {}
        self.artigos_cache: Dict = {}

    def gerar_explicacao_adaptativa(
        self,
        topico: str,
        contexto: str,
        perfil_estudante: StudentProfile = StudentProfile.INTERMEDIARIO,
        nivel_preferido: Optional[ExplanationLevel] = None
    ) -> Explanation:
        """
        Gera uma explicação adaptada ao perfil do estudante.

        Args:
            topico: Tópico a ser explicado
            contexto: Contexto da dúvida (questão, erro, etc)
            perfil_estudante: Perfil do estudante (iniciante/intermediario/avancado)
            nivel_preferido: Nível específico solicitado (opcional)

        Returns:
            Explanation adaptada ao perfil
        """
        # Determina nível ideal baseado no perfil
        if nivel_preferido:
            nivel = nivel_preferido
        else:
            nivel = self._determinar_nivel_ideal(perfil_estudante)

        # Gera explicação no nível apropriado
        return self._gerar_explicacao_nivel(topico, contexto, nivel)

    def gerar_explicacao_completa(
        self,
        topico: str,
        disciplina: str,
        contexto: str
    ) -> MultiLevelExplanation:
        """
        Gera conjunto completo de explicações (4 níveis).

        Args:
            topico: Tópico a ser explicado
            disciplina: Disciplina jurídica (Penal, Civil, etc)
            contexto: Contexto da explicação

        Returns:
            MultiLevelExplanation com todos os 4 níveis
        """
        nivel_1 = self._gerar_explicacao_nivel(
            topico, contexto, ExplanationLevel.TECNICA
        )
        nivel_2 = self._gerar_explicacao_nivel(
            topico, contexto, ExplanationLevel.DIDATICA
        )
        nivel_3 = self._gerar_explicacao_nivel(
            topico, contexto, ExplanationLevel.ANALOGIA
        )
        nivel_4 = self._gerar_explicacao_nivel(
            topico, contexto, ExplanationLevel.PRATICA
        )

        pegadinhas = self._identificar_pegadinhas(topico, disciplina)
        dicas = self._gerar_dicas_oab(topico, disciplina)

        return MultiLevelExplanation(
            topico=topico,
            disciplina=disciplina,
            nivel_1_tecnica=nivel_1,
            nivel_2_didatica=nivel_2,
            nivel_3_analogia=nivel_3,
            nivel_4_pratica=nivel_4,
            pegadinhas_comuns=pegadinhas,
            dicas_oab=dicas
        )

    def explicar_alternativa_errada(
        self,
        alternativa: str,
        motivo_erro: str,
        nivel: ExplanationLevel = ExplanationLevel.DIDATICA
    ) -> str:
        """
        Explica POR QUE uma alternativa está errada.

        Fundamental: aprender com erros é tão importante quanto acertar.

        Args:
            alternativa: Texto da alternativa errada
            motivo_erro: Razão técnica do erro
            nivel: Nível de explicação desejado

        Returns:
            Explicação clara do erro
        """
        if nivel == ExplanationLevel.TECNICA:
            return self._explicar_erro_tecnico(alternativa, motivo_erro)
        elif nivel == ExplanationLevel.DIDATICA:
            return self._explicar_erro_didatico(alternativa, motivo_erro)
        elif nivel == ExplanationLevel.ANALOGIA:
            return self._explicar_erro_analogia(alternativa, motivo_erro)
        else:  # PRATICA
            return self._explicar_erro_pratico(alternativa, motivo_erro)

    def identificar_conceitos_faltantes(
        self,
        topico: str,
        erro_estudante: str
    ) -> List[str]:
        """
        Identifica quais conceitos fundamentais o estudante não domina.

        Args:
            topico: Tópico da questão/erro
            erro_estudante: Descrição do erro cometido

        Returns:
            Lista de conceitos que precisam ser revisados
        """
        # Extrai conceitos do tópico
        conceitos_necessarios = self._extrair_conceitos_topico(topico)

        # Analisa o erro para identificar gap conceitual
        conceitos_faltantes = []
        for conceito in conceitos_necessarios:
            if self._conceito_relacionado_ao_erro(conceito, erro_estudante):
                conceitos_faltantes.append(conceito)

        return conceitos_faltantes

    def gerar_progressao_didatica(
        self,
        conceito_complexo: str,
        nivel_atual: StudentProfile
    ) -> List[str]:
        """
        Gera sequência didática para construir compreensão progressiva.

        Args:
            conceito_complexo: Conceito difícil a ser ensinado
            nivel_atual: Nível atual do estudante

        Returns:
            Lista ordenada de passos didáticos
        """
        progressao = []

        # Passo 1: Conceitos fundamentais
        progressao.append(f"FUNDAMENTO: {self._extrair_fundamento(conceito_complexo)}")

        # Passo 2: Definição simples
        progressao.append(f"DEFINIÇÃO: {self._definir_simples(conceito_complexo)}")

        # Passo 3: Exemplo concreto
        progressao.append(f"EXEMPLO: {self._gerar_exemplo_concreto(conceito_complexo)}")

        # Passo 4: Distinções importantes
        progressao.append(f"DISTINÇÕES: {self._gerar_distincoes(conceito_complexo)}")

        # Passo 5: Aplicação OAB
        progressao.append(f"NA OAB: {self._aplicacao_oab(conceito_complexo)}")

        return progressao

    # ============================================================
    # MÉTODOS PRIVADOS - GERAÇÃO DE EXPLICAÇÕES
    # ============================================================

    def _determinar_nivel_ideal(self, perfil: StudentProfile) -> ExplanationLevel:
        """Determina nível ideal de explicação baseado no perfil"""
        if perfil == StudentProfile.INICIANTE:
            return ExplanationLevel.PRATICA  # Nível 4: exemplo prático
        elif perfil == StudentProfile.INTERMEDIARIO:
            return ExplanationLevel.DIDATICA  # Nível 2: didático
        else:  # AVANCADO
            return ExplanationLevel.TECNICA  # Nível 1: técnico

    def _gerar_explicacao_nivel(
        self,
        topico: str,
        contexto: str,
        nivel: ExplanationLevel
    ) -> Explanation:
        """Gera explicação em um nível específico"""

        if nivel == ExplanationLevel.TECNICA:
            return self._gerar_explicacao_tecnica(topico, contexto)
        elif nivel == ExplanationLevel.DIDATICA:
            return self._gerar_explicacao_didatica(topico, contexto)
        elif nivel == ExplanationLevel.ANALOGIA:
            return self._gerar_explicacao_analogia(topico, contexto)
        else:  # PRATICA
            return self._gerar_explicacao_pratica(topico, contexto)

    def _gerar_explicacao_tecnica(self, topico: str, contexto: str) -> Explanation:
        """
        Nível 1: Explicação técnica para quem domina.
        Foco: precisão, citações, doutrina, jurisprudência.
        """
        conceitos = self._extrair_conceitos_topico(topico)
        artigos = self._extrair_artigos_relacionados(topico)

        conteudo = f"""
EXPLICAÇÃO TÉCNICA - {topico}

{contexto}

FUNDAMENTO LEGAL:
{self._formatar_fundamento_legal(artigos)}

DOUTRINA:
{self._extrair_doutrina(topico)}

ELEMENTOS ESSENCIAIS:
{self._listar_elementos_essenciais(topico)}

DISTINÇÕES IMPORTANTES:
{self._gerar_distincoes(topico)}
        """.strip()

        return Explanation(
            nivel=1,
            tipo="TÉCNICA",
            conteudo=conteudo,
            conceitos_chave=conceitos,
            artigos_relacionados=artigos,
            jurisprudencia=self._buscar_jurisprudencia(topico)
        )

    def _gerar_explicacao_didatica(self, topico: str, contexto: str) -> Explanation:
        """
        Nível 2: Explicação didática simples.
        Foco: clareza, linguagem acessível, sem jargão excessivo.
        """
        conceitos = self._extrair_conceitos_topico(topico)
        artigos = self._extrair_artigos_relacionados(topico)

        conteudo = f"""
EXPLICAÇÃO DIDÁTICA - {topico}

O QUE É:
{self._definir_simples(topico)}

POR QUE IMPORTA:
{self._explicar_importancia(topico)}

COMO FUNCIONA:
{self._explicar_funcionamento(topico)}

QUANDO APLICAR:
{self._explicar_aplicacao(topico)}

RESUMO EM 3 PONTOS:
{self._resumir_tres_pontos(topico)}
        """.strip()

        return Explanation(
            nivel=2,
            tipo="DIDÁTICA",
            conteudo=conteudo,
            conceitos_chave=conceitos,
            artigos_relacionados=artigos
        )

    def _gerar_explicacao_analogia(self, topico: str, contexto: str) -> Explanation:
        """
        Nível 3: Explicação por analogia.
        Foco: compreensão intuitiva através de comparações.
        """
        conceitos = self._extrair_conceitos_topico(topico)
        artigos = self._extrair_artigos_relacionados(topico)
        analogia = self._criar_analogia(topico)

        conteudo = f"""
EXPLICAÇÃO POR ANALOGIA - {topico}

ANALOGIA:
{analogia}

COMO A ANALOGIA SE RELACIONA COM O DIREITO:
{self._conectar_analogia_direito(topico, analogia)}

DIFERENÇAS IMPORTANTES:
{self._listar_limites_analogia(topico)}
        """.strip()

        return Explanation(
            nivel=3,
            tipo="ANALOGIA",
            conteudo=conteudo,
            conceitos_chave=conceitos,
            artigos_relacionados=artigos,
            analogia=analogia
        )

    def _gerar_explicacao_pratica(self, topico: str, contexto: str) -> Explanation:
        """
        Nível 4: Exemplo prático real.
        Foco: aplicação concreta, casos reais, situações do dia a dia.
        """
        conceitos = self._extrair_conceitos_topico(topico)
        artigos = self._extrair_artigos_relacionados(topico)
        exemplo = self._criar_exemplo_pratico(topico)

        conteudo = f"""
EXPLICAÇÃO PRÁTICA - {topico}

CASO PRÁTICO:
{exemplo}

ANÁLISE DO CASO:
{self._analisar_caso_pratico(topico, exemplo)}

COMO ISSO CAI NA OAB:
{self._conectar_caso_oab(topico)}

DICA PRÁTICA:
{self._gerar_dica_pratica(topico)}
        """.strip()

        return Explanation(
            nivel=4,
            tipo="PRÁTICA",
            conteudo=conteudo,
            conceitos_chave=conceitos,
            artigos_relacionados=artigos,
            exemplo_pratico=exemplo
        )

    # ============================================================
    # MÉTODOS PRIVADOS - ANÁLISE DE ERROS
    # ============================================================

    def _explicar_erro_tecnico(self, alternativa: str, motivo: str) -> str:
        """Explica erro de forma técnica"""
        return f"""
ERRO TÉCNICO:
Alternativa: {alternativa}

INCORREÇÃO: {motivo}

FUNDAMENTO LEGAL: {self._extrair_fundamento_erro(motivo)}

CORREÇÃO: {self._corrigir_tecnicamente(alternativa, motivo)}
        """.strip()

    def _explicar_erro_didatico(self, alternativa: str, motivo: str) -> str:
        """Explica erro de forma didática"""
        return f"""
POR QUE ESTÁ ERRADA:
"{alternativa}"

O ERRO: {self._simplificar_erro(motivo)}

FORMA CORRETA: {self._apresentar_forma_correta(alternativa, motivo)}

COMO LEMBRAR: {self._criar_mnemonica_erro(motivo)}
        """.strip()

    def _explicar_erro_analogia(self, alternativa: str, motivo: str) -> str:
        """Explica erro usando analogia"""
        analogia = self._criar_analogia_erro(motivo)
        return f"""
PENSANDO POR ANALOGIA:
Esta alternativa diz: "{alternativa}"

{analogia}

Por isso está errada: {self._conectar_analogia_erro(motivo, analogia)}
        """.strip()

    def _explicar_erro_pratico(self, alternativa: str, motivo: str) -> str:
        """Explica erro com exemplo prático"""
        exemplo = self._criar_exemplo_erro(motivo)
        return f"""
EXEMPLO PRÁTICO DO ERRO:
A alternativa afirma: "{alternativa}"

SITUAÇÃO REAL:
{exemplo}

VEJA O PROBLEMA: {self._mostrar_problema_pratico(alternativa, exemplo)}

NA PRÁTICA SERIA: {self._mostrar_correto_pratico(motivo)}
        """.strip()

    # ============================================================
    # MÉTODOS PRIVADOS - UTILITÁRIOS
    # ============================================================

    def _extrair_conceitos_topico(self, topico: str) -> List[str]:
        """Extrai conceitos-chave do tópico"""
        # Em produção, consultaria ontologia jurídica
        # Por ora, retorna lista básica
        conceitos_base = {
            "dolo": ["dolo", "vontade", "consciência", "intenção"],
            "culpa": ["culpa", "negligência", "imprudência", "imperícia"],
            "legítima defesa": ["legítima defesa", "excludente", "agressão injusta"],
            "petição inicial": ["petição", "causa de pedir", "pedido", "partes"],
        }

        for chave, conceitos in conceitos_base.items():
            if chave.lower() in topico.lower():
                return conceitos

        return [topico]

    def _extrair_artigos_relacionados(self, topico: str) -> List[str]:
        """Extrai artigos de lei relacionados"""
        # Em produção, consultaria base de lei seca
        artigos_base = {
            "dolo": ["CP art. 18, I", "CP art. 20"],
            "culpa": ["CP art. 18, II", "CP art. 13"],
            "legítima defesa": ["CP art. 23, II", "CP art. 25"],
            "petição inicial": ["CPC art. 319", "CPC art. 320", "CPC art. 321"],
        }

        for chave, artigos in artigos_base.items():
            if chave.lower() in topico.lower():
                return artigos

        return []

    def _buscar_jurisprudencia(self, topico: str) -> List[str]:
        """Busca jurisprudência relevante"""
        # Em produção, consultaria base de súmulas e precedentes
        return [
            "Súmula ou precedente relacionado ao tópico",
            "Jurisprudência consolidada sobre o tema"
        ]

    def _identificar_pegadinhas(self, topico: str, disciplina: str) -> List[str]:
        """Identifica pegadinhas comuns da OAB"""
        # Em produção, consultaria base de pegadinhas catalogadas
        return [
            "Pegadinha 1: Confusão entre conceitos similares",
            "Pegadinha 2: Inversão de requisitos",
            "Pegadinha 3: Exceção apresentada como regra"
        ]

    def _gerar_dicas_oab(self, topico: str, disciplina: str) -> List[str]:
        """Gera dicas específicas para OAB"""
        return [
            "Leia TODOS os requisitos antes de responder",
            "Atenção para exceções e ressalvas legais",
            "Não invente: se não sabe, volte ao texto da lei"
        ]

    def _conceito_relacionado_ao_erro(self, conceito: str, erro: str) -> bool:
        """Verifica se conceito está relacionado ao erro"""
        return conceito.lower() in erro.lower()

    def _extrair_fundamento(self, conceito: str) -> str:
        """Extrai fundamento básico do conceito"""
        return f"O fundamento de {conceito} está nos princípios jurídicos de..."

    def _definir_simples(self, topico: str) -> str:
        """Define o tópico de forma simples"""
        return f"{topico} é..."

    def _gerar_exemplo_concreto(self, conceito: str) -> str:
        """Gera exemplo concreto"""
        return f"Exemplo: Imagine uma situação em que..."

    def _gerar_distincoes(self, topico: str) -> str:
        """Gera distinções importantes"""
        return f"Não confunda {topico} com..."

    def _aplicacao_oab(self, conceito: str) -> str:
        """Como o conceito é cobrado na OAB"""
        return f"Na OAB, {conceito} costuma ser cobrado..."

    def _formatar_fundamento_legal(self, artigos: List[str]) -> str:
        """Formata fundamento legal"""
        return "\n".join(f"- {artigo}" for artigo in artigos)

    def _extrair_doutrina(self, topico: str) -> str:
        """Extrai posicionamento doutrinário"""
        return f"Segundo a doutrina majoritária..."

    def _listar_elementos_essenciais(self, topico: str) -> str:
        """Lista elementos essenciais"""
        return "1. Elemento 1\n2. Elemento 2\n3. Elemento 3"

    def _explicar_importancia(self, topico: str) -> str:
        """Explica importância do tópico"""
        return f"{topico} é importante porque..."

    def _explicar_funcionamento(self, topico: str) -> str:
        """Explica como funciona"""
        return f"{topico} funciona da seguinte forma..."

    def _explicar_aplicacao(self, topico: str) -> str:
        """Explica quando aplicar"""
        return f"Aplica-se {topico} quando..."

    def _resumir_tres_pontos(self, topico: str) -> str:
        """Resume em 3 pontos"""
        return "1. Ponto 1\n2. Ponto 2\n3. Ponto 3"

    def _criar_analogia(self, topico: str) -> str:
        """Cria analogia pedagógica"""
        return f"Pense em {topico} como..."

    def _conectar_analogia_direito(self, topico: str, analogia: str) -> str:
        """Conecta analogia com conceito jurídico"""
        return f"Assim como na analogia, no direito..."

    def _listar_limites_analogia(self, topico: str) -> str:
        """Lista limites da analogia"""
        return "Atenção: a analogia não se aplica quando..."

    def _criar_exemplo_pratico(self, topico: str) -> str:
        """Cria exemplo prático"""
        return f"CASO: João, em situação real..."

    def _analisar_caso_pratico(self, topico: str, exemplo: str) -> str:
        """Analisa caso prático"""
        return f"Neste caso, perceba que..."

    def _conectar_caso_oab(self, topico: str) -> str:
        """Conecta caso com prova OAB"""
        return f"A OAB costuma cobrar {topico} em cenários similares..."

    def _gerar_dica_pratica(self, topico: str) -> str:
        """Gera dica prática"""
        return f"Na prova, quando ver {topico}, lembre-se..."

    def _extrair_fundamento_erro(self, motivo: str) -> str:
        """Extrai fundamento legal do erro"""
        return "Artigo X da Lei Y"

    def _corrigir_tecnicamente(self, alternativa: str, motivo: str) -> str:
        """Corrige tecnicamente"""
        return "A forma correta seria..."

    def _simplificar_erro(self, motivo: str) -> str:
        """Simplifica explicação do erro"""
        return f"Em termos simples, o erro é..."

    def _apresentar_forma_correta(self, alternativa: str, motivo: str) -> str:
        """Apresenta forma correta"""
        return "O correto seria afirmar que..."

    def _criar_mnemonica_erro(self, motivo: str) -> str:
        """Cria mnemônica para lembrar"""
        return "Para não errar, lembre: ..."

    def _criar_analogia_erro(self, motivo: str) -> str:
        """Cria analogia do erro"""
        return "É como se você dissesse que..."

    def _conectar_analogia_erro(self, motivo: str, analogia: str) -> str:
        """Conecta analogia com erro"""
        return "E isso não faz sentido porque..."

    def _criar_exemplo_erro(self, motivo: str) -> str:
        """Cria exemplo do erro"""
        return "Imagine se isso fosse verdade..."

    def _mostrar_problema_pratico(self, alternativa: str, exemplo: str) -> str:
        """Mostra problema na prática"""
        return "Perceba o absurdo: se isso fosse verdade..."

    def _mostrar_correto_pratico(self, motivo: str) -> str:
        """Mostra forma correta na prática"""
        return "Na realidade, aconteceria..."


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_engine_explicacao() -> ExplanationEngine:
    """Factory function para criar engine de explicação"""
    return ExplanationEngine(
        ontologia_path="/d/JURIS_IA_CORE_V1/ontologia",
        lei_seca_path="/d/JURIS_IA_CORE_V1/lei_seca"
    )


def explicar_questao_oab(
    questao_id: str,
    alternativa_escolhida: str,
    alternativa_correta: str,
    perfil_estudante: StudentProfile
) -> Dict:
    """
    Explica uma questão OAB de forma adaptativa.

    Args:
        questao_id: ID da questão
        alternativa_escolhida: Alternativa que o aluno escolheu
        alternativa_correta: Alternativa correta
        perfil_estudante: Perfil do estudante

    Returns:
        Dict com explicações detalhadas
    """
    engine = criar_engine_explicacao()

    # Se errou, explica o erro
    if alternativa_escolhida != alternativa_correta:
        explicacao_erro = engine.explicar_alternativa_errada(
            alternativa=alternativa_escolhida,
            motivo_erro="Análise do erro específico",
            nivel=ExplanationLevel.DIDATICA
        )

        # Identifica conceitos faltantes
        conceitos_faltantes = engine.identificar_conceitos_faltantes(
            topico="Tópico da questão",
            erro_estudante=alternativa_escolhida
        )

        return {
            "resultado": "ERRO",
            "explicacao_erro": explicacao_erro,
            "explicacao_correta": "Explicação da alternativa correta",
            "conceitos_revisar": conceitos_faltantes,
            "nivel_explicacao": "DIDÁTICA"
        }

    # Se acertou, explica de forma adaptativa
    else:
        explicacao = engine.gerar_explicacao_adaptativa(
            topico="Tópico da questão",
            contexto="Contexto específico",
            perfil_estudante=perfil_estudante
        )

        return {
            "resultado": "ACERTO",
            "explicacao": explicacao.conteudo,
            "conceitos_dominados": explicacao.conceitos_chave,
            "nivel_explicacao": explicacao.tipo
        }


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Cria engine
    engine = criar_engine_explicacao()

    # Exemplo 1: Explicação adaptativa
    print("=" * 60)
    print("EXEMPLO 1: EXPLICAÇÃO ADAPTATIVA")
    print("=" * 60)

    explicacao_iniciante = engine.gerar_explicacao_adaptativa(
        topico="Dolo eventual vs Culpa consciente",
        contexto="Questão OAB sobre homicídio no trânsito",
        perfil_estudante=StudentProfile.INICIANTE
    )

    print(f"\nNível: {explicacao_iniciante.tipo}")
    print(explicacao_iniciante.conteudo)

    # Exemplo 2: Explicação de alternativa errada
    print("\n" + "=" * 60)
    print("EXEMPLO 2: EXPLICAÇÃO DE ERRO")
    print("=" * 60)

    explicacao_erro = engine.explicar_alternativa_errada(
        alternativa="Há dolo eventual quando o agente não quer o resultado mas assume o risco de produzi-lo",
        motivo_erro="A definição está CORRETA, não é erro - esta é a definição legal de dolo eventual (CP art. 18, I)",
        nivel=ExplanationLevel.DIDATICA
    )

    print(explicacao_erro)

    # Exemplo 3: Identificar conceitos faltantes
    print("\n" + "=" * 60)
    print("EXEMPLO 3: CONCEITOS FALTANTES")
    print("=" * 60)

    conceitos = engine.identificar_conceitos_faltantes(
        topico="Legítima defesa",
        erro_estudante="Confundiu legítima defesa com estado de necessidade"
    )

    print("Conceitos que precisam ser revisados:")
    for conceito in conceitos:
        print(f"  - {conceito}")

    print("\n" + "=" * 60)
    print("EXPLANATION ENGINE - OPERACIONAL")
    print("=" * 60)
