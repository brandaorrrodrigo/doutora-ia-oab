#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
COMPLIANCE SERVICE - GOVERNANÇA E LGPD
================================================================================

Serviço de compliance jurídico:
- Termos de uso e políticas
- Avisos obrigatórios
- Logs legais (LGPD)
- Solicitações LGPD
- Anonimização de dados

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

import json
from datetime import datetime, date
from typing import Dict, Optional, Tuple, List
from uuid import UUID, uuid4
from sqlalchemy import text
from database.connection import DatabaseConnection


class ComplianceService:
    """Serviço de compliance e governança jurídica."""

    def __init__(self):
        self.db = DatabaseConnection()

    # ============================================================================
    # TERMOS E POLÍTICAS
    # ============================================================================

    def obter_termo_ativo(self, tipo: str) -> Optional[Dict]:
        """
        Obtém termo/política ativa.

        Args:
            tipo: Tipo (termos_uso, privacidade, uso_aceitavel)

        Returns:
            Dict com termo ou None
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT id, versao, titulo, conteudo, resumo,
                           data_publicacao, data_vigencia, obrigatorio
                    FROM termo_politica
                    WHERE tipo = :tipo
                      AND ativo = TRUE
                      AND data_vigencia <= NOW()
                      AND (data_expiracao IS NULL OR data_expiracao > NOW())
                    ORDER BY data_vigencia DESC
                    LIMIT 1
                """),
                {"tipo": tipo}
            ).fetchone()

            if not result:
                return None

            return {
                "id": result[0],
                "tipo": tipo,
                "versao": result[1],
                "titulo": result[2],
                "conteudo": result[3],
                "resumo": result[4],
                "data_publicacao": result[5],
                "data_vigencia": result[6],
                "obrigatorio": result[7]
            }

    def verificar_aceitacao_termos(self, usuario_id: UUID) -> Tuple[bool, List[str]]:
        """
        Verifica se usuário aceitou todos os termos obrigatórios.

        Args:
            usuario_id: ID do usuário

        Returns:
            Tupla (todos_aceitos, termos_pendentes)
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT termos_aceitos, termos_pendentes
                    FROM verificar_aceitacao_termos(:usuario_id)
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            if not result:
                return False, []

            return result[0], result[1]

    def registrar_aceitacao_termo(
        self,
        usuario_id: UUID,
        termo_politica_id: UUID,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Registra aceitação de termo/política.

        Args:
            usuario_id: ID do usuário
            termo_politica_id: ID do termo
            ip_origem: IP de origem
            user_agent: User agent

        Returns:
            Tupla (sucesso, erro)
        """
        with self.db.get_session() as session:
            try:
                # Obter versão do termo
                result = session.execute(
                    text("SELECT versao FROM termo_politica WHERE id = :id"),
                    {"id": termo_politica_id}
                ).fetchone()

                if not result:
                    return False, "Termo não encontrado"

                versao = result[0]

                # Registrar aceitação
                session.execute(
                    text("""
                        INSERT INTO aceitacao_termo (
                            id, usuario_id, termo_politica_id,
                            data_aceitacao, ip_origem, user_agent,
                            aceite_explicito, versao_aceita
                        ) VALUES (
                            :id, :usuario_id, :termo_politica_id,
                            NOW(), :ip_origem, :user_agent,
                            TRUE, :versao
                        )
                        ON CONFLICT (usuario_id, termo_politica_id) DO NOTHING
                    """),
                    {
                        "id": uuid4(),
                        "usuario_id": usuario_id,
                        "termo_politica_id": termo_politica_id,
                        "ip_origem": ip_origem,
                        "user_agent": user_agent,
                        "versao": versao
                    }
                )
                session.commit()

                # Log legal
                self.registrar_log_legal(
                    usuario_id,
                    "aceitacao_termo",
                    "acesso_dados",
                    f"Aceitação de termo {versao}",
                    base_legal="consentimento"
                )

                return True, None

            except Exception as e:
                session.rollback()
                return False, str(e)

    # ============================================================================
    # AVISOS OBRIGATÓRIOS
    # ============================================================================

    def obter_aviso(self, codigo: str) -> Optional[Dict]:
        """
        Obtém aviso obrigatório.

        Args:
            codigo: Código do aviso

        Returns:
            Dict com aviso ou None
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT id, titulo, mensagem, contexto, tipo_aviso,
                           obrigatorio, requer_confirmacao, exibir_sempre
                    FROM aviso_obrigatorio
                    WHERE codigo = :codigo AND ativo = TRUE
                """),
                {"codigo": codigo}
            ).fetchone()

            if not result:
                return None

            return {
                "id": result[0],
                "codigo": codigo,
                "titulo": result[1],
                "mensagem": result[2],
                "contexto": result[3],
                "tipo_aviso": result[4],
                "obrigatorio": result[5],
                "requer_confirmacao": result[6],
                "exibir_sempre": result[7]
            }

    def obter_avisos_por_contexto(self, contexto: str) -> List[Dict]:
        """
        Obtém avisos para contexto específico.

        Args:
            contexto: Contexto (pre_sessao, pre_peca, pre_cadastro)

        Returns:
            Lista de avisos
        """
        with self.db.get_session() as session:
            results = session.execute(
                text("""
                    SELECT id, codigo, titulo, mensagem, tipo_aviso,
                           obrigatorio, requer_confirmacao, exibir_sempre
                    FROM aviso_obrigatorio
                    WHERE contexto = :contexto AND ativo = TRUE
                    ORDER BY obrigatorio DESC, tipo_aviso
                """),
                {"contexto": contexto}
            ).fetchall()

            return [
                {
                    "id": r[0],
                    "codigo": r[1],
                    "titulo": r[2],
                    "mensagem": r[3],
                    "tipo_aviso": r[4],
                    "obrigatorio": r[5],
                    "requer_confirmacao": r[6],
                    "exibir_sempre": r[7]
                }
                for r in results
            ]

    def verificar_aviso_confirmado(
        self,
        usuario_id: UUID,
        codigo_aviso: str
    ) -> bool:
        """
        Verifica se usuário já confirmou aviso.

        Args:
            usuario_id: ID do usuário
            codigo_aviso: Código do aviso

        Returns:
            True se já confirmado
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM confirmacao_aviso ca
                    JOIN aviso_obrigatorio ao ON ca.aviso_obrigatorio_id = ao.id
                    WHERE ca.usuario_id = :usuario_id
                      AND ao.codigo = :codigo
                """),
                {
                    "usuario_id": usuario_id,
                    "codigo": codigo_aviso
                }
            ).fetchone()

            return result[0] > 0 if result else False

    def registrar_confirmacao_aviso(
        self,
        usuario_id: UUID,
        aviso_obrigatorio_id: UUID,
        ip_origem: Optional[str] = None,
        sessao_id: Optional[UUID] = None,
        contexto_exibicao: Optional[str] = None
    ):
        """
        Registra confirmação de aviso.

        Args:
            usuario_id: ID do usuário
            aviso_obrigatorio_id: ID do aviso
            ip_origem: IP de origem
            sessao_id: ID da sessão (opcional)
            contexto_exibicao: Contexto de exibição
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO confirmacao_aviso (
                        id, usuario_id, aviso_obrigatorio_id,
                        data_confirmacao, ip_origem, sessao_id, contexto_exibicao
                    ) VALUES (
                        :id, :usuario_id, :aviso_obrigatorio_id,
                        NOW(), :ip_origem, :sessao_id, :contexto_exibicao
                    )
                """),
                {
                    "id": uuid4(),
                    "usuario_id": usuario_id,
                    "aviso_obrigatorio_id": aviso_obrigatorio_id,
                    "ip_origem": ip_origem,
                    "sessao_id": sessao_id,
                    "contexto_exibicao": contexto_exibicao
                }
            )
            session.commit()

    # ============================================================================
    # LOGS LEGAIS (LGPD)
    # ============================================================================

    def registrar_log_legal(
        self,
        usuario_id: UUID,
        tipo_acao: str,
        categoria: str,
        descricao: str,
        recurso_acessado: Optional[str] = None,
        dados_acessados: Optional[Dict] = None,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None,
        base_legal: str = "consentimento"
    ) -> UUID:
        """
        Registra log de ação sensível (LGPD).

        Args:
            usuario_id: ID do usuário
            tipo_acao: Tipo da ação
            categoria: Categoria (acesso_dados, modificacao, exclusao, exportacao)
            descricao: Descrição da ação
            recurso_acessado: Recurso acessado
            dados_acessados: Dados acessados (JSONB)
            ip_origem: IP de origem
            user_agent: User agent
            base_legal: Base legal LGPD

        Returns:
            ID do log criado
        """
        log_id = uuid4()

        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO log_legal (
                        id, usuario_id, tipo_acao, categoria, descricao,
                        recurso_acessado, dados_acessados, ip_origem,
                        user_agent, consentimento_presente, base_legal, timestamp
                    ) VALUES (
                        :id, :usuario_id, :tipo_acao, :categoria, :descricao,
                        :recurso, :dados::jsonb, :ip_origem,
                        :user_agent, TRUE, :base_legal, NOW()
                    )
                """),
                {
                    "id": log_id,
                    "usuario_id": usuario_id,
                    "tipo_acao": tipo_acao,
                    "categoria": categoria,
                    "descricao": descricao,
                    "recurso": recurso_acessado,
                    "dados": json.dumps(dados_acessados) if dados_acessados else None,
                    "ip_origem": ip_origem,
                    "user_agent": user_agent,
                    "base_legal": base_legal
                }
            )
            session.commit()

        return log_id

    def obter_logs_usuario(
        self,
        usuario_id: UUID,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None
    ) -> List[Dict]:
        """
        Obtém logs de ações do usuário.

        Args:
            usuario_id: ID do usuário
            data_inicio: Data inicial (opcional)
            data_fim: Data final (opcional)

        Returns:
            Lista de logs
        """
        with self.db.get_session() as session:
            query = """
                SELECT tipo_acao, categoria, descricao,
                       recurso_acessado, timestamp
                FROM log_legal
                WHERE usuario_id = :usuario_id
                  AND anonimizado = FALSE
            """

            params = {"usuario_id": usuario_id}

            if data_inicio:
                query += " AND timestamp >= :data_inicio"
                params["data_inicio"] = data_inicio

            if data_fim:
                query += " AND timestamp <= :data_fim"
                params["data_fim"] = data_fim

            query += " ORDER BY timestamp DESC LIMIT 1000"

            results = session.execute(text(query), params).fetchall()

            return [
                {
                    "tipo_acao": r[0],
                    "categoria": r[1],
                    "descricao": r[2],
                    "recurso_acessado": r[3],
                    "timestamp": r[4]
                }
                for r in results
            ]

    # ============================================================================
    # SOLICITAÇÕES LGPD
    # ============================================================================

    def criar_solicitacao_lgpd(
        self,
        usuario_id: UUID,
        tipo_solicitacao: str,
        descricao: Optional[str] = None
    ) -> Tuple[bool, Optional[UUID], Optional[str]]:
        """
        Cria solicitação de direito LGPD.

        Args:
            usuario_id: ID do usuário
            tipo_solicitacao: Tipo (acesso, retificacao, exclusao, portabilidade, oposicao)
            descricao: Descrição adicional

        Returns:
            Tupla (sucesso, solicitacao_id, erro)
        """
        tipos_validos = ['acesso', 'retificacao', 'exclusao', 'portabilidade', 'oposicao']

        if tipo_solicitacao not in tipos_validos:
            return False, None, f"Tipo inválido. Use: {', '.join(tipos_validos)}"

        solicitacao_id = uuid4()

        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO solicitacao_lgpd (
                        id, usuario_id, tipo_solicitacao, status,
                        descricao, data_solicitacao
                    ) VALUES (
                        :id, :usuario_id, :tipo, 'pendente',
                        :descricao, NOW()
                    )
                """),
                {
                    "id": solicitacao_id,
                    "usuario_id": usuario_id,
                    "tipo": tipo_solicitacao,
                    "descricao": descricao
                }
            )
            session.commit()

            # Log legal
            self.registrar_log_legal(
                usuario_id,
                f"solicitacao_lgpd_{tipo_solicitacao}",
                "acesso_dados",
                f"Solicitação LGPD: {tipo_solicitacao}",
                base_legal="exercício_de_direitos"
            )

            return True, solicitacao_id, None

    def processar_solicitacao_acesso(
        self,
        solicitacao_id: UUID
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Processa solicitação de acesso aos dados (Art. 18, LGPD).

        Args:
            solicitacao_id: ID da solicitação

        Returns:
            Tupla (sucesso, dados_usuario, erro)
        """
        with self.db.get_session() as session:
            # Buscar solicitação
            result = session.execute(
                text("""
                    SELECT usuario_id
                    FROM solicitacao_lgpd
                    WHERE id = :id AND tipo_solicitacao = 'acesso'
                """),
                {"id": solicitacao_id}
            ).fetchone()

            if not result:
                return False, None, "Solicitação não encontrada"

            usuario_id = result[0]

            # Coletar dados do usuário
            dados_usuario = {
                "dados_cadastrais": self._exportar_dados_cadastrais(session, usuario_id),
                "assinaturas": self._exportar_assinaturas(session, usuario_id),
                "uso": self._exportar_uso(session, usuario_id),
                "logs_acesso": self._exportar_logs(session, usuario_id)
            }

            # Atualizar status
            session.execute(
                text("""
                    UPDATE solicitacao_lgpd
                    SET status = 'concluida',
                        data_conclusao = NOW()
                    WHERE id = :id
                """),
                {"id": solicitacao_id}
            )
            session.commit()

            return True, dados_usuario, None

    def _exportar_dados_cadastrais(self, session, usuario_id: UUID) -> Dict:
        """Exporta dados cadastrais do usuário."""
        result = session.execute(
            text("""
                SELECT email, nome_completo, cpf, role, modo_atual,
                       ativo, created_at
                FROM usuario
                WHERE id = :usuario_id
            """),
            {"usuario_id": usuario_id}
        ).fetchone()

        if not result:
            return {}

        return {
            "email": result[0],
            "nome_completo": result[1],
            "cpf": result[2],
            "role": result[3],
            "modo_atual": result[4],
            "ativo": result[5],
            "data_cadastro": result[6].isoformat() if result[6] else None
        }

    def _exportar_assinaturas(self, session, usuario_id: UUID) -> List[Dict]:
        """Exporta histórico de assinaturas."""
        results = session.execute(
            text("""
                SELECT p.codigo, a.status, a.periodo,
                       a.data_inicio, a.data_fim
                FROM assinatura a
                JOIN plano p ON a.plano_id = p.id
                WHERE a.usuario_id = :usuario_id
                ORDER BY a.data_inicio DESC
            """),
            {"usuario_id": usuario_id}
        ).fetchall()

        return [
            {
                "plano": r[0],
                "status": r[1],
                "periodo": r[2],
                "data_inicio": r[3].isoformat() if r[3] else None,
                "data_fim": r[4].isoformat() if r[4] else None
            }
            for r in results
        ]

    def _exportar_uso(self, session, usuario_id: UUID) -> Dict:
        """Exporta estatísticas de uso."""
        result = session.execute(
            text("""
                SELECT
                    SUM(questoes_respondidas) as total_questoes,
                    SUM(consultas_realizadas) as total_consultas,
                    SUM(pecas_geradas) as total_pecas
                FROM uso_diario
                WHERE usuario_id = :usuario_id
            """),
            {"usuario_id": usuario_id}
        ).fetchone()

        return {
            "total_questoes_respondidas": result[0] or 0,
            "total_consultas_realizadas": result[1] or 0,
            "total_pecas_geradas": result[2] or 0
        }

    def _exportar_logs(self, session, usuario_id: UUID) -> List[Dict]:
        """Exporta logs de acesso (últimos 90 dias)."""
        results = session.execute(
            text("""
                SELECT tipo_acao, descricao, timestamp
                FROM log_legal
                WHERE usuario_id = :usuario_id
                  AND timestamp >= NOW() - INTERVAL '90 days'
                  AND anonimizado = FALSE
                ORDER BY timestamp DESC
                LIMIT 100
            """),
            {"usuario_id": usuario_id}
        ).fetchall()

        return [
            {
                "tipo_acao": r[0],
                "descricao": r[1],
                "timestamp": r[2].isoformat() if r[2] else None
            }
            for r in results
        ]

    # ============================================================================
    # ANONIMIZAÇÃO
    # ============================================================================

    def anonimizar_dados_antigos(self) -> int:
        """
        Executa anonimização de dados conforme política de retenção.

        Returns:
            Número de registros anonimizados
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("SELECT anonimizar_dados_antigos()")
            ).fetchone()
            session.commit()

            return result[0] if result else 0
