"""
JURIS_IA_CORE_V1 - QUESTION ENGINE (Database-Integrated)
=========================================================

Motor de Seleção Inteligente de Questões com persistência em PostgreSQL.

Funcionalidades DATABASE-CENTRIC:
- Seleção baseada em perfil cognitivo persistido
- Análise de histórico de erros do banco
- Priorização por revisões agendadas
- Ajuste dinâmico de dificuldade baseado em dados reais
- Geração de drills e simulados personalizados

DIFERENÇAS DA VERSÃO ORIGINAL:
- Questões carregadas do PostgreSQL (questoes_banco)
- Seleção baseada em progresso_topico e progresso_disciplina
- Histórico completo em interacao_questao
- Integração com sistema de revisão espaçada
- Métricas de dificuldade real baseadas em taxa_acerto_geral

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 2.0.0 (Database-Integrated)
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import random
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import (
    NivelDominio, DificuldadeQuestao, TipoResposta
)

logger = logging.getLogger(__name__)


class QuestionEngineDB:
    """
    Motor de seleção inteligente de questões integrado com banco de dados.

    Funcionalidades:
    - Seleciona questões baseadas em perfil cognitivo
    - Prioriza tópicos fracos e em revisão
    - Ajusta dificuldade dinamicamente
    - Gera drills focados
    - Cria simulados balanceados
    - Persiste ordem e resultados
    """

    def __init__(self):
        """Inicializa o motor de questões"""
        logger.info("QuestionEngineDB inicializado (database-integrated)")

    def selecionar_proximas_questoes(
        self,
        user_id: UUID,
        quantidade: int = 10,
        disciplina: Optional[str] = None,
        foco: str = "adaptativo"
    ) -> Dict:
        """
        Seleciona próximas questões adaptadas ao perfil do usuário.

        Args:
            user_id: ID do usuário
            quantidade: Número de questões a selecionar
            disciplina: Filtrar por disciplina específica
            foco: Tipo de seleção ("adaptativo", "revisao", "conceito", "velocidade")

        Returns:
            Dict com questões selecionadas e estratégia
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar perfil do usuário
                perfil = repos.perfis.get_by_user_id(user_id)
                if not perfil:
                    return {"erro": "Perfil não encontrado"}

                # Determinar estratégia de seleção baseada no foco
                if foco == "revisao":
                    questoes = self._selecionar_para_revisao(
                        session, user_id, quantidade, disciplina
                    )
                elif foco == "conceito":
                    questoes = self._selecionar_conceituais(
                        session, user_id, quantidade, disciplina
                    )
                elif foco == "velocidade":
                    questoes = self._selecionar_velocidade(
                        session, user_id, quantidade, disciplina
                    )
                else:  # adaptativo
                    questoes = self._selecionar_adaptativo(
                        session, user_id, perfil, quantidade, disciplina
                    )

                # Persistir seleção
                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "QUESTOES_SELECIONADAS",
                        "detalhes": {
                            "foco": foco,
                            "quantidade": len(questoes),
                            "questoes_ids": [str(q["id"]) for q in questoes],
                            "disciplina": disciplina,
                            "nivel_perfil": perfil.nivel_geral.value
                        }
                    }
                )

                logger.info(
                    f"Selecionadas {len(questoes)} questões para user {user_id} (foco: {foco})"
                )

                return {
                    "status": "selecionadas",
                    "quantidade": len(questoes),
                    "foco": foco,
                    "questoes": questoes,
                    "tempo_estimado_minutos": len(questoes) * 3,
                    "nivel_perfil": perfil.nivel_geral.value
                }

        except Exception as e:
            logger.error(f"Erro ao selecionar questões: {e}")
            return {"erro": str(e)}

    def gerar_drill_personalizado(
        self,
        user_id: UUID,
        disciplina: Optional[str] = None,
        topico: Optional[str] = None,
        quantidade: int = 10
    ) -> Dict:
        """
        Gera drill personalizado baseado em pontos fracos do usuário.

        Args:
            user_id: ID do usuário
            disciplina: Disciplina específica (opcional)
            topico: Tópico específico (opcional)
            quantidade: Número de questões

        Returns:
            Dict com drill configurado
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Identificar pontos fracos
                disciplinas_fracas = repos.progressos_disciplina.get_weakest_disciplines(
                    user_id, limit=3
                )

                # Se disciplina não especificada, focar em pontos fracos
                if not disciplina and disciplinas_fracas:
                    disciplina = disciplinas_fracas[0].disciplina

                # Buscar tópicos com baixa performance
                topicos_fracos = []
                if disciplina:
                    topicos = repos.progressos_topico.session.query(
                        repos.progressos_topico.model_class
                    ).filter(
                        repos.progressos_topico.model_class.user_id == user_id,
                        repos.progressos_topico.model_class.disciplina == disciplina,
                        repos.progressos_topico.model_class.taxa_acerto < 60.0
                    ).order_by(
                        repos.progressos_topico.model_class.taxa_acerto.asc()
                    ).limit(5).all()

                    topicos_fracos = [t.topico for t in topicos]

                # Selecionar questões focadas nos pontos fracos
                questoes = self._selecionar_por_topicos_fracos(
                    session, topicos_fracos or [topico] if topico else [],
                    disciplina, quantidade
                )

                # Criar drill no log
                drill_id = f"drill_{user_id}_{datetime.utcnow().timestamp()}"

                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "DRILL_GERADO",
                        "detalhes": {
                            "drill_id": drill_id,
                            "disciplina": disciplina,
                            "topico": topico,
                            "topicos_fracos": topicos_fracos,
                            "quantidade_questoes": len(questoes),
                            "questoes_ids": [str(q["id"]) for q in questoes]
                        }
                    }
                )

                return {
                    "status": "gerado",
                    "drill_id": drill_id,
                    "disciplina": disciplina,
                    "topico": topico,
                    "topicos_fracos_foco": topicos_fracos,
                    "questoes": questoes,
                    "quantidade": len(questoes),
                    "tempo_estimado_minutos": len(questoes) * 3
                }

        except Exception as e:
            logger.error(f"Erro ao gerar drill: {e}")
            return {"erro": str(e)}

    def gerar_simulado(
        self,
        user_id: UUID,
        tipo: str = "completo"
    ) -> Dict:
        """
        Gera simulado OAB balanceado.

        Args:
            user_id: ID do usuário
            tipo: "completo" (80 questões) ou "medio" (40 questões)

        Returns:
            Dict com simulado configurado
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Distribuição OAB padrão
                if tipo == "completo":
                    distribuicao = {
                        "Direito Constitucional": 10,
                        "Direito Civil": 12,
                        "Direito Processual Civil": 10,
                        "Direito Penal": 10,
                        "Direito Processual Penal": 8,
                        "Direito do Trabalho": 8,
                        "Direito Empresarial": 6,
                        "Direito Tributário": 6,
                        "Direito Administrativo": 5,
                        "Direitos Humanos": 3,
                        "Ética e Estatuto": 2
                    }
                else:  # medio
                    distribuicao = {
                        "Direito Constitucional": 5,
                        "Direito Civil": 6,
                        "Direito Processual Civil": 5,
                        "Direito Penal": 5,
                        "Direito Processual Penal": 4,
                        "Direito do Trabalho": 4,
                        "Direito Empresarial": 3,
                        "Direito Tributário": 3,
                        "Direito Administrativo": 3,
                        "Direitos Humanos": 1,
                        "Ética e Estatuto": 1
                    }

                # Selecionar questões por disciplina
                todas_questoes = []
                for disciplina, qtd in distribuicao.items():
                    questoes_disc = self._selecionar_questoes_disciplina(
                        session, disciplina, qtd
                    )
                    todas_questoes.extend(questoes_disc)

                # Embaralhar questões
                random.shuffle(todas_questoes)

                # Criar simulado
                simulado_id = f"sim_{user_id}_{datetime.utcnow().timestamp()}"

                repos.session.execute(
                    """
                    INSERT INTO log_sistema (user_id, evento, detalhes)
                    VALUES (:user_id, :evento, :detalhes)
                    """,
                    {
                        "user_id": user_id,
                        "evento": "SIMULADO_GERADO",
                        "detalhes": {
                            "simulado_id": simulado_id,
                            "tipo": tipo,
                            "total_questoes": len(todas_questoes),
                            "distribuicao": distribuicao,
                            "questoes_ids": [str(q["id"]) for q in todas_questoes]
                        }
                    }
                )

                return {
                    "status": "gerado",
                    "simulado_id": simulado_id,
                    "tipo": tipo,
                    "questoes": todas_questoes,
                    "total_questoes": len(todas_questoes),
                    "distribuicao": distribuicao,
                    "tempo_limite_minutos": 300 if tipo == "completo" else 150
                }

        except Exception as e:
            logger.error(f"Erro ao gerar simulado: {e}")
            return {"erro": str(e)}

    def ajustar_dificuldade_dinamica(
        self,
        user_id: UUID,
        disciplina: Optional[str] = None
    ) -> Dict:
        """
        Calcula dificuldade ideal baseada em desempenho recente.

        Args:
            user_id: ID do usuário
            disciplina: Disciplina específica (opcional)

        Returns:
            Dict com dificuldade recomendada
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar últimas 20 interações
                query = repos.interacoes.session.query(
                    repos.interacoes.model_class
                ).filter(
                    repos.interacoes.model_class.user_id == user_id
                )

                if disciplina:
                    query = query.filter(
                        repos.interacoes.model_class.disciplina == disciplina
                    )

                interacoes = query.order_by(
                    repos.interacoes.model_class.created_at.desc()
                ).limit(20).all()

                if len(interacoes) < 5:
                    return {
                        "dificuldade": "MEDIO",
                        "motivo": "Dados insuficientes"
                    }

                # Calcular taxa de acerto recente
                acertos = sum(
                    1 for i in interacoes
                    if i.tipo_resposta == TipoResposta.CORRETA
                )
                taxa = acertos / len(interacoes)

                # Determinar dificuldade
                if taxa >= 0.80:
                    dificuldade = "DIFICIL"
                    motivo = f"Taxa de acerto alta ({taxa*100:.1f}%) - aumentar desafio"
                elif taxa >= 0.60:
                    dificuldade = "MEDIO"
                    motivo = f"Taxa de acerto adequada ({taxa*100:.1f}%)"
                elif taxa >= 0.40:
                    dificuldade = "MEDIO"
                    motivo = f"Taxa de acerto moderada ({taxa*100:.1f}%)"
                else:
                    dificuldade = "FACIL"
                    motivo = f"Taxa de acerto baixa ({taxa*100:.1f}%) - reduzir dificuldade"

                return {
                    "dificuldade": dificuldade,
                    "taxa_acerto_recente": round(taxa * 100, 1),
                    "total_analisado": len(interacoes),
                    "motivo": motivo
                }

        except Exception as e:
            logger.error(f"Erro ao ajustar dificuldade: {e}")
            return {"erro": str(e)}

    # ========================================================================
    # MÉTODOS PRIVADOS - SELEÇÃO
    # ========================================================================

    def _selecionar_adaptativo(
        self, session, user_id: UUID, perfil, quantidade: int, disciplina: Optional[str]
    ) -> List[Dict]:
        """Seleção adaptativa baseada no perfil completo"""

        # Determinar dificuldade ideal pelo nível
        if perfil.nivel_geral in [NivelDominio.INICIANTE, NivelDominio.BASICO]:
            dificuldade_alvo = DificuldadeQuestao.FACIL
        elif perfil.nivel_geral == NivelDominio.INTERMEDIARIO:
            dificuldade_alvo = DificuldadeQuestao.MEDIO
        else:
            dificuldade_alvo = DificuldadeQuestao.DIFICIL

        # Mix: 60% na dificuldade alvo, 40% variado
        qtd_alvo = int(quantidade * 0.6)
        qtd_variado = quantidade - qtd_alvo

        questoes = []

        # Questões da dificuldade alvo
        questoes.extend(
            self._buscar_questoes_por_dificuldade(
                session, dificuldade_alvo, disciplina, qtd_alvo
            )
        )

        # Questões variadas
        questoes.extend(
            self._buscar_questoes_variadas(session, disciplina, qtd_variado)
        )

        random.shuffle(questoes)
        return questoes[:quantidade]

    def _selecionar_para_revisao(
        self, session, user_id: UUID, quantidade: int, disciplina: Optional[str]
    ) -> List[Dict]:
        """Seleciona questões de tópicos que precisam revisão"""
        repos = RepositoryFactory(session)

        # Buscar tópicos que precisam revisão
        topicos_revisao = repos.progressos_topico.get_topics_due_for_review(
            user_id, limit=10
        )

        if not topicos_revisao:
            # Se não há revisões pendentes, seleciona aleatório
            return self._buscar_questoes_variadas(session, disciplina, quantidade)

        # Selecionar questões dos tópicos em revisão
        topicos = [t.topico for t in topicos_revisao]
        return self._selecionar_por_topicos_fracos(
            session, topicos, disciplina, quantidade
        )

    def _selecionar_conceituais(
        self, session, user_id: UUID, quantidade: int, disciplina: Optional[str]
    ) -> List[Dict]:
        """Seleciona questões conceituais de tópicos fracos"""
        repos = RepositoryFactory(session)

        # Buscar tópicos com baixa taxa de acerto
        query = repos.progressos_topico.session.query(
            repos.progressos_topico.model_class
        ).filter(
            repos.progressos_topico.model_class.user_id == user_id,
            repos.progressos_topico.model_class.taxa_acerto < 60.0
        )

        if disciplina:
            query = query.filter(
                repos.progressos_topico.model_class.disciplina == disciplina
            )

        topicos_fracos = query.order_by(
            repos.progressos_topico.model_class.taxa_acerto.asc()
        ).limit(5).all()

        topicos = [t.topico for t in topicos_fracos]

        if not topicos:
            return self._buscar_questoes_variadas(session, disciplina, quantidade)

        return self._selecionar_por_topicos_fracos(
            session, topicos, disciplina, quantidade
        )

    def _selecionar_velocidade(
        self, session, user_id: UUID, quantidade: int, disciplina: Optional[str]
    ) -> List[Dict]:
        """Seleciona questões fáceis para treinar velocidade"""
        return self._buscar_questoes_por_dificuldade(
            session, DificuldadeQuestao.FACIL, disciplina, quantidade
        )

    def _selecionar_por_topicos_fracos(
        self, session, topicos: List[str], disciplina: Optional[str], quantidade: int
    ) -> List[Dict]:
        """Seleciona questões de tópicos específicos"""
        from database.models import QuestaoBanco

        query = session.query(QuestaoBanco).filter(
            QuestaoBanco.ativa == True
        )

        if topicos:
            query = query.filter(QuestaoBanco.topico.in_(topicos))

        if disciplina:
            query = query.filter(QuestaoBanco.disciplina == disciplina)

        questoes_obj = query.limit(quantidade * 2).all()

        # Converter para dict
        questoes = []
        for q in questoes_obj:
            questoes.append({
                "id": q.id,
                "codigo": q.codigo_questao,
                "enunciado": q.enunciado,
                "alternativas": q.alternativas,
                "alternativa_correta": q.alternativa_correta,
                "disciplina": q.disciplina,
                "topico": q.topico,
                "dificuldade": q.dificuldade.value,
                "explicacao": q.explicacao_detalhada
            })

        random.shuffle(questoes)
        return questoes[:quantidade]

    def _buscar_questoes_por_dificuldade(
        self, session, dificuldade: DificuldadeQuestao, disciplina: Optional[str], quantidade: int
    ) -> List[Dict]:
        """Busca questões por dificuldade"""
        from database.models import QuestaoBanco

        query = session.query(QuestaoBanco).filter(
            QuestaoBanco.dificuldade == dificuldade,
            QuestaoBanco.ativa == True
        )

        if disciplina:
            query = query.filter(QuestaoBanco.disciplina == disciplina)

        questoes_obj = query.limit(quantidade * 2).all()

        questoes = []
        for q in questoes_obj:
            questoes.append({
                "id": q.id,
                "codigo": q.codigo_questao,
                "enunciado": q.enunciado,
                "alternativas": q.alternativas,
                "alternativa_correta": q.alternativa_correta,
                "disciplina": q.disciplina,
                "topico": q.topico,
                "dificuldade": q.dificuldade.value,
                "explicacao": q.explicacao_detalhada
            })

        random.shuffle(questoes)
        return questoes[:quantidade]

    def _buscar_questoes_variadas(
        self, session, disciplina: Optional[str], quantidade: int
    ) -> List[Dict]:
        """Busca questões variadas (mix de dificuldades)"""
        from database.models import QuestaoBanco

        query = session.query(QuestaoBanco).filter(
            QuestaoBanco.ativa == True
        )

        if disciplina:
            query = query.filter(QuestaoBanco.disciplina == disciplina)

        questoes_obj = query.limit(quantidade * 3).all()

        questoes = []
        for q in questoes_obj:
            questoes.append({
                "id": q.id,
                "codigo": q.codigo_questao,
                "enunciado": q.enunciado,
                "alternativas": q.alternativas,
                "alternativa_correta": q.alternativa_correta,
                "disciplina": q.disciplina,
                "topico": q.topico,
                "dificuldade": q.dificuldade.value,
                "explicacao": q.explicacao_detalhada
            })

        random.shuffle(questoes)
        return questoes[:quantidade]

    def _selecionar_questoes_disciplina(
        self, session, disciplina: str, quantidade: int
    ) -> List[Dict]:
        """Seleciona questões de uma disciplina específica"""
        from database.models import QuestaoBanco

        questoes_obj = session.query(QuestaoBanco).filter(
            QuestaoBanco.disciplina == disciplina,
            QuestaoBanco.ativa == True
        ).limit(quantidade * 2).all()

        questoes = []
        for q in questoes_obj:
            questoes.append({
                "id": q.id,
                "codigo": q.codigo_questao,
                "enunciado": q.enunciado,
                "alternativas": q.alternativas,
                "alternativa_correta": q.alternativa_correta,
                "disciplina": q.disciplina,
                "topico": q.topico,
                "dificuldade": q.dificuldade.value,
                "explicacao": q.explicacao_detalhada
            })

        random.shuffle(questoes)
        return questoes[:quantidade]


def criar_question_engine_db() -> QuestionEngineDB:
    """Factory function para criar question engine DB"""
    return QuestionEngineDB()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("QUESTION ENGINE DB - Operacional (Database-Integrated)")
    print("=" * 70)
    print("\nEngine pronta para seleção inteligente de questões do banco de dados.")
    print("Utilize as funções:")
    print("  - selecionar_proximas_questoes()")
    print("  - gerar_drill_personalizado()")
    print("  - gerar_simulado()")
    print("  - ajustar_dificuldade_dinamica()")
