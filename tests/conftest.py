"""
Fixtures compartilhadas para testes do JURIS IA
================================================

Fixtures:
  - client: FastAPI TestClient
  - auth_headers: Headers com JWT token (usuario registrado)
  - db_session: Sessao SQLAlchemy para acesso direto ao banco
"""
import sys
import os

# Adicionar raiz do projeto e pasta api ao path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT_DIR, "api")
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, API_DIR)

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """
    FastAPI TestClient para toda a sessao de testes.
    Importa o app de api/main.py.
    """
    from api.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def db_session():
    """
    Sessao SQLAlchemy para acesso direto ao banco.
    Util para verificar dados ou limpar apos testes.
    """
    from database.connection import DatabaseManager

    db_manager = DatabaseManager()
    SessionFactory = db_manager.get_session_factory()
    session = SessionFactory()

    yield session

    session.close()


@pytest.fixture(scope="session")
def test_user_email():
    """Email unico para o usuario de teste desta sessao"""
    return f"test_{uuid4().hex[:8]}@jurisia.com"


@pytest.fixture(scope="session")
def test_user_password():
    """Senha do usuario de teste"""
    return "test123456"


@pytest.fixture(scope="session")
def registered_user(client, test_user_email, test_user_password):
    """
    Registra um usuario de teste e retorna os dados.
    Retorna dict com: token, user_id, email
    """
    response = client.post("/auth/register", json={
        "nome": "Tester Automatizado",
        "email": test_user_email,
        "senha": test_user_password
    })

    assert response.status_code == 201, f"Falha no registro: {response.text}"
    data = response.json()
    assert data["success"] is True

    return {
        "token": data["data"]["token"],
        "user_id": data["data"]["user"]["id"],
        "email": data["data"]["user"]["email"],
        "nome": data["data"]["user"]["nome"]
    }


@pytest.fixture(scope="session")
def auth_headers(registered_user):
    """
    Headers HTTP com Bearer token para endpoints autenticados.

    Uso:
        def test_algo(client, auth_headers):
            response = client.get("/auth/me", headers=auth_headers)
    """
    return {
        "Authorization": f"Bearer {registered_user['token']}"
    }


@pytest.fixture
def ensure_no_active_session(client, auth_headers):
    """
    Garante que nao existe sessao ativa antes do teste.
    Finaliza qualquer sessao ativa encontrada.
    """
    response = client.get("/api/sessao/ativa", headers=auth_headers)
    if response.status_code == 200:
        data = response.json()
        if data.get("ativa"):
            client.post("/api/sessao/finalizar", headers=auth_headers)


@pytest.fixture
def ensure_questoes_exist(db_session):
    """
    Verifica se existem questoes no questoes_banco.
    Se nao existem, pula o teste com mensagem clara.
    """
    from database.models import QuestaoBanco

    count = db_session.query(QuestaoBanco).filter(
        QuestaoBanco.ativa == True
    ).count()

    if count < 5:
        pytest.skip(
            f"Apenas {count} questoes em questoes_banco. "
            "Execute: POST /admin/seed-questoes ou python scripts/migrate_questoes.py"
        )

    return count
