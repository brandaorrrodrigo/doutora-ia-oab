"""
================================================================================
SCRIPT: POPULAR EMBEDDINGS DAS QUESTÕES OAB
================================================================================
Objetivo: Gerar embeddings para todas as questões existentes no banco
Prioridade: P0 (CRÍTICA)
Data: 2025-12-17
================================================================================

IMPORTANTE:
- Requer OPENAI_API_KEY configurada
- Processa em batches de 100 questões
- Custo estimado: ~$0.10 por 1000 questões
- Pode ser executado múltiplas vezes (idempotente)

CUSTO ESTIMADO:
- text-embedding-3-large: $0.00013 / 1K tokens
- Média de ~300 tokens por questão
- 1000 questões = ~300K tokens = ~$0.039
- 10000 questões = ~3M tokens = ~$0.39

USO:
    python popular_embeddings.py --limite 100
    python popular_embeddings.py --all
    python popular_embeddings.py --stats-only

================================================================================
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

# Adicionar diretório raiz ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from core.embedding_service import EmbeddingService, verificar_suporte_pgvector, estatisticas_embeddings

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validar_ambiente() -> Dict[str, bool]:
    """
    Valida configuração do ambiente.

    Returns:
        Dict com status de cada validação
    """
    validacoes = {
        "database_url": False,
        "openai_api_key": False,
        "pgvector_instalado": False
    }

    # Verificar DATABASE_URL
    if os.getenv("DATABASE_URL"):
        validacoes["database_url"] = True
        logger.info("✓ DATABASE_URL configurado")
    else:
        logger.error("✗ DATABASE_URL não configurado")

    # Verificar OPENAI_API_KEY
    if os.getenv("OPENAI_API_KEY"):
        validacoes["openai_api_key"] = True
        logger.info("✓ OPENAI_API_KEY configurado")
    else:
        logger.error("✗ OPENAI_API_KEY não configurado")

    return validacoes


def exibir_estatisticas(session) -> None:
    """
    Exibe estatísticas atuais de embeddings.

    Args:
        session: Sessão do SQLAlchemy
    """
    logger.info("\n" + "=" * 80)
    logger.info("ESTATÍSTICAS DE EMBEDDINGS")
    logger.info("=" * 80)

    stats = estatisticas_embeddings(session)

    logger.info(f"Total de questões: {stats['total_questoes']}")
    logger.info(f"Questões com embedding: {stats['questoes_com_embedding']}")
    logger.info(f"Questões sem embedding: {stats['questoes_sem_embedding']}")
    logger.info(f"Cobertura: {stats['percentual_cobertura']}%")

    # Estatísticas por disciplina
    logger.info("\n--- Por Disciplina ---")
    disciplinas = session.execute(
        text("""
            SELECT
                disciplina,
                COUNT(*) as total,
                COUNT(embedding) as com_embedding,
                ROUND(
                    (COUNT(embedding)::FLOAT / NULLIF(COUNT(*), 0)) * 100,
                    1
                ) as percentual
            FROM questao_oab
            WHERE disciplina IS NOT NULL
            GROUP BY disciplina
            ORDER BY total DESC
        """)
    ).fetchall()

    for disc in disciplinas:
        logger.info(
            f"{disc[0]}: {disc[2]}/{disc[1]} ({disc[3]}%)"
        )


def popular_embeddings(
    limite: int = None,
    apenas_sem_embedding: bool = True,
    stats_only: bool = False
) -> None:
    """
    Popula embeddings das questões.

    Args:
        limite: Limite de questões a processar (None = todas)
        apenas_sem_embedding: Se True, processa apenas questões sem embedding
        stats_only: Se True, apenas exibe estatísticas
    """
    logger.info("=" * 80)
    logger.info("POPULAR EMBEDDINGS - QUESTÕES OAB")
    logger.info("=" * 80)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Validar ambiente
    validacoes = validar_ambiente()

    if not all(validacoes.values()):
        logger.error("\nConfigurações faltando. Abortando.")
        sys.exit(1)

    # Conectar ao banco
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        logger.info("✓ Conectado ao banco de dados")

    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        sys.exit(1)

    # Verificar pgvector
    if not verificar_suporte_pgvector(session):
        logger.error("✗ Extensão pgvector não instalada")
        logger.error("Execute: CREATE EXTENSION IF NOT EXISTS vector;")
        sys.exit(1)
    else:
        logger.info("✓ pgvector instalado")

    # Exibir estatísticas atuais
    exibir_estatisticas(session)

    # Se stats_only, encerrar aqui
    if stats_only:
        logger.info("\nModo stats-only. Nenhuma modificação realizada.")
        session.close()
        return

    # Confirmação do usuário
    logger.info("\n" + "=" * 80)
    logger.info("CONFIRMAÇÃO")
    logger.info("=" * 80)

    if limite:
        logger.info(f"Será processado: até {limite} questões")
    else:
        logger.info("Será processado: TODAS as questões sem embedding")

    logger.info("\nCUSTO ESTIMADO:")
    logger.info("- text-embedding-3-large: $0.00013 / 1K tokens")
    logger.info("- Média: ~300 tokens por questão")

    if limite:
        custo = (limite * 300 * 0.00013) / 1000
        logger.info(f"- Total estimado: ~${custo:.4f}")
    else:
        stats = estatisticas_embeddings(session)
        sem_embedding = stats['questoes_sem_embedding']
        custo = (sem_embedding * 300 * 0.00013) / 1000
        logger.info(f"- Total estimado para {sem_embedding} questões: ~${custo:.4f}")

    resposta = input("\nDeseja continuar? (s/n): ")

    if resposta.lower() != 's':
        logger.info("Operação cancelada pelo usuário")
        session.close()
        return

    # Inicializar serviço de embeddings
    try:
        embedding_service = EmbeddingService()
        logger.info("\n✓ EmbeddingService inicializado")

    except Exception as e:
        logger.error(f"Erro ao inicializar EmbeddingService: {e}")
        session.close()
        sys.exit(1)

    # Processar embeddings em lote
    logger.info("\n" + "=" * 80)
    logger.info("PROCESSANDO EMBEDDINGS")
    logger.info("=" * 80)

    try:
        resultado = embedding_service.gerar_embeddings_batch(
            session=session,
            limite=limite,
            apenas_sem_embedding=apenas_sem_embedding
        )

        # Exibir resultado
        logger.info("\n" + "=" * 80)
        logger.info("RESULTADO FINAL")
        logger.info("=" * 80)
        logger.info(f"Total processado: {resultado['total_questoes']}")
        logger.info(f"Sucessos: {resultado['sucessos']}")
        logger.info(f"Erros: {resultado['erros']}")
        logger.info(f"Tempo total: {resultado['tempo_total']:.2f}s")

        if resultado['sucessos'] > 0:
            velocidade = resultado['sucessos'] / resultado['tempo_total']
            logger.info(f"Velocidade: {velocidade:.2f} questões/segundo")

            # Custo real
            custo_real = (resultado['sucessos'] * 300 * 0.00013) / 1000
            logger.info(f"Custo estimado: ${custo_real:.4f}")

        if resultado['erros'] > 0:
            logger.warning(f"\n{resultado['erros']} erros encontrados:")
            for erro in resultado['erros_detalhes'][:10]:  # Primeiros 10
                logger.warning(f"- Questão {erro['questao_id']}: {erro['erro']}")

            if len(resultado['erros_detalhes']) > 10:
                logger.warning(f"... e mais {len(resultado['erros_detalhes']) - 10} erros")

        # Estatísticas finais
        logger.info("\n" + "=" * 80)
        logger.info("ESTATÍSTICAS FINAIS")
        logger.info("=" * 80)
        exibir_estatisticas(session)

    except Exception as e:
        logger.error(f"\nErro durante processamento: {e}")
        raise

    finally:
        session.close()
        logger.info("\nConexão com banco encerrada")


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description="Popula embeddings das questões OAB"
    )

    parser.add_argument(
        "--limite",
        type=int,
        help="Limite de questões a processar (padrão: todas)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Processar TODAS as questões (inclusive as que já têm embedding)"
    )

    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Apenas exibir estatísticas (não processar)"
    )

    args = parser.parse_args()

    # Executar
    popular_embeddings(
        limite=args.limite,
        apenas_sem_embedding=not args.all,
        stats_only=args.stats_only
    )


if __name__ == "__main__":
    main()
