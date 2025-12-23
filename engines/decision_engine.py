"""
JURIS_IA_CORE_V1 - DECISION ENGINE
Motor de Decisão Inteligente para Sistema Jurídico

Este módulo processa eventos do estudante e decide quais módulos de IA ativar.
Baseado na arquitetura do ENEM-IA, adaptado para o domínio jurídico.

Funcionalidades:
- Processa eventos em tempo real
- Seleciona módulos apropriados
- Prioriza ações baseadas em contexto
- Mantém estado do estudante
- Gera ações personalizadas

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict


# ============================================================
# TIPOS E ENUMS
# ============================================================

class EventType(Enum):
    """Tipos de eventos que o estudante pode gerar"""
    # Eventos de performance
    ERRO = "erro"
    ERRO_REPETIDO = "erro_repetido"
    ACERTO = "acerto"
    ACERTO_SEQUENCIAL = "acerto_sequencial"

    # Eventos de tempo
    TEMPO_EXCESSIVO = "tempo_excessivo"
    RESPOSTA_RAPIDA = "resposta_rapida"

    # Eventos de dúvida
    DUVIDA = "duvida"
    PULOU_QUESTAO = "pulou_questao"

    # Eventos de sessão
    INICIO_SESSAO = "inicio_sessao"
    FIM_SESSAO = "fim_sessao"
    PAUSA_LONGA = "pausa_longa"

    # Eventos de progresso
    BLOCO_COMPLETO = "bloco_completo"
    DISCIPLINA_COMPLETA = "disciplina_completa"
    SIMULADO_COMPLETO = "simulado_completo"

    # Eventos de padrão
    REGRESSAO_DETECTADA = "regressao_detectada"
    MELHORA_DETECTADA = "melhora_detectada"
    PLATÔ_DETECTADO = "plato_detectado"

    # Eventos de 2ª fase
    PECA_INICIADA = "peca_iniciada"
    PECA_COMPLETA = "peca_completa"
    ERRO_FORMAL = "erro_formal"
    ERRO_MATERIAL = "erro_material"


class ModuleType(Enum):
    """Tipos de módulos de IA"""
    MEMORY = "MEMORY"                  # Memória e fixação
    STRATEGY = "STRATEGY"              # Estratégia de resolução
    PIECE_CONSTRUCTION = "PIECE"       # Construção de peças
    ORGANIZATION = "ORGANIZATION"      # Organização e produtividade
    DIAGNOSIS = "DIAGNOSIS"            # Diagnóstico e análise
    MOTIVATION = "MOTIVATION"          # Motivação e engajamento


class ActionType(Enum):
    """Tipos de ações que o engine pode retornar"""
    GERAR_DRILL = "gerar_drill"
    AGENDAR_REVISAO = "agendar_revisao"
    EXPLICAR_MULTINIVEL = "explicar_multinivel"
    MOSTRAR_ARTIGO_LEI = "mostrar_artigo_lei"
    GERAR_PECA_MODELO = "gerar_peca_modelo"
    AJUSTAR_DIFICULDADE = "ajustar_dificuldade"
    ENVIAR_MOTIVACAO = "enviar_motivacao"
    SUGERIR_PAUSA = "sugerir_pausa"
    ALERT_REGRESSAO = "alert_regressao"
    PARABENIZAR = "parabenizar"


@dataclass
class EngineEvent:
    """Evento gerado pelo estudante"""
    tipo: EventType
    timestamp: datetime
    contexto: Dict[str, Any]
    aluno_id: str
    disciplina: Optional[str] = None
    topico: Optional[str] = None
    questao_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StudentState:
    """Estado completo do estudante"""
    aluno_id: str

    # Progresso por disciplina (0-100)
    progresso_disciplinas: Dict[str, float] = field(default_factory=dict)

    # Histórico de erros recentes (últimos 50)
    erros_recentes: List[EngineEvent] = field(default_factory=list)

    # Acertos recentes (últimos 50)
    acertos_recentes: List[EngineEvent] = field(default_factory=list)

    # Nível emocional
    nivel_stress: float = 0.0      # 0-1
    nivel_motivacao: float = 0.5   # 0-1
    nivel_confianca: float = 0.5   # 0-1

    # Estatísticas gerais
    total_questoes: int = 0
    total_acertos: int = 0
    total_erros: int = 0
    taxa_acerto_geral: float = 0.0

    # Taxa de acerto por disciplina
    taxa_acerto_disciplina: Dict[str, float] = field(default_factory=dict)

    # Conceitos dominados e deficientes
    conceitos_dominados: List[str] = field(default_factory=list)
    conceitos_deficientes: List[str] = field(default_factory=list)

    # Padrões de erro
    tipo_erro_predominante: Optional[str] = None
    areas_fragilidade: List[str] = field(default_factory=list)

    # Histórico de módulos ativados (últimos 20)
    modulos_ativados_recentes: List[str] = field(default_factory=list)

    # Última atividade
    ultima_atividade: Optional[datetime] = None

    # Revisões agendadas
    revisoes_agendadas: List[Dict] = field(default_factory=list)


@dataclass
class EngineAction:
    """Ação recomendada pelo engine"""
    tipo: ActionType
    prioridade: int  # 1-10
    modulo_origem: str
    parametros: Dict[str, Any]
    justificativa: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EngineModule:
    """Módulo de IA do sistema"""
    id: str
    nome: str
    tipo: ModuleType
    objetivo: str
    gatilhos: List[EventType]
    algoritmo: List[str]
    acoes_retorno: List[ActionType]
    prioridade_base: int = 5


# ============================================================
# DECISION ENGINE
# ============================================================

class DecisionEngine:
    """
    Motor de decisão inteligente para sistema jurídico.

    Responsabilidades:
    - Processar eventos do estudante
    - Atualizar estado do estudante
    - Selecionar módulos apropriados
    - Priorizar ações
    - Detectar padrões de erro
    - Ajustar dinamicamente dificuldade
    """

    def __init__(self):
        """Inicializa o motor de decisão"""
        self.modules: Dict[str, EngineModule] = {}
        self.student_states: Dict[str, StudentState] = {}
        self.event_history: List[EngineEvent] = []
        self.action_history: List[EngineAction] = []

        # Carrega módulos
        self._load_modules()

    def processar_evento(
        self,
        evento: EngineEvent
    ) -> List[EngineAction]:
        """
        Processa um evento e retorna ações recomendadas.

        Args:
            evento: Evento gerado pelo estudante

        Returns:
            Lista de ações priorizadas
        """
        # Atualiza estado do estudante
        self._atualizar_estado_estudante(evento)

        # Registra evento no histórico
        self.event_history.append(evento)

        # Seleciona módulos relevantes
        modulos_ativados = self._selecionar_modulos(evento)

        # Gera ações de cada módulo
        acoes = []
        for modulo in modulos_ativados:
            acoes_modulo = self._executar_modulo(modulo, evento)
            acoes.extend(acoes_modulo)

        # Prioriza ações
        acoes_priorizadas = self._priorizar_acoes(acoes)

        # Registra ações no histórico
        self.action_history.extend(acoes_priorizadas)

        # Atualiza módulos ativados recentes
        state = self.student_states[evento.aluno_id]
        for modulo in modulos_ativados:
            state.modulos_ativados_recentes.append(modulo.id)
            if len(state.modulos_ativados_recentes) > 20:
                state.modulos_ativados_recentes.pop(0)

        return acoes_priorizadas

    def obter_estado_estudante(self, aluno_id: str) -> StudentState:
        """Obtém estado atual do estudante"""
        if aluno_id not in self.student_states:
            self.student_states[aluno_id] = StudentState(aluno_id=aluno_id)
        return self.student_states[aluno_id]

    def diagnosticar_estudante(self, aluno_id: str) -> Dict[str, Any]:
        """
        Gera diagnóstico completo do estudante.

        Returns:
            Dict com análise detalhada
        """
        state = self.obter_estado_estudante(aluno_id)

        # Análise de desempenho
        desempenho = self._analisar_desempenho(state)

        # Análise de padrões de erro
        padroes_erro = self._analisar_padroes_erro(state)

        # Análise emocional
        estado_emocional = {
            "stress": state.nivel_stress,
            "motivacao": state.nivel_motivacao,
            "confianca": state.nivel_confianca,
            "avaliacao": self._avaliar_estado_emocional(state)
        }

        # Recomendações
        recomendacoes = self._gerar_recomendacoes(state)

        return {
            "aluno_id": aluno_id,
            "desempenho": desempenho,
            "padroes_erro": padroes_erro,
            "estado_emocional": estado_emocional,
            "recomendacoes": recomendacoes,
            "timestamp": datetime.now().isoformat()
        }

    # ============================================================
    # MÉTODOS PRIVADOS - GESTÃO DE ESTADO
    # ============================================================

    def _atualizar_estado_estudante(self, evento: EngineEvent):
        """Atualiza estado do estudante baseado no evento"""
        state = self.obter_estado_estudante(evento.aluno_id)
        state.ultima_atividade = evento.timestamp

        if evento.tipo == EventType.ERRO:
            self._processar_erro(state, evento)
        elif evento.tipo == EventType.ACERTO:
            self._processar_acerto(state, evento)
        elif evento.tipo == EventType.BLOCO_COMPLETO:
            self._processar_bloco_completo(state, evento)
        elif evento.tipo == EventType.REGRESSAO_DETECTADA:
            self._processar_regressao(state, evento)

        # Atualiza taxa de acerto geral
        if state.total_questoes > 0:
            state.taxa_acerto_geral = state.total_acertos / state.total_questoes

        # Atualiza nível emocional
        self._atualizar_nivel_emocional(state, evento)

    def _processar_erro(self, state: StudentState, evento: EngineEvent):
        """Processa evento de erro"""
        state.total_erros += 1
        state.total_questoes += 1
        state.erros_recentes.append(evento)

        if len(state.erros_recentes) > 50:
            state.erros_recentes.pop(0)

        # Atualiza taxa por disciplina
        if evento.disciplina:
            self._atualizar_taxa_disciplina(state, evento.disciplina, acertou=False)

        # Identifica conceito deficiente
        if evento.topico and evento.topico not in state.conceitos_deficientes:
            state.conceitos_deficientes.append(evento.topico)

    def _processar_acerto(self, state: StudentState, evento: EngineEvent):
        """Processa evento de acerto"""
        state.total_acertos += 1
        state.total_questoes += 1
        state.acertos_recentes.append(evento)

        if len(state.acertos_recentes) > 50:
            state.acertos_recentes.pop(0)

        # Atualiza taxa por disciplina
        if evento.disciplina:
            self._atualizar_taxa_disciplina(state, evento.disciplina, acertou=True)

        # Identifica conceito dominado (3 acertos consecutivos)
        if evento.topico:
            acertos_consecutivos = self._contar_acertos_consecutivos(state, evento.topico)
            if acertos_consecutivos >= 3 and evento.topico not in state.conceitos_dominados:
                state.conceitos_dominados.append(evento.topico)
                # Remove de deficientes se estava lá
                if evento.topico in state.conceitos_deficientes:
                    state.conceitos_deficientes.remove(evento.topico)

    def _processar_bloco_completo(self, state: StudentState, evento: EngineEvent):
        """Processa conclusão de bloco"""
        if evento.disciplina:
            progresso_atual = state.progresso_disciplinas.get(evento.disciplina, 0)
            state.progresso_disciplinas[evento.disciplina] = min(progresso_atual + 5, 100)

    def _processar_regressao(self, state: StudentState, evento: EngineEvent):
        """Processa detecção de regressão"""
        state.nivel_confianca = max(state.nivel_confianca - 0.1, 0)
        state.nivel_stress = min(state.nivel_stress + 0.1, 1)

    def _atualizar_taxa_disciplina(self, state: StudentState, disciplina: str, acertou: bool):
        """Atualiza taxa de acerto por disciplina"""
        if disciplina not in state.taxa_acerto_disciplina:
            state.taxa_acerto_disciplina[disciplina] = 0.5

        # Média móvel ponderada (peso maior para recentes)
        taxa_atual = state.taxa_acerto_disciplina[disciplina]
        nova_taxa = (taxa_atual * 0.9) + (1.0 if acertou else 0.0) * 0.1
        state.taxa_acerto_disciplina[disciplina] = nova_taxa

    def _atualizar_nivel_emocional(self, state: StudentState, evento: EngineEvent):
        """Atualiza níveis emocionais baseado em padrões"""
        # Analisa últimos 10 eventos
        ultimos_eventos = (state.erros_recentes[-10:] + state.acertos_recentes[-10:])
        ultimos_eventos.sort(key=lambda e: e.timestamp)

        if len(ultimos_eventos) >= 5:
            erros_recentes = sum(1 for e in ultimos_eventos[-5:] if e.tipo == EventType.ERRO)

            # Muitos erros = stress aumenta, motivação e confiança caem
            if erros_recentes >= 4:
                state.nivel_stress = min(state.nivel_stress + 0.15, 1.0)
                state.nivel_motivacao = max(state.nivel_motivacao - 0.1, 0.0)
                state.nivel_confianca = max(state.nivel_confianca - 0.15, 0.0)

            # Muitos acertos = stress cai, motivação e confiança sobem
            elif erros_recentes <= 1:
                state.nivel_stress = max(state.nivel_stress - 0.1, 0.0)
                state.nivel_motivacao = min(state.nivel_motivacao + 0.15, 1.0)
                state.nivel_confianca = min(state.nivel_confianca + 0.1, 1.0)

    def _contar_acertos_consecutivos(self, state: StudentState, topico: str) -> int:
        """Conta acertos consecutivos em um tópico"""
        contador = 0
        for evento in reversed(state.acertos_recentes):
            if evento.topico == topico:
                contador += 1
            else:
                break
        return contador

    # ============================================================
    # MÉTODOS PRIVADOS - SELEÇÃO DE MÓDULOS
    # ============================================================

    def _selecionar_modulos(self, evento: EngineEvent) -> List[EngineModule]:
        """Seleciona módulos relevantes para o evento"""
        modulos_ativados = []

        for modulo in self.modules.values():
            if self._modulo_deve_ativar(modulo, evento):
                modulos_ativados.append(modulo)

        return modulos_ativados

    def _modulo_deve_ativar(self, modulo: EngineModule, evento: EngineEvent) -> bool:
        """Verifica se módulo deve ser ativado para este evento"""
        # Verifica se evento está nos gatilhos
        if evento.tipo not in modulo.gatilhos:
            return False

        # Verifica se módulo não foi ativado muito recentemente
        state = self.obter_estado_estudante(evento.aluno_id)
        if len(state.modulos_ativados_recentes) > 0:
            ultimos_3 = state.modulos_ativados_recentes[-3:]
            if ultimos_3.count(modulo.id) >= 2:
                return False  # Evita ativar mesmo módulo repetidamente

        return True

    def _executar_modulo(
        self,
        modulo: EngineModule,
        evento: EngineEvent
    ) -> List[EngineAction]:
        """
        Executa lógica do módulo e retorna ações.

        Cada módulo tem seu próprio algoritmo de decisão.
        """
        state = self.obter_estado_estudante(evento.aluno_id)
        acoes = []

        # Módulos de MEMÓRIA (J01-J10)
        if modulo.tipo == ModuleType.MEMORY:
            acoes = self._executar_modulo_memoria(modulo, evento, state)

        # Módulos de ESTRATÉGIA (J11-J20)
        elif modulo.tipo == ModuleType.STRATEGY:
            acoes = self._executar_modulo_estrategia(modulo, evento, state)

        # Módulos de PEÇAS (J21-J30)
        elif modulo.tipo == ModuleType.PIECE_CONSTRUCTION:
            acoes = self._executar_modulo_peca(modulo, evento, state)

        # Módulos de ORGANIZAÇÃO (J31-J40)
        elif modulo.tipo == ModuleType.ORGANIZATION:
            acoes = self._executar_modulo_organizacao(modulo, evento, state)

        return acoes

    def _executar_modulo_memoria(
        self,
        modulo: EngineModule,
        evento: EngineEvent,
        state: StudentState
    ) -> List[EngineAction]:
        """Executa módulos de memória (revisão espaçada, fixação)"""
        acoes = []

        # J01: Ciclo 1-24-7
        if modulo.id == "J01" and evento.tipo == EventType.BLOCO_COMPLETO:
            acoes.append(EngineAction(
                tipo=ActionType.AGENDAR_REVISAO,
                prioridade=8,
                modulo_origem=modulo.id,
                parametros={
                    "topico": evento.topico,
                    "ciclo": "1h",
                    "tipo": "drill_rapido"
                },
                justificativa="Ciclo 1-24-7: Revisão em 1 hora para fixação imediata"
            ))

        # J02: Fixação por repetição variada
        elif modulo.id == "J02" and evento.tipo == EventType.ERRO_REPETIDO:
            acoes.append(EngineAction(
                tipo=ActionType.GERAR_DRILL,
                prioridade=9,
                modulo_origem=modulo.id,
                parametros={
                    "topico": evento.topico,
                    "quantidade": 5,
                    "variacao": "alta",
                    "foco": "conceito_basico"
                },
                justificativa="Erro repetido detectado - drill de fixação intensivo"
            ))

        return acoes

    def _executar_modulo_estrategia(
        self,
        modulo: EngineModule,
        evento: EngineEvent,
        state: StudentState
    ) -> List[EngineAction]:
        """Executa módulos de estratégia de resolução"""
        acoes = []

        # J11: Técnica de eliminação
        if modulo.id == "J11" and evento.tipo == EventType.TEMPO_EXCESSIVO:
            acoes.append(EngineAction(
                tipo=ActionType.EXPLICAR_MULTINIVEL,
                prioridade=7,
                modulo_origem=modulo.id,
                parametros={
                    "topico": "tecnica_eliminacao",
                    "nivel": 2,  # Didático
                    "foco": "velocidade"
                },
                justificativa="Tempo excessivo - ensinar técnica de eliminação"
            ))

        # J12: Leitura estratégica do enunciado
        elif modulo.id == "J12" and evento.tipo == EventType.ERRO:
            tipo_erro = evento.contexto.get("tipo_erro", "")
            if "leitura" in tipo_erro.lower():
                acoes.append(EngineAction(
                    tipo=ActionType.EXPLICAR_MULTINIVEL,
                    prioridade=8,
                    modulo_origem=modulo.id,
                    parametros={
                        "topico": "leitura_estrategica",
                        "nivel": 2,
                        "exemplo_aplicado": True
                    },
                    justificativa="Erro de leitura - reforçar técnica de leitura estratégica"
                ))

        return acoes

    def _executar_modulo_peca(
        self,
        modulo: EngineModule,
        evento: EngineEvent,
        state: StudentState
    ) -> List[EngineAction]:
        """Executa módulos de construção de peças (2ª fase)"""
        acoes = []

        # J21: Checklist de petição inicial
        if modulo.id == "J21" and evento.tipo == EventType.PECA_INICIADA:
            acoes.append(EngineAction(
                tipo=ActionType.GERAR_PECA_MODELO,
                prioridade=7,
                modulo_origem=modulo.id,
                parametros={
                    "tipo_peca": "peticao_inicial",
                    "area": evento.contexto.get("area", "civel"),
                    "mostrar_checklist": True
                },
                justificativa="Peça iniciada - fornecer checklist de verificação"
            ))

        # J22: Erro fatal detector
        elif modulo.id == "J22" and evento.tipo == EventType.ERRO_FORMAL:
            acoes.append(EngineAction(
                tipo=ActionType.EXPLICAR_MULTINIVEL,
                prioridade=10,  # Máxima prioridade!
                modulo_origem=modulo.id,
                parametros={
                    "topico": "erros_fatais_peca",
                    "erro_especifico": evento.contexto.get("erro", ""),
                    "nivel": 4  # Exemplo prático
                },
                justificativa="ERRO FATAL detectado - correção urgente necessária"
            ))

        return acoes

    def _executar_modulo_organizacao(
        self,
        modulo: EngineModule,
        evento: EngineEvent,
        state: StudentState
    ) -> List[EngineAction]:
        """Executa módulos de organização e produtividade"""
        acoes = []

        # J31: Detector de fadiga
        if modulo.id == "J31" and state.nivel_stress > 0.7:
            acoes.append(EngineAction(
                tipo=ActionType.SUGERIR_PAUSA,
                prioridade=9,
                modulo_origem=modulo.id,
                parametros={
                    "duracao_minutos": 15,
                    "razao": "alta_deteccao_stress"
                },
                justificativa="Nível de stress elevado - pausa recomendada"
            ))

        # J32: Motivação inteligente
        elif modulo.id == "J32" and state.nivel_motivacao < 0.3:
            acoes.append(EngineAction(
                tipo=ActionType.ENVIAR_MOTIVACAO,
                prioridade=6,
                modulo_origem=modulo.id,
                parametros={
                    "tipo": "progressomostrado",
                    "dados": {
                        "acertos_hoje": len([e for e in state.acertos_recentes if (datetime.now() - e.timestamp).days == 0])
                    }
                },
                justificativa="Motivação baixa - mostrar progresso alcançado"
            ))

        return acoes

    # ============================================================
    # MÉTODOS PRIVADOS - PRIORIZAÇÃO
    # ============================================================

    def _priorizar_acoes(self, acoes: List[EngineAction]) -> List[EngineAction]:
        """Prioriza ações por importância e urgência"""
        # Ordena por prioridade (maior primeiro)
        acoes_ordenadas = sorted(acoes, key=lambda a: a.prioridade, reverse=True)

        # Remove duplicatas (mesma ação de módulos diferentes)
        acoes_unicas = []
        tipos_vistos = set()

        for acao in acoes_ordenadas:
            chave = f"{acao.tipo.value}_{acao.parametros.get('topico', '')}"
            if chave not in tipos_vistos:
                acoes_unicas.append(acao)
                tipos_vistos.add(chave)

        # Limita a 5 ações mais importantes
        return acoes_unicas[:5]

    # ============================================================
    # MÉTODOS PRIVADOS - ANÁLISE E DIAGNÓSTICO
    # ============================================================

    def _analisar_desempenho(self, state: StudentState) -> Dict:
        """Analisa desempenho geral do estudante"""
        return {
            "taxa_acerto_geral": round(state.taxa_acerto_geral * 100, 1),
            "total_questoes": state.total_questoes,
            "total_acertos": state.total_acertos,
            "total_erros": state.total_erros,
            "por_disciplina": {
                disc: round(taxa * 100, 1)
                for disc, taxa in state.taxa_acerto_disciplina.items()
            },
            "nivel": self._classificar_nivel(state.taxa_acerto_geral)
        }

    def _classificar_nivel(self, taxa: float) -> str:
        """Classifica nível do estudante"""
        if taxa < 0.4:
            return "INICIANTE"
        elif taxa < 0.7:
            return "INTERMEDIÁRIO"
        else:
            return "AVANÇADO"

    def _analisar_padroes_erro(self, state: StudentState) -> Dict:
        """Analisa padrões de erro do estudante"""
        # Agrupa erros por tipo
        tipos_erro = defaultdict(int)
        for erro in state.erros_recentes:
            tipo = erro.contexto.get("tipo_erro", "desconhecido")
            tipos_erro[tipo] += 1

        # Identifica tipo predominante
        if tipos_erro:
            tipo_predominante = max(tipos_erro.items(), key=lambda x: x[1])[0]
            state.tipo_erro_predominante = tipo_predominante
        else:
            tipo_predominante = None

        return {
            "tipo_predominante": tipo_predominante,
            "distribuicao": dict(tipos_erro),
            "conceitos_deficientes": state.conceitos_deficientes[:5],  # Top 5
            "areas_fragilidade": state.areas_fragilidade
        }

    def _avaliar_estado_emocional(self, state: StudentState) -> str:
        """Avalia estado emocional geral"""
        if state.nivel_stress > 0.7:
            return "STRESS_ALTO - Risco de burnout"
        elif state.nivel_motivacao < 0.3:
            return "MOTIVACAO_BAIXA - Precisa de incentivo"
        elif state.nivel_confianca < 0.3:
            return "CONFIANCA_BAIXA - Reforço necessário"
        elif state.nivel_motivacao > 0.7 and state.nivel_confianca > 0.7:
            return "OTIMO - Estado ideal para aprendizagem"
        else:
            return "NORMAL - Estado adequado"

    def _gerar_recomendacoes(self, state: StudentState) -> List[str]:
        """Gera recomendações personalizadas"""
        recomendacoes = []

        # Baseado em taxa de acerto
        if state.taxa_acerto_geral < 0.4:
            recomendacoes.append("Volte aos conceitos fundamentais - base está frágil")

        # Baseado em conceitos deficientes
        if len(state.conceitos_deficientes) > 5:
            recomendacoes.append(f"Foque em: {', '.join(state.conceitos_deficientes[:3])}")

        # Baseado em estado emocional
        if state.nivel_stress > 0.7:
            recomendacoes.append("Reduza ritmo - stress muito alto pode prejudicar")

        if state.nivel_motivacao < 0.3:
            recomendacoes.append("Celebre pequenas vitórias - você está progredindo!")

        # Baseado em padrões de erro
        if state.tipo_erro_predominante == "leitura":
            recomendacoes.append("Pratique leitura estratégica do enunciado")
        elif state.tipo_erro_predominante == "conceitual":
            recomendacoes.append("Revise teoria antes de fazer mais questões")

        return recomendacoes if recomendacoes else ["Continue no ritmo atual"]

    # ============================================================
    # MÉTODOS PRIVADOS - CARREGAMENTO DE MÓDULOS
    # ============================================================

    def _load_modules(self):
        """Carrega módulos do sistema (simplificado)"""
        # Em produção, carregaria de modules_juridicos.ts
        # Aqui, criamos alguns módulos essenciais como exemplo

        self.modules["J01"] = EngineModule(
            id="J01",
            nome="Ciclo 1-24-7 Jurídico",
            tipo=ModuleType.MEMORY,
            objetivo="Fixar conceitos com revisão espaçada",
            gatilhos=[EventType.BLOCO_COMPLETO, EventType.ACERTO],
            algoritmo=["Agendar revisões em 1h, 24h, 7d"],
            acoes_retorno=[ActionType.AGENDAR_REVISAO, ActionType.GERAR_DRILL],
            prioridade_base=8
        )

        self.modules["J02"] = EngineModule(
            id="J02",
            nome="Fixação por Repetição Variada",
            tipo=ModuleType.MEMORY,
            objetivo="Corrigir erros repetidos",
            gatilhos=[EventType.ERRO_REPETIDO],
            algoritmo=["Gerar drill com variações do mesmo conceito"],
            acoes_retorno=[ActionType.GERAR_DRILL],
            prioridade_base=9
        )

        self.modules["J11"] = EngineModule(
            id="J11",
            nome="Técnica de Eliminação",
            tipo=ModuleType.STRATEGY,
            objetivo="Ensinar eliminação de alternativas",
            gatilhos=[EventType.TEMPO_EXCESSIVO, EventType.DUVIDA],
            algoritmo=["Ensinar análise alternativa por alternativa"],
            acoes_retorno=[ActionType.EXPLICAR_MULTINIVEL],
            prioridade_base=7
        )

        self.modules["J21"] = EngineModule(
            id="J21",
            nome="Checklist de Petição Inicial",
            tipo=ModuleType.PIECE_CONSTRUCTION,
            objetivo="Garantir peça completa e correta",
            gatilhos=[EventType.PECA_INICIADA, EventType.PECA_COMPLETA],
            algoritmo=["Verificar 8 partes obrigatórias"],
            acoes_retorno=[ActionType.GERAR_PECA_MODELO],
            prioridade_base=7
        )

        self.modules["J22"] = EngineModule(
            id="J22",
            nome="Erro Fatal Detector",
            tipo=ModuleType.PIECE_CONSTRUCTION,
            objetivo="Detectar erros que zeram peça",
            gatilhos=[EventType.ERRO_FORMAL, EventType.ERRO_MATERIAL],
            algoritmo=["Identificar erros fatais", "Alertar imediatamente"],
            acoes_retorno=[ActionType.EXPLICAR_MULTINIVEL],
            prioridade_base=10
        )

        self.modules["J31"] = EngineModule(
            id="J31",
            nome="Detector de Fadiga",
            tipo=ModuleType.ORGANIZATION,
            objetivo="Prevenir burnout",
            gatilhos=[EventType.ERRO_REPETIDO, EventType.TEMPO_EXCESSIVO],
            algoritmo=["Monitorar stress", "Sugerir pausa quando necessário"],
            acoes_retorno=[ActionType.SUGERIR_PAUSA],
            prioridade_base=9
        )

        self.modules["J32"] = EngineModule(
            id="J32",
            nome="Motivação Inteligente",
            tipo=ModuleType.ORGANIZATION,
            objetivo="Manter estudante motivado",
            gatilhos=[EventType.ACERTO_SEQUENCIAL, EventType.FIM_SESSAO],
            algoritmo=["Detectar baixa motivação", "Enviar mensagem personalizada"],
            acoes_retorno=[ActionType.ENVIAR_MOTIVACAO, ActionType.PARABENIZAR],
            prioridade_base=6
        )


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_decision_engine() -> DecisionEngine:
    """Factory function para criar decision engine"""
    return DecisionEngine()


# ============================================================
# EXEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    # Cria engine
    engine = criar_decision_engine()

    print("=" * 60)
    print("DECISION ENGINE - EXEMPLO DE USO")
    print("=" * 60)

    # Simula eventos de um estudante
    aluno_id = "aluno_123"

    # Evento 1: Erro
    evento1 = EngineEvent(
        tipo=EventType.ERRO,
        timestamp=datetime.now(),
        contexto={"tipo_erro": "conceitual"},
        aluno_id=aluno_id,
        disciplina="Direito Penal",
        topico="Dolo eventual",
        questao_id="Q001"
    )

    print("\nPROCESSANDO EVENTO: ERRO")
    acoes1 = engine.processar_evento(evento1)
    print(f"Ações geradas: {len(acoes1)}")
    for acao in acoes1:
        print(f"  - [{acao.prioridade}] {acao.tipo.value}: {acao.justificativa}")

    # Evento 2: Erro repetido (mesmo tópico)
    evento2 = EngineEvent(
        tipo=EventType.ERRO_REPETIDO,
        timestamp=datetime.now(),
        contexto={"tipo_erro": "conceitual"},
        aluno_id=aluno_id,
        disciplina="Direito Penal",
        topico="Dolo eventual",
        questao_id="Q002"
    )

    print("\nPROCESSANDO EVENTO: ERRO REPETIDO")
    acoes2 = engine.processar_evento(evento2)
    print(f"Ações geradas: {len(acoes2)}")
    for acao in acoes2:
        print(f"  - [{acao.prioridade}] {acao.tipo.value}: {acao.justificativa}")

    # Evento 3: Bloco completo
    evento3 = EngineEvent(
        tipo=EventType.BLOCO_COMPLETO,
        timestamp=datetime.now(),
        contexto={},
        aluno_id=aluno_id,
        disciplina="Direito Penal",
        topico="Dolo eventual"
    )

    print("\nPROCESSANDO EVENTO: BLOCO COMPLETO")
    acoes3 = engine.processar_evento(evento3)
    print(f"Ações geradas: {len(acoes3)}")
    for acao in acoes3:
        print(f"  - [{acao.prioridade}] {acao.tipo.value}: {acao.justificativa}")

    # Diagnóstico do estudante
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DO ESTUDANTE")
    print("=" * 60)

    diagnostico = engine.diagnosticar_estudante(aluno_id)
    print(json.dumps(diagnostico, indent=2, ensure_ascii=False, default=str))

    print("\n" + "=" * 60)
    print("DECISION ENGINE - OPERACIONAL")
    print("=" * 60)
