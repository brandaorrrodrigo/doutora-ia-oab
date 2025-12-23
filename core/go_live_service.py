#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GO-LIVE SERVICE - CONTROLE DE LANÇAMENTO
================================================================================

Serviço de controle para go-live controlado:
- Feature flags
- Limites de uso
- Métricas de sessão
- Eventos de monitoramento

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

from datetime import datetime, date, timedelta
from typing import Dict, Optional, Tuple, List
from uuid import UUID, uuid4
from sqlalchemy import text
from database.connection import DatabaseConnection


class GoLiveService:
    """Serviço de controle de go-live."""

    def __init__(self):
        self.db = DatabaseConnection()

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================

    def verificar_feature_habilitada(
        self,
        codigo_feature: str,
        usuario_id: Optional[UUID] = None
    ) -> bool:
        """
        Verifica se feature está habilitada.

        Args:
            codigo_feature: Código da feature
            usuario_id: ID do usuário (opcional)

        Returns:
            True se habilitada
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT verificar_feature_habilitada(:codigo, :usuario_id)
                """),
                {
                    "codigo": codigo_feature,
                    "usuario_id": usuario_id
                }
            ).fetchone()

            return result[0] if result else False

    def obter_features_habilitadas(self) -> List[Dict]:
        """
        Lista todas as features habilitadas.

        Returns:
            Lista de features
        """
        with self.db.get_session() as session:
            results = session.execute(
                text("""
                    SELECT codigo, nome, descricao, limite_usuarios,
                           usuarios_atuais, percentual_rollout
                    FROM feature_flag
                    WHERE habilitado = TRUE
                    ORDER BY categoria, codigo
                """)
            ).fetchall()

            return [
                {
                    "codigo": r[0],
                    "nome": r[1],
                    "descricao": r[2],
                    "limite_usuarios": r[3],
                    "usuarios_atuais": r[4],
                    "percentual_rollout": r[5]
                }
                for r in results
            ]

    def habilitar_feature(
        self,
        codigo_feature: str,
        habilitado_por: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Habilita feature flag.

        Args:
            codigo_feature: Código da feature
            habilitado_por: ID do usuário que habilitou

        Returns:
            Tupla (sucesso, erro)
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    UPDATE feature_flag
                    SET habilitado = TRUE,
                        habilitado_em = NOW(),
                        habilitado_por = :habilitado_por
                    WHERE codigo = :codigo
                """),
                {
                    "codigo": codigo_feature,
                    "habilitado_por": habilitado_por
                }
            )
            session.commit()

            # Log evento
            self.registrar_evento(
                "feature_habilitada",
                "info",
                f"Feature {codigo_feature} habilitada",
                usuario_id=habilitado_por,
                detalhes={"feature": codigo_feature}
            )

            return True, None

    def desabilitar_feature(
        self,
        codigo_feature: str,
        desabilitado_por: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Desabilita feature flag.

        Args:
            codigo_feature: Código da feature
            desabilitado_por: ID do usuário que desabilitou

        Returns:
            Tupla (sucesso, erro)
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    UPDATE feature_flag
                    SET habilitado = FALSE,
                        desabilitado_em = NOW()
                    WHERE codigo = :codigo
                """),
                {"codigo": codigo_feature}
            )
            session.commit()

            # Log evento
            self.registrar_evento(
                "feature_desabilitada",
                "warning",
                f"Feature {codigo_feature} desabilitada",
                usuario_id=desabilitado_por,
                detalhes={"feature": codigo_feature}
            )

            return True, None

    # ============================================================================
    # LIMITES DE GO-LIVE
    # ============================================================================

    def verificar_limite(
        self,
        tipo_limite: str,
        usuario_id: UUID
    ) -> Dict:
        """
        Verifica limite específico do go-live.

        Args:
            tipo_limite: Tipo do limite (sessoes_dia, questoes_sessao, pecas_semana)
            usuario_id: ID do usuário

        Returns:
            Dict com status do limite
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT atingido, limite, uso_atual, restante
                    FROM verificar_limite_go_live(:tipo, :usuario_id)
                """),
                {
                    "tipo": tipo_limite,
                    "usuario_id": usuario_id
                }
            ).fetchone()

            if not result:
                return {
                    "atingido": False,
                    "limite": None,
                    "uso_atual": 0,
                    "restante": None
                }

            return {
                "atingido": result[0],
                "limite": result[1],
                "uso_atual": result[2],
                "restante": result[3]
            }

    def pode_iniciar_sessao(self, usuario_id: UUID) -> Tuple[bool, Optional[str], Dict]:
        """
        Verifica se usuário pode iniciar nova sessão.

        Args:
            usuario_id: ID do usuário

        Returns:
            Tupla (pode, motivo_bloqueio, info)
        """
        # Verificar feature habilitada
        if not self.verificar_feature_habilitada("modo_oab", usuario_id):
            return False, "Modo OAB não habilitado", {}

        # Verificar limite de sessões/dia
        limite_info = self.verificar_limite("sessoes_dia", usuario_id)

        if limite_info["atingido"]:
            return False, f"Limite de {limite_info['limite']} sessões/dia atingido", limite_info

        return True, None, limite_info

    def pode_responder_questao(
        self,
        usuario_id: UUID,
        sessao_id: UUID
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Verifica se usuário pode responder mais uma questão.

        Args:
            usuario_id: ID do usuário
            sessao_id: ID da sessão atual

        Returns:
            Tupla (pode, motivo_bloqueio, info)
        """
        # Verificar limite de questões/sessão
        limite_info = self.verificar_limite("questoes_sessao", usuario_id)

        if limite_info["atingido"]:
            return False, f"Limite de {limite_info['limite']} questões/sessão atingido", limite_info

        return True, None, limite_info

    # ============================================================================
    # MÉTRICAS DE SESSÃO
    # ============================================================================

    def iniciar_sessao(
        self,
        usuario_id: UUID,
        modo: str = "pedagogico"
    ) -> Tuple[bool, Optional[UUID], Optional[str]]:
        """
        Inicia nova sessão de estudo.

        Args:
            usuario_id: ID do usuário
            modo: Modo (pedagogico, profissional)

        Returns:
            Tupla (sucesso, sessao_id, erro)
        """
        # Verificar se pode iniciar
        pode, motivo, info = self.pode_iniciar_sessao(usuario_id)

        if not pode:
            self.registrar_evento(
                "sessao_bloqueada",
                "warning",
                motivo,
                usuario_id=usuario_id,
                detalhes=info
            )
            return False, None, motivo

        # Obter plano ativo
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT plano_codigo
                    FROM obter_assinatura_ativa(:usuario_id)
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            plano_ativo = result[0] if result else "FREE"

            # Criar sessão
            sessao_id = uuid4()

            session.execute(
                text("""
                    INSERT INTO metrica_sessao (
                        id, usuario_id, sessao_id, data_sessao,
                        hora_inicio, modo_utilizado, plano_ativo
                    ) VALUES (
                        :id, :usuario_id, :sessao_id, CURRENT_DATE,
                        NOW(), :modo, :plano_ativo
                    )
                """),
                {
                    "id": uuid4(),
                    "usuario_id": usuario_id,
                    "sessao_id": sessao_id,
                    "modo": modo,
                    "plano_ativo": plano_ativo
                }
            )
            session.commit()

            # Log evento
            self.registrar_evento(
                "sessao_iniciada",
                "info",
                f"Sessão iniciada no modo {modo}",
                usuario_id=usuario_id,
                detalhes={
                    "sessao_id": str(sessao_id),
                    "modo": modo,
                    "plano": plano_ativo
                }
            )

            return True, sessao_id, None

    def registrar_resposta_questao(
        self,
        usuario_id: UUID,
        sessao_id: UUID,
        questao_id: UUID,
        alternativa_escolhida: str,
        correta: bool,
        tipo_erro: Optional[str] = None
    ):
        """
        Registra resposta de questão na sessão.

        Args:
            usuario_id: ID do usuário
            sessao_id: ID da sessão
            questao_id: ID da questão
            alternativa_escolhida: Letra escolhida
            correta: Se acertou
            tipo_erro: Tipo de erro (se errou)
        """
        with self.db.get_session() as session:
            # Atualizar contadores da sessão
            if correta:
                session.execute(
                    text("""
                        UPDATE metrica_sessao
                        SET questoes_respondidas = questoes_respondidas + 1,
                            questoes_corretas = questoes_corretas + 1
                        WHERE sessao_id = :sessao_id
                    """),
                    {"sessao_id": sessao_id}
                )
            else:
                # Incrementar contador de erro por tipo
                campo_erro = f"erros_{tipo_erro}" if tipo_erro else None

                query = """
                    UPDATE metrica_sessao
                    SET questoes_respondidas = questoes_respondidas + 1,
                        questoes_incorretas = questoes_incorretas + 1
                """

                if campo_erro:
                    query += f", {campo_erro} = {campo_erro} + 1"

                query += " WHERE sessao_id = :sessao_id"

                session.execute(text(query), {"sessao_id": sessao_id})

            session.commit()

    def finalizar_sessao(
        self,
        usuario_id: UUID,
        sessao_id: UUID,
        concluida: bool = True,
        motivo_abandono: Optional[str] = None
    ):
        """
        Finaliza sessão de estudo.

        Args:
            usuario_id: ID do usuário
            sessao_id: ID da sessão
            concluida: Se foi concluída ou abandonada
            motivo_abandono: Motivo se abandonada
        """
        with self.db.get_session() as session:
            # Calcular duração
            session.execute(
                text("""
                    UPDATE metrica_sessao
                    SET hora_fim = NOW(),
                        duracao_segundos = EXTRACT(EPOCH FROM (NOW() - hora_inicio)),
                        sessao_concluida = :concluida,
                        abandonada = :abandonada,
                        motivo_abandono = :motivo
                    WHERE sessao_id = :sessao_id
                """),
                {
                    "sessao_id": sessao_id,
                    "concluida": concluida,
                    "abandonada": not concluida,
                    "motivo": motivo_abandono
                }
            )
            session.commit()

            # Log evento
            tipo_evento = "sessao_concluida" if concluida else "sessao_abandonada"
            self.registrar_evento(
                tipo_evento,
                "info" if concluida else "warning",
                f"Sessão {'concluída' if concluida else 'abandonada'}",
                usuario_id=usuario_id,
                detalhes={
                    "sessao_id": str(sessao_id),
                    "motivo_abandono": motivo_abandono
                }
            )

    # ============================================================================
    # ANALYTICS E RELATÓRIOS
    # ============================================================================

    def obter_metricas_sessao(self, sessao_id: UUID) -> Optional[Dict]:
        """
        Obtém métricas de uma sessão específica.

        Args:
            sessao_id: ID da sessão

        Returns:
            Dict com métricas ou None
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT
                        usuario_id, data_sessao, hora_inicio, hora_fim,
                        duracao_segundos, questoes_respondidas,
                        questoes_corretas, questoes_incorretas,
                        erros_conceitual, erros_normativo, erros_interpretacao,
                        erros_estrategico, erros_leitura, erros_confusao_institutos,
                        sessao_concluida, abandonada, motivo_abandono,
                        modo_utilizado, plano_ativo
                    FROM metrica_sessao
                    WHERE sessao_id = :sessao_id
                """),
                {"sessao_id": sessao_id}
            ).fetchone()

            if not result:
                return None

            # Calcular taxa de acerto
            total = result[5]  # questoes_respondidas
            corretas = result[6]  # questoes_corretas
            taxa_acerto = (corretas / total * 100) if total > 0 else 0

            return {
                "usuario_id": result[0],
                "data_sessao": result[1],
                "hora_inicio": result[2],
                "hora_fim": result[3],
                "duracao_segundos": result[4],
                "duracao_minutos": result[4] // 60 if result[4] else None,
                "questoes_respondidas": result[5],
                "questoes_corretas": result[6],
                "questoes_incorretas": result[7],
                "taxa_acerto": round(taxa_acerto, 2),
                "erros_por_tipo": {
                    "conceitual": result[8],
                    "normativo": result[9],
                    "interpretacao": result[10],
                    "estrategico": result[11],
                    "leitura": result[12],
                    "confusao_institutos": result[13]
                },
                "sessao_concluida": result[14],
                "abandonada": result[15],
                "motivo_abandono": result[16],
                "modo_utilizado": result[17],
                "plano_ativo": result[18]
            }

    def obter_metricas_agregadas(
        self,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> Dict:
        """
        Obtém métricas agregadas do go-live.

        Args:
            data_inicio: Data inicial (padrão: 7 dias atrás)
            data_fim: Data final (padrão: hoje)

        Returns:
            Dict com métricas agregadas
        """
        if data_inicio is None:
            data_inicio = date.today() - timedelta(days=7)
        if data_fim is None:
            data_fim = date.today()

        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT
                        COUNT(DISTINCT usuario_id) as usuarios_ativos,
                        COUNT(*) as total_sessoes,
                        SUM(CASE WHEN sessao_concluida THEN 1 ELSE 0 END) as sessoes_concluidas,
                        SUM(CASE WHEN abandonada THEN 1 ELSE 0 END) as sessoes_abandonadas,
                        SUM(questoes_respondidas) as total_questoes,
                        SUM(questoes_corretas) as total_corretas,
                        SUM(questoes_incorretas) as total_incorretas,
                        AVG(duracao_segundos) as duracao_media,
                        SUM(erros_conceitual) as total_erros_conceitual,
                        SUM(erros_normativo) as total_erros_normativo,
                        SUM(erros_interpretacao) as total_erros_interpretacao,
                        SUM(erros_estrategico) as total_erros_estrategico,
                        SUM(erros_leitura) as total_erros_leitura,
                        SUM(erros_confusao_institutos) as total_erros_confusao
                    FROM metrica_sessao
                    WHERE data_sessao BETWEEN :data_inicio AND :data_fim
                """),
                {
                    "data_inicio": data_inicio,
                    "data_fim": data_fim
                }
            ).fetchone()

            if not result or result[0] is None:
                return {
                    "usuarios_ativos": 0,
                    "total_sessoes": 0,
                    "taxa_conclusao": 0,
                    "taxa_abandono": 0,
                    "total_questoes": 0,
                    "taxa_acerto_geral": 0
                }

            total_sessoes = result[1]
            total_questoes = result[4]
            total_corretas = result[5]

            return {
                "periodo": {
                    "inicio": data_inicio.isoformat(),
                    "fim": data_fim.isoformat()
                },
                "usuarios_ativos": result[0],
                "total_sessoes": result[1],
                "sessoes_concluidas": result[2],
                "sessoes_abandonadas": result[3],
                "taxa_conclusao": round(result[2] / total_sessoes * 100, 2) if total_sessoes > 0 else 0,
                "taxa_abandono": round(result[3] / total_sessoes * 100, 2) if total_sessoes > 0 else 0,
                "total_questoes": result[4],
                "total_corretas": result[5],
                "total_incorretas": result[6],
                "taxa_acerto_geral": round(total_corretas / total_questoes * 100, 2) if total_questoes > 0 else 0,
                "duracao_media_segundos": int(result[7]) if result[7] else 0,
                "duracao_media_minutos": int(result[7] // 60) if result[7] else 0,
                "erros_por_tipo": {
                    "conceitual": result[8],
                    "normativo": result[9],
                    "interpretacao": result[10],
                    "estrategico": result[11],
                    "leitura": result[12],
                    "confusao_institutos": result[13]
                }
            }

    # ============================================================================
    # EVENTOS E LOGGING
    # ============================================================================

    def registrar_evento(
        self,
        tipo_evento: str,
        severidade: str,
        mensagem: str,
        usuario_id: Optional[UUID] = None,
        feature_flag_codigo: Optional[str] = None,
        detalhes: Optional[Dict] = None,
        stack_trace: Optional[str] = None
    ):
        """
        Registra evento de go-live.

        Args:
            tipo_evento: Tipo do evento
            severidade: info, warning, error, critical
            mensagem: Mensagem descritiva
            usuario_id: ID do usuário (opcional)
            feature_flag_codigo: Código da feature (opcional)
            detalhes: Detalhes em JSONB (opcional)
            stack_trace: Stack trace para erros (opcional)
        """
        import json

        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO evento_go_live (
                        id, tipo_evento, severidade, mensagem,
                        usuario_id, feature_flag_codigo, detalhes,
                        stack_trace, timestamp
                    ) VALUES (
                        :id, :tipo_evento, :severidade, :mensagem,
                        :usuario_id, :feature_flag_codigo, :detalhes::jsonb,
                        :stack_trace, NOW()
                    )
                """),
                {
                    "id": uuid4(),
                    "tipo_evento": tipo_evento,
                    "severidade": severidade,
                    "mensagem": mensagem,
                    "usuario_id": usuario_id,
                    "feature_flag_codigo": feature_flag_codigo,
                    "detalhes": json.dumps(detalhes) if detalhes else None,
                    "stack_trace": stack_trace
                }
            )
            session.commit()

    def obter_eventos_criticos(self, ultimas_horas: int = 24) -> List[Dict]:
        """
        Obtém eventos críticos recentes.

        Args:
            ultimas_horas: Últimas N horas

        Returns:
            Lista de eventos
        """
        with self.db.get_session() as session:
            results = session.execute(
                text("""
                    SELECT tipo_evento, mensagem, usuario_id, timestamp, detalhes
                    FROM evento_go_live
                    WHERE severidade IN ('error', 'critical')
                      AND timestamp >= NOW() - INTERVAL ':horas hours'
                    ORDER BY timestamp DESC
                    LIMIT 100
                """),
                {"horas": ultimas_horas}
            ).fetchall()

            return [
                {
                    "tipo_evento": r[0],
                    "mensagem": r[1],
                    "usuario_id": r[2],
                    "timestamp": r[3],
                    "detalhes": r[4]
                }
                for r in results
            ]
