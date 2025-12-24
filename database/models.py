"""
JURIS_IA_CORE_V1 - Modelos SQLAlchemy do Banco de Dados
=======================================================

Modelos ORM que representam as entidades do banco de dados PostgreSQL.
Baseado no schema.sql e na arquitetura de dados definida nas 5 etapas.

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 1.0.0
"""

from datetime import datetime
from typing import Optional, Dict, Any
import enum
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, ForeignKey,
    Enum, DECIMAL, Text, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class UserStatus(str, enum.Enum):
    """Status do usuário no sistema (LGPD-aware)"""
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    INATIVO_LONGO_PRAZO = "INATIVO_LONGO_PRAZO"
    EXCLUSAO_SOLICITADA = "EXCLUSAO_SOLICITADA"
    ANONIMIZADO = "ANONIMIZADO"
    APROVADO_OAB = "APROVADO_OAB"


class NivelDominio(str, enum.Enum):
    """Níveis de domínio jurídico do estudante"""
    INICIANTE = "INICIANTE"
    BASICO = "BASICO"
    INTERMEDIARIO = "INTERMEDIARIO"
    AVANCADO = "AVANCADO"
    EXPERT = "EXPERT"


class TipoResposta(str, enum.Enum):
    """Tipo de resposta dada pelo estudante"""
    CORRETA = "CORRETA"
    INCORRETA = "INCORRETA"
    ANULADA = "ANULADA"
    NAO_RESPONDIDA = "NAO_RESPONDIDA"


class TipoErro(str, enum.Enum):
    """28 tipos de erros jurídicos classificados"""
    # ERRO_CONCEITUAL (42%)
    CONCEITO_NAO_COMPREENDIDO = "CONCEITO_NAO_COMPREENDIDO"
    APLICACAO_INCORRETA_CONCEITO = "APLICACAO_INCORRETA_CONCEITO"
    CONFUSAO_DEFINICOES_SIMILARES = "CONFUSAO_DEFINICOES_SIMILARES"
    FALHA_LOGICA_JURIDICA = "FALHA_LOGICA_JURIDICA"
    DECOREBA_SEM_ENTENDIMENTO = "DECOREBA_SEM_ENTENDIMENTO"

    # ERRO_INTERPRETACAO (23%)
    INTERPRETACAO_LITERAL_EQUIVOCADA = "INTERPRETACAO_LITERAL_EQUIVOCADA"
    NAO_IDENTIFICACAO_EXCECAO = "NAO_IDENTIFICACAO_EXCECAO"
    INVERSAO_REGRA_EXCECAO = "INVERSAO_REGRA_EXCECAO"
    CONTEXTO_MAL_INTERPRETADO = "CONTEXTO_MAL_INTERPRETADO"

    # CONFUSAO_INSTITUTOS (18%)
    CONFUSAO_INSTITUTOS_AFINS = "CONFUSAO_INSTITUTOS_AFINS"
    CONFUSAO_COMPETENCIAS = "CONFUSAO_COMPETENCIAS"
    CONFUSAO_PRAZOS_SIMILARES = "CONFUSAO_PRAZOS_SIMILARES"
    CONFUSAO_PROCEDIMENTOS = "CONFUSAO_PROCEDIMENTOS"

    # ERRO_LEITURA_ATENCAO (12%)
    PRESSA_DESATENCAO = "PRESSA_DESATENCAO"
    NAO_LEITURA_COMPLETA_ENUNCIADO = "NAO_LEITURA_COMPLETA_ENUNCIADO"
    PALAVRA_CHAVE_NAO_IDENTIFICADA = "PALAVRA_CHAVE_NAO_IDENTIFICADA"
    DUPLA_NEGATIVA_NAO_PERCEBIDA = "DUPLA_NEGATIVA_NAO_PERCEBIDA"

    # FALTA_BASE_JURIDICA (8%)
    TOPICO_DESCONHECIDO = "TOPICO_DESCONHECIDO"
    LEGISLACAO_DESCONHECIDA = "LEGISLACAO_DESCONHECIDA"
    JURISPRUDENCIA_DESATUALIZADA = "JURISPRUDENCIA_DESATUALIZADA"

    # ERRO_ESTRATEGICO_2FASE (5%)
    ESTRUTURA_PECA_INCORRETA = "ESTRUTURA_PECA_INCORRETA"
    FUNDAMENTACAO_INSUFICIENTE = "FUNDAMENTACAO_INSUFICIENTE"
    TESE_INADEQUADA = "TESE_INADEQUADA"
    ERRO_FORMAL_REDACAO = "ERRO_FORMAL_REDACAO"

    # ERRO_TRAP (4%)
    TRAP_ALTERNATIVA_PLAUSIVEL = "TRAP_ALTERNATIVA_PLAUSIVEL"
    TRAP_INVERSAO_SUTIL = "TRAP_INVERSAO_SUTIL"
    TRAP_EXCECAO_RARA = "TRAP_EXCECAO_RARA"
    TRAP_ATUALIZACAO_RECENTE = "TRAP_ATUALIZACAO_RECENTE"


class DificuldadeQuestao(str, enum.Enum):
    """Dificuldade da questão"""
    FACIL = "FACIL"
    MEDIO = "MEDIO"
    DIFICIL = "DIFICIL"
    MUITO_DIFICIL = "MUITO_DIFICIL"


class TipoTriggerSnapshot(str, enum.Enum):
    """Tipos de triggers para geração de snapshots"""
    FIM_SESSAO = "FIM_SESSAO"
    FIM_SIMULADO = "FIM_SIMULADO"
    MUDANCA_NIVEL = "MUDANCA_NIVEL"
    MILESTONE_QUESTOES = "MILESTONE_QUESTOES"
    SNAPSHOT_SEMANAL = "SNAPSHOT_SEMANAL"
    PRE_PROVA_REAL = "PRE_PROVA_REAL"
    POS_PROVA_REAL = "POS_PROVA_REAL"
    REGRESSAO_DETECTADA = "REGRESSAO_DETECTADA"
    BREAKTHROUGH_DETECTADO = "BREAKTHROUGH_DETECTADO"
    MUDANCA_COMPORTAMENTAL = "MUDANCA_COMPORTAMENTAL"
    RISCO_ALTO_EVASAO = "RISCO_ALTO_EVASAO"


class TipoConsentimento(str, enum.Enum):
    """Tipos de consentimento LGPD"""
    DADOS_CADASTRAIS = "DADOS_CADASTRAIS"
    DADOS_DESEMPENHO = "DADOS_DESEMPENHO"
    DADOS_EMOCIONAIS = "DADOS_EMOCIONAIS"
    COMUNICACAO_MARKETING = "COMUNICACAO_MARKETING"
    COMPARTILHAMENTO_PESQUISA = "COMPARTILHAMENTO_PESQUISA"


# ============================================================================
# ENTIDADES PRINCIPAIS
# ============================================================================

class User(Base):
    """Entidade de usuário - Dados cadastrais básicos"""
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)  # Hash da senha para autenticação
    cpf = Column(String(14), unique=True, index=True)
    telefone = Column(String(20))
    data_nascimento = Column(DateTime)
    estado_uf = Column(String(2))
    cidade = Column(String(100))
    status = Column(Enum(UserStatus), default=UserStatus.ATIVO, nullable=False, index=True)
    data_ultimo_acesso = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    perfil_juridico = relationship("PerfilJuridico", back_populates="user", uselist=False, cascade="all, delete-orphan")
    progressos_disciplina = relationship("ProgressoDisciplina", back_populates="user", cascade="all, delete-orphan")
    progressos_topico = relationship("ProgressoTopico", back_populates="user", cascade="all, delete-orphan")
    sessoes_estudo = relationship("SessaoEstudo", back_populates="user", cascade="all, delete-orphan")
    interacoes_questao = relationship("InteracaoQuestao", back_populates="user", cascade="all, delete-orphan")
    analises_erro = relationship("AnaliseErro", back_populates="user", cascade="all, delete-orphan")
    praticas_peca = relationship("PraticaPeca", back_populates="user", cascade="all, delete-orphan")
    revisoes_agendadas = relationship("RevisaoAgendada", back_populates="user", cascade="all, delete-orphan")
    snapshots_cognitivos = relationship("SnapshotCognitivo", back_populates="user", cascade="all, delete-orphan")
    consentimentos = relationship("Consentimento", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, status={self.status})>"


class PerfilJuridico(Base):
    """Perfil Cognitivo Jurídico - Core do sistema (8 dimensões)"""
    __tablename__ = 'perfil_juridico'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)

    # Dimensão 1: Nível Geral
    nivel_geral = Column(Enum(NivelDominio), default=NivelDominio.INICIANTE, nullable=False)

    # Dimensão 2: Pontuação Global (gamificação)
    pontuacao_global = Column(Integer, default=0, nullable=False)

    # Dimensão 3: Taxa de Acerto Global
    taxa_acerto_global = Column(DECIMAL(5, 2), default=0.0, nullable=False)

    # Dimensão 4: Estado Cognitivo-Emocional (JSONB)
    estado_emocional = Column(
        JSONB,
        default={"confianca": 0.50, "stress": 0.50, "motivacao": 0.70, "fadiga": 0.20},
        nullable=False
    )

    # Dimensão 5: Maturidade Jurídica (JSONB)
    maturidade_juridica = Column(
        JSONB,
        default={
            "pensamento_sistemico": 0.3,
            "capacidade_abstrair": 0.3,
            "dominio_terminologia": 0.4,
            "raciocinio_analogico": 0.3,
            "interpretacao_legal": 0.3
        },
        nullable=False
    )

    # Dimensão 6: Padrões de Aprendizagem (JSONB)
    padroes_aprendizagem = Column(
        JSONB,
        default={
            "estilo_aprendizagem": "MISTO",
            "velocidade_leitura": "MEDIA",
            "preferencia_explicacao": ["DIDATICA", "PRATICA"],
            "melhor_horario": None,
            "sessao_ideal_minutos": 60
        },
        nullable=False
    )

    # Dimensão 7: Riscos e Alertas (JSONB)
    riscos = Column(
        JSONB,
        default={
            "risco_evasao": 0.1,
            "risco_burnout": 0.1,
            "dias_seguidos_estudo": 0,
            "ultima_quebra_streak": None
        },
        nullable=False
    )

    # Dimensão 8: Metas e Metacognição (JSONB)
    metas = Column(
        JSONB,
        default={
            "data_prova_alvo": None,
            "ritmo_necessario_questoes_dia": 0,
            "ritmo_real_questoes_dia": 0,
            "topicos_prioritarios": [],
            "objetivo_pontuacao": 700
        },
        nullable=False
    )

    # Campos de suporte
    total_questoes_respondidas = Column(Integer, default=0, nullable=False)
    total_questoes_corretas = Column(Integer, default=0, nullable=False)
    total_tempo_estudo_minutos = Column(Integer, default=0, nullable=False)
    sequencia_dias_consecutivos = Column(Integer, default=0, nullable=False)
    data_ultima_atualizacao_perfil = Column(DateTime, server_default=func.now())

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="perfil_juridico")

    # Constraints
    __table_args__ = (
        CheckConstraint('pontuacao_global >= 0 AND pontuacao_global <= 1000', name='check_pontuacao_range'),
        CheckConstraint('taxa_acerto_global >= 0 AND taxa_acerto_global <= 100', name='check_taxa_acerto_range'),
        Index('idx_perfil_user', 'user_id'),
        Index('idx_perfil_nivel', 'nivel_geral'),
        Index('idx_perfil_estado_emocional_gin', 'estado_emocional', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<PerfilJuridico(user_id={self.user_id}, nivel={self.nivel_geral}, pontos={self.pontuacao_global})>"


class ProgressoDisciplina(Base):
    """Progresso do estudante por disciplina"""
    __tablename__ = 'progresso_disciplina'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    disciplina = Column(String(100), nullable=False)

    nivel_dominio = Column(Enum(NivelDominio), default=NivelDominio.INICIANTE, nullable=False)
    taxa_acerto = Column(DECIMAL(5, 2), default=0.0, nullable=False)
    total_questoes = Column(Integer, default=0, nullable=False)
    questoes_corretas = Column(Integer, default=0, nullable=False)
    tempo_total_minutos = Column(Integer, default=0, nullable=False)

    peso_prova_oab = Column(DECIMAL(4, 2), default=1.0)
    prioridade_estudo = Column(Integer, default=5)

    distribuicao_dificuldade = Column(JSONB, default={
        "FACIL": {"total": 0, "acertos": 0},
        "MEDIO": {"total": 0, "acertos": 0},
        "DIFICIL": {"total": 0, "acertos": 0},
        "MUITO_DIFICIL": {"total": 0, "acertos": 0}
    })

    ultima_questao_respondida = Column(DateTime)
    proximo_revisao_sugerida = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="progressos_disciplina")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'disciplina', name='uq_user_disciplina'),
        Index('idx_progresso_disc_user', 'user_id'),
        Index('idx_progresso_disc_user_disciplina', 'user_id', 'disciplina'),
        Index('idx_progresso_disc_nivel', 'nivel_dominio'),
    )

    def __repr__(self):
        return f"<ProgressoDisciplina(user_id={self.user_id}, disciplina={self.disciplina}, nivel={self.nivel_dominio})>"


class ProgressoTopico(Base):
    """Progresso granular por tópico (subtema de disciplina)"""
    __tablename__ = 'progresso_topico'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    disciplina = Column(String(100), nullable=False)
    topico = Column(String(200), nullable=False)

    nivel_dominio = Column(Enum(NivelDominio), default=NivelDominio.INICIANTE, nullable=False)
    taxa_acerto = Column(DECIMAL(5, 2), default=0.0, nullable=False)
    total_questoes = Column(Integer, default=0, nullable=False)
    questoes_corretas = Column(Integer, default=0, nullable=False)

    fator_retencao = Column(DECIMAL(4, 3), default=0.5)
    intervalo_revisao_dias = Column(Integer, default=1)
    numero_revisoes = Column(Integer, default=0)

    erros_recorrentes = Column(JSONB, default=[])
    conceitos_criticos = Column(JSONB, default=[])

    ultima_interacao = Column(DateTime)
    proxima_revisao_calculada = Column(DateTime)

    bloqueado_ate = Column(DateTime)
    motivo_bloqueio = Column(Text)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="progressos_topico")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'disciplina', 'topico', name='uq_user_disciplina_topico'),
        Index('idx_progresso_top_user', 'user_id'),
        Index('idx_progresso_top_user_disciplina', 'user_id', 'disciplina'),
        Index('idx_progresso_top_proxima_revisao', 'proxima_revisao_calculada'),
    )

    def __repr__(self):
        return f"<ProgressoTopico(user_id={self.user_id}, topico={self.topico}, nivel={self.nivel_dominio})>"


class SessaoEstudo(Base):
    """Sessão de estudo do usuário"""
    __tablename__ = 'sessao_estudo'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    inicio = Column(DateTime, nullable=False, server_default=func.now())
    fim = Column(DateTime)
    duracao_minutos = Column(Integer)

    modo_estudo = Column(String(50))
    disciplinas_estudadas = Column(JSONB, default=[])

    total_questoes = Column(Integer, default=0)
    questoes_corretas = Column(Integer, default=0)
    taxa_acerto_sessao = Column(DECIMAL(5, 2))

    estado_emocional_inicio = Column(JSONB)
    estado_emocional_fim = Column(JSONB)

    qualidade_sessao = Column(DECIMAL(3, 2))
    interrompida = Column(Boolean, default=False)
    motivo_interrupcao = Column(Text)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="sessoes_estudo")

    # Constraints
    __table_args__ = (
        Index('idx_sessao_user', 'user_id'),
        Index('idx_sessao_user_inicio', 'user_id', 'inicio'),
    )

    def __repr__(self):
        return f"<SessaoEstudo(user_id={self.user_id}, inicio={self.inicio}, duracao={self.duracao_minutos}min)>"


class InteracaoQuestao(Base):
    """Interação do usuário com questão - ENTIDADE MAIS IMPORTANTE"""
    __tablename__ = 'interacao_questao'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    questao_id = Column(UUID(as_uuid=True), ForeignKey('questoes_banco.id'), nullable=False, index=True)
    sessao_estudo_id = Column(UUID(as_uuid=True), ForeignKey('sessao_estudo.id', ondelete='SET NULL'))

    disciplina = Column(String(100), nullable=False, index=True)
    topico = Column(String(200))
    tipo_resposta = Column(Enum(TipoResposta), nullable=False)

    alternativa_escolhida = Column(String(1))
    alternativa_correta = Column(String(1))
    tempo_resposta_segundos = Column(Integer)

    nivel_confianca = Column(DECIMAL(3, 2))
    marcada_revisao = Column(Boolean, default=False)
    comentario_estudante = Column(Text)

    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="interacoes_questao")
    questao = relationship("QuestaoBanco", back_populates="interacoes")
    sessao = relationship("SessaoEstudo")
    analise_erro = relationship("AnaliseErro", back_populates="interacao", uselist=False, cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        Index('idx_interacao_user', 'user_id'),
        Index('idx_interacao_user_disciplina', 'user_id', 'disciplina'),
        Index('idx_interacao_user_created', 'user_id', 'created_at'),
        Index('idx_interacao_questao', 'questao_id'),
        Index('idx_interacao_tipo_resposta', 'tipo_resposta'),
    )

    def __repr__(self):
        return f"<InteracaoQuestao(user_id={self.user_id}, tipo={self.tipo_resposta}, created={self.created_at})>"


class AnaliseErro(Base):
    """Análise profunda de erro cometido pelo estudante"""
    __tablename__ = 'analise_erro'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    interacao_id = Column(UUID(as_uuid=True), ForeignKey('interacao_questao.id', ondelete='CASCADE'), nullable=False, unique=True)

    tipo_erro = Column(Enum(TipoErro), nullable=False, index=True)
    categoria_erro = Column(String(50), nullable=False)
    nivel_gravidade = Column(Integer, default=5)

    diagnostico_ia = Column(Text)
    conceitos_faltantes = Column(JSONB, default=[])
    intervencao_sugerida = Column(JSONB)

    ja_corrigido = Column(Boolean, default=False)
    data_correcao = Column(DateTime)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="analises_erro")
    interacao = relationship("InteracaoQuestao", back_populates="analise_erro")

    # Constraints
    __table_args__ = (
        Index('idx_analise_user', 'user_id'),
        Index('idx_analise_tipo_erro', 'tipo_erro'),
        Index('idx_analise_user_tipo', 'user_id', 'tipo_erro'),
        CheckConstraint('nivel_gravidade >= 1 AND nivel_gravidade <= 10', name='check_gravidade_range'),
    )

    def __repr__(self):
        return f"<AnaliseErro(user_id={self.user_id}, tipo={self.tipo_erro}, gravidade={self.nivel_gravidade})>"


class PraticaPeca(Base):
    """Prática de peças processuais (2ª Fase OAB)"""
    __tablename__ = 'pratica_peca'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    tipo_peca = Column(String(100), nullable=False)
    enunciado_caso = Column(Text, nullable=False)
    texto_produzido = Column(Text, nullable=False)

    nota_estrutura = Column(DECIMAL(4, 2))
    nota_fundamentacao = Column(DECIMAL(4, 2))
    nota_adequacao_tese = Column(DECIMAL(4, 2))
    nota_formal = Column(DECIMAL(4, 2))
    nota_final = Column(DECIMAL(5, 2))

    tempo_elaboracao_minutos = Column(Integer)
    numero_palavras = Column(Integer)

    feedback_ia = Column(JSONB)
    aprovado = Column(Boolean)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="praticas_peca")
    erros_peca = relationship("ErroPeca", back_populates="pratica", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        Index('idx_pratica_user', 'user_id'),
        Index('idx_pratica_tipo', 'tipo_peca'),
    )

    def __repr__(self):
        return f"<PraticaPeca(user_id={self.user_id}, tipo={self.tipo_peca}, nota={self.nota_final})>"


class ErroPeca(Base):
    """Erros identificados em peças processuais"""
    __tablename__ = 'erro_peca'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pratica_peca_id = Column(UUID(as_uuid=True), ForeignKey('pratica_peca.id', ondelete='CASCADE'), nullable=False, index=True)

    categoria = Column(String(50), nullable=False)
    tipo_especifico = Column(String(100))
    descricao = Column(Text, nullable=False)
    localizacao_texto = Column(String(200))

    gravidade = Column(Integer, default=5)
    sugestao_correcao = Column(Text)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    pratica = relationship("PraticaPeca", back_populates="erros_peca")

    def __repr__(self):
        return f"<ErroPeca(pratica_id={self.pratica_peca_id}, categoria={self.categoria})>"


class RevisaoAgendada(Base):
    """Revisões agendadas via repetição espaçada"""
    __tablename__ = 'revisao_agendada'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    disciplina = Column(String(100), nullable=False)
    topico = Column(String(200), nullable=False)
    questao_id = Column(UUID(as_uuid=True), ForeignKey('questoes_banco.id'))

    data_agendada = Column(DateTime, nullable=False, index=True)
    intervalo_dias = Column(Integer, nullable=False)
    numero_revisao = Column(Integer, default=1)

    concluida = Column(Boolean, default=False)
    data_conclusao = Column(DateTime)
    resultado_revisao = Column(Enum(TipoResposta))

    fator_facilidade = Column(DECIMAL(4, 3), default=0.5)
    proximo_intervalo_calculado = Column(Integer)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="revisoes_agendadas")
    questao = relationship("QuestaoBanco")

    # Constraints
    __table_args__ = (
        Index('idx_revisao_user', 'user_id'),
        Index('idx_revisao_data_agendada', 'data_agendada'),
        Index('idx_revisao_user_pendentes', 'user_id', 'concluida', 'data_agendada'),
    )

    def __repr__(self):
        return f"<RevisaoAgendada(user_id={self.user_id}, topico={self.topico}, data={self.data_agendada})>"


class SnapshotCognitivo(Base):
    """Snapshots temporais do estado cognitivo do estudante"""
    __tablename__ = 'snapshot_cognitivo'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    momento = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    tipo_trigger = Column(Enum(TipoTriggerSnapshot), nullable=False)

    # 6 blocos JSONB
    perfil_completo = Column(JSONB, nullable=False)
    desempenho = Column(JSONB, nullable=False)
    padroes_erro = Column(JSONB, nullable=False)
    estado_memoria = Column(JSONB, nullable=False)
    predicao = Column(JSONB, nullable=False)
    contexto_momento = Column(JSONB, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="snapshots_cognitivos")

    # Constraints
    __table_args__ = (
        Index('idx_snapshot_user', 'user_id'),
        Index('idx_snapshot_user_momento', 'user_id', 'momento', postgresql_ops={'momento': 'DESC'}),
        Index('idx_snapshot_tipo_trigger', 'tipo_trigger'),
        Index('idx_snapshot_perfil_gin', 'perfil_completo', postgresql_using='gin'),
        Index('idx_snapshot_desempenho_gin', 'desempenho', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<SnapshotCognitivo(user_id={self.user_id}, momento={self.momento}, trigger={self.tipo_trigger})>"


class MetricasTemporal(Base):
    """Métricas pré-calculadas para dashboards"""
    __tablename__ = 'metricas_temporais'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), index=True)

    periodo = Column(String(20), nullable=False)
    data_referencia = Column(DateTime, nullable=False, index=True)

    total_questoes = Column(Integer, default=0)
    taxa_acerto = Column(DECIMAL(5, 2))
    tempo_estudo_minutos = Column(Integer, default=0)

    distribuicao_disciplinas = Column(JSONB)
    distribuicao_erros = Column(JSONB)
    evolucao_nivel = Column(JSONB)

    metricas_adicionais = Column(JSONB)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'periodo', 'data_referencia', name='uq_user_periodo_data'),
        Index('idx_metricas_user', 'user_id'),
        Index('idx_metricas_data', 'data_referencia'),
    )

    def __repr__(self):
        return f"<MetricasTemporal(user_id={self.user_id}, periodo={self.periodo}, data={self.data_referencia})>"


# ============================================================================
# BANCO DE QUESTÕES
# ============================================================================

class QuestaoBanco(Base):
    """Banco de questões OAB"""
    __tablename__ = 'questoes_banco'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    codigo_questao = Column(String(50), unique=True, nullable=False, index=True)
    disciplina = Column(String(100), nullable=False, index=True)
    topico = Column(String(200), nullable=False, index=True)
    subtopico = Column(String(200))

    enunciado = Column(Text, nullable=False)
    alternativas = Column(JSONB, nullable=False)
    alternativa_correta = Column(String(1), nullable=False)

    dificuldade = Column(Enum(DificuldadeQuestao), nullable=False)
    ano_prova = Column(Integer)
    numero_exame = Column(String(20))

    explicacao_detalhada = Column(Text)
    fundamentacao_legal = Column(JSONB)
    tags = Column(JSONB, default=[])

    eh_trap = Column(Boolean, default=False)
    tipo_trap = Column(String(100))

    taxa_acerto_geral = Column(DECIMAL(5, 2))
    total_respostas = Column(Integer, default=0)

    ativa = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    interacoes = relationship("InteracaoQuestao", back_populates="questao")

    # Constraints
    __table_args__ = (
        Index('idx_questao_disciplina', 'disciplina'),
        Index('idx_questao_topico', 'topico'),
        Index('idx_questao_dificuldade', 'dificuldade'),
        Index('idx_questao_tags_gin', 'tags', postgresql_using='gin'),
    )

    def __repr__(self):
        return f"<QuestaoBanco(codigo={self.codigo_questao}, disciplina={self.disciplina})>"


# ============================================================================
# GOVERNANÇA E LGPD
# ============================================================================

class LogSistema(Base):
    """Logs de auditoria do sistema"""
    __tablename__ = 'log_sistema'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), index=True)

    evento = Column(String(100), nullable=False, index=True)
    detalhes = Column(JSONB)
    ip_origem = Column(String(45))
    user_agent = Column(String(500))

    sucesso = Column(Boolean, default=True)
    mensagem_erro = Column(Text)

    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Constraints
    __table_args__ = (
        Index('idx_log_user', 'user_id'),
        Index('idx_log_evento', 'evento'),
        Index('idx_log_timestamp', 'timestamp', postgresql_ops={'timestamp': 'DESC'}),
    )

    def __repr__(self):
        return f"<LogSistema(evento={self.evento}, timestamp={self.timestamp})>"


class Consentimento(Base):
    """Consentimentos LGPD do usuário"""
    __tablename__ = 'consentimentos'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    tipo_consentimento = Column(Enum(TipoConsentimento), nullable=False)
    consentido = Column(Boolean, nullable=False)

    data_consentimento = Column(DateTime, server_default=func.now(), nullable=False)
    data_revogacao = Column(DateTime)

    versao_termos = Column(String(20), nullable=False)
    ip_consentimento = Column(String(45))

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relacionamentos
    user = relationship("User", back_populates="consentimentos")

    # Constraints
    __table_args__ = (
        Index('idx_consentimento_user', 'user_id'),
        Index('idx_consentimento_tipo', 'tipo_consentimento'),
        Index('idx_consentimento_user_tipo', 'user_id', 'tipo_consentimento'),
    )

    def __repr__(self):
        return f"<Consentimento(user_id={self.user_id}, tipo={self.tipo_consentimento}, consentido={self.consentido})>"


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def get_all_models():
    """Retorna todos os modelos SQLAlchemy"""
    return [
        User, PerfilJuridico, ProgressoDisciplina, ProgressoTopico,
        SessaoEstudo, InteracaoQuestao, AnaliseErro, PraticaPeca,
        ErroPeca, RevisaoAgendada, SnapshotCognitivo, MetricasTemporal,
        QuestaoBanco, LogSistema, Consentimento
    ]


def get_model_by_name(name: str):
    """Retorna modelo por nome"""
    models_map = {model.__tablename__: model for model in get_all_models()}
    return models_map.get(name)
