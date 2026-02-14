"""
Endpoints de Autenticacao - Registro e Login
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from database.connection import DatabaseManager
from database.models import User, UserStatus, PerfilJuridico, NivelDominio
from api.auth import hash_password, verify_password, create_access_token, get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================================

class RegisterRequest(BaseModel):
    """Request para registro de novo usuario"""
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo")
    email: EmailStr = Field(..., description="Email valido")
    senha: str = Field(..., min_length=6, description="Senha (minimo 6 caracteres)")
    cpf: Optional[str] = Field(None, description="CPF (opcional)")
    telefone: Optional[str] = Field(None, description="Telefone (opcional)")


class LoginRequest(BaseModel):
    """Request para login"""
    email: EmailStr = Field(..., description="Email cadastrado")
    senha: str = Field(..., description="Senha")


class AuthResponse(BaseModel):
    """Response de autenticacao"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Registra um novo usuario no sistema

    - **nome**: Nome completo do usuario
    - **email**: Email unico (sera validado)
    - **senha**: Senha com minimo 6 caracteres
    - **cpf**: CPF (opcional)
    - **telefone**: Telefone (opcional)

    Retorna:
    - Token JWT para autenticacao
    - Dados basicos do usuario
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        # Verificar se email ja existe
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email ja cadastrado"
            )

        # Verificar se CPF ja existe (se fornecido)
        if request.cpf:
            existing_cpf = db.query(User).filter(User.cpf == request.cpf).first()
            if existing_cpf:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF ja cadastrado"
                )

        # Hash da senha
        password_hash = hash_password(request.senha)

        # Criar novo usuario
        new_user = User(
            nome=request.nome,
            email=request.email,
            password_hash=password_hash,
            cpf=request.cpf,
            telefone=request.telefone,
            status=UserStatus.ATIVO,
            ultimo_acesso=datetime.utcnow()
        )

        db.add(new_user)
        db.flush()  # Gera o ID sem commitar

        # Criar perfil juridico inicial
        perfil = PerfilJuridico(
            user_id=new_user.id,
            nivel_geral=NivelDominio.INICIANTE,
            pontuacao_global=0,
            taxa_acerto_global=0.0
        )

        db.add(perfil)
        db.commit()
        db.refresh(new_user)

        # Gerar token JWT
        token = create_access_token(
            data={
                "user_id": str(new_user.id),
                "email": new_user.email
            }
        )

        return AuthResponse(
            success=True,
            message="Usuario registrado com sucesso",
            data={
                "token": token,
                "user": {
                    "id": str(new_user.id),
                    "nome": new_user.nome,
                    "email": new_user.email,
                    "status": new_user.status.value
                }
            }
        )

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao registrar usuario: dados duplicados"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar usuario: {str(e)}"
        )
    finally:
        db.close()


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Autentica um usuario

    - **email**: Email cadastrado
    - **senha**: Senha do usuario

    Retorna:
    - Token JWT para autenticacao
    - Dados do usuario
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        # Buscar usuario pelo email
        user = db.query(User).filter(User.email == request.email).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )

        # Verificar senha
        if not verify_password(request.senha, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )

        # Verificar se usuario esta ativo
        if user.status != UserStatus.ATIVO and user.status != UserStatus.APROVADO_OAB:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inativo"
            )

        # Atualizar ultimo acesso
        user.ultimo_acesso = datetime.utcnow()
        db.commit()

        # Gerar token JWT
        token = create_access_token(
            data={
                "user_id": str(user.id),
                "email": user.email
            }
        )

        return AuthResponse(
            success=True,
            message="Login realizado com sucesso",
            data={
                "token": token,
                "user": {
                    "id": str(user.id),
                    "nome": user.nome,
                    "email": user.email,
                    "status": user.status.value
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao fazer login: {str(e)}"
        )
    finally:
        db.close()


@router.get("/me", response_model=AuthResponse)
async def get_current_user(user_id: str = Depends(get_current_user_id)):
    """
    Retorna dados do usuario autenticado

    Requer autenticacao via Bearer token no header Authorization
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        # Buscar usuario pelo ID do JWT
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario nao encontrado"
            )

        # Buscar perfil juridico associado
        perfil = db.query(PerfilJuridico).filter(
            PerfilJuridico.user_id == user.id
        ).first()

        return AuthResponse(
            success=True,
            message="Dados do usuario obtidos com sucesso",
            data={
                "user": {
                    "id": str(user.id),
                    "nome": user.nome,
                    "email": user.email,
                    "status": user.status.value,
                    "created_at": user.created_at.isoformat()
                },
                "perfil": {
                    "nivel_geral": perfil.nivel_geral.value if perfil else "INICIANTE",
                    "pontuacao_global": perfil.pontuacao_global if perfil else 0,
                    "taxa_acerto_global": float(perfil.taxa_acerto_global) if perfil else 0.0,
                    "total_questoes_respondidas": perfil.total_questoes_respondidas if perfil else 0,
                    "total_questoes_corretas": perfil.total_questoes_corretas if perfil else 0,
                    "total_tempo_estudo_minutos": perfil.total_tempo_estudo_minutos if perfil else 0,
                    "sequencia_dias_consecutivos": perfil.sequencia_dias_consecutivos if perfil else 0
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados do usuario: {str(e)}"
        )
    finally:
        db.close()
