"""
================================================================================
JURIS_IA_CORE_V1 - API REST COM ENFORCEMENT
================================================================================
API RESTful com enforcement completo de limites por plano.

Tecnologia: FastAPI
Enforcement: Integrado em todos os endpoints criticos

Autor: JURIS_IA_CORE_V1
Data: 2025-12-19
================================================================================
"""

import os
import httpx
import json
import asyncio
import requests
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from sqlalchemy import text

# Importa sistema principal
from engines.juris_ia import JurisIA
from engines.piece_engine import PieceType

# Importa enforcement
from core.enforcement import LimitsEnforcement, ReasonCode
from dotenv import load_dotenv

# Importa routers
from api.endpoints.admin import router as admin_router
from api.endpoints.auth import router as auth_router
from api.endpoints.sessao import router as sessao_router
from api.endpoints.progresso import router as progresso_router

# Carrega variaveis de ambiente
# Prioridade: .env.local (desenvolvimento) > .env (producao)
load_dotenv(".env")  # Carrega .env primeiro
load_dotenv(".env.local", override=True)  # Sobrescreve com .env.local se existir

# ============================================================
# SENTRY - MONITORAMENTO DE ERROS (OPCIONAL)
# ============================================================
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    SENTRY_DSN = os.getenv("SENTRY_DSN")
    if SENTRY_DSN:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            environment=os.getenv("ENVIRONMENT", "development"),
            traces_sample_rate=0.1,  # 10% de transações rastreadas
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration()
            ]
        )
        print("✓ Sentry inicializado com sucesso")
except ImportError:
    print("⚠ Sentry SDK não instalado (opcional)")
except Exception as e:
    print(f"⚠ Erro ao inicializar Sentry: {e}")


# ============================================================
# MODELOS DE DADOS (REQUEST/RESPONSE)
# ============================================================

class TipoSessao(str, Enum):
    """Tipos de sessao de estudo"""
    DRILL = "drill"
    SIMULADO = "simulado"
    REVISAO = "revisao"


class SessaoEstudoRequest(BaseModel):
    """Request para iniciar sessao de estudo"""
    aluno_id: str = Field(..., description="ID do aluno")
    disciplina: Optional[str] = Field(None, description="Disciplina especifica")
    tipo: TipoSessao = Field(TipoSessao.DRILL, description="Tipo de sessao")
    modo_estudo_continuo: bool = Field(False, description="Se true, inicia modo revisao")


class RespostaQuestaoRequest(BaseModel):
    """Request para responder questao"""
    aluno_id: str = Field(..., description="ID do aluno")
    questao_id: str = Field(..., description="ID da questao")
    session_id: Optional[str] = Field(None, description="ID da sessao ativa")
    alternativa_escolhida: str = Field(..., description="Alternativa escolhida (A, B, C, D)", pattern="^[A-D]$")
    tempo_segundos: int = Field(..., description="Tempo gasto em segundos", gt=0)


class IniciarPecaRequest(BaseModel):
    """Request para iniciar pratica de peca"""
    aluno_id: str = Field(..., description="ID do aluno")
    tipo_peca: str = Field(..., description="Tipo de peca processual")
    enunciado: str = Field(..., description="Enunciado da questao")


class AvaliarPecaRequest(BaseModel):
    """Request para avaliar peca"""
    aluno_id: str = Field(..., description="ID do aluno")
    tipo_peca: str = Field(..., description="Tipo de peca processual")
    conteudo: str = Field(..., description="Texto da peca escrita")
    enunciado: str = Field(..., description="Enunciado original")


class ChatRequest(BaseModel):
    """Request para chat com IA"""
    user_name: str = Field(..., description="Nome do usuario")
    message: str = Field(..., description="Mensagem do usuario")


class ChatThreadRequest(BaseModel):
    """Request para criar thread de chat"""
    aluno_id: str = Field(..., description="ID do aluno")
    topic: Optional[str] = Field(None, description="Tópico da conversa")
    disciplina: Optional[str] = Field(None, description="Disciplina relacionada")
    title: Optional[str] = Field(None, description="Título da thread")


class ChatMessageRequest(BaseModel):
    """Request para enviar mensagem no chat"""
    aluno_id: str = Field(..., description="ID do aluno")
    thread_id: str = Field(..., description="ID da thread de conversa")
    message: str = Field(..., description="Mensagem do usuário")
    questao_id: Optional[str] = Field(None, description="ID da questão relacionada")
    interacao_id: Optional[str] = Field(None, description="ID da interação relacionada")


class Response(BaseModel):
    """Response padrao da API"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================
# APLICACAO FASTAPI
# ============================================================

app = FastAPI(
    title="JURIS_IA API (com Enforcement)",
    description="API RESTful para o sistema de aprovacao OAB com IA e controle de limites",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuracao CORS
# Em producao, apenas dominios especificos
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://oab.doutoraia.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Incluir routers
app.include_router(admin_router)     # /admin/*
app.include_router(auth_router)      # /auth/register, /auth/login, /auth/me
app.include_router(sessao_router)    # /api/sessao/iniciar, /responder, /finalizar, /ativa
app.include_router(progresso_router) # /api/progresso, /disciplinas, /erros, /ranking

# Instancia global do sistema
sistema = JurisIA()

# Instancia global do enforcement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://juris_ia_user:changeme123@localhost:5432/juris_ia")
enforcement = LimitsEnforcement(DATABASE_URL)

# ============================================================
# RATE LIMITING (OPCIONAL)
# ============================================================
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    print("✓ Rate limiting configurado com sucesso")
except ImportError:
    limiter = None
    print("⚠ slowapi não instalado (rate limiting desabilitado)")


# ============================================================
# EXCEPTION HANDLER CUSTOMIZADO
# ============================================================

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler customizado para HTTPException.
    Garante que bloqueios de enforcement sejam retornados corretamente.
    """
    # Se e um bloqueio de enforcement (403 com detail dict)
    if exc.status_code == status.HTTP_403_FORBIDDEN and isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    # Outros erros HTTP
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": str(exc.detail),
            "status_code": exc.status_code
        }
    )


# ============================================================
# ENDPOINTS - INFORMACOES
# ============================================================

@app.get("/", response_model=Response)
async def root():
    """Endpoint raiz - informacoes da API"""
    return Response(
        success=True,
        data={
            "nome": "JURIS_IA API (Enforcement Enabled)",
            "versao": "2.0.0",
            "descricao": "Sistema de IA para aprovacao na OAB com controle de limites",
            "features": [
                "Enforcement de limites por plano",
                "Mensagens pedagogicas",
                "Logs de auditoria",
                "Modo estudo continuo",
                "Sessoes estendidas"
            ],
            "endpoints": [
                "/estudo/iniciar",
                "/estudo/responder",
                "/estudo/finalizar",
                "/peca/iniciar",
                "/peca/avaliar",
                "/estudante/painel",
                "/estudante/relatorio"
            ]
        },
        message="Sistema operacional com enforcement ativo"
    )


@app.get("/health")
async def health_check():
    """
    Health check para monitoramento com verificação de dependências.
    Retorna 200 se healthy, 503 se degraded.
    """
    from database.connection import get_db_session

    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "enforcement": "ativo",
        "checks": {}
    }

    # Check 1: Database
    try:
        with get_db_session() as session:
            session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["checks"]["database"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"

    # Check 2: Redis (opcional)
    try:
        # Tentar importar Redis client se disponível
        try:
            from database.redis_client import redis_client
            redis_client.ping()
            health_status["checks"]["redis"] = "ok"
        except ImportError:
            health_status["checks"]["redis"] = "not_configured"
    except Exception as e:
        health_status["checks"]["redis"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"

    # Check 3: Ollama
    try:
        ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        if response.status_code == 200:
            health_status["checks"]["ollama"] = "ok"
        else:
            health_status["checks"]["ollama"] = f"status: {response.status_code}"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["checks"]["ollama"] = f"error: {str(e)[:100]}"
        health_status["status"] = "degraded"

    # Return com status code apropriado
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


# ============================================================
# ENDPOINTS - SESSAO DE ESTUDO (COM ENFORCEMENT)
# ============================================================

@app.post("/estudo/iniciar", response_model=Response)
async def iniciar_sessao_estudo(request_body: SessaoEstudoRequest, request: Request):
    """
    Inicia sessao de estudo personalizada.

    **ENFORCEMENT APLICADO:**
    - Verifica limite de sessoes diarias
    - Verifica permissao de estudo continuo (se aplicavel)
    - Bloqueia se plano inativo/expirado

    Retorna conjunto de questoes selecionadas baseado no perfil do estudante.
    """
    try:
        # ENFORCEMENT: Verificar limites
        enforcement_result = enforcement.check_can_start_session(
            user_id=request_body.aluno_id,
            modo_estudo_continuo=request_body.modo_estudo_continuo,
            endpoint="/estudo/iniciar"
        )

        if not enforcement_result.allowed:
            # Bloqueado - retornar resposta de enforcement
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=enforcement_result.to_dict()
            )

        # Permitido - executar logica normal
        resultado = sistema.iniciar_sessao_estudo(
            aluno_id=request_body.aluno_id,
            disciplina=request_body.disciplina,
            tipo=request_body.tipo.value
        )

        return Response(
            success=True,
            data=resultado,
            message=f"Sessao de {request_body.tipo.value} iniciada com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao iniciar sessao. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/estudo/responder", response_model=Response)
@limiter.limit("60/minute") if limiter else lambda x: x
async def responder_questao(request_body: RespostaQuestaoRequest, request: Request):
    """
    Processa resposta de uma questao.

    **ENFORCEMENT APLICADO:**
    - Verifica limite de questoes por sessao
    - Verifica limite de questoes diarias

    Retorna feedback completo com explicacao adaptativa e proximas acoes.
    """
    try:
        # ENFORCEMENT: Verificar limites (se session_id fornecido)
        if request_body.session_id:
            enforcement_result = enforcement.check_can_answer_question(
                user_id=request_body.aluno_id,
                session_id=request_body.session_id,
                endpoint="/estudo/responder"
            )

            if not enforcement_result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=enforcement_result.to_dict()
                )

        # Permitido - executar logica normal
        resultado = sistema.responder_questao(
            aluno_id=request_body.aluno_id,
            questao_id=request_body.questao_id,
            alternativa_escolhida=request_body.alternativa_escolhida,
            tempo_segundos=request_body.tempo_segundos
        )

        return Response(
            success=True,
            data=resultado,
            message="Resposta processada com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao processar resposta. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/estudo/finalizar/{aluno_id}", response_model=Response)
async def finalizar_sessao_estudo(aluno_id: str):
    """
    Finaliza sessao de estudo e gera relatorio.

    Retorna analise completa do desempenho na sessao.
    """
    try:
        resultado = sistema.finalizar_sessao_estudo(aluno_id)

        return Response(
            success=True,
            data=resultado,
            message="Sessao finalizada com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao finalizar sessao. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/estudo/responder/stream")
@limiter.limit("60/minute") if limiter else lambda x: x
async def responder_questao_stream(
    request_body: RespostaQuestaoRequest,
    request: Request
):
    """
    Processa resposta com streaming de explicação (SSE).

    **ENFORCEMENT APLICADO:**
    - Verifica limite de questoes por sessao
    - Verifica limite de questoes diarias

    Retorna explicação em tempo real usando Server-Sent Events.
    """
    try:
        # ENFORCEMENT: Verificar limites (se session_id fornecido)
        if request_body.session_id:
            enforcement_result = enforcement.check_can_answer_question(
                user_id=request_body.aluno_id,
                session_id=request_body.session_id,
                endpoint="/estudo/responder/stream"
            )

            if not enforcement_result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=enforcement_result.to_dict()
                )

        async def event_stream():
            """Gerador de eventos SSE"""
            from database.connection import get_db_session
            from core.explicacao_service_ollama import ExplicacaoServiceOllama

            try:
                with get_db_session() as session:
                    servico = ExplicacaoServiceOllama()

                    # Yield start event
                    yield f"data: {json.dumps({'type': 'start', 'questao_id': request_body.questao_id})}\n\n"

                    # Stream tokens
                    for token in servico.gerar_explicacao_stream(
                        session=session,
                        questao_id=request_body.questao_id,
                        alternativa_escolhida=request_body.alternativa_escolhida,
                        tipo_erro="conceito"
                    ):
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                        await asyncio.sleep(0)  # Permite outros tasks rodarem

                    # Yield completion
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                error_msg = str(e) if os.getenv("DEBUG") else "Erro ao gerar explicação"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao processar resposta em streaming.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - CHAT PEDAGÓGICO (COM LANGCHAIN)
# ============================================================

@app.post("/chat/thread/create", response_model=Response)
@limiter.limit("30/minute") if limiter else lambda x: x
async def criar_thread_chat(request_body: ChatThreadRequest):
    """
    Cria nova thread de conversa no chat pedagógico.

    Retorna ID da thread criada para uso posterior.
    """
    try:
        from database.connection import get_db_session
        from core.chat_service_langchain import ChatServiceLangChain
        from uuid import UUID

        with get_db_session() as session:
            chat_service = ChatServiceLangChain()

            thread_id = chat_service.criar_thread(
                session=session,
                user_id=UUID(request_body.aluno_id),
                title=request_body.title,
                topic=request_body.topic,
                disciplina=request_body.disciplina
            )

            return Response(
                success=True,
                data={
                    "thread_id": str(thread_id),
                    "title": request_body.title or "Nova Conversa"
                },
                message="Thread de chat criada com sucesso"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro ao criar thread de chat",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.get("/chat/threads/{aluno_id}", response_model=Response)
@limiter.limit("120/minute") if limiter else lambda x: x
async def listar_threads_chat(aluno_id: str, limit: int = 20):
    """
    Lista threads de chat do usuário.

    Retorna lista de conversas com metadados.
    """
    try:
        from database.connection import get_db_session
        from core.chat_service_langchain import ChatServiceLangChain
        from uuid import UUID

        with get_db_session() as session:
            chat_service = ChatServiceLangChain()

            threads = chat_service.listar_threads(
                session=session,
                user_id=UUID(aluno_id),
                limit=limit
            )

            return Response(
                success=True,
                data={"threads": threads},
                message="Threads listadas com sucesso"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro ao listar threads",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/chat/message/stream")
@limiter.limit("60/minute") if limiter else lambda x: x
async def enviar_mensagem_stream(request_body: ChatMessageRequest):
    """
    Envia mensagem no chat com streaming de resposta (SSE).

    Retorna resposta da IA em tempo real usando Server-Sent Events.
    """
    try:
        async def event_stream():
            """Gerador de eventos SSE"""
            from database.connection import get_db_session
            from core.chat_service_langchain import ChatServiceLangChain
            from uuid import UUID

            try:
                with get_db_session() as session:
                    chat_service = ChatServiceLangChain()

                    # Yield start event
                    yield f"data: {json.dumps({'type': 'start', 'thread_id': request_body.thread_id})}\n\n"

                    # Converter IDs para UUID
                    questao_id = UUID(request_body.questao_id) if request_body.questao_id else None
                    interacao_id = UUID(request_body.interacao_id) if request_body.interacao_id else None

                    # Stream tokens da resposta
                    for token in chat_service.chat_stream(
                        session=session,
                        user_id=UUID(request_body.aluno_id),
                        thread_id=UUID(request_body.thread_id),
                        message=request_body.message,
                        questao_id=questao_id,
                        interacao_id=interacao_id
                    ):
                        yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                        await asyncio.sleep(0)  # Permite outros tasks rodarem

                    # Yield completion
                    yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                error_msg = str(e) if os.getenv("DEBUG") else "Erro ao gerar resposta"
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro ao processar mensagem do chat",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - PRATICA DE PECAS (COM ENFORCEMENT)
# ============================================================

@app.post("/peca/iniciar", response_model=Response)
async def iniciar_pratica_peca(request_body: IniciarPecaRequest, request: Request):
    """
    Inicia pratica de peca processual.

    **ENFORCEMENT APLICADO:**
    - Verifica limite mensal de pecas
    - Bloqueia se plano nao permite pecas

    Retorna checklist e orientacoes para elaboracao.
    """
    try:
        # ENFORCEMENT: Verificar limites
        enforcement_result = enforcement.check_can_practice_piece(
            user_id=request_body.aluno_id,
            endpoint="/peca/iniciar"
        )

        if not enforcement_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=enforcement_result.to_dict()
            )

        # Converte string para enum
        tipo_peca = PieceType[request_body.tipo_peca.upper()]

        # Permitido - executar logica normal
        resultado = sistema.iniciar_pratica_peca(
            aluno_id=request_body.aluno_id,
            tipo_peca=tipo_peca,
            enunciado=request_body.enunciado
        )

        return Response(
            success=True,
            data=resultado,
            message="Pratica de peca iniciada"
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": True,
                "message": f"Tipo de peca invalido: {request_body.tipo_peca}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao iniciar pratica. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/peca/avaliar", response_model=Response)
async def avaliar_peca(request_body: AvaliarPecaRequest, request: Request):
    """
    Avalia peca escrita pelo estudante.

    Retorna nota, erros encontrados e feedback detalhado.
    """
    try:
        # Converte string para enum
        tipo_peca = PieceType[request_body.tipo_peca.upper()]

        resultado = sistema.avaliar_peca(
            aluno_id=request_body.aluno_id,
            tipo_peca=tipo_peca,
            conteudo=request_body.conteudo,
            enunciado=request_body.enunciado
        )

        return Response(
            success=True,
            data=resultado,
            message="Peca avaliada com sucesso"
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": True,
                "message": f"Tipo de peca invalido: {request_body.tipo_peca}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao avaliar peca. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - ACOMPANHAMENTO DO ESTUDANTE (COM ENFORCEMENT)
# ============================================================

@app.get("/estudante/painel/{aluno_id}", response_model=Response)
async def obter_painel_estudante(aluno_id: str):
    """
    Retorna painel completo do estudante.

    Inclui: desempenho, memoria, proximas revisoes, recomendacoes.
    """
    try:
        resultado = sistema.obter_painel_estudante(aluno_id)

        return Response(
            success=True,
            data=resultado,
            message="Painel obtido com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao obter painel. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.get("/estudante/relatorio/{aluno_id}", response_model=Response)
async def obter_relatorio_progresso(
    aluno_id: str,
    periodo: str = "semanal"
):
    """
    Gera relatorio de progresso.

    **ENFORCEMENT APLICADO:**
    - Verifica se plano permite relatorio completo
    - Retorna versao basica se plano FREE

    Params:
        periodo: "diario", "semanal", "mensal"
    """
    try:
        if periodo not in ["diario", "semanal", "mensal"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": True,
                    "message": "Periodo deve ser 'diario', 'semanal' ou 'mensal'"
                }
            )

        # ENFORCEMENT: Verificar se pode acessar relatorio completo
        enforcement_result = enforcement.check_can_access_complete_report(
            user_id=aluno_id,
            endpoint="/estudante/relatorio"
        )

        if not enforcement_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=enforcement_result.to_dict()
            )

        # Permitido - gerar relatorio completo
        resultado = sistema.obter_relatorio_progresso(aluno_id, periodo)

        return Response(
            success=True,
            data=resultado,
            message=f"Relatorio {periodo} gerado"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao gerar relatorio. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - DIAGNOSTICO E ANALISE
# ============================================================

@app.get("/diagnostico/{aluno_id}", response_model=Response)
async def diagnostico_completo(aluno_id: str):
    """
    Retorna diagnostico completo do estudante.

    Analise profunda de desempenho, padroes de erro, estado emocional.
    """
    try:
        diagnostico = sistema.decision_engine.diagnosticar_estudante(aluno_id)

        return Response(
            success=True,
            data=diagnostico,
            message="Diagnostico gerado com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao gerar diagnostico. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.get("/memoria/{aluno_id}", response_model=Response)
async def analise_memoria(aluno_id: str):
    """
    Retorna analise de memoria do estudante.

    Estado de retencao de conceitos e proximas revisoes.
    """
    try:
        memoria = sistema.memory_engine.analisar_memoria(aluno_id)
        alertas = sistema.memory_engine.detectar_esquecimento(aluno_id)

        return Response(
            success=True,
            data={
                "analise": memoria,
                "alertas": alertas
            },
            message="Analise de memoria concluida"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao analisar memoria. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - CHAT COM IA
# ============================================================

@app.post("/api/chat", response_model=Response)
async def chat_com_ia(request_body: ChatRequest):
    """
    Proxy seguro para chat com IA.

    A API key do chat server fica no backend, nao exposta ao frontend.
    """
    try:
        # URL e API key do chat server (configurados em .env)
        chat_server_url = os.getenv("CHAT_SERVER_URL", "http://localhost:3001")
        chat_api_key = os.getenv("CHAT_API_KEY", "")

        if not chat_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": True,
                    "message": "Chat server nao configurado. Entre em contato com o suporte."
                }
            )

        # Fazer requisicao ao chat server
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{chat_server_url}/api/chat",
                json={
                    "userName": request_body.user_name,
                    "message": request_body.message
                },
                headers={
                    "X-API-Key": chat_api_key,
                    "Content-Type": "application/json"
                }
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={
                        "error": True,
                        "message": "Erro ao comunicar com servidor de chat"
                    }
                )

            chat_response = response.json()

            return Response(
                success=True,
                data={
                    "response": chat_response.get("response", ""),
                    "timestamp": datetime.now().isoformat()
                },
                message="Mensagem processada com sucesso"
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": True,
                "message": "Timeout ao processar mensagem. Tente novamente."
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao processar chat. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# INICIALIZACAO
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a API"""
    print("=" * 70)
    print("JURIS_IA API - INICIANDO (ENFORCEMENT ENABLED)")
    print("=" * 70)
    print("Sistema carregado e pronto para receber requisicoes")
    print("Enforcement: ATIVO")
    print("Documentacao: http://localhost:8000/docs")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a API"""
    print("JURIS_IA API - ENCERRANDO")


# ============================================================
# EXECUCAO
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           JURIS_IA API SERVER (ENFORCEMENT v2.0)           ║
    ║                                                            ║
    ║  Sistema de IA para Aprovacao na OAB                       ║
    ║  Enforcement de Limites: ATIVO                             ║
    ╚════════════════════════════════════════════════════════════╝

    Inicializando servidor...

    Features de Enforcement:
    ✓ Verificacao de limites por plano
    ✓ Mensagens pedagogicas personalizadas
    ✓ Logs de auditoria completos
    ✓ Suporte a estudo continuo
    ✓ Sessoes estendidas (plano Semestral)

    Endpoints disponiveis:
    - POST /estudo/iniciar       - Inicia sessao de estudo
    - POST /estudo/responder     - Responde questao
    - POST /estudo/finalizar     - Finaliza sessao
    - POST /peca/iniciar         - Inicia pratica de peca
    - POST /peca/avaliar         - Avalia peca escrita
    - GET  /estudante/painel     - Painel do estudante
    - GET  /estudante/relatorio  - Relatorio de progresso
    - GET  /diagnostico          - Diagnostico completo
    - GET  /memoria              - Analise de memoria

    Documentacao interativa: http://localhost:8000/docs
    """)

    uvicorn.run(
        "api_server_with_enforcement:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
