"""
Sistema de Repetição Espaçada - Padrão Funcional Puro
====================================================

Baseado no algoritmo SuperMemo SM-2 para otimizar retenção de conhecimento.
Funções puras, sem efeitos colaterais.

Autor: JURIS_IA_CORE_V1
Data: 2025-12-28
"""

from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import math


# ============================================================================
# TIPOS E ESTRUTURAS IMUTÁVEIS
# ============================================================================

class DificuldadeResposta(str, Enum):
    """Dificuldade percebida pelo usuário ao responder"""
    BLACKOUT = "blackout"      # Não lembrava nada (0)
    DIFICIL = "dificil"         # Lembrou com muito esforço (1-2)
    MEDIO = "medio"             # Lembrou com esforço (3)
    FACIL = "facil"             # Lembrou facilmente (4)
    MUITO_FACIL = "muito_facil" # Lembrou imediatamente (5)


@dataclass(frozen=True)
class CartaoRevisao:
    """Estado imutável de um cartão de revisão (questão)"""
    questao_id: str
    disciplina: str
    topico: str

    # Estado do aprendizado
    intervalo_dias: int  # Intervalo atual até próxima revisão
    repeticoes: int      # Número de vezes que foi revisada com sucesso
    ease_factor: float   # Fator de facilidade (1.3 - 2.5)

    # Datas
    ultima_revisao: Optional[datetime]
    proxima_revisao: datetime

    # Histórico
    total_revisoes: int
    total_acertos: int
    total_erros: int


@dataclass(frozen=True)
class ResultadoRevisao:
    """Resultado imutável de uma revisão"""
    acertou: bool
    dificuldade: DificuldadeResposta
    tempo_segundos: int
    timestamp: datetime


# ============================================================================
# CONSTANTES
# ============================================================================

# Fator de facilidade padrão (SuperMemo SM-2)
EASE_FACTOR_INICIAL = 2.5
EASE_FACTOR_MINIMO = 1.3
EASE_FACTOR_MAXIMO = 2.5

# Intervalos iniciais (em dias)
INTERVALO_INICIAL = 1
INTERVALO_FACIL = 4

# Modificadores de ease factor baseado na dificuldade
EASE_MODIFICADORES = {
    DificuldadeResposta.BLACKOUT: -0.8,
    DificuldadeResposta.DIFICIL: -0.15,
    DificuldadeResposta.MEDIO: 0.0,
    DificuldadeResposta.FACIL: 0.0,
    DificuldadeResposta.MUITO_FACIL: 0.15,
}


# ============================================================================
# FUNÇÕES PURAS - CÁLCULO DE INTERVALOS
# ============================================================================

def calcular_novo_ease_factor(ease_atual: float, dificuldade: DificuldadeResposta) -> float:
    """
    Função pura: calcula novo ease factor baseado na dificuldade

    Args:
        ease_atual: Ease factor atual
        dificuldade: Dificuldade percebida na resposta

    Returns:
        Novo ease factor (limitado entre 1.3 e 2.5)
    """
    modificador = EASE_MODIFICADORES.get(dificuldade, 0.0)
    novo_ease = ease_atual + modificador
    return max(EASE_FACTOR_MINIMO, min(novo_ease, EASE_FACTOR_MAXIMO))


def calcular_proximo_intervalo(
    intervalo_atual: int,
    repeticoes: int,
    ease_factor: float,
    acertou: bool,
    dificuldade: DificuldadeResposta
) -> int:
    """
    Função pura: calcula próximo intervalo usando algoritmo SuperMemo SM-2

    Args:
        intervalo_atual: Intervalo atual em dias
        repeticoes: Número de repetições bem-sucedidas
        ease_factor: Fator de facilidade
        acertou: Se acertou a resposta
        dificuldade: Dificuldade percebida

    Returns:
        Próximo intervalo em dias
    """
    # Se errou ou foi muito difícil, recomeça
    if not acertou or dificuldade == DificuldadeResposta.BLACKOUT:
        return INTERVALO_INICIAL

    # Se acertou com dificuldade, diminui o intervalo
    if dificuldade == DificuldadeResposta.DIFICIL:
        return max(INTERVALO_INICIAL, int(intervalo_atual * 0.5))

    # Primeira repetição bem-sucedida
    if repeticoes == 0:
        return INTERVALO_INICIAL

    # Segunda repetição bem-sucedida
    if repeticoes == 1:
        if dificuldade == DificuldadeResposta.MUITO_FACIL:
            return INTERVALO_FACIL
        return INTERVALO_INICIAL + 2  # 3 dias

    # Repetições subsequentes: intervalo cresce exponencialmente
    if dificuldade == DificuldadeResposta.MUITO_FACIL:
        # Se foi muito fácil, aumenta mais rapidamente
        return int(intervalo_atual * ease_factor * 1.3)

    return int(intervalo_atual * ease_factor)


def calcular_nova_data_revisao(data_atual: datetime, intervalo_dias: int) -> datetime:
    """
    Função pura: calcula data da próxima revisão

    Args:
        data_atual: Data/hora atual
        intervalo_dias: Intervalo em dias

    Returns:
        Data/hora da próxima revisão
    """
    return data_atual + timedelta(days=intervalo_dias)


# ============================================================================
# FUNÇÕES PURAS - PROCESSAMENTO DE REVISÃO
# ============================================================================

def processar_revisao(
    cartao: CartaoRevisao,
    resultado: ResultadoRevisao
) -> CartaoRevisao:
    """
    Função pura: processa uma revisão e retorna novo estado do cartão

    Args:
        cartao: Estado atual do cartão
        resultado: Resultado da revisão

    Returns:
        Novo estado do cartão (imutável)
    """
    # Calcular novo ease factor
    novo_ease = calcular_novo_ease_factor(cartao.ease_factor, resultado.dificuldade)

    # Calcular novas repetições
    if resultado.acertou and resultado.dificuldade != DificuldadeResposta.BLACKOUT:
        novas_repeticoes = cartao.repeticoes + 1
    else:
        novas_repeticoes = 0

    # Calcular próximo intervalo
    novo_intervalo = calcular_proximo_intervalo(
        cartao.intervalo_dias,
        cartao.repeticoes,
        novo_ease,
        resultado.acertou,
        resultado.dificuldade
    )

    # Calcular próxima data de revisão
    proxima_data = calcular_nova_data_revisao(resultado.timestamp, novo_intervalo)

    # Atualizar estatísticas
    novo_total_revisoes = cartao.total_revisoes + 1
    novo_total_acertos = cartao.total_acertos + (1 if resultado.acertou else 0)
    novo_total_erros = cartao.total_erros + (0 if resultado.acertou else 1)

    # Criar novo cartão (imutável)
    return CartaoRevisao(
        questao_id=cartao.questao_id,
        disciplina=cartao.disciplina,
        topico=cartao.topico,
        intervalo_dias=novo_intervalo,
        repeticoes=novas_repeticoes,
        ease_factor=novo_ease,
        ultima_revisao=resultado.timestamp,
        proxima_revisao=proxima_data,
        total_revisoes=novo_total_revisoes,
        total_acertos=novo_total_acertos,
        total_erros=novo_total_erros,
    )


def criar_cartao_inicial(
    questao_id: str,
    disciplina: str,
    topico: str,
    data_criacao: datetime
) -> CartaoRevisao:
    """
    Função pura: cria cartão inicial para nova questão

    Args:
        questao_id: ID da questão
        disciplina: Disciplina da questão
        topico: Tópico da questão
        data_criacao: Data de criação

    Returns:
        Cartão inicial
    """
    return CartaoRevisao(
        questao_id=questao_id,
        disciplina=disciplina,
        topico=topico,
        intervalo_dias=INTERVALO_INICIAL,
        repeticoes=0,
        ease_factor=EASE_FACTOR_INICIAL,
        ultima_revisao=None,
        proxima_revisao=data_criacao,  # Disponível imediatamente
        total_revisoes=0,
        total_acertos=0,
        total_erros=0,
    )


# ============================================================================
# FUNÇÕES PURAS - SELEÇÃO DE CARTÕES
# ============================================================================

def cartao_deve_revisar(cartao: CartaoRevisao, agora: datetime) -> bool:
    """
    Função pura: verifica se cartão deve ser revisado agora

    Args:
        cartao: Cartão de revisão
        agora: Data/hora atual

    Returns:
        True se deve revisar
    """
    return cartao.proxima_revisao <= agora


def filtrar_cartoes_pendentes(
    cartoes: List[CartaoRevisao],
    agora: datetime
) -> List[CartaoRevisao]:
    """
    Função pura: filtra cartões pendentes de revisão

    Args:
        cartoes: Lista de cartões
        agora: Data/hora atual

    Returns:
        Lista de cartões que devem ser revisados
    """
    return [c for c in cartoes if cartao_deve_revisar(c, agora)]


def ordenar_cartoes_prioridade(cartoes: List[CartaoRevisao]) -> List[CartaoRevisao]:
    """
    Função pura: ordena cartões por prioridade de revisão

    Prioridade:
    1. Cartões vencidos há mais tempo
    2. Cartões com menor ease factor (mais difíceis)
    3. Cartões com menos repetições

    Args:
        cartoes: Lista de cartões

    Returns:
        Lista ordenada por prioridade
    """
    return sorted(
        cartoes,
        key=lambda c: (
            c.proxima_revisao,      # Mais antigos primeiro
            c.ease_factor,          # Mais difíceis primeiro
            c.repeticoes,           # Menos revisados primeiro
        )
    )


def agrupar_por_disciplina(
    cartoes: List[CartaoRevisao]
) -> Dict[str, List[CartaoRevisao]]:
    """
    Função pura: agrupa cartões por disciplina

    Args:
        cartoes: Lista de cartões

    Returns:
        Dict com cartões agrupados por disciplina
    """
    resultado = {}
    for cartao in cartoes:
        if cartao.disciplina not in resultado:
            resultado[cartao.disciplina] = []
        resultado[cartao.disciplina].append(cartao)
    return resultado


# ============================================================================
# FUNÇÕES PURAS - ESTATÍSTICAS
# ============================================================================

def calcular_taxa_retencao(cartao: CartaoRevisao) -> float:
    """
    Função pura: calcula taxa de retenção do cartão

    Args:
        cartao: Cartão de revisão

    Returns:
        Taxa de retenção (0.0 - 1.0)
    """
    if cartao.total_revisoes == 0:
        return 0.0
    return cartao.total_acertos / cartao.total_revisoes


def calcular_nivel_dominio(cartao: CartaoRevisao) -> str:
    """
    Função pura: calcula nível de domínio baseado em métricas

    Args:
        cartao: Cartão de revisão

    Returns:
        Nível: NOVO, APRENDENDO, CONSOLIDANDO, DOMINADO, EXPERT
    """
    taxa_retencao = calcular_taxa_retencao(cartao)

    if cartao.repeticoes == 0:
        return "NOVO"

    if cartao.repeticoes < 3:
        return "APRENDENDO"

    if taxa_retencao < 0.7:
        return "APRENDENDO"

    if cartao.repeticoes < 5 or cartao.intervalo_dias < 14:
        return "CONSOLIDANDO"

    if cartao.repeticoes >= 8 and cartao.intervalo_dias >= 30 and taxa_retencao >= 0.9:
        return "EXPERT"

    return "DOMINADO"


def calcular_estatisticas_globais(
    cartoes: List[CartaoRevisao]
) -> Dict[str, any]:
    """
    Função pura: calcula estatísticas globais dos cartões

    Args:
        cartoes: Lista de todos os cartões

    Returns:
        Dict com estatísticas
    """
    if not cartoes:
        return {
            "total_cartoes": 0,
            "total_revisoes": 0,
            "taxa_retencao_geral": 0.0,
            "cartoes_por_nivel": {},
            "proximas_24h": 0,
            "proximos_7d": 0,
        }

    agora = datetime.now()
    amanha = agora + timedelta(days=1)
    proxima_semana = agora + timedelta(days=7)

    total_revisoes = sum(c.total_revisoes for c in cartoes)
    total_acertos = sum(c.total_acertos for c in cartoes)

    # Contar por nível
    niveis = {}
    for cartao in cartoes:
        nivel = calcular_nivel_dominio(cartao)
        niveis[nivel] = niveis.get(nivel, 0) + 1

    # Contar próximas revisões
    proximas_24h = len([c for c in cartoes if c.proxima_revisao <= amanha])
    proximos_7d = len([c for c in cartoes if c.proxima_revisao <= proxima_semana])

    return {
        "total_cartoes": len(cartoes),
        "total_revisoes": total_revisoes,
        "taxa_retencao_geral": total_acertos / total_revisoes if total_revisoes > 0 else 0.0,
        "cartoes_por_nivel": niveis,
        "proximas_24h": proximas_24h,
        "proximos_7d": proximos_7d,
    }


# ============================================================================
# FUNÇÕES AUXILIARES - CONVERSÃO
# ============================================================================

def cartao_para_dict(cartao: CartaoRevisao) -> Dict[str, any]:
    """Converte CartaoRevisao para dict"""
    return {
        "questao_id": cartao.questao_id,
        "disciplina": cartao.disciplina,
        "topico": cartao.topico,
        "intervalo_dias": cartao.intervalo_dias,
        "repeticoes": cartao.repeticoes,
        "ease_factor": round(cartao.ease_factor, 2),
        "ultima_revisao": cartao.ultima_revisao.isoformat() if cartao.ultima_revisao else None,
        "proxima_revisao": cartao.proxima_revisao.isoformat(),
        "total_revisoes": cartao.total_revisoes,
        "total_acertos": cartao.total_acertos,
        "total_erros": cartao.total_erros,
        "taxa_retencao": round(calcular_taxa_retencao(cartao), 3),
        "nivel_dominio": calcular_nivel_dominio(cartao),
    }


def dict_para_cartao(data: Dict[str, any]) -> CartaoRevisao:
    """Converte dict para CartaoRevisao"""
    return CartaoRevisao(
        questao_id=data["questao_id"],
        disciplina=data["disciplina"],
        topico=data["topico"],
        intervalo_dias=data["intervalo_dias"],
        repeticoes=data["repeticoes"],
        ease_factor=data["ease_factor"],
        ultima_revisao=datetime.fromisoformat(data["ultima_revisao"]) if data.get("ultima_revisao") else None,
        proxima_revisao=datetime.fromisoformat(data["proxima_revisao"]),
        total_revisoes=data["total_revisoes"],
        total_acertos=data["total_acertos"],
        total_erros=data["total_erros"],
    )
