"""
================================================================================
JURIS_IA_CORE_V1 - Serviço de Embeddings com OLLAMA (IA Própria)
================================================================================
Objetivo: Gerar embeddings vetoriais usando modelos locais via Ollama
Prioridade: P0 (CRÍTICA)
Data: 2025-12-17
================================================================================

MODELOS RECOMENDADOS PARA EMBEDDINGS:
- nomic-embed-text (768 dims) - Melhor qualidade, ~1.5GB
- mxbai-embed-large (1024 dims) - Alta qualidade, ~670MB
- all-minilm (384 dims) - Mais rápido, ~120MB

VANTAGENS OLLAMA:
- Custo ZERO de API
- Dados 100% privados
- Sem limites de rate limiting
- Performance previsível

REQUISITOS:
- Ollama instalado e rodando
- Modelo de embedding baixado (ollama pull nomic-embed-text)
- 8GB+ RAM para modelos maiores

================================================================================
"""

import logging
import requests
import json
from typing import List, Optional, Dict, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingServiceOllama:
    """
    Serviço de geração de embeddings usando Ollama (IA local).

    Usa modelos de embedding open-source rodando localmente:
    - Busca semântica de questões similares
    - Recomendação de revisão
    - Agrupamento por temas
    """

    # Configuração do modelo
    DEFAULT_MODEL = "nomic-embed-text"  # 768 dimensões
    DEFAULT_HOST = "http://localhost:11434"

    # Mapeamento de dimensões por modelo
    MODEL_DIMENSIONS = {
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "all-minilm": 384,
        "bge-large": 1024,
        "bge-base": 768
    }

    # Tamanho do batch para geração
    BATCH_SIZE = 50  # Menor que OpenAI porque é local

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        ollama_host: str = DEFAULT_HOST
    ):
        """
        Inicializa o serviço de embeddings com Ollama.

        Args:
            model: Nome do modelo de embedding
            ollama_host: URL do servidor Ollama
        """
        self.model = model
        self.ollama_host = ollama_host
        self.embedding_dimensions = self.MODEL_DIMENSIONS.get(model, 768)

        # Verificar se Ollama está disponível
        if not self._verificar_ollama():
            raise ConnectionError(
                f"Ollama não está acessível em {ollama_host}. "
                "Certifique-se de que o servidor Ollama está rodando."
            )

        # Verificar se modelo está disponível
        if not self._verificar_modelo():
            raise ValueError(
                f"Modelo {model} não encontrado. "
                f"Execute: ollama pull {model}"
            )

        logger.info(
            f"EmbeddingServiceOllama inicializado: "
            f"modelo={model}, dimensões={self.embedding_dimensions}"
        )


    def _verificar_ollama(self) -> bool:
        """
        Verifica se servidor Ollama está rodando.

        Returns:
            True se Ollama está acessível
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Erro ao conectar ao Ollama: {e}")
            return False


    def _verificar_modelo(self) -> bool:
        """
        Verifica se modelo está disponível no Ollama.

        Returns:
            True se modelo está disponível
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)

            if response.status_code == 200:
                modelos = response.json().get("models", [])
                modelos_disponiveis = [m["name"].split(":")[0] for m in modelos]
                return self.model in modelos_disponiveis

            return False

        except Exception as e:
            logger.error(f"Erro ao verificar modelo: {e}")
            return False


    def _construir_texto_questao(
        self,
        enunciado: str,
        alternativas: Dict[str, str]
    ) -> str:
        """
        Constrói o texto completo da questão para embedding.

        Args:
            enunciado: Enunciado da questão
            alternativas: Dict com alternativas {A: texto, B: texto, ...}

        Returns:
            Texto formatado para embedding
        """
        # Formatar alternativas
        alternativas_texto = "\n".join([
            f"{letra}) {texto}"
            for letra, texto in sorted(alternativas.items())
        ])

        # Texto completo
        texto_completo = f"{enunciado}\n\n{alternativas_texto}"

        return texto_completo


    def gerar_embedding(self, texto: str) -> List[float]:
        """
        Gera embedding para um texto usando Ollama.

        Args:
            texto: Texto para gerar embedding

        Returns:
            Lista de floats representando o vetor

        Raises:
            Exception: Se falhar ao gerar embedding
        """
        try:
            # Chamar API do Ollama
            response = requests.post(
                f"{self.ollama_host}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": texto
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(
                    f"Ollama retornou status {response.status_code}: "
                    f"{response.text}"
                )

            embedding = response.json()["embedding"]

            # Validar dimensões
            if len(embedding) != self.embedding_dimensions:
                raise ValueError(
                    f"Embedding com {len(embedding)} dimensões, "
                    f"esperado {self.embedding_dimensions}"
                )

            logger.debug(f"Embedding gerado com sucesso ({len(embedding)} dims)")
            return embedding

        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise


    def gerar_embedding_questao(
        self,
        session: Session,
        questao_id: UUID
    ) -> Tuple[bool, Optional[str]]:
        """
        Gera embedding para uma questão específica.

        Args:
            session: Sessão do SQLAlchemy
            questao_id: ID da questão

        Returns:
            Tupla (sucesso, mensagem_erro)
        """
        try:
            # Buscar questão
            result = session.execute(
                text("""
                    SELECT enunciado, alternativas, embedding
                    FROM questao_oab
                    WHERE id = :id
                """),
                {"id": questao_id}
            ).fetchone()

            if not result:
                return False, f"Questão {questao_id} não encontrada"

            enunciado, alternativas, embedding_atual = result

            # Verificar se já tem embedding
            if embedding_atual is not None:
                logger.info(f"Questão {questao_id} já possui embedding")
                return True, None

            # Construir texto
            texto_completo = self._construir_texto_questao(enunciado, alternativas)

            # Gerar embedding
            embedding = self.gerar_embedding(texto_completo)

            # Salvar no banco (ajustar dimensão do vetor)
            session.execute(
                text(f"""
                    UPDATE questao_oab
                    SET embedding = :embedding::vector({self.embedding_dimensions}),
                        updated_at = NOW()
                    WHERE id = :id
                """),
                {
                    "id": questao_id,
                    "embedding": str(embedding)
                }
            )

            session.commit()

            logger.info(f"Embedding gerado para questão {questao_id}")
            return True, None

        except Exception as e:
            session.rollback()
            error_msg = f"Erro ao gerar embedding para questão {questao_id}: {e}"
            logger.error(error_msg)
            return False, error_msg


    def gerar_embeddings_batch(
        self,
        session: Session,
        limite: Optional[int] = None,
        apenas_sem_embedding: bool = True
    ) -> Dict[str, any]:
        """
        Gera embeddings em lote para múltiplas questões.

        Args:
            session: Sessão do SQLAlchemy
            limite: Limite de questões a processar (None = todas)
            apenas_sem_embedding: Se True, processa apenas questões sem embedding

        Returns:
            Dict com estatísticas do processamento
        """
        inicio = datetime.now()

        logger.info("=" * 80)
        logger.info("INICIANDO GERAÇÃO DE EMBEDDINGS EM LOTE (OLLAMA)")
        logger.info("=" * 80)
        logger.info(f"Modelo: {self.model}")
        logger.info(f"Dimensões: {self.embedding_dimensions}")

        # Buscar questões para processar
        query = """
            SELECT id, enunciado, alternativas
            FROM questao_oab
        """

        if apenas_sem_embedding:
            query += " WHERE embedding IS NULL"

        if limite:
            query += f" LIMIT {limite}"

        questoes = session.execute(text(query)).fetchall()

        total_questoes = len(questoes)
        logger.info(f"Total de questões a processar: {total_questoes}")

        if total_questoes == 0:
            logger.info("Nenhuma questão para processar")
            return {
                "total_questoes": 0,
                "sucessos": 0,
                "erros": 0,
                "tempo_total": 0,
                "erros_detalhes": []
            }

        # Processar em batches
        sucessos = 0
        erros = 0
        erros_detalhes = []

        for i in range(0, total_questoes, self.BATCH_SIZE):
            batch = questoes[i:i + self.BATCH_SIZE]
            batch_num = (i // self.BATCH_SIZE) + 1
            total_batches = (total_questoes + self.BATCH_SIZE - 1) // self.BATCH_SIZE

            logger.info(f"\n--- Batch {batch_num}/{total_batches} ---")

            for questao_id, enunciado, alternativas in batch:
                try:
                    # Construir texto
                    texto_completo = self._construir_texto_questao(
                        enunciado,
                        alternativas
                    )

                    # Gerar embedding
                    embedding = self.gerar_embedding(texto_completo)

                    # Salvar no banco
                    session.execute(
                        text(f"""
                            UPDATE questao_oab
                            SET embedding = :embedding::vector({self.embedding_dimensions}),
                                updated_at = NOW()
                            WHERE id = :id
                        """),
                        {
                            "id": questao_id,
                            "embedding": str(embedding)
                        }
                    )

                    session.commit()
                    sucessos += 1

                    if sucessos % 10 == 0:
                        logger.info(f"Progresso: {sucessos}/{total_questoes} questões processadas")

                except Exception as e:
                    session.rollback()
                    erros += 1
                    erro_detalhe = {
                        "questao_id": str(questao_id),
                        "erro": str(e)
                    }
                    erros_detalhes.append(erro_detalhe)
                    logger.error(f"Erro ao processar questão {questao_id}: {e}")

        # Calcular tempo total
        tempo_total = (datetime.now() - inicio).total_seconds()

        # Estatísticas finais
        logger.info("\n" + "=" * 80)
        logger.info("GERAÇÃO DE EMBEDDINGS CONCLUÍDA")
        logger.info("=" * 80)
        logger.info(f"Total de questões: {total_questoes}")
        logger.info(f"Sucessos: {sucessos}")
        logger.info(f"Erros: {erros}")
        logger.info(f"Tempo total: {tempo_total:.2f}s")
        logger.info(f"Taxa de sucesso: {(sucessos/total_questoes)*100:.1f}%")

        if sucessos > 0:
            logger.info(f"Velocidade: {sucessos/tempo_total:.2f} questões/segundo")

        return {
            "total_questoes": total_questoes,
            "sucessos": sucessos,
            "erros": erros,
            "tempo_total": tempo_total,
            "erros_detalhes": erros_detalhes,
            "modelo": self.model,
            "dimensoes": self.embedding_dimensions
        }


    def buscar_questoes_similares(
        self,
        session: Session,
        questao_id: UUID,
        limite: int = 5,
        threshold_similaridade: float = 0.7
    ) -> List[Dict]:
        """
        Busca questões similares usando busca vetorial.

        Args:
            session: Sessão do SQLAlchemy
            questao_id: ID da questão de referência
            limite: Número máximo de questões similares
            threshold_similaridade: Threshold mínimo de similaridade (0-1)

        Returns:
            Lista de questões similares com score de similaridade
        """
        try:
            # Buscar embedding da questão de referência
            result = session.execute(
                text("""
                    SELECT embedding
                    FROM questao_oab
                    WHERE id = :id
                """),
                {"id": questao_id}
            ).fetchone()

            if not result or not result[0]:
                logger.warning(f"Questão {questao_id} não tem embedding")
                return []

            embedding_ref = result[0]

            # Busca vetorial usando similaridade de cosseno
            questoes_similares = session.execute(
                text("""
                    SELECT
                        id,
                        numero_questao,
                        enunciado,
                        disciplina,
                        assunto,
                        1 - (embedding <=> :embedding::vector) as similaridade
                    FROM questao_oab
                    WHERE id != :questao_id
                      AND embedding IS NOT NULL
                      AND 1 - (embedding <=> :embedding::vector) >= :threshold
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limite
                """),
                {
                    "questao_id": questao_id,
                    "embedding": embedding_ref,
                    "threshold": threshold_similaridade,
                    "limite": limite
                }
            ).fetchall()

            resultados = []
            for row in questoes_similares:
                resultados.append({
                    "id": str(row[0]),
                    "numero_questao": row[1],
                    "enunciado": row[2][:200] + "...",
                    "disciplina": row[3],
                    "assunto": row[4],
                    "similaridade": float(row[5])
                })

            logger.info(
                f"Encontradas {len(resultados)} questões similares "
                f"para {questao_id}"
            )

            return resultados

        except Exception as e:
            logger.error(f"Erro ao buscar questões similares: {e}")
            return []


    def recomendar_revisao(
        self,
        session: Session,
        usuario_id: UUID,
        limite: int = 10
    ) -> List[Dict]:
        """
        Recomenda questões para revisão baseado em erros anteriores.

        Usa embeddings para encontrar questões similares às que o usuário errou.

        Args:
            session: Sessão do SQLAlchemy
            usuario_id: ID do usuário
            limite: Número de questões a recomendar

        Returns:
            Lista de questões recomendadas
        """
        try:
            # Buscar questões que o usuário errou recentemente
            questoes_erradas = session.execute(
                text("""
                    SELECT DISTINCT q.id, q.embedding
                    FROM resposta r
                    JOIN questao_oab q ON r.questao_id = q.id
                    WHERE r.usuario_id = :usuario_id
                      AND r.correta = FALSE
                      AND q.embedding IS NOT NULL
                    ORDER BY r.respondida_em DESC
                    LIMIT 5
                """),
                {"usuario_id": usuario_id}
            ).fetchall()

            if not questoes_erradas:
                logger.info(f"Usuário {usuario_id} não tem erros recentes")
                return []

            # Coletar embeddings das questões erradas
            embeddings_erros = [row[1] for row in questoes_erradas]

            # Usar primeiro embedding como referência (simplificado)
            embedding_ref = embeddings_erros[0]

            # Buscar questões similares que o usuário ainda não respondeu
            recomendacoes = session.execute(
                text("""
                    SELECT
                        q.id,
                        q.numero_questao,
                        q.enunciado,
                        q.disciplina,
                        q.assunto,
                        q.dificuldade,
                        1 - (q.embedding <=> :embedding::vector) as relevancia
                    FROM questao_oab q
                    LEFT JOIN resposta r ON q.id = r.questao_id
                        AND r.usuario_id = :usuario_id
                    WHERE q.embedding IS NOT NULL
                      AND r.id IS NULL
                      AND 1 - (q.embedding <=> :embedding::vector) >= 0.6
                    ORDER BY q.embedding <=> :embedding::vector
                    LIMIT :limite
                """),
                {
                    "usuario_id": usuario_id,
                    "embedding": embedding_ref,
                    "limite": limite
                }
            ).fetchall()

            resultados = []
            for row in recomendacoes:
                resultados.append({
                    "id": str(row[0]),
                    "numero_questao": row[1],
                    "enunciado": row[2][:200] + "...",
                    "disciplina": row[3],
                    "assunto": row[4],
                    "dificuldade": row[5],
                    "relevancia": float(row[6])
                })

            logger.info(
                f"Recomendadas {len(resultados)} questões "
                f"para revisão do usuário {usuario_id}"
            )

            return resultados

        except Exception as e:
            logger.error(f"Erro ao recomendar revisão: {e}")
            return []


# ================================================================================
# FUNÇÕES AUXILIARES
# ================================================================================

def listar_modelos_ollama(ollama_host: str = "http://localhost:11434") -> List[Dict]:
    """
    Lista modelos de embedding disponíveis no Ollama.

    Args:
        ollama_host: URL do servidor Ollama

    Returns:
        Lista de modelos disponíveis
    """
    try:
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)

        if response.status_code == 200:
            modelos = response.json().get("models", [])

            # Filtrar apenas modelos de embedding
            modelos_embedding = []
            for modelo in modelos:
                nome = modelo["name"].split(":")[0]
                if "embed" in nome.lower():
                    modelos_embedding.append({
                        "nome": nome,
                        "tamanho": modelo.get("size", 0),
                        "modificado": modelo.get("modified_at")
                    })

            return modelos_embedding

        return []

    except Exception as e:
        logger.error(f"Erro ao listar modelos: {e}")
        return []


def verificar_suporte_pgvector(session: Session) -> bool:
    """
    Verifica se pgvector está instalado e configurado.

    Args:
        session: Sessão do SQLAlchemy

    Returns:
        True se pgvector está disponível
    """
    try:
        result = session.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).fetchone()

        return result is not None

    except Exception as e:
        logger.error(f"Erro ao verificar pgvector: {e}")
        return False


def estatisticas_embeddings(session: Session) -> Dict:
    """
    Retorna estatísticas sobre embeddings no banco.

    Args:
        session: Sessão do SQLAlchemy

    Returns:
        Dict com estatísticas
    """
    try:
        stats = session.execute(
            text("""
                SELECT
                    COUNT(*) as total_questoes,
                    COUNT(embedding) as questoes_com_embedding,
                    COUNT(*) - COUNT(embedding) as questoes_sem_embedding,
                    ROUND(
                        (COUNT(embedding)::FLOAT / NULLIF(COUNT(*), 0)) * 100,
                        2
                    ) as percentual_cobertura
                FROM questao_oab
            """)
        ).fetchone()

        return {
            "total_questoes": stats[0],
            "questoes_com_embedding": stats[1],
            "questoes_sem_embedding": stats[2],
            "percentual_cobertura": float(stats[3]) if stats[3] else 0.0
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return {}
