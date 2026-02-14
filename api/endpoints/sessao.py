"""
Endpoints de Sessao de Estudo - Iniciar, Responder, Finalizar
"""
from typing import Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from database.connection import DatabaseManager
from database.models import (
    SessaoEstudo, QuestaoBanco, InteracaoQuestao, PerfilJuridico,
    TipoResposta, DificuldadeQuestao
)
from database.repositories import RepositoryFactory
from api.auth import get_current_user_id
from api.schemas import (
    IniciarSessaoRequest,
    QuestaoSessaoItem,
    IniciarSessaoResponse,
    ResponderQuestaoRequest,
    SessaoStatsParcias,
    ResponderQuestaoResponse,
    ResumoDisciplinaSessao,
    FinalizarSessaoResponse,
    SessaoAtivaResponse
)

router = APIRouter(prefix="/api/sessao", tags=["sessao"])


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/iniciar", response_model=IniciarSessaoResponse)
async def iniciar_sessao(
    request: IniciarSessaoRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Inicia uma nova sessao de estudo

    - **disciplina**: Disciplina especifica (null = todas)
    - **num_questoes**: Numero de questoes (1-80, default 10)

    Retorna questoes SEM gabarito para o aluno responder.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        # Verificar se ja existe sessao ativa
        sessao_ativa = repos.sessoes.get_active_session(uid)
        if sessao_ativa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sessao ja em andamento. Finalize a sessao atual antes de iniciar outra."
            )

        # Buscar questoes aleatorias do banco
        questoes = repos.questoes.get_random_questions(
            count=request.num_questoes,
            disciplina=request.disciplina
        )

        if not questoes:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma questao encontrada com os criterios especificados"
            )

        # Coletar disciplinas unicas
        disciplinas_unicas = list(set(q.disciplina for q in questoes))

        # Iniciar sessao de estudo
        sessao = repos.sessoes.start_session(
            user_id=uid,
            modo_estudo="drill",
            estado_emocional_inicio={"confianca": 0.5, "motivacao": 0.7}
        )

        # Guardar IDs das questoes e disciplinas na sessao
        sessao.disciplinas_estudadas = {
            "disciplinas": disciplinas_unicas,
            "questao_ids": [str(q.id) for q in questoes]
        }
        sessao.total_questoes = len(questoes)
        db.commit()

        # Montar resposta SEM gabarito
        questoes_response = []
        for q in questoes:
            questoes_response.append(QuestaoSessaoItem(
                id=str(q.id),
                enunciado=q.enunciado,
                alternativas=q.alternativas if q.alternativas else {},
                disciplina=q.disciplina,
                topico=q.topico if q.topico else None
            ))

        return IniciarSessaoResponse(
            sessao_id=str(sessao.id),
            modo="drill",
            disciplina=request.disciplina,
            total_questoes=len(questoes),
            questoes=questoes_response,
            inicio=sessao.inicio.isoformat()
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar sessao: {str(e)}"
        )
    finally:
        db.close()


@router.post("/responder", response_model=ResponderQuestaoResponse)
async def responder_questao(
    request: ResponderQuestaoRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Responde uma questao dentro de uma sessao ativa

    - **questao_id**: UUID da questao
    - **alternativa_escolhida**: A, B, C ou D
    - **tempo_segundos**: Tempo gasto em segundos

    Retorna se acertou, alternativa correta, pontos e stats parciais.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        # Buscar sessao ativa
        sessao = repos.sessoes.get_active_session(uid)
        if not sessao:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma sessao ativa. Inicie uma sessao primeiro."
            )

        # Buscar questao no banco
        questao_uuid = UUID(request.questao_id)
        questao = repos.questoes.get_by_id(questao_uuid)
        if not questao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Questao nao encontrada"
            )

        # Verificar resposta
        acertou = request.alternativa_escolhida.upper() == questao.alternativa_correta.upper()
        tipo_resposta = TipoResposta.CORRETA if acertou else TipoResposta.INCORRETA

        # Calcular pontos
        pontos = 0
        if acertou:
            pontos = 10
            if request.tempo_segundos <= 30:
                pontos += 5  # Bonus por velocidade
            elif request.tempo_segundos <= 60:
                pontos += 2

        # Criar interacao
        repos.interacoes.create_interaction(
            user_id=uid,
            questao_id=questao.id,
            disciplina=questao.disciplina,
            topico=questao.topico or "Geral",
            tipo_resposta=tipo_resposta,
            alternativa_escolhida=request.alternativa_escolhida.upper(),
            alternativa_correta=questao.alternativa_correta,
            tempo_resposta_segundos=request.tempo_segundos,
            sessao_estudo_id=sessao.id
        )

        # Atualizar contadores da sessao
        sessao.total_questoes = (sessao.total_questoes or 0) + 1
        if acertou:
            sessao.questoes_corretas = (sessao.questoes_corretas or 0) + 1

        # Atualizar estatisticas da questao
        repos.questoes.update_statistics(questao.id, acertou)

        # Atualizar progresso da disciplina
        tempo_minutos = max(1, request.tempo_segundos // 60)
        dificuldade = questao.dificuldade or DificuldadeQuestao.MEDIO
        repos.progressos_disciplina.update_stats(
            user_id=uid,
            disciplina=questao.disciplina,
            acertou=acertou,
            tempo_minutos=tempo_minutos,
            dificuldade=dificuldade
        )

        # Atualizar perfil juridico
        perfil = repos.perfis.get_by_user_id(uid)
        if perfil:
            perfil.total_questoes_respondidas += 1
            if acertou:
                perfil.total_questoes_corretas += 1
            if pontos > 0:
                repos.perfis.increment_score(uid, pontos)
            repos.perfis.update_accuracy_rate(uid)

        db.commit()

        # Calcular stats parciais da sessao
        respondidas = sessao.total_questoes or 0
        corretas = sessao.questoes_corretas or 0
        taxa = round((corretas / respondidas) * 100, 1) if respondidas > 0 else 0.0

        return ResponderQuestaoResponse(
            correto=acertou,
            alternativa_correta=questao.alternativa_correta,
            alternativa_escolhida=request.alternativa_escolhida.upper(),
            explicacao=questao.explicacao_detalhada,
            pontos_ganhos=pontos,
            sessao_stats=SessaoStatsParcias(
                respondidas=respondidas,
                corretas=corretas,
                taxa_acerto_parcial=taxa
            )
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao responder questao: {str(e)}"
        )
    finally:
        db.close()


@router.post("/finalizar", response_model=FinalizarSessaoResponse)
async def finalizar_sessao(
    user_id: str = Depends(get_current_user_id)
):
    """
    Finaliza a sessao de estudo ativa

    Retorna resumo completo: duracao, acertos, taxa, pontos, por disciplina.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        # Buscar sessao ativa
        sessao = repos.sessoes.get_active_session(uid)
        if not sessao:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma sessao ativa para finalizar"
            )

        # Calcular qualidade da sessao
        total = sessao.total_questoes or 0
        corretas = sessao.questoes_corretas or 0
        taxa_acerto = round((corretas / total) * 100, 1) if total > 0 else 0.0
        qualidade = taxa_acerto / 100.0

        # Finalizar sessao
        sessao_finalizada = repos.sessoes.end_session(
            sessao_id=sessao.id,
            estado_emocional_fim={"confianca": min(1.0, 0.5 + qualidade * 0.3)},
            qualidade_sessao=qualidade
        )

        # Atualizar taxa de acerto da sessao
        sessao.taxa_acerto_sessao = taxa_acerto

        # Calcular duracao
        duracao_minutos = sessao_finalizada.duracao_minutos or 0

        # Atualizar tempo total de estudo no perfil
        perfil = repos.perfis.get_by_user_id(uid)
        if perfil:
            perfil.total_tempo_estudo_minutos += max(1, duracao_minutos)

        # Calcular pontos totais (baseado em interacoes da sessao)
        pontos_totais = corretas * 10  # Simplificado

        # Buscar resumo por disciplina da sessao
        interacoes = db.query(InteracaoQuestao).filter(
            InteracaoQuestao.sessao_estudo_id == sessao.id
        ).all()

        # Agrupar por disciplina
        por_disc = {}
        for inter in interacoes:
            disc = inter.disciplina
            if disc not in por_disc:
                por_disc[disc] = {"total": 0, "corretas": 0}
            por_disc[disc]["total"] += 1
            if inter.tipo_resposta == TipoResposta.CORRETA:
                por_disc[disc]["corretas"] += 1

        resumo_disciplinas = []
        for disc, dados in por_disc.items():
            taxa_disc = round((dados["corretas"] / dados["total"]) * 100, 1) if dados["total"] > 0 else 0.0
            resumo_disciplinas.append(ResumoDisciplinaSessao(
                disciplina=disc,
                total=dados["total"],
                corretas=dados["corretas"],
                taxa_acerto=taxa_disc
            ))

        db.commit()

        return FinalizarSessaoResponse(
            sessao_id=str(sessao.id),
            duracao_minutos=duracao_minutos,
            total_questoes=total,
            questoes_corretas=corretas,
            taxa_acerto=taxa_acerto,
            pontos_totais=pontos_totais,
            por_disciplina=resumo_disciplinas
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao finalizar sessao: {str(e)}"
        )
    finally:
        db.close()


@router.get("/ativa", response_model=SessaoAtivaResponse)
async def verificar_sessao_ativa(
    user_id: str = Depends(get_current_user_id)
):
    """
    Verifica se existe uma sessao de estudo ativa

    Retorna dados da sessao ativa ou indica que nao ha sessao.
    """
    db_manager = DatabaseManager()
    Session = db_manager.get_session_factory()
    db = Session()

    try:
        repos = RepositoryFactory(db)
        uid = UUID(user_id)

        sessao = repos.sessoes.get_active_session(uid)

        if not sessao:
            return SessaoAtivaResponse(ativa=False)

        return SessaoAtivaResponse(
            ativa=True,
            sessao_id=str(sessao.id),
            modo=sessao.modo_estudo,
            inicio=sessao.inicio.isoformat() if sessao.inicio else None,
            questoes_respondidas=sessao.total_questoes or 0,
            questoes_corretas=sessao.questoes_corretas or 0
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar sessao: {str(e)}"
        )
    finally:
        db.close()
