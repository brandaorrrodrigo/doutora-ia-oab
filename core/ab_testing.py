"""
================================================================================
A/B TESTING - JURIS_IA_CORE_V1
================================================================================
Módulo para gerenciamento de experimentos A/B de pricing e limites.

Funcionalidades:
- Atribuição consistente de usuários a grupos
- Registro de métricas de experimento
- Consulta de configuração de experimento
- Habilitação/desabilitação de experimentos

Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing Avançado
Data: 2025-12-19
================================================================================
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


class ABTestingManager:
    """Gerenciador de experimentos A/B"""

    def __init__(self, database_url: str):
        """
        Inicializa gerenciador de A/B testing.

        Args:
            database_url: URL de conexão PostgreSQL
        """
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)

    def assign_user_to_group(
        self,
        experiment_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Atribui usuário a grupo de experimento (control ou variant).

        Args:
            experiment_name: Nome do experimento
            user_id: UUID do usuário

        Returns:
            Dict com group_name e is_new_assignment, ou None se experimento inativo
        """
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT * FROM atribuir_grupo_experimento(:experiment_name, :user_id)"),
                {
                    "experiment_name": experiment_name,
                    "user_id": user_id
                }
            ).fetchone()

            if not result or result[0] is None:
                return None

            group_assigned, is_new = result

            return {
                "group_name": group_assigned,
                "is_new_assignment": is_new
            }

        finally:
            session.close()

    def get_user_experiment_config(
        self,
        experiment_name: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração de experimento para usuário específico.

        Args:
            experiment_name: Nome do experimento
            user_id: UUID do usuário

        Returns:
            Dict com group_name e experiment_config, ou None se não participando
        """
        session = self.Session()
        try:
            result = session.execute(
                text("SELECT * FROM obter_config_experimento(:experiment_name, :user_id)"),
                {
                    "experiment_name": experiment_name,
                    "user_id": user_id
                }
            ).fetchone()

            if not result or result[0] is None:
                return None

            group_name, metadata = result

            return {
                "group_name": group_name,
                "config": metadata.get(group_name, {}) if metadata else {}
            }

        finally:
            session.close()

    def record_metric(
        self,
        experiment_name: str,
        user_id: str,
        metric_name: str,
        metric_value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Registra métrica de experimento para usuário.

        Args:
            experiment_name: Nome do experimento
            user_id: UUID do usuário
            metric_name: Nome da métrica (ex: conversion, retention_7d)
            metric_value: Valor da métrica
            metadata: Metadados adicionais (opcional)

        Returns:
            True se registrado com sucesso, False caso contrário
        """
        session = self.Session()
        try:
            result = session.execute(
                text("""
                    SELECT registrar_metrica_experimento(
                        :experiment_name,
                        :user_id,
                        :metric_name,
                        :metric_value,
                        :metadata
                    )
                """),
                {
                    "experiment_name": experiment_name,
                    "user_id": user_id,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "metadata": metadata if metadata else None
                }
            ).scalar()

            session.commit()
            return result or False

        finally:
            session.close()

    def get_experiment_results(
        self,
        experiment_name: str,
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Obtém resultados agregados de experimento.

        Args:
            experiment_name: Nome do experimento
            metric_names: Lista de métricas para incluir (opcional, se None inclui todas)

        Returns:
            Dict com resultados por grupo
        """
        session = self.Session()
        try:
            # Buscar experimento
            experiment = session.execute(
                text("""
                    SELECT id, enabled, start_date, end_date, metadata
                    FROM ab_experiments
                    WHERE experiment_name = :experiment_name
                    LIMIT 1
                """),
                {"experiment_name": experiment_name}
            ).fetchone()

            if not experiment:
                return {"error": "Experimento não encontrado"}

            exp_id, enabled, start_date, end_date, metadata = experiment

            # Query base para métricas
            base_query = """
                SELECT
                    group_name,
                    metric_name,
                    COUNT(*) as count,
                    AVG(metric_value) as avg_value,
                    MIN(metric_value) as min_value,
                    MAX(metric_value) as max_value,
                    STDDEV(metric_value) as stddev_value
                FROM ab_experiment_metrics
                WHERE experiment_id = :exp_id
            """

            params = {"exp_id": exp_id}

            if metric_names:
                base_query += " AND metric_name = ANY(:metric_names)"
                params["metric_names"] = metric_names

            base_query += """
                GROUP BY group_name, metric_name
                ORDER BY group_name, metric_name
            """

            results = session.execute(text(base_query), params).fetchall()

            # Organizar resultados
            groups = {}
            for row in results:
                group, metric, count, avg, min_val, max_val, stddev = row

                if group not in groups:
                    groups[group] = {}

                groups[group][metric] = {
                    "count": count,
                    "average": float(avg) if avg else 0.0,
                    "min": float(min_val) if min_val else 0.0,
                    "max": float(max_val) if max_val else 0.0,
                    "stddev": float(stddev) if stddev else 0.0
                }

            # Contar usuários por grupo
            user_counts = session.execute(
                text("""
                    SELECT group_name, COUNT(DISTINCT user_id) as user_count
                    FROM ab_user_groups
                    WHERE experiment_id = :exp_id
                    GROUP BY group_name
                """),
                {"exp_id": exp_id}
            ).fetchall()

            user_counts_dict = {row[0]: row[1] for row in user_counts}

            return {
                "experiment_name": experiment_name,
                "enabled": enabled,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "groups": groups,
                "user_counts": user_counts_dict,
                "metadata": metadata
            }

        finally:
            session.close()

    def enable_experiment(self, experiment_name: str) -> bool:
        """
        Habilita experimento.

        Args:
            experiment_name: Nome do experimento

        Returns:
            True se habilitado, False se não encontrado
        """
        session = self.Session()
        try:
            result = session.execute(
                text("""
                    UPDATE ab_experiments
                    SET enabled = true,
                        start_date = COALESCE(start_date, NOW()),
                        updated_at = NOW()
                    WHERE experiment_name = :experiment_name
                    RETURNING id
                """),
                {"experiment_name": experiment_name}
            )

            session.commit()
            return result.rowcount > 0

        finally:
            session.close()

    def disable_experiment(self, experiment_name: str) -> bool:
        """
        Desabilita experimento.

        Args:
            experiment_name: Nome do experimento

        Returns:
            True se desabilitado, False se não encontrado
        """
        session = self.Session()
        try:
            result = session.execute(
                text("""
                    UPDATE ab_experiments
                    SET enabled = false,
                        end_date = COALESCE(end_date, NOW()),
                        updated_at = NOW()
                    WHERE experiment_name = :experiment_name
                    RETURNING id
                """),
                {"experiment_name": experiment_name}
            )

            session.commit()
            return result.rowcount > 0

        finally:
            session.close()

    def list_experiments(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Lista experimentos disponíveis.

        Args:
            enabled_only: Se True, retorna apenas experimentos ativos

        Returns:
            Lista de experimentos
        """
        session = self.Session()
        try:
            query = """
                SELECT
                    experiment_name,
                    description,
                    enabled,
                    start_date,
                    end_date,
                    target_plan_codigo,
                    control_group_percentage,
                    variant_group_percentage
                FROM ab_experiments
            """

            if enabled_only:
                query += " WHERE enabled = true"

            query += " ORDER BY created_at DESC"

            results = session.execute(text(query)).fetchall()

            return [
                {
                    "name": row[0],
                    "description": row[1],
                    "enabled": row[2],
                    "start_date": row[3].isoformat() if row[3] else None,
                    "end_date": row[4].isoformat() if row[4] else None,
                    "target_plan": row[5],
                    "control_pct": float(row[6]),
                    "variant_pct": float(row[7])
                }
                for row in results
            ]

        finally:
            session.close()

    def get_user_group(self, experiment_name: str, user_id: str) -> Optional[str]:
        """
        Obtém grupo do usuário sem atribuir novo (apenas consulta).

        Args:
            experiment_name: Nome do experimento
            user_id: UUID do usuário

        Returns:
            Nome do grupo ('control' ou 'variant') ou None
        """
        session = self.Session()
        try:
            result = session.execute(
                text("""
                    SELECT aug.group_name
                    FROM ab_user_groups aug
                    INNER JOIN ab_experiments ae ON aug.experiment_id = ae.id
                    WHERE ae.experiment_name = :experiment_name
                      AND aug.user_id = :user_id
                    LIMIT 1
                """),
                {
                    "experiment_name": experiment_name,
                    "user_id": user_id
                }
            ).fetchone()

            return result[0] if result else None

        finally:
            session.close()
