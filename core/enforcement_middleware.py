"""
================================================================================
MIDDLEWARE DE ENFORCEMENT - JURIS_IA_CORE_V1
================================================================================
Decorators e helpers para integração de enforcement nos endpoints FastAPI.

Autor: JURIS_IA_CORE_V1 - Engenheiro de Enforcement
Data: 2025-12-19
================================================================================
"""

from functools import wraps
from typing import Callable, Optional
from fastapi import HTTPException, Request, status
import uuid

from core.enforcement import LimitsEnforcement, EnforcementResult


class EnforcementMiddleware:
    """Middleware para aplicar enforcement em endpoints FastAPI"""

    def __init__(self, database_url: str):
        """
        Inicializa middleware.

        Args:
            database_url: URL de conexão PostgreSQL
        """
        self.enforcement = LimitsEnforcement(database_url)

    def require_session_limit(self, modo_estudo_continuo: bool = False):
        """
        Decorator para verificar limite de sessões antes de executar endpoint.

        Args:
            modo_estudo_continuo: Se true, verifica permissão de estudo contínuo

        Usage:
            @app.post("/estudo/iniciar")
            @enforcement_middleware.require_session_limit()
            async def iniciar_sessao(...):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extrair request dos argumentos
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

                if not request:
                    # Tentar kwargs
                    request = kwargs.get('request')

                # Extrair user_id do body/params
                # Assume que o primeiro argumento após Request é o body
                user_id = None
                for arg in args:
                    if hasattr(arg, 'aluno_id'):
                        user_id = arg.aluno_id
                        break

                if not user_id:
                    # Fallback: tentar extrair de kwargs
                    body = kwargs.get('request_body') or kwargs.get('body')
                    if body and hasattr(body, 'aluno_id'):
                        user_id = body.aluno_id

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id/aluno_id não fornecido"
                    )

                # Gerar request_id para correlação
                request_id = str(uuid.uuid4())

                # Verificar enforcement
                result = self.enforcement.check_can_start_session(
                    user_id=user_id,
                    modo_estudo_continuo=modo_estudo_continuo,
                    endpoint=str(request.url.path) if request else "/unknown",
                    request_id=request_id
                )

                if not result.allowed:
                    # Retornar resposta de bloqueio padronizada
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=result.to_dict()
                    )

                # Permitido - executar função original
                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def require_question_limit(self):
        """
        Decorator para verificar limite de questões por sessão.

        Usage:
            @app.post("/estudo/responder")
            @enforcement_middleware.require_question_limit()
            async def responder_questao(...):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extrair user_id e session_id do body
                user_id = None
                session_id = None

                for arg in args:
                    if hasattr(arg, 'aluno_id'):
                        user_id = arg.aluno_id
                    if hasattr(arg, 'session_id'):
                        session_id = arg.session_id

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id não fornecido"
                    )

                # Session ID pode ser obtido de outra forma se necessário
                # Por ora, vamos permitir sem session_id
                # (o enforcement interno vai verificar pelo banco)

                request_id = str(uuid.uuid4())

                # Se temos session_id, verificar
                if session_id:
                    result = self.enforcement.check_can_answer_question(
                        user_id=user_id,
                        session_id=session_id,
                        request_id=request_id
                    )

                    if not result.allowed:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=result.to_dict()
                        )

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def require_piece_limit(self):
        """
        Decorator para verificar limite de peças.

        Usage:
            @app.post("/peca/iniciar")
            @enforcement_middleware.require_piece_limit()
            async def iniciar_peca(...):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user_id = None

                for arg in args:
                    if hasattr(arg, 'aluno_id'):
                        user_id = arg.aluno_id
                        break

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id não fornecido"
                    )

                request_id = str(uuid.uuid4())

                result = self.enforcement.check_can_practice_piece(
                    user_id=user_id,
                    request_id=request_id
                )

                if not result.allowed:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=result.to_dict()
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def require_complete_report_access(self):
        """
        Decorator para verificar acesso a relatório completo.

        Usage:
            @app.get("/estudante/relatorio/{aluno_id}")
            @enforcement_middleware.require_complete_report_access()
            async def obter_relatorio(...):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extrair user_id (pode vir como path param)
                user_id = kwargs.get('aluno_id') or kwargs.get('user_id')

                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="user_id não fornecido"
                    )

                request_id = str(uuid.uuid4())

                result = self.enforcement.check_can_access_complete_report(
                    user_id=user_id,
                    request_id=request_id
                )

                if not result.allowed:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=result.to_dict()
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator


# Helper para criar instância global
def create_enforcement_middleware(database_url: str) -> EnforcementMiddleware:
    """
    Factory para criar middleware de enforcement.

    Args:
        database_url: URL de conexão PostgreSQL

    Returns:
        Instância configurada de EnforcementMiddleware
    """
    return EnforcementMiddleware(database_url)
