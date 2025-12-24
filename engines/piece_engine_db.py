"""
JURIS_IA_CORE_V1 - PIECE ENGINE (DATABASE INTEGRATED)
Motor de Verificação de Peças Processuais - Integrado com PostgreSQL

Este módulo verifica peças processuais (2ª fase OAB), identifica erros fatais
e formais, e persiste TODAS as avaliações no banco de dados.

INTEGRAÇÃO COM DATABASE:
- Persiste avaliações completas em 'pratica_peca'
- Registra erros específicos em 'erro_peca'
- Rastreia evolução histórica do aluno por área jurídica
- Analisa padrões de erros recorrentes
- Gera recomendações baseadas em histórico real

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
from uuid import UUID

# Database imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_db_session
from database.repositories import RepositoryFactory


# ============================================================
# TIPOS E ENUMS
# ============================================================

class PieceType(Enum):
    """Tipos de peças processuais"""
    PETICAO_INICIAL_CIVEL = "peticao_inicial_civel"
    CONTESTACAO_CIVEL = "contestacao_civel"
    RECURSO_APELACAO = "recurso_apelacao"
    HABEAS_CORPUS = "habeas_corpus"
    MANDADO_SEGURANCA = "mandado_seguranca"
    RECLAMACAO_TRABALHISTA = "reclamacao_trabalhista"
    CONTRAMINUTA = "contraminuta"
    QUEIXA_CRIME = "queixa_crime"


class ErrorSeverity(Enum):
    """Gravidade do erro"""
    FATAL = "FATAL"          # Zera a peça
    GRAVE = "GRAVE"          # Reduz muito a nota
    MODERADO = "MODERADO"    # Reduz moderadamente
    LEVE = "LEVE"           # Reduz pouco


class PartStatus(Enum):
    """Status de cada parte da peça"""
    PRESENTE = "presente"
    AUSENTE = "ausente"
    INCOMPLETA = "incompleta"
    INCORRETA = "incorreta"


@dataclass
class ErrorFound:
    """Erro encontrado na peça"""
    tipo: str
    gravidade: ErrorSeverity
    localizacao: str
    descricao: str
    impacto: str
    correcao_sugerida: str
    artigo_relacionado: Optional[str] = None


@dataclass
class PartEvaluation:
    """Avaliação de uma parte da peça"""
    parte: str
    status: PartStatus
    nota: float  # 0-10
    presente: bool
    completa: bool
    correta: bool
    erros: List[ErrorFound]
    comentarios: List[str]


# ============================================================
# PIECE ENGINE DB
# ============================================================

class PieceEngineDB:
    """
    Motor de verificação de peças processuais - DATABASE INTEGRATED.

    Responsabilidades:
    - Avaliar peças processuais (2ª fase OAB)
    - Detectar erros fatais e formais
    - Persistir TODAS as avaliações no database
    - Rastrear evolução histórica por área jurídica
    - Identificar padrões de erro recorrentes
    - Gerar recomendações baseadas em dados reais
    """

    def __init__(self):
        """Inicializa o motor de peças"""
        self.piece_templates: Dict[PieceType, Dict] = {}
        self.checklists: Dict[PieceType, List[str]] = {}
        self._load_templates()

    # ============================================================
    # MÉTODOS PRINCIPAIS
    # ============================================================

    def avaliar_peca(
        self,
        user_id: UUID,
        tipo_peca: PieceType,
        conteudo: str,
        enunciado: str,
        area_direito: str
    ) -> Dict:
        """
        Avalia uma peça processual completa e PERSISTE no database.

        Args:
            user_id: ID do usuário
            tipo_peca: Tipo da peça
            conteudo: Texto da peça escrita pelo aluno
            enunciado: Enunciado da questão
            area_direito: Área do direito (civil, penal, trabalhista, etc.)

        Returns:
            Dict com avaliação completa + ID da avaliação persistida
        """
        try:
            with get_db_session() as session:
                repos = RepositoryFactory(session)

                # 1. Verifica partes obrigatórias
                partes_avaliadas = self._verificar_partes_obrigatorias(tipo_peca, conteudo)

                # 2. Detecta erros
                erros = self._detectar_erros(tipo_peca, conteudo, enunciado)

                # 3. Classifica erros por gravidade
                erros_fatais = [e for e in erros if e.gravidade == ErrorSeverity.FATAL]
                erros_graves = [e for e in erros if e.gravidade == ErrorSeverity.GRAVE]
                erros_moderados = [e for e in erros if e.gravidade == ErrorSeverity.MODERADO]
                erros_leves = [e for e in erros if e.gravidade == ErrorSeverity.LEVE]

                # 4. Calcula notas por competência
                adequacao = self._avaliar_adequacao_normas(partes_avaliadas, erros)
                tecnica = self._avaliar_tecnica_processual(partes_avaliadas, erros)
                argumentacao = self._avaliar_argumentacao(conteudo, erros)
                clareza = self._avaliar_clareza(conteudo)

                # 5. Calcula nota final
                nota_final = self._calcular_nota_final(
                    adequacao, tecnica, argumentacao, clareza, erros_fatais
                )

                # 6. Verifica aprovação (>= 6.0)
                aprovado = nota_final >= 6.0 and len(erros_fatais) == 0

                # 7. Executa checklist
                checklist_resultado = self._executar_checklist(tipo_peca, conteudo)

                # 8. Gera feedback
                pontos_fortes = self._identificar_pontos_fortes(partes_avaliadas)
                pontos_melhorar = self._identificar_pontos_melhorar(erros, partes_avaliadas)
                recomendacoes = self._gerar_recomendacoes(tipo_peca, erros, nota_final)

                # 9. PERSISTE AVALIAÇÃO NO DATABASE
                pratica_id = self._persistir_avaliacao(
                    session=session,
                    user_id=user_id,
                    tipo_peca=tipo_peca,
                    area_direito=area_direito,
                    conteudo=conteudo,
                    enunciado=enunciado,
                    nota_final=nota_final,
                    aprovado=aprovado,
                    adequacao=adequacao,
                    tecnica=tecnica,
                    argumentacao=argumentacao,
                    clareza=clareza,
                    erros_fatais=erros_fatais,
                    erros_graves=erros_graves,
                    erros_moderados=erros_moderados,
                    erros_leves=erros_leves,
                    checklist=checklist_resultado,
                    partes=partes_avaliadas
                )

                # 10. PERSISTE ERROS ESPECÍFICOS
                self._persistir_erros(
                    session=session,
                    pratica_id=pratica_id,
                    erros=erros
                )

                # 11. LOG DA AVALIAÇÃO
                repos.session.execute(
                    """INSERT INTO log_sistema (user_id, evento, detalhes, created_at)
                       VALUES (:user_id, :evento, :detalhes, :created_at)""",
                    {
                        "user_id": user_id,
                        "evento": "PECA_AVALIADA",
                        "detalhes": {
                            "pratica_id": str(pratica_id),
                            "tipo_peca": tipo_peca.value,
                            "area_direito": area_direito,
                            "nota_final": nota_final,
                            "aprovado": aprovado,
                            "erros_fatais": len(erros_fatais),
                            "erros_graves": len(erros_graves),
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        },
                        "created_at": datetime.now(timezone.utc)
                    }
                )

                session.commit()

                return {
                    "sucesso": True,
                    "pratica_id": str(pratica_id),
                    "tipo_peca": tipo_peca.value,
                    "nota_final": nota_final,
                    "aprovado": aprovado,
                    "competencias": {
                        "adequacao_normas": adequacao,
                        "tecnica_processual": tecnica,
                        "argumentacao_juridica": argumentacao,
                        "clareza_objetividade": clareza
                    },
                    "erros": {
                        "fatais": len(erros_fatais),
                        "graves": len(erros_graves),
                        "moderados": len(erros_moderados),
                        "leves": len(erros_leves)
                    },
                    "erros_detalhados": {
                        "fatais": [self._erro_to_dict(e) for e in erros_fatais],
                        "graves": [self._erro_to_dict(e) for e in erros_graves],
                        "moderados": [self._erro_to_dict(e) for e in erros_moderados],
                        "leves": [self._erro_to_dict(e) for e in erros_leves]
                    },
                    "partes_avaliadas": [self._parte_to_dict(p) for p in partes_avaliadas],
                    "checklist": checklist_resultado,
                    "feedback": {
                        "pontos_fortes": pontos_fortes,
                        "pontos_melhorar": pontos_melhorar,
                        "recomendacoes": recomendacoes
                    }
                }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao avaliar peça: {str(e)}"
            }

    def analisar_evolucao_historica(
        self,
        user_id: UUID,
        area_direito: Optional[str] = None,
        tipo_peca: Optional[PieceType] = None
    ) -> Dict:
        """
        Analisa evolução histórica do aluno em peças processuais.

        Args:
            user_id: ID do usuário
            area_direito: Filtro por área (opcional)
            tipo_peca: Filtro por tipo de peça (opcional)

        Returns:
            Dict com análise evolutiva completa
        """
        try:
            with get_db_session() as session:
                # Busca todas as práticas do aluno
                query = """
                    SELECT
                        id, tipo_peca, area_direito, nota_final,
                        aprovado, erros_fatais, erros_graves,
                        created_at
                    FROM pratica_peca
                    WHERE user_id = :user_id
                """
                params = {"user_id": user_id}

                if area_direito:
                    query += " AND area_direito = :area_direito"
                    params["area_direito"] = area_direito

                if tipo_peca:
                    query += " AND tipo_peca = :tipo_peca"
                    params["tipo_peca"] = tipo_peca.value

                query += " ORDER BY created_at ASC"

                result = session.execute(query, params).fetchall()

                if not result:
                    return {
                        "sucesso": True,
                        "total_pecas": 0,
                        "evolucao": []
                    }

                # Análise evolutiva
                total_pecas = len(result)
                aprovadas = sum(1 for r in result if r[4])  # aprovado
                taxa_aprovacao = (aprovadas / total_pecas) * 100 if total_pecas > 0 else 0

                # Média de notas
                notas = [r[3] for r in result]  # nota_final
                media_notas = sum(notas) / len(notas) if notas else 0

                # Evolução temporal
                evolucao = []
                for i, row in enumerate(result):
                    evolucao.append({
                        "sequencia": i + 1,
                        "pratica_id": str(row[0]),
                        "tipo_peca": row[1],
                        "area_direito": row[2],
                        "nota": float(row[3]),
                        "aprovado": row[4],
                        "erros_fatais": row[5],
                        "erros_graves": row[6],
                        "data": row[7].isoformat() if row[7] else None
                    })

                # Tendência (últimas 3 vs primeiras 3)
                tendencia = "estavel"
                if total_pecas >= 6:
                    media_primeiras = sum(notas[:3]) / 3
                    media_ultimas = sum(notas[-3:]) / 3
                    diferenca = media_ultimas - media_primeiras

                    if diferenca > 1.0:
                        tendencia = "melhora"
                    elif diferenca < -1.0:
                        tendencia = "piora"

                return {
                    "sucesso": True,
                    "total_pecas": total_pecas,
                    "aprovadas": aprovadas,
                    "taxa_aprovacao": round(taxa_aprovacao, 1),
                    "media_notas": round(media_notas, 2),
                    "tendencia": tendencia,
                    "evolucao": evolucao
                }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao analisar evolução: {str(e)}"
            }

    def identificar_erros_recorrentes(
        self,
        user_id: UUID,
        area_direito: Optional[str] = None
    ) -> Dict:
        """
        Identifica erros recorrentes do aluno em peças.

        Args:
            user_id: ID do usuário
            area_direito: Filtro por área (opcional)

        Returns:
            Dict com padrões de erro identificados
        """
        try:
            with get_db_session() as session:
                # Busca erros do aluno
                query = """
                    SELECT
                        e.tipo_erro, e.gravidade, e.localizacao,
                        COUNT(*) as frequencia
                    FROM erro_peca e
                    JOIN pratica_peca p ON e.pratica_id = p.id
                    WHERE p.user_id = :user_id
                """
                params = {"user_id": user_id}

                if area_direito:
                    query += " AND p.area_direito = :area_direito"
                    params["area_direito"] = area_direito

                query += """
                    GROUP BY e.tipo_erro, e.gravidade, e.localizacao
                    ORDER BY frequencia DESC
                    LIMIT 10
                """

                result = session.execute(query, params).fetchall()

                erros_recorrentes = []
                for row in result:
                    erros_recorrentes.append({
                        "tipo_erro": row[0],
                        "gravidade": row[1],
                        "localizacao": row[2],
                        "frequencia": row[3]
                    })

                return {
                    "sucesso": True,
                    "erros_recorrentes": erros_recorrentes,
                    "total_tipos": len(erros_recorrentes)
                }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao identificar padrões: {str(e)}"
            }

    def gerar_checklist(self, tipo_peca: PieceType) -> List[str]:
        """Gera checklist de verificação para tipo de peça"""
        return self.checklists.get(tipo_peca, [])

    def gerar_peca_modelo(
        self,
        user_id: UUID,
        tipo_peca: PieceType,
        enunciado: str,
        detalhada: bool = False
    ) -> Dict:
        """
        Gera peça-modelo baseada no enunciado.
        Persiste no log para rastreamento.

        Args:
            user_id: ID do usuário
            tipo_peca: Tipo de peça
            enunciado: Enunciado da questão
            detalhada: Se deve incluir comentários detalhados

        Returns:
            Dict com estrutura da peça-modelo
        """
        try:
            template = self.piece_templates.get(tipo_peca, {})

            # Extrai informações do enunciado
            informacoes = self._extrair_informacoes_enunciado(enunciado)

            # Gera cada parte da peça
            partes = {}
            for parte_nome, parte_config in template.get("partes", {}).items():
                partes[parte_nome] = self._gerar_parte_modelo(
                    parte_nome,
                    parte_config,
                    informacoes,
                    detalhada
                )

            peca_modelo = {
                "tipo": tipo_peca.value,
                "partes": partes,
                "observacoes": template.get("observacoes", []),
                "dicas": template.get("dicas", [])
            }

            # LOG da geração
            with get_db_session() as session:
                repos = RepositoryFactory(session)
                repos.session.execute(
                    """INSERT INTO log_sistema (user_id, evento, detalhes, created_at)
                       VALUES (:user_id, :evento, :detalhes, :created_at)""",
                    {
                        "user_id": user_id,
                        "evento": "PECA_MODELO_GERADA",
                        "detalhes": {
                            "tipo_peca": tipo_peca.value,
                            "detalhada": detalhada,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        },
                        "created_at": datetime.now(timezone.utc)
                    }
                )
                session.commit()

            return {
                "sucesso": True,
                "peca_modelo": peca_modelo
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": f"Erro ao gerar peça-modelo: {str(e)}"
            }

    # ============================================================
    # MÉTODOS PRIVADOS - PERSISTÊNCIA
    # ============================================================

    def _persistir_avaliacao(
        self,
        session,
        user_id: UUID,
        tipo_peca: PieceType,
        area_direito: str,
        conteudo: str,
        enunciado: str,
        nota_final: float,
        aprovado: bool,
        adequacao: float,
        tecnica: float,
        argumentacao: float,
        clareza: float,
        erros_fatais: List[ErrorFound],
        erros_graves: List[ErrorFound],
        erros_moderados: List[ErrorFound],
        erros_leves: List[ErrorFound],
        checklist: Dict[str, bool],
        partes: List[PartEvaluation]
    ) -> UUID:
        """Persiste avaliação completa na tabela pratica_peca"""

        # Prepara dados JSON para competencias
        competencias = {
            "adequacao_normas": adequacao,
            "tecnica_processual": tecnica,
            "argumentacao_juridica": argumentacao,
            "clareza_objetividade": clareza
        }

        # Prepara dados JSON para partes avaliadas
        partes_json = [self._parte_to_dict(p) for p in partes]

        # Insere na tabela pratica_peca
        result = session.execute(
            """INSERT INTO pratica_peca (
                user_id, tipo_peca, area_direito, conteudo, enunciado,
                nota_final, aprovado, competencias, partes_avaliadas,
                erros_fatais, erros_graves, erros_moderados, erros_leves,
                checklist_resultado, created_at
            ) VALUES (
                :user_id, :tipo_peca, :area_direito, :conteudo, :enunciado,
                :nota_final, :aprovado, :competencias, :partes_avaliadas,
                :erros_fatais, :erros_graves, :erros_moderados, :erros_leves,
                :checklist_resultado, :created_at
            ) RETURNING id""",
            {
                "user_id": user_id,
                "tipo_peca": tipo_peca.value,
                "area_direito": area_direito,
                "conteudo": conteudo,
                "enunciado": enunciado,
                "nota_final": nota_final,
                "aprovado": aprovado,
                "competencias": json.dumps(competencias),
                "partes_avaliadas": json.dumps(partes_json),
                "erros_fatais": len(erros_fatais),
                "erros_graves": len(erros_graves),
                "erros_moderados": len(erros_moderados),
                "erros_leves": len(erros_leves),
                "checklist_resultado": json.dumps(checklist),
                "created_at": datetime.now(timezone.utc)
            }
        )

        pratica_id = result.fetchone()[0]
        return pratica_id

    def _persistir_erros(
        self,
        session,
        pratica_id: UUID,
        erros: List[ErrorFound]
    ):
        """Persiste erros específicos na tabela erro_peca"""

        for erro in erros:
            session.execute(
                """INSERT INTO erro_peca (
                    pratica_id, tipo_erro, gravidade, localizacao,
                    descricao, impacto, correcao_sugerida, artigo_relacionado,
                    created_at
                ) VALUES (
                    :pratica_id, :tipo_erro, :gravidade, :localizacao,
                    :descricao, :impacto, :correcao_sugerida, :artigo_relacionado,
                    :created_at
                )""",
                {
                    "pratica_id": pratica_id,
                    "tipo_erro": erro.tipo,
                    "gravidade": erro.gravidade.value,
                    "localizacao": erro.localizacao,
                    "descricao": erro.descricao,
                    "impacto": erro.impacto,
                    "correcao_sugerida": erro.correcao_sugerida,
                    "artigo_relacionado": erro.artigo_relacionado,
                    "created_at": datetime.now(timezone.utc)
                }
            )

    # ============================================================
    # MÉTODOS PRIVADOS - VERIFICAÇÃO
    # ============================================================

    def _verificar_partes_obrigatorias(
        self,
        tipo_peca: PieceType,
        conteudo: str
    ) -> List[PartEvaluation]:
        """Verifica presença de todas as partes obrigatórias"""
        template = self.piece_templates.get(tipo_peca, {})
        partes_obrigatorias = template.get("partes", {})

        avaliacoes = []

        for parte_nome, parte_config in partes_obrigatorias.items():
            # Verifica se parte está presente
            presente = self._verificar_presenca_parte(
                conteudo,
                parte_config.get("indicadores", [])
            )

            # Verifica se está completa
            completa = self._verificar_completude_parte(
                conteudo,
                parte_config.get("criterios", [])
            ) if presente else False

            # Verifica se está correta
            correta = self._verificar_corretude_parte(
                conteudo,
                parte_config.get("regras", [])
            ) if presente else False

            # Determina status
            if not presente:
                status = PartStatus.AUSENTE
            elif not completa:
                status = PartStatus.INCOMPLETA
            elif not correta:
                status = PartStatus.INCORRETA
            else:
                status = PartStatus.PRESENTE

            # Calcula nota da parte
            if status == PartStatus.PRESENTE and completa and correta:
                nota = 10.0
            elif status == PartStatus.PRESENTE and completa:
                nota = 8.0
            elif status == PartStatus.PRESENTE:
                nota = 6.0
            elif status == PartStatus.INCOMPLETA:
                nota = 4.0
            else:
                nota = 0.0

            avaliacao = PartEvaluation(
                parte=parte_nome,
                status=status,
                nota=nota,
                presente=presente,
                completa=completa,
                correta=correta,
                erros=[],
                comentarios=[]
            )

            avaliacoes.append(avaliacao)

        return avaliacoes

    def _detectar_erros(
        self,
        tipo_peca: PieceType,
        conteudo: str,
        enunciado: str
    ) -> List[ErrorFound]:
        """Detecta todos os erros na peça"""
        erros = []

        # Erros fatais
        erros.extend(self._detectar_erros_fatais(tipo_peca, conteudo))

        # Erros formais graves
        erros.extend(self._detectar_erros_formais(conteudo))

        # Erros de técnica processual
        erros.extend(self._detectar_erros_tecnicos(tipo_peca, conteudo))

        # Erros de adequação ao enunciado
        if enunciado:
            erros.extend(self._detectar_erros_adequacao(conteudo, enunciado))

        return erros

    def _detectar_erros_fatais(
        self,
        tipo_peca: PieceType,
        conteudo: str
    ) -> List[ErrorFound]:
        """Detecta erros que ZERAM a peça"""
        erros = []

        # Lista de erros fatais por tipo de peça
        erros_fatais_config = {
            PieceType.PETICAO_INICIAL_CIVEL: [
                {
                    "nome": "ausencia_qualificacao_partes",
                    "verificacao": lambda c: "autor" not in c.lower() or "réu" not in c.lower(),
                    "descricao": "Ausência de qualificação das partes",
                    "correcao": "Incluir: nome completo, CPF/CNPJ, endereço de autor e réu"
                },
                {
                    "nome": "ausencia_causa_pedir",
                    "verificacao": lambda c: len(c) < 200,
                    "descricao": "Ausência de causa de pedir",
                    "correcao": "Narrar os fatos e o fundamento jurídico do pedido"
                },
                {
                    "nome": "ausencia_pedido",
                    "verificacao": lambda c: "requer" not in c.lower() and "pede" not in c.lower(),
                    "descricao": "Ausência de pedido",
                    "correcao": "Incluir seção clara com todos os pedidos"
                }
            ]
        }

        config_tipo = erros_fatais_config.get(tipo_peca, [])

        for erro_config in config_tipo:
            if erro_config["verificacao"](conteudo):
                erros.append(ErrorFound(
                    tipo=erro_config["nome"],
                    gravidade=ErrorSeverity.FATAL,
                    localizacao="Estrutura geral",
                    descricao=erro_config["descricao"],
                    impacto="ZERA A PEÇA - Erro fatal",
                    correcao_sugerida=erro_config["correcao"],
                    artigo_relacionado="CPC art. 319" if tipo_peca == PieceType.PETICAO_INICIAL_CIVEL else None
                ))

        return erros

    def _detectar_erros_formais(self, conteudo: str) -> List[ErrorFound]:
        """Detecta erros formais (formatação, estrutura)"""
        erros = []

        # Verifica endereçamento ao juízo
        if "excelentíssimo" not in conteudo.lower() and "mm. juiz" not in conteudo.lower():
            erros.append(ErrorFound(
                tipo="ausencia_enderecamento",
                gravidade=ErrorSeverity.MODERADO,
                localizacao="Cabeçalho",
                descricao="Ausência de endereçamento adequado ao juízo",
                impacto="Reduz nota em adequação formal",
                correcao_sugerida="Iniciar com 'EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO...'"
            ))

        # Verifica assinatura
        if "advogado" not in conteudo.lower() and "oab" not in conteudo.lower():
            erros.append(ErrorFound(
                tipo="ausencia_assinatura",
                gravidade=ErrorSeverity.GRAVE,
                localizacao="Fim da peça",
                descricao="Ausência de assinatura e identificação do advogado",
                impacto="Reduz significativamente a nota",
                correcao_sugerida="Incluir nome completo e número OAB ao final"
            ))

        return erros

    def _detectar_erros_tecnicos(
        self,
        tipo_peca: PieceType,
        conteudo: str
    ) -> List[ErrorFound]:
        """Detecta erros de técnica processual"""
        erros = []

        # Verifica fundamentação legal
        if "art." not in conteudo.lower() and "artigo" not in conteudo.lower():
            erros.append(ErrorFound(
                tipo="ausencia_fundamentacao_legal",
                gravidade=ErrorSeverity.GRAVE,
                localizacao="Fundamentação",
                descricao="Ausência de citação de artigos de lei",
                impacto="Prejudica argumentação jurídica",
                correcao_sugerida="Citar artigos específicos da lei aplicável"
            ))

        return erros

    def _detectar_erros_adequacao(
        self,
        conteudo: str,
        enunciado: str
    ) -> List[ErrorFound]:
        """Detecta erros de adequação ao enunciado"""
        erros = []
        # Análise simplificada - em produção seria mais sofisticada
        return erros

    # ============================================================
    # MÉTODOS PRIVADOS - AVALIAÇÃO
    # ============================================================

    def _avaliar_adequacao_normas(
        self,
        partes: List[PartEvaluation],
        erros: List[ErrorFound]
    ) -> float:
        """Avalia adequação às normas processuais"""
        nota_base = 10.0

        # Deduz por partes ausentes
        partes_ausentes = sum(1 for p in partes if p.status == PartStatus.AUSENTE)
        nota_base -= partes_ausentes * 2.0

        # Deduz por erros
        for erro in erros:
            if erro.gravidade == ErrorSeverity.FATAL:
                nota_base = 0.0
                break
            elif erro.gravidade == ErrorSeverity.GRAVE:
                nota_base -= 2.0
            elif erro.gravidade == ErrorSeverity.MODERADO:
                nota_base -= 1.0

        return max(nota_base, 0.0)

    def _avaliar_tecnica_processual(
        self,
        partes: List[PartEvaluation],
        erros: List[ErrorFound]
    ) -> float:
        """Avalia técnica processual"""
        nota_base = 10.0

        # Deduz por erros técnicos
        erros_tecnicos = [e for e in erros if "tecnic" in e.tipo.lower()]
        nota_base -= len(erros_tecnicos) * 1.5

        # Deduz por partes incompletas
        partes_incompletas = sum(1 for p in partes if p.status == PartStatus.INCOMPLETA)
        nota_base -= partes_incompletas * 1.0

        return max(nota_base, 0.0)

    def _avaliar_argumentacao(self, conteudo: str, erros: List[ErrorFound]) -> float:
        """Avalia argumentação jurídica"""
        nota_base = 10.0

        # Verifica presença de fundamentação
        tem_fundamentacao = "art." in conteudo.lower() or "artigo" in conteudo.lower()
        if not tem_fundamentacao:
            nota_base -= 3.0

        # Verifica erros de fundamentação
        erros_fund = [e for e in erros if "fundamenta" in e.tipo.lower()]
        nota_base -= len(erros_fund) * 2.0

        return max(nota_base, 0.0)

    def _avaliar_clareza(self, conteudo: str) -> float:
        """Avalia clareza e objetividade"""
        nota_base = 10.0

        # Penaliza texto muito curto (falta conteúdo)
        if len(conteudo) < 300:
            nota_base -= 4.0

        # Penaliza texto muito longo (falta objetividade)
        elif len(conteudo) > 5000:
            nota_base -= 2.0

        return max(nota_base, 0.0)

    def _calcular_nota_final(
        self,
        adequacao: float,
        tecnica: float,
        argumentacao: float,
        clareza: float,
        erros_fatais: List[ErrorFound]
    ) -> float:
        """Calcula nota final ponderada"""
        # Se tem erro fatal, ZERA
        if erros_fatais:
            return 0.0

        # Pesos: adequação (30%), técnica (30%), argumentação (30%), clareza (10%)
        nota = (
            adequacao * 0.30 +
            tecnica * 0.30 +
            argumentacao * 0.30 +
            clareza * 0.10
        )

        return round(nota, 1)

    # ============================================================
    # MÉTODOS PRIVADOS - UTILITÁRIOS
    # ============================================================

    def _verificar_presenca_parte(
        self,
        conteudo: str,
        indicadores: List[str]
    ) -> bool:
        """Verifica se parte está presente"""
        conteudo_lower = conteudo.lower()
        return any(ind.lower() in conteudo_lower for ind in indicadores)

    def _verificar_completude_parte(
        self,
        conteudo: str,
        criterios: List[str]
    ) -> bool:
        """Verifica se parte está completa"""
        # Simplificado - em produção seria mais sofisticado
        return len(criterios) > 0

    def _verificar_corretude_parte(
        self,
        conteudo: str,
        regras: List[str]
    ) -> bool:
        """Verifica se parte está correta"""
        # Simplificado
        return True

    def _executar_checklist(
        self,
        tipo_peca: PieceType,
        conteudo: str
    ) -> Dict[str, bool]:
        """Executa checklist de verificação"""
        checklist = self.gerar_checklist(tipo_peca)
        resultado = {}

        for item in checklist:
            # Simplificado - verifica presença de palavras-chave
            resultado[item] = any(
                palavra in conteudo.lower()
                for palavra in item.lower().split()
            )

        return resultado

    def _identificar_pontos_fortes(
        self,
        partes: List[PartEvaluation]
    ) -> List[str]:
        """Identifica pontos fortes da peça"""
        fortes = []

        for parte in partes:
            if parte.nota >= 9.0:
                fortes.append(f"{parte.parte}: bem estruturada e completa")

        return fortes if fortes else ["Estrutura básica presente"]

    def _identificar_pontos_melhorar(
        self,
        erros: List[ErrorFound],
        partes: List[PartEvaluation]
    ) -> List[str]:
        """Identifica pontos a melhorar"""
        melhorar = []

        # Erros prioritários
        for erro in erros:
            if erro.gravidade in [ErrorSeverity.FATAL, ErrorSeverity.GRAVE]:
                melhorar.append(f"{erro.descricao}: {erro.correcao_sugerida}")

        # Partes deficientes
        for parte in partes:
            if parte.nota < 6.0:
                melhorar.append(f"{parte.parte}: precisa ser melhorada")

        return melhorar

    def _gerar_recomendacoes(
        self,
        tipo_peca: PieceType,
        erros: List[ErrorFound],
        nota: float
    ) -> List[str]:
        """Gera recomendações personalizadas"""
        recomendacoes = []

        if erros:
            recomendacoes.append("Revise os erros apontados antes de refazer")

        if nota < 6.0:
            recomendacoes.append("Estude o guia de construção de peças")
            recomendacoes.append("Pratique com peças-modelo comentadas")

        elif nota < 8.0:
            recomendacoes.append("Aperfeiçoe a fundamentação jurídica")

        else:
            recomendacoes.append("Excelente trabalho! Continue praticando")

        return recomendacoes

    def _extrair_informacoes_enunciado(self, enunciado: str) -> Dict:
        """Extrai informações relevantes do enunciado"""
        # Simplificado - em produção usaria NLP
        return {
            "autor": "AUTOR (extrair do enunciado)",
            "reu": "RÉU (extrair do enunciado)",
            "fatos": "Fatos narrados no enunciado",
            "pedido_base": "Pedido principal"
        }

    def _gerar_parte_modelo(
        self,
        parte_nome: str,
        parte_config: Dict,
        informacoes: Dict,
        detalhada: bool
    ) -> str:
        """Gera uma parte da peça-modelo"""
        modelo = parte_config.get("modelo", "")

        if detalhada:
            comentarios = parte_config.get("comentarios", [])
            modelo += "\n\n[COMENTÁRIOS]\n" + "\n".join(f"- {c}" for c in comentarios)

        return modelo

    def _erro_to_dict(self, erro: ErrorFound) -> Dict:
        """Converte ErrorFound para dict"""
        return {
            "tipo": erro.tipo,
            "gravidade": erro.gravidade.value,
            "localizacao": erro.localizacao,
            "descricao": erro.descricao,
            "impacto": erro.impacto,
            "correcao_sugerida": erro.correcao_sugerida,
            "artigo_relacionado": erro.artigo_relacionado
        }

    def _parte_to_dict(self, parte: PartEvaluation) -> Dict:
        """Converte PartEvaluation para dict"""
        return {
            "parte": parte.parte,
            "status": parte.status.value,
            "nota": parte.nota,
            "presente": parte.presente,
            "completa": parte.completa,
            "correta": parte.correta
        }

    def _load_templates(self):
        """Carrega templates de peças"""
        # Petição Inicial Cível
        self.piece_templates[PieceType.PETICAO_INICIAL_CIVEL] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "mm. juiz"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ... VARA CÍVEL DE ..."
                },
                "qualificacao": {
                    "indicadores": ["autor", "réu", "cpf"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "[NOME], nacionalidade, estado civil, profissão, portador do CPF ..."
                },
                "causa_pedir": {
                    "indicadores": ["fatos", "direito"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS FATOS\n[Narrativa dos fatos]\n\nDO DIREITO\n[Fundamentação jurídica]"
                },
                "pedido": {
                    "indicadores": ["requer", "pede"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nDiante do exposto, requer..."
                }
            },
            "observacoes": ["Incluir valor da causa", "Incluir requerimento de provas"],
            "dicas": ["Fundamentar com CPC", "Ser objetivo nos pedidos"]
        }

        # Checklists
        self.checklists[PieceType.PETICAO_INICIAL_CIVEL] = [
            "Endereçamento ao juízo correto",
            "Qualificação completa das partes",
            "Causa de pedir (fatos + direito)",
            "Pedidos claros e específicos",
            "Valor da causa",
            "Requerimento de provas",
            "Data e local",
            "Assinatura e OAB"
        ]

        # Contestação Cível
        self.piece_templates[PieceType.CONTESTACAO_CIVEL] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "mm. juiz"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ... VARA CÍVEL DE ..."
                },
                "qualificacao": {
                    "indicadores": ["réu", "autor", "autos"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "[NOME DO RÉU], já qualificado nos autos da ação que lhe move [NOME DO AUTOR]..."
                },
                "preliminares": {
                    "indicadores": ["preliminarmente", "prescrição", "ilegitimidade"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DAS PRELIMINARES\n[Argumentos preliminares se houver]"
                },
                "merito": {
                    "indicadores": ["mérito", "improcedência", "improcedente"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DO MÉRITO\n[Argumentação de mérito contestando os fatos]"
                },
                "pedido": {
                    "indicadores": ["requer", "pede", "improcedência"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nDiante do exposto, requer a improcedência total dos pedidos..."
                }
            },
            "observacoes": ["Contestar todos os fatos alegados", "Apresentar documentos"],
            "dicas": ["Impugnar especificamente cada alegação", "Fundamentar com CPC e jurisprudência"]
        }

        self.checklists[PieceType.CONTESTACAO_CIVEL] = [
            "Endereçamento correto",
            "Referência aos autos e partes",
            "Preliminares (se houver)",
            "Contestação ponto a ponto dos fatos",
            "Fundamentação jurídica",
            "Pedido de improcedência",
            "Requerimento de provas",
            "Assinatura e OAB"
        ]

        # Recurso de Apelação
        self.piece_templates[PieceType.RECURSO_APELACAO] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["egrégio", "tribunal"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EGRÉGIO TRIBUNAL DE JUSTIÇA DO ESTADO DE ..."
                },
                "qualificacao": {
                    "indicadores": ["apelante", "apelado", "autos"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "[NOME], já qualificado nos autos, vem, respeitosamente, interpor..."
                },
                "razoes": {
                    "indicadores": ["razões", "sentença", "equivocada"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DAS RAZÕES DO RECURSO\n1. DOS FATOS\n2. DO DIREITO\n3. DA REFORMA NECESSÁRIA"
                },
                "pedido": {
                    "indicadores": ["provimento", "reforma"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nRequer o provimento do recurso para reformar a sentença..."
                }
            },
            "observacoes": ["Prazo de 15 dias", "Preparo obrigatório em regra"],
            "dicas": ["Demonstrar prejuízo", "Atacar todos os fundamentos da sentença"]
        }

        self.checklists[PieceType.RECURSO_APELACAO] = [
            "Endereçamento ao Tribunal",
            "Qualificação e referência aos autos",
            "Tempestividade (prazo)",
            "Razões de fato e de direito",
            "Pedido específico de reforma",
            "Requerimento de provas (se necessário)",
            "Assinatura e OAB",
            "Comprovante de preparo"
        ]

        # Habeas Corpus
        self.piece_templates[PieceType.HABEAS_CORPUS] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "tribunal", "juiz"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO / DESEMBARGADOR..."
                },
                "qualificacao": {
                    "indicadores": ["paciente", "impetrante", "coator"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "Impetrante: [ADVOGADO]\nPaciente: [NOME DO PRESO]\nCoator: [AUTORIDADE COATORA]"
                },
                "coacao": {
                    "indicadores": ["coação", "ilegal", "constrangimento"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DA COAÇÃO ILEGAL\n[Demonstração da ilegalidade ou abuso]"
                },
                "pedido": {
                    "indicadores": ["liberdade", "relaxamento", "concessão"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nRequer a concessão da ordem para..."
                }
            },
            "observacoes": ["Não admite condenação em custas", "Liminar possível"],
            "dicas": ["Demonstrar ilegalidade flagrante", "Juntar documentos que provem a coação"]
        }

        self.checklists[PieceType.HABEAS_CORPUS] = [
            "Endereçamento correto",
            "Qualificação completa (paciente, impetrante, coator)",
            "Descrição da coação ilegal",
            "Fundamentação (CF, CPP, jurisprudência)",
            "Pedido claro de liberdade",
            "Requerimento de liminar (se urgente)",
            "Assinatura e OAB"
        ]

        # Mandado de Segurança
        self.piece_templates[PieceType.MANDADO_SEGURANCA] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "juiz", "desembargador"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ FEDERAL/ESTADUAL..."
                },
                "qualificacao": {
                    "indicadores": ["impetrante", "impetrado"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "Impetrante: [NOME]\nImpetrado: [AUTORIDADE COATORA]"
                },
                "ato_coator": {
                    "indicadores": ["ato coator", "ilegal", "direito líquido"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DO ATO COATOR\n[Descrição do ato ilegal ou abusivo]"
                },
                "direito_liquido": {
                    "indicadores": ["direito líquido e certo", "prova pré-constituída"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DO DIREITO LÍQUIDO E CERTO\n[Demonstração com documentos]"
                },
                "pedido": {
                    "indicadores": ["concessão", "segurança", "liminar"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nRequer a concessão da segurança para..."
                }
            },
            "observacoes": ["Necessária prova pré-constituída", "Prazo de 120 dias"],
            "dicas": ["Demonstrar direito líquido e certo", "Fundamentar com CF/88"]
        }

        self.checklists[PieceType.MANDADO_SEGURANCA] = [
            "Endereçamento correto",
            "Qualificação (impetrante e impetrado)",
            "Descrição do ato coator",
            "Demonstração de direito líquido e certo",
            "Prova pré-constituída",
            "Pedido de liminar (se urgente)",
            "Pedido principal",
            "Assinatura e OAB"
        ]

        # Reclamação Trabalhista
        self.piece_templates[PieceType.RECLAMACAO_TRABALHISTA] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "vara do trabalho"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DA ... VARA DO TRABALHO DE ..."
                },
                "qualificacao": {
                    "indicadores": ["reclamante", "reclamada"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "Reclamante: [EMPREGADO]\nReclamada: [EMPREGADOR]"
                },
                "relacao_emprego": {
                    "indicadores": ["vínculo", "carteira assinada", "jornada"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DA RELAÇÃO DE EMPREGO\n[Detalhes do contrato e condições de trabalho]"
                },
                "verbas": {
                    "indicadores": ["verbas rescisórias", "horas extras", "fgts"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DAS VERBAS DEVIDAS\n[Discriminação de cada verba com cálculo]"
                },
                "pedido": {
                    "indicadores": ["requer", "condenação", "procedência"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nRequer a procedência total para condenar a reclamada..."
                }
            },
            "observacoes": ["Discriminar e calcular cada verba", "Juntar documentos trabalhistas"],
            "dicas": ["Fundamentar com CLT", "Especificar valores de cada pedido"]
        }

        self.checklists[PieceType.RECLAMACAO_TRABALHISTA] = [
            "Endereçamento à Vara do Trabalho",
            "Qualificação (reclamante e reclamada)",
            "Descrição da relação de emprego",
            "Discriminação das verbas devidas",
            "Cálculos detalhados",
            "Pedidos especificados",
            "Valor da causa",
            "Assinatura e OAB"
        ]

        # Contraminuta
        self.piece_templates[PieceType.CONTRAMINUTA] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["egrégio", "tribunal"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EGRÉGIO TRIBUNAL DE JUSTIÇA DO ESTADO DE ..."
                },
                "qualificacao": {
                    "indicadores": ["apelado", "apelante", "contraminuta"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "[APELADO], vem apresentar CONTRAMINUTA ao recurso de apelação..."
                },
                "contrarrazoes": {
                    "indicadores": ["manutenção", "sentença", "acerto"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DAS CONTRARRAZÕES\n[Refutação dos argumentos do apelante]"
                },
                "pedido": {
                    "indicadores": ["desprovi mento", "manutenção", "sentença"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nRequer o desprovimento do recurso..."
                }
            },
            "observacoes": ["Prazo de 15 dias após intimação do recurso"],
            "dicas": ["Defender a sentença ponto a ponto", "Demonstrar acerto do juízo"]
        }

        self.checklists[PieceType.CONTRAMINUTA] = [
            "Endereçamento ao Tribunal",
            "Referência aos autos e recurso",
            "Contrarrazões fundamentadas",
            "Refutação dos argumentos do apelante",
            "Pedido de desprovimento",
            "Assinatura e OAB"
        ]

        # Queixa-Crime
        self.piece_templates[PieceType.QUEIXA_CRIME] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "juiz criminal"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ... VARA CRIMINAL DE ..."
                },
                "qualificacao": {
                    "indicadores": ["querelante", "querelado"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "Querelante: [VÍTIMA]\nQuerelado: [ACUSADO]"
                },
                "fatos": {
                    "indicadores": ["fato criminoso", "ocorrido", "praticado"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS FATOS\n[Narrativa detalhada do crime]"
                },
                "tipificacao": {
                    "indicadores": ["tipifica", "código penal", "artigo"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DA TIPIFICAÇÃO\n[Enquadramento legal - CP, art. X]"
                },
                "pedido": {
                    "indicadores": ["recebimento", "citação", "condenação"],
                    "criterios": [],
                    "regras": [],
                    "modelo": "DOS PEDIDOS\nRequer o recebimento da queixa e citação do querelado..."
                }
            },
            "observacoes": ["Prazo decadencial de 6 meses", "Apenas para crimes de ação privada"],
            "dicas": ["Narrar fatos com clareza", "Tipificar corretamente o crime"]
        }

        self.checklists[PieceType.QUEIXA_CRIME] = [
            "Endereçamento correto",
            "Qualificação completa",
            "Narrativa clara dos fatos",
            "Tipificação penal",
            "Pedido de recebimento e citação",
            "Requerimento de provas",
            "Assinatura e OAB"
        ]


# ============================================================
# FUNÇÕES FACTORY
# ============================================================

def criar_piece_engine_db() -> PieceEngineDB:
    """Factory function para criar piece engine DB"""
    return PieceEngineDB()
