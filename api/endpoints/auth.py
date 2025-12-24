"""
Endpoints de Autenticação - Registro e Login
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from database.connection import DatabaseManager
from database.models import User, UserStatus, PerfilJuridico, NivelDominio
from api.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================================

class RegisterRequest(BaseModel):
    """Request para registro de novo usuário"""
    nome: str = Field(..., min_length=3, max_length=255, description="Nome completo")
    email: EmailStr = Field(..., description="Email válido")
    senha: str = Field(..., min_length=6, description="Senha (mínimo 6 caracteres)")
    cpf: Optional[str] = Field(None, description="CPF (opcional)")
    telefone: Optional[str] = Field(None, description="Telefone (opcional)")


class LoginRequest(BaseModel):
    """Request para login"""
    email: EmailStr = Field(..., description="Email cadastrado")
    senha: str = Field(..., description="Senha")


class AuthResponse(BaseModel):
    """Response de autenticação"""
    success: bool
    message: str
    data: Optional[dict] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Registra um novo usuário no sistema

    - **nome**: Nome completo do usuário
    - **email**: Email único (será validado)
    - **senha**: Senha com mínimo 6 caracteres
    - **cpf**: CPF (opcional)
    - **telefone**: Telefone (opcional)

    Retorna:
    - Token JWT para autenticação
    - Dados básicos do usuário
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        # Verificar se email já existe
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )

        # Verificar se CPF já existe (se fornecido)
        if request.cpf:
            existing_cpf = db.query(User).filter(User.cpf == request.cpf).first()
            if existing_cpf:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CPF já cadastrado"
                )

        # Hash da senha
        password_hash = hash_password(request.senha)

        # Criar novo usuário
        new_user = User(
            nome=request.nome,
            email=request.email,
            password_hash=password_hash,
            cpf=request.cpf,
            telefone=request.telefone,
            status=UserStatus.ATIVO,
            data_ultimo_acesso=datetime.utcnow()
        )

        db.add(new_user)
        db.flush()  # Gera o ID sem commitar

        # Criar perfil jurídico inicial
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
            message="Usuário registrado com sucesso",
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
            detail="Erro ao registrar usuário: dados duplicados"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao registrar usuário: {str(e)}"
        )
    finally:
        db.close()


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """
    Autentica um usuário

    - **email**: Email cadastrado
    - **senha**: Senha do usuário

    Retorna:
    - Token JWT para autenticação
    - Dados do usuário
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        # Buscar usuário pelo email
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

        # Verificar se usuário está ativo
        if user.status != UserStatus.ATIVO and user.status != UserStatus.APROVADO_OAB:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )

        # Atualizar último acesso
        user.data_ultimo_acesso = datetime.utcnow()
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
async def get_current_user(user_id: str = None):
    """
    Retorna dados do usuário autenticado

    Requer autenticação via Bearer token
    """
    from api.auth import get_current_user_id
    from fastapi import Depends

    # TODO: Implementar depois com dependency injection
    # Por enquanto retorna mensagem de não implementado
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint /me será implementado em breve"
    )
