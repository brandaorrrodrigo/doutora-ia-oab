"""
Endpoints de Autenticação e Perfil - JURIS_IA_CORE_V1
======================================================

Endpoints para recuperação de senha, perfil e configurações do usuário.

Autor: JURIS_IA_CORE_V1
Data: 2025-12-28
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timedelta
import secrets
import hashlib
import os
import uuid

from database.connection import get_db_session
from database.repositories import RepositoryFactory
from database.models import User, PasswordResetToken, UserSettings
from engines.email_service import get_email_service

router = APIRouter(prefix="/auth", tags=["autenticação"])
user_router = APIRouter(prefix="/usuario", tags=["perfil"])


# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class EsqueciSenhaRequest(BaseModel):
    email: EmailStr


class ResetarSenhaRequest(BaseModel):
    token: str
    nova_senha: str


class AtualizarPerfilRequest(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    data_nascimento: Optional[str] = None
    estado_uf: Optional[str] = None
    cidade: Optional[str] = None


class AtualizarConfiguracoesRequest(BaseModel):
    notificacao_email: Optional[bool] = None
    notificacao_push: Optional[bool] = None
    lembrete_diario: Optional[bool] = None
    horario_lembrete: Optional[str] = None
    tema: Optional[str] = None
    questoes_por_sessao: Optional[int] = None
    dificuldade_preferida: Optional[str] = None
    som_ativado: Optional[bool] = None
    som_acerto: Optional[bool] = None
    som_erro: Optional[bool] = None
    perfil_publico: Optional[bool] = None
    mostrar_ranking: Optional[bool] = None
    compartilhar_estatisticas: Optional[bool] = None


class Response(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None


# ============================================================================
# ENDPOINTS DE RECUPERAÇÃO DE SENHA
# ============================================================================

@router.post("/esqueci-senha", response_model=Response)
async def esqueci_senha(request: EsqueciSenhaRequest):
    """
    Endpoint: POST /auth/esqueci-senha

    Envia email com token de recuperação de senha
    """
    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # Buscar usuário por email
            user = session.query(User).filter(User.email == request.email).first()

            if not user:
                # Por segurança, não revelar se o email existe ou não
                return Response(
                    success=True,
                    message="Se o email existir, você receberá instruções para recuperação de senha"
                )

            # Gerar token seguro
            token = secrets.token_urlsafe(32)

            # Criar registro de reset token
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expira_em=datetime.now() + timedelta(hours=1),
                usado=False
            )

            session.add(reset_token)
            session.commit()

            # Enviar email
            email_service = get_email_service()
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

            email_enviado = email_service.enviar_recuperacao_senha(
                para=user.email,
                nome=user.nome,
                token=token,
                frontend_url=frontend_url
            )

            if not email_enviado:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Erro ao enviar email de recuperação"
                )

            return Response(
                success=True,
                message="Email de recuperação enviado com sucesso"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar solicitação: {str(e)}"
        )


@router.post("/resetar-senha", response_model=Response)
async def resetar_senha(request: ResetarSenhaRequest):
    """
    Endpoint: POST /auth/resetar-senha

    Redefine senha usando token válido
    """
    try:
        with get_db_session() as session:
            # Buscar token
            reset_token = session.query(PasswordResetToken).filter(
                PasswordResetToken.token == request.token,
                PasswordResetToken.usado == False,
                PasswordResetToken.expira_em > datetime.now()
            ).first()

            if not reset_token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token inválido ou expirado"
                )

            # Buscar usuário
            user = session.query(User).filter(User.id == reset_token.user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )

            # Atualizar senha (usando hash seguro)
            import bcrypt
            senha_hash = bcrypt.hashpw(request.nova_senha.encode('utf-8'), bcrypt.gensalt())
            user.password_hash = senha_hash.decode('utf-8')

            # Marcar token como usado
            reset_token.usado = True
            reset_token.usado_em = datetime.now()

            session.commit()

            return Response(
                success=True,
                message="Senha redefinida com sucesso"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao redefinir senha: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE PERFIL DO USUÁRIO
# ============================================================================

@user_router.get("/perfil/{user_id}", response_model=Response)
async def obter_perfil(user_id: str):
    """
    Endpoint: GET /usuario/perfil/{user_id}

    Retorna dados do perfil do usuário
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )

            perfil_data = {
                "id": str(user.id),
                "nome": user.nome,
                "email": user.email,
                "cpf": user.cpf,
                "telefone": user.telefone,
                "data_nascimento": user.data_nascimento.isoformat() if user.data_nascimento else None,
                "estado_uf": user.estado_uf,
                "cidade": user.cidade,
                "foto_perfil": user.foto_perfil,
                "status": user.status.value,
                "created_at": user.created_at.isoformat()
            }

            return Response(
                success=True,
                data=perfil_data
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar perfil: {str(e)}"
        )


@user_router.put("/perfil/{user_id}", response_model=Response)
async def atualizar_perfil(user_id: str, request: AtualizarPerfilRequest):
    """
    Endpoint: PUT /usuario/perfil/{user_id}

    Atualiza dados do perfil do usuário
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )

            # Atualizar campos fornecidos
            if request.nome is not None:
                user.nome = request.nome
            if request.telefone is not None:
                user.telefone = request.telefone
            if request.data_nascimento is not None:
                user.data_nascimento = datetime.fromisoformat(request.data_nascimento)
            if request.estado_uf is not None:
                user.estado_uf = request.estado_uf
            if request.cidade is not None:
                user.cidade = request.cidade

            user.updated_at = datetime.now()
            session.commit()

            return Response(
                success=True,
                message="Perfil atualizado com sucesso"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar perfil: {str(e)}"
        )


@user_router.post("/perfil/{user_id}/foto", response_model=Response)
async def upload_foto_perfil(user_id: str, file: UploadFile = File(...)):
    """
    Endpoint: POST /usuario/perfil/{user_id}/foto

    Faz upload da foto de perfil do usuário
    """
    try:
        # Validar tipo de arquivo
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de imagem inválido. Use JPEG, PNG ou WebP"
            )

        # Validar tamanho (máximo 5MB)
        contents = await file.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Imagem muito grande. Tamanho máximo: 5MB"
            )

        with get_db_session() as session:
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuário não encontrado"
                )

            # Criar diretório de uploads se não existir
            upload_dir = "static/uploads/perfil"
            os.makedirs(upload_dir, exist_ok=True)

            # Gerar nome único para o arquivo
            file_extension = file.filename.split(".")[-1]
            unique_filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)

            # Salvar arquivo
            with open(file_path, "wb") as f:
                f.write(contents)

            # Atualizar URL da foto no banco
            foto_url = f"/uploads/perfil/{unique_filename}"
            user.foto_perfil = foto_url
            session.commit()

            return Response(
                success=True,
                data={"foto_url": foto_url},
                message="Foto de perfil atualizada com sucesso"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao fazer upload da foto: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE CONFIGURAÇÕES
# ============================================================================

@user_router.get("/configuracoes/{user_id}", response_model=Response)
async def obter_configuracoes(user_id: str):
    """
    Endpoint: GET /usuario/configuracoes/{user_id}

    Retorna configurações do usuário
    """
    try:
        with get_db_session() as session:
            settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()

            if not settings:
                # Criar configurações padrão
                settings = UserSettings(user_id=user_id)
                session.add(settings)
                session.commit()
                session.refresh(settings)

            settings_data = {
                "notificacao_email": settings.notificacao_email,
                "notificacao_push": settings.notificacao_push,
                "lembrete_diario": settings.lembrete_diario,
                "horario_lembrete": settings.horario_lembrete,
                "tema": settings.tema,
                "questoes_por_sessao": settings.questoes_por_sessao,
                "dificuldade_preferida": settings.dificuldade_preferida,
                "som_ativado": settings.som_ativado,
                "som_acerto": settings.som_acerto,
                "som_erro": settings.som_erro,
                "perfil_publico": settings.perfil_publico,
                "mostrar_ranking": settings.mostrar_ranking,
                "compartilhar_estatisticas": settings.compartilhar_estatisticas
            }

            return Response(
                success=True,
                data=settings_data
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar configurações: {str(e)}"
        )


@user_router.put("/configuracoes/{user_id}", response_model=Response)
async def atualizar_configuracoes(user_id: str, request: AtualizarConfiguracoesRequest):
    """
    Endpoint: PUT /usuario/configuracoes/{user_id}

    Atualiza configurações do usuário
    """
    try:
        with get_db_session() as session:
            settings = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()

            if not settings:
                settings = UserSettings(user_id=user_id)
                session.add(settings)

            # Atualizar campos fornecidos
            update_data = request.dict(exclude_unset=True)
            for key, value in update_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)

            settings.updated_at = datetime.now()
            session.commit()

            return Response(
                success=True,
                message="Configurações atualizadas com sucesso"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar configurações: {str(e)}"
        )
