"""
JURIS_IA_CORE_V1 - Gerenciamento de Conexão com Banco de Dados
===============================================================

Gerencia conexões PostgreSQL, sessões SQLAlchemy e pool de conexões.
Implementa padrões de session management e connection lifecycle.

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-17
Versão: 1.0.0
"""

import os
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
import logging

from database.models import Base

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuração centralizada do banco de dados"""

    def __init__(self):
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = os.getenv("POSTGRES_DB", "juris_ia")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "")

        # Pool de conexões
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        # Configurações de performance
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        self.echo_pool = os.getenv("DB_ECHO_POOL", "false").lower() == "true"

        # SSL (para produção)
        self.use_ssl = os.getenv("DB_USE_SSL", "false").lower() == "true"
        self.ssl_cert_path = os.getenv("DB_SSL_CERT_PATH")

    def get_database_url(self, async_mode: bool = False) -> str:
        """
        Retorna URL de conexão do banco de dados

        Args:
            async_mode: Se True, retorna URL para asyncpg (assíncrono)

        Returns:
            str: URL de conexão PostgreSQL
        """
        # PRIORIDADE 1: Usar DATABASE_URL se fornecido (Railway, produção)
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Railway fornece URL com postgres://, precisamos de postgresql://
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)

            # Adicionar driver correto
            if async_mode and "postgresql://" in database_url:
                database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif not async_mode and "postgresql://" in database_url and "+psycopg2" not in database_url:
                database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

            return database_url

        # PRIORIDADE 2: Construir URL a partir de variáveis individuais (desenvolvimento)
        driver = "postgresql+asyncpg" if async_mode else "postgresql+psycopg2"
        url = f"{driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

        # Adiciona parâmetros SSL se necessário
        if self.use_ssl and self.ssl_cert_path:
            url += f"?sslmode=require&sslrootcert={self.ssl_cert_path}"

        return url

    def __repr__(self):
        return f"<DatabaseConfig(host={self.host}, db={self.database}, pool={self.pool_size})>"


# ============================================================================
# ENGINE E SESSION FACTORY
# ============================================================================

class DatabaseManager:
    """
    Gerenciador central de conexões com banco de dados.
    Implementa Singleton para garantir uma única engine por aplicação.
    """

    _instance: Optional['DatabaseManager'] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None
    _scoped_session_factory: Optional[scoped_session] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializa o gerenciador (apenas uma vez devido ao Singleton)"""
        if not hasattr(self, 'initialized'):
            self.config = DatabaseConfig()
            self.initialized = True
            logger.info("DatabaseManager inicializado")

    def create_engine(self, force_recreate: bool = False) -> Engine:
        """
        Cria ou retorna engine SQLAlchemy existente

        Args:
            force_recreate: Se True, recria a engine mesmo se já existir

        Returns:
            Engine: SQLAlchemy engine
        """
        if self._engine is not None and not force_recreate:
            return self._engine

        logger.info(f"Criando engine para {self.config.host}:{self.config.port}/{self.config.database}")

        # Criar engine com pool de conexões configurado
        self._engine = create_engine(
            self.config.get_database_url(),
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,  # Verifica conexões antes de usar
            echo=self.config.echo,
            echo_pool=self.config.echo_pool,
            future=True,  # SQLAlchemy 2.0 style
        )

        # Configurar eventos do engine
        self._setup_engine_events(self._engine)

        logger.info(f"Engine criada com sucesso. Pool size: {self.config.pool_size}")
        return self._engine

    def _setup_engine_events(self, engine: Engine):
        """Configura eventos do engine para logging e otimizações"""

        @event.listens_for(engine, "connect")
        def set_postgresql_options(dbapi_connection, connection_record):
            """Configura opções PostgreSQL na conexão"""
            cursor = dbapi_connection.cursor()
            # Otimizações PostgreSQL
            cursor.execute("SET TIME ZONE 'UTC'")
            cursor.execute("SET statement_timeout = '60s'")  # Timeout de 60s para queries
            cursor.close()
            logger.debug("Conexão PostgreSQL configurada")

        @event.listens_for(engine, "checkout")
        def checkout_event(dbapi_connection, connection_record, connection_proxy):
            """Log quando conexão é retirada do pool"""
            logger.debug("Conexão retirada do pool")

        @event.listens_for(engine, "checkin")
        def checkin_event(dbapi_connection, connection_record):
            """Log quando conexão retorna ao pool"""
            logger.debug("Conexão retornada ao pool")

    def get_session_factory(self) -> sessionmaker:
        """
        Retorna session factory para criar sessões

        Returns:
            sessionmaker: Factory para criar sessões
        """
        if self._session_factory is None:
            if self._engine is None:
                self.create_engine()

            self._session_factory = sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
            logger.info("Session factory criada")

        return self._session_factory

    def get_scoped_session(self) -> scoped_session:
        """
        Retorna scoped session (thread-safe)
        Útil para aplicações web multi-thread

        Returns:
            scoped_session: Sessão thread-safe
        """
        if self._scoped_session_factory is None:
            session_factory = self.get_session_factory()
            self._scoped_session_factory = scoped_session(session_factory)
            logger.info("Scoped session factory criada")

        return self._scoped_session_factory

    def create_all_tables(self):
        """Cria todas as tabelas do banco de dados"""
        if self._engine is None:
            self.create_engine()

        logger.info("Criando todas as tabelas...")
        Base.metadata.create_all(bind=self._engine)
        logger.info("Todas as tabelas criadas com sucesso")

    def drop_all_tables(self):
        """
        CUIDADO: Remove todas as tabelas do banco de dados
        Use apenas em desenvolvimento ou testes
        """
        if self._engine is None:
            self.create_engine()

        logger.warning("ATENÇÃO: Removendo todas as tabelas do banco de dados!")
        Base.metadata.drop_all(bind=self._engine)
        logger.warning("Todas as tabelas removidas")

    def dispose(self):
        """Fecha todas as conexões e limpa o pool"""
        if self._engine is not None:
            logger.info("Fechando todas as conexões do pool...")
            self._engine.dispose()
            logger.info("Engine disposed")

        self._engine = None
        self._session_factory = None
        self._scoped_session_factory = None

    def get_pool_status(self) -> dict:
        """
        Retorna status do pool de conexões

        Returns:
            dict: Informações sobre o pool
        """
        if self._engine is None:
            return {"status": "Engine não inicializada"}

        pool = self._engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
            "timeout": self.config.pool_timeout,
        }


# ============================================================================
# CONTEXT MANAGERS PARA SESSÕES
# ============================================================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager para obter sessão de banco de dados.
    Garante commit/rollback automático e fechamento da sessão.

    Uso:
        with get_db_session() as session:
            user = session.query(User).first()
            # ... operações ...
        # Sessão automaticamente fechada aqui

    Yields:
        Session: Sessão SQLAlchemy
    """
    db_manager = DatabaseManager()
    SessionFactory = db_manager.get_session_factory()
    session = SessionFactory()

    try:
        yield session
        session.commit()
        logger.debug("Transação commitada com sucesso")
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na transação, rollback executado: {e}")
        raise
    finally:
        session.close()
        logger.debug("Sessão fechada")


@contextmanager
def get_db_session_no_commit() -> Generator[Session, None, None]:
    """
    Context manager para obter sessão SEM commit automático.
    Útil quando você quer controlar manualmente o commit.

    Uso:
        with get_db_session_no_commit() as session:
            user = session.query(User).first()
            session.commit()  # Commit manual

    Yields:
        Session: Sessão SQLAlchemy
    """
    db_manager = DatabaseManager()
    SessionFactory = db_manager.get_session_factory()
    session = SessionFactory()

    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Erro na transação, rollback executado: {e}")
        raise
    finally:
        session.close()
        logger.debug("Sessão fechada (no auto-commit)")


# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def init_database():
    """
    Inicializa o banco de dados:
    1. Cria engine
    2. Cria todas as tabelas
    3. Verifica conexão
    """
    logger.info("Inicializando banco de dados...")

    db_manager = DatabaseManager()

    # Criar engine
    db_manager.create_engine()

    # Testar conexão
    try:
        with get_db_session() as session:
            session.execute("SELECT 1")
            logger.info("Conexão com banco de dados estabelecida com sucesso")
    except Exception as e:
        logger.error(f"Falha ao conectar no banco de dados: {e}")
        raise

    # Criar tabelas
    db_manager.create_all_tables()

    logger.info("Banco de dados inicializado com sucesso")


def check_database_health() -> dict:
    """
    Verifica saúde do banco de dados

    Returns:
        dict: Status da saúde do banco
    """
    db_manager = DatabaseManager()

    health = {
        "database": "healthy",
        "pool_status": None,
        "connection_test": False,
        "tables_exist": False,
    }

    try:
        # Status do pool
        health["pool_status"] = db_manager.get_pool_status()

        # Testar conexão
        with get_db_session() as session:
            result = session.execute("SELECT 1").scalar()
            health["connection_test"] = (result == 1)

        # Verificar se tabelas existem
        with get_db_session() as session:
            result = session.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ).scalar()
            health["tables_exist"] = (result > 0)
            health["table_count"] = result

    except Exception as e:
        health["database"] = "unhealthy"
        health["error"] = str(e)
        logger.error(f"Erro ao verificar saúde do banco: {e}")

    return health


def close_all_connections():
    """Fecha todas as conexões do pool"""
    db_manager = DatabaseManager()
    db_manager.dispose()
    logger.info("Todas as conexões fechadas")


# ============================================================================
# DECORATORS
# ============================================================================

def with_db_session(func):
    """
    Decorator que injeta sessão de banco de dados como primeiro argumento.

    Uso:
        @with_db_session
        def minha_funcao(session, user_id):
            user = session.query(User).get(user_id)
            return user
    """
    def wrapper(*args, **kwargs):
        with get_db_session() as session:
            return func(session, *args, **kwargs)
    return wrapper


# ============================================================================
# INSTÂNCIA GLOBAL (SINGLETON)
# ============================================================================

# Instância global do DatabaseManager
db_manager = DatabaseManager()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    print("=== TESTE DE CONEXÃO COM BANCO DE DADOS ===\n")

    # Inicializar banco
    init_database()

    # Verificar saúde
    health = check_database_health()
    print(f"\nStatus do banco: {health}\n")

    # Status do pool
    pool_status = db_manager.get_pool_status()
    print(f"Status do pool: {pool_status}\n")

    # Testar sessão
    try:
        with get_db_session() as session:
            # Executar query simples
            result = session.execute("SELECT version()").scalar()
            print(f"PostgreSQL Version: {result}\n")

            # Contar tabelas
            count = session.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ).scalar()
            print(f"Total de tabelas criadas: {count}\n")

    except Exception as e:
        print(f"Erro: {e}\n")

    finally:
        # Fechar conexões
        close_all_connections()
        print("Conexões fechadas. Teste concluído.")
