#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
SUBSCRIPTION SERVICE - ETAPA 10.3
================================================================================

Serviço de assinaturas e metering com:
- Gestão de planos
- Verificação de limites
- Incremento de uso
- Rate limiting
- Enforcement de quotas

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

from datetime import datetime, date
from typing import Dict, Optional, Tuple, List
from uuid import UUID, uuid4
from sqlalchemy import text
from database.connection import DatabaseConnection


class SubscriptionService:
    """Serviço de gestão de assinaturas e limites."""

    def __init__(self):
        self.db = DatabaseConnection()

    # ============================================================================
    # PLANOS
    # ============================================================================

    def obter_plano(self, codigo: str) -> Optional[Dict]:
        """
        Obtém plano por código.

        Args:
            codigo: Código do plano (FREE, BASIC, PRO)

        Returns:
            Dict com dados do plano ou None
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT
                        id, codigo, nome, descricao,
                        limite_questoes_dia, limite_consultas_dia, limite_peca_mes,
                        acesso_modo_pedagogico, acesso_modo_profissional,
                        acesso_piece_engine, acesso_jurisprudencia, acesso_analytics,
                        preco_mensal, preco_anual, moeda
                    FROM plano
                    WHERE codigo = :codigo AND ativo = TRUE
                """),
                {"codigo": codigo}
            ).fetchone()

            if not result:
                return None

            return {
                "id": result[0],
                "codigo": result[1],
                "nome": result[2],
                "descricao": result[3],
                "limite_questoes_dia": result[4],
                "limite_consultas_dia": result[5],
                "limite_peca_mes": result[6],
                "acesso_modo_pedagogico": result[7],
                "acesso_modo_profissional": result[8],
                "acesso_piece_engine": result[9],
                "acesso_jurisprudencia": result[10],
                "acesso_analytics": result[11],
                "preco_mensal": float(result[12]) if result[12] else None,
                "preco_anual": float(result[13]) if result[13] else None,
                "moeda": result[14]
            }

    def listar_planos_publicos(self) -> List[Dict]:
        """
        Lista todos os planos públicos disponíveis.

        Returns:
            Lista de planos
        """
        with self.db.get_session() as session:
            results = session.execute(
                text("""
                    SELECT
                        id, codigo, nome, descricao,
                        limite_questoes_dia, limite_consultas_dia, limite_peca_mes,
                        acesso_modo_pedagogico, acesso_modo_profissional,
                        acesso_piece_engine, acesso_jurisprudencia, acesso_analytics,
                        preco_mensal, preco_anual, moeda
                    FROM plano
                    WHERE ativo = TRUE AND visivel_publico = TRUE
                    ORDER BY preco_mensal NULLS FIRST
                """)
            ).fetchall()

            return [
                {
                    "id": r[0],
                    "codigo": r[1],
                    "nome": r[2],
                    "descricao": r[3],
                    "limite_questoes_dia": r[4],
                    "limite_consultas_dia": r[5],
                    "limite_peca_mes": r[6],
                    "acesso_modo_pedagogico": r[7],
                    "acesso_modo_profissional": r[8],
                    "acesso_piece_engine": r[9],
                    "acesso_jurisprudencia": r[10],
                    "acesso_analytics": r[11],
                    "preco_mensal": float(r[12]) if r[12] else None,
                    "preco_anual": float(r[13]) if r[13] else None,
                    "moeda": r[14]
                }
                for r in results
            ]

    # ============================================================================
    # ASSINATURAS
    # ============================================================================

    def criar_assinatura(
        self,
        usuario_id: UUID,
        codigo_plano: str,
        periodo: str = "monthly",
        em_trial: bool = False,
        stripe_subscription_id: Optional[str] = None
    ) -> Tuple[bool, Optional[UUID], Optional[str]]:
        """
        Cria nova assinatura para usuário.

        Args:
            usuario_id: ID do usuário
            codigo_plano: Código do plano (FREE, BASIC, PRO)
            periodo: Período (monthly, yearly, trial)
            em_trial: Se está em período trial
            stripe_subscription_id: ID da subscription no Stripe

        Returns:
            Tupla (sucesso, assinatura_id, erro)
        """
        # Validações
        if periodo not in ['monthly', 'yearly', 'trial']:
            return False, None, "Período inválido"

        # Obter plano
        plano = self.obter_plano(codigo_plano)
        if not plano:
            return False, None, f"Plano {codigo_plano} não encontrado"

        with self.db.get_session() as session:
            # Cancelar assinaturas ativas anteriores
            session.execute(
                text("""
                    UPDATE assinatura
                    SET status = 'canceled',
                        data_cancelamento = NOW(),
                        auto_renovar = FALSE,
                        motivo_cancelamento = 'Nova assinatura criada'
                    WHERE usuario_id = :usuario_id
                      AND status = 'active'
                """),
                {"usuario_id": usuario_id}
            )

            # Criar nova assinatura
            assinatura_id = uuid4()

            # Calcular data_fim baseado no período
            data_fim = None
            trial_ate = None

            if periodo == 'trial':
                from datetime import timedelta
                trial_ate = datetime.now() + timedelta(days=7)
                data_fim = trial_ate

            session.execute(
                text("""
                    INSERT INTO assinatura (
                        id,
                        usuario_id,
                        plano_id,
                        status,
                        periodo,
                        data_inicio,
                        data_fim,
                        em_trial,
                        trial_ate,
                        stripe_subscription_id,
                        auto_renovar,
                        created_at
                    ) VALUES (
                        :id,
                        :usuario_id,
                        :plano_id,
                        :status,
                        :periodo,
                        NOW(),
                        :data_fim,
                        :em_trial,
                        :trial_ate,
                        :stripe_subscription_id,
                        TRUE,
                        NOW()
                    )
                """),
                {
                    "id": assinatura_id,
                    "usuario_id": usuario_id,
                    "plano_id": plano["id"],
                    "status": "trial" if em_trial else "active",
                    "periodo": periodo,
                    "data_fim": data_fim,
                    "em_trial": em_trial,
                    "trial_ate": trial_ate,
                    "stripe_subscription_id": stripe_subscription_id
                }
            )
            session.commit()

            return True, assinatura_id, None

    def obter_assinatura_ativa(self, usuario_id: UUID) -> Optional[Dict]:
        """
        Obtém assinatura ativa do usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            Dict com assinatura ou None
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT
                        assinatura_id, plano_id, plano_codigo, status,
                        limite_questoes_dia, limite_consultas_dia, limite_peca_mes
                    FROM obter_assinatura_ativa(:usuario_id)
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            if not result:
                return None

            return {
                "assinatura_id": result[0],
                "plano_id": result[1],
                "plano_codigo": result[2],
                "status": result[3],
                "limite_questoes_dia": result[4],
                "limite_consultas_dia": result[5],
                "limite_peca_mes": result[6]
            }

    def cancelar_assinatura(
        self,
        assinatura_id: UUID,
        motivo: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Cancela assinatura.

        Args:
            assinatura_id: ID da assinatura
            motivo: Motivo do cancelamento

        Returns:
            Tupla (sucesso, erro)
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    UPDATE assinatura
                    SET status = 'canceled',
                        data_cancelamento = NOW(),
                        auto_renovar = FALSE,
                        motivo_cancelamento = :motivo
                    WHERE id = :assinatura_id
                """),
                {
                    "assinatura_id": assinatura_id,
                    "motivo": motivo
                }
            )
            session.commit()

            return True, None

    # ============================================================================
    # METERING E LIMITES
    # ============================================================================

    def obter_uso_dia(self, usuario_id: UUID, data: Optional[date] = None) -> Dict:
        """
        Obtém uso do dia.

        Args:
            usuario_id: ID do usuário
            data: Data (padrão: hoje)

        Returns:
            Dict com uso do dia
        """
        if data is None:
            data = date.today()

        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT questoes_respondidas, consultas_realizadas,
                           pecas_geradas, tempo_uso_segundos
                    FROM obter_uso_dia(:usuario_id, :data)
                """),
                {"usuario_id": usuario_id, "data": data}
            ).fetchone()

            return {
                "questoes_respondidas": result[0],
                "consultas_realizadas": result[1],
                "pecas_geradas": result[2],
                "tempo_uso_segundos": result[3]
            }

    def verificar_limite(
        self,
        usuario_id: UUID,
        tipo_recurso: str
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Verifica se usuário atingiu limite do plano.

        Args:
            usuario_id: ID do usuário
            tipo_recurso: Tipo ('questao', 'consulta', 'peca')

        Returns:
            Tupla (pode_usar, info)
            info = {
                "limite": int,
                "uso_atual": int,
                "restante": int,
                "ilimitado": bool
            }
        """
        if tipo_recurso not in ['questao', 'consulta', 'peca']:
            return False, {"erro": "Tipo de recurso inválido"}

        # Obter assinatura e limites
        assinatura = self.obter_assinatura_ativa(usuario_id)
        if not assinatura:
            # Sem assinatura = sem acesso
            return False, {
                "limite": 0,
                "uso_atual": 0,
                "restante": 0,
                "ilimitado": False,
                "erro": "Nenhuma assinatura ativa"
            }

        # Obter limite do plano
        if tipo_recurso == 'questao':
            limite = assinatura["limite_questoes_dia"]
        elif tipo_recurso == 'consulta':
            limite = assinatura["limite_consultas_dia"]
        else:  # peca
            limite = assinatura["limite_peca_mes"]

        # NULL = ilimitado
        if limite is None:
            return True, {
                "limite": None,
                "uso_atual": 0,
                "restante": None,
                "ilimitado": True
            }

        # Obter uso atual
        uso = self.obter_uso_dia(usuario_id)

        if tipo_recurso == 'questao':
            uso_atual = uso["questoes_respondidas"]
        elif tipo_recurso == 'consulta':
            uso_atual = uso["consultas_realizadas"]
        else:  # peca
            # Peça é limite mensal, não diário
            with self.db.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT COALESCE(SUM(pecas_geradas), 0)
                        FROM uso_diario
                        WHERE usuario_id = :usuario_id
                          AND data >= DATE_TRUNC('month', CURRENT_DATE)
                    """),
                    {"usuario_id": usuario_id}
                ).fetchone()
                uso_atual = result[0]

        # Verificar limite
        pode_usar = uso_atual < limite
        restante = max(0, limite - uso_atual)

        return pode_usar, {
            "limite": limite,
            "uso_atual": uso_atual,
            "restante": restante,
            "ilimitado": False
        }

    def incrementar_uso(
        self,
        usuario_id: UUID,
        tipo_evento: str,
        recurso_id: Optional[UUID] = None,
        incremento: int = 1
    ) -> Tuple[bool, Optional[str]]:
        """
        Incrementa uso e registra evento.

        Args:
            usuario_id: ID do usuário
            tipo_evento: Tipo ('questao', 'consulta', 'peca')
            recurso_id: ID do recurso usado
            incremento: Quantidade a incrementar

        Returns:
            Tupla (sucesso, erro)
        """
        with self.db.get_session() as session:
            try:
                # Incrementar contador
                session.execute(
                    text("SELECT incrementar_uso(:usuario_id, :tipo_evento, :incremento)"),
                    {
                        "usuario_id": usuario_id,
                        "tipo_evento": tipo_evento,
                        "incremento": incremento
                    }
                )

                # Registrar evento
                uso_diario_id = session.execute(
                    text("""
                        SELECT id FROM uso_diario
                        WHERE usuario_id = :usuario_id
                          AND data = CURRENT_DATE
                    """),
                    {"usuario_id": usuario_id}
                ).fetchone()

                session.execute(
                    text("""
                        INSERT INTO evento_uso (
                            id,
                            usuario_id,
                            uso_diario_id,
                            tipo_evento,
                            recurso_id,
                            sucesso,
                            bloqueado_por_limite,
                            timestamp
                        ) VALUES (
                            :id,
                            :usuario_id,
                            :uso_diario_id,
                            :tipo_evento,
                            :recurso_id,
                            TRUE,
                            FALSE,
                            NOW()
                        )
                    """),
                    {
                        "id": uuid4(),
                        "usuario_id": usuario_id,
                        "uso_diario_id": uso_diario_id[0] if uso_diario_id else None,
                        "tipo_evento": f"{tipo_evento}_respondida" if tipo_evento == "questao" else f"{tipo_evento}_realizada",
                        "recurso_id": recurso_id
                    }
                )

                session.commit()
                return True, None

            except Exception as e:
                session.rollback()
                return False, str(e)

    def registrar_bloqueio(
        self,
        usuario_id: UUID,
        tipo_evento: str,
        limite_atingido: str
    ):
        """
        Registra tentativa bloqueada por limite.

        Args:
            usuario_id: ID do usuário
            tipo_evento: Tipo do evento
            limite_atingido: Qual limite foi atingido
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO evento_uso (
                        id,
                        usuario_id,
                        tipo_evento,
                        sucesso,
                        bloqueado_por_limite,
                        limite_atingido,
                        timestamp
                    ) VALUES (
                        :id,
                        :usuario_id,
                        :tipo_evento,
                        FALSE,
                        TRUE,
                        :limite_atingido,
                        NOW()
                    )
                """),
                {
                    "id": uuid4(),
                    "usuario_id": usuario_id,
                    "tipo_evento": tipo_evento,
                    "limite_atingido": limite_atingido
                }
            )
            session.commit()

    # ============================================================================
    # ENFORCEMENT (RATE LIMITING)
    # ============================================================================

    def pode_usar_recurso(
        self,
        usuario_id: UUID,
        tipo_recurso: str
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Verifica se usuário pode usar recurso (enforcement completo).

        Args:
            usuario_id: ID do usuário
            tipo_recurso: Tipo ('questao', 'consulta', 'peca')

        Returns:
            Tupla (pode_usar, erro, info)
        """
        # Verificar limite
        pode_usar, info = self.verificar_limite(usuario_id, tipo_recurso)

        if not pode_usar:
            # Registrar bloqueio
            if "erro" not in info:
                self.registrar_bloqueio(
                    usuario_id,
                    tipo_recurso,
                    f"limite_{tipo_recurso}_dia"
                )

                return False, f"Limite diário de {tipo_recurso}s atingido", info
            else:
                return False, info["erro"], info

        return True, None, info

    # ============================================================================
    # ANALYTICS
    # ============================================================================

    def obter_estatisticas_uso(
        self,
        usuario_id: UUID,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict:
        """
        Obtém estatísticas de uso do usuário.

        Args:
            usuario_id: ID do usuário
            data_inicio: Data inicial (padrão: início do mês)
            data_fim: Data final (padrão: hoje)

        Returns:
            Dict com estatísticas
        """
        if data_inicio is None:
            from datetime import datetime
            data_inicio = datetime.now().replace(day=1).date()

        if data_fim is None:
            data_fim = date.today()

        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT
                        SUM(questoes_respondidas) as total_questoes,
                        SUM(consultas_realizadas) as total_consultas,
                        SUM(pecas_geradas) as total_pecas,
                        SUM(tempo_uso_segundos) as total_tempo,
                        COUNT(DISTINCT data) as dias_ativos
                    FROM uso_diario
                    WHERE usuario_id = :usuario_id
                      AND data BETWEEN :data_inicio AND :data_fim
                """),
                {
                    "usuario_id": usuario_id,
                    "data_inicio": data_inicio,
                    "data_fim": data_fim
                }
            ).fetchone()

            return {
                "total_questoes": result[0] or 0,
                "total_consultas": result[1] or 0,
                "total_pecas": result[2] or 0,
                "total_tempo_minutos": (result[3] or 0) // 60,
                "dias_ativos": result[4] or 0,
                "periodo": {
                    "inicio": data_inicio.isoformat(),
                    "fim": data_fim.isoformat()
                }
            }
