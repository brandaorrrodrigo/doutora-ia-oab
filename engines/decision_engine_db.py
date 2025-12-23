"""
JURIS_IA_CORE_V1 - DECISION ENGINE (Database-Integrated)
=========================================================

Motor de Decisão Inteligente com persistência em PostgreSQL.

Processa eventos do estudante e decide quais ações executar:
- Analisa perfil cognitivo persistido
- Decide mudanças de nível
- Ativa revisões agendadas
- Recomenda aprofundamento
- Persiste TODAS as decisões e justificativas

DIFERENÇAS DA VERSÃO ORIGINAL:
- Decisões persistem no log_sistema
- Estado lido do banco (perfil_juridico, progresso_*)
- Mudanças de nível persistidas
- Histórico completo de decisões rastreável
- Integração com outros engines DB

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 2.0.0 (Database-Integrated)
"""

import sys
import os
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import (
    NivelDominio, TipoResposta, TipoErro, TipoTriggerSnapshot
)

logger = logging.getLogger(__name__)


class EventType:
    """Tipos de eventos"""
    ERRO = "erro"
    ERRO_REPETIDO = "erro_repetido"
    ACERTO = "acerto"
    ACERTO_SEQUENCIAL = "acerto_sequencial"
    TEMPO_EXCESSIVO = "tempo_excessivo"
    RESPOSTA_RAPIDA = "resposta_rapida"
    BLOCO_COMPLETO = "bloco_completo"
    DISCIPLINA_COMPLETA = "disciplina_completa"
    SIMULADO_COMPLETO = "simulado_completo"
    REGRESSAO_DETECTADA = "regressao_detectada"
    MELHORA_DETECTADA = "melhora_detectada"
    PECA_INICIADA = "peca_iniciada"
    PECA_COMPLETA = "peca_completa"


class ActionType:
    """Tipos de ações possíveis"""
    GERAR_DRILL = "gerar_drill"
    AGENDAR_REVISAO = "agendar_revisao"
    EXPLICAR_ERRO = "explicar_erro"
    AJUSTAR_NIVEL = "ajustar_nivel"
    CRIAR_SNAPSHOT = "criar_snapshot"
    APROFUNDAR_TOPICO = "aprofundar_topico"
    SUGERIR_PAUSA = "sugerir_pausa"
    PARABENIZAR = "parabenizar"
    ALERTAR_REGRESSAO = "alertar_regressao"


class DecisionEngineDB:
    """
    Motor de decisão inteligente integrado com banco de dados.

    Funcionalidades:
    - Processa eventos do estudante
    - Analisa perfil cognitivo do banco
    - Decide ações baseadas em dados históricos
    - Persiste TODAS as decisões
    - Registra justificativas
    - Detecta padrões complexos
    """

    def __init__(self):
        """Inicializa o motor de decisão"""
        logger.info("DecisionEngineDB inicializado (database-integrated)")

    def processar_evento(
        self,
        user_id: UUID,
        evento_tipo: str,
        contexto: Dict[str, Any]
    ) -> Dict:
        """
        Processa um evento e retorna ações recomendadas.

        Args:
            user_id: ID do usuário
            evento_tipo: Tipo do evento
            contexto: Contexto adicional do evento

        Returns:
            Dict com ações priorizadas e justificativas
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar perfil
                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {"erro": "Perfil não encontrado"}

                # Analisar evento e gerar ações
                acoes = self._analisar_e_gerar_acoes(
                    session, repos, user_id, perfil, evento_tipo, contexto
                )

                # Persistir evento e decisões
                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "DECISAO_PROCESSADA",
                        "detalhes": {
                            "evento_tipo": evento_tipo,
                            "contexto": contexto,
                            "acoes_geradas": len(acoes),
                            "acoes": [
                                {
                                    "tipo": a["tipo"],
                                    "prioridade": a["prioridade"],
                                    "justificativa": a["justificativa"]
                                }
                                for a in acoes
                            ]
                        }
                    }
                )

                logger.info(
                    f"Evento processado: {evento_tipo} para user {user_id} - {len(acoes)} ações geradas"
                )

                return {
                    "status": "processado",
                    "evento_tipo": evento_tipo,
                    "acoes": acoes,
                    "perfil_nivel": perfil.nivel_geral.value
                }

        except Exception as e:
            logger.error(f"Erro ao processar evento: {e}")
            return {"erro": str(e)}

    def avaliar_mudanca_nivel(
        self,
        user_id: UUID
    ) -> Dict:
        """
        Avalia se usuário deve mudar de nível e executa mudança se apropriado.

        Args:
            user_id: ID do usuário

        Returns:
            Dict com decisão e justificativa
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {"erro": "Perfil não encontrado"}

                nivel_atual = perfil.nivel_geral
                taxa_acerto = float(perfil.taxa_acerto_global)

                # Regras de mudança de nível
                novo_nivel = None
                justificativa = ""

                # Subir nível
                if taxa_acerto >= 80.0 and perfil.total_questoes_respondidas >= 50:
                    if nivel_atual == NivelDominio.INICIANTE:
                        novo_nivel = NivelDominio.BASICO
                        justificativa = f"Taxa de acerto {taxa_acerto:.1f}% com {perfil.total_questoes_respondidas} questões - promovido a BÁSICO"
                    elif nivel_atual == NivelDominio.BASICO:
                        novo_nivel = NivelDominio.INTERMEDIARIO
                        justificativa = f"Consistência demonstrada - promovido a INTERMEDIÁRIO"
                    elif nivel_atual == NivelDominio.INTERMEDIARIO:
                        novo_nivel = NivelDominio.AVANCADO
                        justificativa = f"Domínio consolidado - promovido a AVANÇADO"
                    elif nivel_atual == NivelDominio.AVANCADO and perfil.total_questoes_respondidas >= 200:
                        novo_nivel = NivelDominio.EXPERT
                        justificativa = f"Excelência comprovada - promovido a EXPERT"

                # Descer nível (apenas se regressão significativa)
                elif taxa_acerto < 40.0 and perfil.total_questoes_respondidas >= 30:
                    if nivel_atual == NivelDominio.EXPERT:
                        novo_nivel = NivelDominio.AVANCADO
                        justificativa = f"Regressão detectada ({taxa_acerto:.1f}%) - ajustado para AVANÇADO"
                    elif nivel_atual == NivelDominio.AVANCADO:
                        novo_nivel = NivelDominio.INTERMEDIARIO
                        justificativa = f"Regressão significativa - ajustado para INTERMEDIÁRIO"

                # Executar mudança se necessário
                if novo_nivel and novo_nivel != nivel_atual:
                    perfil.nivel_geral = novo_nivel

                    # Criar snapshot da mudança
                    repos.snapshots.create_snapshot(
                        user_id=user_id,
                        tipo_trigger=TipoTriggerSnapshot.MUDANCA_NIVEL,
                        perfil_completo={
                            "nivel_anterior": nivel_atual.value,
                            "nivel_novo": novo_nivel.value,
                            "taxa_acerto": taxa_acerto,
                            "total_questoes": perfil.total_questoes_respondidas
                        },
                        desempenho={
                            "taxa_acerto": taxa_acerto,
                            "questoes": perfil.total_questoes_respondidas
                        },
                        padroes_erro={},
                        estado_memoria={},
                        predicao={},
                        contexto_momento={
                            "tipo": "mudanca_nivel",
                            "justificativa": justificativa
                        }
                    )

                    # Registrar decisão
                    repos.session.execute(
                        """
                        INSERT INTO log_sistema (user_id, evento, detalhes)
                        VALUES (:user_id, :evento, :detalhes)
                        """,
                        {
                            "user_id": user_id,
                            "evento": "MUDANCA_NIVEL",
                            "detalhes": {
                                "nivel_anterior": nivel_atual.value,
                                "nivel_novo": novo_nivel.value,
                                "justificativa": justificativa,
                                "taxa_acerto": taxa_acerto,
                                "total_questoes": perfil.total_questoes_respondidas
                            }
                        }
                    )

                    return {
                        "status": "nivel_alterado",
                        "nivel_anterior": nivel_atual.value,
                        "nivel_novo": novo_nivel.value,
                        "justificativa": justificativa
                    }

                else:
                    return {
                        "status": "nivel_mantido",
                        "nivel_atual": nivel_atual.value,
                        "motivo": f"Taxa de acerto {taxa_acerto:.1f}% com {perfil.total_questoes_respondidas} questões - nível adequado"
                    }

        except Exception as e:
            logger.error(f"Erro ao avaliar mudança de nível: {e}")
            return {"erro": str(e)}

    def recomendar_acoes_personalizadas(
        self,
        user_id: UUID
    ) -> Dict:
        """
        Gera recomendações personalizadas baseadas em análise completa do perfil.

        Args:
            user_id: ID do usuário

        Returns:
            Dict com recomendações priorizadas
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {"erro": "Perfil não encontrado"}

                recomendacoes = []

                # Análise de performance
                taxa_acerto = float(perfil.taxa_acerto_global)

                if taxa_acerto < 50.0:
                    recomendacoes.append({
                        "prioridade": 10,
                        "tipo": "voltar_fundamentos",
                        "titulo": "Volte aos fundamentos",
                        "descricao": f"Taxa de acerto de {taxa_acerto:.1f}% indica base conceitual frágil. Recomendamos revisar conceitos fundamentais antes de prosseguir.",
                        "acoes": [
                            "Estudar teoria dos tópicos com mais erros",
                            "Fazer questões fáceis para consolidar base",
                            "Utilizar explicações no nível PRÁTICO"
                        ]
                    })

                # Análise de disciplinas fracas
                disciplinas_fracas = repos.progressos_disciplina.get_weakest_disciplines(
                    user_id, limit=3
                )

                if disciplinas_fracas:
                    disc_nomes = [d.disciplina for d in disciplinas_fracas]
                    recomendacoes.append({
                        "prioridade": 8,
                        "tipo": "reforcar_disciplinas",
                        "titulo": f"Reforçar {len(disciplinas_fracas)} disciplinas",
                        "descricao": f"Disciplinas que precisam de atenção: {', '.join(disc_nomes)}",
                        "acoes": [
                            f"Drill focado em {d.disciplina} (taxa: {d.taxa_acerto:.1f}%)"
                            for d in disciplinas_fracas
                        ]
                    })

                # Análise de revisões pendentes
                revisoes_pendentes = repos.revisoes_agendadas.session.query(
                    repos.revisoes_agendadas.model_class
                ).filter(
                    repos.revisoes_agendadas.model_class.user_id == user_id,
                    repos.revisoes_agendadas.model_class.concluida == False,
                    repos.revisoes_agendadas.model_class.data_agendada <= datetime.utcnow()
                ).count()

                if revisoes_pendentes > 0:
                    recomendacoes.append({
                        "prioridade": 9,
                        "tipo": "revisar_pendente",
                        "titulo": f"{revisoes_pendentes} revisões pendentes",
                        "descricao": "Revisões agendadas aguardando conclusão. Revisar antes de avançar.",
                        "acoes": [
                            "Completar revisões pendentes",
                            "Priorizar tópicos com mais atraso"
                        ]
                    })

                # Análise de estado emocional
                estado_emocional = perfil.estado_emocional
                confianca = estado_emocional.get("confianca", 0.5)
                stress = estado_emocional.get("stress", 0.5)
                motivacao = estado_emocional.get("motivacao", 0.7)

                if stress > 0.7:
                    recomendacoes.append({
                        "prioridade": 7,
                        "tipo": "reduzir_stress",
                        "titulo": "Nível de stress elevado",
                        "descricao": "Detectado stress alto. Recomendamos pausa e ajuste de ritmo.",
                        "acoes": [
                            "Fazer pausa de 15-30 minutos",
                            "Reduzir quantidade de questões por sessão",
                            "Focar em questões fáceis para recuperar confiança"
                        ]
                    })

                if motivacao < 0.3:
                    recomendacoes.append({
                        "prioridade": 6,
                        "tipo": "motivacao",
                        "titulo": "Manter motivação",
                        "descricao": "Celebre suas conquistas! Você já respondeu {perfil.total_questoes_respondidas} questões.",
                        "acoes": [
                            "Revisar progresso alcançado",
                            "Fazer drill em tópico já dominado",
                            "Definir metas pequenas e alcançáveis"
                        ]
                    })

                # Ordenar por prioridade
                recomendacoes.sort(key=lambda r: r["prioridade"], reverse=True)

                # Persistir geração de recomendações
                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "RECOMENDACOES_GERADAS",
                        "detalhes": {
                            "total_recomendacoes": len(recomendacoes),
                            "recomendacoes": recomendacoes
                        }
                    }
                )

                return {
                    "status": "geradas",
                    "total": len(recomendacoes),
                    "recomendacoes": recomendacoes
                }

        except Exception as e:
            logger.error(f"Erro ao gerar recomendações: {e}")
            return {"erro": str(e)}

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    def _analisar_e_gerar_acoes(
        self, session, repos, user_id: UUID, perfil, evento_tipo: str, contexto: Dict
    ) -> List[Dict]:
        """Analisa evento e gera ações apropriadas"""

        acoes = []

        # ERRO - Gerar explicação e drill
        if evento_tipo == EventType.ERRO:
            tipo_erro = contexto.get("tipo_erro")
            topico = contexto.get("topico")

            acoes.append({
                "tipo": ActionType.EXPLICAR_ERRO,
                "prioridade": 9,
                "justificativa": f"Erro detectado em {topico} - explicação necessária",
                "parametros": {
                    "topico": topico,
                    "tipo_erro": tipo_erro,
                    "nivel": self._nivel_explicacao_por_perfil(perfil.nivel_geral)
                }
            })

        # ERRO REPETIDO - Drill intensivo
        elif evento_tipo == EventType.ERRO_REPETIDO:
            topico = contexto.get("topico")

            acoes.append({
                "tipo": ActionType.GERAR_DRILL,
                "prioridade": 10,
                "justificativa": f"Erro repetido em {topico} - drill de fixação urgente",
                "parametros": {
                    "topico": topico,
                    "quantidade": 10,
                    "foco": "conceito"
                }
            })

            acoes.append({
                "tipo": ActionType.APROFUNDAR_TOPICO,
                "prioridade": 9,
                "justificativa": "Conceito não consolidado - aprofundamento necessário",
                "parametros": {
                    "topico": topico,
                    "modo": "teoria_intensiva"
                }
            })

        # BLOCO COMPLETO - Agendar revisão
        elif evento_tipo == EventType.BLOCO_COMPLETO:
            topico = contexto.get("topico")

            acoes.append({
                "tipo": ActionType.AGENDAR_REVISAO,
                "prioridade": 8,
                "justificativa": "Bloco completo - ativar ciclo de revisão espaçada 1-24-7",
                "parametros": {
                    "topico": topico,
                    "primeira_revisao": "1h"
                }
            })

        # ACERTO SEQUENCIAL - Parabenizar e aumentar dificuldade
        elif evento_tipo == EventType.ACERTO_SEQUENCIAL:
            acoes.append({
                "tipo": ActionType.PARABENIZAR,
                "prioridade": 5,
                "justificativa": "Sequência de acertos - reforço positivo",
                "parametros": {
                    "tipo": "acertos_consecutivos"
                }
            })

            acoes.append({
                "tipo": ActionType.AJUSTAR_NIVEL,
                "prioridade": 6,
                "justificativa": "Desempenho consistente - aumentar desafio",
                "parametros": {
                    "direcao": "aumentar_dificuldade"
                }
            })

        # SIMULADO COMPLETO - Criar snapshot
        elif evento_tipo == EventType.SIMULADO_COMPLETO:
            acoes.append({
                "tipo": ActionType.CRIAR_SNAPSHOT,
                "prioridade": 8,
                "justificativa": "Simulado completo - registrar estado cognitivo",
                "parametros": {
                    "tipo_trigger": "FIM_SIMULADO",
                    "contexto": contexto
                }
            })

        # REGRESSAO DETECTADA - Alerta e ajuste
        elif evento_tipo == EventType.REGRESSAO_DETECTADA:
            acoes.append({
                "tipo": ActionType.ALERTAR_REGRESSAO,
                "prioridade": 10,
                "justificativa": "Regressão de desempenho - intervenção urgente",
                "parametros": {
                    "topico": contexto.get("topico"),
                    "queda_performance": contexto.get("queda_percentual")
                }
            })

            acoes.append({
                "tipo": ActionType.GERAR_DRILL,
                "prioridade": 9,
                "justificativa": "Recuperar nível anterior",
                "parametros": {
                    "foco": "revisao",
                    "topico": contexto.get("topico")
                }
            })

        # Ordenar por prioridade
        acoes.sort(key=lambda a: a["prioridade"], reverse=True)

        return acoes[:5]  # Top 5 ações

    def _nivel_explicacao_por_perfil(self, nivel_dominio: NivelDominio) -> int:
        """Determina nível ideal de explicação"""
        if nivel_dominio in [NivelDominio.INICIANTE, NivelDominio.BASICO]:
            return 4  # Prática
        elif nivel_dominio == NivelDominio.INTERMEDIARIO:
            return 2  # Didática
        else:
            return 1  # Técnica


def criar_decision_engine_db() -> DecisionEngineDB:
    """Factory function para criar decision engine DB"""
    return DecisionEngineDB()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("DECISION ENGINE DB - Operacional (Database-Integrated)")
    print("=" * 70)
    print("\nEngine pronta para processar eventos e tomar decisões pedagógicas.")
    print("Utilize as funções:")
    print("  - processar_evento()")
    print("  - avaliar_mudanca_nivel()")
    print("  - recomendar_acoes_personalizadas()")
