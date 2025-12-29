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

# Importa database
from database.connection import get_db_session
from database.repositories import RepositoryFactory

# Importa gamificação
from engines.gamification import (
    processar_acao,
    AcaoUsuario,
    EstadoGamificacao,
    estado_de_dict,
    estado_para_dict,
    obter_catalogo_conquistas,
)

# Importa repetição espaçada
from engines.spaced_repetition import (
    CartaoRevisao,
    ResultadoRevisao,
    DificuldadeResposta,
    processar_revisao,
    criar_cartao_inicial,
    filtrar_cartoes_pendentes,
    ordenar_cartoes_prioridade,
    calcular_estatisticas_globais,
    cartao_para_dict,
    dict_para_cartao,
)


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


class AcaoGamificacaoRequest(BaseModel):
    """Request para processar ação de gamificação"""
    tipo: str = Field(..., description="Tipo de ação: questao_correta, questao_errada, sessao_completa, peca_concluida, login_diario")
    valor: int = Field(1, description="Quantidade (ex: 1 questão, 1 sessão)", ge=1)
    bonus: int = Field(0, description="Bonus adicional de XP", ge=0)


class RevisaoRequest(BaseModel):
    """Request para processar revisão espaçada"""
    questao_id: str = Field(..., description="ID da questão revisada")
    acertou: bool = Field(..., description="Se acertou a questão")
    dificuldade: str = Field(..., description="Dificuldade percebida: blackout, dificil, medio, facil, muito_facil")
    tempo_segundos: int = Field(..., description="Tempo gasto em segundos", gt=0)


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
from api.auth_endpoints import router as auth_router, user_router
from api.payment_endpoints import router as payment_router

app.include_router(admin_router)
# app.include_router(auth_router)  # Temporariamente desabilitado para debug
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(payment_router)


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
# ENDPOINTS - ANALYTICS E COMPARATIVOS (ENEM-STYLE)
# ============================================================

@app.get("/estudante/analytics/{aluno_id}", response_model=Response)
async def obter_analytics(aluno_id: str):
    """
    Retorna análise completa de desempenho por área + estatísticas comparativas.

    Inspirado no ENEM: mostra desempenho individual vs média geral.
    """
    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # 1. Buscar progresso por disciplina do aluno
            progressos = repos.progresso_disciplina.get_all_by_user(aluno_id)

            # 2. Calcular média geral de todos os estudantes
            query_media = """
                SELECT
                    disciplina,
                    AVG(taxa_acerto) as media_taxa_acerto,
                    COUNT(DISTINCT user_id) as total_estudantes
                FROM progresso_disciplina
                WHERE total_questoes > 0
                GROUP BY disciplina
            """
            resultado_media = session.execute(query_media).fetchall()
            medias_globais = {
                row.disciplina: {
                    "media": float(row.media_taxa_acerto),
                    "total_estudantes": row.total_estudantes
                }
                for row in resultado_media
            }

            # 3. Montar análise comparativa
            analise_por_area = []
            for prog in progressos:
                media_global = medias_globais.get(prog.disciplina, {"media": 0, "total_estudantes": 0})

                diferenca = float(prog.taxa_acerto) - media_global["media"]
                percentil = 50  # Calcular percentil real depois

                analise_por_area.append({
                    "disciplina": prog.disciplina,
                    "seu_desempenho": {
                        "taxa_acerto": float(prog.taxa_acerto),
                        "questoes_respondidas": prog.total_questoes,
                        "acertos": prog.questoes_corretas,
                        "erros": prog.total_questoes - prog.questoes_corretas,
                        "nivel_dominio": prog.nivel_dominio.value,
                        "tempo_medio_minutos": prog.tempo_total_minutos / max(prog.total_questoes, 1)
                    },
                    "comparativo": {
                        "media_geral": media_global["media"],
                        "diferenca": diferenca,
                        "status": "acima_media" if diferenca > 5 else "na_media" if diferenca > -5 else "abaixo_media",
                        "total_estudantes": media_global["total_estudantes"],
                        "percentil_estimado": percentil
                    },
                    "distribuicao_dificuldade": prog.distribuicao_dificuldade
                })

            # 4. Calcular estatísticas gerais
            total_questoes_aluno = sum(p.total_questoes for p in progressos)
            total_acertos_aluno = sum(p.questoes_corretas for p in progressos)
            taxa_global_aluno = (total_acertos_aluno / total_questoes_aluno * 100) if total_questoes_aluno > 0 else 0

            # 5. Ranking de disciplinas (fortes e fracas)
            areas_ordenadas = sorted(
                analise_por_area,
                key=lambda x: x["seu_desempenho"]["taxa_acerto"],
                reverse=True
            )

            return Response(
                success=True,
                data={
                    "resumo_geral": {
                        "taxa_acerto_global": round(taxa_global_aluno, 2),
                        "total_questoes": total_questoes_aluno,
                        "total_acertos": total_acertos_aluno,
                        "areas_estudadas": len(progressos)
                    },
                    "analise_por_area": analise_por_area,
                    "ranking": {
                        "areas_fortes": areas_ordenadas[:3] if len(areas_ordenadas) >= 3 else areas_ordenadas,
                        "areas_fracas": list(reversed(areas_ordenadas[-3:])) if len(areas_ordenadas) >= 3 else []
                    }
                },
                message="Analytics gerado com sucesso"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar analytics: {str(e)}"
        )


@app.get("/estudante/plano-estudos/{aluno_id}", response_model=Response)
async def gerar_plano_estudos(
    aluno_id: str,
    data_prova: str = None  # Formato: YYYY-MM-DD
):
    """
    Gera plano de estudos personalizado baseado na data da prova e desempenho atual.

    Inspirado no ENEM: distribui tempo de estudo por área baseado em fraquezas.
    """
    try:
        from datetime import datetime, timedelta

        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # 1. Calcular dias até a prova
            if data_prova:
                data_prova_dt = datetime.strptime(data_prova, "%Y-%m-%d")
            else:
                # Padrão: próxima prova OAB (exemplo: 3 meses)
                data_prova_dt = datetime.now() + timedelta(days=90)

            dias_restantes = (data_prova_dt - datetime.now()).days

            # 2. Buscar progresso por disciplina
            progressos = repos.progresso_disciplina.get_all_by_user(aluno_id)

            # 3. Identificar áreas que precisam de mais atenção
            areas_priorizadas = []
            for prog in progressos:
                peso_oab = float(prog.peso_prova_oab) if prog.peso_prova_oab else 1.0
                taxa_acerto = float(prog.taxa_acerto)

                # Calcular prioridade (quanto menor a taxa, maior a prioridade)
                prioridade = (100 - taxa_acerto) * peso_oab

                areas_priorizadas.append({
                    "disciplina": prog.disciplina,
                    "taxa_acerto": taxa_acerto,
                    "peso_oab": peso_oab,
                    "prioridade": prioridade,
                    "questoes_estudadas": prog.total_questoes
                })

            # 4. Ordenar por prioridade
            areas_priorizadas.sort(key=lambda x: x["prioridade"], reverse=True)

            # 5. Distribuir tempo de estudo
            total_prioridade = sum(a["prioridade"] for a in areas_priorizadas)
            horas_semanais = 20  # Padrão: 20h/semana

            plano_semanal = []
            for area in areas_priorizadas:
                proporcao = area["prioridade"] / total_prioridade if total_prioridade > 0 else 0
                horas_por_semana = horas_semanais * proporcao
                questoes_por_semana = int(horas_por_semana * 10)  # ~10 questões/hora

                plano_semanal.append({
                    "disciplina": area["disciplina"],
                    "horas_por_semana": round(horas_por_semana, 1),
                    "questoes_por_semana": questoes_por_semana,
                    "dias_sugeridos": ["Segunda", "Quarta", "Sexta"] if horas_por_semana >= 3 else ["Sábado"],
                    "status_atual": "crítico" if area["taxa_acerto"] < 50 else "atenção" if area["taxa_acerto"] < 70 else "reforço"
                })

            # 6. Calcular meta de questões total
            semanas_restantes = max(dias_restantes // 7, 1)
            meta_questoes_total = sum(p["questoes_por_semana"] for p in plano_semanal) * semanas_restantes

            return Response(
                success=True,
                data={
                    "info_prova": {
                        "data_prova": data_prova_dt.strftime("%Y-%m-%d"),
                        "dias_restantes": dias_restantes,
                        "semanas_restantes": semanas_restantes
                    },
                    "plano_semanal": plano_semanal,
                    "metas": {
                        "questoes_por_semana": sum(p["questoes_por_semana"] for p in plano_semanal),
                        "questoes_ate_prova": meta_questoes_total,
                        "horas_por_semana": horas_semanais
                    },
                    "recomendacoes": [
                        f"Priorize {plano_semanal[0]['disciplina']} (área mais crítica)",
                        f"Faça pelo menos {plano_semanal[0]['questoes_por_semana']} questões/semana dessa área",
                        f"Revise áreas fortes nos últimos {min(30, dias_restantes)} dias"
                    ]
                },
                message="Plano de estudos gerado"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar plano de estudos: {str(e)}"
        )


@app.get("/estudante/gerar-simulado/{aluno_id}", response_model=Response)
async def gerar_simulado_oab(
    aluno_id: str,
    tipo: str = "completo"  # "completo" (80q) ou "medio" (40q)
):
    """
    Gera simulado OAB com distribuição oficial de questões por disciplina.

    Args:
        tipo: "completo" (80 questões, 4h) ou "medio" (40 questões, 2h)
    """
    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # Distribuição oficial OAB
            if tipo == "completo":
                distribuicao = {
                    "Direito Civil": 12,
                    "Direito Penal": 10,
                    "Direito Constitucional": 10,
                    "Direito Processual Civil": 10,
                    "Direito Processual Penal": 8,
                    "Direito do Trabalho": 8,
                    "Direito Tributário": 6,
                    "Direito Empresarial": 6,
                    "Direito Administrativo": 5,
                    "Ética Profissional": 5
                }
            else:  # medio
                distribuicao = {
                    "Direito Civil": 6,
                    "Direito Penal": 5,
                    "Direito Constitucional": 5,
                    "Direito Processual Civil": 5,
                    "Direito Processual Penal": 4,
                    "Direito do Trabalho": 4,
                    "Direito Tributário": 3,
                    "Direito Empresarial": 3,
                    "Direito Administrativo": 3,
                    "Ética Profissional": 2
                }

            questoes = []

            # Buscar questões de cada disciplina
            for disciplina, quantidade in distribuicao.items():
                query = """
                    SELECT id, disciplina, enunciado,
                           alternativa_a, alternativa_b, alternativa_c, alternativa_d,
                           alternativa_correta, dificuldade
                    FROM questoes_banco
                    WHERE disciplina = :disciplina
                    AND ativa = true
                    ORDER BY RANDOM()
                    LIMIT :quantidade
                """

                resultado = session.execute(query, {
                    "disciplina": disciplina,
                    "quantidade": quantidade
                }).fetchall()

                for row in resultado:
                    questoes.append({
                        "id": str(row.id),
                        "disciplina": row.disciplina,
                        "enunciado": row.enunciado,
                        "alternativa_a": row.alternativa_a,
                        "alternativa_b": row.alternativa_b,
                        "alternativa_c": row.alternativa_c,
                        "alternativa_d": row.alternativa_d,
                        "alternativa_correta": row.alternativa_correta,
                        "dificuldade": row.dificuldade or "medio"
                    })

            # Embaralhar questões
            import random
            random.shuffle(questoes)

            return Response(
                success=True,
                data={
                    "tipo": tipo,
                    "total_questoes": len(questoes),
                    "tempo_limite_minutos": 240 if tipo == "completo" else 120,
                    "questoes": questoes,
                    "distribuicao": distribuicao
                },
                message=f"Simulado {tipo} gerado com sucesso"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar simulado: {str(e)}"
        )


# ============================================================
# ENDPOINTS - GAMIFICAÇÃO (FP PATTERN)
# ============================================================

@app.get("/gamificacao/{user_id}", response_model=Response)
async def obter_gamificacao(user_id: str):
    """
    Retorna estado atual de gamificação do usuário (XP, nível, conquistas, streak).

    Implementado com programação funcional pura.
    """
    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # Buscar perfil juridico
            perfil = repos.perfil_juridico.get_by_user_id(user_id)

            if not perfil:
                # Criar estado inicial
                estado = EstadoGamificacao(
                    total_fp=0,
                    nivel=1,
                    conquistas=tuple(),
                    streak_atual=0,
                    streak_maximo=0,
                    ultima_atividade=None,
                    total_questoes=0,
                    total_acertos=0,
                    total_sessoes=0,
                    total_pecas=0,
                    taxa_acerto=0.0,
                )
            else:
                # Buscar estatísticas de sessões e peças
                sessoes = repos.sessao_estudo.get_by_user_id(user_id)
                pecas = session.execute(
                    f"SELECT COUNT(*) as total FROM pratica_peca WHERE user_id = '{user_id}'"
                ).fetchone()

                total_sessoes = len(sessoes) if sessoes else 0
                total_pecas = pecas.total if pecas else 0

                # Construir estado
                estado = EstadoGamificacao(
                    total_fp=perfil.pontuacao_global,
                    nivel=int(perfil.nivel_geral.value) if hasattr(perfil.nivel_geral, 'value') else 1,
                    conquistas=tuple(),  # TODO: implementar storage de conquistas
                    streak_atual=perfil.sequencia_dias_consecutivos,
                    streak_maximo=perfil.sequencia_dias_consecutivos,
                    ultima_atividade=perfil.data_ultima_atualizacao_perfil,
                    total_questoes=perfil.total_questoes_respondidas,
                    total_acertos=perfil.total_questoes_corretas,
                    total_sessoes=total_sessoes,
                    total_pecas=total_pecas,
                    taxa_acerto=float(perfil.taxa_acerto_global),
                )

            # Converter para dict
            estado_dict = estado_para_dict(estado)

            # Adicionar informações extras
            from engines.gamification import calcular_fp_para_proximo_nivel, calcular_progresso_nivel

            estado_dict['fp_para_proximo_nivel'] = calcular_fp_para_proximo_nivel(estado.nivel)
            estado_dict['progresso_nivel'] = calcular_progresso_nivel(estado.total_fp, estado.nivel)

            return Response(
                success=True,
                data=estado_dict,
                message="Estado de gamificação recuperado"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter gamificação: {str(e)}"
        )


@app.post("/gamificacao/{user_id}/acao", response_model=Response)
async def processar_acao_gamificacao(user_id: str, acao: AcaoGamificacaoRequest):
    """
    Processa uma ação do usuário e atualiza gamificação (FP, nível, conquistas).

    Implementado com programação funcional pura - sem efeitos colaterais.
    """
    try:
        with get_db_session() as session:
            repos = RepositoryFactory(session)

            # 1. Buscar estado atual (reutiliza lógica acima)
            perfil = repos.perfil_juridico.get_by_user_id(user_id)

            if not perfil:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Perfil do usuário não encontrado"
                )

            # Buscar estatísticas
            sessoes = repos.sessao_estudo.get_by_user_id(user_id)
            pecas = session.execute(
                f"SELECT COUNT(*) as total FROM pratica_peca WHERE user_id = '{user_id}'"
            ).fetchone()

            total_sessoes = len(sessoes) if sessoes else 0
            total_pecas = pecas.total if pecas else 0

            estado_atual = EstadoGamificacao(
                total_fp=perfil.pontuacao_global,
                nivel=int(perfil.nivel_geral.value) if hasattr(perfil.nivel_geral, 'value') else 1,
                conquistas=tuple(),
                streak_atual=perfil.sequencia_dias_consecutivos,
                streak_maximo=perfil.sequencia_dias_consecutivos,
                ultima_atividade=perfil.data_ultima_atualizacao_perfil,
                total_questoes=perfil.total_questoes_respondidas,
                total_acertos=perfil.total_questoes_corretas,
                total_sessoes=total_sessoes,
                total_pecas=total_pecas,
                taxa_acerto=float(perfil.taxa_acerto_global),
            )

            # 2. Criar objeto de ação
            acao_obj = AcaoUsuario(
                tipo=acao.tipo,
                valor=acao.valor,
                bonus=acao.bonus,
                timestamp=datetime.now()
            )

            # 3. Processar ação (FUNÇÃO PURA)
            novo_estado, resultado = processar_acao(estado_atual, acao_obj)

            # 4. Persistir novo estado (side effect isolado)
            perfil.pontuacao_global = novo_estado.total_fp
            perfil.sequencia_dias_consecutivos = novo_estado.streak_atual
            perfil.data_ultima_atualizacao_perfil = novo_estado.ultima_atividade
            perfil.total_questoes_respondidas = novo_estado.total_questoes
            perfil.total_questoes_corretas = novo_estado.total_acertos
            perfil.taxa_acerto_global = novo_estado.taxa_acerto

            session.commit()

            # 5. Retornar resultado
            return Response(
                success=True,
                data={
                    "resultado": resultado,
                    "novo_estado": estado_para_dict(novo_estado)
                },
                message="Ação processada com sucesso!"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar ação: {str(e)}"
        )


@app.get("/gamificacao/conquistas", response_model=Response)
async def listar_conquistas():
    """
    Retorna catálogo completo de conquistas disponíveis.

    Função pura - sem acesso a banco de dados.
    """
    try:
        catalogo = obter_catalogo_conquistas()

        # Agrupar por categoria
        por_categoria = {}
        for conquista in catalogo:
            categoria = conquista['categoria']
            if categoria not in por_categoria:
                por_categoria[categoria] = []
            por_categoria[categoria].append(conquista)

        return Response(
            success=True,
            data={
                "total": len(catalogo),
                "conquistas": catalogo,
                "por_categoria": por_categoria
            },
            message="Catálogo de conquistas recuperado"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar conquistas: {str(e)}"
        )


# ============================================================
# ENDPOINTS - REVISÃO ESPAÇADA (FP PATTERN)
# ============================================================

@app.get("/revisao/{user_id}/pendentes", response_model=Response)
async def obter_revisoes_pendentes(user_id: str, limite: int = 20):
    """
    Retorna cartões de revisão pendentes para o usuário.

    Usa algoritmo SuperMemo SM-2 (programação funcional).
    """
    try:
        with get_db_session() as session:
            # Buscar revisões agendadas do usuário
            query = f"""
                SELECT
                    ra.id,
                    ra.questao_id,
                    ra.disciplina,
                    ra.topico,
                    ra.intervalo_dias,
                    ra.numero_revisao as repeticoes,
                    ra.fator_facilidade as ease_factor,
                    ra.data_conclusao as ultima_revisao,
                    ra.data_agendada as proxima_revisao,
                    COALESCE(stats.total_revisoes, 0) as total_revisoes,
                    COALESCE(stats.acertos, 0) as total_acertos,
                    COALESCE(stats.erros, 0) as total_erros
                FROM revisao_agendada ra
                LEFT JOIN (
                    SELECT
                        questao_id,
                        COUNT(*) as total_revisoes,
                        SUM(CASE WHEN tipo_resposta = 'CORRETA' THEN 1 ELSE 0 END) as acertos,
                        SUM(CASE WHEN tipo_resposta = 'INCORRETA' THEN 1 ELSE 0 END) as erros
                    FROM interacao_questao
                    WHERE user_id = '{user_id}'
                    GROUP BY questao_id
                ) stats ON ra.questao_id = stats.questao_id
                WHERE ra.user_id = '{user_id}'
                AND ra.concluida = FALSE
                ORDER BY ra.data_agendada ASC
                LIMIT {limite}
            """

            resultados = session.execute(query).fetchall()

            agora = datetime.now()
            cartoes = []

            for row in resultados:
                cartao = CartaoRevisao(
                    questao_id=str(row.questao_id),
                    disciplina=row.disciplina,
                    topico=row.topico,
                    intervalo_dias=row.intervalo_dias or 1,
                    repeticoes=row.repeticoes or 0,
                    ease_factor=float(row.ease_factor) if row.ease_factor else 2.5,
                    ultima_revisao=row.ultima_revisao,
                    proxima_revisao=row.proxima_revisao,
                    total_revisoes=row.total_revisoes,
                    total_acertos=row.total_acertos,
                    total_erros=row.total_erros,
                )
                cartoes.append(cartao)

            # Filtrar pendentes (FP)
            pendentes = filtrar_cartoes_pendentes(cartoes, agora)

            # Ordenar por prioridade (FP)
            ordenados = ordenar_cartoes_prioridade(pendentes)

            # Converter para dicts
            cartoes_dict = [cartao_para_dict(c) for c in ordenados]

            # Buscar questões completas
            if cartoes_dict:
                questao_ids = [c["questao_id"] for c in cartoes_dict]
                questoes_query = f"""
                    SELECT
                        id,
                        enunciado,
                        alternativa_a,
                        alternativa_b,
                        alternativa_c,
                        alternativa_d,
                        alternativa_correta,
                        disciplina,
                        topico,
                        dificuldade
                    FROM questoes_banco
                    WHERE id IN ('{"','".join(questao_ids)}')
                """
                questoes = session.execute(questoes_query).fetchall()

                # Mapear questões por ID
                questoes_map = {
                    str(q.id): {
                        "id": str(q.id),
                        "enunciado": q.enunciado,
                        "alternativas": {
                            "A": q.alternativa_a,
                            "B": q.alternativa_b,
                            "C": q.alternativa_c,
                            "D": q.alternativa_d,
                        },
                        "dificuldade": q.dificuldade,
                        "disciplina": q.disciplina,
                        "topico": q.topico,
                    }
                    for q in questoes
                }

                # Adicionar questões aos cartões
                for cartao in cartoes_dict:
                    cartao["questao"] = questoes_map.get(cartao["questao_id"])

            return Response(
                success=True,
                data={
                    "total": len(cartoes_dict),
                    "cartoes": cartoes_dict
                },
                message="Cartões pendentes recuperados"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter revisões pendentes: {str(e)}"
        )


@app.post("/revisao/{user_id}/processar", response_model=Response)
async def processar_revisao_cartao(user_id: str, revisao: RevisaoRequest):
    """
    Processa revisão de um cartão e atualiza próxima data.

    Implementado com programação funcional pura.
    """
    try:
        with get_db_session() as session:
            # Buscar cartão atual
            query = f"""
                SELECT
                    ra.questao_id,
                    ra.disciplina,
                    ra.topico,
                    ra.intervalo_dias,
                    ra.numero_revisao,
                    ra.fator_facilidade,
                    ra.data_conclusao,
                    ra.data_agendada,
                    COALESCE(stats.total, 0) as total_revisoes,
                    COALESCE(stats.acertos, 0) as total_acertos,
                    COALESCE(stats.erros, 0) as total_erros
                FROM revisao_agendada ra
                LEFT JOIN (
                    SELECT
                        questao_id,
                        COUNT(*) as total,
                        SUM(CASE WHEN tipo_resposta = 'CORRETA' THEN 1 ELSE 0 END) as acertos,
                        SUM(CASE WHEN tipo_resposta = 'INCORRETA' THEN 1 ELSE 0 END) as erros
                    FROM interacao_questao
                    WHERE user_id = '{user_id}'
                    GROUP BY questao_id
                ) stats ON ra.questao_id = stats.questao_id
                WHERE ra.user_id = '{user_id}'
                AND ra.questao_id = '{revisao.questao_id}'
                AND ra.concluida = FALSE
                LIMIT 1
            """

            row = session.execute(query).fetchone()

            if not row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cartão de revisão não encontrado"
                )

            # Criar cartão atual
            cartao_atual = CartaoRevisao(
                questao_id=str(row.questao_id),
                disciplina=row.disciplina,
                topico=row.topico,
                intervalo_dias=row.intervalo_dias or 1,
                repeticoes=row.numero_revisao or 0,
                ease_factor=float(row.fator_facilidade) if row.fator_facilidade else 2.5,
                ultima_revisao=row.data_conclusao,
                proxima_revisao=row.data_agendada,
                total_revisoes=row.total_revisoes,
                total_acertos=row.total_acertos,
                total_erros=row.total_erros,
            )

            # Criar resultado da revisão
            resultado = ResultadoRevisao(
                acertou=revisao.acertou,
                dificuldade=DificuldadeResposta(revisao.dificuldade),
                tempo_segundos=revisao.tempo_segundos,
                timestamp=datetime.now()
            )

            # Processar revisão (FUNÇÃO PURA)
            novo_cartao = processar_revisao(cartao_atual, resultado)

            # Persistir novo estado
            update_query = f"""
                UPDATE revisao_agendada
                SET
                    intervalo_dias = {novo_cartao.intervalo_dias},
                    numero_revisao = {novo_cartao.repeticoes},
                    fator_facilidade = {novo_cartao.ease_factor},
                    data_conclusao = '{novo_cartao.ultima_revisao.isoformat()}',
                    concluida = TRUE,
                    resultado_revisao = '{("CORRETA" if revisao.acertou else "INCORRETA")}',
                    proximo_intervalo_calculado = {novo_cartao.intervalo_dias}
                WHERE user_id = '{user_id}'
                AND questao_id = '{revisao.questao_id}'
                AND concluida = FALSE
            """
            session.execute(update_query)

            # Criar nova revisão agendada
            insert_query = f"""
                INSERT INTO revisao_agendada (
                    user_id, questao_id, disciplina, topico,
                    data_agendada, intervalo_dias, numero_revisao,
                    fator_facilidade, concluida
                ) VALUES (
                    '{user_id}',
                    '{novo_cartao.questao_id}',
                    '{novo_cartao.disciplina}',
                    '{novo_cartao.topico}',
                    '{novo_cartao.proxima_revisao.isoformat()}',
                    {novo_cartao.intervalo_dias},
                    {novo_cartao.repeticoes},
                    {novo_cartao.ease_factor},
                    FALSE
                )
            """
            session.execute(insert_query)

            session.commit()

            return Response(
                success=True,
                data={
                    "cartao_anterior": cartao_para_dict(cartao_atual),
                    "novo_cartao": cartao_para_dict(novo_cartao),
                    "proxima_revisao_em": f"{novo_cartao.intervalo_dias} dias"
                },
                message="Revisão processada com sucesso"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar revisão: {str(e)}"
        )


@app.get("/revisao/{user_id}/estatisticas", response_model=Response)
async def obter_estatisticas_revisao(user_id: str):
    """
    Retorna estatísticas de revisão espaçada do usuário.

    Função pura - cálculos feitos em memória.
    """
    try:
        with get_db_session() as session:
            # Buscar todas as revisões do usuário
            query = f"""
                SELECT
                    ra.questao_id,
                    ra.disciplina,
                    ra.topico,
                    ra.intervalo_dias,
                    ra.numero_revisao,
                    ra.fator_facilidade,
                    ra.data_conclusao,
                    ra.data_agendada,
                    COALESCE(stats.total, 0) as total_revisoes,
                    COALESCE(stats.acertos, 0) as total_acertos,
                    COALESCE(stats.erros, 0) as total_erros
                FROM revisao_agendada ra
                LEFT JOIN (
                    SELECT
                        questao_id,
                        COUNT(*) as total,
                        SUM(CASE WHEN tipo_resposta = 'CORRETA' THEN 1 ELSE 0 END) as acertos,
                        SUM(CASE WHEN tipo_resposta = 'INCORRETA' THEN 1 ELSE 0 END) as erros
                    FROM interacao_questao
                    WHERE user_id = '{user_id}'
                    GROUP BY questao_id
                ) stats ON ra.questao_id = stats.questao_id
                WHERE ra.user_id = '{user_id}'
            """

            resultados = session.execute(query).fetchall()

            cartoes = [
                CartaoRevisao(
                    questao_id=str(row.questao_id),
                    disciplina=row.disciplina,
                    topico=row.topico,
                    intervalo_dias=row.intervalo_dias or 1,
                    repeticoes=row.numero_revisao or 0,
                    ease_factor=float(row.fator_facilidade) if row.fator_facilidade else 2.5,
                    ultima_revisao=row.data_conclusao,
                    proxima_revisao=row.data_agendada,
                    total_revisoes=row.total_revisoes,
                    total_acertos=row.total_acertos,
                    total_erros=row.total_erros,
                )
                for row in resultados
            ]

            # Calcular estatísticas (FUNÇÃO PURA)
            stats = calcular_estatisticas_globais(cartoes)

            return Response(
                success=True,
                data=stats,
                message="Estatísticas de revisão calculadas"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter estatísticas: {str(e)}"
        )


# ============================================================
# RECUPERAÇÃO DE SENHA
# ============================================================

class SolicitarResetRequest(BaseModel):
    """Request para solicitar reset de senha"""
    email: str = Field(..., description="Email do usuário")


class ResetarSenhaRequest(BaseModel):
    """Request para resetar senha"""
    token: str = Field(..., description="Token de reset recebido por email")
    nova_senha: str = Field(..., description="Nova senha", min_length=6)


@app.post("/auth/solicitar-reset-senha", response_model=Response)
async def solicitar_reset_senha(request: SolicitarResetRequest):
    """
    Solicita reset de senha. Envia email com token.

    Se o email não existir, retorna sucesso mesmo assim (segurança).
    """
    try:
        from services.password_reset import create_password_reset_token
        from services.email_service import send_password_reset_email

        # Criar token
        sucesso, token, nome = create_password_reset_token(request.email)

        if sucesso and token and nome:
            # Enviar email
            email_enviado = send_password_reset_email(nome, request.email, token)

            if not email_enviado:
                # Log error but don't expose to user
                print(f"Erro ao enviar email de reset para {request.email}")

        # Sempre retornar sucesso (não revelar se email existe)
        return Response(
            success=True,
            message="Se o email existir, você receberá instruções de recuperação de senha."
        )

    except Exception as e:
        # Log error but return generic message
        print(f"Erro em solicitar_reset_senha: {str(e)}")
        return Response(
            success=True,
            message="Se o email existir, você receberá instruções de recuperação de senha."
        )


@app.post("/auth/resetar-senha", response_model=Response)
async def resetar_senha(request: ResetarSenhaRequest):
    """
    Reseta senha usando token válido.
    """
    try:
        from services.password_reset import reset_password
        import bcrypt

        # Hash da nova senha
        senha_hash = bcrypt.hashpw(
            request.nova_senha.encode(),
            bcrypt.gensalt(rounds=12)
        ).decode()

        # Resetar senha
        sucesso, erro = reset_password(request.token, senha_hash)

        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=erro or "Token inválido ou expirado"
            )

        return Response(
            success=True,
            message="Senha redefinida com sucesso! Você já pode fazer login."
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao resetar senha: {str(e)}"
        )


# ============================================================
# ENVIO DE EMAIL DE BOAS-VINDAS
# ============================================================

@app.post("/auth/enviar-boas-vindas", response_model=Response)
async def enviar_email_boas_vindas(user_id: str):
    """
    Envia email de boas-vindas para usuário (chamar após cadastro).
    """
    try:
        from services.email_service import send_welcome_email
        from database.connection import get_db_connection

        # Buscar dados do usuário
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT nome, email FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )

        nome, email = result

        # Enviar email
        enviado = send_welcome_email(nome, email)

        if not enviado:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao enviar email"
            )

        return Response(
            success=True,
            message="Email de boas-vindas enviado com sucesso"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar email: {str(e)}"
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
    - POST /estudo/iniciar              - Inicia sessão de estudo
    - POST /estudo/responder            - Responde questão
    - POST /estudo/finalizar            - Finaliza sessão
    - POST /peca/iniciar                - Inicia prática de peça
    - POST /peca/avaliar                - Avalia peça escrita
    - GET  /estudante/painel            - Painel do estudante
    - GET  /estudante/relatorio         - Relatório de progresso
    - GET  /estudante/analytics         - Análise comparativa (ENEM-style) ✨
    - GET  /estudante/plano-estudos     - Plano de estudos personalizado ✨
    - GET  /diagnostico                 - Diagnóstico completo
    - GET  /memoria                     - Análise de memória

    Documentação interativa: http://localhost:8000/docs
    """)

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
