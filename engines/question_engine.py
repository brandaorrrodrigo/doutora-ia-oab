"""
JURIS_IA_CORE_V1 - QUESTION ENGINE
Motor de Geração e Seleção de Questões OAB

Este módulo gerencia banco de questões, gera drills personalizados,
e seleciona questões ideais baseadas no perfil do estudante.

Funcionalidades:
- Seleção inteligente de questões
- Geração de drills focados
- Ajuste dinâmico de dificuldade
- Análise de padrões de erro
- Criação de simulados

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
import random
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


# ============================================================
# TIPOS E ENUMS
# ============================================================

class DifficultyLevel(Enum):
    """Nível de dificuldade"""
    FACIL = 1
    MEDIO = 2
    DIFICIL = 3
    MUITO_DIFICIL = 4


class QuestionType(Enum):
    """Tipo de questão"""
    MULTIPLA_ESCOLHA = "multipla_escolha"
    VERDADEIRO_FALSO = "verdadeiro_falso"
    CASO_PRATICO = "caso_pratico"
    DISSERTATIVA = "dissertativa"


@dataclass
class Alternative:
    """Alternativa de questão"""
    letra: str
    texto: str
    correta: bool
    explicacao_erro: Optional[str] = None
    pegadinha: Optional[str] = None


@dataclass
class Question:
    """Questão OAB completa"""
    id: str
    enunciado: str
    alternativas: List[Alternative]
    tipo: QuestionType
    disciplina: str
    topico: str
    subtopicos: List[str]
    dificuldade: DifficultyLevel
    artigos_relacionados: List[str]
    conceitos_testados: List[str]

    # Metadados
    ano_prova: Optional[int] = None
    exame: Optional[str] = None  # "XXXII", "XXXIII", etc
    taxa_acerto_geral: Optional[float] = None
    taxa_acerto_banco: float = 0.0  # Taxa no nosso banco
    vezes_respondida: int = 0

    # Explicação multinível
    explicacao_nivel_1: Optional[str] = None  # Técnica
    explicacao_nivel_2: Optional[str] = None  # Didática
    explicacao_nivel_3: Optional[str] = None  # Analogia
    explicacao_nivel_4: Optional[str] = None  # Prática

    # Tags
    tags: List[str] = field(default_factory=list)
    pegadinhas_comuns: List[str] = field(default_factory=list)


@dataclass
class Drill:
    """Drill personalizado"""
    drill_id: str
    aluno_id: str
    objetivo: str
    questoes: List[Question]
    foco: str  # "conceito", "pegadinha", "velocidade", "revisao"
    tempo_estimado_minutos: int
    disciplina: Optional[str] = None
    created_at: str = ""


@dataclass
class Simulado:
    """Simulado completo OAB"""
    simulado_id: str
    aluno_id: str
    questoes: List[Question]
    disciplinas_cobertas: List[str]
    tempo_limite_minutos: int = 300  # 5 horas padrão OAB
    tipo: str = "completo"  # "completo", "disciplina_especifica"


# ============================================================
# QUESTION ENGINE
# ============================================================

class QuestionEngine:
    """
    Motor de questões para sistema OAB.

    Responsabilidades:
    - Gerenciar banco de questões
    - Selecionar questões ideais
    - Gerar drills personalizados
    - Ajustar dificuldade dinamicamente
    - Criar simulados balanceados
    """

    def __init__(self, questoes_path: str = None):
        """
        Inicializa o motor de questões.

        Args:
            questoes_path: Caminho para banco de questões
        """
        self.questoes_path = questoes_path
        self.banco_questoes: Dict[str, Question] = {}
        self.questoes_por_disciplina: Dict[str, List[str]] = defaultdict(list)
        self.questoes_por_topico: Dict[str, List[str]] = defaultdict(list)
        self.questoes_por_dificuldade: Dict[DifficultyLevel, List[str]] = defaultdict(list)

        # Histórico de respostas por aluno
        self.historico_respostas: Dict[str, List[Dict]] = defaultdict(list)

        # Performance por tópico por aluno
        self.performance_topico: Dict[str, Dict[str, float]] = defaultdict(dict)

    def adicionar_questao(self, questao: Question):
        """Adiciona questão ao banco"""
        self.banco_questoes[questao.id] = questao

        # Indexa por disciplina
        self.questoes_por_disciplina[questao.disciplina].append(questao.id)

        # Indexa por tópico
        self.questoes_por_topico[questao.topico].append(questao.id)

        # Indexa por dificuldade
        self.questoes_por_dificuldade[questao.dificuldade].append(questao.id)

    def gerar_drill_personalizado(
        self,
        aluno_id: str,
        foco: str,
        disciplina: Optional[str] = None,
        topico: Optional[str] = None,
        quantidade: int = 10
    ) -> Drill:
        """
        Gera drill personalizado baseado em foco específico.

        Args:
            aluno_id: ID do aluno
            foco: Tipo de drill ("conceito", "pegadinha", "velocidade", "revisao")
            disciplina: Disciplina específica (opcional)
            topico: Tópico específico (opcional)
            quantidade: Número de questões

        Returns:
            Drill configurado
        """
        questoes_selecionadas = []

        if foco == "conceito":
            # Drill conceitual: questões sobre conceitos não dominados
            questoes_selecionadas = self._selecionar_questoes_conceituais(
                aluno_id, disciplina, topico, quantidade
            )

        elif foco == "pegadinha":
            # Drill de pegadinhas: questões com pegadinhas típicas
            questoes_selecionadas = self._selecionar_questoes_pegadinha(
                disciplina, topico, quantidade
            )

        elif foco == "velocidade":
            # Drill de velocidade: questões mais fáceis para ganhar agilidade
            questoes_selecionadas = self._selecionar_questoes_velocidade(
                aluno_id, disciplina, quantidade
            )

        elif foco == "revisao":
            # Drill de revisão: questões sobre tópicos já estudados
            questoes_selecionadas = self._selecionar_questoes_revisao(
                aluno_id, disciplina, topico, quantidade
            )

        else:
            # Drill misto
            questoes_selecionadas = self._selecionar_questoes_balanceadas(
                aluno_id, disciplina, quantidade
            )

        # Estima tempo (3 min por questão)
        tempo_estimado = len(questoes_selecionadas) * 3

        drill = Drill(
            drill_id=f"drill_{aluno_id}_{foco}_{len(self.historico_respostas[aluno_id])}",
            aluno_id=aluno_id,
            objetivo=self._gerar_objetivo_drill(foco, disciplina, topico),
            questoes=questoes_selecionadas,
            foco=foco,
            tempo_estimado_minutos=tempo_estimado,
            disciplina=disciplina
        )

        return drill

    def gerar_simulado(
        self,
        aluno_id: str,
        tipo: str = "completo",
        disciplina: Optional[str] = None
    ) -> Simulado:
        """
        Gera simulado OAB.

        Args:
            aluno_id: ID do aluno
            tipo: "completo" ou "disciplina_especifica"
            disciplina: Disciplina específica (se tipo for disciplina_especifica)

        Returns:
            Simulado configurado
        """
        if tipo == "completo":
            # Simulado completo OAB: 80 questões, todas as disciplinas
            questoes = self._selecionar_questoes_simulado_completo(aluno_id)
        else:
            # Simulado de disciplina: 30 questões de uma disciplina
            questoes = self._selecionar_questoes_por_disciplina(
                disciplina or "Direito Constitucional",
                quantidade=30
            )

        # Identifica disciplinas cobertas
        disciplinas = list(set(q.disciplina for q in questoes))

        simulado = Simulado(
            simulado_id=f"sim_{aluno_id}_{tipo}_{len(self.historico_respostas[aluno_id])}",
            aluno_id=aluno_id,
            questoes=questoes,
            disciplinas_cobertas=disciplinas,
            tipo=tipo
        )

        return simulado

    def registrar_resposta(
        self,
        aluno_id: str,
        questao_id: str,
        alternativa_escolhida: str,
        tempo_segundos: int
    ) -> Dict:
        """
        Registra resposta do aluno e retorna feedback.

        Args:
            aluno_id: ID do aluno
            questao_id: ID da questão
            alternativa_escolhida: Letra da alternativa
            tempo_segundos: Tempo gasto na questão

        Returns:
            Dict com feedback e próxima ação
        """
        questao = self.banco_questoes.get(questao_id)
        if not questao:
            return {"erro": "Questão não encontrada"}

        # Verifica se acertou
        alternativa_correta = next(
            (a for a in questao.alternativas if a.correta),
            None
        )
        acertou = alternativa_escolhida == alternativa_correta.letra

        # Atualiza estatísticas da questão
        questao.vezes_respondida += 1
        if acertou:
            questao.taxa_acerto_banco = (
                (questao.taxa_acerto_banco * (questao.vezes_respondida - 1) + 1) /
                questao.vezes_respondida
            )
        else:
            questao.taxa_acerto_banco = (
                (questao.taxa_acerto_banco * (questao.vezes_respondida - 1)) /
                questao.vezes_respondida
            )

        # Registra no histórico
        self.historico_respostas[aluno_id].append({
            "questao_id": questao_id,
            "disciplina": questao.disciplina,
            "topico": questao.topico,
            "acertou": acertou,
            "alternativa_escolhida": alternativa_escolhida,
            "tempo_segundos": tempo_segundos,
            "dificuldade": questao.dificuldade.value
        })

        # Atualiza performance no tópico
        self._atualizar_performance_topico(aluno_id, questao.topico, acertou)

        # Gera feedback
        feedback = self._gerar_feedback(questao, alternativa_escolhida, acertou, tempo_segundos)

        # Recomenda próxima ação
        proxima_acao = self._recomendar_proxima_acao(aluno_id, questao, acertou)

        return {
            "acertou": acertou,
            "feedback": feedback,
            "proxima_acao": proxima_acao,
            "estatisticas": {
                "taxa_acerto_questao": round(questao.taxa_acerto_banco * 100, 1),
                "dificuldade": questao.dificuldade.name,
                "tempo_gasto": tempo_segundos
            }
        }

    def ajustar_dificuldade_dinamica(
        self,
        aluno_id: str,
        disciplina: Optional[str] = None
    ) -> DifficultyLevel:
        """
        Ajusta dificuldade baseada no desempenho recente.

        Args:
            aluno_id: ID do aluno
            disciplina: Disciplina específica (opcional)

        Returns:
            Nível de dificuldade recomendado
        """
        # Analisa últimas 10 respostas
        ultimas = self.historico_respostas[aluno_id][-10:]

        if disciplina:
            ultimas = [r for r in ultimas if r["disciplina"] == disciplina]

        if len(ultimas) < 5:
            return DifficultyLevel.MEDIO  # Padrão

        # Calcula taxa de acerto recente
        acertos = sum(1 for r in ultimas if r["acertou"])
        taxa = acertos / len(ultimas)

        # Ajusta dificuldade
        if taxa >= 0.8:
            # Muito bem: aumenta dificuldade
            return DifficultyLevel.DIFICIL
        elif taxa >= 0.6:
            # Bem: mantém médio ou sobe um pouco
            return DifficultyLevel.MEDIO
        elif taxa >= 0.4:
            # Razoável: mantém médio
            return DifficultyLevel.MEDIO
        else:
            # Mal: reduz dificuldade
            return DifficultyLevel.FACIL

    def analisar_desempenho(self, aluno_id: str) -> Dict:
        """
        Analisa desempenho geral do aluno.

        Returns:
            Dict com análise completa
        """
        respostas = self.historico_respostas[aluno_id]

        if not respostas:
            return {"erro": "Sem dados suficientes"}

        # Estatísticas gerais
        total = len(respostas)
        acertos = sum(1 for r in respostas if r["acertou"])
        taxa_geral = (acertos / total) * 100

        # Por disciplina
        por_disciplina = defaultdict(lambda: {"total": 0, "acertos": 0})
        for r in respostas:
            por_disciplina[r["disciplina"]]["total"] += 1
            if r["acertou"]:
                por_disciplina[r["disciplina"]]["acertos"] += 1

        taxas_disciplina = {
            disc: round((dados["acertos"] / dados["total"]) * 100, 1)
            for disc, dados in por_disciplina.items()
        }

        # Identifica pontos fortes e fracos
        fortes = [disc for disc, taxa in taxas_disciplina.items() if taxa >= 70]
        fracos = [disc for disc, taxa in taxas_disciplina.items() if taxa < 50]

        # Tempo médio
        tempo_medio = sum(r["tempo_segundos"] for r in respostas) / total

        return {
            "total_questoes": total,
            "acertos": acertos,
            "taxa_acerto_geral": round(taxa_geral, 1),
            "por_disciplina": taxas_disciplina,
            "disciplinas_fortes": fortes,
            "disciplinas_fracas": fracos,
            "tempo_medio_segundos": int(tempo_medio),
            "performance_topicos": dict(self.performance_topico[aluno_id])
        }

    # ============================================================
    # MÉTODOS PRIVADOS - SELEÇÃO DE QUESTÕES
    # ============================================================

    def _selecionar_questoes_conceituais(
        self,
        aluno_id: str,
        disciplina: Optional[str],
        topico: Optional[str],
        quantidade: int
    ) -> List[Question]:
        """Seleciona questões para drill conceitual"""
        # Identifica conceitos não dominados
        conceitos_fracos = self._identificar_conceitos_fracos(aluno_id)

        candidatas = []
        for q_id, questao in self.banco_questoes.items():
            # Filtros
            if disciplina and questao.disciplina != disciplina:
                continue
            if topico and questao.topico != topico:
                continue

            # Prioriza questões que testam conceitos fracos
            for conceito in questao.conceitos_testados:
                if conceito in conceitos_fracos:
                    candidatas.append(questao)
                    break

        # Se não encontrou suficientes, adiciona questões gerais
        if len(candidatas) < quantidade:
            for q_id, questao in self.banco_questoes.items():
                if questao not in candidatas:
                    if not disciplina or questao.disciplina == disciplina:
                        candidatas.append(questao)

        # Embaralha e retorna
        random.shuffle(candidatas)
        return candidatas[:quantidade]

    def _selecionar_questoes_pegadinha(
        self,
        disciplina: Optional[str],
        topico: Optional[str],
        quantidade: int
    ) -> List[Question]:
        """Seleciona questões com pegadinhas típicas"""
        candidatas = []

        for q_id, questao in self.banco_questoes.items():
            # Filtros
            if disciplina and questao.disciplina != disciplina:
                continue
            if topico and questao.topico != topico:
                continue

            # Prioriza questões com pegadinhas identificadas
            if questao.pegadinhas_comuns:
                candidatas.append(questao)

        random.shuffle(candidatas)
        return candidatas[:quantidade]

    def _selecionar_questoes_velocidade(
        self,
        aluno_id: str,
        disciplina: Optional[str],
        quantidade: int
    ) -> List[Question]:
        """Seleciona questões mais fáceis para treinar velocidade"""
        candidatas = []

        # Prioriza questões fáceis
        for q_id in self.questoes_por_dificuldade[DifficultyLevel.FACIL]:
            questao = self.banco_questoes[q_id]
            if not disciplina or questao.disciplina == disciplina:
                candidatas.append(questao)

        # Adiciona algumas médias se necessário
        if len(candidatas) < quantidade:
            for q_id in self.questoes_por_dificuldade[DifficultyLevel.MEDIO]:
                questao = self.banco_questoes[q_id]
                if not disciplina or questao.disciplina == disciplina:
                    candidatas.append(questao)

        random.shuffle(candidatas)
        return candidatas[:quantidade]

    def _selecionar_questoes_revisao(
        self,
        aluno_id: str,
        disciplina: Optional[str],
        topico: Optional[str],
        quantidade: int
    ) -> List[Question]:
        """Seleciona questões para revisão de tópicos já estudados"""
        # Identifica tópicos já estudados
        topicos_estudados = set()
        for r in self.historico_respostas[aluno_id]:
            topicos_estudados.add(r["topico"])

        candidatas = []
        for q_id, questao in self.banco_questoes.items():
            # Filtros
            if disciplina and questao.disciplina != disciplina:
                continue
            if topico and questao.topico != topico:
                continue

            # Apenas tópicos já estudados
            if questao.topico in topicos_estudados:
                candidatas.append(questao)

        random.shuffle(candidatas)
        return candidatas[:quantidade]

    def _selecionar_questoes_balanceadas(
        self,
        aluno_id: str,
        disciplina: Optional[str],
        quantidade: int
    ) -> List[Question]:
        """Seleciona questões balanceadas por dificuldade"""
        # Mix: 30% fácil, 50% médio, 20% difícil
        qtd_facil = int(quantidade * 0.3)
        qtd_medio = int(quantidade * 0.5)
        qtd_dificil = quantidade - qtd_facil - qtd_medio

        questoes = []

        # Fáceis
        candidatas_facil = [
            self.banco_questoes[q_id]
            for q_id in self.questoes_por_dificuldade[DifficultyLevel.FACIL]
            if not disciplina or self.banco_questoes[q_id].disciplina == disciplina
        ]
        random.shuffle(candidatas_facil)
        questoes.extend(candidatas_facil[:qtd_facil])

        # Médias
        candidatas_medio = [
            self.banco_questoes[q_id]
            for q_id in self.questoes_por_dificuldade[DifficultyLevel.MEDIO]
            if not disciplina or self.banco_questoes[q_id].disciplina == disciplina
        ]
        random.shuffle(candidatas_medio)
        questoes.extend(candidatas_medio[:qtd_medio])

        # Difíceis
        candidatas_dificil = [
            self.banco_questoes[q_id]
            for q_id in self.questoes_por_dificuldade[DifficultyLevel.DIFICIL]
            if not disciplina or self.banco_questoes[q_id].disciplina == disciplina
        ]
        random.shuffle(candidatas_dificil)
        questoes.extend(candidatas_dificil[:qtd_dificil])

        # Embaralha mix final
        random.shuffle(questoes)
        return questoes

    def _selecionar_questoes_simulado_completo(self, aluno_id: str) -> List[Question]:
        """Seleciona 80 questões para simulado completo OAB"""
        # Distribuição por disciplina (aproximada OAB)
        distribuicao = {
            "Direito Constitucional": 10,
            "Direito Civil": 12,
            "Direito Processual Civil": 10,
            "Direito Penal": 10,
            "Direito Processual Penal": 8,
            "Direito do Trabalho": 8,
            "Direito Empresarial": 6,
            "Direito Tributário": 6,
            "Direito Administrativo": 5,
            "Direitos Humanos": 3,
            "Ética e Estatuto": 2
        }

        questoes = []
        for disciplina, qtd in distribuicao.items():
            candidatas = self._selecionar_questoes_por_disciplina(disciplina, qtd)
            questoes.extend(candidatas)

        # Embaralha
        random.shuffle(questoes)
        return questoes

    def _selecionar_questoes_por_disciplina(
        self,
        disciplina: str,
        quantidade: int
    ) -> List[Question]:
        """Seleciona questões de uma disciplina"""
        candidatas = [
            self.banco_questoes[q_id]
            for q_id in self.questoes_por_disciplina[disciplina]
        ]

        random.shuffle(candidatas)
        return candidatas[:quantidade]

    # ============================================================
    # MÉTODOS PRIVADOS - ANÁLISE E FEEDBACK
    # ============================================================

    def _identificar_conceitos_fracos(self, aluno_id: str) -> Set[str]:
        """Identifica conceitos que o aluno tem dificuldade"""
        conceitos_fracos = set()

        # Analisa erros recentes
        erros_recentes = [
            r for r in self.historico_respostas[aluno_id][-20:]
            if not r["acertou"]
        ]

        for erro in erros_recentes:
            questao = self.banco_questoes.get(erro["questao_id"])
            if questao:
                conceitos_fracos.update(questao.conceitos_testados)

        return conceitos_fracos

    def _atualizar_performance_topico(self, aluno_id: str, topico: str, acertou: bool):
        """Atualiza performance do aluno em um tópico"""
        if topico not in self.performance_topico[aluno_id]:
            self.performance_topico[aluno_id][topico] = 0.5  # Começa no meio

        # Média móvel ponderada
        taxa_atual = self.performance_topico[aluno_id][topico]
        nova_taxa = (taxa_atual * 0.8) + (1.0 if acertou else 0.0) * 0.2
        self.performance_topico[aluno_id][topico] = nova_taxa

    def _gerar_feedback(
        self,
        questao: Question,
        alternativa_escolhida: str,
        acertou: bool,
        tempo_segundos: int
    ) -> str:
        """Gera feedback personalizado"""
        if acertou:
            tempo_ideal = 180  # 3 minutos
            if tempo_segundos < tempo_ideal:
                return f"Excelente! Acertou em {tempo_segundos}s (rápido)."
            else:
                return f"Correto! Mas tente ser mais rápido (levou {tempo_segundos}s)."
        else:
            # Retorna explicação do erro
            alternativa = next(
                (a for a in questao.alternativas if a.letra == alternativa_escolhida),
                None
            )
            if alternativa and alternativa.explicacao_erro:
                return alternativa.explicacao_erro
            else:
                return "Resposta incorreta. Revise o conceito."

    def _recomendar_proxima_acao(
        self,
        aluno_id: str,
        questao: Question,
        acertou: bool
    ) -> str:
        """Recomenda próxima ação baseada no resultado"""
        if acertou:
            # Acertou: avança ou aumenta dificuldade
            return "Avançar para próxima questão"
        else:
            # Errou: revisar conceito
            return f"Revisar conceito: {questao.topico}"

    def _gerar_objetivo_drill(
        self,
        foco: str,
        disciplina: Optional[str],
        topico: Optional[str]
    ) -> str:
        """Gera objetivo do drill"""
        base = f"Drill de {foco}"
        if disciplina:
            base += f" - {disciplina}"
        if topico:
            base += f" - {topico}"
        return base


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_question_engine() -> QuestionEngine:
    """Factory function para criar question engine"""
    return QuestionEngine()


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Cria engine
    engine = criar_question_engine()

    print("=" * 60)
    print("QUESTION ENGINE - EXEMPLO DE USO")
    print("=" * 60)

    # Adiciona questões de exemplo
    print("\n1. ADICIONANDO QUESTÕES AO BANCO")
    print("-" * 60)

    q1 = Question(
        id="Q001",
        enunciado="Sobre dolo eventual e culpa consciente, assinale a alternativa correta:",
        alternativas=[
            Alternative("A", "Dolo eventual = prever e não querer", False,
                       "ERRADO: Dolo eventual = prever E aceitar o risco"),
            Alternative("B", "Culpa consciente = prever e aceitar", False,
                       "ERRADO: Culpa consciente = prever e CONFIAR que não acontecerá"),
            Alternative("C", "Dolo eventual = assumir o risco", True),
            Alternative("D", "São a mesma coisa", False,
                       "ERRADO: São institutos distintos")
        ],
        tipo=QuestionType.MULTIPLA_ESCOLHA,
        disciplina="Direito Penal",
        topico="Dolo eventual vs Culpa consciente",
        subtopicos=["dolo", "culpa", "tipo subjetivo"],
        dificuldade=DifficultyLevel.DIFICIL,
        artigos_relacionados=["CP art. 18, I e II"],
        conceitos_testados=["dolo eventual", "culpa consciente", "previsibilidade"],
        taxa_acerto_geral=0.42,
        pegadinhas_comuns=["Confundir previsão com aceitação"]
    )

    engine.adicionar_questao(q1)
    print(f"✓ Questão {q1.id} adicionada: {q1.topico}")

    # Gera drill
    print("\n2. GERANDO DRILL PERSONALIZADO")
    print("-" * 60)

    aluno_id = "aluno_123"

    drill = engine.gerar_drill_personalizado(
        aluno_id=aluno_id,
        foco="conceito",
        disciplina="Direito Penal",
        quantidade=5
    )

    print(f"Drill ID: {drill.drill_id}")
    print(f"Objetivo: {drill.objetivo}")
    print(f"Questões: {len(drill.questoes)}")
    print(f"Tempo estimado: {drill.tempo_estimado_minutos} minutos")

    # Registra resposta
    print("\n3. REGISTRANDO RESPOSTA")
    print("-" * 60)

    resultado = engine.registrar_resposta(
        aluno_id=aluno_id,
        questao_id="Q001",
        alternativa_escolhida="A",  # Errada
        tempo_segundos=240
    )

    print(json.dumps(resultado, indent=2, ensure_ascii=False))

    # Ajusta dificuldade
    print("\n4. AJUSTE DINÂMICO DE DIFICULDADE")
    print("-" * 60)

    dificuldade = engine.ajustar_dificuldade_dinamica(aluno_id, "Direito Penal")
    print(f"Dificuldade recomendada: {dificuldade.name}")

    print("\n" + "=" * 60)
    print("QUESTION ENGINE - OPERACIONAL")
    print("=" * 60)
