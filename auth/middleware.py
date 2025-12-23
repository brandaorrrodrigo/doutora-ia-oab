#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
AUTHENTICATION MIDDLEWARE - ETAPA 10.1 / 10.2
================================================================================

Middleware FastAPI para:
- Autenticação JWT automática
- Autorização baseada em roles
- Proteção de rotas
- Injeção de usuário autenticado
- Verificação de modo (pedagogico vs profissional)

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from uuid import UUID
from functools import wraps
from auth.jwt_manager import JWTManager


# ================================================================================
# SECURITY SCHEME
# ================================================================================

security = HTTPBearer()


# ================================================================================
# USUÁRIO AUTENTICADO
# ================================================================================

class UsuarioAutenticado:
    """Representa um usuário autenticado extraído do JWT."""

    def __init__(self, payload: dict):
        self.usuario_id = UUID(payload["sub"])
        self.email = payload["email"]
        self.role = payload["role"]
        self.modo_atual = payload["modo"]
        self.jti = payload["jti"]

    def tem_role(self, role: str) -> bool:
        """Verifica se usuário tem a role especificada."""
        return self.role == role

    def tem_qualquer_role(self, roles: List[str]) -> bool:
        """Verifica se usuário tem qualquer uma das roles."""
        return self.role in roles

    def esta_em_modo(self, modo: str) -> bool:
        """Verifica se usuário está no modo especificado."""
        return self.modo_atual == modo

    def pode_acessar_gabarito(self) -> bool:
        """
        Verifica se usuário pode acessar gabarito.

        Apenas role_pedagogico em modo pedagógico pode acessar.
        role_profissional NUNCA acessa.
        """
        return self.role == "role_pedagogico" and self.modo_atual == "pedagogico"


# ================================================================================
# DEPENDENCY: OBTER USUÁRIO AUTENTICADO
# ================================================================================

jwt_manager = JWTManager()


async def obter_usuario_autenticado(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UsuarioAutenticado:
    """
    Dependency FastAPI para obter usuário autenticado.

    Args:
        credentials: Credenciais Bearer token

    Returns:
        UsuarioAutenticado

    Raises:
        HTTPException: Se token inválido ou expirado
    """
    token = credentials.credentials

    # Validar token
    valido, payload, erro = jwt_manager.validar_access_token(token)

    if not valido:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=erro or "Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UsuarioAutenticado(payload)


# ================================================================================
# DEPENDENCY: OBTER USUÁRIO OPCIONAL (ROTAS PÚBLICAS)
# ================================================================================

async def obter_usuario_opcional(
    request: Request
) -> Optional[UsuarioAutenticado]:
    """
    Dependency FastAPI para obter usuário autenticado (opcional).

    Usado em rotas públicas que podem funcionar com ou sem autenticação.

    Args:
        request: Request FastAPI

    Returns:
        UsuarioAutenticado ou None
    """
    # Tentar extrair token do header
    authorization = request.headers.get("Authorization")

    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    # Validar token
    valido, payload, _ = jwt_manager.validar_access_token(token)

    if not valido:
        return None

    return UsuarioAutenticado(payload)


# ================================================================================
# DECORATOR: REQUER AUTENTICAÇÃO
# ================================================================================

def requer_autenticacao(func):
    """
    Decorator para rotas que requerem autenticação.

    Usage:
        @app.get("/protected")
        @requer_autenticacao
        async def protected_route(usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)):
            return {"usuario_id": usuario.usuario_id}
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # FastAPI Depends já faz a validação
        return await func(*args, **kwargs)
    return wrapper


# ================================================================================
# DEPENDENCY: REQUER ROLE
# ================================================================================

def requer_role(role_requerida: str):
    """
    Dependency factory para exigir role específica.

    Args:
        role_requerida: Role necessária

    Returns:
        Dependency function

    Usage:
        @app.get("/admin")
        async def admin_route(usuario: UsuarioAutenticado = Depends(requer_role("role_admin"))):
            return {"message": "Admin area"}
    """
    async def dependency(
        usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)
    ) -> UsuarioAutenticado:
        if not usuario.tem_role(role_requerida):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Role requerida: {role_requerida}"
            )
        return usuario

    return dependency


# ================================================================================
# DEPENDENCY: REQUER QUALQUER ROLE
# ================================================================================

def requer_qualquer_role(roles_requeridas: List[str]):
    """
    Dependency factory para exigir qualquer uma das roles.

    Args:
        roles_requeridas: Lista de roles aceitáveis

    Returns:
        Dependency function

    Usage:
        @app.get("/mixed")
        async def mixed_route(
            usuario: UsuarioAutenticado = Depends(
                requer_qualquer_role(["role_pedagogico", "role_profissional"])
            )
        ):
            return {"message": "Acesso permitido"}
    """
    async def dependency(
        usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)
    ) -> UsuarioAutenticado:
        if not usuario.tem_qualquer_role(roles_requeridas):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Roles requeridas: {', '.join(roles_requeridas)}"
            )
        return usuario

    return dependency


# ================================================================================
# DEPENDENCY: REQUER MODO
# ================================================================================

def requer_modo(modo_requerido: str):
    """
    Dependency factory para exigir modo específico.

    Args:
        modo_requerido: Modo necessário ('pedagogico' ou 'profissional')

    Returns:
        Dependency function

    Usage:
        @app.get("/pedagogico")
        async def pedagogico_route(
            usuario: UsuarioAutenticado = Depends(requer_modo("pedagogico"))
        ):
            return {"message": "Modo pedagógico"}
    """
    async def dependency(
        usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)
    ) -> UsuarioAutenticado:
        if not usuario.esta_em_modo(modo_requerido):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Modo requerido: {modo_requerido}"
            )
        return usuario

    return dependency


# ================================================================================
# DEPENDENCY: REQUER ACESSO A GABARITO
# ================================================================================

async def requer_acesso_gabarito(
    usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)
) -> UsuarioAutenticado:
    """
    Dependency para rotas que exigem acesso a gabarito.

    Apenas role_pedagogico em modo pedagógico pode acessar.
    role_profissional NUNCA acessa.

    Args:
        usuario: Usuário autenticado

    Returns:
        UsuarioAutenticado

    Raises:
        HTTPException: Se usuário não pode acessar gabarito

    Usage:
        @app.get("/gabarito/{questao_id}")
        async def obter_gabarito(
            questao_id: UUID,
            usuario: UsuarioAutenticado = Depends(requer_acesso_gabarito)
        ):
            # Retornar gabarito
            pass
    """
    if not usuario.pode_acessar_gabarito():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso a gabarito negado. Disponível apenas para modo pedagógico."
        )
    return usuario


# ================================================================================
# DEPENDENCY: MODO PROFISSIONAL (PROÍBE GABARITO)
# ================================================================================

async def requer_modo_profissional(
    usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)
) -> UsuarioAutenticado:
    """
    Dependency para modo profissional.

    Garante que usuário NUNCA verá gabarito.

    Args:
        usuario: Usuário autenticado

    Returns:
        UsuarioAutenticado

    Raises:
        HTTPException: Se não estiver em modo profissional

    Usage:
        @app.post("/questao/responder-sem-gabarito")
        async def responder_profissional(
            usuario: UsuarioAutenticado = Depends(requer_modo_profissional)
        ):
            # Processar resposta SEM mostrar gabarito
            pass
    """
    if not usuario.esta_em_modo("profissional"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rota disponível apenas para modo profissional"
        )
    return usuario


# ================================================================================
# MIDDLEWARE: RATE LIMITING POR USUÁRIO (PREPARAÇÃO PARA ETAPA 10.3)
# ================================================================================

class RateLimitMiddleware:
    """
    Middleware para rate limiting por usuário.

    (Será expandido em ETAPA 10.3 com planos e limites)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # TODO: Implementar rate limiting baseado em plano
        # Por enquanto, apenas passa adiante
        response = await call_next(request)
        return response


# ================================================================================
# EXEMPLO DE USO
# ================================================================================

"""
from fastapi import FastAPI, Depends
from auth.middleware import (
    obter_usuario_autenticado,
    obter_usuario_opcional,
    requer_role,
    requer_qualquer_role,
    requer_modo,
    requer_acesso_gabarito,
    requer_modo_profissional,
    UsuarioAutenticado
)

app = FastAPI()

# Rota pública (sem autenticação)
@app.get("/public")
async def public_route():
    return {"message": "Público"}

# Rota pública com autenticação opcional
@app.get("/semi-public")
async def semi_public_route(usuario: Optional[UsuarioAutenticado] = Depends(obter_usuario_opcional)):
    if usuario:
        return {"message": f"Olá, {usuario.email}"}
    return {"message": "Olá, visitante"}

# Rota protegida (requer autenticação)
@app.get("/protected")
async def protected_route(usuario: UsuarioAutenticado = Depends(obter_usuario_autenticado)):
    return {"usuario_id": str(usuario.usuario_id)}

# Rota apenas para admins
@app.get("/admin")
async def admin_route(usuario: UsuarioAutenticado = Depends(requer_role("role_admin"))):
    return {"message": "Admin area"}

# Rota para pedagógico ou profissional
@app.get("/mixed")
async def mixed_route(
    usuario: UsuarioAutenticado = Depends(
        requer_qualquer_role(["role_pedagogico", "role_profissional"])
    )
):
    return {"role": usuario.role}

# Rota apenas modo pedagógico
@app.get("/pedagogico")
async def pedagogico_route(usuario: UsuarioAutenticado = Depends(requer_modo("pedagogico"))):
    return {"modo": "pedagógico"}

# Rota com acesso a gabarito (CRÍTICA)
@app.get("/gabarito/{questao_id}")
async def obter_gabarito(
    questao_id: str,
    usuario: UsuarioAutenticado = Depends(requer_acesso_gabarito)
):
    # role_profissional NUNCA chega aqui
    return {"gabarito": "C", "questao_id": questao_id}

# Rota modo profissional (SEM gabarito)
@app.post("/responder-profissional")
async def responder_profissional(
    usuario: UsuarioAutenticado = Depends(requer_modo_profissional)
):
    # Processar resposta SEM mostrar gabarito
    return {"feedback": "Resposta registrada", "gabarito_mostrado": False}
"""
