"""
================================================================================
ENFORCEMENT DE LIMITES - JURIS_IA_CORE_V1
================================================================================
Módulo responsável por:
- Verificar limites de uso por plano
- Aplicar bloqueios consistentes
- Gerar respostas padronizadas
- Registrar eventos de bloqueio

Autor: JURIS_IA_CORE_V1 - Engenheiro de Enforcement
Data: 2025-12-19
================================================================================
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date
from enum import Enum
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from core.enforcement_messages import EnforcementMessages
from core.enforcement_logger import EnforcementLogger
from core.enforcement_heavy_user import HeavyUserEscapeValve


class ReasonCode(str, Enum):
    """Códigos padronizados de bloqueio"""
    # Sessões
    LIMIT_SESSIONS_DAILY = "LIMIT_SESSIONS_DAILY"
    LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED = "LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED"

    # Questões
    LIMIT_QUESTIONS_SESSION = "LIMIT_QUESTIONS_SESSION"
    LIMIT_QUESTIONS_DAILY = "LIMIT_QUESTIONS_DAILY"

    # Peças
    LIMIT_PIECE_WEEKLY = "LIMIT_PIECE_WEEKLY"
    LIMIT_PIECE_MONTHLY = "LIMIT_PIECE_MONTHLY"

    # Relatórios
    FEATURE_REPORT_COMPLETE_NOT_ALLOWED = "FEATURE_REPORT_COMPLETE_NOT_ALLOWED"

    # Acesso
    NO_ACTIVE_SUBSCRIPTION = "NO_ACTIVE_SUBSCRIPTION"
    SUBSCRIPTION_EXPIRED = "SUBSCRIPTION_EXPIRED"
    FEATURE_MODE_PROFESSIONAL_NOT_ALLOWED = "FEATURE_MODE_PROFESSIONAL_NOT_ALLOWED"

    # Heavy User Escape Valve
    HEAVY_USER_EXTRA_SESSION_GRANTED = "HEAVY_USER_EXTRA_SESSION_GRANTED"


class EnforcementResult:
    """Resultado de verificação de enforcement"""

    def __init__(
        self,
        allowed: bool,
        reason_code: Optional[ReasonCode] = None,
        message_title: Optional[str] = None,
        message_body: Optional[str] = None,
        upgrade_suggestion: Optional[str] = None,
        next_reset: Optional[datetime] = None,
        plan_recommendation: str = "OAB_SEMESTRAL",
        current_usage: int = 0,
        limit: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.allowed = allowed
        self.reason_code = reason_code
        self.message_title = message_title
        self.message_body = message_body
        self.upgrade_suggestion = upgrade_suggestion
        self.next_reset = next_reset
        self.plan_recommendation = plan_recommendation
        self.current_usage = current_usage
        self.limit = limit
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (resposta API)"""
        if self.allowed:
            return {
                "allowed": True,
                "current_usage": self.current_usage,
                "limit": self.limit
            }

        return {
            "blocked": True,
            "reason_code": self.reason_code.value if self.reason_code else None,
            "message_title": self.message_title,
            "message_body": self.message_body,
            "upgrade_suggestion": self.upgrade_suggestion,
            "next_reset": self.next_reset.isoformat() if self.next_reset else None,
            "plan_recommendation": self.plan_recommendation,
            "current_usage": self.current_usage,
            "limit": self.limit,
            **self.metadata
        }


class LimitsEnforcement:
    """Classe principal de enforcement de limites"""

    def __init__(self, database_url: str):
        """
        Inicializa enforcement com conexão ao banco.

        Args:
            database_url: URL de conexão PostgreSQL
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.messages = EnforcementMessages()
        self.logger = EnforcementLogger(database_url)
        self.heavy_user_escape = HeavyUserEscapeValve(database_url)

    def check_can_start_session(
        self,
        user_id: str,
        modo_estudo_continuo: bool = False,
        endpoint: str = "/estudo/iniciar",
        request_id: Optional[str] = None
    ) -> EnforcementResult:
        """
        Verifica se usuário pode iniciar nova sessão.

        Args:
            user_id: UUID do usuário
            modo_estudo_continuo: Se true, verifica permissão de estudo contínuo
            endpoint: Endpoint que solicitou (para log)
            request_id: ID da requisição (para correlação)

        Returns:
            EnforcementResult com decisão e mensagens
        """
        session = self.Session()
        try:
            # Chamar função SQL pode_iniciar_sessao
            result = session.execute(
                text("SELECT * FROM pode_iniciar_sessao(:user_id, :modo_estudo_continuo)"),
                {
                    "user_id": user_id,
                    "modo_estudo_continuo": modo_estudo_continuo
                }
            ).fetchone()

            if result is None:
                # Nenhum plano ativo
                reason = ReasonCode.NO_ACTIVE_SUBSCRIPTION
                msg = self.messages.get_message(reason)

                enforcement_result = EnforcementResult(
                    allowed=False,
                    reason_code=reason,
                    message_title=msg["title"],
                    message_body=msg["body"],
                    upgrade_suggestion=msg["upgrade"],
                    next_reset=None,
                    current_usage=0,
                    limit=0
                )

                # Log do bloqueio
                self.logger.log_block(
                    user_id=user_id,
                    endpoint=endpoint,
                    reason_code=reason,
                    current_usage=0,
                    limit=0,
                    request_id=request_id
                )

                return enforcement_result

            # Parse do resultado
            pode_iniciar, motivo, sessoes_usadas, sessoes_disponiveis = result

            if pode_iniciar:
                # Permitido
                return EnforcementResult(
                    allowed=True,
                    current_usage=sessoes_usadas,
                    limit=sessoes_usadas + sessoes_disponiveis
                )

            # Bloqueado - determinar reason_code baseado no motivo
            if "não permite estudo contínuo" in motivo.lower():
                reason = ReasonCode.LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED
            elif "limite de sessões diárias atingido" in motivo.lower():
                reason = ReasonCode.LIMIT_SESSIONS_DAILY
            elif "nenhuma assinatura ativa" in motivo.lower():
                reason = ReasonCode.NO_ACTIVE_SUBSCRIPTION
            else:
                reason = ReasonCode.LIMIT_SESSIONS_DAILY  # fallback

            # HEAVY USER ESCAPE VALVE
            # Se bloqueio é por limite diário, tentar ativar escape para heavy users
            if reason == ReasonCode.LIMIT_SESSIONS_DAILY:
                escape_result = self.heavy_user_escape.check_and_activate(user_id)

                if escape_result["activated"]:
                    # Escape ativado! Permitir sessão com mensagem especial
                    msg = self.messages.get_message(ReasonCode.HEAVY_USER_EXTRA_SESSION_GRANTED)

                    return EnforcementResult(
                        allowed=True,
                        current_usage=sessoes_usadas,
                        limit=sessoes_usadas + sessoes_disponiveis + escape_result["extra_sessions"],
                        metadata={
                            "heavy_user_escape_activated": True,
                            "escape_reason": escape_result["reason"],
                            "extra_sessions_granted": escape_result["extra_sessions"],
                            "sessions_last_7_days": escape_result["sessions_last_7_days"],
                            "message_title": msg["title"],
                            "message_body": msg["body"]
                        }
                    )

            # Escape não ativado ou outro motivo - prosseguir com bloqueio normal
            msg = self.messages.get_message(reason)

            # Calcular próximo reset (meia-noite)
            tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = tomorrow.replace(day=tomorrow.day + 1)

            enforcement_result = EnforcementResult(
                allowed=False,
                reason_code=reason,
                message_title=msg["title"],
                message_body=msg["body"],
                upgrade_suggestion=msg["upgrade"],
                next_reset=tomorrow,
                current_usage=sessoes_usadas,
                limit=sessoes_usadas + sessoes_disponiveis
            )

            # Log do bloqueio
            self.logger.log_block(
                user_id=user_id,
                endpoint=endpoint,
                reason_code=reason,
                current_usage=sessoes_usadas,
                limit=sessoes_usadas + sessoes_disponiveis,
                request_id=request_id
            )

            return enforcement_result

        finally:
            session.close()

    def check_can_answer_question(
        self,
        user_id: str,
        session_id: str,
        endpoint: str = "/estudo/responder",
        request_id: Optional[str] = None
    ) -> EnforcementResult:
        """
        Verifica se usuário pode responder mais uma questão na sessão.

        Args:
            user_id: UUID do usuário
            session_id: UUID da sessão ativa
            endpoint: Endpoint que solicitou
            request_id: ID da requisição

        Returns:
            EnforcementResult
        """
        session = self.Session()
        try:
            # Buscar sessão e plano
            result = session.execute(
                text("""
                    SELECT
                        se.total_questoes,
                        p.limite_questoes_por_sessao,
                        p.limite_questoes_dia
                    FROM sessao_estudo se
                    INNER JOIN assinatura a ON se.user_id = a.user_id
                    INNER JOIN plano p ON a.plano_id = p.id
                    WHERE se.id = :session_id
                      AND se.user_id = :user_id
                      AND a.status = 'active'
                      AND (a.data_fim IS NULL OR a.data_fim > NOW())
                    ORDER BY a.data_inicio DESC
                    LIMIT 1
                """),
                {"session_id": session_id, "user_id": user_id}
            ).fetchone()

            if not result:
                return EnforcementResult(
                    allowed=False,
                    reason_code=ReasonCode.NO_ACTIVE_SUBSCRIPTION,
                    message_title="Sessão inválida",
                    message_body="Sessão não encontrada ou assinatura inativa.",
                    upgrade_suggestion=None
                )

            total_questoes, limite_por_sessao, limite_dia = result

            # Verificar limite por sessão
            if total_questoes >= limite_por_sessao:
                reason = ReasonCode.LIMIT_QUESTIONS_SESSION
                msg = self.messages.get_message(reason)

                enforcement_result = EnforcementResult(
                    allowed=False,
                    reason_code=reason,
                    message_title=msg["title"],
                    message_body=msg["body"],
                    upgrade_suggestion=msg["upgrade"],
                    current_usage=total_questoes,
                    limit=limite_por_sessao
                )

                self.logger.log_block(
                    user_id=user_id,
                    endpoint=endpoint,
                    reason_code=reason,
                    current_usage=total_questoes,
                    limit=limite_por_sessao,
                    request_id=request_id,
                    metadata={"session_id": session_id}
                )

                return enforcement_result

            # Permitido
            return EnforcementResult(
                allowed=True,
                current_usage=total_questoes,
                limit=limite_por_sessao
            )

        finally:
            session.close()

    def check_can_practice_piece(
        self,
        user_id: str,
        endpoint: str = "/peca/iniciar",
        request_id: Optional[str] = None
    ) -> EnforcementResult:
        """
        Verifica se usuário pode iniciar prática de peça.

        Args:
            user_id: UUID do usuário
            endpoint: Endpoint que solicitou
            request_id: ID da requisição

        Returns:
            EnforcementResult
        """
        session = self.Session()
        try:
            # Buscar limite mensal de peças e uso atual
            result = session.execute(
                text("""
                    SELECT
                        p.limite_peca_mes,
                        (
                            SELECT COUNT(*)
                            FROM pratica_peca pp
                            WHERE pp.user_id = :user_id
                              AND pp.criado_em >= DATE_TRUNC('month', CURRENT_DATE)
                        ) as pecas_mes
                    FROM assinatura a
                    INNER JOIN plano p ON a.plano_id = p.id
                    WHERE a.user_id = :user_id
                      AND a.status = 'active'
                      AND (a.data_fim IS NULL OR a.data_fim > NOW())
                    ORDER BY a.data_inicio DESC
                    LIMIT 1
                """),
                {"user_id": user_id}
            ).fetchone()

            if not result:
                reason = ReasonCode.NO_ACTIVE_SUBSCRIPTION
                msg = self.messages.get_message(reason)

                enforcement_result = EnforcementResult(
                    allowed=False,
                    reason_code=reason,
                    message_title=msg["title"],
                    message_body=msg["body"],
                    upgrade_suggestion=msg["upgrade"]
                )

                self.logger.log_block(
                    user_id=user_id,
                    endpoint=endpoint,
                    reason_code=reason,
                    current_usage=0,
                    limit=0,
                    request_id=request_id
                )

                return enforcement_result

            limite_mes, pecas_mes = result

            # Verificar limite
            if pecas_mes >= limite_mes:
                reason = ReasonCode.LIMIT_PIECE_MONTHLY
                msg = self.messages.get_message(reason)

                # Próximo reset = início do próximo mês
                next_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if next_month.month == 12:
                    next_month = next_month.replace(year=next_month.year + 1, month=1)
                else:
                    next_month = next_month.replace(month=next_month.month + 1)

                enforcement_result = EnforcementResult(
                    allowed=False,
                    reason_code=reason,
                    message_title=msg["title"],
                    message_body=msg["body"],
                    upgrade_suggestion=msg["upgrade"],
                    next_reset=next_month,
                    current_usage=pecas_mes,
                    limit=limite_mes
                )

                self.logger.log_block(
                    user_id=user_id,
                    endpoint=endpoint,
                    reason_code=reason,
                    current_usage=pecas_mes,
                    limit=limite_mes,
                    request_id=request_id
                )

                return enforcement_result

            # Permitido
            return EnforcementResult(
                allowed=True,
                current_usage=pecas_mes,
                limit=limite_mes
            )

        finally:
            session.close()

    def check_can_access_complete_report(
        self,
        user_id: str,
        endpoint: str = "/estudante/relatorio",
        request_id: Optional[str] = None
    ) -> EnforcementResult:
        """
        Verifica se usuário pode acessar relatório completo.

        Args:
            user_id: UUID do usuário
            endpoint: Endpoint que solicitou
            request_id: ID da requisição

        Returns:
            EnforcementResult
        """
        session = self.Session()
        try:
            # Buscar tipo de relatório permitido
            result = session.execute(
                text("""
                    SELECT p.acesso_relatorio_tipo
                    FROM assinatura a
                    INNER JOIN plano p ON a.plano_id = p.id
                    WHERE a.user_id = :user_id
                      AND a.status = 'active'
                      AND (a.data_fim IS NULL OR a.data_fim > NOW())
                    ORDER BY a.data_inicio DESC
                    LIMIT 1
                """),
                {"user_id": user_id}
            ).fetchone()

            if not result:
                reason = ReasonCode.NO_ACTIVE_SUBSCRIPTION
                msg = self.messages.get_message(reason)

                enforcement_result = EnforcementResult(
                    allowed=False,
                    reason_code=reason,
                    message_title=msg["title"],
                    message_body=msg["body"],
                    upgrade_suggestion=msg["upgrade"]
                )

                self.logger.log_block(
                    user_id=user_id,
                    endpoint=endpoint,
                    reason_code=reason,
                    current_usage=0,
                    limit=0,
                    request_id=request_id
                )

                return enforcement_result

            tipo_relatorio = result[0]

            # Se é "basico", bloqueia acesso a relatório completo
            if tipo_relatorio == 'basico':
                reason = ReasonCode.FEATURE_REPORT_COMPLETE_NOT_ALLOWED
                msg = self.messages.get_message(reason)

                enforcement_result = EnforcementResult(
                    allowed=False,
                    reason_code=reason,
                    message_title=msg["title"],
                    message_body=msg["body"],
                    upgrade_suggestion=msg["upgrade"]
                )

                self.logger.log_block(
                    user_id=user_id,
                    endpoint=endpoint,
                    reason_code=reason,
                    current_usage=0,
                    limit=0,
                    request_id=request_id,
                    metadata={"tipo_relatorio_atual": tipo_relatorio}
                )

                return enforcement_result

            # Permitido (completo ou nenhum - mas nenhum não deveria existir)
            return EnforcementResult(allowed=True)

        finally:
            session.close()
