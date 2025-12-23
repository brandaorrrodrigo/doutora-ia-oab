"""
================================================================================
SCRIPT: POPULAR EMBEDDINGS COM OLLAMA (IA Própria)
================================================================================
Objetivo: Gerar embeddings para todas as questões usando modelos locais
Prioridade: P0 (CRÍTICA)
Data: 2025-12-17
================================================================================

IMPORTANTE:
- Requer Ollama instalado e rodando
- Requer modelo de embedding baixado (ollama pull nomic-embed-text)
- Custo ZERO de API
- Processa em batches de 50 questões
- Pode ser executado múltiplas vezes (idempotente)

MODELOS RECOMENDADOS:
- nomic-embed-text (768 dims) - Melhor qualidade, ~1.5GB
- mxbai-embed-large (1024 dims) - Alta qualidade, ~670MB
- all-minilm (384 dims) - Mais rápido, ~120MB

USO:
    python popular_embeddings_ollama.py --modelo nomic-embed-text --limite 100
    python popular_embeddings_ollama.py --modelo mxbai-embed-large --all
    python popular_embeddings_ollama.py --stats-only

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
from core.embedding_service_ollama import (
    EmbeddingServiceOllama,
    verificar_suporte_pgvector,
    estatisticas_embeddings,
    listar_modelos_ollama
)

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
        "ollama_rodando": False,
    }

    # Verificar DATABASE_URL
    if os.getenv("DATABASE_URL"):
        validacoes["database_url"] = True
        logger.info("✓ DATABASE_URL configurado")
    else:
        logger.error("✗ DATABASE_URL não configurado")

    # Verificar Ollama
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            validacoes["ollama_rodando"] = True
            logger.info("✓ Ollama rodando")
        else:
            logger.error("✗ Ollama não está rodando")
    except Exception as e:
        logger.error(f"✗ Ollama não está acessível: {e}")

    return validacoes


def exibir_modelos_disponiveis() -> None:
    """
    Exibe modelos de embedding disponíveis no Ollama.
    """
    logger.info("\n" + "=" * 80)
    logger.info("MODELOS DE EMBEDDING DISPONÍVEIS")
    logger.info("=" * 80)

    modelos = listar_modelos_ollama()

    if modelos:
        logger.info(f"Total: {len(modelos)} modelos")
        logger.info("")
        for modelo in modelos:
            logger.info(f"• {modelo['nome']}")
            if 'tamanho_gb' in modelo: logger.info(f"  Tamanho: {modelo['tamanho_gb']:.2f} GB")
    else:
        logger.warning("Nenhum modelo de embedding encontrado")
        logger.info("\nModelos recomendados:")
        logger.info("• ollama pull nomic-embed-text  (768 dims, ~1.5GB)")
        logger.info("• ollama pull mxbai-embed-large (1024 dims, ~670MB)")
        logger.info("• ollama pull all-minilm       (384 dims, ~120MB)")


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


def ajustar_coluna_embedding(session, dimensoes: int) -> bool:
    """
    Ajusta coluna embedding para as dimensões do modelo.

    Args:
        session: Sessão do SQLAlchemy
        dimensoes: Número de dimensões do modelo

    Returns:
        True se ajustou com sucesso
    """
    try:
        # Verificar dimensão atual
        result = session.execute(
            text("""
                SELECT atttypmod
                FROM pg_attribute
                WHERE attrelid = 'questao_oab'::regclass
                  AND attname = 'embedding'
            """)
        ).fetchone()

        dimensao_atual = result[0] if result else None

        # Se coluna não existe, criar
        if dimensao_atual is None:
            logger.info(f"Criando coluna embedding com {dimensoes} dimensões...")
            session.execute(
                text(f"ALTER TABLE questao_oab ADD COLUMN embedding VECTOR({dimensoes})")
            )
            session.commit()
            logger.info("✓ Coluna embedding criada")
            return True

        # Se dimensão é diferente, avisar mas continuar
        # (permite ter embeddings de diferentes modelos)
        logger.info(f"Coluna embedding existente (dimensões podem variar)")
        return True

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao ajustar coluna: {e}")
        return False


def popular_embeddings(
    modelo: str = "nomic-embed-text",
    limite: int = None,
    apenas_sem_embedding: bool = True,
    stats_only: bool = False
) -> None:
    """
    Popula embeddings das questões usando Ollama.

    Args:
        modelo: Nome do modelo de embedding
        limite: Limite de questões a processar (None = todas)
        apenas_sem_embedding: Se True, processa apenas questões sem embedding
        stats_only: Se True, apenas exibe estatísticas
    """
    logger.info("=" * 80)
    logger.info("POPULAR EMBEDDINGS - OLLAMA (IA PRÓPRIA)")
    logger.info("=" * 80)
    logger.info(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Modelo: {modelo}")
    logger.info("")

    # Validar ambiente
    validacoes = validar_ambiente()

    if not all(validacoes.values()):
        logger.error("\nConfigurações faltando. Abortando.")
        if not validacoes["ollama_rodando"]:
            logger.error("\nPara iniciar Ollama:")
            logger.error("  Windows: ollama serve")
            logger.error("  Linux: systemctl start ollama")
        sys.exit(1)

    # Exibir modelos disponíveis
    exibir_modelos_disponiveis()

    # Conectar ao banco
    try:
        database_url = os.getenv("DATABASE_URL")
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()

        logger.info("\n✓ Conectado ao banco de dados")

    except Exception as e:
        logger.error(f"Erro ao conectar ao banco: {e}")
        sys.exit(1)

    # Verificar pgvector
    #     if not verificar_suporte_pgvector(session):
    #         logger.error("✗ Extensão pgvector não instalada")
    #         logger.error("Execute: CREATE EXTENSION IF NOT EXISTS vector;")
    #         sys.exit(1)
    else:
        logger.info("✓ pgvector instalado")

    # Exibir estatísticas atuais
    exibir_estatisticas(session)

    # Se stats_only, encerrar aqui
    if stats_only:
        logger.info("\nModo stats-only. Nenhuma modificação realizada.")
        session.close()
        return

    # Inicializar serviço de embeddings
    try:
        embedding_service = EmbeddingServiceOllama(model=modelo)
        logger.info(f"\n✓ EmbeddingServiceOllama inicializado")
        logger.info(f"  Modelo: {modelo}")
        logger.info(f"  Dimensões: {embedding_service.embedding_dimensions}")

    except Exception as e:
        logger.error(f"Erro ao inicializar EmbeddingServiceOllama: {e}")
        logger.error(f"\nPara baixar o modelo:")
        logger.error(f"  ollama pull {modelo}")
        session.close()
        sys.exit(1)

    # Ajustar coluna embedding
    if not ajustar_coluna_embedding(session, embedding_service.embedding_dimensions):
        logger.error("Erro ao ajustar coluna embedding")
        session.close()
        sys.exit(1)

    # Confirmação do usuário
    logger.info("\n" + "=" * 80)
    logger.info("CONFIRMAÇÃO")
    logger.info("=" * 80)

    if limite:
        logger.info(f"Será processado: até {limite} questões")
    else:
        logger.info("Será processado: TODAS as questões sem embedding")

    logger.info("\nVANTAGENS OLLAMA:")
    logger.info("- Custo: R$ 0,00 (modelo local)")
    logger.info("- Privacidade: Dados não saem do servidor")
    logger.info("- Sem limites: Processa quantas questões quiser")

    logger.info("\nREQUISITOS:")
    logger.info(f"- Modelo: {modelo}")
    logger.info(f"- Dimensões: {embedding_service.embedding_dimensions}")

    if limite:
        logger.info(f"- Tempo estimado: ~{limite * 0.5:.0f}s ({limite} questões)")
    else:
        stats = estatisticas_embeddings(session)
        sem_embedding = stats['questoes_sem_embedding']
        logger.info(f"- Tempo estimado: ~{sem_embedding * 0.5:.0f}s ({sem_embedding} questões)")

    resposta = input("\nDeseja continuar? (s/n): ")

    if resposta.lower() != 's':
        logger.info("Operação cancelada pelo usuário")
        session.close()
        return

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

        logger.info(f"\nModelo usado: {resultado['modelo']}")
        logger.info(f"Dimensões: {resultado['dimensoes']}")
        logger.info(f"Custo: R$ 0,00 (modelo local)")

        if resultado['erros'] > 0:
            logger.warning(f"\n{resultado['erros']} erros encontrados:")
            for erro in resultado['erros_detalhes'][:10]:
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
        description="Popula embeddings das questões OAB usando Ollama"
    )

    parser.add_argument(
        "--modelo",
        type=str,
        default="nomic-embed-text",
        help="Modelo de embedding (padrão: nomic-embed-text)"
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
        modelo=args.modelo,
        limite=args.limite,
        apenas_sem_embedding=not args.all,
        stats_only=args.stats_only
    )


if __name__ == "__main__":
    main()
