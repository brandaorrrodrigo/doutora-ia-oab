"""
JURIS_IA_CORE_V1 - ORQUESTRADOR PRINCIPAL
Sistema Completo de IA Jurídica para OAB

Este é o ponto de entrada principal do sistema. Integra todos os engines
e fornece interface unificada para interação com estudantes.

Autor: JURIS_IA_CORE_V1
Data: 2025-12-17
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import asdict

# Importa todos os engines
from engines.explanation_engine import ExplanationEngine, StudentProfile, ExplanationLevel
from engines.decision_engine import DecisionEngine, EngineEvent, EventType, EngineAction
from engines.memory_engine import MemoryEngine, ReviewCycle
from engines.question_engine_db import QuestionEngineDB
from engines.piece_engine import PieceEngine, PieceType, PieceEvaluation


# ============================================================
# JURIS_IA - SISTEMA PRINCIPAL
# ============================================================

class JurisIA:
    """
    Sistema completo de IA jurídica para aprovação na OAB.

    Integra todos os engines e fornece interface única para:
    - Estudar teoria
    - Resolver questões
    - Escrever peças
    - Receber feedback personalizado
    - Acompanhar progresso
    """

    def __init__(self):
        """Inicializa o sistema JURIS_IA"""
        print("Inicializando JURIS_IA_CORE_V1...")

        # Inicializa todos os engines
        self.explanation_engine = ExplanationEngine()
        self.decision_engine = DecisionEngine()
        self.memory_engine = MemoryEngine()
        self.question_engine = QuestionEngineDB()
        self.piece_engine = PieceEngine()

        print("[OK] Explanation Engine carregado")
        print("[OK] Decision Engine carregado")
        print("[OK] Memory Engine carregado")
        print("[OK] Question Engine carregado")
        print("[OK] Piece Engine carregado")
        print("\nSistema pronto!")

    # ============================================================
    # FLUXO: SESSÃO DE ESTUDO (1ª FASE)
    # ============================================================

    def iniciar_sessao_estudo(
        self,
        aluno_id: str,
        disciplina: Optional[str] = None,
        tipo: str = "drill"  # "drill", "simulado", "revisao"
    ) -> Dict:
        """
        Inicia sessão de estudo personalizada.

        Args:
            aluno_id: ID do aluno
            disciplina: Disciplina específica (opcional)
            tipo: Tipo de sessão

        Returns:
            Dict com configuração da sessão
        """
        # Registra evento de início
        evento = EngineEvent(
            tipo=EventType.INICIO_SESSAO,
            timestamp=datetime.now(),
            contexto={"tipo_sessao": tipo, "disciplina": disciplina},
            aluno_id=aluno_id,
            disciplina=disciplina
        )

        # Decision engine processa e gera ações
        acoes = self.decision_engine.processar_evento(evento)

        # Obtém estado do estudante
        estado = self.decision_engine.obter_estado_estudante(aluno_id)

        # Determina perfil do estudante
        perfil = self._determinar_perfil(estado)

        # Gera drill ou simulado apropriado
        if tipo == "drill":
            drill = self.question_engine.gerar_drill_personalizado(
                aluno_id=aluno_id,
                foco=self._determinar_foco_drill(estado),
                disciplina=disciplina,
                quantidade=10
            )
            questoes = drill.questoes
            configuracao = {
                "tipo": "drill",
                "drill_id": drill.drill_id,
                "objetivo": drill.objetivo,
                "tempo_estimado": drill.tempo_estimado_minutos
            }

        elif tipo == "simulado":
            simulado = self.question_engine.gerar_simulado(
                aluno_id=aluno_id,
                tipo="completo" if not disciplina else "disciplina_especifica",
                disciplina=disciplina
            )
            questoes = simulado.questoes
            configuracao = {
                "tipo": "simulado",
                "simulado_id": simulado.simulado_id,
                "tempo_limite": simulado.tempo_limite_minutos
            }

        else:  # revisao
            itens_revisao = self.memory_engine.obter_itens_revisar(aluno_id)
            # Gera drill de revisão com tópicos devidos
            drill = self.question_engine.gerar_drill_personalizado(
                aluno_id=aluno_id,
                foco="revisao",
                disciplina=disciplina,
                quantidade=len(itens_revisao)
            )
            questoes = drill.questoes
            configuracao = {
                "tipo": "revisao",
                "itens_pendentes": len(itens_revisao)
            }

        return {
            "aluno_id": aluno_id,
            "perfil": perfil.value,
            "configuracao": configuracao,
            "total_questoes": len(questoes),
            "questoes": [self._serializar_questao(q) for q in questoes],
            "acoes_recomendadas": [
                {
                    "tipo": acao.tipo.value,
                    "prioridade": acao.prioridade,
                    "justificativa": acao.justificativa
                }
                for acao in acoes
            ],
            "estado_emocional": {
                "stress": estado.nivel_stress,
                "motivacao": estado.nivel_motivacao,
                "confianca": estado.nivel_confianca
            }
        }

    def responder_questao(
        self,
        aluno_id: str,
        questao_id: str,
        alternativa_escolhida: str,
        tempo_segundos: int
    ) -> Dict:
        """
        Processa resposta de uma questão.

        Args:
            aluno_id: ID do aluno
            questao_id: ID da questão
            alternativa_escolhida: Letra escolhida (A, B, C, D)
            tempo_segundos: Tempo gasto

        Returns:
            Dict com feedback completo
        """
        # 1. Registra resposta no question engine
        resultado = self.question_engine.registrar_resposta(
            aluno_id=aluno_id,
            questao_id=questao_id,
            alternativa_escolhida=alternativa_escolhida,
            tempo_segundos=tempo_segundos
        )

        # 2. Cria evento para decision engine
        questao = self.question_engine.banco_questoes.get(questao_id)
        acertou = resultado["acertou"]

        evento = EngineEvent(
            tipo=EventType.ACERTO if acertou else EventType.ERRO,
            timestamp=datetime.now(),
            contexto={
                "tempo_segundos": tempo_segundos,
                "tipo_erro": "conceitual" if not acertou else None
            },
            aluno_id=aluno_id,
            disciplina=questao.disciplina if questao else None,
            topico=questao.topico if questao else None,
            questao_id=questao_id
        )

        # 3. Decision engine processa e gera ações
        acoes = self.decision_engine.processar_evento(evento)

        # 4. Obtém explicação adaptativa
        estado = self.decision_engine.obter_estado_estudante(aluno_id)
        perfil = self._determinar_perfil(estado)

        explicacao = self.explanation_engine.gerar_explicacao_adaptativa(
            topico=questao.topico if questao else "Tópico",
            contexto=f"Questão {questao_id}",
            perfil_estudante=perfil
        )

        # 5. Se errou, agenda revisão
        if not acertou and questao:
            self.memory_engine.adicionar_item(
                aluno_id=aluno_id,
                topico=questao.topico,
                disciplina=questao.disciplina,
                conceitos=questao.conceitos_testados,
                artigos=questao.artigos_relacionados
            )

        # 6. Monta resposta completa
        return {
            "resultado": "ACERTO" if acertou else "ERRO",
            "explicacao": explicacao.conteudo,
            "nivel_explicacao": explicacao.tipo,
            "conceitos_chave": explicacao.conceitos_chave,
            "artigos_relacionados": explicacao.artigos_relacionados,
            "feedback_tempo": self._feedback_tempo(tempo_segundos),
            "proximas_acoes": [
                {
                    "tipo": acao.tipo.value,
                    "prioridade": acao.prioridade,
                    "parametros": acao.parametros,
                    "justificativa": acao.justificativa
                }
                for acao in acoes[:3]  # Top 3 ações
            ],
            "estatisticas": resultado.get("estatisticas", {}),
            "revisao_agendada": not acertou
        }

    def finalizar_sessao_estudo(self, aluno_id: str) -> Dict:
        """
        Finaliza sessão de estudo e gera relatório.

        Args:
            aluno_id: ID do aluno

        Returns:
            Dict com resumo da sessão
        """
        # Registra evento de fim
        evento = EngineEvent(
            tipo=EventType.FIM_SESSAO,
            timestamp=datetime.now(),
            contexto={},
            aluno_id=aluno_id
        )

        acoes = self.decision_engine.processar_evento(evento)

        # Gera diagnóstico completo
        diagnostico = self.decision_engine.diagnosticar_estudante(aluno_id)

        # Análise de desempenho
        desempenho = self.question_engine.analisar_desempenho(aluno_id)

        # Análise de memória
        memoria = self.memory_engine.analisar_memoria(aluno_id)

        # Detecta problemas
        alertas_esquecimento = self.memory_engine.detectar_esquecimento(aluno_id)

        return {
            "aluno_id": aluno_id,
            "diagnostico": diagnostico,
            "desempenho": desempenho,
            "memoria": memoria,
            "alertas": alertas_esquecimento,
            "recomendacoes_proxima_sessao": diagnostico.get("recomendacoes", []),
            "proximas_acoes": [
                {
                    "tipo": acao.tipo.value,
                    "justificativa": acao.justificativa
                }
                for acao in acoes
            ]
        }

    # ============================================================
    # FLUXO: PRÁTICA DE PEÇAS (2ª FASE)
    # ============================================================

    def iniciar_pratica_peca(
        self,
        aluno_id: str,
        tipo_peca: PieceType,
        enunciado: str
    ) -> Dict:
        """
        Inicia prática de peça processual.

        Args:
            aluno_id: ID do aluno
            tipo_peca: Tipo de peça
            enunciado: Enunciado da questão

        Returns:
            Dict com checklist e orientações
        """
        # Registra evento
        evento = EngineEvent(
            tipo=EventType.PECA_INICIADA,
            timestamp=datetime.now(),
            contexto={"tipo_peca": tipo_peca.value},
            aluno_id=aluno_id
        )

        acoes = self.decision_engine.processar_evento(evento)

        # Gera checklist
        checklist = self.piece_engine.gerar_checklist(tipo_peca)

        # Gera peça-modelo (opcional, se aluno solicitar)
        peca_modelo = self.piece_engine.gerar_peca_modelo(
            tipo_peca=tipo_peca,
            enunciado=enunciado,
            detalhada=False
        )

        return {
            "aluno_id": aluno_id,
            "tipo_peca": tipo_peca.value,
            "enunciado": enunciado,
            "checklist": checklist,
            "orientacoes": [
                "Leia o enunciado 3 vezes antes de começar",
                "Use o checklist para verificar cada parte",
                "Cite artigos específicos da lei",
                "Revise antes de enviar"
            ],
            "peca_modelo_disponivel": True,
            "tempo_recomendado_minutos": 60
        }

    def avaliar_peca(
        self,
        aluno_id: str,
        tipo_peca: PieceType,
        conteudo: str,
        enunciado: str
    ) -> Dict:
        """
        Avalia peça escrita pelo aluno.

        Args:
            aluno_id: ID do aluno
            tipo_peca: Tipo de peça
            conteudo: Texto da peça
            enunciado: Enunciado original

        Returns:
            Dict com avaliação completa
        """
        # 1. Avalia peça
        avaliacao = self.piece_engine.avaliar_peca(
            aluno_id=aluno_id,
            tipo_peca=tipo_peca,
            conteudo=conteudo,
            enunciado=enunciado
        )

        # 2. Registra evento
        evento_tipo = EventType.PECA_COMPLETA if avaliacao.aprovado else EventType.ERRO_FORMAL

        evento = EngineEvent(
            tipo=evento_tipo,
            timestamp=datetime.now(),
            contexto={
                "nota": avaliacao.nota_final,
                "erros_fatais": len(avaliacao.erros_fatais)
            },
            aluno_id=aluno_id
        )

        acoes = self.decision_engine.processar_evento(evento)

        # 3. Gera explicações para erros
        explicacoes_erros = []
        if avaliacao.erros_fatais or avaliacao.erros_graves:
            for erro in (avaliacao.erros_fatais + avaliacao.erros_graves):
                explicacao = self.explanation_engine.explicar_alternativa_errada(
                    alternativa=erro.localizacao,
                    motivo_erro=erro.descricao,
                    nivel=ExplanationLevel.DIDATICA
                )
                explicacoes_erros.append({
                    "erro": erro.descricao,
                    "gravidade": erro.gravidade.value,
                    "explicacao": explicacao,
                    "correcao": erro.correcao_sugerida
                })

        return {
            "aluno_id": aluno_id,
            "nota_final": avaliacao.nota_final,
            "aprovado": avaliacao.aprovado,
            "competencias": {
                "adequacao_normas": avaliacao.adequacao_normas,
                "tecnica_processual": avaliacao.tecnica_processual,
                "argumentacao_juridica": avaliacao.argumentacao_juridica,
                "clareza_objetividade": avaliacao.clareza_objetividade
            },
            "erros_fatais": len(avaliacao.erros_fatais),
            "erros_graves": len(avaliacao.erros_graves),
            "explicacoes_erros": explicacoes_erros,
            "pontos_fortes": avaliacao.pontos_fortes,
            "pontos_melhorar": avaliacao.pontos_melhorar,
            "recomendacoes": avaliacao.recomendacoes,
            "checklist_resultado": avaliacao.checklist_resultado,
            "proximas_acoes": [
                {
                    "tipo": acao.tipo.value,
                    "justificativa": acao.justificativa
                }
                for acao in acoes
            ]
        }

    # ============================================================
    # DIAGNÓSTICO E ACOMPANHAMENTO
    # ============================================================

    def obter_painel_estudante(self, aluno_id: str) -> Dict:
        """
        Retorna painel completo do estudante.

        Args:
            aluno_id: ID do aluno

        Returns:
            Dict com todas as informações
        """
        # Diagnóstico completo
        diagnostico = self.decision_engine.diagnosticar_estudante(aluno_id)

        # Desempenho em questões
        desempenho = self.question_engine.analisar_desempenho(aluno_id)

        # Estado da memória
        memoria = self.memory_engine.analisar_memoria(aluno_id)

        # Próximas revisões
        itens_revisar = self.memory_engine.obter_itens_revisar(aluno_id, limite=5)

        # Ajuste de dificuldade
        dificuldade = self.question_engine.ajustar_dificuldade_dinamica(aluno_id)

        return {
            "aluno_id": aluno_id,
            "visao_geral": {
                "nivel": diagnostico["desempenho"].get("nivel", "INTERMEDIÁRIO"),
                "taxa_acerto_geral": diagnostico["desempenho"].get("taxa_acerto_geral", 0),
                "total_questoes": diagnostico["desempenho"].get("total_questoes", 0),
                "estado_emocional": diagnostico["estado_emocional"]
            },
            "desempenho_detalhado": desempenho,
            "memoria": {
                "total_conceitos": memoria.get("total_itens", 0),
                "conceitos_dominados": len(memoria.get("conceitos_dominados", [])),
                "conceitos_frageis": len(memoria.get("conceitos_frageis", [])),
                "taxa_retencao": memoria.get("taxa_retencao", 0)
            },
            "proximas_revisoes": [
                {
                    "topico": item.topico,
                    "disciplina": item.disciplina,
                    "proxima_revisao": item.proxima_revisao.isoformat(),
                    "forca_memoria": item.forca_memoria.name
                }
                for item in itens_revisar
            ],
            "recomendacoes": diagnostico.get("recomendacoes", []),
            "dificuldade_recomendada": dificuldade.name
        }

    def obter_relatorio_progresso(
        self,
        aluno_id: str,
        periodo: str = "semanal"
    ) -> Dict:
        """
        Gera relatório de progresso.

        Args:
            aluno_id: ID do aluno
            periodo: "diario", "semanal", "mensal"

        Returns:
            Dict com relatório completo
        """
        # Obtém dados históricos
        estado = self.decision_engine.obter_estado_estudante(aluno_id)
        desempenho = self.question_engine.analisar_desempenho(aluno_id)

        # Calcula métricas
        return {
            "aluno_id": aluno_id,
            "periodo": periodo,
            "metricas": {
                "questoes_resolvidas": estado.total_questoes,
                "taxa_acerto": round(estado.taxa_acerto_geral * 100, 1),
                "tempo_total_estudo_horas": self._calcular_tempo_estudo(estado),
                "disciplinas_estudadas": len(estado.progresso_disciplinas),
                "conceitos_dominados": len(estado.conceitos_dominados)
            },
            "evolucao": {
                "por_disciplina": estado.taxa_acerto_disciplina,
                "conceitos_novos_dominados": len(estado.conceitos_dominados)
            },
            "conquistas": self._gerar_conquistas(estado),
            "meta_proxima_semana": self._gerar_meta(estado)
        }

    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================

    def _determinar_perfil(self, estado) -> StudentProfile:
        """Determina perfil baseado na taxa de acerto"""
        taxa = estado.taxa_acerto_geral

        if taxa < 0.4:
            return StudentProfile.INICIANTE
        elif taxa < 0.7:
            return StudentProfile.INTERMEDIARIO
        else:
            return StudentProfile.AVANCADO

    def _determinar_foco_drill(self, estado) -> str:
        """Determina foco do drill baseado no estado"""
        if len(estado.conceitos_deficientes) > 5:
            return "conceito"
        elif estado.nivel_confianca < 0.4:
            return "velocidade"
        else:
            return "pegadinha"

    def _serializar_questao(self, questao: Question) -> Dict:
        """Serializa questão para JSON"""
        return {
            "id": questao.id,
            "enunciado": questao.enunciado,
            "alternativas": [
                {
                    "letra": alt.letra,
                    "texto": alt.texto
                }
                for alt in questao.alternativas
            ],
            "disciplina": questao.disciplina,
            "topico": questao.topico,
            "dificuldade": questao.dificuldade.name
        }

    def _feedback_tempo(self, tempo_segundos: int) -> str:
        """Gera feedback sobre tempo gasto"""
        tempo_ideal = 180  # 3 minutos

        if tempo_segundos < tempo_ideal * 0.5:
            return "Muito rápido! Certifique-se de ler com atenção."
        elif tempo_segundos < tempo_ideal:
            return "Excelente ritmo!"
        elif tempo_segundos < tempo_ideal * 1.5:
            return "Bom, mas tente ser um pouco mais rápido."
        else:
            return "Muito lento. Pratique técnicas de leitura rápida."

    def _calcular_tempo_estudo(self, estado) -> int:
        """Calcula tempo total de estudo em horas"""
        # Simplificado: 3 min por questão
        minutos = estado.total_questoes * 3
        return minutos // 60

    def _gerar_conquistas(self, estado) -> List[str]:
        """Gera lista de conquistas do aluno"""
        conquistas = []

        if estado.total_questoes >= 100:
            conquistas.append("Centurião: 100+ questões resolvidas")

        if estado.taxa_acerto_geral >= 0.7:
            conquistas.append("Expert: Taxa de acerto acima de 70%")

        if len(estado.conceitos_dominados) >= 20:
            conquistas.append("Mestre Jurídico: 20+ conceitos dominados")

        return conquistas if conquistas else ["Continue estudando para desbloquear conquistas!"]

    def _gerar_meta(self, estado) -> str:
        """Gera meta para próxima semana"""
        if estado.taxa_acerto_geral < 0.5:
            return "Alcançar 50% de acerto geral"
        elif estado.taxa_acerto_geral < 0.7:
            return "Alcançar 70% de acerto geral"
        else:
            return "Manter taxa acima de 70% e resolver 50 questões"


# ============================================================
# EXEMPLO DE USO COMPLETO
# ============================================================

if __name__ == "__main__":
    print("=" * 80)
    print("JURIS_IA_CORE_V1 - SISTEMA COMPLETO")
    print("Demonstração de Fluxo End-to-End")
    print("=" * 80)

    # Inicializa sistema
    sistema = JurisIA()

    aluno_id = "estudante_001"

    print("\n" + "=" * 80)
    print("CENÁRIO 1: SESSÃO DE ESTUDO (1ª FASE)")
    print("=" * 80)

    # 1. Inicia sessão
    print("\n1. Iniciando sessão de estudo...")
    sessao = sistema.iniciar_sessao_estudo(
        aluno_id=aluno_id,
        disciplina="Direito Penal",
        tipo="drill"
    )

    print(f"\nPerfil do estudante: {sessao['perfil']}")
    print(f"Total de questões: {sessao['total_questoes']}")
    print(f"Tipo: {sessao['configuracao']['tipo']}")
    print(f"Estado emocional:")
    print(f"  Stress: {sessao['estado_emocional']['stress']:.2f}")
    print(f"  Motivação: {sessao['estado_emocional']['motivacao']:.2f}")
    print(f"  Confiança: {sessao['estado_emocional']['confianca']:.2f}")

    # 2. Simula resposta de questão
    print("\n2. Respondendo questão...")
    if sessao['total_questoes'] > 0:
        primeira_questao = sessao['questoes'][0]

        resposta = sistema.responder_questao(
            aluno_id=aluno_id,
            questao_id=primeira_questao['id'],
            alternativa_escolhida="A",
            tempo_segundos=195
        )

        print(f"\nResultado: {resposta['resultado']}")
        print(f"Nível de explicação: {resposta['nivel_explicacao']}")
        print(f"Feedback de tempo: {resposta['feedback_tempo']}")
        print(f"Revisão agendada: {resposta['revisao_agendada']}")

        if resposta.get('proximas_acoes'):
            print("\nPróximas ações recomendadas:")
            for acao in resposta['proximas_acoes']:
                print(f"  [{acao['prioridade']}] {acao['tipo']}: {acao['justificativa']}")

    # 3. Finaliza sessão
    print("\n3. Finalizando sessão...")
    relatorio = sistema.finalizar_sessao_estudo(aluno_id)

    print(f"\nResumo da sessão:")
    if relatorio.get('desempenho'):
        print(f"  Taxa de acerto: {relatorio['desempenho'].get('taxa_acerto_geral', 0)}%")
        print(f"  Total de questões: {relatorio['desempenho'].get('total_questoes', 0)}")

    print("\n" + "=" * 80)
    print("CENÁRIO 2: PRÁTICA DE PEÇA (2ª FASE)")
    print("=" * 80)

    # 4. Inicia prática de peça
    print("\n4. Iniciando prática de peça...")
    enunciado = "João emprestou R$ 10.000,00 a Maria que não pagou. Elabore petição inicial de cobrança."

    pratica = sistema.iniciar_pratica_peca(
        aluno_id=aluno_id,
        tipo_peca=PieceType.PETICAO_INICIAL_CIVEL,
        enunciado=enunciado
    )

    print(f"\nTipo de peça: {pratica['tipo_peca']}")
    print(f"Tempo recomendado: {pratica['tempo_recomendado_minutos']} minutos")
    print("\nChecklist:")
    for item in pratica['checklist']:
        print(f"  ☐ {item}")

    # 5. Avalia peça (simplificada)
    print("\n5. Avaliando peça...")
    peca_exemplo = """
    EXCELENTÍSSIMO SENHOR DOUTOR JUIZ DE DIREITO

    JOÃO DA SILVA vem propor AÇÃO DE COBRANÇA contra MARIA SOUZA.

    DOS FATOS: Autor emprestou R$ 10.000,00 à ré.

    Requer a condenação ao pagamento.

    ADVOGADO OAB/SP 123456
    """

    avaliacao_peca = sistema.avaliar_peca(
        aluno_id=aluno_id,
        tipo_peca=PieceType.PETICAO_INICIAL_CIVEL,
        conteudo=peca_exemplo,
        enunciado=enunciado
    )

    print(f"\nNota final: {avaliacao_peca['nota_final']}")
    print(f"Aprovado: {'SIM' if avaliacao_peca['aprovado'] else 'NÃO'}")
    print(f"Erros fatais: {avaliacao_peca['erros_fatais']}")
    print(f"Erros graves: {avaliacao_peca['erros_graves']}")

    print("\nCompetências:")
    for comp, nota in avaliacao_peca['competencias'].items():
        print(f"  {comp}: {nota:.1f}")

    # 6. Painel do estudante
    print("\n" + "=" * 80)
    print("CENÁRIO 3: PAINEL DO ESTUDANTE")
    print("=" * 80)

    print("\n6. Obtendo painel completo...")
    painel = sistema.obter_painel_estudante(aluno_id)

    print(f"\nVisão Geral:")
    print(f"  Nível: {painel['visao_geral']['nivel']}")
    print(f"  Taxa de acerto: {painel['visao_geral']['taxa_acerto_geral']}%")
    print(f"  Total de questões: {painel['visao_geral']['total_questoes']}")

    print(f"\nMemória:")
    print(f"  Total de conceitos: {painel['memoria']['total_conceitos']}")
    print(f"  Conceitos dominados: {painel['memoria']['conceitos_dominados']}")
    print(f"  Taxa de retenção: {painel['memoria']['taxa_retencao']}%")

    if painel.get('recomendacoes'):
        print("\nRecomendações:")
        for rec in painel['recomendacoes']:
            print(f"  • {rec}")

    # 7. Relatório de progresso
    print("\n7. Gerando relatório de progresso...")
    relatorio_progresso = sistema.obter_relatorio_progresso(aluno_id, periodo="semanal")

    print(f"\nMétricas da semana:")
    print(f"  Questões resolvidas: {relatorio_progresso['metricas']['questoes_resolvidas']}")
    print(f"  Taxa de acerto: {relatorio_progresso['metricas']['taxa_acerto']}%")
    print(f"  Tempo de estudo: {relatorio_progresso['metricas']['tempo_total_estudo_horas']}h")

    print("\nConquistas:")
    for conquista in relatorio_progresso['conquistas']:
        print(f"  🏆 {conquista}")

    print(f"\nMeta para próxima semana:")
    print(f"  🎯 {relatorio_progresso['meta_proxima_semana']}")

    print("\n" + "=" * 80)
    print("SISTEMA JURIS_IA - TOTALMENTE OPERACIONAL")
    print("=" * 80)
    print("\nTodos os engines integrados e funcionando em harmonia!")
    print("Sistema pronto para processar estudantes reais.")
