"""
================================================================================
JURIS_IA_CORE_V1 - API REST COM ENFORCEMENT
================================================================================
API RESTful com enforcement completo de limites por plano.

Tecnologia: FastAPI
Enforcement: Integrado em todos os endpoints críticos

Autor: JURIS_IA_CORE_V1
Data: 2025-12-19
================================================================================
"""

import os
import httpx
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Importa sistema principal
from engines.juris_ia import JurisIA
from engines.piece_engine import PieceType

# Importa enforcement
from core.enforcement import LimitsEnforcement, ReasonCode
from dotenv import load_dotenv

# Importa routers
from api.endpoints.admin import router as admin_router

# Carrega variáveis de ambiente
# Prioridade: .env.local (desenvolvimento) > .env (produção)
load_dotenv(".env")  # Carrega .env primeiro
load_dotenv(".env.local", override=True)  # Sobrescreve com .env.local se existir


# ============================================================
# MODELOS DE DADOS (REQUEST/RESPONSE)
# ============================================================

class TipoSessao(str, Enum):
    """Tipos de sessão de estudo"""
    DRILL = "drill"
    SIMULADO = "simulado"
    REVISAO = "revisao"


class SessaoEstudoRequest(BaseModel):
    """Request para iniciar sessão de estudo"""
    aluno_id: str = Field(..., description="ID do aluno")
    disciplina: Optional[str] = Field(None, description="Disciplina específica")
    tipo: TipoSessao = Field(TipoSessao.DRILL, description="Tipo de sessão")
    modo_estudo_continuo: bool = Field(False, description="Se true, inicia modo revisão")


class RespostaQuestaoRequest(BaseModel):
    """Request para responder questão"""
    aluno_id: str = Field(..., description="ID do aluno")
    questao_id: str = Field(..., description="ID da questão")
    session_id: Optional[str] = Field(None, description="ID da sessão ativa")
    alternativa_escolhida: str = Field(..., description="Alternativa escolhida (A, B, C, D)", pattern="^[A-D]$")
    tempo_segundos: int = Field(..., description="Tempo gasto em segundos", gt=0)


class IniciarPecaRequest(BaseModel):
    """Request para iniciar prática de peça"""
    aluno_id: str = Field(..., description="ID do aluno")
    tipo_peca: str = Field(..., description="Tipo de peça processual")
    enunciado: str = Field(..., description="Enunciado da questão")


class AvaliarPecaRequest(BaseModel):
    """Request para avaliar peça"""
    aluno_id: str = Field(..., description="ID do aluno")
    tipo_peca: str = Field(..., description="Tipo de peça processual")
    conteudo: str = Field(..., description="Texto da peça escrita")
    enunciado: str = Field(..., description="Enunciado original")


class ChatRequest(BaseModel):
    """Request para chat com IA"""
    user_name: str = Field(..., description="Nome do usuário")
    message: str = Field(..., description="Mensagem do usuário")


class Response(BaseModel):
    """Response padrão da API"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================
# APLICAÇÃO FASTAPI
# ============================================================

app = FastAPI(
    title="JURIS_IA API (com Enforcement)",
    description="API RESTful para o sistema de aprovação OAB com IA e controle de limites",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS
# Em produção, apenas domínios específicos
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://oab.doutoraia.com").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Incluir routers
app.include_router(admin_router)  # Router já tem prefix="/admin" definido

# Instância global do sistema
sistema = JurisIA()

# Instância global do enforcement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://juris_ia_user:changeme123@localhost:5432/juris_ia")
enforcement = LimitsEnforcement(DATABASE_URL)


# ============================================================
# EXCEPTION HANDLER CUSTOMIZADO
# ============================================================

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler customizado para HTTPException.
    Garante que bloqueios de enforcement sejam retornados corretamente.
    """
    # Se é um bloqueio de enforcement (403 com detail dict)
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
# ENDPOINTS - INFORMAÇÕES
# ============================================================

@app.get("/", response_model=Response)
async def root():
    """Endpoint raiz - informações da API"""
    return Response(
        success=True,
        data={
            "nome": "JURIS_IA API (Enforcement Enabled)",
            "versao": "2.0.0",
            "descricao": "Sistema de IA para aprovação na OAB com controle de limites",
            "features": [
                "Enforcement de limites por plano",
                "Mensagens pedagógicas",
                "Logs de auditoria",
                "Modo estudo contínuo",
                "Sessões estendidas"
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
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sistema": "operacional",
        "enforcement": "ativo"
    }


# ============================================================
# ENDPOINTS - SESSÃO DE ESTUDO (COM ENFORCEMENT)
# ============================================================

@app.post("/estudo/iniciar", response_model=Response)
async def iniciar_sessao_estudo(request_body: SessaoEstudoRequest, request: Request):
    """
    Inicia sessão de estudo personalizada.

    **ENFORCEMENT APLICADO:**
    - Verifica limite de sessões diárias
    - Verifica permissão de estudo contínuo (se aplicável)
    - Bloqueia se plano inativo/expirado

    Retorna conjunto de questões selecionadas baseado no perfil do estudante.
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

        # Permitido - executar lógica normal
        resultado = sistema.iniciar_sessao_estudo(
            aluno_id=request_body.aluno_id,
            disciplina=request_body.disciplina,
            tipo=request_body.tipo.value
        )

        return Response(
            success=True,
            data=resultado,
            message=f"Sessão de {request_body.tipo.value} iniciada com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao iniciar sessão. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/estudo/responder", response_model=Response)
async def responder_questao(request_body: RespostaQuestaoRequest, request: Request):
    """
    Processa resposta de uma questão.

    **ENFORCEMENT APLICADO:**
    - Verifica limite de questões por sessão
    - Verifica limite de questões diárias

    Retorna feedback completo com explicação adaptativa e próximas ações.
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

        # Permitido - executar lógica normal
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
    Finaliza sessão de estudo e gera relatório.

    Retorna análise completa do desempenho na sessão.
    """
    try:
        resultado = sistema.finalizar_sessao_estudo(aluno_id)

        return Response(
            success=True,
            data=resultado,
            message="Sessão finalizada com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao finalizar sessão. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - PRÁTICA DE PEÇAS (COM ENFORCEMENT)
# ============================================================

@app.post("/peca/iniciar", response_model=Response)
async def iniciar_pratica_peca(request_body: IniciarPecaRequest, request: Request):
    """
    Inicia prática de peça processual.

    **ENFORCEMENT APLICADO:**
    - Verifica limite mensal de peças
    - Bloqueia se plano não permite peças

    Retorna checklist e orientações para elaboração.
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

        # Permitido - executar lógica normal
        resultado = sistema.iniciar_pratica_peca(
            aluno_id=request_body.aluno_id,
            tipo_peca=tipo_peca,
            enunciado=request_body.enunciado
        )

        return Response(
            success=True,
            data=resultado,
            message="Prática de peça iniciada"
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": True,
                "message": f"Tipo de peça inválido: {request_body.tipo_peca}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao iniciar prática. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.post("/peca/avaliar", response_model=Response)
async def avaliar_peca(request_body: AvaliarPecaRequest, request: Request):
    """
    Avalia peça escrita pelo estudante.

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
            message="Peça avaliada com sucesso"
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": True,
                "message": f"Tipo de peça inválido: {request_body.tipo_peca}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao avaliar peça. Nossa equipe foi notificada.",
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

    Inclui: desempenho, memória, próximas revisões, recomendações.
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
    Gera relatório de progresso.

    **ENFORCEMENT APLICADO:**
    - Verifica se plano permite relatório completo
    - Retorna versão básica se plano FREE

    Params:
        periodo: "diario", "semanal", "mensal"
    """
    try:
        if periodo not in ["diario", "semanal", "mensal"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": True,
                    "message": "Período deve ser 'diario', 'semanal' ou 'mensal'"
                }
            )

        # ENFORCEMENT: Verificar se pode acessar relatório completo
        enforcement_result = enforcement.check_can_access_complete_report(
            user_id=aluno_id,
            endpoint="/estudante/relatorio"
        )

        if not enforcement_result.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=enforcement_result.to_dict()
            )

        # Permitido - gerar relatório completo
        resultado = sistema.obter_relatorio_progresso(aluno_id, periodo)

        return Response(
            success=True,
            data=resultado,
            message=f"Relatório {periodo} gerado"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao gerar relatório. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


# ============================================================
# ENDPOINTS - DIAGNÓSTICO E ANÁLISE
# ============================================================

@app.get("/diagnostico/{aluno_id}", response_model=Response)
async def diagnostico_completo(aluno_id: str):
    """
    Retorna diagnóstico completo do estudante.

    Análise profunda de desempenho, padrões de erro, estado emocional.
    """
    try:
        diagnostico = sistema.decision_engine.diagnosticar_estudante(aluno_id)

        return Response(
            success=True,
            data=diagnostico,
            message="Diagnóstico gerado com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao gerar diagnóstico. Nossa equipe foi notificada.",
                "technical_details": str(e) if os.getenv("DEBUG") else None
            }
        )


@app.get("/memoria/{aluno_id}", response_model=Response)
async def analise_memoria(aluno_id: str):
    """
    Retorna análise de memória do estudante.

    Estado de retenção de conceitos e próximas revisões.
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
            message="Análise de memória concluída"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": True,
                "message": "Erro interno ao analisar memória. Nossa equipe foi notificada.",
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

    A API key do chat server fica no backend, não exposta ao frontend.
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
                    "message": "Chat server não configurado. Entre em contato com o suporte."
                }
            )

        # Fazer requisição ao chat server
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
# INICIALIZAÇÃO
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a API"""
    print("=" * 70)
    print("JURIS_IA API - INICIANDO (ENFORCEMENT ENABLED)")
    print("=" * 70)
    print("Sistema carregado e pronto para receber requisições")
    print("Enforcement: ATIVO")
    print("Documentação: http://localhost:8000/docs")
    print("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Executado ao desligar a API"""
    print("JURIS_IA API - ENCERRANDO")


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           JURIS_IA API SERVER (ENFORCEMENT v2.0)           ║
    ║                                                            ║
    ║  Sistema de IA para Aprovação na OAB                       ║
    ║  Enforcement de Limites: ATIVO                             ║
    ╚════════════════════════════════════════════════════════════╝

    Inicializando servidor...

    Features de Enforcement:
    ✓ Verificação de limites por plano
    ✓ Mensagens pedagógicas personalizadas
    ✓ Logs de auditoria completos
    ✓ Suporte a estudo contínuo
    ✓ Sessões estendidas (plano Semestral)

    Endpoints disponíveis:
    - POST /estudo/iniciar       - Inicia sessão de estudo
    - POST /estudo/responder     - Responde questão
    - POST /estudo/finalizar     - Finaliza sessão
    - POST /peca/iniciar         - Inicia prática de peça
    - POST /peca/avaliar         - Avalia peça escrita
    - GET  /estudante/painel     - Painel do estudante
    - GET  /estudante/relatorio  - Relatório de progresso
    - GET  /diagnostico          - Diagnóstico completo
    - GET  /memoria              - Análise de memória

    Documentação interativa: http://localhost:8000/docs
    """)

    uvicorn.run(
        "api_server_with_enforcement:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
