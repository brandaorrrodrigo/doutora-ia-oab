"""
JURIS_IA_CORE_V1 - API REST
API RESTful para acesso ao sistema JURIS_IA

Tecnologia: FastAPI
Endpoints: Estudo, Questões, Peças, Diagnóstico

Para executar:
    pip install fastapi uvicorn pydantic
    uvicorn api_server:app --reload

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Importa sistema principal
from engines.juris_ia import JurisIA
from engines.piece_engine import PieceType


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


class RespostaQuestaoRequest(BaseModel):
    """Request para responder questão"""
    aluno_id: str = Field(..., description="ID do aluno")
    questao_id: str = Field(..., description="ID da questão")
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
    title="JURIS_IA API",
    description="API RESTful para o sistema de aprovação OAB com IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração CORS (permite acesso de qualquer origem)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância global do sistema
sistema = JurisIA()

# Importar e registrar routers
from api.endpoints.admin import router as admin_router
# from api.endpoints.auth import router as auth_router  # Temporariamente desabilitado para debug

app.include_router(admin_router)
# app.include_router(auth_router)  # Temporariamente desabilitado para debug


# ============================================================
# ENDPOINTS - INFORMAÇÕES
# ============================================================

@app.get("/", response_model=Response)
async def root():
    """Endpoint raiz - informações da API"""
    return Response(
        success=True,
        data={
            "nome": "JURIS_IA API",
            "versao": "1.0.0",
            "descricao": "Sistema de IA para aprovação na OAB",
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
        message="Sistema operacional"
    )


@app.get("/health")
async def health_check():
    """Health check para monitoramento"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "sistema": "operacional"
    }


# ============================================================
# ENDPOINTS - SESSÃO DE ESTUDO (1ª FASE)
# ============================================================

@app.post("/estudo/iniciar", response_model=Response)
async def iniciar_sessao_estudo(request: SessaoEstudoRequest):
    """
    Inicia sessão de estudo personalizada.

    Retorna conjunto de questões selecionadas baseado no perfil do estudante.
    """
    try:
        resultado = sistema.iniciar_sessao_estudo(
            aluno_id=request.aluno_id,
            disciplina=request.disciplina,
            tipo=request.tipo.value
        )

        return Response(
            success=True,
            data=resultado,
            message=f"Sessão de {request.tipo.value} iniciada com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar sessão: {str(e)}"
        )


@app.post("/estudo/responder", response_model=Response)
async def responder_questao(request: RespostaQuestaoRequest):
    """
    Processa resposta de uma questão.

    Retorna feedback completo com explicação adaptativa e próximas ações.
    """
    try:
        resultado = sistema.responder_questao(
            aluno_id=request.aluno_id,
            questao_id=request.questao_id,
            alternativa_escolhida=request.alternativa_escolhida,
            tempo_segundos=request.tempo_segundos
        )

        return Response(
            success=True,
            data=resultado,
            message="Resposta processada com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar resposta: {str(e)}"
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
            detail=f"Erro ao finalizar sessão: {str(e)}"
        )


# ============================================================
# ENDPOINTS - PRÁTICA DE PEÇAS (2ª FASE)
# ============================================================

@app.post("/peca/iniciar", response_model=Response)
async def iniciar_pratica_peca(request: IniciarPecaRequest):
    """
    Inicia prática de peça processual.

    Retorna checklist e orientações para elaboração.
    """
    try:
        # Converte string para enum
        tipo_peca = PieceType[request.tipo_peca.upper()]

        resultado = sistema.iniciar_pratica_peca(
            aluno_id=request.aluno_id,
            tipo_peca=tipo_peca,
            enunciado=request.enunciado
        )

        return Response(
            success=True,
            data=resultado,
            message="Prática de peça iniciada"
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de peça inválido: {request.tipo_peca}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar prática: {str(e)}"
        )


@app.post("/peca/avaliar", response_model=Response)
async def avaliar_peca(request: AvaliarPecaRequest):
    """
    Avalia peça escrita pelo estudante.

    Retorna nota, erros encontrados e feedback detalhado.
    """
    try:
        # Converte string para enum
        tipo_peca = PieceType[request.tipo_peca.upper()]

        resultado = sistema.avaliar_peca(
            aluno_id=request.aluno_id,
            tipo_peca=tipo_peca,
            conteudo=request.conteudo,
            enunciado=request.enunciado
        )

        return Response(
            success=True,
            data=resultado,
            message="Peça avaliada com sucesso"
        )

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de peça inválido: {request.tipo_peca}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao avaliar peça: {str(e)}"
        )


# ============================================================
# ENDPOINTS - ACOMPANHAMENTO DO ESTUDANTE
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
            detail=f"Erro ao obter painel: {str(e)}"
        )


@app.get("/estudante/relatorio/{aluno_id}", response_model=Response)
async def obter_relatorio_progresso(
    aluno_id: str,
    periodo: str = "semanal"
):
    """
    Gera relatório de progresso.

    Params:
        periodo: "diario", "semanal", "mensal"
    """
    try:
        if periodo not in ["diario", "semanal", "mensal"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Período deve ser 'diario', 'semanal' ou 'mensal'"
            )

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
            detail=f"Erro ao gerar relatório: {str(e)}"
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
        # Usa o decision engine diretamente para diagnóstico
        diagnostico = sistema.decision_engine.diagnosticar_estudante(aluno_id)

        return Response(
            success=True,
            data=diagnostico,
            message="Diagnóstico gerado com sucesso"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar diagnóstico: {str(e)}"
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
            detail=f"Erro ao analisar memória: {str(e)}"
        )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Executado ao iniciar a API"""
    print("=" * 60)
    print("JURIS_IA API - INICIANDO")
    print("=" * 60)
    print("Sistema carregado e pronto para receber requisições")
    print("Documentação: http://localhost:8000/docs")
    print("=" * 60)


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
    ║                  JURIS_IA API SERVER                       ║
    ║                                                            ║
    ║  Sistema de IA para Aprovação na OAB                       ║
    ║  Versão 1.0.0                                              ║
    ╚════════════════════════════════════════════════════════════╝

    Inicializando servidor...

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
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
