"""
Serviço de recuperação de senha
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from database.connection import get_db_connection
import logging

logger = logging.getLogger(__name__)


def generate_reset_token() -> str:
    """
    Gera token aleatório para reset de senha
    """
    return secrets.token_urlsafe(32)


def create_password_reset_token(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Cria token de reset de senha para um usuário

    Args:
        email: Email do usuário

    Returns:
        Tuple: (sucesso, token, nome_usuario)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verificar se usuário existe
        cursor.execute(
            "SELECT id, nome FROM users WHERE email = %s",
            (email,)
        )
        result = cursor.fetchone()

        if not result:
            logger.warning(f"Tentativa de reset para email inexistente: {email}")
            return (False, None, None)

        user_id, nome = result

        # Gerar token
        token = generate_reset_token()

        # Hash do token para armazenar no DB (segurança extra)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Expiração: 1 hora
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Inserir token no banco
        cursor.execute("""
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (user_id)
            DO UPDATE SET
                token_hash = EXCLUDED.token_hash,
                expires_at = EXCLUDED.expires_at,
                created_at = EXCLUDED.created_at,
                used_at = NULL
        """, (user_id, token_hash, expires_at))

        conn.commit()

        logger.info(f"Token de reset criado para usuário {user_id} (email: {email})")

        return (True, token, nome)

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao criar token de reset: {str(e)}")
        return (False, None, None)

    finally:
        cursor.close()
        conn.close()


def validate_reset_token(token: str) -> Tuple[bool, Optional[int]]:
    """
    Valida token de reset de senha

    Args:
        token: Token recebido do usuário

    Returns:
        Tuple: (válido, user_id)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        cursor.execute("""
            SELECT user_id, expires_at, used_at
            FROM password_reset_tokens
            WHERE token_hash = %s
        """, (token_hash,))

        result = cursor.fetchone()

        if not result:
            logger.warning("Token de reset não encontrado")
            return (False, None)

        user_id, expires_at, used_at = result

        # Verificar se já foi usado
        if used_at is not None:
            logger.warning(f"Token de reset já foi usado (user_id: {user_id})")
            return (False, None)

        # Verificar se expirou
        if datetime.utcnow() > expires_at:
            logger.warning(f"Token de reset expirado (user_id: {user_id})")
            return (False, None)

        return (True, user_id)

    except Exception as e:
        logger.error(f"Erro ao validar token de reset: {str(e)}")
        return (False, None)

    finally:
        cursor.close()
        conn.close()


def reset_password(token: str, new_password_hash: str) -> Tuple[bool, Optional[str]]:
    """
    Redefine senha do usuário usando token válido

    Args:
        token: Token de reset
        new_password_hash: Hash bcrypt da nova senha

    Returns:
        Tuple: (sucesso, mensagem_erro)
    """
    # Validar token
    valid, user_id = validate_reset_token(token)

    if not valid:
        return (False, "Token inválido ou expirado")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Atualizar senha
        cursor.execute("""
            UPDATE users
            SET password_hash = %s, atualizado_em = NOW()
            WHERE id = %s
        """, (new_password_hash, user_id))

        # Marcar token como usado
        cursor.execute("""
            UPDATE password_reset_tokens
            SET used_at = NOW()
            WHERE token_hash = %s
        """, (token_hash,))

        conn.commit()

        logger.info(f"Senha redefinida com sucesso para user_id: {user_id}")

        return (True, None)

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao redefinir senha: {str(e)}")
        return (False, "Erro ao redefinir senha")

    finally:
        cursor.close()
        conn.close()


def cleanup_expired_tokens():
    """
    Remove tokens expirados do banco (executar via cron job)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            DELETE FROM password_reset_tokens
            WHERE expires_at < NOW() - INTERVAL '7 days'
        """)

        deleted_count = cursor.rowcount
        conn.commit()

        logger.info(f"Tokens expirados removidos: {deleted_count}")

        return deleted_count

    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao limpar tokens expirados: {str(e)}")
        return 0

    finally:
        cursor.close()
        conn.close()
