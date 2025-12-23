#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
JWT MANAGER - ETAPA 10.1
================================================================================

Gerenciador de tokens JWT com:
- Geração de access tokens (15 minutos)
- Geração de refresh tokens (7 dias)
- Validação de tokens
- Rotação de secrets
- Token family tracking (segurança contra reutilização)

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4
from sqlalchemy import text
from database.connection import DatabaseConnection


class JWTManager:
    """Gerenciador de tokens JWT com suporte a rotação de secrets."""

    # Configurações de tempo de vida
    ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)
    REFRESH_TOKEN_EXPIRY = timedelta(days=7)

    # Algoritmo de assinatura
    ALGORITHM = "HS256"

    def __init__(self):
        self.db = DatabaseConnection()

    # ============================================================================
    # GERAÇÃO DE SECRETS
    # ============================================================================

    def gerar_secret(self, tipo: str = "access") -> str:
        """
        Gera um secret aleatório para assinatura JWT.

        Args:
            tipo: 'access' ou 'refresh'

        Returns:
            Secret de 64 bytes em hexadecimal
        """
        return secrets.token_hex(64)

    def obter_secret_ativo(self, tipo: str = "access") -> str:
        """
        Obtém o secret ativo para assinatura.

        Args:
            tipo: 'access' ou 'refresh'

        Returns:
            Secret ativo ou cria um novo se não existir
        """
        with self.db.get_session() as session:
            # Buscar secret ativo
            result = session.execute(
                text("""
                    SELECT secret_key
                    FROM jwt_secret
                    WHERE ativo = TRUE
                      AND tipo = :tipo
                      AND valido_de <= NOW()
                      AND (valido_ate IS NULL OR valido_ate > NOW())
                    ORDER BY valido_de DESC
                    LIMIT 1
                """),
                {"tipo": tipo}
            ).fetchone()

            if result:
                return result[0]

            # Criar novo secret se não existe
            novo_secret = self.gerar_secret(tipo)

            session.execute(
                text("""
                    INSERT INTO jwt_secret (
                        id,
                        secret_key,
                        ativo,
                        valido_de,
                        tipo,
                        created_at
                    ) VALUES (
                        :id,
                        :secret_key,
                        TRUE,
                        NOW(),
                        :tipo,
                        NOW()
                    )
                """),
                {
                    "id": uuid4(),
                    "secret_key": novo_secret,
                    "tipo": tipo
                }
            )
            session.commit()

            return novo_secret

    def rotacionar_secret(self, tipo: str = "access") -> str:
        """
        Rotaciona o secret ativo (para segurança periódica).

        Args:
            tipo: 'access' ou 'refresh'

        Returns:
            Novo secret gerado
        """
        with self.db.get_session() as session:
            # Desativar secret atual
            session.execute(
                text("""
                    UPDATE jwt_secret
                    SET ativo = FALSE,
                        valido_ate = NOW(),
                        rotacionado_em = NOW()
                    WHERE ativo = TRUE
                      AND tipo = :tipo
                """),
                {"tipo": tipo}
            )

            # Criar novo secret
            novo_secret = self.gerar_secret(tipo)

            session.execute(
                text("""
                    INSERT INTO jwt_secret (
                        id,
                        secret_key,
                        ativo,
                        valido_de,
                        tipo,
                        created_at
                    ) VALUES (
                        :id,
                        :secret_key,
                        TRUE,
                        NOW(),
                        :tipo,
                        NOW()
                    )
                """),
                {
                    "id": uuid4(),
                    "secret_key": novo_secret,
                    "tipo": tipo
                }
            )
            session.commit()

            return novo_secret

    # ============================================================================
    # GERAÇÃO DE TOKENS
    # ============================================================================

    def gerar_access_token(
        self,
        usuario_id: UUID,
        email: str,
        role: str,
        modo_atual: str
    ) -> Tuple[str, str, datetime]:
        """
        Gera um access token JWT.

        Args:
            usuario_id: ID do usuário
            email: Email do usuário
            role: Role do usuário (role_pedagogico, role_profissional, role_admin)
            modo_atual: Modo atual (pedagogico, profissional)

        Returns:
            Tupla (token, jti, expiracao)
        """
        jti = str(uuid4())  # JWT ID único
        agora = datetime.utcnow()
        expiracao = agora + self.ACCESS_TOKEN_EXPIRY

        payload = {
            "jti": jti,
            "sub": str(usuario_id),
            "email": email,
            "role": role,
            "modo": modo_atual,
            "type": "access",
            "iat": agora,
            "exp": expiracao
        }

        secret = self.obter_secret_ativo("access")
        token = jwt.encode(payload, secret, algorithm=self.ALGORITHM)

        return token, jti, expiracao

    def gerar_refresh_token(
        self,
        usuario_id: UUID,
        token_family: Optional[UUID] = None
    ) -> Tuple[str, UUID, UUID, datetime]:
        """
        Gera um refresh token JWT.

        Args:
            usuario_id: ID do usuário
            token_family: Família de tokens (para rotação). Se None, cria nova família.

        Returns:
            Tupla (token, token_id, token_family, expiracao)
        """
        if token_family is None:
            token_family = uuid4()

        token_id = uuid4()
        agora = datetime.utcnow()
        expiracao = agora + self.REFRESH_TOKEN_EXPIRY

        payload = {
            "jti": str(token_id),
            "sub": str(usuario_id),
            "family": str(token_family),
            "type": "refresh",
            "iat": agora,
            "exp": expiracao
        }

        secret = self.obter_secret_ativo("refresh")
        token = jwt.encode(payload, secret, algorithm=self.ALGORITHM)

        return token, token_id, token_family, expiracao

    # ============================================================================
    # VALIDAÇÃO DE TOKENS
    # ============================================================================

    def validar_access_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Valida um access token.

        Args:
            token: Token JWT

        Returns:
            Tupla (valido, payload, erro)
        """
        try:
            secret = self.obter_secret_ativo("access")
            payload = jwt.decode(token, secret, algorithms=[self.ALGORITHM])

            # Verificar tipo
            if payload.get("type") != "access":
                return False, None, "Token não é do tipo access"

            # Verificar se sessão está ativa
            jti = payload.get("jti")
            with self.db.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT ativa
                        FROM sessao_usuario
                        WHERE token_acesso_jti = :jti
                    """),
                    {"jti": jti}
                ).fetchone()

                if not result or not result[0]:
                    return False, None, "Sessão inválida ou expirada"

            return True, payload, None

        except jwt.ExpiredSignatureError:
            return False, None, "Token expirado"
        except jwt.InvalidTokenError as e:
            return False, None, f"Token inválido: {str(e)}"
        except Exception as e:
            return False, None, f"Erro ao validar token: {str(e)}"

    def validar_refresh_token(self, token: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Valida um refresh token.

        Args:
            token: Token JWT

        Returns:
            Tupla (valido, payload, erro)
        """
        try:
            secret = self.obter_secret_ativo("refresh")
            payload = jwt.decode(token, secret, algorithms=[self.ALGORITHM])

            # Verificar tipo
            if payload.get("type") != "refresh":
                return False, None, "Token não é do tipo refresh"

            # Verificar se token está revogado
            jti = payload.get("jti")
            with self.db.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT revogado
                        FROM token_refresh
                        WHERE token = :token
                    """),
                    {"token": token}
                ).fetchone()

                if not result:
                    return False, None, "Token não encontrado no banco"

                if result[0]:  # revogado = True
                    return False, None, "Token revogado"

            return True, payload, None

        except jwt.ExpiredSignatureError:
            return False, None, "Token expirado"
        except jwt.InvalidTokenError as e:
            return False, None, f"Token inválido: {str(e)}"
        except Exception as e:
            return False, None, f"Erro ao validar token: {str(e)}"

    # ============================================================================
    # PERSISTÊNCIA DE TOKENS
    # ============================================================================

    def salvar_refresh_token(
        self,
        usuario_id: UUID,
        token: str,
        token_id: UUID,
        token_family: UUID,
        expiracao: datetime,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Salva refresh token no banco.

        Args:
            usuario_id: ID do usuário
            token: Token JWT
            token_id: ID do token (jti)
            token_family: Família do token
            expiracao: Data de expiração
            ip_origem: IP de origem
            user_agent: User agent
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO token_refresh (
                        id,
                        usuario_id,
                        token,
                        token_family,
                        expira_em,
                        ip_origem,
                        user_agent,
                        created_at
                    ) VALUES (
                        :id,
                        :usuario_id,
                        :token,
                        :token_family,
                        :expira_em,
                        :ip_origem,
                        :user_agent,
                        NOW()
                    )
                """),
                {
                    "id": token_id,
                    "usuario_id": usuario_id,
                    "token": token,
                    "token_family": token_family,
                    "expira_em": expiracao,
                    "ip_origem": ip_origem,
                    "user_agent": user_agent
                }
            )
            session.commit()

    def salvar_sessao(
        self,
        usuario_id: UUID,
        jti: str,
        refresh_token_id: UUID,
        expiracao: datetime,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Salva sessão no banco.

        Args:
            usuario_id: ID do usuário
            jti: JWT ID do access token
            refresh_token_id: ID do refresh token relacionado
            expiracao: Data de expiração do access token
            ip_origem: IP de origem
            user_agent: User agent
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    INSERT INTO sessao_usuario (
                        id,
                        usuario_id,
                        token_acesso_jti,
                        token_refresh_id,
                        expira_em,
                        ip_origem,
                        user_agent,
                        ativa,
                        created_at
                    ) VALUES (
                        :id,
                        :usuario_id,
                        :jti,
                        :refresh_token_id,
                        :expira_em,
                        :ip_origem,
                        :user_agent,
                        TRUE,
                        NOW()
                    )
                """),
                {
                    "id": uuid4(),
                    "usuario_id": usuario_id,
                    "jti": jti,
                    "refresh_token_id": refresh_token_id,
                    "expira_em": expiracao,
                    "ip_origem": ip_origem,
                    "user_agent": user_agent
                }
            )
            session.commit()

    # ============================================================================
    # REFRESH DE TOKENS (ROTAÇÃO)
    # ============================================================================

    def refresh_access_token(
        self,
        refresh_token: str,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Gera novo access token usando refresh token (com rotação).

        Args:
            refresh_token: Refresh token JWT
            ip_origem: IP de origem
            user_agent: User agent

        Returns:
            Tupla (sucesso, dados, erro)
            dados = {
                "access_token": str,
                "refresh_token": str,
                "access_expires_at": datetime,
                "refresh_expires_at": datetime
            }
        """
        # Validar refresh token
        valido, payload, erro = self.validar_refresh_token(refresh_token)
        if not valido:
            return False, None, erro

        usuario_id = UUID(payload["sub"])
        token_family = UUID(payload["family"])

        with self.db.get_session() as session:
            # Buscar dados do usuário
            result = session.execute(
                text("""
                    SELECT email, role, modo_atual, ativo
                    FROM usuario
                    WHERE id = :usuario_id
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            if not result:
                return False, None, "Usuário não encontrado"

            if not result[3]:  # ativo = False
                return False, None, "Usuário inativo"

            email, role, modo_atual = result[0], result[1], result[2]

            # Revogar refresh token antigo (rotação)
            session.execute(
                text("""
                    UPDATE token_refresh
                    SET revogado = TRUE,
                        revogado_em = NOW(),
                        motivo_revogacao = 'Rotação automática'
                    WHERE token = :token
                """),
                {"token": refresh_token}
            )

            # Gerar novo access token
            access_token, jti, access_expiracao = self.gerar_access_token(
                usuario_id, email, role, modo_atual
            )

            # Gerar novo refresh token (mesma família)
            novo_refresh_token, refresh_id, _, refresh_expiracao = self.gerar_refresh_token(
                usuario_id, token_family
            )

            # Salvar novo refresh token
            self.salvar_refresh_token(
                usuario_id,
                novo_refresh_token,
                refresh_id,
                token_family,
                refresh_expiracao,
                ip_origem,
                user_agent
            )

            # Salvar sessão
            self.salvar_sessao(
                usuario_id,
                jti,
                refresh_id,
                access_expiracao,
                ip_origem,
                user_agent
            )

            session.commit()

            return True, {
                "access_token": access_token,
                "refresh_token": novo_refresh_token,
                "access_expires_at": access_expiracao,
                "refresh_expires_at": refresh_expiracao
            }, None

    # ============================================================================
    # REVOGAÇÃO DE TOKENS
    # ============================================================================

    def revogar_refresh_token(self, token: str, motivo: str = "Revogação manual"):
        """
        Revoga um refresh token.

        Args:
            token: Refresh token JWT
            motivo: Motivo da revogação
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    UPDATE token_refresh
                    SET revogado = TRUE,
                        revogado_em = NOW(),
                        motivo_revogacao = :motivo
                    WHERE token = :token
                """),
                {"token": token, "motivo": motivo}
            )
            session.commit()

    def revogar_todos_tokens_usuario(self, usuario_id: UUID):
        """
        Revoga todos os tokens de um usuário (logout completo).

        Args:
            usuario_id: ID do usuário
        """
        with self.db.get_session() as session:
            # Usar função do banco
            session.execute(
                text("SELECT revogar_tokens_usuario(:usuario_id)"),
                {"usuario_id": usuario_id}
            )
            session.commit()

    def finalizar_sessao(self, jti: str):
        """
        Finaliza uma sessão (logout).

        Args:
            jti: JWT ID do access token
        """
        with self.db.get_session() as session:
            session.execute(
                text("""
                    UPDATE sessao_usuario
                    SET ativa = FALSE,
                        finalizada_em = NOW()
                    WHERE token_acesso_jti = :jti
                """),
                {"jti": jti}
            )
            session.commit()

    # ============================================================================
    # LIMPEZA
    # ============================================================================

    def limpar_tokens_expirados(self) -> int:
        """
        Remove tokens expirados do banco.

        Returns:
            Número de tokens removidos
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("SELECT limpar_tokens_expirados()")
            ).fetchone()
            session.commit()
            return result[0]
