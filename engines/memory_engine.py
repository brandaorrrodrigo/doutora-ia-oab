"""
JURIS_IA_CORE_V1 - MEMORY ENGINE
Motor de Memória e Revisão Espaçada para Direito

Este módulo implementa o sistema de revisão espaçada científica adaptado
para conteúdo jurídico, garantindo fixação de longo prazo.

Ciclo 1-24-7:
- 1 hora: fixação imediata
- 24 horas: consolidação
- 7 dias: memória de longo prazo

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import heapq


# ============================================================
# TIPOS E ENUMS
# ============================================================

class ReviewCycle(Enum):
    """Ciclos de revisão"""
    CYCLE_1H = "1h"       # 1 hora depois
    CYCLE_24H = "24h"     # 24 horas depois
    CYCLE_7D = "7d"       # 7 dias depois
    CYCLE_30D = "30d"     # 30 dias depois (bônus)


class MemoryStrength(Enum):
    """Força da memória"""
    FRAGIL = 1      # Precisa revisão urgente
    FRACA = 2       # Precisa revisão em breve
    MEDIA = 3       # Memória consolidando
    FORTE = 4       # Bem fixado
    DOMINADO = 5    # Totalmente dominado


@dataclass
class ReviewItem:
    """Item para revisão"""
    topico: str
    disciplina: str
    conceitos: List[str]
    artigos_relacionados: List[str]
    aprendido_em: datetime
    proxima_revisao: datetime
    ciclo_atual: ReviewCycle
    forca_memoria: MemoryStrength
    acertos_consecutivos: int = 0
    erros_na_revisao: int = 0
    ultima_revisao: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class ReviewSession:
    """Sessão de revisão agendada"""
    session_id: str
    aluno_id: str
    itens: List[ReviewItem]
    agendada_para: datetime
    tipo: str  # "drill", "simulado", "teoria"
    disciplina: Optional[str] = None
    concluida: bool = False
    resultado: Optional[Dict] = None


# ============================================================
# MEMORY ENGINE
# ============================================================

class MemoryEngine:
    """
    Motor de memória e revisão espaçada.

    Funcionalidades:
    - Agenda revisões no ciclo 1-24-7
    - Ajusta intervalo baseado em desempenho
    - Detecta esquecimento
    - Prioriza itens com memória frágil
    - Gera sessões de revisão otimizadas
    """

    def __init__(self):
        """Inicializa o motor de memória"""
        self.items_por_aluno: Dict[str, List[ReviewItem]] = {}
        self.sessoes_agendadas: List[ReviewSession] = []
        self.historico_revisoes: List[Dict] = []

    def adicionar_item(
        self,
        aluno_id: str,
        topico: str,
        disciplina: str,
        conceitos: List[str],
        artigos: List[str]
    ) -> ReviewItem:
        """
        Adiciona novo item para rastreamento de memória.

        Args:
            aluno_id: ID do aluno
            topico: Tópico aprendido
            disciplina: Disciplina jurídica
            conceitos: Lista de conceitos abordados
            artigos: Artigos de lei relacionados

        Returns:
            ReviewItem criado
        """
        agora = datetime.now()

        item = ReviewItem(
            topico=topico,
            disciplina=disciplina,
            conceitos=conceitos,
            artigos_relacionados=artigos,
            aprendido_em=agora,
            proxima_revisao=agora + timedelta(hours=1),  # Primeira revisão em 1h
            ciclo_atual=ReviewCycle.CYCLE_1H,
            forca_memoria=MemoryStrength.FRAGIL
        )

        if aluno_id not in self.items_por_aluno:
            self.items_por_aluno[aluno_id] = []

        self.items_por_aluno[aluno_id].append(item)

        # Agenda primeira revisão
        self._agendar_revisao(aluno_id, item)

        return item

    def processar_revisao(
        self,
        aluno_id: str,
        topico: str,
        acertou: bool
    ) -> Dict:
        """
        Processa resultado de uma revisão.

        Args:
            aluno_id: ID do aluno
            topico: Tópico revisado
            acertou: Se o aluno acertou a revisão

        Returns:
            Dict com status e próxima revisão
        """
        item = self._buscar_item(aluno_id, topico)
        if not item:
            return {"erro": "Item não encontrado"}

        agora = datetime.now()
        item.ultima_revisao = agora

        if acertou:
            # Acerto: fortalece memória e avança ciclo
            item.acertos_consecutivos += 1
            self._fortalecer_memoria(item)
            self._avancar_ciclo(item)
        else:
            # Erro: enfraquece memória e reinicia ciclo
            item.erros_na_revisao += 1
            item.acertos_consecutivos = 0
            self._enfraquecer_memoria(item)
            self._reiniciar_ciclo(item)

        # Agenda próxima revisão
        self._agendar_revisao(aluno_id, item)

        # Registra no histórico
        self.historico_revisoes.append({
            "aluno_id": aluno_id,
            "topico": topico,
            "timestamp": agora.isoformat(),
            "acertou": acertou,
            "ciclo": item.ciclo_atual.value,
            "forca_memoria": item.forca_memoria.value
        })

        return {
            "status": "processado",
            "forca_memoria": item.forca_memoria.name,
            "proxima_revisao": item.proxima_revisao.isoformat(),
            "ciclo_atual": item.ciclo_atual.value,
            "acertos_consecutivos": item.acertos_consecutivos
        }

    def obter_itens_revisar(
        self,
        aluno_id: str,
        limite: int = 10
    ) -> List[ReviewItem]:
        """
        Obtém itens que precisam ser revisados agora.

        Args:
            aluno_id: ID do aluno
            limite: Número máximo de itens

        Returns:
            Lista de itens para revisão, priorizados
        """
        if aluno_id not in self.items_por_aluno:
            return []

        agora = datetime.now()
        itens_pendentes = []

        for item in self.items_por_aluno[aluno_id]:
            if item.proxima_revisao <= agora:
                # Calcula prioridade baseada em força da memória e atraso
                atraso = (agora - item.proxima_revisao).total_seconds() / 3600  # horas
                prioridade = self._calcular_prioridade(item, atraso)

                itens_pendentes.append((prioridade, item))

        # Ordena por prioridade (maior primeiro) e retorna top N
        itens_pendentes.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in itens_pendentes[:limite]]

    def gerar_sessao_revisao(
        self,
        aluno_id: str,
        tipo: str = "drill",
        disciplina: Optional[str] = None,
        duracao_minutos: int = 30
    ) -> ReviewSession:
        """
        Gera sessão de revisão otimizada.

        Args:
            aluno_id: ID do aluno
            tipo: Tipo de sessão ("drill", "simulado", "teoria")
            disciplina: Filtrar por disciplina (opcional)
            duracao_minutos: Duração planejada em minutos

        Returns:
            ReviewSession configurada
        """
        # Estima quantos itens cabem na sessão (média 3min/item)
        qtd_itens = duracao_minutos // 3

        # Obtém itens prioritários
        itens_todos = self.obter_itens_revisar(aluno_id, limite=50)

        # Filtra por disciplina se especificado
        if disciplina:
            itens_todos = [i for i in itens_todos if i.disciplina == disciplina]

        # Seleciona itens para a sessão
        itens_sessao = self._selecionar_itens_sessao(
            itens_todos,
            qtd_itens,
            tipo
        )

        # Cria sessão
        session_id = f"rev_{aluno_id}_{int(datetime.now().timestamp())}"
        sessao = ReviewSession(
            session_id=session_id,
            aluno_id=aluno_id,
            itens=itens_sessao,
            agendada_para=datetime.now(),
            tipo=tipo,
            disciplina=disciplina
        )

        self.sessoes_agendadas.append(sessao)

        return sessao

    def analisar_memoria(self, aluno_id: str) -> Dict:
        """
        Analisa estado da memória do aluno.

        Returns:
            Dict com estatísticas de memória
        """
        if aluno_id not in self.items_por_aluno:
            return {"erro": "Aluno não encontrado"}

        itens = self.items_por_aluno[aluno_id]

        # Estatísticas gerais
        total_itens = len(itens)
        if total_itens == 0:
            return {"total_itens": 0}

        # Distribuição por força de memória
        distribuicao = {forca.name: 0 for forca in MemoryStrength}
        for item in itens:
            distribuicao[item.forca_memoria.name] += 1

        # Itens em cada ciclo
        por_ciclo = {ciclo.value: 0 for ciclo in ReviewCycle}
        for item in itens:
            por_ciclo[item.ciclo_atual.value] += 1

        # Itens atrasados
        agora = datetime.now()
        atrasados = sum(1 for item in itens if item.proxima_revisao < agora)

        # Conceitos dominados vs frágeis
        conceitos_dominados = [
            item.topico for item in itens
            if item.forca_memoria == MemoryStrength.DOMINADO
        ]
        conceitos_frageis = [
            item.topico for item in itens
            if item.forca_memoria in [MemoryStrength.FRAGIL, MemoryStrength.FRACA]
        ]

        # Taxa de retenção (acertos consecutivos >= 3)
        retencao = sum(1 for item in itens if item.acertos_consecutivos >= 3)
        taxa_retencao = (retencao / total_itens) * 100 if total_itens > 0 else 0

        return {
            "total_itens": total_itens,
            "distribuicao_forca": distribuicao,
            "por_ciclo": por_ciclo,
            "itens_atrasados": atrasados,
            "conceitos_dominados": conceitos_dominados,
            "conceitos_frageis": conceitos_frageis,
            "taxa_retencao": round(taxa_retencao, 1),
            "proxima_revisao": self._proxima_revisao_urgente(itens)
        }

    def detectar_esquecimento(self, aluno_id: str) -> List[Dict]:
        """
        Detecta conceitos que o aluno está esquecendo.

        Returns:
            Lista de alertas de esquecimento
        """
        if aluno_id not in self.items_por_aluno:
            return []

        alertas = []
        agora = datetime.now()

        for item in self.items_por_aluno[aluno_id]:
            # Esquecimento detectado se:
            # 1. Tinha memória forte mas errou na última revisão
            # 2. Está muito atrasado na revisão
            # 3. Múltiplos erros recentes

            # Caso 1: Regressão de memória
            if (item.forca_memoria.value <= 2 and
                item.ultima_revisao and
                item.erros_na_revisao > 0):
                alertas.append({
                    "tipo": "regressao",
                    "topico": item.topico,
                    "disciplina": item.disciplina,
                    "gravidade": "ALTA",
                    "mensagem": f"Conceito {item.topico} está sendo esquecido - reforço urgente"
                })

            # Caso 2: Revisão muito atrasada
            atraso_horas = (agora - item.proxima_revisao).total_seconds() / 3600
            if atraso_horas > 48:  # 2 dias atrasado
                alertas.append({
                    "tipo": "atraso_critico",
                    "topico": item.topico,
                    "disciplina": item.disciplina,
                    "gravidade": "MEDIA",
                    "atraso_horas": int(atraso_horas),
                    "mensagem": f"Revisão de {item.topico} atrasada há {int(atraso_horas)}h"
                })

            # Caso 3: Múltiplos erros
            if item.erros_na_revisao >= 3:
                alertas.append({
                    "tipo": "dificuldade_persistente",
                    "topico": item.topico,
                    "disciplina": item.disciplina,
                    "gravidade": "ALTA",
                    "erros": item.erros_na_revisao,
                    "mensagem": f"{item.topico} com {item.erros_na_revisao} erros - base conceitual frágil"
                })

        # Ordena por gravidade
        ordem_gravidade = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}
        alertas.sort(key=lambda x: ordem_gravidade.get(x["gravidade"], 3))

        return alertas

    # ============================================================
    # MÉTODOS PRIVADOS
    # ============================================================

    def _buscar_item(self, aluno_id: str, topico: str) -> Optional[ReviewItem]:
        """Busca item específico"""
        if aluno_id not in self.items_por_aluno:
            return None

        for item in self.items_por_aluno[aluno_id]:
            if item.topico == topico:
                return item

        return None

    def _fortalecer_memoria(self, item: ReviewItem):
        """Fortalece memória do item"""
        if item.forca_memoria.value < 5:
            item.forca_memoria = MemoryStrength(item.forca_memoria.value + 1)

    def _enfraquecer_memoria(self, item: ReviewItem):
        """Enfraquece memória do item"""
        if item.forca_memoria.value > 1:
            item.forca_memoria = MemoryStrength(item.forca_memoria.value - 1)

    def _avancar_ciclo(self, item: ReviewItem):
        """Avança para próximo ciclo de revisão"""
        agora = datetime.now()

        if item.ciclo_atual == ReviewCycle.CYCLE_1H:
            item.ciclo_atual = ReviewCycle.CYCLE_24H
            item.proxima_revisao = agora + timedelta(hours=24)

        elif item.ciclo_atual == ReviewCycle.CYCLE_24H:
            item.ciclo_atual = ReviewCycle.CYCLE_7D
            item.proxima_revisao = agora + timedelta(days=7)

        elif item.ciclo_atual == ReviewCycle.CYCLE_7D:
            item.ciclo_atual = ReviewCycle.CYCLE_30D
            item.proxima_revisao = agora + timedelta(days=30)

        else:  # CYCLE_30D
            # Mantém no ciclo de 30 dias
            item.proxima_revisao = agora + timedelta(days=30)

    def _reiniciar_ciclo(self, item: ReviewItem):
        """Reinicia ciclo de revisão (devido a erro)"""
        agora = datetime.now()

        # Volta para ciclo 1h, mas com intervalo ajustado
        item.ciclo_atual = ReviewCycle.CYCLE_1H
        item.proxima_revisao = agora + timedelta(hours=1)

    def _agendar_revisao(self, aluno_id: str, item: ReviewItem):
        """Agenda próxima revisão do item"""
        # Em produção, enviaria notificação/alerta
        pass

    def _calcular_prioridade(self, item: ReviewItem, atraso_horas: float) -> float:
        """
        Calcula prioridade de revisão.

        Quanto maior a prioridade, mais urgente.
        """
        # Base: força da memória (invertido - frágil é prioritário)
        prioridade = 6 - item.forca_memoria.value  # 5 a 1

        # Fator de atraso (exponencial)
        if atraso_horas > 0:
            prioridade += min(atraso_horas / 24, 5)  # Max +5 pontos

        # Penaliza múltiplos erros (muito urgente)
        if item.erros_na_revisao >= 3:
            prioridade += 10

        # Bônus para itens no ciclo inicial (fixar bem)
        if item.ciclo_atual == ReviewCycle.CYCLE_1H:
            prioridade += 2

        return prioridade

    def _selecionar_itens_sessao(
        self,
        itens_disponiveis: List[ReviewItem],
        quantidade: int,
        tipo: str
    ) -> List[ReviewItem]:
        """Seleciona itens ideais para sessão"""

        if tipo == "drill":
            # Drill: prioriza itens frágeis
            itens_ordenados = sorted(
                itens_disponiveis,
                key=lambda i: i.forca_memoria.value
            )

        elif tipo == "simulado":
            # Simulado: mix balanceado
            itens_ordenados = sorted(
                itens_disponiveis,
                key=lambda i: (i.forca_memoria.value, i.acertos_consecutivos)
            )

        else:  # teoria
            # Teoria: foca em conceitos não dominados
            itens_ordenados = [
                i for i in itens_disponiveis
                if i.forca_memoria.value <= 3
            ]

        return itens_ordenados[:quantidade]

    def _proxima_revisao_urgente(self, itens: List[ReviewItem]) -> Optional[str]:
        """Encontra próxima revisão mais urgente"""
        if not itens:
            return None

        proximo = min(itens, key=lambda i: i.proxima_revisao)
        return proximo.proxima_revisao.isoformat()


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_memory_engine() -> MemoryEngine:
    """Factory function para criar memory engine"""
    return MemoryEngine()


def ciclo_1_24_7(
    engine: MemoryEngine,
    aluno_id: str,
    topico: str,
    disciplina: str,
    conceitos: List[str],
    artigos: List[str]
) -> Dict:
    """
    Implementa ciclo completo 1-24-7 para um tópico.

    Returns:
        Dict com cronograma de revisões
    """
    # Adiciona item ao engine
    item = engine.adicionar_item(
        aluno_id=aluno_id,
        topico=topico,
        disciplina=disciplina,
        conceitos=conceitos,
        artigos=artigos
    )

    # Calcula datas das revisões
    agora = datetime.now()
    revisao_1h = agora + timedelta(hours=1)
    revisao_24h = agora + timedelta(hours=24)
    revisao_7d = agora + timedelta(days=7)

    return {
        "topico": topico,
        "cronograma": {
            "1h": revisao_1h.isoformat(),
            "24h": revisao_24h.isoformat(),
            "7d": revisao_7d.isoformat()
        },
        "instrucoes": {
            "1h": "Drill rápido: 3 questões conceituais sobre o tópico",
            "24h": "Drill médio: 5 questões com variações do tema",
            "7d": "Drill completo: 10 questões mesclando com outros temas"
        }
    }


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Cria engine
    engine = criar_memory_engine()

    print("=" * 60)
    print("MEMORY ENGINE - EXEMPLO DE USO")
    print("=" * 60)

    aluno_id = "aluno_123"

    # Adiciona alguns itens
    print("\n1. ADICIONANDO ITENS PARA MEMÓRIA")
    print("-" * 60)

    item1 = engine.adicionar_item(
        aluno_id=aluno_id,
        topico="Dolo eventual vs Culpa consciente",
        disciplina="Direito Penal",
        conceitos=["dolo", "culpa", "vontade", "previsibilidade"],
        artigos=["CP art. 18, I e II"]
    )
    print(f"✓ Adicionado: {item1.topico}")
    print(f"  Primeira revisão em: {item1.proxima_revisao}")

    item2 = engine.adicionar_item(
        aluno_id=aluno_id,
        topico="Legítima defesa",
        disciplina="Direito Penal",
        conceitos=["excludente", "agressão injusta", "moderação"],
        artigos=["CP art. 23, II", "CP art. 25"]
    )
    print(f"✓ Adicionado: {item2.topico}")

    # Simula passagem de tempo e revisões
    print("\n2. SIMULANDO REVISÕES")
    print("-" * 60)

    # Primeira revisão: ACERTO
    resultado1 = engine.processar_revisao(
        aluno_id=aluno_id,
        topico="Dolo eventual vs Culpa consciente",
        acertou=True
    )
    print(f"Revisão 1: ACERTO")
    print(f"  Força memória: {resultado1['forca_memoria']}")
    print(f"  Próxima revisão: {resultado1['proxima_revisao']}")

    # Segunda revisão: ACERTO
    resultado2 = engine.processar_revisao(
        aluno_id=aluno_id,
        topico="Dolo eventual vs Culpa consciente",
        acertou=True
    )
    print(f"\nRevisão 2: ACERTO")
    print(f"  Força memória: {resultado2['forca_memoria']}")
    print(f"  Acertos consecutivos: {resultado2['acertos_consecutivos']}")

    # Terceira revisão: ERRO (simula esquecimento)
    resultado3 = engine.processar_revisao(
        aluno_id=aluno_id,
        topico="Legítima defesa",
        acertou=False
    )
    print(f"\nRevisão 3: ERRO")
    print(f"  Força memória: {resultado3['forca_memoria']}")
    print(f"  Ciclo atual: {resultado3['ciclo_atual']}")

    # Análise de memória
    print("\n3. ANÁLISE DE MEMÓRIA")
    print("-" * 60)

    analise = engine.analisar_memoria(aluno_id)
    print(json.dumps(analise, indent=2, ensure_ascii=False))

    # Detecção de esquecimento
    print("\n4. DETECÇÃO DE ESQUECIMENTO")
    print("-" * 60)

    alertas = engine.detectar_esquecimento(aluno_id)
    if alertas:
        print(f"⚠️  {len(alertas)} alerta(s) detectado(s):")
        for alerta in alertas:
            print(f"\n  [{alerta['gravidade']}] {alerta['tipo']}")
            print(f"  {alerta['mensagem']}")
    else:
        print("✓ Nenhum problema de memória detectado")

    # Gera sessão de revisão
    print("\n5. GERANDO SESSÃO DE REVISÃO")
    print("-" * 60)

    sessao = engine.gerar_sessao_revisao(
        aluno_id=aluno_id,
        tipo="drill",
        duracao_minutos=30
    )

    print(f"Sessão ID: {sessao.session_id}")
    print(f"Tipo: {sessao.tipo}")
    print(f"Itens: {len(sessao.itens)}")
    for idx, item in enumerate(sessao.itens, 1):
        print(f"  {idx}. {item.topico} (força: {item.forca_memoria.name})")

    # Demonstra ciclo 1-24-7
    print("\n6. CICLO 1-24-7 COMPLETO")
    print("-" * 60)

    cronograma = ciclo_1_24_7(
        engine=engine,
        aluno_id=aluno_id,
        topico="Estado de necessidade",
        disciplina="Direito Penal",
        conceitos=["excludente", "perigo atual", "sacrifício do bem menor"],
        artigos=["CP art. 23, I", "CP art. 24"]
    )

    print(json.dumps(cronograma, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("MEMORY ENGINE - OPERACIONAL")
    print("=" * 60)
