"""
Endpoints de Progresso e Dashboard - Acompanhamento do usuario
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func

from database.connection import DatabaseManager
from database.models import SessaoEstudo, InteracaoQuestao, TipoResposta
from database.repositories import RepositoryFactory
from api.auth import get_current_user_id
from api.schemas import (
    ProgressoGeralResponse,
    ProgressoDisciplinaItem,
    ProgressoDisciplinasResponse,
    ErroRecenteItem,
    ErrosAnaliseResponse,
    RankingItem,
    RankingResponse
)

router = APIRouter(prefix="/api/progresso", tags=["progresso"])


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("", response_model=ProgressoGeralResponse)
async def progresso_geral(
    user_id: str = Depends(get_current_user_id)
):
    """
    Dashboard geral do progresso do usuario

    Retorna: nivel, pontuacao, taxa de acerto, tempo de estudo,
    total de sessoes, sequencia de dias consecutivos.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        # Buscar perfil juridico
        perfil = repos.perfis.get_by_user_id(uid)
        if not perfil:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil nao encontrado. Registre-se primeiro."
            )

        # Contar total de sessoes do usuario
        total_sessoes = db.query(func.count(SessaoEstudo.id)).filter(
            SessaoEstudo.user_id == uid,
            SessaoEstudo.fim != None
        ).scalar() or 0

        return ProgressoGeralResponse(
            total_questoes_respondidas=perfil.total_questoes_respondidas or 0,
            total_questoes_corretas=perfil.total_questoes_corretas or 0,
            taxa_acerto_global=float(perfil.taxa_acerto_global or 0),
            nivel_geral=perfil.nivel_geral.value if perfil.nivel_geral else "INICIANTE",
            pontuacao_global=perfil.pontuacao_global or 0,
            total_sessoes=total_sessoes,
            tempo_total_estudo_minutos=perfil.total_tempo_estudo_minutos or 0,
            sequencia_dias_consecutivos=perfil.sequencia_dias_consecutivos or 0
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar progresso: {str(e)}"
        )
    finally:
        db.close()


@router.get("/disciplinas", response_model=ProgressoDisciplinasResponse)
async def progresso_por_disciplina(
    user_id: str = Depends(get_current_user_id)
):
    """
    Progresso detalhado por disciplina

    Retorna lista com taxa de acerto, nivel de dominio e total por disciplina.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        # Buscar todos os progressos por disciplina
        progressos = repos.progressos_disciplina.get_all_by_user(uid)

        disciplinas = []
        for p in progressos:
            disciplinas.append(ProgressoDisciplinaItem(
                disciplina=p.disciplina,
                total_questoes=p.total_questoes or 0,
                questoes_corretas=p.questoes_corretas or 0,
                taxa_acerto=float(p.taxa_acerto or 0),
                nivel_dominio=p.nivel_dominio.value if p.nivel_dominio else "INICIANTE",
                prioridade_estudo=p.prioridade_estudo or 5
            ))

        return ProgressoDisciplinasResponse(
            total_disciplinas=len(disciplinas),
            disciplinas=disciplinas
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar progresso por disciplina: {str(e)}"
        )
    finally:
        db.close()


@router.get("/erros", response_model=ErrosAnaliseResponse)
async def analise_erros(
    user_id: str = Depends(get_current_user_id)
):
    """
    Analise de erros recentes do usuario

    Retorna erros dos ultimos 30 dias e taxa de acerto por disciplina.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        # Buscar erros recentes (ultimos 30 dias)
        erros_recentes = repos.interacoes.get_recent_errors(
            user_id=uid,
            days=30,
            limit=20
        )

        # Buscar taxa de acerto por disciplina
        taxa_por_disciplina = repos.interacoes.get_accuracy_by_discipline(uid)

        # Montar lista de erros
        erros_lista = []
        for erro in erros_recentes:
            erros_lista.append(ErroRecenteItem(
                disciplina=erro.disciplina,
                alternativa_escolhida=erro.alternativa_escolhida,
                alternativa_correta=erro.alternativa_correta,
                tempo_resposta_segundos=erro.tempo_resposta_segundos,
                created_at=erro.created_at.isoformat() if erro.created_at else ""
            ))

        # Montar taxa por disciplina
        taxa_lista = []
        for disciplina, taxa in taxa_por_disciplina:
            taxa_lista.append({
                "disciplina": disciplina,
                "taxa_acerto": taxa
            })

        return ErrosAnaliseResponse(
            total_erros_recentes=len(erros_lista),
            taxa_acerto_por_disciplina=taxa_lista,
            erros_recentes=erros_lista
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao analisar erros: {str(e)}"
        )
    finally:
        db.close()


@router.get("/ranking", response_model=RankingResponse)
async def ranking_usuarios(
    user_id: str = Depends(get_current_user_id)
):
    """
    Ranking dos top 10 usuarios por pontuacao

    Requer autenticacao para visualizar.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)

        # Buscar top 10 perfis
        top_perfis = repos.perfis.get_top_scores(limit=10)

        ranking = []
        for i, perfil in enumerate(top_perfis, start=1):
            # Acessar nome via relacionamento User
            nome = "Usuario"
            if perfil.user:
                nome = perfil.user.nome

            ranking.append(RankingItem(
                posicao=i,
                nome=nome,
                nivel_geral=perfil.nivel_geral.value if perfil.nivel_geral else "INICIANTE",
                pontuacao_global=perfil.pontuacao_global or 0,
                taxa_acerto_global=float(perfil.taxa_acerto_global or 0)
            ))

        return RankingResponse(
            total=len(ranking),
            ranking=ranking
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar ranking: {str(e)}"
        )
    finally:
        db.close()
