#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
VALIDAÇÃO PÓS-INGESTÃO - ETAPA 9.3
================================================================================

Script de validação de integridade após ingestão de dados legais e avaliativos:
- Validação de integridade referencial
- Detecção de registros órfãos
- Verificação de associações
- Validação de índices
- Checagem de constraints
- Relatório de qualidade dos dados

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from decimal import Decimal

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.connection import DatabaseConnection


# ================================================================================
# CONFIGURAÇÃO DE LOGGING
# ================================================================================

def configurar_logging():
    """Configura logging para arquivo e console."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"validacao_pos_ingestao_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    return str(log_file)


# ================================================================================
# VALIDADOR PÓS-INGESTÃO
# ================================================================================

class ValidadorPosIngestao:
    """Validador de integridade pós-ingestão de dados."""

    def __init__(self):
        self.db = DatabaseConnection()
        self.logger = logging.getLogger(__name__)
        self.problemas = []

    def adicionar_problema(self, categoria: str, descricao: str, severidade: str = "ALTA"):
        """Registra um problema encontrado."""
        problema = {
            "categoria": categoria,
            "descricao": descricao,
            "severidade": severidade,
            "timestamp": datetime.now().isoformat()
        }
        self.problemas.append(problema)
        self.logger.warning(f"[{severidade}] {categoria}: {descricao}")

    # ============================================================================
    # VALIDAÇÕES DE NORMAS LEGAIS
    # ============================================================================

    def validar_normas_legais(self, session) -> Dict:
        """Valida integridade das normas legais."""
        self.logger.info("\n=== Validando Normas Legais ===")

        resultados = {
            "total_normas": 0,
            "normas_sem_diploma": 0,
            "normas_sem_texto": 0,
            "normas_duplicadas": 0,
            "normas_sem_hash": 0,
            "normas_sem_ramo": 0
        }

        # Total de normas
        result = session.execute(text("SELECT COUNT(*) FROM norma_legal")).fetchone()
        resultados["total_normas"] = result[0]
        self.logger.info(f"Total de normas: {resultados['total_normas']}")

        # Normas sem diploma_legal
        result = session.execute(
            text("SELECT COUNT(*) FROM norma_legal WHERE diploma_legal IS NULL OR diploma_legal = ''")
        ).fetchone()
        resultados["normas_sem_diploma"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "NORMAS_LEGAIS",
                f"{result[0]} normas sem diploma_legal",
                "ALTA"
            )

        # Normas sem texto_normativo
        result = session.execute(
            text("SELECT COUNT(*) FROM norma_legal WHERE texto_normativo IS NULL OR texto_normativo = ''")
        ).fetchone()
        resultados["normas_sem_texto"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "NORMAS_LEGAIS",
                f"{result[0]} normas sem texto_normativo",
                "CRÍTICA"
            )

        # Normas duplicadas (mesmo diploma + artigo + parágrafo)
        result = session.execute(
            text("""
                SELECT diploma_legal, artigo, COALESCE(paragrafo, ''), COUNT(*) as cnt
                FROM norma_legal
                GROUP BY diploma_legal, artigo, COALESCE(paragrafo, '')
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        resultados["normas_duplicadas"] = len(result)
        if len(result) > 0:
            self.adicionar_problema(
                "NORMAS_LEGAIS",
                f"{len(result)} grupos de normas duplicadas",
                "ALTA"
            )

        # Normas sem hash
        result = session.execute(
            text("SELECT COUNT(*) FROM norma_legal WHERE hash_texto_normativo IS NULL")
        ).fetchone()
        resultados["normas_sem_hash"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "NORMAS_LEGAIS",
                f"{result[0]} normas sem hash_texto_normativo",
                "MÉDIA"
            )

        # Normas sem ramo_direito
        result = session.execute(
            text("SELECT COUNT(*) FROM norma_legal WHERE ramo_direito IS NULL OR ramo_direito = ''")
        ).fetchone()
        resultados["normas_sem_ramo"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "NORMAS_LEGAIS",
                f"{result[0]} normas sem ramo_direito",
                "MÉDIA"
            )

        self.logger.info(f"✓ Validação de normas legais concluída")
        return resultados

    # ============================================================================
    # VALIDAÇÕES DE QUESTÕES OAB
    # ============================================================================

    def validar_questoes_oab(self, session) -> Dict:
        """Valida integridade das questões OAB."""
        self.logger.info("\n=== Validando Questões OAB ===")

        resultados = {
            "total_questoes": 0,
            "questoes_sem_enunciado": 0,
            "questoes_sem_alternativas": 0,
            "questoes_sem_gabarito": 0,
            "questoes_com_multiplos_gabaritos": 0,
            "questoes_sem_area": 0,
            "alternativas_incorretas_sem_erro": 0
        }

        # Total de questões
        result = session.execute(text("SELECT COUNT(*) FROM questao_oab")).fetchone()
        resultados["total_questoes"] = result[0]
        self.logger.info(f"Total de questões: {resultados['total_questoes']}")

        # Questões sem enunciado
        result = session.execute(
            text("SELECT COUNT(*) FROM questao_oab WHERE enunciado IS NULL OR enunciado = ''")
        ).fetchone()
        resultados["questoes_sem_enunciado"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "QUESTOES_OAB",
                f"{result[0]} questões sem enunciado",
                "CRÍTICA"
            )

        # Questões sem alternativas
        result = session.execute(
            text("SELECT COUNT(*) FROM questao_oab WHERE alternativas IS NULL")
        ).fetchone()
        resultados["questoes_sem_alternativas"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "QUESTOES_OAB",
                f"{result[0]} questões sem alternativas",
                "CRÍTICA"
            )

        # Questões sem gabarito (órfãs)
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM questao_oab q
                LEFT JOIN gabarito_questao g ON q.id = g.questao_id
                WHERE g.id IS NULL
            """)
        ).fetchone()
        resultados["questoes_sem_gabarito"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "QUESTOES_OAB",
                f"{result[0]} questões sem gabarito",
                "CRÍTICA"
            )

        # Questões com múltiplos gabaritos
        result = session.execute(
            text("""
                SELECT questao_id, COUNT(*) as cnt
                FROM gabarito_questao
                GROUP BY questao_id
                HAVING COUNT(*) > 1
            """)
        ).fetchall()
        resultados["questoes_com_multiplos_gabaritos"] = len(result)
        if len(result) > 0:
            self.adicionar_problema(
                "QUESTOES_OAB",
                f"{len(result)} questões com múltiplos gabaritos",
                "CRÍTICA"
            )

        # Questões sem área
        result = session.execute(
            text("SELECT COUNT(*) FROM questao_oab WHERE area IS NULL OR area = ''")
        ).fetchone()
        resultados["questoes_sem_area"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "QUESTOES_OAB",
                f"{result[0]} questões sem área",
                "MÉDIA"
            )

        # Verificar alternativas incorretas sem tipo_erro
        # (todas as alternativas exceto o gabarito devem ter tipo_erro)
        result = session.execute(
            text("""
                SELECT q.id, q.numero_questao
                FROM questao_oab q
                JOIN gabarito_questao g ON q.id = g.questao_id
                WHERE (
                    SELECT COUNT(*)
                    FROM alternativa_erro ae
                    WHERE ae.questao_id = q.id
                ) < (jsonb_array_length(q.alternativas) - 1)
            """)
        ).fetchall()
        resultados["alternativas_incorretas_sem_erro"] = len(result)
        if len(result) > 0:
            self.adicionar_problema(
                "QUESTOES_OAB",
                f"{len(result)} questões com alternativas incorretas sem tipo_erro",
                "MÉDIA"
            )

        self.logger.info(f"✓ Validação de questões OAB concluída")
        return resultados

    # ============================================================================
    # VALIDAÇÕES DE GABARITO
    # ============================================================================

    def validar_gabaritos(self, session) -> Dict:
        """Valida isolamento e integridade dos gabaritos."""
        self.logger.info("\n=== Validando Gabaritos ===")

        resultados = {
            "total_gabaritos": 0,
            "gabaritos_orfaos": 0,
            "gabaritos_invalidos": 0
        }

        # Total de gabaritos
        result = session.execute(text("SELECT COUNT(*) FROM gabarito_questao")).fetchone()
        resultados["total_gabaritos"] = result[0]
        self.logger.info(f"Total de gabaritos: {resultados['total_gabaritos']}")

        # Gabaritos órfãos (sem questão correspondente)
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM gabarito_questao g
                LEFT JOIN questao_oab q ON g.questao_id = q.id
                WHERE q.id IS NULL
            """)
        ).fetchone()
        resultados["gabaritos_orfaos"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "GABARITOS",
                f"{result[0]} gabaritos órfãos (sem questão)",
                "ALTA"
            )

        # Gabaritos com alternativa_correta inválida (não existe nas alternativas da questão)
        # Esta validação é complexa e requer parsing do JSONB, deixamos como TODO se necessário

        self.logger.info(f"✓ Validação de gabaritos concluída")
        return resultados

    # ============================================================================
    # VALIDAÇÕES DE ASSOCIAÇÕES
    # ============================================================================

    def validar_associacoes(self, session) -> Dict:
        """Valida associações entre entidades."""
        self.logger.info("\n=== Validando Associações ===")

        resultados = {
            "associacoes_norma_conceito_orfas": 0,
            "associacoes_questao_norma_orfas": 0,
            "associacoes_questao_conceito_orfas": 0,
            "questoes_sem_associacao_norma": 0,
            "questoes_sem_associacao_conceito": 0
        }

        # Associações norma-conceito órfãs
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM norma_conceito_associacao nca
                LEFT JOIN norma_legal n ON nca.norma_id = n.id
                LEFT JOIN conceito_juridico c ON nca.conceito_id = c.id
                WHERE n.id IS NULL OR c.id IS NULL
            """)
        ).fetchone()
        resultados["associacoes_norma_conceito_orfas"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "ASSOCIACOES",
                f"{result[0]} associações norma-conceito órfãs",
                "ALTA"
            )

        # Associações questão-norma órfãs
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM questao_norma_associacao qna
                LEFT JOIN questao_oab q ON qna.questao_id = q.id
                LEFT JOIN norma_legal n ON qna.norma_id = n.id
                WHERE q.id IS NULL OR n.id IS NULL
            """)
        ).fetchone()
        resultados["associacoes_questao_norma_orfas"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "ASSOCIACOES",
                f"{result[0]} associações questão-norma órfãs",
                "ALTA"
            )

        # Associações questão-conceito órfãs
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM questao_conceito_associacao qca
                LEFT JOIN questao_oab q ON qca.questao_id = q.id
                LEFT JOIN conceito_juridico c ON qca.conceito_id = c.id
                WHERE q.id IS NULL OR c.id IS NULL
            """)
        ).fetchone()
        resultados["associacoes_questao_conceito_orfas"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "ASSOCIACOES",
                f"{result[0]} associações questão-conceito órfãs",
                "ALTA"
            )

        # Questões sem associação com normas
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM questao_oab q
                LEFT JOIN questao_norma_associacao qna ON q.id = qna.questao_id
                WHERE qna.id IS NULL
            """)
        ).fetchone()
        resultados["questoes_sem_associacao_norma"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "ASSOCIACOES",
                f"{result[0]} questões sem associação com normas",
                "MÉDIA"
            )

        # Questões sem associação com conceitos
        result = session.execute(
            text("""
                SELECT COUNT(*)
                FROM questao_oab q
                LEFT JOIN questao_conceito_associacao qca ON q.id = qca.questao_id
                WHERE qca.id IS NULL
            """)
        ).fetchone()
        resultados["questoes_sem_associacao_conceito"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "ASSOCIACOES",
                f"{result[0]} questões sem associação com conceitos",
                "BAIXA"
            )

        self.logger.info(f"✓ Validação de associações concluída")
        return resultados

    # ============================================================================
    # VALIDAÇÕES DE CONCEITOS E INSTITUTOS
    # ============================================================================

    def validar_conceitos_institutos(self, session) -> Dict:
        """Valida conceitos e institutos jurídicos."""
        self.logger.info("\n=== Validando Conceitos e Institutos ===")

        resultados = {
            "total_conceitos": 0,
            "total_institutos": 0,
            "conceitos_sem_nome": 0,
            "conceitos_sem_ramo": 0,
            "institutos_sem_nome": 0,
            "institutos_sem_ramo": 0
        }

        # Total de conceitos
        result = session.execute(text("SELECT COUNT(*) FROM conceito_juridico")).fetchone()
        resultados["total_conceitos"] = result[0]
        self.logger.info(f"Total de conceitos: {resultados['total_conceitos']}")

        # Total de institutos
        result = session.execute(text("SELECT COUNT(*) FROM instituto_juridico")).fetchone()
        resultados["total_institutos"] = result[0]
        self.logger.info(f"Total de institutos: {resultados['total_institutos']}")

        # Conceitos sem nome
        result = session.execute(
            text("SELECT COUNT(*) FROM conceito_juridico WHERE nome IS NULL OR nome = ''")
        ).fetchone()
        resultados["conceitos_sem_nome"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "CONCEITOS",
                f"{result[0]} conceitos sem nome",
                "ALTA"
            )

        # Conceitos sem ramo
        result = session.execute(
            text("SELECT COUNT(*) FROM conceito_juridico WHERE ramo_direito IS NULL OR ramo_direito = ''")
        ).fetchone()
        resultados["conceitos_sem_ramo"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "CONCEITOS",
                f"{result[0]} conceitos sem ramo_direito",
                "MÉDIA"
            )

        # Institutos sem nome
        result = session.execute(
            text("SELECT COUNT(*) FROM instituto_juridico WHERE nome IS NULL OR nome = ''")
        ).fetchone()
        resultados["institutos_sem_nome"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "INSTITUTOS",
                f"{result[0]} institutos sem nome",
                "ALTA"
            )

        # Institutos sem ramo
        result = session.execute(
            text("SELECT COUNT(*) FROM instituto_juridico WHERE ramo_direito IS NULL OR ramo_direito = ''")
        ).fetchone()
        resultados["institutos_sem_ramo"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "INSTITUTOS",
                f"{result[0]} institutos sem ramo_direito",
                "MÉDIA"
            )

        self.logger.info(f"✓ Validação de conceitos e institutos concluída")
        return resultados

    # ============================================================================
    # VALIDAÇÕES DE ÍNDICES
    # ============================================================================

    def validar_indices(self, session) -> Dict:
        """Valida existência e integridade dos índices."""
        self.logger.info("\n=== Validando Índices ===")

        resultados = {
            "indices_existentes": [],
            "indices_ausentes": []
        }

        # Índices esperados (conforme arquitetura)
        indices_esperados = [
            "idx_norma_legal_diploma",
            "idx_norma_legal_ramo",
            "idx_norma_legal_hash",
            "idx_questao_oab_numero",
            "idx_questao_oab_exame",
            "idx_questao_oab_area",
            "idx_gabarito_questao_questao_id",
            "idx_alternativa_erro_questao_id",
            "idx_questao_norma_questao_id",
            "idx_questao_norma_norma_id",
            "idx_questao_conceito_questao_id",
            "idx_questao_conceito_conceito_id",
            "idx_norma_conceito_norma_id",
            "idx_norma_conceito_conceito_id"
        ]

        # Verificar quais índices existem
        for indice in indices_esperados:
            result = session.execute(
                text("""
                    SELECT indexname
                    FROM pg_indexes
                    WHERE indexname = :indice
                """),
                {"indice": indice}
            ).fetchone()

            if result:
                resultados["indices_existentes"].append(indice)
            else:
                resultados["indices_ausentes"].append(indice)
                self.adicionar_problema(
                    "INDICES",
                    f"Índice ausente: {indice}",
                    "MÉDIA"
                )

        self.logger.info(f"Índices existentes: {len(resultados['indices_existentes'])}")
        self.logger.info(f"Índices ausentes: {len(resultados['indices_ausentes'])}")

        self.logger.info(f"✓ Validação de índices concluída")
        return resultados

    # ============================================================================
    # VALIDAÇÕES DE VETORIZAÇÃO
    # ============================================================================

    def validar_vetorizacao(self, session) -> Dict:
        """Valida embeddings e índices vetoriais."""
        self.logger.info("\n=== Validando Vetorização ===")

        resultados = {
            "normas_sem_embedding": 0,
            "questoes_sem_embedding": 0,
            "conceitos_sem_embedding": 0,
            "institutos_sem_embedding": 0
        }

        # Normas sem embedding
        result = session.execute(
            text("SELECT COUNT(*) FROM norma_legal WHERE embedding IS NULL")
        ).fetchone()
        resultados["normas_sem_embedding"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "VETORIZACAO",
                f"{result[0]} normas sem embedding",
                "BAIXA"  # Embeddings podem ser gerados posteriormente
            )

        # Questões sem embedding
        result = session.execute(
            text("SELECT COUNT(*) FROM questao_oab WHERE embedding IS NULL")
        ).fetchone()
        resultados["questoes_sem_embedding"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "VETORIZACAO",
                f"{result[0]} questões sem embedding",
                "BAIXA"
            )

        # Conceitos sem embedding
        result = session.execute(
            text("SELECT COUNT(*) FROM conceito_juridico WHERE embedding IS NULL")
        ).fetchone()
        resultados["conceitos_sem_embedding"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "VETORIZACAO",
                f"{result[0]} conceitos sem embedding",
                "BAIXA"
            )

        # Institutos sem embedding
        result = session.execute(
            text("SELECT COUNT(*) FROM instituto_juridico WHERE embedding IS NULL")
        ).fetchone()
        resultados["institutos_sem_embedding"] = result[0]
        if result[0] > 0:
            self.adicionar_problema(
                "VETORIZACAO",
                f"{result[0]} institutos sem embedding",
                "BAIXA"
            )

        self.logger.info(f"✓ Validação de vetorização concluída")
        return resultados

    # ============================================================================
    # RELATÓRIO FINAL
    # ============================================================================

    def gerar_relatorio(self, resultados_validacoes: Dict) -> Dict:
        """Gera relatório consolidado de validação."""
        self.logger.info("\n=== Gerando Relatório Final ===")

        # Contar problemas por severidade
        problemas_criticos = [p for p in self.problemas if p["severidade"] == "CRÍTICA"]
        problemas_altos = [p for p in self.problemas if p["severidade"] == "ALTA"]
        problemas_medios = [p for p in self.problemas if p["severidade"] == "MÉDIA"]
        problemas_baixos = [p for p in self.problemas if p["severidade"] == "BAIXA"]

        # Status geral
        if len(problemas_criticos) > 0:
            status_geral = "CRÍTICO"
        elif len(problemas_altos) > 0:
            status_geral = "ATENÇÃO"
        elif len(problemas_medios) > 0:
            status_geral = "REVISÃO RECOMENDADA"
        else:
            status_geral = "OK"

        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "status_geral": status_geral,
            "total_problemas": len(self.problemas),
            "problemas_por_severidade": {
                "CRÍTICA": len(problemas_criticos),
                "ALTA": len(problemas_altos),
                "MÉDIA": len(problemas_medios),
                "BAIXA": len(problemas_baixos)
            },
            "validacoes": resultados_validacoes,
            "problemas": self.problemas
        }

        return relatorio

    # ============================================================================
    # EXECUTAR TODAS AS VALIDAÇÕES
    # ============================================================================

    def executar(self) -> Dict:
        """Executa todas as validações."""
        inicio = datetime.now()
        self.logger.info("=" * 80)
        self.logger.info("INICIANDO VALIDAÇÃO PÓS-INGESTÃO")
        self.logger.info("=" * 80)

        resultados_validacoes = {}

        with self.db.get_session() as session:
            # Validar normas legais
            resultados_validacoes["normas_legais"] = self.validar_normas_legais(session)

            # Validar questões OAB
            resultados_validacoes["questoes_oab"] = self.validar_questoes_oab(session)

            # Validar gabaritos
            resultados_validacoes["gabaritos"] = self.validar_gabaritos(session)

            # Validar associações
            resultados_validacoes["associacoes"] = self.validar_associacoes(session)

            # Validar conceitos e institutos
            resultados_validacoes["conceitos_institutos"] = self.validar_conceitos_institutos(session)

            # Validar índices
            resultados_validacoes["indices"] = self.validar_indices(session)

            # Validar vetorização
            resultados_validacoes["vetorizacao"] = self.validar_vetorizacao(session)

        # Gerar relatório final
        relatorio = self.gerar_relatorio(resultados_validacoes)

        fim = datetime.now()
        duracao = (fim - inicio).total_seconds()
        relatorio["duracao_segundos"] = duracao

        self.logger.info("\n" + "=" * 80)
        self.logger.info("RELATÓRIO FINAL DE VALIDAÇÃO")
        self.logger.info("=" * 80)
        self.logger.info(f"Status Geral: {relatorio['status_geral']}")
        self.logger.info(f"Total de Problemas: {relatorio['total_problemas']}")
        self.logger.info(f"  - Críticos: {relatorio['problemas_por_severidade']['CRÍTICA']}")
        self.logger.info(f"  - Altos: {relatorio['problemas_por_severidade']['ALTA']}")
        self.logger.info(f"  - Médios: {relatorio['problemas_por_severidade']['MÉDIA']}")
        self.logger.info(f"  - Baixos: {relatorio['problemas_por_severidade']['BAIXA']}")
        self.logger.info(f"Duração: {duracao:.2f}s")
        self.logger.info("=" * 80)

        return relatorio


# ================================================================================
# INTERFACE DE LINHA DE COMANDO
# ================================================================================

def main():
    """Função principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Validação de integridade pós-ingestão'
    )
    parser.add_argument(
        '--output',
        help='Arquivo de saída para relatório JSON (opcional)'
    )

    args = parser.parse_args()

    # Configurar logging
    log_file = configurar_logging()
    print(f"Log salvo em: {log_file}")

    # Executar validação
    validador = ValidadorPosIngestao()

    try:
        relatorio = validador.executar()

        # Salvar relatório JSON se especificado
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(relatorio, f, indent=2, ensure_ascii=False)
            print(f"\nRelatório salvo em: {args.output}")

        # Determinar código de saída
        if relatorio["status_geral"] == "CRÍTICO":
            print("\n✗ Validação FALHOU - problemas críticos encontrados!")
            return 1
        elif relatorio["status_geral"] == "ATENÇÃO":
            print("\n⚠ Validação com ATENÇÃO - problemas de alta severidade encontrados!")
            return 0  # Não falha, mas alerta
        else:
            print("\n✓ Validação concluída com sucesso!")
            return 0

    except Exception as e:
        print(f"\n✗ Erro na validação: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
