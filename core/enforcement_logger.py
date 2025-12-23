"""
================================================================================
LOGGER DE ENFORCEMENT - JURIS_IA_CORE_V1
================================================================================
Módulo responsável por registrar todos os eventos de bloqueio para:
- Auditoria
- Análise de BI
- Detecção de padrões
- Otimização de limites

Autor: JURIS_IA_CORE_V1 - Engenheiro de Enforcement
Data: 2025-12-19
================================================================================
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class EnforcementLogger:
    """Logger centralizado para eventos de enforcement"""

    def __init__(self, database_url: str):
        """
        Inicializa logger com conexão ao banco.

        Args:
            database_url: URL de conexão PostgreSQL
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

        # Criar tabela de log se não existir
        self._create_log_table()

    def _create_log_table(self):
        """Cria tabela de log de bloqueios se não existir"""
        session = self.Session()
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS enforcement_log (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    endpoint VARCHAR(255) NOT NULL,
                    reason_code VARCHAR(100) NOT NULL,
                    plano_codigo VARCHAR(50),
                    current_usage INTEGER,
                    limit_value INTEGER,
                    ip_address INET,
                    user_agent TEXT,
                    request_id VARCHAR(100),
                    metadata JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_enforcement_log_user
                ON enforcement_log(user_id, timestamp DESC);

                CREATE INDEX IF NOT EXISTS idx_enforcement_log_reason
                ON enforcement_log(reason_code, timestamp DESC);

                CREATE INDEX IF NOT EXISTS idx_enforcement_log_endpoint
                ON enforcement_log(endpoint, timestamp DESC);

                CREATE INDEX IF NOT EXISTS idx_enforcement_log_plano
                ON enforcement_log(plano_codigo, timestamp DESC);

                CREATE INDEX IF NOT EXISTS idx_enforcement_log_timestamp
                ON enforcement_log(timestamp DESC);

                COMMENT ON TABLE enforcement_log IS 'Log de todos os bloqueios de enforcement para auditoria e BI';
                COMMENT ON COLUMN enforcement_log.reason_code IS 'Código do motivo do bloqueio (ex: LIMIT_SESSIONS_DAILY)';
                COMMENT ON COLUMN enforcement_log.current_usage IS 'Uso atual quando bloqueado (ex: 5 sessões)';
                COMMENT ON COLUMN enforcement_log.limit_value IS 'Limite do plano (ex: 5 sessões)';
                COMMENT ON COLUMN enforcement_log.metadata IS 'Dados adicionais em JSON (ex: session_id, etc)';
            """))
            session.commit()
        except Exception as e:
            session.rollback()
            # Tabela já existe, ok
            pass
        finally:
            session.close()

    def log_block(
        self,
        user_id: str,
        endpoint: str,
        reason_code: str,
        current_usage: int = 0,
        limit: int = 0,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra evento de bloqueio.

        Args:
            user_id: UUID do usuário
            endpoint: Endpoint que bloqueou
            reason_code: Código do motivo
            current_usage: Uso atual
            limit: Limite do plano
            ip_address: IP da requisição
            user_agent: User agent da requisição
            request_id: ID da requisição (correlação)
            metadata: Dados adicionais
        """
        session = self.Session()
        try:
            # Buscar código do plano do usuário
            plano_result = session.execute(
                text("""
                    SELECT p.codigo
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

            plano_codigo = plano_result[0] if plano_result else None

            # Inserir log
            session.execute(
                text("""
                    INSERT INTO enforcement_log (
                        user_id,
                        endpoint,
                        reason_code,
                        plano_codigo,
                        current_usage,
                        limit_value,
                        ip_address,
                        user_agent,
                        request_id,
                        metadata
                    ) VALUES (
                        :user_id,
                        :endpoint,
                        :reason_code,
                        :plano_codigo,
                        :current_usage,
                        :limit_value,
                        :ip_address,
                        :user_agent,
                        :request_id,
                        :metadata
                    )
                """),
                {
                    "user_id": user_id,
                    "endpoint": endpoint,
                    "reason_code": reason_code,
                    "plano_codigo": plano_codigo,
                    "current_usage": current_usage,
                    "limit_value": limit,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "request_id": request_id,
                    "metadata": json.dumps(metadata) if metadata else None
                }
            )
            session.commit()

        except Exception as e:
            session.rollback()
            # Falha no log não deve quebrar o fluxo principal
            print(f"[WARN] Erro ao registrar log de enforcement: {e}")

        finally:
            session.close()

    def get_blocks_by_user(
        self,
        user_id: str,
        limit: int = 100
    ) -> list:
        """
        Obtém bloqueios de um usuário.

        Args:
            user_id: UUID do usuário
            limit: Limite de registros

        Returns:
            Lista de bloqueios
        """
        session = self.Session()
        try:
            result = session.execute(
                text("""
                    SELECT
                        id,
                        timestamp,
                        endpoint,
                        reason_code,
                        plano_codigo,
                        current_usage,
                        limit_value,
                        request_id,
                        metadata
                    FROM enforcement_log
                    WHERE user_id = :user_id
                    ORDER BY timestamp DESC
                    LIMIT :limit
                """),
                {"user_id": user_id, "limit": limit}
            ).fetchall()

            return [
                {
                    "id": str(row[0]),
                    "timestamp": row[1].isoformat(),
                    "endpoint": row[2],
                    "reason_code": row[3],
                    "plano_codigo": row[4],
                    "current_usage": row[5],
                    "limit": row[6],
                    "request_id": row[7],
                    "metadata": row[8]
                }
                for row in result
            ]

        finally:
            session.close()

    def get_aggregated_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas agregadas de bloqueios.

        Args:
            start_date: Data inicial (default: 30 dias atrás)
            end_date: Data final (default: agora)

        Returns:
            Dict com estatísticas
        """
        session = self.Session()
        try:
            if not start_date:
                start_date = datetime.now().replace(day=datetime.now().day - 30)
            if not end_date:
                end_date = datetime.now()

            # Bloqueios por dia
            blocks_per_day = session.execute(
                text("""
                    SELECT
                        DATE(timestamp) as dia,
                        COUNT(*) as total
                    FROM enforcement_log
                    WHERE timestamp >= :start_date
                      AND timestamp <= :end_date
                    GROUP BY DATE(timestamp)
                    ORDER BY dia DESC
                """),
                {"start_date": start_date, "end_date": end_date}
            ).fetchall()

            # Bloqueios por plano
            blocks_per_plan = session.execute(
                text("""
                    SELECT
                        plano_codigo,
                        COUNT(*) as total
                    FROM enforcement_log
                    WHERE timestamp >= :start_date
                      AND timestamp <= :end_date
                      AND plano_codigo IS NOT NULL
                    GROUP BY plano_codigo
                    ORDER BY total DESC
                """),
                {"start_date": start_date, "end_date": end_date}
            ).fetchall()

            # Bloqueios por motivo
            blocks_per_reason = session.execute(
                text("""
                    SELECT
                        reason_code,
                        COUNT(*) as total
                    FROM enforcement_log
                    WHERE timestamp >= :start_date
                      AND timestamp <= :end_date
                    GROUP BY reason_code
                    ORDER BY total DESC
                """),
                {"start_date": start_date, "end_date": end_date}
            ).fetchall()

            # Bloqueios por endpoint
            blocks_per_endpoint = session.execute(
                text("""
                    SELECT
                        endpoint,
                        COUNT(*) as total
                    FROM enforcement_log
                    WHERE timestamp >= :start_date
                      AND timestamp <= :end_date
                    GROUP BY endpoint
                    ORDER BY total DESC
                """),
                {"start_date": start_date, "end_date": end_date}
            ).fetchall()

            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "blocks_per_day": [
                    {"date": row[0].isoformat(), "total": row[1]}
                    for row in blocks_per_day
                ],
                "blocks_per_plan": [
                    {"plan": row[0], "total": row[1]}
                    for row in blocks_per_plan
                ],
                "blocks_per_reason": [
                    {"reason": row[0], "total": row[1]}
                    for row in blocks_per_reason
                ],
                "blocks_per_endpoint": [
                    {"endpoint": row[0], "total": row[1]}
                    for row in blocks_per_endpoint
                ]
            }

        finally:
            session.close()
