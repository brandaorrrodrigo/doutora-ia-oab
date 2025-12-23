"""
JURIS_IA_CORE_V1 - Camada de Repositórios (Data Access Layer)
==============================================================

Implementa padrão Repository para acesso aos dados.
Cada repositório encapsula a lógica de acesso aos dados de uma entidade específica.

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 1.0.0
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import and_, or_, func, desc, asc, case
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from database.models import (
    User, PerfilJuridico, ProgressoDisciplina, ProgressoTopico,
    SessaoEstudo, InteracaoQuestao, AnaliseErro, PraticaPeca, ErroPeca,
    RevisaoAgendada, SnapshotCognitivo, MetricasTemporal, QuestaoBanco,
    LogSistema, Consentimento,
    UserStatus, NivelDominio, TipoResposta, TipoErro, DificuldadeQuestao,
    TipoTriggerSnapshot, TipoConsentimento
)

logger = logging.getLogger(__name__)


# ============================================================================
# REPOSITÓRIO BASE
# ============================================================================

class BaseRepository:
    """Repositório base com operações CRUD genéricas"""

    def __init__(self, session: Session, model_class):
        self.session = session
        self.model_class = model_class

    def create(self, **kwargs) -> Any:
        """Cria novo registro"""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        logger.debug(f"Criado {self.model_class.__name__}: {instance.id}")
        return instance

    def get_by_id(self, id: UUID) -> Optional[Any]:
        """Busca registro por ID"""
        return self.session.query(self.model_class).filter(
            self.model_class.id == id
        ).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """Retorna todos os registros (com paginação)"""
        return self.session.query(self.model_class).limit(limit).offset(offset).all()

    def update(self, id: UUID, **kwargs) -> Optional[Any]:
        """Atualiza registro existente"""
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                setattr(instance, key, value)
            self.session.flush()
            logger.debug(f"Atualizado {self.model_class.__name__}: {id}")
        return instance

    def delete(self, id: UUID) -> bool:
        """Remove registro"""
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.flush()
            logger.debug(f"Removido {self.model_class.__name__}: {id}")
            return True
        return False

    def count(self) -> int:
        """Conta total de registros"""
        return self.session.query(self.model_class).count()


# ============================================================================
# REPOSITÓRIOS ESPECÍFICOS
# ============================================================================

class UserRepository(BaseRepository):
    """Repositório de usuários"""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email"""
        return self.session.query(User).filter(User.email == email).first()

    def get_by_cpf(self, cpf: str) -> Optional[User]:
        """Busca usuário por CPF"""
        return self.session.query(User).filter(User.cpf == cpf).first()

    def get_active_users(self) -> List[User]:
        """Retorna todos os usuários ativos"""
        return self.session.query(User).filter(User.status == UserStatus.ATIVO).all()

    def update_last_access(self, user_id: UUID) -> None:
        """Atualiza data de último acesso"""
        self.update(user_id, data_ultimo_acesso=datetime.utcnow())

    def get_inactive_users(self, days: int = 180) -> List[User]:
        """Retorna usuários inativos há X dias"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(User).filter(
            User.data_ultimo_acesso < cutoff_date,
            User.status == UserStatus.ATIVO
        ).all()

    def anonymize_user(self, user_id: UUID) -> bool:
        """
        Anonimiza dados do usuário (LGPD)
        Implementa algoritmo de anonimização de 16 passos
        """
        user = self.get_by_id(user_id)
        if not user:
            return False

        # Hash para anonimização
        import hashlib
        hash_base = f"{user_id}{datetime.utcnow().isoformat()}"
        hash_anonimo = hashlib.sha256(hash_base.encode()).hexdigest()[:16]

        # Anonimizar dados
        self.update(
            user_id,
            nome="Usuário Anonimizado",
            email=f"anonimizado_{hash_anonimo}@anonimizado.local",
            cpf=None,
            telefone=None,
            data_nascimento=None,
            status=UserStatus.ANONIMIZADO
        )

        logger.info(f"Usuário {user_id} anonimizado com sucesso")
        return True


class PerfilJuridicoRepository(BaseRepository):
    """Repositório de perfis jurídicos cognitivos"""

    def __init__(self, session: Session):
        super().__init__(session, PerfilJuridico)

    def get_by_user_id(self, user_id: UUID) -> Optional[PerfilJuridico]:
        """Busca perfil por user_id"""
        return self.session.query(PerfilJuridico).filter(
            PerfilJuridico.user_id == user_id
        ).first()

    def create_initial_profile(self, user_id: UUID) -> PerfilJuridico:
        """Cria perfil inicial para novo usuário"""
        return self.create(
            user_id=user_id,
            nivel_geral=NivelDominio.INICIANTE,
            pontuacao_global=0,
            taxa_acerto_global=0.0,
            estado_emocional={
                "confianca": 0.50,
                "stress": 0.50,
                "motivacao": 0.70,
                "fadiga": 0.20
            },
            maturidade_juridica={
                "pensamento_sistemico": 0.3,
                "capacidade_abstrair": 0.3,
                "dominio_terminologia": 0.4,
                "raciocinio_analogico": 0.3,
                "interpretacao_legal": 0.3
            },
            padroes_aprendizagem={
                "estilo_aprendizagem": "MISTO",
                "velocidade_leitura": "MEDIA",
                "preferencia_explicacao": ["DIDATICA", "PRATICA"],
                "melhor_horario": None,
                "sessao_ideal_minutos": 60
            },
            riscos={
                "risco_evasao": 0.1,
                "risco_burnout": 0.1,
                "dias_seguidos_estudo": 0,
                "ultima_quebra_streak": None
            },
            metas={
                "data_prova_alvo": None,
                "ritmo_necessario_questoes_dia": 0,
                "ritmo_real_questoes_dia": 0,
                "topicos_prioritarios": [],
                "objetivo_pontuacao": 700
            }
        )

    def update_emotional_state(
        self,
        user_id: UUID,
        confianca: Optional[float] = None,
        stress: Optional[float] = None,
        motivacao: Optional[float] = None,
        fadiga: Optional[float] = None
    ) -> Optional[PerfilJuridico]:
        """Atualiza estado emocional do perfil"""
        perfil = self.get_by_user_id(user_id)
        if not perfil:
            return None

        estado = perfil.estado_emocional.copy()

        if confianca is not None:
            estado["confianca"] = max(0.0, min(1.0, confianca))
        if stress is not None:
            estado["stress"] = max(0.0, min(1.0, stress))
        if motivacao is not None:
            estado["motivacao"] = max(0.0, min(1.0, motivacao))
        if fadiga is not None:
            estado["fadiga"] = max(0.0, min(1.0, fadiga))

        perfil.estado_emocional = estado
        perfil.data_ultima_atualizacao_perfil = datetime.utcnow()
        self.session.flush()

        return perfil

    def increment_score(self, user_id: UUID, points: int) -> Optional[PerfilJuridico]:
        """Incrementa pontuação global (gamificação)"""
        perfil = self.get_by_user_id(user_id)
        if not perfil:
            return None

        perfil.pontuacao_global = min(1000, perfil.pontuacao_global + points)
        self.session.flush()

        return perfil

    def update_accuracy_rate(self, user_id: UUID) -> Optional[PerfilJuridico]:
        """Recalcula taxa de acerto global baseado em interações"""
        perfil = self.get_by_user_id(user_id)
        if not perfil:
            return None

        if perfil.total_questoes_respondidas > 0:
            taxa = (perfil.total_questoes_corretas / perfil.total_questoes_respondidas) * 100
            perfil.taxa_acerto_global = round(taxa, 2)
            self.session.flush()

        return perfil

    def get_users_by_level(self, nivel: NivelDominio) -> List[PerfilJuridico]:
        """Retorna perfis de determinado nível"""
        return self.session.query(PerfilJuridico).filter(
            PerfilJuridico.nivel_geral == nivel
        ).all()

    def get_top_scores(self, limit: int = 10) -> List[PerfilJuridico]:
        """Retorna top perfis por pontuação (leaderboard)"""
        return self.session.query(PerfilJuridico).order_by(
            desc(PerfilJuridico.pontuacao_global)
        ).limit(limit).all()


class ProgressoDisciplinaRepository(BaseRepository):
    """Repositório de progresso por disciplina"""

    def __init__(self, session: Session):
        super().__init__(session, ProgressoDisciplina)

    def get_by_user_and_disciplina(
        self, user_id: UUID, disciplina: str
    ) -> Optional[ProgressoDisciplina]:
        """Busca progresso específico de uma disciplina"""
        return self.session.query(ProgressoDisciplina).filter(
            ProgressoDisciplina.user_id == user_id,
            ProgressoDisciplina.disciplina == disciplina
        ).first()

    def get_all_by_user(self, user_id: UUID) -> List[ProgressoDisciplina]:
        """Retorna todos os progressos de um usuário"""
        return self.session.query(ProgressoDisciplina).filter(
            ProgressoDisciplina.user_id == user_id
        ).order_by(desc(ProgressoDisciplina.taxa_acerto)).all()

    def get_or_create(
        self, user_id: UUID, disciplina: str
    ) -> ProgressoDisciplina:
        """Busca ou cria progresso de disciplina"""
        progresso = self.get_by_user_and_disciplina(user_id, disciplina)
        if not progresso:
            progresso = self.create(
                user_id=user_id,
                disciplina=disciplina,
                nivel_dominio=NivelDominio.INICIANTE,
                taxa_acerto=0.0,
                total_questoes=0,
                questoes_corretas=0,
                tempo_total_minutos=0
            )
        return progresso

    def update_stats(
        self,
        user_id: UUID,
        disciplina: str,
        acertou: bool,
        tempo_minutos: int,
        dificuldade: DificuldadeQuestao
    ) -> ProgressoDisciplina:
        """Atualiza estatísticas após responder questão"""
        progresso = self.get_or_create(user_id, disciplina)

        # Atualizar totais
        progresso.total_questoes += 1
        if acertou:
            progresso.questoes_corretas += 1

        progresso.tempo_total_minutos += tempo_minutos
        progresso.ultima_questao_respondida = datetime.utcnow()

        # Recalcular taxa de acerto
        progresso.taxa_acerto = round(
            (progresso.questoes_corretas / progresso.total_questoes) * 100, 2
        )

        # Atualizar distribuição por dificuldade
        dist = progresso.distribuicao_dificuldade.copy()
        dif_key = dificuldade.value
        if dif_key not in dist:
            dist[dif_key] = {"total": 0, "acertos": 0}

        dist[dif_key]["total"] += 1
        if acertou:
            dist[dif_key]["acertos"] += 1

        progresso.distribuicao_dificuldade = dist

        self.session.flush()
        return progresso

    def get_weakest_disciplines(
        self, user_id: UUID, limit: int = 3
    ) -> List[ProgressoDisciplina]:
        """Retorna disciplinas com menor taxa de acerto"""
        return self.session.query(ProgressoDisciplina).filter(
            ProgressoDisciplina.user_id == user_id,
            ProgressoDisciplina.total_questoes >= 5  # Mínimo de questões
        ).order_by(asc(ProgressoDisciplina.taxa_acerto)).limit(limit).all()


class ProgressoTopicoRepository(BaseRepository):
    """Repositório de progresso por tópico (granular)"""

    def __init__(self, session: Session):
        super().__init__(session, ProgressoTopico)

    def get_by_user_disciplina_topico(
        self, user_id: UUID, disciplina: str, topico: str
    ) -> Optional[ProgressoTopico]:
        """Busca progresso específico de um tópico"""
        return self.session.query(ProgressoTopico).filter(
            ProgressoTopico.user_id == user_id,
            ProgressoTopico.disciplina == disciplina,
            ProgressoTopico.topico == topico
        ).first()

    def get_or_create(
        self, user_id: UUID, disciplina: str, topico: str
    ) -> ProgressoTopico:
        """Busca ou cria progresso de tópico"""
        progresso = self.get_by_user_disciplina_topico(user_id, disciplina, topico)
        if not progresso:
            progresso = self.create(
                user_id=user_id,
                disciplina=disciplina,
                topico=topico,
                nivel_dominio=NivelDominio.INICIANTE,
                taxa_acerto=0.0,
                total_questoes=0,
                questoes_corretas=0,
                fator_retencao=0.5,
                intervalo_revisao_dias=1,
                numero_revisoes=0
            )
        return progresso

    def update_after_interaction(
        self,
        user_id: UUID,
        disciplina: str,
        topico: str,
        acertou: bool
    ) -> ProgressoTopico:
        """
        Atualiza progresso de tópico após interação.
        Implementa lógica de repetição espaçada.
        """
        progresso = self.get_or_create(user_id, disciplina, topico)

        # Atualizar estatísticas
        progresso.total_questoes += 1
        if acertou:
            progresso.questoes_corretas += 1

        progresso.ultima_interacao = datetime.utcnow()

        # Recalcular taxa de acerto
        progresso.taxa_acerto = round(
            (progresso.questoes_corretas / progresso.total_questoes) * 100, 2
        )

        # Atualizar fator de retenção (algoritmo SM-2 simplificado)
        if acertou:
            progresso.fator_retencao = min(1.0, progresso.fator_retencao + 0.1)
            progresso.intervalo_revisao_dias = int(
                progresso.intervalo_revisao_dias * (1 + progresso.fator_retencao)
            )
        else:
            progresso.fator_retencao = max(0.3, progresso.fator_retencao - 0.2)
            progresso.intervalo_revisao_dias = 1  # Reset

        progresso.numero_revisoes += 1

        # Calcular próxima revisão
        progresso.proxima_revisao_calculada = datetime.utcnow() + timedelta(
            days=progresso.intervalo_revisao_dias
        )

        self.session.flush()
        return progresso

    def get_topics_due_for_review(
        self, user_id: UUID, limit: int = 10
    ) -> List[ProgressoTopico]:
        """Retorna tópicos que precisam ser revisados"""
        now = datetime.utcnow()
        return self.session.query(ProgressoTopico).filter(
            ProgressoTopico.user_id == user_id,
            ProgressoTopico.proxima_revisao_calculada <= now,
            or_(
                ProgressoTopico.bloqueado_ate == None,
                ProgressoTopico.bloqueado_ate <= now
            )
        ).order_by(asc(ProgressoTopico.proxima_revisao_calculada)).limit(limit).all()


class InteracaoQuestaoRepository(BaseRepository):
    """Repositório de interações com questões - MAIS IMPORTANTE"""

    def __init__(self, session: Session):
        super().__init__(session, InteracaoQuestao)

    def create_interaction(
        self,
        user_id: UUID,
        questao_id: UUID,
        disciplina: str,
        topico: str,
        tipo_resposta: TipoResposta,
        alternativa_escolhida: Optional[str] = None,
        alternativa_correta: Optional[str] = None,
        tempo_resposta_segundos: Optional[int] = None,
        nivel_confianca: Optional[float] = None,
        sessao_estudo_id: Optional[UUID] = None
    ) -> InteracaoQuestao:
        """Cria nova interação com questão"""
        return self.create(
            user_id=user_id,
            questao_id=questao_id,
            disciplina=disciplina,
            topico=topico,
            tipo_resposta=tipo_resposta,
            alternativa_escolhida=alternativa_escolhida,
            alternativa_correta=alternativa_correta,
            tempo_resposta_segundos=tempo_resposta_segundos,
            nivel_confianca=nivel_confianca,
            sessao_estudo_id=sessao_estudo_id
        )

    def get_user_interactions(
        self,
        user_id: UUID,
        limit: int = 100,
        disciplina: Optional[str] = None
    ) -> List[InteracaoQuestao]:
        """Retorna interações do usuário"""
        query = self.session.query(InteracaoQuestao).filter(
            InteracaoQuestao.user_id == user_id
        )

        if disciplina:
            query = query.filter(InteracaoQuestao.disciplina == disciplina)

        return query.order_by(desc(InteracaoQuestao.created_at)).limit(limit).all()

    def get_recent_errors(
        self, user_id: UUID, days: int = 7, limit: int = 20
    ) -> List[InteracaoQuestao]:
        """Retorna erros recentes do usuário"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(InteracaoQuestao).filter(
            InteracaoQuestao.user_id == user_id,
            InteracaoQuestao.tipo_resposta == TipoResposta.INCORRETA,
            InteracaoQuestao.created_at >= cutoff_date
        ).order_by(desc(InteracaoQuestao.created_at)).limit(limit).all()

    def get_accuracy_by_discipline(self, user_id: UUID) -> List[Tuple[str, float]]:
        """Retorna taxa de acerto por disciplina"""
        results = self.session.query(
            InteracaoQuestao.disciplina,
            func.count(InteracaoQuestao.id).label('total'),
            func.sum(
                case((InteracaoQuestao.tipo_resposta == TipoResposta.CORRETA, 1), else_=0)
            ).label('corretas')
        ).filter(
            InteracaoQuestao.user_id == user_id
        ).group_by(InteracaoQuestao.disciplina).all()

        return [
            (disciplina, round((corretas / total) * 100, 2) if total > 0 else 0.0)
            for disciplina, total, corretas in results
        ]

    def count_interactions(
        self,
        user_id: UUID,
        tipo_resposta: Optional[TipoResposta] = None,
        disciplina: Optional[str] = None
    ) -> int:
        """Conta interações com filtros opcionais"""
        query = self.session.query(InteracaoQuestao).filter(
            InteracaoQuestao.user_id == user_id
        )

        if tipo_resposta:
            query = query.filter(InteracaoQuestao.tipo_resposta == tipo_resposta)

        if disciplina:
            query = query.filter(InteracaoQuestao.disciplina == disciplina)

        return query.count()


class AnaliseErroRepository(BaseRepository):
    """Repositório de análises de erros"""

    def __init__(self, session: Session):
        super().__init__(session, AnaliseErro)

    def create_from_interaction(
        self,
        interacao: InteracaoQuestao,
        tipo_erro: TipoErro,
        categoria_erro: str,
        nivel_gravidade: int,
        diagnostico_ia: str,
        conceitos_faltantes: List[str],
        intervencao_sugerida: Dict[str, Any]
    ) -> AnaliseErro:
        """Cria análise de erro a partir de interação"""
        return self.create(
            user_id=interacao.user_id,
            interacao_id=interacao.id,
            tipo_erro=tipo_erro,
            categoria_erro=categoria_erro,
            nivel_gravidade=nivel_gravidade,
            diagnostico_ia=diagnostico_ia,
            conceitos_faltantes=conceitos_faltantes,
            intervencao_sugerida=intervencao_sugerida
        )

    def get_user_error_distribution(self, user_id: UUID) -> Dict[str, int]:
        """Retorna distribuição de tipos de erros do usuário"""
        results = self.session.query(
            AnaliseErro.tipo_erro,
            func.count(AnaliseErro.id).label('count')
        ).filter(
            AnaliseErro.user_id == user_id
        ).group_by(AnaliseErro.tipo_erro).all()

        return {tipo_erro.value: count for tipo_erro, count in results}

    def get_uncorrected_errors(
        self, user_id: UUID, limit: int = 10
    ) -> List[AnaliseErro]:
        """Retorna erros ainda não corrigidos"""
        return self.session.query(AnaliseErro).filter(
            AnaliseErro.user_id == user_id,
            AnaliseErro.ja_corrigido == False
        ).order_by(desc(AnaliseErro.nivel_gravidade)).limit(limit).all()

    def mark_as_corrected(self, analise_id: UUID) -> Optional[AnaliseErro]:
        """Marca erro como corrigido"""
        analise = self.get_by_id(analise_id)
        if analise:
            analise.ja_corrigido = True
            analise.data_correcao = datetime.utcnow()
            self.session.flush()
        return analise


class SnapshotCognitivoRepository(BaseRepository):
    """Repositório de snapshots cognitivos"""

    def __init__(self, session: Session):
        super().__init__(session, SnapshotCognitivo)

    def create_snapshot(
        self,
        user_id: UUID,
        tipo_trigger: TipoTriggerSnapshot,
        perfil_completo: Dict[str, Any],
        desempenho: Dict[str, Any],
        padroes_erro: Dict[str, Any],
        estado_memoria: Dict[str, Any],
        predicao: Dict[str, Any],
        contexto_momento: Dict[str, Any]
    ) -> SnapshotCognitivo:
        """Cria novo snapshot cognitivo"""
        return self.create(
            user_id=user_id,
            tipo_trigger=tipo_trigger,
            perfil_completo=perfil_completo,
            desempenho=desempenho,
            padroes_erro=padroes_erro,
            estado_memoria=estado_memoria,
            predicao=predicao,
            contexto_momento=contexto_momento
        )

    def get_user_snapshots(
        self,
        user_id: UUID,
        limit: int = 50,
        tipo_trigger: Optional[TipoTriggerSnapshot] = None
    ) -> List[SnapshotCognitivo]:
        """Retorna snapshots do usuário"""
        query = self.session.query(SnapshotCognitivo).filter(
            SnapshotCognitivo.user_id == user_id
        )

        if tipo_trigger:
            query = query.filter(SnapshotCognitivo.tipo_trigger == tipo_trigger)

        return query.order_by(desc(SnapshotCognitivo.momento)).limit(limit).all()

    def get_temporal_evolution(
        self, user_id: UUID, days: int = 30
    ) -> List[SnapshotCognitivo]:
        """Retorna evolução temporal dos últimos X dias"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(SnapshotCognitivo).filter(
            SnapshotCognitivo.user_id == user_id,
            SnapshotCognitivo.momento >= cutoff_date
        ).order_by(asc(SnapshotCognitivo.momento)).all()

    def get_latest_snapshot(
        self, user_id: UUID, tipo_trigger: Optional[TipoTriggerSnapshot] = None
    ) -> Optional[SnapshotCognitivo]:
        """Retorna snapshot mais recente"""
        query = self.session.query(SnapshotCognitivo).filter(
            SnapshotCognitivo.user_id == user_id
        )

        if tipo_trigger:
            query = query.filter(SnapshotCognitivo.tipo_trigger == tipo_trigger)

        return query.order_by(desc(SnapshotCognitivo.momento)).first()


class QuestaoBancoRepository(BaseRepository):
    """Repositório de banco de questões"""

    def __init__(self, session: Session):
        super().__init__(session, QuestaoBanco)

    def get_by_codigo(self, codigo_questao: str) -> Optional[QuestaoBanco]:
        """Busca questão por código"""
        return self.session.query(QuestaoBanco).filter(
            QuestaoBanco.codigo_questao == codigo_questao
        ).first()

    def get_by_filters(
        self,
        disciplina: Optional[str] = None,
        topico: Optional[str] = None,
        dificuldade: Optional[DificuldadeQuestao] = None,
        apenas_ativas: bool = True,
        limit: int = 50
    ) -> List[QuestaoBanco]:
        """Busca questões com filtros"""
        query = self.session.query(QuestaoBanco)

        if disciplina:
            query = query.filter(QuestaoBanco.disciplina == disciplina)

        if topico:
            query = query.filter(QuestaoBanco.topico == topico)

        if dificuldade:
            query = query.filter(QuestaoBanco.dificuldade == dificuldade)

        if apenas_ativas:
            query = query.filter(QuestaoBanco.ativa == True)

        return query.limit(limit).all()

    def get_random_questions(
        self,
        count: int,
        disciplina: Optional[str] = None,
        dificuldade: Optional[DificuldadeQuestao] = None
    ) -> List[QuestaoBanco]:
        """Retorna questões aleatórias"""
        query = self.session.query(QuestaoBanco).filter(QuestaoBanco.ativa == True)

        if disciplina:
            query = query.filter(QuestaoBanco.disciplina == disciplina)

        if dificuldade:
            query = query.filter(QuestaoBanco.dificuldade == dificuldade)

        return query.order_by(func.random()).limit(count).all()

    def update_statistics(self, questao_id: UUID, acertou: bool) -> Optional[QuestaoBanco]:
        """Atualiza estatísticas globais da questão"""
        questao = self.get_by_id(questao_id)
        if not questao:
            return None

        questao.total_respostas += 1

        # Recalcular taxa de acerto global
        if questao.taxa_acerto_geral is None:
            questao.taxa_acerto_geral = 100.0 if acertou else 0.0
        else:
            # Média móvel
            peso_anterior = min(0.95, questao.total_respostas / (questao.total_respostas + 1))
            peso_novo = 1 - peso_anterior
            novo_valor = 100.0 if acertou else 0.0
            questao.taxa_acerto_geral = round(
                float(questao.taxa_acerto_geral) * peso_anterior + novo_valor * peso_novo,
                2
            )

        self.session.flush()
        return questao


class SessaoEstudoRepository(BaseRepository):
    """Repositório de sessões de estudo"""

    def __init__(self, session: Session):
        super().__init__(session, SessaoEstudo)

    def start_session(
        self,
        user_id: UUID,
        modo_estudo: str,
        estado_emocional_inicio: Dict[str, Any]
    ) -> SessaoEstudo:
        """Inicia nova sessão de estudo"""
        return self.create(
            user_id=user_id,
            inicio=datetime.utcnow(),
            modo_estudo=modo_estudo,
            estado_emocional_inicio=estado_emocional_inicio
        )

    def end_session(
        self,
        sessao_id: UUID,
        estado_emocional_fim: Dict[str, Any],
        qualidade_sessao: float
    ) -> Optional[SessaoEstudo]:
        """Finaliza sessão de estudo"""
        sessao = self.get_by_id(sessao_id)
        if not sessao:
            return None

        sessao.fim = datetime.utcnow()
        sessao.duracao_minutos = int((sessao.fim - sessao.inicio).total_seconds() / 60)
        sessao.estado_emocional_fim = estado_emocional_fim
        sessao.qualidade_sessao = qualidade_sessao

        self.session.flush()
        return sessao

    def get_active_session(self, user_id: UUID) -> Optional[SessaoEstudo]:
        """Retorna sessão ativa do usuário (se houver)"""
        return self.session.query(SessaoEstudo).filter(
            SessaoEstudo.user_id == user_id,
            SessaoEstudo.fim == None
        ).first()


# ============================================================================
# FACTORY PARA REPOSITÓRIOS
# ============================================================================

class RepositoryFactory:
    """Factory para criar repositórios com sessão injetada"""

    def __init__(self, session: Session):
        self.session = session

    @property
    def users(self) -> UserRepository:
        return UserRepository(self.session)

    @property
    def perfis(self) -> PerfilJuridicoRepository:
        return PerfilJuridicoRepository(self.session)

    @property
    def progressos_disciplina(self) -> ProgressoDisciplinaRepository:
        return ProgressoDisciplinaRepository(self.session)

    @property
    def progressos_topico(self) -> ProgressoTopicoRepository:
        return ProgressoTopicoRepository(self.session)

    @property
    def interacoes(self) -> InteracaoQuestaoRepository:
        return InteracaoQuestaoRepository(self.session)

    @property
    def analises_erro(self) -> AnaliseErroRepository:
        return AnaliseErroRepository(self.session)

    @property
    def snapshots(self) -> SnapshotCognitivoRepository:
        return SnapshotCognitivoRepository(self.session)

    @property
    def questoes(self) -> QuestaoBancoRepository:
        return QuestaoBancoRepository(self.session)

    @property
    def sessoes(self) -> SessaoEstudoRepository:
        return SessaoEstudoRepository(self.session)
