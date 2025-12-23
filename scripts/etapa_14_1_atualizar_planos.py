#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ETAPA 14.1 - DEFINIÇÃO DE PLANOS E PREÇOS
================================================================================
Script para atualizar planos no banco de dados com pricing definitivo.

Planos:
- FREE: R$ 0,00
- OAB MENSAL: R$ 49,90
- OAB SEMESTRAL: R$ 247,00 (PLANO ÂNCORA)

Características:
- Preços configuráveis via .env
- Desativa plano PRO (não mais oferecido)
- Mantém estrutura de billing existente
- Pronto para produção

Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
Data: 2025-12-18
================================================================================
"""

import os
import sys
from pathlib import Path
from decimal import Decimal
from typing import Dict, Optional
import logging

# Adiciona path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()


class PricingConfig:
    """Configuração de pricing baseada em variáveis de ambiente."""

    def __init__(self):
        # Plano FREE
        self.free_preco = Decimal(os.getenv('PLANO_FREE_PRECO_MENSAL', '0.00'))

        # Plano OAB MENSAL
        self.oab_mensal_preco = Decimal(os.getenv('PLANO_OAB_MENSAL_PRECO_MENSAL', '49.90'))

        # Plano OAB SEMESTRAL (6 meses)
        self.oab_semestral_preco = Decimal(os.getenv('PLANO_OAB_SEMESTRAL_PRECO_SEMESTRAL', '247.00'))

        # Moeda
        self.moeda = os.getenv('PRICING_MOEDA', 'BRL')

    def get_preco_mensal_equivalente_semestral(self) -> Decimal:
        """Calcula preço mensal equivalente do plano semestral."""
        return self.oab_semestral_preco / Decimal('6')

    def get_economia_semestral_vs_mensal(self) -> Decimal:
        """Calcula economia do plano semestral vs pagar 6x mensal."""
        custo_6_meses_mensal = self.oab_mensal_preco * Decimal('6')
        economia = custo_6_meses_mensal - self.oab_semestral_preco
        return economia

    def get_percentual_economia(self) -> Decimal:
        """Calcula percentual de economia do plano semestral."""
        custo_6_meses_mensal = self.oab_mensal_preco * Decimal('6')
        if custo_6_meses_mensal > 0:
            return (self.get_economia_semestral_vs_mensal() / custo_6_meses_mensal) * Decimal('100')
        return Decimal('0')


def conectar_database() -> sessionmaker:
    """Conecta ao database e retorna session maker."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL não configurada")

    # Para conexão de fora do Docker, ajusta host
    if 'postgres:5432' in database_url:
        database_url = database_url.replace('postgres:5432', 'localhost:5432')

    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session


def atualizar_plano_free(session, config: PricingConfig) -> bool:
    """Atualiza plano FREE."""
    try:
        logger.info("Atualizando plano FREE...")

        result = session.execute(
            text("""
                UPDATE plano
                SET
                    nome = 'Plano Gratuito',
                    descricao = 'Acesso básico para conhecer a plataforma',
                    preco_mensal = :preco,
                    preco_anual = NULL,
                    moeda = :moeda,
                    ativo = true,
                    visivel_publico = true,
                    updated_at = NOW()
                WHERE codigo = 'FREE'
                RETURNING id
            """),
            {
                'preco': float(config.free_preco),
                'moeda': config.moeda
            }
        )

        if result.rowcount > 0:
            logger.info(f"✓ Plano FREE atualizado: R$ {config.free_preco}")
            session.commit()
            return True
        else:
            logger.warning("Plano FREE não encontrado")
            return False

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao atualizar plano FREE: {e}")
        return False


def atualizar_plano_oab_mensal(session, config: PricingConfig) -> bool:
    """Atualiza plano OAB MENSAL (antigo BASIC)."""
    try:
        logger.info("Atualizando plano OAB MENSAL...")

        # Primeiro verifica se existe com código BASIC
        result_check = session.execute(
            text("SELECT id FROM plano WHERE codigo = 'BASIC'")
        ).fetchone()

        if result_check:
            # Atualiza BASIC para OAB_MENSAL
            result = session.execute(
                text("""
                    UPDATE plano
                    SET
                        codigo = 'OAB_MENSAL',
                        nome = 'OAB Mensal',
                        descricao = 'Plano mensal para preparação consistente para OAB',
                        preco_mensal = :preco,
                        preco_anual = NULL,
                        moeda = :moeda,
                        ativo = true,
                        visivel_publico = true,
                        updated_at = NOW()
                    WHERE codigo = 'BASIC'
                    RETURNING id
                """),
                {
                    'preco': float(config.oab_mensal_preco),
                    'moeda': config.moeda
                }
            )
        else:
            # Cria novo se não existir
            result = session.execute(
                text("""
                    INSERT INTO plano (
                        codigo, nome, descricao, preco_mensal, moeda,
                        ativo, visivel_publico
                    )
                    VALUES (
                        'OAB_MENSAL', 'OAB Mensal',
                        'Plano mensal para preparação consistente para OAB',
                        :preco, :moeda, true, true
                    )
                    RETURNING id
                """),
                {
                    'preco': float(config.oab_mensal_preco),
                    'moeda': config.moeda
                }
            )

        if result.rowcount > 0:
            logger.info(f"✓ Plano OAB MENSAL atualizado: R$ {config.oab_mensal_preco}/mês")
            session.commit()
            return True
        else:
            logger.warning("Falha ao atualizar plano OAB MENSAL")
            return False

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao atualizar plano OAB MENSAL: {e}")
        return False


def criar_plano_oab_semestral(session, config: PricingConfig) -> bool:
    """Cria plano OAB SEMESTRAL."""
    try:
        logger.info("Criando plano OAB SEMESTRAL...")

        # Verifica se já existe
        result_check = session.execute(
            text("SELECT id FROM plano WHERE codigo = 'OAB_SEMESTRAL'")
        ).fetchone()

        if result_check:
            # Atualiza se já existir
            result = session.execute(
                text("""
                    UPDATE plano
                    SET
                        nome = 'OAB Semestral',
                        descricao = 'Plano semestral com economia - ideal para preparação completa (PLANO ÂNCORA)',
                        preco_mensal = :preco_mensal_equiv,
                        preco_anual = NULL,
                        moeda = :moeda,
                        ativo = true,
                        visivel_publico = true,
                        updated_at = NOW()
                    WHERE codigo = 'OAB_SEMESTRAL'
                    RETURNING id
                """),
                {
                    'preco_mensal_equiv': float(config.get_preco_mensal_equivalente_semestral()),
                    'moeda': config.moeda
                }
            )
            logger.info("Plano OAB SEMESTRAL já existia, foi atualizado")
        else:
            # Cria novo
            result = session.execute(
                text("""
                    INSERT INTO plano (
                        codigo, nome, descricao, preco_mensal, moeda,
                        ativo, visivel_publico
                    )
                    VALUES (
                        'OAB_SEMESTRAL', 'OAB Semestral',
                        'Plano semestral com economia - ideal para preparação completa (PLANO ÂNCORA)',
                        :preco_mensal_equiv, :moeda, true, true
                    )
                    RETURNING id
                """),
                {
                    'preco_mensal_equiv': float(config.get_preco_mensal_equivalente_semestral()),
                    'moeda': config.moeda
                }
            )

        if result.rowcount > 0:
            preco_mensal_equiv = config.get_preco_mensal_equivalente_semestral()
            economia = config.get_economia_semestral_vs_mensal()
            percentual = config.get_percentual_economia()

            logger.info(f"✓ Plano OAB SEMESTRAL criado:")
            logger.info(f"  - Valor total (6 meses): R$ {config.oab_semestral_preco}")
            logger.info(f"  - Equivalente mensal: R$ {preco_mensal_equiv:.2f}/mês")
            logger.info(f"  - Economia vs Mensal: R$ {economia:.2f} ({percentual:.1f}%)")
            session.commit()
            return True
        else:
            logger.warning("Falha ao criar plano OAB SEMESTRAL")
            return False

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao criar plano OAB SEMESTRAL: {e}")
        return False


def desativar_plano_pro(session) -> bool:
    """Desativa plano PRO (não mais oferecido)."""
    try:
        logger.info("Desativando plano PRO...")

        result = session.execute(
            text("""
                UPDATE plano
                SET
                    ativo = false,
                    visivel_publico = false,
                    updated_at = NOW()
                WHERE codigo = 'PRO'
                RETURNING id
            """)
        )

        if result.rowcount > 0:
            logger.info("✓ Plano PRO desativado (não mais oferecido)")
            session.commit()
            return True
        else:
            logger.info("Plano PRO não encontrado (ok)")
            return True

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao desativar plano PRO: {e}")
        return False


def exibir_resumo_pricing(config: PricingConfig):
    """Exibe resumo do pricing configurado."""
    logger.info("\n" + "=" * 80)
    logger.info("RESUMO DO PRICING - ETAPA 14.1 CONCLUÍDA")
    logger.info("=" * 80)

    logger.info("\n📋 PLANOS ATIVOS:")
    logger.info(f"\n1. FREE")
    logger.info(f"   Preço: R$ {config.free_preco}/mês")

    logger.info(f"\n2. OAB MENSAL")
    logger.info(f"   Preço: R$ {config.oab_mensal_preco}/mês")

    preco_mensal_equiv = config.get_preco_mensal_equivalente_semestral()
    economia = config.get_economia_semestral_vs_mensal()
    percentual = config.get_percentual_economia()

    logger.info(f"\n3. OAB SEMESTRAL ⭐ (PLANO ÂNCORA)")
    logger.info(f"   Preço: R$ {config.oab_semestral_preco} (6 meses)")
    logger.info(f"   Equivalente: R$ {preco_mensal_equiv:.2f}/mês")
    logger.info(f"   Economia: R$ {economia:.2f} ({percentual:.1f}% vs pagar 6x Mensal)")

    logger.info(f"\n💰 MOEDA: {config.moeda}")

    logger.info("\n✅ Preços configuráveis via variáveis de ambiente (.env)")
    logger.info("=" * 80 + "\n")


def main():
    """Função principal."""
    logger.info("=" * 80)
    logger.info("ETAPA 14.1 - DEFINIÇÃO DE PLANOS E PREÇOS")
    logger.info("=" * 80)
    logger.info("Atualizando planos no banco de dados...\n")

    # Carrega configuração de pricing
    config = PricingConfig()

    # Conecta ao database
    try:
        Session = conectar_database()
        session = Session()
        logger.info("✓ Conectado ao database\n")
    except Exception as e:
        logger.error(f"Erro ao conectar ao database: {e}")
        sys.exit(1)

    # Atualiza planos
    sucesso = True

    sucesso &= atualizar_plano_free(session, config)
    sucesso &= atualizar_plano_oab_mensal(session, config)
    sucesso &= criar_plano_oab_semestral(session, config)
    sucesso &= desativar_plano_pro(session)

    # Exibe resumo
    if sucesso:
        exibir_resumo_pricing(config)
        logger.info("✅ ETAPA 14.1 CONCLUÍDA COM SUCESSO")
    else:
        logger.error("❌ ETAPA 14.1 CONCLUÍDA COM ERROS")
        sys.exit(1)

    session.close()


if __name__ == "__main__":
    main()
