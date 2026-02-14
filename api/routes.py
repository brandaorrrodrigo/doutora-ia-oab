"""Rotas da API JURIS IA"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
import psycopg2
from db_legacy import get_db
from schemas import (
    QuestaoResponse,
    QuestaoListResponse,
    SimuladoRequest,
    SimuladoResponse,
    EstatisticasResponse,
    HealthResponse
)
from config import get_settings
import math

router = APIRouter()
settings = get_settings()


@router.get("/", tags=["Informações"])
async def root():
    """Endpoint raiz da API"""
    return {
        "message": "JURIS IA - API de Questões Jurídicas",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "endpoints": {
            "questoes": "/api/questoes",
            "simulado": "/api/simulado",
            "estatisticas": "/api/estatisticas",
            "health": "/api/health"
        }
    }


@router.get("/api/health", response_model=HealthResponse, tags=["Saúde"])
async def health_check(conn=Depends(get_db)):
    """Verifica saúde da API e conexão com o banco"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM questoes;")
        result = cursor.fetchone()
        total_questoes = result['total']
        cursor.close()

        return HealthResponse(
            status="healthy",
            database="connected",
            total_questoes=total_questoes,
            version=settings.API_VERSION
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no health check: {str(e)}")


@router.get("/api/questoes", response_model=QuestaoListResponse, tags=["Questões"])
async def listar_questoes(
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(10, ge=1, le=100, description="Questões por página"),
    disciplina: Optional[str] = Query(None, description="Filtrar por disciplina"),
    fonte: Optional[str] = Query(None, description="Filtrar por fonte"),
    gabarito: Optional[str] = Query(None, pattern="^[A-D]$", description="Filtrar por gabarito"),
    conn=Depends(get_db)
):
    """Lista questões com paginação e filtros"""
    try:
        cursor = conn.cursor()

        # Construir query base
        where_clauses = []
        params = []

        if disciplina:
            where_clauses.append("disciplina ILIKE %s")
            params.append(f"%{disciplina}%")

        if fonte:
            where_clauses.append("fonte ILIKE %s")
            params.append(f"%{fonte}%")

        if gabarito:
            where_clauses.append("gabarito = %s")
            params.append(gabarito.upper())

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Contar total
        count_sql = f"SELECT COUNT(*) as total FROM questoes WHERE {where_sql}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']

        # Calcular paginação
        total_pages = math.ceil(total / per_page)
        offset = (page - 1) * per_page

        # Buscar questões
        query_sql = f"""
            SELECT id, disciplina, enunciado, alternativa_a, alternativa_b,
                   alternativa_c, alternativa_d, gabarito, numero_original,
                   fonte, data_importacao
            FROM questoes
            WHERE {where_sql}
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        cursor.execute(query_sql, params + [per_page, offset])
        questoes = cursor.fetchall()

        cursor.close()

        return QuestaoListResponse(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            questoes=[QuestaoResponse(**q) for q in questoes]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar questões: {str(e)}")


@router.get("/api/questoes/{questao_id}", response_model=QuestaoResponse, tags=["Questões"])
async def obter_questao(questao_id: int, conn=Depends(get_db)):
    """Obtém uma questão específica por ID"""
    try:
        cursor = conn.cursor()

        query = """
            SELECT id, disciplina, enunciado, alternativa_a, alternativa_b,
                   alternativa_c, alternativa_d, gabarito, numero_original,
                   fonte, data_importacao
            FROM questoes
            WHERE id = %s
        """
        cursor.execute(query, (questao_id,))
        questao = cursor.fetchone()

        cursor.close()

        if not questao:
            raise HTTPException(status_code=404, detail="Questão não encontrada")

        return QuestaoResponse(**questao)

    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar questão: {str(e)}")


@router.post("/api/simulado", response_model=SimuladoResponse, tags=["Simulados"])
async def gerar_simulado(request: SimuladoRequest, conn=Depends(get_db)):
    """Gera um simulado aleatório com questões"""
    try:
        cursor = conn.cursor()

        # Construir filtro de disciplinas
        where_sql = "1=1"
        params = []

        if request.disciplinas:
            placeholders = ", ".join(["%s"] * len(request.disciplinas))
            where_sql = f"disciplina IN ({placeholders})"
            params = request.disciplinas

        # Buscar questões aleatórias
        query = f"""
            SELECT id, disciplina, enunciado, alternativa_a, alternativa_b,
                   alternativa_c, alternativa_d, gabarito, numero_original,
                   fonte, data_importacao
            FROM questoes
            WHERE {where_sql}
            ORDER BY RANDOM()
            LIMIT %s
        """
        cursor.execute(query, params + [request.num_questoes])
        questoes = cursor.fetchall()

        cursor.close()

        if not questoes:
            raise HTTPException(
                status_code=404,
                detail="Nenhuma questão encontrada com os critérios especificados"
            )

        # Se não incluir gabarito, remover o campo
        questoes_response = []
        for q in questoes:
            q_dict = dict(q)
            if not request.incluir_gabarito:
                q_dict['gabarito'] = "?"  # Ocultar gabarito
            questoes_response.append(QuestaoResponse(**q_dict))

        # Obter disciplinas únicas
        disciplinas_unicas = list(set(q['disciplina'] for q in questoes))

        return SimuladoResponse(
            total_questoes=len(questoes),
            disciplinas=disciplinas_unicas,
            questoes=questoes_response
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar simulado: {str(e)}")


@router.get("/api/estatisticas", response_model=EstatisticasResponse, tags=["Estatísticas"])
async def obter_estatisticas(conn=Depends(get_db)):
    """Obtém estatísticas do banco de questões"""
    try:
        cursor = conn.cursor()

        # Total geral
        cursor.execute("SELECT COUNT(*) as total FROM questoes")
        total = cursor.fetchone()['total']

        # Por disciplina
        cursor.execute("""
            SELECT disciplina, COUNT(*) as total
            FROM questoes
            GROUP BY disciplina
            ORDER BY total DESC
        """)
        por_disciplina = {row['disciplina']: row['total'] for row in cursor.fetchall()}

        # Por fonte
        cursor.execute("""
            SELECT fonte, COUNT(*) as total
            FROM questoes
            GROUP BY fonte
            ORDER BY total DESC
        """)
        por_fonte = {row['fonte']: row['total'] for row in cursor.fetchall()}

        # Por gabarito
        cursor.execute("""
            SELECT gabarito, COUNT(*) as total
            FROM questoes
            GROUP BY gabarito
            ORDER BY gabarito
        """)
        por_gabarito = {row['gabarito']: row['total'] for row in cursor.fetchall()}

        cursor.close()

        return EstatisticasResponse(
            total_questoes=total,
            por_disciplina=por_disciplina,
            por_fonte=por_fonte,
            por_gabarito=por_gabarito
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")


@router.get("/api/disciplinas", tags=["Informações"])
async def listar_disciplinas(conn=Depends(get_db)):
    """Lista todas as disciplinas disponíveis"""
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT disciplina, COUNT(*) as total
            FROM questoes
            GROUP BY disciplina
            ORDER BY disciplina
        """)
        disciplinas = cursor.fetchall()

        cursor.close()

        return {
            "total": len(disciplinas),
            "disciplinas": [
                {"nome": d['disciplina'], "total_questoes": d['total']}
                for d in disciplinas
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar disciplinas: {str(e)}")
