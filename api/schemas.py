"""Schemas Pydantic para validação de dados"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuestaoBase(BaseModel):
    """Schema base de uma questão"""
    enunciado: str
    alternativa_a: str
    alternativa_b: str
    alternativa_c: str
    alternativa_d: str
    gabarito: str = Field(..., pattern="^[A-D]$")
    disciplina: str
    fonte: Optional[str] = None
    numero_original: Optional[int] = None


class QuestaoResponse(QuestaoBase):
    """Schema de resposta de uma questão"""
    id: int
    data_importacao: datetime

    class Config:
        from_attributes = True


class QuestaoListResponse(BaseModel):
    """Schema de resposta para lista de questões"""
    total: int
    page: int
    per_page: int
    total_pages: int
    questoes: List[QuestaoResponse]


class SimuladoRequest(BaseModel):
    """Schema para solicitar um simulado"""
    disciplinas: Optional[List[str]] = None
    num_questoes: int = Field(default=10, ge=1, le=100)
    incluir_gabarito: bool = False


class SimuladoResponse(BaseModel):
    """Schema de resposta de um simulado"""
    total_questoes: int
    disciplinas: List[str]
    questoes: List[QuestaoResponse]


class EstatisticasResponse(BaseModel):
    """Schema de resposta de estatísticas"""
    total_questoes: int
    por_disciplina: dict
    por_fonte: dict
    por_gabarito: dict


class HealthResponse(BaseModel):
    """Schema de resposta do health check"""
    status: str
    database: str
    total_questoes: int
    version: str


# ============================================================================
# SCHEMAS DE SESSAO DE ESTUDO
# ============================================================================

class IniciarSessaoRequest(BaseModel):
    """Request para iniciar uma sessao de estudo"""
    disciplina: Optional[str] = Field(None, description="Disciplina especifica (null = todas)")
    num_questoes: int = Field(default=10, ge=1, le=80, description="Numero de questoes")


class QuestaoSessaoItem(BaseModel):
    """Uma questao dentro de uma sessao (SEM gabarito)"""
    id: str
    enunciado: str
    alternativas: dict
    disciplina: str
    topico: Optional[str] = None


class IniciarSessaoResponse(BaseModel):
    """Response ao iniciar sessao"""
    sessao_id: str
    modo: str
    disciplina: Optional[str] = None
    total_questoes: int
    questoes: List[QuestaoSessaoItem]
    inicio: str


class ResponderQuestaoRequest(BaseModel):
    """Request para responder uma questao dentro de uma sessao"""
    questao_id: str = Field(..., description="ID da questao (UUID)")
    alternativa_escolhida: str = Field(..., pattern="^[A-D]$", description="Alternativa escolhida")
    tempo_segundos: int = Field(..., gt=0, le=3600, description="Tempo gasto em segundos")


class SessaoStatsParcias(BaseModel):
    """Estatisticas parciais da sessao em andamento"""
    respondidas: int
    corretas: int
    taxa_acerto_parcial: float


class ResponderQuestaoResponse(BaseModel):
    """Response apos responder uma questao"""
    correto: bool
    alternativa_correta: str
    alternativa_escolhida: str
    explicacao: Optional[str] = None
    pontos_ganhos: int = 0
    sessao_stats: SessaoStatsParcias


class ResumoDisciplinaSessao(BaseModel):
    """Resumo por disciplina ao finalizar sessao"""
    disciplina: str
    total: int
    corretas: int
    taxa_acerto: float


class FinalizarSessaoResponse(BaseModel):
    """Response ao finalizar uma sessao"""
    sessao_id: str
    duracao_minutos: int
    total_questoes: int
    questoes_corretas: int
    taxa_acerto: float
    pontos_totais: int
    por_disciplina: List[ResumoDisciplinaSessao]


class SessaoAtivaResponse(BaseModel):
    """Response para verificar sessao ativa"""
    ativa: bool
    sessao_id: Optional[str] = None
    modo: Optional[str] = None
    inicio: Optional[str] = None
    questoes_respondidas: Optional[int] = None
    questoes_corretas: Optional[int] = None


# ============================================================================
# SCHEMAS DE PROGRESSO E DASHBOARD
# ============================================================================

class ProgressoGeralResponse(BaseModel):
    """Dashboard geral do progresso do usuario"""
    total_questoes_respondidas: int
    total_questoes_corretas: int
    taxa_acerto_global: float
    nivel_geral: str
    pontuacao_global: int
    total_sessoes: int
    tempo_total_estudo_minutos: int
    sequencia_dias_consecutivos: int


class ProgressoDisciplinaItem(BaseModel):
    """Progresso de uma disciplina especifica"""
    disciplina: str
    total_questoes: int
    questoes_corretas: int
    taxa_acerto: float
    nivel_dominio: str
    prioridade_estudo: int


class ProgressoDisciplinasResponse(BaseModel):
    """Lista de progresso por disciplina"""
    total_disciplinas: int
    disciplinas: List[ProgressoDisciplinaItem]


class ErroRecenteItem(BaseModel):
    """Um erro recente do usuario"""
    disciplina: str
    alternativa_escolhida: Optional[str] = None
    alternativa_correta: Optional[str] = None
    tempo_resposta_segundos: Optional[int] = None
    created_at: str


class ErrosAnaliseResponse(BaseModel):
    """Analise de erros do usuario"""
    total_erros_recentes: int
    taxa_acerto_por_disciplina: List[dict]
    erros_recentes: List[ErroRecenteItem]


class RankingItem(BaseModel):
    """Um item do ranking"""
    posicao: int
    nome: str
    nivel_geral: str
    pontuacao_global: int
    taxa_acerto_global: float


class RankingResponse(BaseModel):
    """Ranking dos top usuarios"""
    total: int
    ranking: List[RankingItem]
