"""
================================================================================
JURIS_IA_CORE_V1 - Serviço de Cache com Redis
================================================================================
Objetivo: Cache de alto desempenho para otimizar queries frequentes
Prioridade: P0 (CRÍTICA)
Data: 2025-12-17
================================================================================

IMPACTO ESPERADO:
- 10x mais rápido para dados frequentemente acessados
- Redução de 90% na carga do PostgreSQL
- Latência < 10ms para cache hits

ESTRATÉGIA DE CACHE:
- Questões: 24 horas (dados estáveis)
- Sessões: 4 horas (dados voláteis)
- Estatísticas de usuário: 1 hora (dados dinâmicos)
- Gabaritos: NUNCA (segurança)

================================================================================
"""

import os
import json
import logging
from typing import Any, Optional, Dict, List
from datetime import timedelta
from uuid import UUID
import redis
from redis.connection import ConnectionPool

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CacheService:
    """
    Serviço de cache usando Redis.

    Estratégia de invalidação:
    - TTL automático para dados voláteis
    - Invalidação explícita para dados modificados
    - Prefix-based namespacing para organização
    """

    # Prefixos de chave
    PREFIX_QUESTAO = "questao"
    PREFIX_SESSAO = "sessao"
    PREFIX_USUARIO = "usuario"
    PREFIX_ESTATISTICAS = "stats"
    PREFIX_RANKING = "ranking"

    # TTLs padrão (em segundos)
    TTL_QUESTAO = 86400  # 24 horas
    TTL_SESSAO = 14400  # 4 horas
    TTL_USUARIO = 3600  # 1 hora
    TTL_ESTATISTICAS = 3600  # 1 hora
    TTL_RANKING = 1800  # 30 minutos

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 50
    ):
        """
        Inicializa o serviço de cache.

        Args:
            redis_url: URL do Redis (se None, usa variável de ambiente)
            max_connections: Número máximo de conexões no pool
        """
        self.redis_url = redis_url or os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0"
        )

        # Criar pool de conexões
        self.pool = ConnectionPool.from_url(
            self.redis_url,
            max_connections=max_connections,
            decode_responses=True  # Retorna strings ao invés de bytes
        )

        # Cliente Redis
        self.redis_client = redis.Redis(connection_pool=self.pool)

        # Testar conexão
        try:
            self.redis_client.ping()
            logger.info(f"CacheService conectado ao Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Redis: {e}")
            raise


    def _construir_chave(self, prefix: str, identificador: str) -> str:
        """
        Constrói chave de cache com namespace.

        Args:
            prefix: Prefixo do tipo de dado
            identificador: Identificador único

        Returns:
            Chave formatada
        """
        return f"juris_ia:{prefix}:{identificador}"


    def get(self, chave: str) -> Optional[Any]:
        """
        Busca valor no cache.

        Args:
            chave: Chave de cache

        Returns:
            Valor deserializado ou None se não encontrado
        """
        try:
            valor = self.redis_client.get(chave)

            if valor is None:
                logger.debug(f"Cache MISS: {chave}")
                return None

            logger.debug(f"Cache HIT: {chave}")

            # Deserializar JSON
            return json.loads(valor)

        except Exception as e:
            logger.error(f"Erro ao buscar cache {chave}: {e}")
            return None


    def set(
        self,
        chave: str,
        valor: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Define valor no cache.

        Args:
            chave: Chave de cache
            valor: Valor a ser armazenado (será serializado como JSON)
            ttl: Time-to-live em segundos (None = sem expiração)

        Returns:
            True se salvou com sucesso
        """
        try:
            # Serializar para JSON
            valor_json = json.dumps(valor, default=str)

            # Salvar no Redis
            if ttl:
                self.redis_client.setex(chave, ttl, valor_json)
            else:
                self.redis_client.set(chave, valor_json)

            logger.debug(f"Cache SET: {chave} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar cache {chave}: {e}")
            return False


    def delete(self, chave: str) -> bool:
        """
        Remove valor do cache.

        Args:
            chave: Chave de cache

        Returns:
            True se removeu com sucesso
        """
        try:
            self.redis_client.delete(chave)
            logger.debug(f"Cache DELETE: {chave}")
            return True

        except Exception as e:
            logger.error(f"Erro ao deletar cache {chave}: {e}")
            return False


    def delete_pattern(self, pattern: str) -> int:
        """
        Remove múltiplas chaves por padrão.

        Args:
            pattern: Padrão de chave (ex: "juris_ia:questao:*")

        Returns:
            Número de chaves removidas
        """
        try:
            chaves = list(self.redis_client.scan_iter(match=pattern))

            if chaves:
                removidas = self.redis_client.delete(*chaves)
                logger.info(f"Cache DELETE PATTERN: {pattern} ({removidas} chaves)")
                return removidas

            return 0

        except Exception as e:
            logger.error(f"Erro ao deletar padrão {pattern}: {e}")
            return 0


    # ============================================================================
    # CACHE DE QUESTÕES
    # ============================================================================

    def get_questao(self, questao_id: UUID) -> Optional[Dict]:
        """
        Busca questão no cache.

        Args:
            questao_id: ID da questão

        Returns:
            Dict com dados da questão ou None
        """
        chave = self._construir_chave(self.PREFIX_QUESTAO, str(questao_id))
        return self.get(chave)


    def set_questao(self, questao_id: UUID, dados: Dict) -> bool:
        """
        Salva questão no cache.

        IMPORTANTE: Dados NÃO devem incluir gabarito (segurança).

        Args:
            questao_id: ID da questão
            dados: Dict com dados da questão (sem gabarito)

        Returns:
            True se salvou com sucesso
        """
        # Garantir que gabarito não está incluído
        if "alternativa_correta" in dados or "gabarito" in dados:
            logger.warning(
                f"Tentativa de cachear questão {questao_id} com gabarito. "
                "BLOQUEADO por segurança."
            )
            return False

        chave = self._construir_chave(self.PREFIX_QUESTAO, str(questao_id))
        return self.set(chave, dados, self.TTL_QUESTAO)


    def invalidar_questao(self, questao_id: UUID) -> bool:
        """
        Invalida questão específica do cache.

        Args:
            questao_id: ID da questão

        Returns:
            True se invalidou com sucesso
        """
        chave = self._construir_chave(self.PREFIX_QUESTAO, str(questao_id))
        return self.delete(chave)


    # ============================================================================
    # CACHE DE SESSÕES
    # ============================================================================

    def get_sessao(self, sessao_id: UUID) -> Optional[Dict]:
        """
        Busca sessão no cache.

        Args:
            sessao_id: ID da sessão

        Returns:
            Dict com dados da sessão ou None
        """
        chave = self._construir_chave(self.PREFIX_SESSAO, str(sessao_id))
        return self.get(chave)


    def set_sessao(self, sessao_id: UUID, dados: Dict) -> bool:
        """
        Salva sessão no cache.

        Args:
            sessao_id: ID da sessão
            dados: Dict com dados da sessão

        Returns:
            True se salvou com sucesso
        """
        chave = self._construir_chave(self.PREFIX_SESSAO, str(sessao_id))
        return self.set(chave, dados, self.TTL_SESSAO)


    def invalidar_sessao(self, sessao_id: UUID) -> bool:
        """
        Invalida sessão específica do cache.

        Args:
            sessao_id: ID da sessão

        Returns:
            True se invalidou com sucesso
        """
        chave = self._construir_chave(self.PREFIX_SESSAO, str(sessao_id))
        return self.delete(chave)


    def invalidar_sessoes_usuario(self, usuario_id: UUID) -> int:
        """
        Invalida todas as sessões de um usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            Número de sessões invalidadas
        """
        pattern = self._construir_chave(self.PREFIX_SESSAO, f"*:usuario:{usuario_id}:*")
        return self.delete_pattern(pattern)


    # ============================================================================
    # CACHE DE ESTATÍSTICAS DE USUÁRIO
    # ============================================================================

    def get_estatisticas_usuario(self, usuario_id: UUID) -> Optional[Dict]:
        """
        Busca estatísticas de usuário no cache.

        Args:
            usuario_id: ID do usuário

        Returns:
            Dict com estatísticas ou None
        """
        chave = self._construir_chave(
            self.PREFIX_ESTATISTICAS,
            f"usuario:{usuario_id}"
        )
        return self.get(chave)


    def set_estatisticas_usuario(self, usuario_id: UUID, stats: Dict) -> bool:
        """
        Salva estatísticas de usuário no cache.

        Args:
            usuario_id: ID do usuário
            stats: Dict com estatísticas

        Returns:
            True se salvou com sucesso
        """
        chave = self._construir_chave(
            self.PREFIX_ESTATISTICAS,
            f"usuario:{usuario_id}"
        )
        return self.set(chave, stats, self.TTL_ESTATISTICAS)


    def invalidar_estatisticas_usuario(self, usuario_id: UUID) -> bool:
        """
        Invalida estatísticas de usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            True se invalidou com sucesso
        """
        chave = self._construir_chave(
            self.PREFIX_ESTATISTICAS,
            f"usuario:{usuario_id}"
        )
        return self.delete(chave)


    # ============================================================================
    # CACHE DE RANKINGS
    # ============================================================================

    def get_ranking(self, tipo: str = "geral") -> Optional[List[Dict]]:
        """
        Busca ranking no cache.

        Args:
            tipo: Tipo de ranking (geral, semanal, disciplina_X)

        Returns:
            Lista de usuários no ranking ou None
        """
        chave = self._construir_chave(self.PREFIX_RANKING, tipo)
        return self.get(chave)


    def set_ranking(self, tipo: str, dados: List[Dict]) -> bool:
        """
        Salva ranking no cache.

        Args:
            tipo: Tipo de ranking
            dados: Lista de usuários no ranking

        Returns:
            True se salvou com sucesso
        """
        chave = self._construir_chave(self.PREFIX_RANKING, tipo)
        return self.set(chave, dados, self.TTL_RANKING)


    def invalidar_todos_rankings(self) -> int:
        """
        Invalida todos os rankings.

        Returns:
            Número de rankings invalidados
        """
        pattern = self._construir_chave(self.PREFIX_RANKING, "*")
        return self.delete_pattern(pattern)


    # ============================================================================
    # CONTADORES E RATE LIMITING
    # ============================================================================

    def incrementar_contador(
        self,
        chave: str,
        ttl: Optional[int] = None
    ) -> int:
        """
        Incrementa contador.

        Útil para rate limiting e métricas.

        Args:
            chave: Chave do contador
            ttl: TTL em segundos (None = sem expiração)

        Returns:
            Valor após incremento
        """
        try:
            pipeline = self.redis_client.pipeline()
            pipeline.incr(chave)

            if ttl:
                pipeline.expire(chave, ttl)

            resultado = pipeline.execute()
            return resultado[0]

        except Exception as e:
            logger.error(f"Erro ao incrementar contador {chave}: {e}")
            return 0


    def verificar_rate_limit(
        self,
        identificador: str,
        limite: int,
        janela_segundos: int
    ) -> bool:
        """
        Verifica rate limit.

        Args:
            identificador: Identificador único (ex: usuario_id, ip)
            limite: Número máximo de requisições
            janela_segundos: Janela de tempo em segundos

        Returns:
            True se está dentro do limite, False se excedeu
        """
        chave = f"rate_limit:{identificador}"

        try:
            contador = self.redis_client.get(chave)

            if contador is None:
                # Primeira requisição na janela
                self.redis_client.setex(chave, janela_segundos, 1)
                return True

            contador_int = int(contador)

            if contador_int >= limite:
                logger.warning(
                    f"Rate limit excedido para {identificador}: "
                    f"{contador_int}/{limite}"
                )
                return False

            # Incrementar contador
            self.redis_client.incr(chave)
            return True

        except Exception as e:
            logger.error(f"Erro ao verificar rate limit: {e}")
            # Em caso de erro, permitir (fail open)
            return True


    # ============================================================================
    # FUNÇÕES DE UTILIDADE
    # ============================================================================

    def flush_all(self) -> bool:
        """
        CUIDADO: Remove TODOS os dados do cache.

        Returns:
            True se limpou com sucesso
        """
        try:
            self.redis_client.flushdb()
            logger.warning("Cache totalmente limpo (FLUSH ALL)")
            return True

        except Exception as e:
            logger.error(f"Erro ao limpar cache: {e}")
            return False


    def info(self) -> Dict:
        """
        Retorna informações sobre o Redis.

        Returns:
            Dict com estatísticas do Redis
        """
        try:
            info = self.redis_client.info()

            return {
                "versao": info.get("redis_version"),
                "modo": info.get("redis_mode"),
                "uptime_segundos": info.get("uptime_in_seconds"),
                "conexoes_ativas": info.get("connected_clients"),
                "memoria_usada_mb": info.get("used_memory") / (1024 * 1024),
                "total_chaves": self.redis_client.dbsize(),
                "hit_rate": self._calcular_hit_rate(info)
            }

        except Exception as e:
            logger.error(f"Erro ao obter info do Redis: {e}")
            return {}


    def _calcular_hit_rate(self, info: Dict) -> float:
        """
        Calcula taxa de acerto do cache.

        Args:
            info: Dict de info do Redis

        Returns:
            Taxa de acerto (0.0 a 1.0)
        """
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)

        total = hits + misses

        if total == 0:
            return 0.0

        return hits / total


    def health_check(self) -> bool:
        """
        Verifica saúde do serviço de cache.

        Returns:
            True se saudável
        """
        try:
            # Ping
            self.redis_client.ping()

            # Test set/get
            chave_teste = "health_check"
            self.redis_client.setex(chave_teste, 10, "ok")
            valor = self.redis_client.get(chave_teste)

            return valor == "ok"

        except Exception as e:
            logger.error(f"Health check FALHOU: {e}")
            return False


# ================================================================================
# DECORADOR PARA CACHE AUTOMÁTICO
# ================================================================================

def cached(
    prefix: str,
    ttl: int,
    key_builder=None
):
    """
    Decorador para cachear automaticamente resultado de função.

    Args:
        prefix: Prefixo da chave de cache
        ttl: TTL em segundos
        key_builder: Função para construir chave (default: usa argumentos da função)

    Exemplo:
        @cached(prefix="usuario", ttl=3600)
        def buscar_usuario(usuario_id):
            # ... query no banco ...
            return usuario
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Construir chave de cache
            if key_builder:
                chave = key_builder(*args, **kwargs)
            else:
                # Usar argumentos como chave
                chave_args = ":".join([str(arg) for arg in args])
                chave_kwargs = ":".join([f"{k}={v}" for k, v in kwargs.items()])
                chave = f"juris_ia:{prefix}:{chave_args}:{chave_kwargs}"

            # Tentar cache
            cache = CacheService()
            resultado = cache.get(chave)

            if resultado is not None:
                logger.debug(f"Cache HIT (decorator): {func.__name__}")
                return resultado

            # Cache miss - executar função
            logger.debug(f"Cache MISS (decorator): {func.__name__}")
            resultado = func(*args, **kwargs)

            # Salvar em cache
            cache.set(chave, resultado, ttl)

            return resultado

        return wrapper
    return decorator
