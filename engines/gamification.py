"""
Sistema de Gamificação - Padrão Funcional Puro
==============================================

Sistema de FP, níveis, streaks e conquistas usando programação funcional.
Sem efeitos colaterais, funções puras, composição de funções.

Autor: JURIS_IA_CORE_V1
Data: 2025-12-28
"""

from typing import Dict, List, Tuple, Callable, Optional, Any
from datetime import datetime, timedelta
from functools import reduce
from dataclasses import dataclass
import math


# ============================================================================
# TIPOS E ESTRUTURAS DE DADOS (IMUTÁVEIS)
# ============================================================================

@dataclass(frozen=True)
class ConquistaConfig:
    """Configuração imutável de uma conquista"""
    codigo: str
    nome: str
    descricao: str
    icone: str
    categoria: str
    fp_recompensa: int
    criterio_tipo: str
    criterio_valor: int
    raridade: str


@dataclass(frozen=True)
class EstadoGamificacao:
    """Estado imutável da gamificação de um usuário"""
    total_fp: int
    nivel: int
    conquistas: Tuple[str, ...]  # Tupla imutável
    streak_atual: int
    streak_maximo: int
    ultima_atividade: Optional[datetime]
    total_questoes: int
    total_acertos: int
    total_sessoes: int
    total_pecas: int
    taxa_acerto: float


@dataclass(frozen=True)
class AcaoUsuario:
    """Ação que gera FP (imutável)"""
    tipo: str  # 'questao_correta', 'questao_errada', 'sessao_completa', 'peca_concluida', 'login_diario'
    valor: int  # Quantidade (ex: 1 questão, 1 sessão, etc)
    bonus: int = 0  # Bonus adicional
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            object.__setattr__(self, 'timestamp', datetime.now())


# ============================================================================
# CONSTANTES FUNCIONAIS
# ============================================================================

# Tabela de FP por ação (imutável)
FP_POR_ACAO: Dict[str, int] = {
    'questao_correta': 10,
    'questao_errada': 2,
    'sessao_completa': 50,
    'peca_concluida': 100,
    'login_diario': 5,
    'streak_bonus_3': 50,
    'streak_bonus_7': 100,
    'streak_bonus_15': 200,
    'streak_bonus_30': 500,
}

# Catálogo de conquistas (imutável)
CONQUISTAS_CATALOGO: Tuple[ConquistaConfig, ...] = (
    # Início
    ConquistaConfig('PRIMEIRA_QUESTAO', 'Primeira Questão', 'Respondeu sua primeira questão', '🎯', 'inicio', 10, 'questoes', 1, 'COMUM'),
    ConquistaConfig('PRIMEIRA_SESSAO', 'Primeira Sessão', 'Completou sua primeira sessão', '📚', 'inicio', 20, 'sessoes', 1, 'COMUM'),
    ConquistaConfig('PRIMEIRA_PECA', 'Primeira Peça', 'Escreveu sua primeira peça', '⚖️', 'inicio', 30, 'pecas', 1, 'COMUM'),

    # Questões
    ConquistaConfig('10_QUESTOES', 'Estudante Dedicado', 'Respondeu 10 questões', '📖', 'questoes', 50, 'questoes', 10, 'COMUM'),
    ConquistaConfig('50_QUESTOES', 'Praticante', 'Respondeu 50 questões', '📝', 'questoes', 100, 'questoes', 50, 'INCOMUM'),
    ConquistaConfig('100_QUESTOES', 'Dedicado', 'Respondeu 100 questões', '📚', 'questoes', 200, 'questoes', 100, 'INCOMUM'),
    ConquistaConfig('500_QUESTOES', 'Expert', 'Respondeu 500 questões', '🎓', 'questoes', 500, 'questoes', 500, 'RARA'),
    ConquistaConfig('1000_QUESTOES', 'Mestre', 'Respondeu 1000 questões', '👨‍⚖️', 'questoes', 1000, 'questoes', 1000, 'EPICA'),

    # Acertos
    ConquistaConfig('ACERTO_70', 'Bom Desempenho', 'Atingiu 70% de acerto', '✅', 'acertos', 150, 'taxa_acerto', 70, 'INCOMUM'),
    ConquistaConfig('ACERTO_80', 'Ótimo Desempenho', 'Atingiu 80% de acerto', '🌟', 'acertos', 300, 'taxa_acerto', 80, 'RARA'),
    ConquistaConfig('ACERTO_90', 'Excepcional', 'Atingiu 90% de acerto', '⭐', 'acertos', 500, 'taxa_acerto', 90, 'EPICA'),

    # Streaks
    ConquistaConfig('STREAK_3', 'Comprometido', '3 dias consecutivos', '🔥', 'streak', 50, 'streak', 3, 'COMUM'),
    ConquistaConfig('STREAK_7', 'Disciplinado', '7 dias consecutivos', '🔥🔥', 'streak', 100, 'streak', 7, 'INCOMUM'),
    ConquistaConfig('STREAK_15', 'Determinado', '15 dias consecutivos', '🔥🔥🔥', 'streak', 200, 'streak', 15, 'RARA'),
    ConquistaConfig('STREAK_30', 'Imparável', '30 dias consecutivos', '🔥🔥🔥🔥', 'streak', 500, 'streak', 30, 'EPICA'),

    # Peças
    ConquistaConfig('5_PECAS', 'Redator Iniciante', 'Escreveu 5 peças', '📄', 'pecas', 100, 'pecas', 5, 'COMUM'),
    ConquistaConfig('10_PECAS', 'Redator Competente', 'Escreveu 10 peças', '📋', 'pecas', 200, 'pecas', 10, 'INCOMUM'),
    ConquistaConfig('20_PECAS', 'Redator Expert', 'Escreveu 20 peças', '📜', 'pecas', 400, 'pecas', 20, 'RARA'),

    # Níveis
    ConquistaConfig('NIVEL_5', 'Aprendiz', 'Atingiu nível 5', '🎯', 'niveis', 100, 'nivel', 5, 'COMUM'),
    ConquistaConfig('NIVEL_10', 'Intermediário', 'Atingiu nível 10', '🎯🎯', 'niveis', 250, 'nivel', 10, 'INCOMUM'),
    ConquistaConfig('NIVEL_20', 'Avançado', 'Atingiu nível 20', '🎯🎯🎯', 'niveis', 500, 'nivel', 20, 'RARA'),
    ConquistaConfig('NIVEL_50', 'Lendário', 'Atingiu nível 50', '👑', 'niveis', 2000, 'nivel', 50, 'LENDARIA'),
)


# ============================================================================
# FUNÇÕES PURAS - CÁLCULO DE FP
# ============================================================================

def calcular_fp_acao(acao: AcaoUsuario) -> int:
    """
    Função pura: calcula FP de uma ação

    Args:
        acao: Ação do usuário

    Returns:
        FP ganho
    """
    fp_base = FP_POR_ACAO.get(acao.tipo, 0)
    return (fp_base * acao.valor) + acao.bonus


def calcular_nivel_por_fp(fp_total: int) -> int:
    """
    Função pura: calcula nível baseado em FP total
    Usa fórmula exponencial: nivel = floor(sqrt(fp / 100))

    Args:
        fp_total: FP total acumulado

    Returns:
        Nível (1-100)
    """
    if fp_total < 0:
        return 1

    nivel = math.floor(math.sqrt(fp_total / 100)) + 1
    return min(max(nivel, 1), 100)


def calcular_fp_para_proximo_nivel(nivel_atual: int) -> int:
    """
    Função pura: calcula FP necessário para o próximo nível

    Args:
        nivel_atual: Nível atual do usuário

    Returns:
        FP total necessário para o próximo nível
    """
    proximo_nivel = nivel_atual + 1
    return ((proximo_nivel - 1) ** 2) * 100


def calcular_progresso_nivel(fp_atual: int, nivel_atual: int) -> float:
    """
    Função pura: calcula progresso percentual no nível atual

    Args:
        fp_atual: FP atual do usuário
        nivel_atual: Nível atual

    Returns:
        Percentual de progresso (0.0 - 1.0)
    """
    fp_nivel_atual = ((nivel_atual - 1) ** 2) * 100
    fp_proximo_nivel = calcular_fp_para_proximo_nivel(nivel_atual)

    fp_no_nivel = fp_atual - fp_nivel_atual
    fp_necessario = fp_proximo_nivel - fp_nivel_atual

    if fp_necessario <= 0:
        return 1.0

    return min(max(fp_no_nivel / fp_necessario, 0.0), 1.0)


# ============================================================================
# FUNÇÕES PURAS - STREAK
# ============================================================================

def calcular_streak(ultima_atividade: Optional[datetime], agora: datetime) -> int:
    """
    Função pura: calcula se o streak continua ou quebrou

    Args:
        ultima_atividade: Data da última atividade
        agora: Data/hora atual

    Returns:
        0 se quebrou, 1 se continua
    """
    if ultima_atividade is None:
        return 0

    # Normaliza para comparar apenas datas (sem horas)
    ultima_data = ultima_atividade.date()
    hoje = agora.date()

    diferenca_dias = (hoje - ultima_data).days

    # Se foi hoje, streak continua (retorna 1 para não incrementar de novo)
    if diferenca_dias == 0:
        return 1

    # Se foi ontem, streak continua
    if diferenca_dias == 1:
        return 1

    # Se passou mais de 1 dia, streak quebrou
    return 0


def aplicar_streak(estado: EstadoGamificacao, agora: datetime) -> EstadoGamificacao:
    """
    Função pura: aplica lógica de streak ao estado

    Args:
        estado: Estado atual da gamificação
        agora: Data/hora atual

    Returns:
        Novo estado com streak atualizado
    """
    if estado.ultima_atividade is None:
        # Primeira atividade
        return EstadoGamificacao(
            **{**estado.__dict__, 'streak_atual': 1, 'ultima_atividade': agora}
        )

    ultima_data = estado.ultima_atividade.date()
    hoje = agora.date()
    diferenca = (hoje - ultima_data).days

    if diferenca == 0:
        # Mesma data, não faz nada
        return estado

    if diferenca == 1:
        # Incrementa streak
        novo_streak = estado.streak_atual + 1
        novo_maximo = max(novo_streak, estado.streak_maximo)
        return EstadoGamificacao(
            **{**estado.__dict__,
               'streak_atual': novo_streak,
               'streak_maximo': novo_maximo,
               'ultima_atividade': agora}
        )

    # Streak quebrou
    return EstadoGamificacao(
        **{**estado.__dict__, 'streak_atual': 1, 'ultima_atividade': agora}
    )


def calcular_bonus_streak(streak: int) -> int:
    """
    Função pura: calcula bonus de FP baseado no streak

    Args:
        streak: Número de dias consecutivos

    Returns:
        FP bonus
    """
    if streak >= 30:
        return FP_POR_ACAO['streak_bonus_30']
    elif streak >= 15:
        return FP_POR_ACAO['streak_bonus_15']
    elif streak >= 7:
        return FP_POR_ACAO['streak_bonus_7']
    elif streak >= 3:
        return FP_POR_ACAO['streak_bonus_3']
    return 0


# ============================================================================
# FUNÇÕES PURAS - CONQUISTAS
# ============================================================================

def verificar_conquista(conquista: ConquistaConfig, estado: EstadoGamificacao) -> bool:
    """
    Função pura: verifica se uma conquista foi desbloqueada

    Args:
        conquista: Configuração da conquista
        estado: Estado atual do usuário

    Returns:
        True se desbloqueou
    """
    criterio_map = {
        'questoes': estado.total_questoes,
        'acertos': estado.total_acertos,
        'taxa_acerto': estado.taxa_acerto,
        'streak': estado.streak_atual,
        'sessoes': estado.total_sessoes,
        'pecas': estado.total_pecas,
        'nivel': estado.nivel,
    }

    valor_atual = criterio_map.get(conquista.criterio_tipo, 0)
    return valor_atual >= conquista.criterio_valor


def encontrar_novas_conquistas(estado: EstadoGamificacao) -> Tuple[ConquistaConfig, ...]:
    """
    Função pura: encontra conquistas recém desbloqueadas

    Args:
        estado: Estado atual

    Returns:
        Tupla de novas conquistas
    """
    conquistas_atuais = set(estado.conquistas)

    novas = tuple(
        c for c in CONQUISTAS_CATALOGO
        if c.codigo not in conquistas_atuais and verificar_conquista(c, estado)
    )

    return novas


def aplicar_conquistas(estado: EstadoGamificacao, novas: Tuple[ConquistaConfig, ...]) -> EstadoGamificacao:
    """
    Função pura: aplica novas conquistas ao estado

    Args:
        estado: Estado atual
        novas: Novas conquistas desbloqueadas

    Returns:
        Novo estado com conquistas adicionadas
    """
    if not novas:
        return estado

    # FP total das conquistas
    fp_conquistas = sum(c.fp_recompensa for c in novas)

    # Adiciona códigos das conquistas
    novos_codigos = tuple(c.codigo for c in novas)
    todas_conquistas = estado.conquistas + novos_codigos

    # Novo FP total
    novo_fp = estado.total_fp + fp_conquistas
    novo_nivel = calcular_nivel_por_fp(novo_fp)

    return EstadoGamificacao(
        **{**estado.__dict__,
           'total_fp': novo_fp,
           'nivel': novo_nivel,
           'conquistas': todas_conquistas}
    )


# ============================================================================
# FUNÇÃO PRINCIPAL - COMPOSIÇÃO FUNCIONAL
# ============================================================================

def processar_acao(estado: EstadoGamificacao, acao: AcaoUsuario) -> Tuple[EstadoGamificacao, Dict[str, Any]]:
    """
    Função pura principal: processa uma ação do usuário
    Composição funcional de todas as operações

    Args:
        estado: Estado atual da gamificação
        acao: Ação realizada pelo usuário

    Returns:
        (novo_estado, resultado_detalhado)
    """
    # 1. Atualizar streak
    estado_com_streak = aplicar_streak(estado, acao.timestamp)

    # 2. Calcular FP da ação
    fp_acao = calcular_fp_acao(acao)

    # 3. Calcular bonus de streak
    bonus_streak = calcular_bonus_streak(estado_com_streak.streak_atual)

    # 4. FP total ganho
    fp_total_ganho = fp_acao + bonus_streak

    # 5. Atualizar estatísticas
    novo_total_fp = estado_com_streak.total_fp + fp_total_ganho
    novo_nivel = calcular_nivel_por_fp(novo_total_fp)

    # Atualizar contadores baseado no tipo de ação
    stats_update = {}
    if acao.tipo == 'questao_correta':
        stats_update = {
            'total_questoes': estado.total_questoes + 1,
            'total_acertos': estado.total_acertos + 1,
        }
    elif acao.tipo == 'questao_errada':
        stats_update = {'total_questoes': estado.total_questoes + 1}
    elif acao.tipo == 'sessao_completa':
        stats_update = {'total_sessoes': estado.total_sessoes + 1}
    elif acao.tipo == 'peca_concluida':
        stats_update = {'total_pecas': estado.total_pecas + 1}

    # Recalcular taxa de acerto
    novo_total_questoes = stats_update.get('total_questoes', estado.total_questoes)
    novo_total_acertos = stats_update.get('total_acertos', estado.total_acertos)
    nova_taxa_acerto = (novo_total_acertos / novo_total_questoes * 100) if novo_total_questoes > 0 else 0.0

    # Criar novo estado intermediário
    estado_intermediario = EstadoGamificacao(
        total_fp=novo_total_fp,
        nivel=novo_nivel,
        conquistas=estado_com_streak.conquistas,
        streak_atual=estado_com_streak.streak_atual,
        streak_maximo=estado_com_streak.streak_maximo,
        ultima_atividade=estado_com_streak.ultima_atividade,
        total_questoes=novo_total_questoes,
        total_acertos=novo_total_acertos,
        total_sessoes=stats_update.get('total_sessoes', estado.total_sessoes),
        total_pecas=stats_update.get('total_pecas', estado.total_pecas),
        taxa_acerto=nova_taxa_acerto,
    )

    # 6. Verificar novas conquistas
    novas_conquistas = encontrar_novas_conquistas(estado_intermediario)

    # 7. Aplicar conquistas
    estado_final = aplicar_conquistas(estado_intermediario, novas_conquistas)

    # 8. Construir resultado detalhado
    subiu_nivel = estado_final.nivel > estado.nivel
    ganhou_streak = estado_final.streak_atual > estado.streak_atual

    resultado = {
        'fp_ganho': fp_total_ganho,
        'fp_acao': fp_acao,
        'bonus_streak': bonus_streak,
        'nivel_anterior': estado.nivel,
        'nivel_atual': estado_final.nivel,
        'subiu_nivel': subiu_nivel,
        'streak_atual': estado_final.streak_atual,
        'ganhou_streak': ganhou_streak,
        'novas_conquistas': [
            {
                'codigo': c.codigo,
                'nome': c.nome,
                'descricao': c.descricao,
                'icone': c.icone,
                'fp_recompensa': c.fp_recompensa,
                'raridade': c.raridade,
            }
            for c in novas_conquistas
        ],
        'progresso_nivel': calcular_progresso_nivel(estado_final.total_fp, estado_final.nivel),
        'fp_para_proximo': calcular_fp_para_proximo_nivel(estado_final.nivel),
    }

    return (estado_final, resultado)


# ============================================================================
# FUNÇÕES AUXILIARES - CONVERSÃO
# ============================================================================

def estado_de_dict(data: Dict[str, Any]) -> EstadoGamificacao:
    """Converte dict para EstadoGamificacao"""
    return EstadoGamificacao(
        total_fp=data.get('total_fp', 0),
        nivel=data.get('nivel', 1),
        conquistas=tuple(data.get('conquistas', [])),
        streak_atual=data.get('streak_atual', 0),
        streak_maximo=data.get('streak_maximo', 0),
        ultima_atividade=data.get('ultima_atividade'),
        total_questoes=data.get('total_questoes', 0),
        total_acertos=data.get('total_acertos', 0),
        total_sessoes=data.get('total_sessoes', 0),
        total_pecas=data.get('total_pecas', 0),
        taxa_acerto=data.get('taxa_acerto', 0.0),
    )


def estado_para_dict(estado: EstadoGamificacao) -> Dict[str, Any]:
    """Converte EstadoGamificacao para dict"""
    return {
        'total_fp': estado.total_fp,
        'nivel': estado.nivel,
        'conquistas': list(estado.conquistas),
        'streak_atual': estado.streak_atual,
        'streak_maximo': estado.streak_maximo,
        'ultima_atividade': estado.ultima_atividade.isoformat() if estado.ultima_atividade else None,
        'total_questoes': estado.total_questoes,
        'total_acertos': estado.total_acertos,
        'total_sessoes': estado.total_sessoes,
        'total_pecas': estado.total_pecas,
        'taxa_acerto': estado.taxa_acerto,
    }


def obter_catalogo_conquistas() -> List[Dict[str, Any]]:
    """Retorna catálogo de conquistas como lista de dicts"""
    return [
        {
            'codigo': c.codigo,
            'nome': c.nome,
            'descricao': c.descricao,
            'icone': c.icone,
            'categoria': c.categoria,
            'fp_recompensa': c.fp_recompensa,
            'criterio_tipo': c.criterio_tipo,
            'criterio_valor': c.criterio_valor,
            'raridade': c.raridade,
        }
        for c in CONQUISTAS_CATALOGO
    ]
