"""
================================================================================
HEAVY USER ESCAPE VALVE - JURIS_IA_CORE_V1
================================================================================
Extensão do módulo de enforcement para válvula de escape de heavy users.

Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
Data: 2025-12-19
================================================================================
"""

from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class HeavyUserEscapeValve:
    """Gerenciador de válvula de escape para heavy users"""

    def __init__(self, database_url: str):
        """
        Inicializa válvula de escape.

        Args:
            database_url: URL de conexão PostgreSQL
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def is_enabled(self) -> bool:
        """
        Verifica se feature está habilitada globalmente.

        Returns:
            True se habilitada, False caso contrário
        """
        session = self.Session()
        try:
            result = session.execute(
                text("""
                    SELECT enabled
                    FROM feature_flags
                    WHERE flag_name = 'heavy_user_escape_valve'
                    LIMIT 1
                """)
            ).fetchone()

            if not result:
                # Se não existe flag, assume desabilitado
                return False

            return result[0]

        except Exception:
            # Se tabela não existe ou erro, assume desabilitado
            return False
        finally:
            session.close()

    def check_and_activate(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica e ativa escape para heavy user se critérios atendidos.

        Args:
            user_id: UUID do usuário

        Returns:
            Dict com resultado da verificação
        """
        if not self.is_enabled():
            return {
                "activated": False,
                "reason": "Feature desabilitada",
                "extra_sessions": 0
            }

        session = self.Session()
        try:
            result = session.execute(
                text("SELECT * FROM verificar_heavy_user_escape(:user_id)"),
                {"user_id": user_id}
            ).fetchone()

            if not result:
                return {
                    "activated": False,
                    "reason": "Erro ao verificar critérios",
                    "extra_sessions": 0
                }

            escape_ativado, motivo, sessoes_extras, sessoes_7dias = result

            return {
                "activated": escape_ativado,
                "reason": motivo,
                "extra_sessions": sessoes_extras,
                "sessions_last_7_days": sessoes_7dias
            }

        finally:
            session.close()

    def can_use_extra_session(self, user_id: str) -> bool:
        """
        Verifica se usuário pode usar sessão extra de heavy user hoje.

        Args:
            user_id: UUID do usuário

        Returns:
            True se pode usar, False caso contrário
        """
        if not self.is_enabled():
            return False

        session = self.Session()
        try:
            result = session.execute(
                text("SELECT pode_usar_sessao_extra_heavy_user(:user_id)"),
                {"user_id": user_id}
            ).scalar()

            return result or False

        finally:
            session.close()

    def get_activations_log(
        self,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Obtém log de ativações do escape valve.

        Args:
            user_id: Filtrar por usuário (opcional)
            limit: Limite de registros

        Returns:
            Lista de ativações
        """
        session = self.Session()
        try:
            if user_id:
                result = session.execute(
                    text("""
                        SELECT
                            id,
                            user_id,
                            plano_codigo,
                            data_ativacao,
                            criterio_atendido,
                            sessoes_ultimos_7_dias,
                            sessoes_extras_concedidas,
                            metadata
                        FROM heavy_user_escape_log
                        WHERE user_id = :user_id
                        ORDER BY data_ativacao DESC
                        LIMIT :limit
                    """),
                    {"user_id": user_id, "limit": limit}
                ).fetchall()
            else:
                result = session.execute(
                    text("""
                        SELECT
                            id,
                            user_id,
                            plano_codigo,
                            data_ativacao,
                            criterio_atendido,
                            sessoes_ultimos_7_dias,
                            sessoes_extras_concedidas,
                            metadata
                        FROM heavy_user_escape_log
                        ORDER BY data_ativacao DESC
                        LIMIT :limit
                    """),
                    {"limit": limit}
                ).fetchall()

            return [
                {
                    "id": str(row[0]),
                    "user_id": str(row[1]),
                    "plan": row[2],
                    "activated_at": row[3].isoformat(),
                    "criterion": row[4],
                    "sessions_7days": row[5],
                    "extra_sessions_granted": row[6],
                    "metadata": row[7]
                }
                for row in result
            ]

        finally:
            session.close()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas de uso do escape valve.

        Returns:
            Dict com estatísticas
        """
        session = self.Session()
        try:
            # Total de ativações
            total = session.execute(
                text("SELECT COUNT(*) FROM heavy_user_escape_log")
            ).scalar()

            # Ativações hoje
            hoje = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM heavy_user_escape_log
                    WHERE DATE(data_ativacao AT TIME ZONE 'America/Sao_Paulo') = CURRENT_DATE
                """)
            ).scalar()

            # Ativações últimos 7 dias
            ultimos_7 = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM heavy_user_escape_log
                    WHERE data_ativacao >= CURRENT_DATE - INTERVAL '6 days'
                """)
            ).scalar()

            # Usuários únicos que já ativaram
            usuarios_unicos = session.execute(
                text("SELECT COUNT(DISTINCT user_id) FROM heavy_user_escape_log")
            ).scalar()

            # Média de sessões nos últimos 7 dias (dos que ativaram)
            media_sessoes = session.execute(
                text("""
                    SELECT AVG(sessoes_ultimos_7_dias)::INTEGER
                    FROM heavy_user_escape_log
                """)
            ).scalar()

            return {
                "total_activations": total or 0,
                "activations_today": hoje or 0,
                "activations_last_7_days": ultimos_7 or 0,
                "unique_users": usuarios_unicos or 0,
                "avg_sessions_7days": media_sessoes or 0,
                "feature_enabled": self.is_enabled()
            }

        finally:
            session.close()

    def enable(self) -> None:
        """Habilita feature globalmente"""
        session = self.Session()
        try:
            session.execute(
                text("""
                    UPDATE feature_flags
                    SET enabled = true, updated_at = NOW()
                    WHERE flag_name = 'heavy_user_escape_valve'
                """)
            )
            session.commit()
        finally:
            session.close()

    def disable(self) -> None:
        """Desabilita feature globalmente"""
        session = self.Session()
        try:
            session.execute(
                text("""
                    UPDATE feature_flags
                    SET enabled = false, updated_at = NOW()
                    WHERE flag_name = 'heavy_user_escape_valve'
                """)
            )
            session.commit()
        finally:
            session.close()
