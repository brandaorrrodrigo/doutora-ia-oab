"""Aplicação principal da API JURIS IA"""
import sys
import os

# Resolver conflito de nomes: api/config.py vs config/ package na raiz
# api/ precisa estar antes de ROOT para 'from config import get_settings' funcionar
# ROOT precisa estar no path para 'from database.connection import ...' funcionar
# api/database.py foi renomeado para db_legacy.py para nao conflitar com database/ package
API_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(API_DIR)
if API_DIR not in sys.path:
    sys.path.insert(0, API_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(1, ROOT_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from routes import router
from endpoints.auth import router as auth_router
from endpoints.admin import router as admin_router
from endpoints.sessao import router as sessao_router
from endpoints.progresso import router as progresso_router

settings = get_settings()

# Criar aplicação FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="""
    ## JURIS IA - API de Questões Jurídicas

    API REST para acesso ao banco de questões jurídicas do sistema JURIS IA.

    ### Funcionalidades:

    * **Questões**: Listar, buscar e filtrar questões por disciplina, fonte e gabarito
    * **Simulados**: Gerar simulados aleatórios personalizados
    * **Estatísticas**: Obter estatísticas do banco de questões
    * **Disciplinas**: Listar disciplinas disponíveis
    * **Sessões de Estudo**: Iniciar, responder questões e finalizar sessões
    * **Progresso**: Dashboard, progresso por disciplina, análise de erros, ranking

    ### Banco de Dados Atual:

    - 925 questões válidas
    - Direito Penal: 624 questões
    - Multidisciplinar OAB: 301 questões

    ### Autores:

    Desenvolvido para o projeto JURIS IA - Sistema de Estudo Jurídico com IA
    """,
    contact={
        "name": "JURIS IA",
        "email": "contato@jurisia.com.br",
    },
    license_info={
        "name": "Proprietário",
    },
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas
app.include_router(router)          # /api/questoes, /api/simulado, /api/estatisticas
app.include_router(auth_router)     # /auth/register, /auth/login, /auth/me
app.include_router(admin_router)    # /admin/create-tables, /admin/seed-questoes, /admin/stats
app.include_router(sessao_router)   # /api/sessao/iniciar, /responder, /finalizar, /ativa
app.include_router(progresso_router) # /api/progresso, /disciplinas, /erros, /ranking


if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print(f"{settings.API_TITLE} v{settings.API_VERSION}")
    print("=" * 80)
    print(f"Iniciando servidor em http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"Documentação: http://localhost:{settings.API_PORT}/docs")
    print(f"Banco de dados: {settings.DB_NAME} @ {settings.DB_HOST}:{settings.DB_PORT}")
    print("=" * 80)

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )
