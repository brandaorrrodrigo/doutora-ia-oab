"""
JURIS_IA_CORE_V1 - ORQUESTRADOR PRINCIPAL (DATABASE INTEGRATED)
Sistema Completo de IA Jurídica para OAB - 100% Integrado com PostgreSQL

Este é o ponto de entrada principal do sistema. Integra todos os engines
com persistência em banco de dados e fornece interface unificada.

INTEGRAÇÃO COMPLETA COM DATABASE:
- TODOS os engines usam PostgreSQL via get_db_session()
- TODAS as decisões são persistidas
- TODAS as interações são rastreáveis
- Sistema FALHA explicitamente se database não disponível
- Zero estado volátil em memória

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from uuid import UUID

# Adiciona path para imports
sys.path.append(str(Path(__file__).parent.parent))

# Importa engines DATABASE-INTEGRATED
from engines.explanation_engine_db import ExplanationEngineDB, criar_explanation_engine_db
from engines.question_engine_db import QuestionEngineDB, criar_question_engine_db
from engines.decision_engine_db import DecisionEngineDB, criar_decision_engine_db
from engines.piece_engine_db import PieceEngineDB, PieceType, criar_piece_engine_db
from engines.memory_engine_db import MemoryEngineDB, criar_memory_engine_db

# Database imports
from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import TipoErro


# ============================================================
# JURIS_IA - SISTEMA PRINCIPAL (DATABASE INTEGRATED)
# ============================================================

class JurisIADB:
    """
    Sistema completo de IA jurídica para aprovação na OAB.
    100% INTEGRADO COM POSTGRESQL.

    CARACTERÍSTICAS:
    - Persistência total em PostgreSQL
    - Zero estado em memória volátil
    - Todas as decisões rastreáveis
    - Falha explicitamente se database indisponível
    - Integração com todos os engines DB

    Responsabilidades:
    - Orquestrar fluxos de estudo (1ª fase)
    - Orquestrar prática de peças (2ª fase)
    - Fornecer diagnóstico completo
    - Garantir persistência de TODAS as interações
    """

    def __init__(self):
        """
        Inicializa o sistema JURIS_IA com engines database-integrated.

        IMPORTANTE: Sistema FALHA se database não disponível.
        """
        print("Inicializando JURIS_IA_CORE_V1 (DATABASE INTEGRATED)...")

        # Verifica conexão com database ANTES de inicializar
        try:
            with get_db_session() as session:
                session.execute("SELECT 1")
            print("✓ Database PostgreSQL conectado")
        except Exception as e:
            print(f"✗ ERRO: Database PostgreSQL não disponível")
            print(f"  Detalhes: {str(e)}")
            print("\nSistema NÃO pode funcionar sem database.")
            print("Configure DATABASE_URL e tente novamente.")
            raise RuntimeError("Database PostgreSQL não disponível") from e

        # Inicializa todos os engines DATABASE-INTEGRATED
        self.explanation_engine = criar_explanation_engine_db()
        self.question_engine = criar_question_engine_db()
        self.decision_engine = criar_decision_engine_db()
        self.piece_engine = criar_piece_engine_db()
        self.memory_engine = criar_memory_engine_db()

        print("✓ Explanation Engine (DB) carregado")
        print("✓ Question Engine (DB) carregado")
        print("✓ Decision Engine (DB) carregado")
        print("✓ Piece Engine (DB) carregado")
        print("✓ Memory Engine (DB) carregado")
        print("\n✓ Sistema 100% DATABASE-CENTRIC pronto!")
        print("  Todas as interações serão persistidas em PostgreSQL")

    # ============================================================
    # FLUXO: SESSÃO DE ESTUDO (1ª FASE)
    # ============================================================

    def iniciar_sessao_estudo(
        self,
        user_id: UUID,
        disciplina: Optional[str] = None,
        tipo: str = "adaptativo"  # "adaptativo", "drill", "simulado", "revisao"
    ) -> Dict:
        """
        Inicia sessão de estudo personalizada.
        PERSISTE evento de início no database.

        Args:
            user_id: UUID do usuário
            disciplina: Disciplina específica (opcional)
            tipo: Tipo de sessão

        Returns:
            Dict com configuração da sessão
        """
        try:
            # Seleciona questões via Question Engine DB
            if tipo == "simulado":
                resultado = self.question_engine.gerar_simulado(
                    user_id=user_id,
                    tipo="completo" if not disciplina else "disciplina"
                )
            else:
                resultado = self.question_engine.selecionar_proximas_questoes(
                    user_id=user_id,
                    quantidade=10,
                    disciplina=disciplina,
                    foco=tipo
                )

            if not resultado.get("sucesso"):
                return resultado

            # Processa evento de início via Decision Engine
            evento_resultado = self.decision_engine.processar_evento(
                user_id=user_id,
                evento_tipo="INICIO_SESSAO",
                contexto={
                    "tipo_sessao": tipo,
                    "disciplina": disciplina,
                    "total_questoes": len(resultado.get("questoes", []))
                }
            )

            return {
                "sucesso": True,
                "user_id": str(user_id),
                "tipo_sessao": tipo,
                "disciplina": disciplina,
                "total_questoes": len(resultado.get("questoes", [])),
                "questoes": resultado.get("questoes", []),
                "estrategia": resultado.get("estrategia", tipo),
                "recomendacoes": evento_resultado.get("acoes", [])
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao iniciar sessão: {str(e)}"
            }

    def responder_questao(
        self,
        user_id: UUID,
        questao_id: UUID,
        alternativa_escolhida: str,
        tempo_segundos: int,
        acertou: bool
    ) -> Dict:
        """
        Processa resposta de uma questão.
        PERSISTE interação completa no database.

        Args:
            user_id: UUID do usuário
            questao_id: UUID da questão
            alternativa_escolhida: Letra escolhida (A, B, C, D, E)
            tempo_segundos: Tempo gasto
            acertou: Se acertou ou não

        Returns:
            Dict com feedback completo + explicação adaptativa
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # 1. Busca questão no database
                questao = repos.questoes.get_by_id(questao_id)
                if not questao:
                    return {
                        "sucesso": False,
                        "erro": "Questão não encontrada"
                    }

                # 2. Registra interação no database
                repos.interacoes_questao.create_interacao(
                    user_id=user_id,
                    questao_id=questao_id,
                    alternativa_escolhida=alternativa_escolhida,
                    acertou=acertou,
                    tempo_segundos=tempo_segundos
                )

                # 3. Atualiza progresso (topico e disciplina)
                repos.progressos_topico.atualizar_progresso(
                    user_id=user_id,
                    topico=questao.topico,
                    acertou=acertou
                )

                repos.progressos_disciplina.atualizar_progresso(
                    user_id=user_id,
                    disciplina=questao.disciplina,
                    acertou=acertou
                )

                session.commit()

            # 4. Processa evento via Decision Engine
            evento_tipo = "ACERTO" if acertou else "ERRO"
            evento_resultado = self.decision_engine.processar_evento(
                user_id=user_id,
                evento_tipo=evento_tipo,
                contexto={
                    "questao_id": str(questao_id),
                    "disciplina": questao.disciplina,
                    "topico": questao.topico,
                    "tempo_segundos": tempo_segundos,
                    "tipo_erro": "conceitual" if not acertou else None
                }
            )

            # 5. Gera explicação adaptativa
            explicacao_resultado = self.explanation_engine.gerar_explicacao_adaptativa(
                user_id=user_id,
                questao_id=questao_id,
                topico=questao.topico,
                contexto=questao.enunciado[:200],  # Primeiros 200 chars
                acertou=acertou,
                alternativa_escolhida=alternativa_escolhida,
                alternativa_correta=questao.gabarito,
                tipo_erro=TipoErro.ERRO_CONCEITUAL if not acertou else None
            )

            # 6. Se errou, agenda revisão via Memory Engine
            if not acertou:
                self.memory_engine.adicionar_item(
                    user_id=user_id,
                    topico=questao.topico,
                    disciplina=questao.disciplina,
                    conceitos=[questao.topico],  # Simplificado
                    artigos=[]
                )

            return {
                "sucesso": True,
                "resultado": "ACERTO" if acertou else "ERRO",
                "questao_id": str(questao_id),
                "tempo_segundos": tempo_segundos,
                "feedback_tempo": self._feedback_tempo(tempo_segundos),
                "explicacao": explicacao_resultado.get("explicacao", {}),
                "proximas_acoes": evento_resultado.get("acoes", []),
                "revisao_agendada": not acertou
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao processar resposta: {str(e)}"
            }

    def finalizar_sessao_estudo(self, user_id: UUID) -> Dict:
        """
        Finaliza sessão de estudo e gera relatório.
        PERSISTE evento de finalização no database.

        Args:
            user_id: UUID do usuário

        Returns:
            Dict com resumo completo da sessão
        """
        try:
            # 1. Processa evento de fim de sessão
            evento_resultado = self.decision_engine.processar_evento(
                user_id=user_id,
                evento_tipo="FIM_SESSAO",
                contexto={}
            )

            # 2. Obtém recomendações personalizadas
            recomendacoes = self.decision_engine.recomendar_acoes_personalizadas(
                user_id=user_id
            )

            # 3. Análise de memória
            memoria = self.memory_engine.analisar_memoria(user_id)

            # 4. Detecta esquecimento
            esquecimento = self.memory_engine.detectar_esquecimento(user_id)

            return {
                "sucesso": True,
                "user_id": str(user_id),
                "recomendacoes": recomendacoes.get("acoes", []),
                "memoria": memoria,
                "alertas_esquecimento": esquecimento,
                "proximas_acoes": evento_resultado.get("acoes", [])
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao finalizar sessão: {str(e)}"
            }

    # ============================================================
    # FLUXO: PRÁTICA DE PEÇAS (2ª FASE)
    # ============================================================

    def iniciar_pratica_peca(
        self,
        user_id: UUID,
        tipo_peca: PieceType,
        enunciado: str
    ) -> Dict:
        """
        Inicia prática de peça processual.
        PERSISTE evento de início no database.

        Args:
            user_id: UUID do usuário
            tipo_peca: Tipo de peça
            enunciado: Enunciado da questão

        Returns:
            Dict com checklist e orientações
        """
        try:
            # 1. Processa evento de início de peça
            evento_resultado = self.decision_engine.processar_evento(
                user_id=user_id,
                evento_tipo="PECA_INICIADA",
                contexto={
                    "tipo_peca": tipo_peca.value,
                    "enunciado": enunciado[:100]
                }
            )

            # 2. Gera checklist
            checklist = self.piece_engine.gerar_checklist(tipo_peca)

            # 3. Gera peça-modelo (persiste log)
            peca_modelo = self.piece_engine.gerar_peca_modelo(
                user_id=user_id,
                tipo_peca=tipo_peca,
                enunciado=enunciado,
                detalhada=False
            )

            return {
                "sucesso": True,
                "user_id": str(user_id),
                "tipo_peca": tipo_peca.value,
                "enunciado": enunciado,
                "checklist": checklist,
                "peca_modelo": peca_modelo.get("peca_modelo", {}),
                "orientacoes": [
                    "Leia o enunciado 3 vezes antes de começar",
                    "Use o checklist para verificar cada parte",
                    "Cite artigos específicos da lei",
                    "Revise antes de enviar"
                ],
                "tempo_recomendado_minutos": 60,
                "proximas_acoes": evento_resultado.get("acoes", [])
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao iniciar prática de peça: {str(e)}"
            }

    def avaliar_peca(
        self,
        user_id: UUID,
        tipo_peca: PieceType,
        conteudo: str,
        enunciado: str,
        area_direito: str
    ) -> Dict:
        """
        Avalia peça escrita pelo aluno.
        PERSISTE avaliação completa no database.

        Args:
            user_id: UUID do usuário
            tipo_peca: Tipo de peça
            conteudo: Texto da peça
            enunciado: Enunciado original
            area_direito: Área do direito (civil, penal, trabalhista, etc.)

        Returns:
            Dict com avaliação completa
        """
        try:
            # 1. Avalia peça (persiste automaticamente)
            avaliacao = self.piece_engine.avaliar_peca(
                user_id=user_id,
                tipo_peca=tipo_peca,
                conteudo=conteudo,
                enunciado=enunciado,
                area_direito=area_direito
            )

            if not avaliacao.get("sucesso"):
                return avaliacao

            # 2. Processa evento de peça completa
            evento_tipo = "PECA_COMPLETA" if avaliacao["aprovado"] else "ERRO_FORMAL"
            evento_resultado = self.decision_engine.processar_evento(
                user_id=user_id,
                evento_tipo=evento_tipo,
                contexto={
                    "pratica_id": avaliacao["pratica_id"],
                    "tipo_peca": tipo_peca.value,
                    "nota_final": avaliacao["nota_final"],
                    "aprovado": avaliacao["aprovado"],
                    "erros_fatais": avaliacao["erros"]["fatais"]
                }
            )

            # 3. Adiciona ações recomendadas
            avaliacao["proximas_acoes"] = evento_resultado.get("acoes", [])

            return avaliacao

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao avaliar peça: {str(e)}"
            }

    def analisar_evolucao_pecas(
        self,
        user_id: UUID,
        area_direito: Optional[str] = None
    ) -> Dict:
        """
        Analisa evolução histórica em peças processuais.

        Args:
            user_id: UUID do usuário
            area_direito: Filtro por área (opcional)

        Returns:
            Dict com análise evolutiva
        """
        try:
            return self.piece_engine.analisar_evolucao_historica(
                user_id=user_id,
                area_direito=area_direito
            )

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao analisar evolução: {str(e)}"
            }

    # ============================================================
    # DIAGNÓSTICO E ACOMPANHAMENTO
    # ============================================================

    def obter_painel_estudante(self, user_id: UUID) -> Dict:
        """
        Retorna painel completo do estudante baseado em dados do database.

        Args:
            user_id: UUID do usuário

        Returns:
            Dict com todas as informações
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Busca perfil jurídico
                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {
                        "sucesso": False,
                        "erro": "Perfil não encontrado"
                    }

                # Análise de memória
                memoria = self.memory_engine.analisar_memoria(user_id)

                # Próximas revisões
                revisoes = self.memory_engine.obter_itens_revisar(
                    user_id=user_id,
                    limite=5
                )

                # Recomendações personalizadas
                recomendacoes = self.decision_engine.recomendar_acoes_personalizadas(
                    user_id=user_id
                )

                return {
                    "sucesso": True,
                    "user_id": str(user_id),
                    "visao_geral": {
                        "nivel": perfil.nivel_geral.value if perfil.nivel_geral else "BASICO",
                        "taxa_acerto_global": float(perfil.taxa_acerto_global),
                        "total_questoes": perfil.total_questoes,
                        "estado_emocional": perfil.estado_emocional
                    },
                    "perfil_cognitivo": {
                        "processamento_normativo": perfil.processamento_normativo,
                        "raciocinio_abstrato": perfil.raciocinio_abstrato,
                        "memoria_trabalho": perfil.memoria_trabalho,
                        "atencao_concentracao": perfil.atencao_concentracao,
                        "velocidade_processamento": perfil.velocidade_processamento,
                        "flexibilidade_cognitiva": perfil.flexibilidade_cognitiva,
                        "controle_inibitorio": perfil.controle_inibitorio,
                        "metacognicao": perfil.metacognicao
                    },
                    "memoria": memoria,
                    "proximas_revisoes": revisoes.get("itens", []),
                    "recomendacoes": recomendacoes.get("acoes", [])
                }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao obter painel: {str(e)}"
            }

    def obter_relatorio_progresso(
        self,
        user_id: UUID,
        periodo_dias: int = 7
    ) -> Dict:
        """
        Gera relatório de progresso baseado em dados do database.

        Args:
            user_id: UUID do usuário
            periodo_dias: Período em dias (padrão: 7)

        Returns:
            Dict com relatório completo
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Busca perfil
                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {
                        "sucesso": False,
                        "erro": "Perfil não encontrado"
                    }

                # Busca interações recentes
                from datetime import timedelta
                data_inicio = datetime.now(timezone.utc) - timedelta(days=periodo_dias)

                query = """
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN acertou THEN 1 ELSE 0 END) as acertos
                    FROM interacao_questao
                    WHERE user_id = :user_id
                      AND created_at >= :data_inicio
                """

                result = session.execute(
                    query,
                    {"user_id": user_id, "data_inicio": data_inicio}
                ).fetchone()

                total_questoes = result[0] if result else 0
                acertos = result[1] if result else 0
                taxa_acerto = (acertos / total_questoes * 100) if total_questoes > 0 else 0

                return {
                    "sucesso": True,
                    "user_id": str(user_id),
                    "periodo_dias": periodo_dias,
                    "metricas": {
                        "questoes_resolvidas": total_questoes,
                        "taxa_acerto": round(taxa_acerto, 1),
                        "nivel_atual": perfil.nivel_geral.value if perfil.nivel_geral else "BASICO",
                        "total_questoes_historico": perfil.total_questoes
                    },
                    "evolucao": {
                        "taxa_acerto_global": float(perfil.taxa_acerto_global),
                        "nivel": perfil.nivel_geral.value if perfil.nivel_geral else "BASICO"
                    }
                }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao gerar relatório: {str(e)}"
            }

    def avaliar_mudanca_nivel(self, user_id: UUID) -> Dict:
        """
        Avalia se aluno deve mudar de nível.
        PERSISTE mudança de nível + snapshot no database.

        Args:
            user_id: UUID do usuário

        Returns:
            Dict com resultado da avaliação
        """
        try:
            return self.decision_engine.avaliar_mudanca_nivel(user_id)

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao avaliar mudança de nível: {str(e)}"
            }

    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================

    def _feedback_tempo(self, tempo_segundos: int) -> str:
        """Gera feedback sobre tempo gasto"""
        tempo_ideal = 180  # 3 minutos

        if tempo_segundos < tempo_ideal * 0.5:
            return "Muito rápido! Certifique-se de ler com atenção."
        elif tempo_segundos < tempo_ideal:
            return "Excelente ritmo!"
        elif tempo_segundos < tempo_ideal * 1.5:
            return "Bom, mas tente ser um pouco mais rápido."
        else:
            return "Muito lento. Pratique técnicas de leitura rápida."


# ============================================================
# FUNÇÕES FACTORY
# ============================================================

def criar_juris_ia_db() -> JurisIADB:
    """
    Factory function para criar sistema JurisIA DATABASE-INTEGRATED.

    IMPORTANTE: Sistema FALHA se database não disponível.
    """
    return JurisIADB()


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    print("=" * 80)
    print("JURIS_IA_CORE_V1 - SISTEMA COMPLETO (DATABASE INTEGRATED)")
    print("=" * 80)

    try:
        # Inicializa sistema (falha se database não disponível)
        sistema = criar_juris_ia_db()

        print("\n✓ Sistema inicializado com sucesso!")
        print("✓ Todos os engines conectados ao PostgreSQL")
        print("✓ Todas as interações serão persistidas")
        print("\nSistema pronto para uso em produção!")

    except RuntimeError as e:
        print(f"\n✗ ERRO: {str(e)}")
        print("  Configure o database e tente novamente.")

    except Exception as e:
        print(f"\n✗ ERRO INESPERADO: {str(e)}")
        import traceback
        traceback.print_exc()
