"""
JURIS_IA_CORE_V1 - PIECE ENGINE
Motor de Verificação de Peças Processuais (OAB 2ª Fase)

Este módulo verifica peças processuais, identifica erros fatais e formais,
e fornece feedback estruturado para a 2ª fase da OAB.

Funcionalidades:
- Verificação de partes obrigatórias
- Detecção de erros fatais (que zeram)
- Detecção de erros formais (que reduzem nota)
- Checklist automatizado
- Feedback estruturado por competência
- Geração de peças-modelo

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


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
class RequiredPart:
    """Parte obrigatória de uma peça"""
    nome: str
    descricao: str
    obrigatoria: bool
    criterios_verificacao: List[str]
    exemplos: List[str]
    erros_comuns: List[str]


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


@dataclass
class PieceEvaluation:
    """Avaliação completa da peça"""
    piece_id: str
    aluno_id: str
    tipo_peca: PieceType
    nota_final: float  # 0-10
    aprovado: bool  # >= 6.0

    # Avaliação por competência
    adequacao_normas: float       # 0-10
    tecnica_processual: float     # 0-10
    argumentacao_juridica: float  # 0-10
    clareza_objetividade: float   # 0-10

    # Partes avaliadas
    partes_avaliadas: List[PartEvaluation]

    # Erros encontrados
    erros_fatais: List[ErrorFound]
    erros_graves: List[ErrorFound]
    erros_moderados: List[ErrorFound]
    erros_leves: List[ErrorFound]

    # Feedback
    pontos_fortes: List[str]
    pontos_melhorar: List[str]
    recomendacoes: List[str]

    # Checklist
    checklist_resultado: Dict[str, bool]


# ============================================================
# PIECE ENGINE
# ============================================================

class PieceEngine:
    """
    Motor de verificação de peças processuais.

    Responsabilidades:
    - Verificar estrutura da peça
    - Identificar erros fatais e formais
    - Avaliar por competência
    - Gerar feedback detalhado
    - Fornecer checklist de verificação
    """

    def __init__(self):
        """Inicializa o motor de peças"""
        self.piece_templates: Dict[PieceType, Dict] = {}
        self.checklists: Dict[PieceType, List[str]] = {}
        self._load_templates()

    def avaliar_peca(
        self,
        aluno_id: str,
        tipo_peca: PieceType,
        conteudo: str,
        enunciado: str
    ) -> PieceEvaluation:
        """
        Avalia uma peça processual completa.

        Args:
            aluno_id: ID do aluno
            tipo_peca: Tipo da peça
            conteudo: Texto da peça escrita pelo aluno
            enunciado: Enunciado da questão

        Returns:
            PieceEvaluation com análise completa
        """
        piece_id = f"peca_{aluno_id}_{tipo_peca.value}"

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

        return PieceEvaluation(
            piece_id=piece_id,
            aluno_id=aluno_id,
            tipo_peca=tipo_peca,
            nota_final=nota_final,
            aprovado=aprovado,
            adequacao_normas=adequacao,
            tecnica_processual=tecnica,
            argumentacao_juridica=argumentacao,
            clareza_objetividade=clareza,
            partes_avaliadas=partes_avaliadas,
            erros_fatais=erros_fatais,
            erros_graves=erros_graves,
            erros_moderados=erros_moderados,
            erros_leves=erros_leves,
            pontos_fortes=pontos_fortes,
            pontos_melhorar=pontos_melhorar,
            recomendacoes=recomendacoes,
            checklist_resultado=checklist_resultado
        )

    def gerar_checklist(self, tipo_peca: PieceType) -> List[str]:
        """Gera checklist de verificação para tipo de peça"""
        return self.checklists.get(tipo_peca, [])

    def gerar_peca_modelo(
        self,
        tipo_peca: PieceType,
        enunciado: str,
        detalhada: bool = False
    ) -> Dict:
        """
        Gera peça-modelo baseada no enunciado.

        Args:
            tipo_peca: Tipo de peça
            enunciado: Enunciado da questão
            detalhada: Se deve incluir comentários detalhados

        Returns:
            Dict com estrutura da peça-modelo
        """
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

        return {
            "tipo": tipo_peca.value,
            "partes": partes,
            "observacoes": template.get("observacoes", []),
            "dicas": template.get("dicas", [])
        }

    def verificar_erro_fatal(
        self,
        tipo_peca: PieceType,
        conteudo: str
    ) -> Optional[ErrorFound]:
        """
        Verifica se há erro fatal (que zera a peça).

        Returns:
            ErrorFound se encontrou erro fatal, None caso contrário
        """
        erros = self._detectar_erros(tipo_peca, conteudo, "")

        erros_fatais = [e for e in erros if e.gravidade == ErrorSeverity.FATAL]

        return erros_fatais[0] if erros_fatais else None

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
                    "verificacao": lambda c: len(c) < 200,  # Simplificado
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

        # Verifica se respondeu ao pedido do enunciado
        # (Análise simplificada - em produção seria mais sofisticada)

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

    def _load_templates(self):
        """Carrega templates de peças"""
        # Petição Inicial Cível
        self.piece_templates[PieceType.PETICAO_INICIAL_CIVEL] = {
            "partes": {
                "enderecamento": {
                    "indicadores": ["excelentíssimo", "mm. juiz"],
                    "modelo": "EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA ... VARA CÍVEL DE ..."
                },
                "qualificacao": {
                    "indicadores": ["autor", "réu", "cpf"],
                    "modelo": "[NOME], nacionalidade, estado civil, profissão, portador do CPF ..."
                },
                "causa_pedir": {
                    "indicadores": ["fatos", "direito"],
                    "modelo": "DOS FATOS\n[Narrativa dos fatos]\n\nDO DIREITO\n[Fundamentação jurídica]"
                },
                "pedido": {
                    "indicadores": ["requer", "pede"],
                    "modelo": "DOS PEDIDOS\nDiante do exposto, requer..."
                }
            }
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


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_piece_engine() -> PieceEngine:
    """Factory function para criar piece engine"""
    return PieceEngine()


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Cria engine
    engine = criar_piece_engine()

    print("=" * 60)
    print("PIECE ENGINE - EXEMPLO DE USO")
    print("=" * 60)

    # Peça de exemplo (incompleta propositalmente)
    peca_exemplo = """
EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO DA 1ª VARA CÍVEL DE SÃO PAULO

JOÃO DA SILVA, brasileiro, casado, portador do CPF 123.456.789-00,
residente na Rua A, 123, vem, por seu advogado, propor

AÇÃO DE COBRANÇA

em face de MARIA SOUZA, brasileira, CPF 987.654.321-00,
residente na Rua B, 456, pelos seguintes fatos e fundamentos:

DOS FATOS

O autor emprestou R$ 10.000,00 à ré em 01/01/2024.
A ré não pagou o valor na data acordada (01/06/2024).

DO DIREITO

O contrato de mútuo está previsto no Código Civil.
O não pagamento gera obrigação de devolver o valor.

Diante do exposto, requer:
a) A citação da ré
b) A condenação ao pagamento de R$ 10.000,00

São Paulo, 17 de dezembro de 2025.

ADVOGADO - OAB/SP 123456
    """

    # Avalia a peça
    print("\n1. AVALIANDO PEÇA")
    print("-" * 60)

    avaliacao = engine.avaliar_peca(
        aluno_id="aluno_123",
        tipo_peca=PieceType.PETICAO_INICIAL_CIVEL,
        conteudo=peca_exemplo,
        enunciado="João emprestou R$ 10.000,00 a Maria que não pagou. Elabore petição inicial."
    )

    print(f"Nota final: {avaliacao.nota_final}")
    print(f"Aprovado: {'SIM' if avaliacao.aprovado else 'NÃO'}")
    print(f"\nNotas por competência:")
    print(f"  Adequação às normas: {avaliacao.adequacao_normas}")
    print(f"  Técnica processual: {avaliacao.tecnica_processual}")
    print(f"  Argumentação jurídica: {avaliacao.argumentacao_juridica}")
    print(f"  Clareza e objetividade: {avaliacao.clareza_objetividade}")

    # Erros encontrados
    print(f"\n2. ERROS ENCONTRADOS")
    print("-" * 60)

    if avaliacao.erros_fatais:
        print("ERROS FATAIS (zeram a peça):")
        for erro in avaliacao.erros_fatais:
            print(f"  ⚠️  {erro.descricao}")
            print(f"      Correção: {erro.correcao_sugerida}")

    if avaliacao.erros_graves:
        print("\nERROS GRAVES:")
        for erro in avaliacao.erros_graves:
            print(f"  - {erro.descricao}")

    # Feedback
    print(f"\n3. FEEDBACK")
    print("-" * 60)

    print("PONTOS FORTES:")
    for ponto in avaliacao.pontos_fortes:
        print(f"  ✓ {ponto}")

    print("\nPONTOS A MELHORAR:")
    for ponto in avaliacao.pontos_melhorar:
        print(f"  → {ponto}")

    print("\nRECOMENDAÇÕES:")
    for rec in avaliacao.recomendacoes:
        print(f"  • {rec}")

    # Checklist
    print(f"\n4. CHECKLIST")
    print("-" * 60)

    for item, ok in avaliacao.checklist_resultado.items():
        status = "✓" if ok else "✗"
        print(f"  {status} {item}")

    print("\n" + "=" * 60)
    print("PIECE ENGINE - OPERACIONAL")
    print("=" * 60)
