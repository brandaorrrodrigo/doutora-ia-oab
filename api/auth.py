"""
Módulo de Autenticação - JWT e Password Hashing
"""
import os
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configurações
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-JURIS_IA_2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 dias

# Context para hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()


def hash_password(password: str) -> str:
    """
    Faz hash de uma senha usando bcrypt

    Args:
        password: Senha em texto plano

    Returns:
        str: Hash da senha
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha corresponde ao hash

    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash armazenado no banco

    Returns:
        bool: True se a senha está correta
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um JWT token de acesso

    Args:
        data: Dados a serem encodados no token
        expires_delta: Tempo de expiração customizado

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decodifica e valida um JWT token

    Args:
        token: JWT token

    Returns:
        dict: Dados decodificados do token

    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Token inválido"
        )


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Dependency para obter o ID do usuário autenticado

    Args:
        credentials: Credenciais HTTP Bearer

    Returns:
        str: ID do usuário

    Raises:
        HTTPException: Se o token for inválido
    """
    token = credentials.credentials
    payload = decode_token(token)

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Token inválido: user_id não encontrado"
        )

    return user_id


# Dependency opcional (não obrigatório)
def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    """
    Dependency para obter o ID do usuário se estiver autenticado
    Não lança erro se não houver token

    Args:
        credentials: Credenciais HTTP Bearer (opcional)

    Returns:
        Optional[str]: ID do usuário ou None
    """
    if credentials is None:
        return None

    try:
        token = credentials.credentials
        payload = decode_token(token)
        return payload.get("user_id")
    except HTTPException:
        return None
