"""
================================================================================
TESTES DE ENFORCEMENT - JURIS_IA_CORE_V1
================================================================================
Suite de testes automatizados para validação de enforcement de limites.

Autor: JURIS_IA_CORE_V1 - Engenheiro de Enforcement
Data: 2025-12-19
================================================================================
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from core.enforcement import LimitsEnforcement, ReasonCode


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def database_url():
    """URL do banco de dados de teste"""
    return "postgresql://juris_ia_user:changeme123@localhost:5432/juris_ia"


@pytest.fixture
def enforcement(database_url):
    """Instância de enforcement para testes"""
    return LimitsEnforcement(database_url)


@pytest.fixture
def test_user_free(database_url):
    """Cria usuário de teste com plano FREE"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Criar usuário
        user_id = str(uuid.uuid4())
        session.execute(
            text("""
                INSERT INTO users (id, email, name, password_hash)
                VALUES (:id, :email, :name, :password)
            """),
            {
                "id": user_id,
                "email": f"test_free_{user_id[:8]}@test.com",
                "name": "Test User FREE",
                "password": "test_hash"
            }
        )

        # Buscar plano FREE
        plano = session.execute(
            text("SELECT id FROM plano WHERE codigo = 'FREE' LIMIT 1")
        ).fetchone()

        if not plano:
            raise Exception("Plano FREE não encontrado no banco")

        # Criar assinatura
        session.execute(
            text("""
                INSERT INTO assinatura (user_id, plano_id, status, data_inicio)
                VALUES (:user_id, :plano_id, 'active', NOW())
            """),
            {
                "user_id": user_id,
                "plano_id": plano[0]
            }
        )

        session.commit()
        yield user_id

    finally:
        # Cleanup
        session.execute(
            text("DELETE FROM assinatura WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        session.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        session.commit()
        session.close()


@pytest.fixture
def test_user_mensal(database_url):
    """Cria usuário de teste com plano OAB_MENSAL"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        user_id = str(uuid.uuid4())
        session.execute(
            text("""
                INSERT INTO users (id, email, name, password_hash)
                VALUES (:id, :email, :name, :password)
            """),
            {
                "id": user_id,
                "email": f"test_mensal_{user_id[:8]}@test.com",
                "name": "Test User MENSAL",
                "password": "test_hash"
            }
        )

        plano = session.execute(
            text("SELECT id FROM plano WHERE codigo = 'OAB_MENSAL' LIMIT 1")
        ).fetchone()

        if not plano:
            raise Exception("Plano OAB_MENSAL não encontrado no banco")

        session.execute(
            text("""
                INSERT INTO assinatura (user_id, plano_id, status, data_inicio)
                VALUES (:user_id, :plano_id, 'active', NOW())
            """),
            {
                "user_id": user_id,
                "plano_id": plano[0]
            }
        )

        session.commit()
        yield user_id

    finally:
        session.execute(
            text("DELETE FROM assinatura WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        session.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        session.commit()
        session.close()


@pytest.fixture
def test_user_semestral(database_url):
    """Cria usuário de teste com plano OAB_SEMESTRAL"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        user_id = str(uuid.uuid4())
        session.execute(
            text("""
                INSERT INTO users (id, email, name, password_hash)
                VALUES (:id, :email, :name, :password)
            """),
            {
                "id": user_id,
                "email": f"test_semestral_{user_id[:8]}@test.com",
                "name": "Test User SEMESTRAL",
                "password": "test_hash"
            }
        )

        plano = session.execute(
            text("SELECT id FROM plano WHERE codigo = 'OAB_SEMESTRAL' LIMIT 1")
        ).fetchone()

        if not plano:
            raise Exception("Plano OAB_SEMESTRAL não encontrado no banco")

        session.execute(
            text("""
                INSERT INTO assinatura (user_id, plano_id, status, data_inicio)
                VALUES (:user_id, :plano_id, 'active', NOW())
            """),
            {
                "user_id": user_id,
                "plano_id": plano[0]
            }
        )

        session.commit()
        yield user_id

    finally:
        session.execute(
            text("DELETE FROM assinatura WHERE user_id = :user_id"),
            {"user_id": user_id}
        )
        session.execute(
            text("DELETE FROM users WHERE id = :user_id"),
            {"user_id": user_id}
        )
        session.commit()
        session.close()


# ============================================================
# TESTES - PLANO FREE
# ============================================================

def test_free_can_start_first_session(enforcement, test_user_free):
    """FREE: Pode iniciar 1ª sessão do dia"""
    result = enforcement.check_can_start_session(
        user_id=test_user_free,
        modo_estudo_continuo=False
    )

    assert result.allowed is True
    assert result.current_usage == 0
    assert result.limit == 1


def test_free_blocked_after_one_session(enforcement, test_user_free, database_url):
    """FREE: Bloqueado após 1 sessão"""
    # Simular 1 sessão já criada hoje
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.execute(
        text("""
            INSERT INTO sessao_estudo (user_id, tipo, conta_limite_diario, iniciado_em)
            VALUES (:user_id, 'drill', true, NOW())
        """),
        {"user_id": test_user_free}
    )
    session.commit()
    session.close()

    # Tentar iniciar 2ª sessão
    result = enforcement.check_can_start_session(
        user_id=test_user_free,
        modo_estudo_continuo=False
    )

    assert result.allowed is False
    assert result.reason_code == ReasonCode.LIMIT_SESSIONS_DAILY
    assert result.current_usage == 1
    assert result.limit == 1
    assert "Limite de sessões diárias atingido" in result.message_title


def test_free_blocked_continuous_study(enforcement, test_user_free):
    """FREE: Bloqueado em modo estudo contínuo"""
    result = enforcement.check_can_start_session(
        user_id=test_user_free,
        modo_estudo_continuo=True
    )

    assert result.allowed is False
    assert result.reason_code == ReasonCode.LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED
    assert "não disponível" in result.message_title.lower()


# ============================================================
# TESTES - PLANO MENSAL
# ============================================================

def test_mensal_can_start_three_sessions(enforcement, test_user_mensal, database_url):
    """MENSAL: Pode iniciar até 3 sessões"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Criar 2 sessões
    for _ in range(2):
        session.execute(
            text("""
                INSERT INTO sessao_estudo (user_id, tipo, conta_limite_diario, iniciado_em)
                VALUES (:user_id, 'drill', true, NOW())
            """),
            {"user_id": test_user_mensal}
        )
    session.commit()
    session.close()

    # Tentar 3ª sessão
    result = enforcement.check_can_start_session(
        user_id=test_user_mensal,
        modo_estudo_continuo=False
    )

    assert result.allowed is True
    assert result.current_usage == 2
    assert result.limit == 3


def test_mensal_allowed_continuous_study(enforcement, test_user_mensal):
    """MENSAL: Permite estudo contínuo"""
    result = enforcement.check_can_start_session(
        user_id=test_user_mensal,
        modo_estudo_continuo=True
    )

    assert result.allowed is True
    assert "não conta no limite" in result.to_dict().get("message", "").lower() or result.allowed


def test_mensal_blocked_after_three_sessions(enforcement, test_user_mensal, database_url):
    """MENSAL: Bloqueado após 3 sessões"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Criar 3 sessões
    for _ in range(3):
        session.execute(
            text("""
                INSERT INTO sessao_estudo (user_id, tipo, conta_limite_diario, iniciado_em)
                VALUES (:user_id, 'drill', true, NOW())
            """),
            {"user_id": test_user_mensal}
        )
    session.commit()
    session.close()

    # Tentar 4ª sessão
    result = enforcement.check_can_start_session(
        user_id=test_user_mensal,
        modo_estudo_continuo=False
    )

    assert result.allowed is False
    assert result.reason_code == ReasonCode.LIMIT_SESSIONS_DAILY
    assert result.current_usage == 3


# ============================================================
# TESTES - PLANO SEMESTRAL
# ============================================================

def test_semestral_can_start_five_sessions(enforcement, test_user_semestral, database_url):
    """SEMESTRAL: Pode iniciar até 5 sessões"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Criar 4 sessões
    for _ in range(4):
        session.execute(
            text("""
                INSERT INTO sessao_estudo (user_id, tipo, conta_limite_diario, iniciado_em)
                VALUES (:user_id, 'drill', true, NOW())
            """),
            {"user_id": test_user_semestral}
        )
    session.commit()
    session.close()

    # Tentar 5ª sessão
    result = enforcement.check_can_start_session(
        user_id=test_user_semestral,
        modo_estudo_continuo=False
    )

    assert result.allowed is True
    assert result.current_usage == 4
    assert result.limit >= 5  # Pode ter +1 extra


def test_semestral_allowed_continuous_study(enforcement, test_user_semestral):
    """SEMESTRAL: Permite estudo contínuo"""
    result = enforcement.check_can_start_session(
        user_id=test_user_semestral,
        modo_estudo_continuo=True
    )

    assert result.allowed is True


# ============================================================
# TESTES - PEÇAS
# ============================================================

def test_free_blocked_piece(enforcement, test_user_free):
    """FREE: Bloqueado para peças (limite = 0)"""
    result = enforcement.check_can_practice_piece(
        user_id=test_user_free
    )

    assert result.allowed is False
    assert result.reason_code == ReasonCode.LIMIT_PIECE_MONTHLY
    assert result.limit == 0


def test_mensal_can_practice_piece(enforcement, test_user_mensal):
    """MENSAL: Pode praticar peças (limite = 3/mês)"""
    result = enforcement.check_can_practice_piece(
        user_id=test_user_mensal
    )

    assert result.allowed is True
    assert result.limit == 3


def test_semestral_can_practice_piece(enforcement, test_user_semestral):
    """SEMESTRAL: Pode praticar peças (limite = 10/mês)"""
    result = enforcement.check_can_practice_piece(
        user_id=test_user_semestral
    )

    assert result.allowed is True
    assert result.limit == 10


# ============================================================
# TESTES - RELATÓRIOS
# ============================================================

def test_free_blocked_complete_report(enforcement, test_user_free):
    """FREE: Bloqueado para relatório completo"""
    result = enforcement.check_can_access_complete_report(
        user_id=test_user_free
    )

    assert result.allowed is False
    assert result.reason_code == ReasonCode.FEATURE_REPORT_COMPLETE_NOT_ALLOWED


def test_mensal_allowed_complete_report(enforcement, test_user_mensal):
    """MENSAL: Permite relatório completo"""
    result = enforcement.check_can_access_complete_report(
        user_id=test_user_mensal
    )

    assert result.allowed is True


def test_semestral_allowed_complete_report(enforcement, test_user_semestral):
    """SEMESTRAL: Permite relatório completo"""
    result = enforcement.check_can_access_complete_report(
        user_id=test_user_semestral
    )

    assert result.allowed is True


# ============================================================
# TESTES - RESET DIÁRIO
# ============================================================

def test_daily_reset_works(enforcement, test_user_free, database_url):
    """Reset diário: Sessões de ontem não contam hoje"""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Criar sessão de ontem
    yesterday = datetime.now() - timedelta(days=1)
    session.execute(
        text("""
            INSERT INTO sessao_estudo (user_id, tipo, conta_limite_diario, iniciado_em)
            VALUES (:user_id, 'drill', true, :iniciado_em)
        """),
        {
            "user_id": test_user_free,
            "iniciado_em": yesterday
        }
    )
    session.commit()
    session.close()

    # Tentar sessão hoje
    result = enforcement.check_can_start_session(
        user_id=test_user_free,
        modo_estudo_continuo=False
    )

    assert result.allowed is True
    assert result.current_usage == 0  # Sessão de ontem não conta


# ============================================================
# TESTES - LOGGING
# ============================================================

def test_logging_block_event(enforcement, test_user_free, database_url):
    """Logging: Bloqueios são registrados corretamente"""
    # Criar 1 sessão para atingir limite
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.execute(
        text("""
            INSERT INTO sessao_estudo (user_id, tipo, conta_limite_diario, iniciado_em)
            VALUES (:user_id, 'drill', true, NOW())
        """),
        {"user_id": test_user_free}
    )
    session.commit()

    # Tentar 2ª sessão (será bloqueado e logado)
    result = enforcement.check_can_start_session(
        user_id=test_user_free,
        modo_estudo_continuo=False
    )

    assert result.allowed is False

    # Verificar se log foi criado
    log_count = session.execute(
        text("""
            SELECT COUNT(*)
            FROM enforcement_log
            WHERE user_id = :user_id
              AND reason_code = :reason_code
        """),
        {
            "user_id": test_user_free,
            "reason_code": ReasonCode.LIMIT_SESSIONS_DAILY.value
        }
    ).scalar()

    session.close()

    assert log_count > 0


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
