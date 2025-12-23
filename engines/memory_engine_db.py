"""
JURIS_IA_CORE_V1 - MEMORY ENGINE (Database-Integrated)
=======================================================

Motor de Memória e Revisão Espaçada com persistência em PostgreSQL.

Este é a versão integrada com banco de dados do Memory Engine.
Todas as revisões, progressos e análises são persistidas.

DIFERENÇAS DA VERSÃO ORIGINAL:
- Dados persistem em PostgreSQL via SQLAlchemy
- Usa repositories para acesso aos dados
- Integra com perfil cognitivo jurídico
- Suporta snapshots cognitivos
- LGPD-compliant

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 2.0.0 (Database-Integrated)
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID
import logging

# Adicionar path do projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import (
    NivelDominio, TipoResposta, TipoTriggerSnapshot
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATABASE-INTEGRATED MEMORY ENGINE
# ============================================================================

class MemoryEngineDB:
    """
    Motor de memória e revisão espaçada integrado com banco de dados.

    Funcionalidades:
    - Agenda revisões no ciclo 1-24-7-30
    - Ajusta intervalo baseado em desempenho (armazenado em DB)
    - Detecta esquecimento analisando progressos
    - Prioriza itens com memória frágil
    - Gera sessões de revisão otimizadas
    - PERSISTE TUDO no PostgreSQL
    """

    def __init__(self):
        """Inicializa o motor de memória"""
        logger.info("MemoryEngineDB inicializado (database-integrated)")

    def adicionar_topico_memoria(
        self,
        user_id: UUID,
        disciplina: str,
        topico: str,
        acertou_na_introducao: bool = True
    ) -> Dict:
        """
        Adiciona novo tópico para rastreamento de memória.

        Args:
            user_id: ID do usuário
            disciplina: Disciplina jurídica
            topico: Tópico aprendido
            acertou_na_introducao: Se acertou na primeira exposição

        Returns:
            Dict com informações do tópico e cronograma
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar ou criar progresso do tópico
                progresso = repos.progressos_topico.get_or_create(
                    user_id=user_id,
                    disciplina=disciplina,
                    topico=topico
                )

                # Criar primeira revisão agendada (1 hora depois)
                agora = datetime.utcnow()
                primeira_revisao = repos.revisoes_agendadas.create(
                    user_id=user_id,
                    disciplina=disciplina,
                    topico=topico,
                    data_agendada=agora + timedelta(hours=1),
                    intervalo_dias=0,  # Primeira revisão
                    numero_revisao=1,
                    fator_facilidade=0.6 if acertou_na_introducao else 0.3
                )

                # Calcular cronograma completo 1-24-7-30
                cronograma = {
                    "1h": (agora + timedelta(hours=1)).isoformat(),
                    "24h": (agora + timedelta(hours=24)).isoformat(),
                    "7d": (agora + timedelta(days=7)).isoformat(),
                    "30d": (agora + timedelta(days=30)).isoformat()
                }

                logger.info(
                    f"Tópico '{topico}' adicionado à memória do usuário {user_id}"
                )

                return {
                    "status": "adicionado",
                    "topico": topico,
                    "disciplina": disciplina,
                    "progresso_id": str(progresso.id),
                    "revisao_id": str(primeira_revisao.id),
                    "cronograma": cronograma,
                    "fator_retencao": float(progresso.fator_retencao)
                }

        except Exception as e:
            logger.error(f"Erro ao adicionar tópico à memória: {e}")
            return {"erro": str(e)}

    def processar_revisao(
        self,
        user_id: UUID,
        disciplina: str,
        topico: str,
        acertou: bool,
        questao_id: Optional[UUID] = None
    ) -> Dict:
        """
        Processa resultado de uma revisão.

        Args:
            user_id: ID do usuário
            disciplina: Disciplina
            topico: Tópico revisado
            acertou: Se o usuário acertou a revisão
            questao_id: ID da questão (opcional)

        Returns:
            Dict com status e próxima revisão
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Atualizar progresso do tópico com lógica de repetição espaçada
                progresso = repos.progressos_topico.update_after_interaction(
                    user_id=user_id,
                    disciplina=disciplina,
                    topico=topico,
                    acertou=acertou
                )

                # Buscar revisão agendada atual (se houver)
                revisoes_pendentes = self._buscar_revisoes_pendentes(
                    session, user_id, disciplina, topico
                )

                if revisoes_pendentes:
                    # Marcar como concluída
                    revisao = revisoes_pendentes[0]
                    revisao.concluida = True
                    revisao.data_conclusao = datetime.utcnow()
                    revisao.resultado_revisao = (
                        TipoResposta.CORRETA if acertou else TipoResposta.INCORRETA
                    )

                    # Calcular próximo intervalo
                    if acertou:
                        novo_intervalo = int(
                            revisao.intervalo_dias * (1.5 + float(progresso.fator_retencao))
                        )
                    else:
                        novo_intervalo = 1  # Reset para 1 dia

                    revisao.proximo_intervalo_calculado = novo_intervalo

                # Criar próxima revisão
                proxima_revisao = repos.revisoes_agendadas.create(
                    user_id=user_id,
                    disciplina=disciplina,
                    topico=topico,
                    questao_id=questao_id,
                    data_agendada=progresso.proxima_revisao_calculada,
                    intervalo_dias=progresso.intervalo_revisao_dias,
                    numero_revisao=progresso.numero_revisoes,
                    fator_facilidade=progresso.fator_retencao
                )

                # Atualizar estado emocional se erro
                if not acertou:
                    perfil = repos.perfis.get_by_user_id(user_id)
                    if perfil:
                        # Diminuir confiança levemente
                        confianca_atual = perfil.estado_emocional.get("confianca", 0.5)
                        repos.perfis.update_emotional_state(
                            user_id=user_id,
                            confianca=max(0.1, confianca_atual - 0.05)
                        )

                logger.info(
                    f"Revisão processada: {topico} - {'ACERTO' if acertou else 'ERRO'}"
                )

                return {
                    "status": "processado",
                    "acertou": acertou,
                    "forca_retencao": float(progresso.fator_retencao),
                    "taxa_acerto_topico": float(progresso.taxa_acerto),
                    "proxima_revisao": progresso.proxima_revisao_calculada.isoformat(),
                    "intervalo_dias": progresso.intervalo_revisao_dias,
                    "numero_revisoes": progresso.numero_revisoes
                }

        except Exception as e:
            logger.error(f"Erro ao processar revisão: {e}")
            return {"erro": str(e)}

    def obter_revisoes_pendentes(
        self,
        user_id: UUID,
        limite: int = 10,
        disciplina: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtém revisões que precisam ser feitas agora.

        Args:
            user_id: ID do usuário
            limite: Número máximo de revisões
            disciplina: Filtrar por disciplina (opcional)

        Returns:
            Lista de revisões pendentes, priorizadas
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar revisões agendadas pendentes
                agora = datetime.utcnow()

                query = session.query(
                    repos.revisoes_agendadas.model_class
                ).filter(
                    repos.revisoes_agendadas.model_class.user_id == user_id,
                    repos.revisoes_agendadas.model_class.concluida == False,
                    repos.revisoes_agendadas.model_class.data_agendada <= agora
                )

                if disciplina:
                    query = query.filter(
                        repos.revisoes_agendadas.model_class.disciplina == disciplina
                    )

                revisoes = query.order_by(
                    repos.revisoes_agendadas.model_class.data_agendada.asc()
                ).limit(limite).all()

                # Converter para dict
                resultado = []
                for revisao in revisoes:
                    # Calcular prioridade
                    atraso_horas = (agora - revisao.data_agendada).total_seconds() / 3600
                    prioridade = self._calcular_prioridade_revisao(
                        revisao.numero_revisao,
                        atraso_horas,
                        float(revisao.fator_facilidade)
                    )

                    resultado.append({
                        "revisao_id": str(revisao.id),
                        "disciplina": revisao.disciplina,
                        "topico": revisao.topico,
                        "data_agendada": revisao.data_agendada.isoformat(),
                        "atraso_horas": round(atraso_horas, 1),
                        "numero_revisao": revisao.numero_revisao,
                        "prioridade": round(prioridade, 2)
                    })

                # Ordenar por prioridade
                resultado.sort(key=lambda x: x["prioridade"], reverse=True)

                return resultado

        except Exception as e:
            logger.error(f"Erro ao obter revisões pendentes: {e}")
            return []

    def analisar_memoria(self, user_id: UUID) -> Dict:
        """
        Analisa estado da memória do usuário através do banco de dados.

        Returns:
            Dict com estatísticas de memória
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # Buscar todos os progressos de tópicos
                progressos = repos.progressos_topico.session.query(
                    repos.progressos_topico.model_class
                ).filter(
                    repos.progressos_topico.model_class.user_id == user_id
                ).all()

                if not progressos:
                    return {"total_topicos": 0, "status": "nenhum_dado"}

                # Estatísticas gerais
                total_topicos = len(progressos)

                # Distribuição por força de retenção
                frageis = sum(1 for p in progressos if p.fator_retencao < 0.4)
                fracos = sum(1 for p in progressos if 0.4 <= p.fator_retencao < 0.6)
                medios = sum(1 for p in progressos if 0.6 <= p.fator_retencao < 0.8)
                fortes = sum(1 for p in progressos if p.fator_retencao >= 0.8)

                # Tópicos atrasados
                agora = datetime.utcnow()
                atrasados = sum(
                    1 for p in progressos
                    if p.proxima_revisao_calculada and p.proxima_revisao_calculada < agora
                )

                # Tópicos dominados (taxa acerto > 80% e fator > 0.8)
                dominados = [
                    p.topico for p in progressos
                    if p.taxa_acerto >= 80.0 and p.fator_retencao >= 0.8
                ]

                # Tópicos críticos (taxa acerto < 50% ou fator < 0.3)
                criticos = [
                    {"topico": p.topico, "disciplina": p.disciplina, "taxa_acerto": float(p.taxa_acerto)}
                    for p in progressos
                    if p.taxa_acerto < 50.0 or p.fator_retencao < 0.3
                ]

                # Próxima revisão mais urgente
                proxima_urgente = min(
                    (p for p in progressos if p.proxima_revisao_calculada),
                    key=lambda p: p.proxima_revisao_calculada,
                    default=None
                )

                # Taxa de retenção geral
                taxa_retencao_media = sum(
                    float(p.fator_retencao) for p in progressos
                ) / total_topicos if total_topicos > 0 else 0.0

                return {
                    "total_topicos": total_topicos,
                    "distribuicao_forca": {
                        "FRAGIL": frageis,
                        "FRACA": fracos,
                        "MEDIA": medios,
                        "FORTE": fortes
                    },
                    "topicos_atrasados": atrasados,
                    "topicos_dominados": dominados,
                    "topicos_criticos": criticos,
                    "taxa_retencao_media": round(taxa_retencao_media * 100, 1),
                    "proxima_revisao_urgente": (
                        proxima_urgente.proxima_revisao_calculada.isoformat()
                        if proxima_urgente else None
                    )
                }

        except Exception as e:
            logger.error(f"Erro ao analisar memória: {e}")
            return {"erro": str(e)}

    def detectar_esquecimento(self, user_id: UUID) -> List[Dict]:
        """
        Detecta conceitos que o usuário está esquecendo através de análise do DB.

        Returns:
            Lista de alertas de esquecimento
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                alertas = []
                agora = datetime.utcnow()

                # Buscar progressos de tópicos
                progressos = repos.progressos_topico.session.query(
                    repos.progressos_topico.model_class
                ).filter(
                    repos.progressos_topico.model_class.user_id == user_id
                ).all()

                for progresso in progressos:
                    # Caso 1: Regressão de memória (tinha boa retenção, mas caiu)
                    if (progresso.fator_retencao < 0.4 and
                        progresso.numero_revisoes >= 3):
                        alertas.append({
                            "tipo": "regressao",
                            "topico": progresso.topico,
                            "disciplina": progresso.disciplina,
                            "gravidade": "ALTA",
                            "fator_retencao": float(progresso.fator_retencao),
                            "mensagem": f"Conceito {progresso.topico} está sendo esquecido - reforço urgente"
                        })

                    # Caso 2: Revisão muito atrasada
                    if progresso.proxima_revisao_calculada:
                        atraso = agora - progresso.proxima_revisao_calculada
                        atraso_horas = atraso.total_seconds() / 3600

                        if atraso_horas > 48:  # 2 dias
                            alertas.append({
                                "tipo": "atraso_critico",
                                "topico": progresso.topico,
                                "disciplina": progresso.disciplina,
                                "gravidade": "MEDIA",
                                "atraso_horas": int(atraso_horas),
                                "mensagem": f"Revisão de {progresso.topico} atrasada há {int(atraso_horas)}h"
                            })

                    # Caso 3: Taxa de acerto muito baixa
                    if progresso.total_questoes >= 5 and progresso.taxa_acerto < 40.0:
                        alertas.append({
                            "tipo": "dificuldade_persistente",
                            "topico": progresso.topico,
                            "disciplina": progresso.disciplina,
                            "gravidade": "ALTA",
                            "taxa_acerto": float(progresso.taxa_acerto),
                            "mensagem": f"{progresso.topico} com taxa de acerto de {progresso.taxa_acerto:.1f}% - base conceitual frágil"
                        })

                # Ordenar por gravidade
                ordem_gravidade = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}
                alertas.sort(key=lambda x: ordem_gravidade.get(x["gravidade"], 3))

                logger.info(f"Detecção de esquecimento: {len(alertas)} alertas gerados")

                return alertas

        except Exception as e:
            logger.error(f"Erro ao detectar esquecimento: {e}")
            return []

    def gerar_sessao_revisao_otimizada(
        self,
        user_id: UUID,
        duracao_minutos: int = 30,
        disciplina: Optional[str] = None
    ) -> Dict:
        """
        Gera sessão de revisão otimizada baseada em dados do DB.

        Args:
            user_id: ID do usuário
            duracao_minutos: Duração desejada em minutos
            disciplina: Filtrar por disciplina (opcional)

        Returns:
            Dict com configuração da sessão
        """
        try:
            # Estima quantos itens cabem (média 3min/item)
            qtd_itens = duracao_minutos // 3

            # Obter revisões pendentes priorizadas
            revisoes = self.obter_revisoes_pendentes(
                user_id=user_id,
                limite=qtd_itens,
                disciplina=disciplina
            )

            # Calcular distribuição por disciplina
            disciplinas_contagem = {}
            for revisao in revisoes:
                disc = revisao["disciplina"]
                disciplinas_contagem[disc] = disciplinas_contagem.get(disc, 0) + 1

            return {
                "status": "gerada",
                "total_itens": len(revisoes),
                "duracao_estimada_minutos": len(revisoes) * 3,
                "disciplinas": disciplinas_contagem,
                "revisoes": revisoes,
                "recomendacao": self._gerar_recomendacao_sessao(revisoes)
            }

        except Exception as e:
            logger.error(f"Erro ao gerar sessão de revisão: {e}")
            return {"erro": str(e)}

    # ========================================================================
    # MÉTODOS PRIVADOS
    # ========================================================================

    def _buscar_revisoes_pendentes(self, session, user_id: UUID, disciplina: str, topico: str):
        """Busca revisões pendentes de um tópico específico"""
        from database.models import RevisaoAgendada

        return session.query(RevisaoAgendada).filter(
            RevisaoAgendada.user_id == user_id,
            RevisaoAgendada.disciplina == disciplina,
            RevisaoAgendada.topico == topico,
            RevisaoAgendada.concluida == False
        ).order_by(RevisaoAgendada.data_agendada.asc()).all()

    def _calcular_prioridade_revisao(
        self,
        numero_revisao: int,
        atraso_horas: float,
        fator_facilidade: float
    ) -> float:
        """
        Calcula prioridade de uma revisão.

        Quanto maior, mais urgente.
        """
        # Base: inversamente proporcional ao fator de facilidade
        prioridade = (1.0 - fator_facilidade) * 10

        # Fator de atraso (exponencial)
        if atraso_horas > 0:
            prioridade += min(atraso_horas / 24, 5)

        # Primeiras revisões são mais importantes
        if numero_revisao <= 3:
            prioridade += (4 - numero_revisao)

        return prioridade

    def _gerar_recomendacao_sessao(self, revisoes: List[Dict]) -> str:
        """Gera recomendação baseada nas revisões"""
        if not revisoes:
            return "Nenhuma revisão pendente no momento. Continue estudando novos tópicos!"

        total = len(revisoes)
        atrasadas = sum(1 for r in revisoes if r["atraso_horas"] > 24)

        if atrasadas > total / 2:
            return f"Atenção: {atrasadas} revisões atrasadas! Priorize estas antes de novos conteúdos."

        urgentes = sum(1 for r in revisoes if r["prioridade"] > 8)
        if urgentes > 0:
            return f"Foco: {urgentes} revisões urgentes detectadas. Revisar agora para evitar esquecimento."

        return f"Boa! {total} revisões no momento certo para consolidar o aprendizado."


# ============================================================================
# FUNÇÃO AUXILIAR
# ============================================================================

def criar_memory_engine_db() -> MemoryEngineDB:
    """Factory function para criar memory engine com DB"""
    return MemoryEngineDB()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("MEMORY ENGINE DB - EXEMPLO DE USO (Database-Integrated)")
    print("=" * 70)

    # Cria engine
    engine = criar_memory_engine_db()

    # NOTA: Para rodar este exemplo, você precisa:
    # 1. PostgreSQL rodando
    # 2. Variáveis de ambiente configuradas (.env)
    # 3. Banco de dados criado (python database/setup.py --full-setup)
    # 4. Um usuário existente no banco

    print("\n⚠️  Este exemplo requer banco de dados configurado.")
    print("Execute: python database/setup.py --full-setup")
    print("\nPara testar com usuário real, obtenha user_id do banco e use as funções:")
    print("  - engine.adicionar_topico_memoria()")
    print("  - engine.processar_revisao()")
    print("  - engine.obter_revisoes_pendentes()")
    print("  - engine.analisar_memoria()")
    print("  - engine.detectar_esquecimento()")

    print("\n" + "=" * 70)
    print("MEMORY ENGINE DB - OPERACIONAL (Database-Integrated)")
    print("=" * 70)
