#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
ETAPA 14.2 - DEFINIÇÃO DE LIMITES POR PLANO
================================================================================
Script para definir limites operacionais técnicos reais para cada plano.

Princípios:
- FREE: Prova valor mas impede estudo sério
- OAB MENSAL: Permite estudo consistente
- OAB SEMESTRAL: Atende heavy users sem bloqueio frustrante

Características:
- Limites pedagógicos, não financeiros
- Sessões longas NÃO consomem sessão adicional
- Estudo contínuo não consome nova sessão
- Heavy users não são punidos

Autor: JURIS_IA_CORE_V1 - Arquiteto de Pricing
Data: 2025-12-19
================================================================================
"""

import os
import sys
from pathlib import Path
import logging
from typing import Dict
from dataclasses import dataclass

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


@dataclass
class LimitesPlano:
    """Limites operacionais de um plano."""
    # Sessões
    limite_sessoes_dia: int
    duracao_maxima_sessao_minutos: int
    limite_questoes_por_sessao: int

    # Questões e consultas
    limite_questoes_dia: int
    limite_consultas_dia: int

    # Práticas de peça
    limite_peca_mes: int

    # Recursos avançados
    permite_estudo_continuo: bool
    permite_sessao_estendida: bool
    sessoes_extras_condicionais: int

    # Relatórios
    acesso_relatorio_tipo: str

    # Acessos
    acesso_modo_pedagogico: bool
    acesso_analytics: bool
    acesso_jurisprudencia: bool


def get_limites_free() -> LimitesPlano:
    """
    Limites do plano FREE.

    Objetivo: Provar valor mas impedir estudo sério.

    Estratégia:
    - 1 sessão curta por dia
    - 5 questões por sessão
    - Sem estudo contínuo
    - Relatório básico apenas
    """
    return LimitesPlano(
        # Sessões - MUITO LIMITADO
        limite_sessoes_dia=1,
        duracao_maxima_sessao_minutos=30,  # 30min max
        limite_questoes_por_sessao=5,

        # Total de questões por dia
        limite_questoes_dia=5,  # 1 sessão x 5 questões
        limite_consultas_dia=3,  # Consultas à lei seca

        # Peças - BLOQUEADO
        limite_peca_mes=0,

        # Extensões - BLOQUEADAS
        permite_estudo_continuo=False,
        permite_sessao_estendida=False,
        sessoes_extras_condicionais=0,

        # Relatórios - BÁSICO
        acesso_relatorio_tipo='basico',

        # Acessos
        acesso_modo_pedagogico=True,
        acesso_analytics=False,
        acesso_jurisprudencia=False
    )


def get_limites_oab_mensal() -> LimitesPlano:
    """
    Limites do plano OAB MENSAL.

    Objetivo: Permitir estudo consistente.

    Estratégia:
    - 3 sessões por dia (manhã, tarde, noite)
    - 15 questões por sessão
    - Estudo contínuo permitido
    - Relatório completo
    """
    return LimitesPlano(
        # Sessões - ADEQUADO
        limite_sessoes_dia=3,
        duracao_maxima_sessao_minutos=90,  # 90min max por sessão
        limite_questoes_por_sessao=15,

        # Total de questões por dia
        limite_questoes_dia=45,  # 3 sessões x 15 questões
        limite_consultas_dia=20,

        # Peças - LIMITADO
        limite_peca_mes=3,

        # Extensões - PARCIAL
        permite_estudo_continuo=True,  # Pode revisar erros sem consumir sessão
        permite_sessao_estendida=False,  # Sessões limitadas a 90min
        sessoes_extras_condicionais=0,

        # Relatórios - COMPLETO
        acesso_relatorio_tipo='completo',

        # Acessos
        acesso_modo_pedagogico=True,
        acesso_analytics=True,
        acesso_jurisprudencia=True
    )


def get_limites_oab_semestral() -> LimitesPlano:
    """
    Limites do plano OAB SEMESTRAL (PLANO ÂNCORA).

    Objetivo: Atender heavy users sem bloqueio frustrante.

    Estratégia:
    - 5 sessões por dia (sem bloqueio real)
    - 25 questões por sessão
    - Sessões estendidas permitidas
    - +1 sessão extra condicional (heavy users)
    - Relatório completo com analytics
    """
    return LimitesPlano(
        # Sessões - GENEROSO
        limite_sessoes_dia=5,
        duracao_maxima_sessao_minutos=180,  # 3h max por sessão
        limite_questoes_por_sessao=25,

        # Total de questões por dia
        limite_questoes_dia=125,  # 5 sessões x 25 questões
        limite_consultas_dia=100,  # Praticamente ilimitado

        # Peças - ADEQUADO
        limite_peca_mes=10,

        # Extensões - COMPLETAS
        permite_estudo_continuo=True,
        permite_sessao_estendida=True,  # Sessões longas não consomem adicional
        sessoes_extras_condicionais=1,  # +1 sessão extra para heavy users

        # Relatórios - COMPLETO
        acesso_relatorio_tipo='completo',

        # Acessos - TUDO
        acesso_modo_pedagogico=True,
        acesso_analytics=True,
        acesso_jurisprudencia=True
    )


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


def aplicar_limites_plano(session, codigo_plano: str, limites: LimitesPlano) -> bool:
    """Aplica limites a um plano específico."""
    try:
        logger.info(f"Aplicando limites ao plano {codigo_plano}...")

        # Desabilitar trigger temporariamente
        session.execute(text("ALTER TABLE plano DISABLE TRIGGER trigger_plano_updated_at"))

        result = session.execute(
            text("""
                UPDATE plano
                SET
                    limite_sessoes_dia = :limite_sessoes_dia,
                    duracao_maxima_sessao_minutos = :duracao_maxima_sessao_minutos,
                    limite_questoes_por_sessao = :limite_questoes_por_sessao,
                    limite_questoes_dia = :limite_questoes_dia,
                    limite_consultas_dia = :limite_consultas_dia,
                    limite_peca_mes = :limite_peca_mes,
                    permite_estudo_continuo = :permite_estudo_continuo,
                    permite_sessao_estendida = :permite_sessao_estendida,
                    sessoes_extras_condicionais = :sessoes_extras_condicionais,
                    acesso_relatorio_tipo = :acesso_relatorio_tipo,
                    acesso_modo_pedagogico = :acesso_modo_pedagogico,
                    acesso_analytics = :acesso_analytics,
                    acesso_jurisprudencia = :acesso_jurisprudencia,
                    updated_at = NOW()
                WHERE codigo = :codigo
                RETURNING id
            """),
            {
                'codigo': codigo_plano,
                'limite_sessoes_dia': limites.limite_sessoes_dia,
                'duracao_maxima_sessao_minutos': limites.duracao_maxima_sessao_minutos,
                'limite_questoes_por_sessao': limites.limite_questoes_por_sessao,
                'limite_questoes_dia': limites.limite_questoes_dia,
                'limite_consultas_dia': limites.limite_consultas_dia,
                'limite_peca_mes': limites.limite_peca_mes,
                'permite_estudo_continuo': limites.permite_estudo_continuo,
                'permite_sessao_estendida': limites.permite_sessao_estendida,
                'sessoes_extras_condicionais': limites.sessoes_extras_condicionais,
                'acesso_relatorio_tipo': limites.acesso_relatorio_tipo,
                'acesso_modo_pedagogico': limites.acesso_modo_pedagogico,
                'acesso_analytics': limites.acesso_analytics,
                'acesso_jurisprudencia': limites.acesso_jurisprudencia
            }
        )

        # Reabilitar trigger
        session.execute(text("ALTER TABLE plano ENABLE TRIGGER trigger_plano_updated_at"))

        if result.rowcount > 0:
            logger.info(f"✓ Limites aplicados ao plano {codigo_plano}")
            session.commit()
            return True
        else:
            logger.warning(f"Plano {codigo_plano} não encontrado")
            return False

    except Exception as e:
        session.rollback()
        logger.error(f"Erro ao aplicar limites ao plano {codigo_plano}: {e}")
        return False


def exibir_resumo_limites(session):
    """Exibe resumo dos limites configurados."""
    logger.info("\n" + "=" * 100)
    logger.info("RESUMO DOS LIMITES - ETAPA 14.2 CONCLUÍDA")
    logger.info("=" * 100)

    result = session.execute(
        text("""
            SELECT
                codigo, nome,
                limite_sessoes_dia,
                duracao_maxima_sessao_minutos,
                limite_questoes_por_sessao,
                limite_questoes_dia,
                limite_peca_mes,
                permite_estudo_continuo,
                permite_sessao_estendida,
                sessoes_extras_condicionais,
                acesso_relatorio_tipo
            FROM plano
            WHERE ativo = true
            ORDER BY CASE
                WHEN codigo = 'FREE' THEN 1
                WHEN codigo = 'OAB_MENSAL' THEN 2
                WHEN codigo = 'OAB_SEMESTRAL' THEN 3
                ELSE 4
            END
        """)
    )

    for row in result:
        logger.info(f"\n📋 {row[0]} - {row[1]}")
        logger.info(f"   Sessões por dia: {row[2]}")
        logger.info(f"   Duração máxima: {row[3]} minutos")
        logger.info(f"   Questões por sessão: {row[4]}")
        logger.info(f"   Questões por dia (total): {row[5]}")
        logger.info(f"   Peças por mês: {row[6]}")
        logger.info(f"   Estudo contínuo: {'Sim' if row[7] else 'Não'}")
        logger.info(f"   Sessão estendida: {'Sim' if row[8] else 'Não'}")

        if row[9] > 0:
            logger.info(f"   Sessões extras (condicional): +{row[9]}")

        logger.info(f"   Relatórios: {row[10]}")

    logger.info("\n" + "=" * 100)
    logger.info("\n✅ Limites configurados com base em princípios pedagógicos")
    logger.info("✅ Heavy users do plano Semestral não serão frustrados")
    logger.info("✅ Sessões longas não consomem sessão adicional (Semestral)")
    logger.info("=" * 100 + "\n")


def main():
    """Função principal."""
    logger.info("=" * 100)
    logger.info("ETAPA 14.2 - DEFINIÇÃO DE LIMITES POR PLANO")
    logger.info("=" * 100)
    logger.info("Definindo limites operacionais técnicos reais...\n")

    # Conecta ao database
    try:
        Session = conectar_database()
        session = Session()
        logger.info("✓ Conectado ao database\n")
    except Exception as e:
        logger.error(f"Erro ao conectar ao database: {e}")
        sys.exit(1)

    # Define limites para cada plano
    sucesso = True

    sucesso &= aplicar_limites_plano(session, 'FREE', get_limites_free())
    sucesso &= aplicar_limites_plano(session, 'OAB_MENSAL', get_limites_oab_mensal())
    sucesso &= aplicar_limites_plano(session, 'OAB_SEMESTRAL', get_limites_oab_semestral())

    # Exibe resumo
    if sucesso:
        exibir_resumo_limites(session)
        logger.info("✅ ETAPA 14.2 CONCLUÍDA COM SUCESSO")
    else:
        logger.error("❌ ETAPA 14.2 CONCLUÍDA COM ERROS")
        sys.exit(1)

    session.close()


if __name__ == "__main__":
    main()
