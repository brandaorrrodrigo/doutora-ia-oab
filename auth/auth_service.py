#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
AUTHENTICATION SERVICE - ETAPA 10.1
================================================================================

Serviço de autenticação com:
- Login com email/senha
- Registro de usuários
- Logout (revogação de tokens)
- Password hashing (bcrypt)
- Proteção contra brute force
- Log de autenticação

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4
from sqlalchemy import text
from database.connection import DatabaseConnection
from auth.jwt_manager import JWTManager


class AuthService:
    """Serviço de autenticação de usuários."""

    # Configurações de segurança
    MAX_TENTATIVAS_LOGIN = 5
    TEMPO_BLOQUEIO = timedelta(minutes=15)

    def __init__(self):
        self.db = DatabaseConnection()
        self.jwt_manager = JWTManager()

    # ============================================================================
    # PASSWORD HASHING
    # ============================================================================

    def hash_password(self, senha: str) -> str:
        """
        Gera hash bcrypt de senha.

        Args:
            senha: Senha em texto plano

        Returns:
            Hash bcrypt
        """
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(senha.encode('utf-8'), salt).decode('utf-8')

    def verificar_senha(self, senha: str, senha_hash: str) -> bool:
        """
        Verifica se senha corresponde ao hash.

        Args:
            senha: Senha em texto plano
            senha_hash: Hash bcrypt armazenado

        Returns:
            True se senha correta
        """
        return bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8'))

    # ============================================================================
    # REGISTRO DE USUÁRIOS
    # ============================================================================

    def registrar_usuario(
        self,
        email: str,
        senha: str,
        nome_completo: str,
        cpf: Optional[str] = None,
        role: str = "role_pedagogico"
    ) -> Tuple[bool, Optional[UUID], Optional[str]]:
        """
        Registra novo usuário.

        Args:
            email: Email do usuário
            senha: Senha em texto plano
            nome_completo: Nome completo
            cpf: CPF (opcional)
            role: Role inicial (padrão: role_pedagogico)

        Returns:
            Tupla (sucesso, usuario_id, erro)
        """
        # Validações
        if not email or '@' not in email:
            return False, None, "Email inválido"

        if not senha or len(senha) < 8:
            return False, None, "Senha deve ter pelo menos 8 caracteres"

        if not nome_completo:
            return False, None, "Nome completo obrigatório"

        if role not in ['role_pedagogico', 'role_profissional']:
            return False, None, "Role inválido"

        with self.db.get_session() as session:
            # Verificar se email já existe
            result = session.execute(
                text("SELECT id FROM usuario WHERE email = :email"),
                {"email": email}
            ).fetchone()

            if result:
                return False, None, "Email já cadastrado"

            # Criar usuário
            usuario_id = uuid4()
            senha_hash = self.hash_password(senha)

            # Determinar modo inicial baseado na role
            modo_inicial = "pedagogico" if role == "role_pedagogico" else "profissional"

            session.execute(
                text("""
                    INSERT INTO usuario (
                        id,
                        email,
                        nome_completo,
                        cpf,
                        senha_hash,
                        role,
                        modo_atual,
                        ativo,
                        created_at
                    ) VALUES (
                        :id,
                        :email,
                        :nome_completo,
                        :cpf,
                        :senha_hash,
                        :role,
                        :modo_atual,
                        TRUE,
                        NOW()
                    )
                """),
                {
                    "id": usuario_id,
                    "email": email,
                    "nome_completo": nome_completo,
                    "cpf": cpf,
                    "senha_hash": senha_hash,
                    "role": role,
                    "modo_atual": modo_inicial
                }
            )
            session.commit()

            # Log de evento
            self._log_evento_autenticacao(
                session,
                usuario_id,
                "registro",
                email,
                True,
                None
            )

            return True, usuario_id, None

    # ============================================================================
    # LOGIN
    # ============================================================================

    def login(
        self,
        email: str,
        senha: str,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Realiza login de usuário.

        Args:
            email: Email do usuário
            senha: Senha em texto plano
            ip_origem: IP de origem
            user_agent: User agent

        Returns:
            Tupla (sucesso, dados, erro)
            dados = {
                "usuario_id": UUID,
                "email": str,
                "nome_completo": str,
                "role": str,
                "modo_atual": str,
                "access_token": str,
                "refresh_token": str,
                "access_expires_at": datetime,
                "refresh_expires_at": datetime
            }
        """
        with self.db.get_session() as session:
            # Buscar usuário
            result = session.execute(
                text("""
                    SELECT id, email, nome_completo, senha_hash, role, modo_atual,
                           ativo, bloqueado, bloqueado_ate, tentativas_login_falhas
                    FROM usuario
                    WHERE email = :email
                """),
                {"email": email}
            ).fetchone()

            if not result:
                self._log_evento_autenticacao(
                    session,
                    None,
                    "login_falha",
                    email,
                    False,
                    "Usuário não encontrado",
                    ip_origem
                )
                return False, None, "Email ou senha inválidos"

            (usuario_id, email_db, nome_completo, senha_hash, role, modo_atual,
             ativo, bloqueado, bloqueado_ate, tentativas_falhas) = result

            # Verificar se usuário está ativo
            if not ativo:
                self._log_evento_autenticacao(
                    session,
                    usuario_id,
                    "login_falha",
                    email,
                    False,
                    "Usuário inativo",
                    ip_origem
                )
                return False, None, "Usuário inativo"

            # Verificar bloqueio temporário
            if bloqueado or (bloqueado_ate and bloqueado_ate > datetime.now()):
                tempo_restante = (bloqueado_ate - datetime.now()).seconds // 60
                self._log_evento_autenticacao(
                    session,
                    usuario_id,
                    "login_falha",
                    email,
                    False,
                    f"Usuário bloqueado por {tempo_restante} minutos",
                    ip_origem
                )
                return False, None, f"Usuário bloqueado. Tente novamente em {tempo_restante} minutos"

            # Verificar senha
            if not self.verificar_senha(senha, senha_hash):
                # Incrementar tentativas falhas
                tentativas_falhas += 1

                if tentativas_falhas >= self.MAX_TENTATIVAS_LOGIN:
                    # Bloquear temporariamente
                    bloqueado_ate = datetime.now() + self.TEMPO_BLOQUEIO

                    session.execute(
                        text("""
                            UPDATE usuario
                            SET tentativas_login_falhas = :tentativas,
                                bloqueado_ate = :bloqueado_ate
                            WHERE id = :usuario_id
                        """),
                        {
                            "tentativas": tentativas_falhas,
                            "bloqueado_ate": bloqueado_ate,
                            "usuario_id": usuario_id
                        }
                    )
                    session.commit()

                    self._log_evento_autenticacao(
                        session,
                        usuario_id,
                        "login_falha",
                        email,
                        False,
                        f"Bloqueio por {self.MAX_TENTATIVAS_LOGIN} tentativas falhas",
                        ip_origem
                    )

                    return False, None, f"Bloqueado por excesso de tentativas. Tente em {self.TEMPO_BLOQUEIO.seconds // 60} minutos"
                else:
                    session.execute(
                        text("""
                            UPDATE usuario
                            SET tentativas_login_falhas = :tentativas
                            WHERE id = :usuario_id
                        """),
                        {
                            "tentativas": tentativas_falhas,
                            "usuario_id": usuario_id
                        }
                    )
                    session.commit()

                    self._log_evento_autenticacao(
                        session,
                        usuario_id,
                        "login_falha",
                        email,
                        False,
                        f"Senha incorreta ({tentativas_falhas}/{self.MAX_TENTATIVAS_LOGIN})",
                        ip_origem
                    )

                    return False, None, "Email ou senha inválidos"

            # LOGIN BEM-SUCEDIDO

            # Resetar tentativas falhas e atualizar último login
            session.execute(
                text("""
                    UPDATE usuario
                    SET tentativas_login_falhas = 0,
                        bloqueado_ate = NULL,
                        ultimo_login = NOW(),
                        ip_ultimo_login = :ip_origem
                    WHERE id = :usuario_id
                """),
                {
                    "ip_origem": ip_origem,
                    "usuario_id": usuario_id
                }
            )

            # Gerar tokens
            access_token, jti, access_expiracao = self.jwt_manager.gerar_access_token(
                usuario_id, email_db, role, modo_atual
            )

            refresh_token, refresh_id, token_family, refresh_expiracao = (
                self.jwt_manager.gerar_refresh_token(usuario_id)
            )

            # Salvar refresh token
            self.jwt_manager.salvar_refresh_token(
                usuario_id,
                refresh_token,
                refresh_id,
                token_family,
                refresh_expiracao,
                ip_origem,
                user_agent
            )

            # Salvar sessão
            self.jwt_manager.salvar_sessao(
                usuario_id,
                jti,
                refresh_id,
                access_expiracao,
                ip_origem,
                user_agent
            )

            session.commit()

            # Log de sucesso
            self._log_evento_autenticacao(
                session,
                usuario_id,
                "login",
                email,
                True,
                None,
                ip_origem
            )

            return True, {
                "usuario_id": usuario_id,
                "email": email_db,
                "nome_completo": nome_completo,
                "role": role,
                "modo_atual": modo_atual,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "access_expires_at": access_expiracao,
                "refresh_expires_at": refresh_expiracao
            }, None

    # ============================================================================
    # LOGOUT
    # ============================================================================

    def logout(self, access_token: str) -> Tuple[bool, Optional[str]]:
        """
        Realiza logout (revoga tokens e finaliza sessão).

        Args:
            access_token: Access token JWT

        Returns:
            Tupla (sucesso, erro)
        """
        # Validar token
        valido, payload, erro = self.jwt_manager.validar_access_token(access_token)
        if not valido:
            return False, erro

        usuario_id = UUID(payload["sub"])
        jti = payload["jti"]

        # Finalizar sessão
        self.jwt_manager.finalizar_sessao(jti)

        # Log de evento
        with self.db.get_session() as session:
            self._log_evento_autenticacao(
                session,
                usuario_id,
                "logout",
                payload["email"],
                True,
                None
            )

        return True, None

    def logout_all(self, usuario_id: UUID) -> Tuple[bool, Optional[str]]:
        """
        Realiza logout de todas as sessões do usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            Tupla (sucesso, erro)
        """
        try:
            # Revogar todos os tokens
            self.jwt_manager.revogar_todos_tokens_usuario(usuario_id)

            # Log de evento
            with self.db.get_session() as session:
                result = session.execute(
                    text("SELECT email FROM usuario WHERE id = :usuario_id"),
                    {"usuario_id": usuario_id}
                ).fetchone()

                if result:
                    self._log_evento_autenticacao(
                        session,
                        usuario_id,
                        "logout_all",
                        result[0],
                        True,
                        None
                    )

            return True, None

        except Exception as e:
            return False, str(e)

    # ============================================================================
    # REFRESH TOKEN
    # ============================================================================

    def refresh_token(
        self,
        refresh_token: str,
        ip_origem: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Renova access token usando refresh token.

        Args:
            refresh_token: Refresh token JWT
            ip_origem: IP de origem
            user_agent: User agent

        Returns:
            Tupla (sucesso, dados, erro)
        """
        sucesso, dados, erro = self.jwt_manager.refresh_access_token(
            refresh_token, ip_origem, user_agent
        )

        if not sucesso:
            return False, None, erro

        # Log de evento
        valido, payload, _ = self.jwt_manager.validar_refresh_token(refresh_token)
        if valido:
            with self.db.get_session() as session:
                self._log_evento_autenticacao(
                    session,
                    UUID(payload["sub"]),
                    "token_refresh",
                    None,
                    True,
                    None,
                    ip_origem
                )

        return True, dados, None

    # ============================================================================
    # ALTERAÇÃO DE SENHA
    # ============================================================================

    def alterar_senha(
        self,
        usuario_id: UUID,
        senha_antiga: str,
        senha_nova: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Altera senha do usuário.

        Args:
            usuario_id: ID do usuário
            senha_antiga: Senha atual
            senha_nova: Nova senha

        Returns:
            Tupla (sucesso, erro)
        """
        # Validações
        if not senha_nova or len(senha_nova) < 8:
            return False, "Nova senha deve ter pelo menos 8 caracteres"

        with self.db.get_session() as session:
            # Buscar usuário
            result = session.execute(
                text("""
                    SELECT senha_hash, email
                    FROM usuario
                    WHERE id = :usuario_id
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            if not result:
                return False, "Usuário não encontrado"

            senha_hash, email = result

            # Verificar senha antiga
            if not self.verificar_senha(senha_antiga, senha_hash):
                self._log_evento_autenticacao(
                    session,
                    usuario_id,
                    "alteracao_senha_falha",
                    email,
                    False,
                    "Senha antiga incorreta"
                )
                return False, "Senha antiga incorreta"

            # Atualizar senha
            novo_hash = self.hash_password(senha_nova)

            session.execute(
                text("""
                    UPDATE usuario
                    SET senha_hash = :novo_hash,
                        updated_at = NOW()
                    WHERE id = :usuario_id
                """),
                {
                    "novo_hash": novo_hash,
                    "usuario_id": usuario_id
                }
            )
            session.commit()

            # Revogar todos os tokens (forçar re-login)
            self.jwt_manager.revogar_todos_tokens_usuario(usuario_id)

            # Log de sucesso
            self._log_evento_autenticacao(
                session,
                usuario_id,
                "alteracao_senha",
                email,
                True,
                "Senha alterada com sucesso"
            )

            return True, None

    # ============================================================================
    # TROCA DE MODO (PEDAGOGICO <-> PROFISSIONAL)
    # ============================================================================

    def trocar_modo(
        self,
        usuario_id: UUID,
        novo_modo: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Troca modo do usuário (pedagogico <-> profissional).

        Args:
            usuario_id: ID do usuário
            novo_modo: Novo modo ('pedagogico' ou 'profissional')

        Returns:
            Tupla (sucesso, erro)
        """
        if novo_modo not in ['pedagogico', 'profissional']:
            return False, "Modo inválido"

        with self.db.get_session() as session:
            # Buscar usuário
            result = session.execute(
                text("""
                    SELECT role, modo_atual, email
                    FROM usuario
                    WHERE id = :usuario_id
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            if not result:
                return False, "Usuário não encontrado"

            role, modo_atual, email = result

            # Verificar se modo é compatível com role
            if novo_modo == 'profissional' and role != 'role_profissional':
                return False, "Modo profissional disponível apenas para role_profissional"

            # Atualizar modo
            session.execute(
                text("""
                    UPDATE usuario
                    SET modo_atual = :novo_modo,
                        updated_at = NOW()
                    WHERE id = :usuario_id
                """),
                {
                    "novo_modo": novo_modo,
                    "usuario_id": usuario_id
                }
            )
            session.commit()

            # Log de evento
            self._log_evento_autenticacao(
                session,
                usuario_id,
                "troca_modo",
                email,
                True,
                f"Modo alterado de {modo_atual} para {novo_modo}"
            )

            return True, None

    # ============================================================================
    # LOG DE EVENTOS
    # ============================================================================

    def _log_evento_autenticacao(
        self,
        session,
        usuario_id: Optional[UUID],
        tipo_evento: str,
        email_tentativa: Optional[str],
        sucesso: bool,
        motivo_falha: Optional[str],
        ip_origem: Optional[str] = None
    ):
        """
        Registra evento de autenticação no log.

        Args:
            session: Sessão do banco
            usuario_id: ID do usuário (None se não identificado)
            tipo_evento: Tipo do evento
            email_tentativa: Email usado na tentativa
            sucesso: Se foi bem-sucedido
            motivo_falha: Motivo da falha (se houver)
            ip_origem: IP de origem
        """
        session.execute(
            text("""
                INSERT INTO log_autenticacao (
                    id,
                    usuario_id,
                    tipo_evento,
                    email_tentativa,
                    sucesso,
                    motivo_falha,
                    ip_origem,
                    timestamp
                ) VALUES (
                    :id,
                    :usuario_id,
                    :tipo_evento,
                    :email_tentativa,
                    :sucesso,
                    :motivo_falha,
                    :ip_origem,
                    NOW()
                )
            """),
            {
                "id": uuid4(),
                "usuario_id": usuario_id,
                "tipo_evento": tipo_evento,
                "email_tentativa": email_tentativa,
                "sucesso": sucesso,
                "motivo_falha": motivo_falha,
                "ip_origem": ip_origem
            }
        )
        session.commit()

    # ============================================================================
    # LIMPEZA
    # ============================================================================

    def limpar_tokens_expirados(self) -> int:
        """
        Remove tokens expirados.

        Returns:
            Número de tokens removidos
        """
        return self.jwt_manager.limpar_tokens_expirados()
