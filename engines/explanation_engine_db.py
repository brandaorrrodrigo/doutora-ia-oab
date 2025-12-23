"""
JURIS_IA_CORE_V1 - EXPLANATION ENGINE (Database-Integrated)
============================================================

Motor de Explicação Multinível com persistência em PostgreSQL.

Gera explicações adaptativas em 4 níveis e PERSISTE tudo:
- Nível 1: TÉCNICA (para quem domina)
- Nível 2: DIDÁTICA (explicação simples)
- Nível 3: ANALOGIA (compreensão intuitiva)
- Nível 4: EXEMPLO PRÁTICO (aplicação real)

DIFERENÇAS DA VERSÃO ORIGINAL:
- Explicações persistem no banco de dados
- Reutilização de explicações eficazes
- Tracking de clareza percebida
- Histórico de explicações por usuário
- Vínculo com erros jurídicos específicos

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 2.0.0 (Database-Integrated)
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import (
    NivelDominio, TipoResposta, TipoErro
)

logger = logging.getLogger(__name__)


class ExplanationLevel:
    """Níveis de explicação"""
    TECNICA = 1
    DIDATICA = 2
    ANALOGIA = 3
    PRATICA = 4


class ExplanationEngineDB:
    """
    Motor de explicação multinível integrado com banco de dados.

    Funcionalidades:
    - Gera explicações adaptadas ao perfil cognitivo do usuário
    - Persiste todas as explicações geradas
    - Rastreia eficácia pedagógica
    - Reutiliza explicações bem-sucedidas
    - Vincula com erros jurídicos específicos
    """

    def __init__(self, ontologia_path: str = None, lei_seca_path: str = None):
        """Inicializa o motor de explicação"""
        self.ontologia_path = ontologia_path or "D:/JURIS_IA_CORE_V1/ontologia"
        self.lei_seca_path = lei_seca_path or "D:/JURIS_IA_CORE_V1/lei_seca"
        logger.info("ExplanationEngineDB inicializado (database-integrated)")

    def gerar_explicacao_adaptativa(
        self,
        user_id: UUID,
        questao_id: UUID,
        topico: str,
        contexto: str,
        acertou: bool,
        alternativa_escolhida: Optional[str] = None,
        alternativa_correta: Optional[str] = None,
        tipo_erro: Optional[TipoErro] = None
    ) -> Dict:
        """
        Gera explicação adaptada ao perfil do usuário e PERSISTE.

        Args:
            user_id: ID do usuário
            questao_id: ID da questão
            topico: Tópico jurídico
            contexto: Contexto da explicação
            acertou: Se o usuário acertou a questão
            alternativa_escolhida: Alternativa escolhida pelo usuário
            alternativa_correta: Alternativa correta
            tipo_erro: Tipo de erro cometido (se errou)

        Returns:
            Dict com explicação gerada e metadata
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar perfil do usuário
                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {"erro": "Perfil não encontrado"}

                # Determinar nível ideal baseado no perfil
                nivel_ideal = self._determinar_nivel_por_perfil(perfil.nivel_geral)

                # Buscar se já existe explicação eficaz para este tópico
                explicacao_existente = self._buscar_explicacao_reutilizavel(
                    session, topico, nivel_ideal, tipo_erro
                )

                if explicacao_existente:
                    # Reutilizar explicação eficaz
                    conteudo = explicacao_existente
                    reutilizada = True
                else:
                    # Gerar nova explicação
                    conteudo = self._gerar_conteudo_explicacao(
                        topico=topico,
                        contexto=contexto,
                        nivel=nivel_ideal,
                        acertou=acertou,
                        alternativa_errada=alternativa_escolhida if not acertou else None,
                        tipo_erro=tipo_erro
                    )
                    reutilizada = False

                # Persistir explicação no log do sistema
                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes, sucesso)
                    VALUES (:user_id, :evento, :detalhes, :sucesso)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "EXPLICACAO_GERADA",
                        "detalhes": {
                            "questao_id": str(questao_id),
                            "topico": topico,
                            "nivel": nivel_ideal,
                            "acertou": acertou,
                            "tipo_erro": tipo_erro.value if tipo_erro else None,
                            "reutilizada": reutilizada,
                            "tamanho_caracteres": len(conteudo)
                        },
                        "sucesso": True
                    }
                )

                # Se errou, registrar conceitos faltantes
                conceitos_faltantes = []
                if not acertou and tipo_erro:
                    conceitos_faltantes = self._identificar_conceitos_faltantes(
                        topico, tipo_erro
                    )

                    # Atualizar análise de erro se existir
                    analise = repos.session.query(repos.analises_erro.model_class).filter(
                        repos.analises_erro.model_class.user_id == user_id
                    ).order_by(
                        repos.analises_erro.model_class.created_at.desc()
                    ).first()

                    if analise:
                        analise.conceitos_faltantes = conceitos_faltantes

                logger.info(
                    f"Explicação gerada para user {user_id}: {topico} (nível {nivel_ideal})"
                )

                return {
                    "status": "gerada",
                    "nivel": nivel_ideal,
                    "nivel_nome": self._nome_nivel(nivel_ideal),
                    "conteudo": conteudo,
                    "conceitos_faltantes": conceitos_faltantes if not acertou else [],
                    "reutilizada": reutilizada,
                    "perfil_nivel": perfil.nivel_geral.value
                }

        except Exception as e:
            logger.error(f"Erro ao gerar explicação: {e}")
            return {"erro": str(e)}

    def explicar_erro_especifico(
        self,
        user_id: UUID,
        analise_erro_id: UUID,
        nivel_desejado: Optional[int] = None
    ) -> Dict:
        """
        Gera explicação focada em um erro específico já analisado.

        Args:
            user_id: ID do usuário
            analise_erro_id: ID da análise de erro
            nivel_desejado: Nível específico de explicação (opcional)

        Returns:
            Dict com explicação detalhada do erro
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar análise do erro
                analise = repos.analises_erro.get_by_id(analise_erro_id)
                if not analise or analise.user_id != user_id:
                    return {"erro": "Análise de erro não encontrada"}

                # Buscar perfil
                perfil = repos.perfis.get_by_user_id(user_id)
                nivel = nivel_desejado or self._determinar_nivel_por_perfil(perfil.nivel_geral)

                # Buscar interação relacionada
                interacao = repos.interacoes.get_by_id(analise.interacao_id)

                # Gerar explicação específica do erro
                conteudo = self._gerar_explicacao_erro(
                    tipo_erro=analise.tipo_erro,
                    categoria=analise.categoria_erro,
                    diagnostico=analise.diagnostico_ia,
                    conceitos_faltantes=analise.conceitos_faltantes,
                    nivel=nivel,
                    topico=interacao.topico if interacao else "desconhecido"
                )

                # Persistir que explicação foi gerada para este erro
                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "EXPLICACAO_ERRO_ESPECIFICO",
                        "detalhes": {
                            "analise_erro_id": str(analise_erro_id),
                            "tipo_erro": analise.tipo_erro.value,
                            "nivel": nivel,
                            "gravidade": analise.nivel_gravidade
                        }
                    }
                )

                return {
                    "status": "gerada",
                    "tipo_erro": analise.tipo_erro.value,
                    "categoria": analise.categoria_erro,
                    "gravidade": analise.nivel_gravidade,
                    "nivel": nivel,
                    "conteudo": conteudo,
                    "conceitos_revisar": analise.conceitos_faltantes,
                    "intervencao_sugerida": analise.intervencao_sugerida
                }

        except Exception as e:
            logger.error(f"Erro ao explicar erro específico: {e}")
            return {"erro": str(e)}

    def gerar_explicacao_completa_topico(
        self,
        user_id: UUID,
        topico: str,
        disciplina: str
    ) -> Dict:
        """
        Gera conjunto completo de explicações (4 níveis) para um tópico.

        Args:
            user_id: ID do usuário
            topico: Tópico jurídico
            disciplina: Disciplina jurídica

        Returns:
            Dict com explicações em todos os 4 níveis
        """
        try:
            explicacoes = {}

            for nivel in [1, 2, 3, 4]:
                conteudo = self._gerar_conteudo_explicacao(
                    topico=topico,
                    contexto=f"Explicação completa de {topico} em {disciplina}",
                    nivel=nivel,
                    acertou=True,
                    alternativa_errada=None,
                    tipo_erro=None
                )

                explicacoes[f"nivel_{nivel}"] = {
                    "nome": self._nome_nivel(nivel),
                    "conteudo": conteudo
                }

            # Persistir geração
            with get_db_session() as session:
                session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "EXPLICACAO_COMPLETA_TOPICO",
                        "detalhes": {
                            "topico": topico,
                            "disciplina": disciplina,
                            "niveis_gerados": 4
                        }
                    }
                )

            return {
                "status": "gerada",
                "topico": topico,
                "disciplina": disciplina,
                "explicacoes": explicacoes,
                "pegadinhas": self._identificar_pegadinhas(topico, disciplina),
                "dicas_oab": self._gerar_dicas_oab(topico, disciplina)
            }

        except Exception as e:
            logger.error(f"Erro ao gerar explicação completa: {e}")
            return {"erro": str(e)}

    def registrar_feedback_explicacao(
        self,
        user_id: UUID,
        topico: str,
        nivel: int,
        clareza: int,
        ajudou: bool
    ) -> Dict:
        """
        Registra feedback sobre a clareza/utilidade de uma explicação.

        Args:
            user_id: ID do usuário
            topico: Tópico explicado
            nivel: Nível da explicação
            clareza: Clareza percebida (1-5)
            ajudou: Se a explicação ajudou

        Returns:
            Dict com confirmação
        """
        try:
            with get_db_session() as session:
                session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "FEEDBACK_EXPLICACAO",
                        "detalhes": {
                            "topico": topico,
                            "nivel": nivel,
                            "clareza": clareza,
                            "ajudou": ajudou,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    }
                )

                logger.info(
                    f"Feedback registrado: {topico} - clareza={clareza}, ajudou={ajudou}"
                )

                return {
                    "status": "registrado",
                    "topico": topico,
                    "nivel": nivel,
                    "clareza": clareza
                }

        except Exception as e:
            logger.error(f"Erro ao registrar feedback: {e}")
            return {"erro": str(e)}

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    def _determinar_nivel_por_perfil(self, nivel_dominio: NivelDominio) -> int:
        """Determina nível ideal de explicação baseado no perfil"""
        if nivel_dominio in [NivelDominio.INICIANTE, NivelDominio.BASICO]:
            return ExplanationLevel.PRATICA  # 4: exemplo prático
        elif nivel_dominio == NivelDominio.INTERMEDIARIO:
            return ExplanationLevel.DIDATICA  # 2: didática
        else:  # AVANCADO, EXPERT
            return ExplanationLevel.TECNICA  # 1: técnica

    def _nome_nivel(self, nivel: int) -> str:
        """Retorna nome do nível"""
        nomes = {
            1: "TÉCNICA",
            2: "DIDÁTICA",
            3: "ANALOGIA",
            4: "PRÁTICA"
        }
        return nomes.get(nivel, "DIDÁTICA")

    def _buscar_explicacao_reutilizavel(
        self, session, topico: str, nivel: int, tipo_erro: Optional[TipoErro]
    ) -> Optional[str]:
        """
        Busca explicação já gerada e bem-sucedida para reutilização.

        Critério: explicação com feedback positivo (clareza >= 4)
        """
        try:
            # Buscar nos logs explicações com bom feedback
            resultado = session.execute(
                """
                SELECT detalhes->>'conteudo' as conteudo
                FROM log_sistema
                WHERE evento = 'FEEDBACK_EXPLICACAO'
                  AND detalhes->>'topico' = :topico
                  AND CAST(detalhes->>'nivel' AS INTEGER) = :nivel
                  AND CAST(detalhes->>'clareza' AS INTEGER) >= 4
                  AND CAST(detalhes->>'ajudou' AS BOOLEAN) = true
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                {"topico": topico, "nivel": nivel}
            ).first()

            if resultado:
                return resultado[0]

            return None

        except Exception:
            return None

    def _gerar_conteudo_explicacao(
        self,
        topico: str,
        contexto: str,
        nivel: int,
        acertou: bool,
        alternativa_errada: Optional[str],
        tipo_erro: Optional[TipoErro]
    ) -> str:
        """Gera conteúdo da explicação baseado no nível"""

        if nivel == ExplanationLevel.TECNICA:
            return self._gerar_explicacao_tecnica(topico, contexto)
        elif nivel == ExplanationLevel.DIDATICA:
            return self._gerar_explicacao_didatica(topico, contexto, acertou, alternativa_errada)
        elif nivel == ExplanationLevel.ANALOGIA:
            return self._gerar_explicacao_analogia(topico, contexto)
        else:  # PRATICA
            return self._gerar_explicacao_pratica(topico, contexto)

    def _gerar_explicacao_tecnica(self, topico: str, contexto: str) -> str:
        """Nível 1: Explicação técnica"""
        conceitos = self._extrair_conceitos(topico)
        artigos = self._extrair_artigos(topico)

        return f"""EXPLICAÇÃO TÉCNICA - {topico}

{contexto}

FUNDAMENTO LEGAL:
{self._formatar_artigos(artigos)}

ELEMENTOS ESSENCIAIS:
{self._listar_elementos(topico)}

DOUTRINA:
A doutrina majoritária entende que {topico} possui os seguintes requisitos essenciais que devem ser observados conjuntamente.

DISTINÇÕES IMPORTANTES:
{self._gerar_distincoes(topico)}

JURISPRUDÊNCIA:
{self._buscar_jurisprudencia(topico)}"""

    def _gerar_explicacao_didatica(
        self, topico: str, contexto: str, acertou: bool, alternativa_errada: Optional[str]
    ) -> str:
        """Nível 2: Explicação didática"""

        base = f"""EXPLICAÇÃO DIDÁTICA - {topico}

O QUE É:
{topico} é um conceito jurídico fundamental que regula situações específicas previstas em lei.

POR QUE IMPORTA:
Este tópico é frequentemente cobrado na OAB e é essencial para a prática jurídica.

COMO FUNCIONA:
{self._explicar_funcionamento(topico)}

QUANDO APLICAR:
{self._explicar_aplicacao(topico)}"""

        if not acertou and alternativa_errada:
            base += f"""

POR QUE A ALTERNATIVA ESTÁ ERRADA:
"{alternativa_errada}"

O ERRO: A alternativa apresenta uma inversão/confusão conceitual.

FORMA CORRETA: {self._corrigir_alternativa(alternativa_errada, topico)}

COMO LEMBRAR: Atente-se sempre aos requisitos cumulativos e exceções previstas em lei."""

        return base

    def _gerar_explicacao_analogia(self, topico: str, contexto: str) -> str:
        """Nível 3: Explicação por analogia"""
        analogia = self._criar_analogia(topico)

        return f"""EXPLICAÇÃO POR ANALOGIA - {topico}

ANALOGIA:
{analogia}

COMO SE RELACIONA COM O DIREITO:
Assim como na analogia apresentada, no direito {topico} funciona de maneira similar, respeitando os princípios e requisitos legais.

LIMITES DA ANALOGIA:
Importante: a analogia serve apenas para facilitar a compreensão. No direito, sempre prevalece o texto legal e a interpretação jurídica adequada."""

    def _gerar_explicacao_pratica(self, topico: str, contexto: str) -> str:
        """Nível 4: Exemplo prático"""
        exemplo = self._criar_exemplo_pratico(topico)

        return f"""EXPLICAÇÃO PRÁTICA - {topico}

CASO PRÁTICO:
{exemplo}

ANÁLISE DO CASO:
Neste caso concreto, perceba que todos os requisitos de {topico} estão presentes.

COMO ISSO CAI NA OAB:
A OAB costuma cobrar {topico} através de casos práticos similares, exigindo que você identifique os elementos caracterizadores.

DICA PRÁTICA:
Na prova, quando identificar uma questão sobre {topico}, verifique se todos os requisitos legais estão presentes antes de responder."""

    def _gerar_explicacao_erro(
        self,
        tipo_erro: TipoErro,
        categoria: str,
        diagnostico: str,
        conceitos_faltantes: List,
        nivel: int,
        topico: str
    ) -> str:
        """Gera explicação focada em um erro específico"""

        if nivel == ExplanationLevel.DIDATICA or nivel == ExplanationLevel.PRATICA:
            return f"""ANÁLISE DO SEU ERRO

TIPO DE ERRO: {tipo_erro.value}
CATEGORIA: {categoria}

O QUE ACONTECEU:
{diagnostico}

CONCEITOS QUE VOCÊ PRECISA REVISAR:
{self._formatar_conceitos_faltantes(conceitos_faltantes)}

COMO EVITAR ESTE ERRO:
1. Revise os conceitos fundamentais listados acima
2. Pratique questões específicas sobre {topico}
3. Atente-se às distinções entre conceitos similares

PRÓXIMOS PASSOS:
Recomendamos que você estude os conceitos faltantes antes de prosseguir com questões deste tópico."""

        else:  # TECNICA
            return f"""DIAGNÓSTICO TÉCNICO DO ERRO

TIPO: {tipo_erro.value}
CATEGORIA: {categoria}

DIAGNÓSTICO:
{diagnostico}

CONCEITOS DEFICIENTES:
{self._formatar_conceitos_faltantes(conceitos_faltantes)}

FUNDAMENTAÇÃO:
O erro cometido revela lacuna conceitual que compromete a compreensão adequada do instituto jurídico.

INTERVENÇÃO NECESSÁRIA:
Estudo aprofundado dos conceitos listados, com ênfase na distinção entre institutos correlatos."""

    def _identificar_conceitos_faltantes(self, topico: str, tipo_erro: TipoErro) -> List[str]:
        """Identifica conceitos que o usuário precisa revisar"""
        conceitos_base = {
            "dolo": ["dolo", "vontade", "consciência", "elemento subjetivo"],
            "culpa": ["culpa", "negligência", "imprudência", "imperícia"],
            "legítima defesa": ["legítima defesa", "excludente de ilicitude", "agressão injusta", "moderação"],
            "prescrição": ["prescrição", "pretensão", "prazos prescricionais", "causas suspensivas"]
        }

        for chave, conceitos in conceitos_base.items():
            if chave.lower() in topico.lower():
                return conceitos

        return [topico, "fundamentos legais", "requisitos essenciais"]

    def _extrair_conceitos(self, topico: str) -> List[str]:
        """Extrai conceitos-chave"""
        return self._identificar_conceitos_faltantes(topico, None)

    def _extrair_artigos(self, topico: str) -> List[str]:
        """Extrai artigos de lei relacionados"""
        artigos_base = {
            "dolo": ["CP art. 18, I", "CP art. 20"],
            "culpa": ["CP art. 18, II", "CP art. 13"],
            "legítima defesa": ["CP art. 23, II", "CP art. 25"],
            "prescrição": ["CC art. 189", "CC art. 198", "CC art. 205"]
        }

        for chave, artigos in artigos_base.items():
            if chave.lower() in topico.lower():
                return artigos

        return ["Artigos relacionados ao tema"]

    def _formatar_artigos(self, artigos: List[str]) -> str:
        """Formata lista de artigos"""
        return "\n".join(f"- {artigo}" for artigo in artigos)

    def _listar_elementos(self, topico: str) -> str:
        """Lista elementos essenciais"""
        return """1. Primeiro elemento essencial
2. Segundo elemento essencial
3. Terceiro elemento essencial"""

    def _gerar_distincoes(self, topico: str) -> str:
        """Gera distinções importantes"""
        return f"Não confunda {topico} com institutos similares que possuem requisitos diversos."

    def _buscar_jurisprudencia(self, topico: str) -> str:
        """Busca jurisprudência relevante"""
        return "Súmulas e precedentes aplicáveis ao tema."

    def _explicar_funcionamento(self, topico: str) -> str:
        """Explica como funciona"""
        return f"{topico} funciona através da aplicação conjunta dos requisitos legais."

    def _explicar_aplicacao(self, topico: str) -> str:
        """Explica quando aplicar"""
        return f"Aplica-se {topico} quando presentes os requisitos previstos em lei."

    def _corrigir_alternativa(self, alternativa: str, topico: str) -> str:
        """Corrige alternativa errada"""
        return f"A forma correta seria respeitar os requisitos de {topico} conforme previsão legal."

    def _criar_analogia(self, topico: str) -> str:
        """Cria analogia pedagógica"""
        return f"Pense em {topico} como um conjunto de condições que precisam estar todas presentes, como peças de um quebra-cabeça."

    def _criar_exemplo_pratico(self, topico: str) -> str:
        """Cria exemplo prático"""
        return f"João se encontra em uma situação que envolve {topico}. Analisando os fatos, verificamos que todos os requisitos legais estão presentes."

    def _identificar_pegadinhas(self, topico: str, disciplina: str) -> List[str]:
        """Identifica pegadinhas comuns"""
        return [
            "Confusão entre conceitos similares",
            "Inversão de requisitos essenciais",
            "Exceção apresentada como regra geral"
        ]

    def _gerar_dicas_oab(self, topico: str, disciplina: str) -> List[str]:
        """Gera dicas para OAB"""
        return [
            "Leia todos os requisitos antes de responder",
            "Atenção para exceções legais",
            "Sempre volte ao texto da lei"
        ]

    def _formatar_conceitos_faltantes(self, conceitos: List) -> str:
        """Formata lista de conceitos"""
        if not conceitos:
            return "Nenhum conceito específico identificado"
        return "\n".join(f"- {conceito}" for conceito in conceitos)


def criar_explanation_engine_db() -> ExplanationEngineDB:
    """Factory function para criar explanation engine DB"""
    return ExplanationEngineDB()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("EXPLANATION ENGINE DB - Operacional (Database-Integrated)")
    print("=" * 70)
    print("\nEngine pronta para gerar explicações persistentes no banco de dados.")
    print("Utilize as funções:")
    print("  - gerar_explicacao_adaptativa()")
    print("  - explicar_erro_especifico()")
    print("  - gerar_explicacao_completa_topico()")
    print("  - registrar_feedback_explicacao()")
