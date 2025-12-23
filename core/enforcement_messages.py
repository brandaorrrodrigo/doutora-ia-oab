"""
================================================================================
MENSAGENS PEDAGÓGICAS DE ENFORCEMENT - JURIS_IA_CORE_V1
================================================================================
Catálogo centralizado de mensagens para bloqueios e limites.

Princípios:
- Tom pedagógico, não financeiro
- Foco em organização do ciclo de estudo
- Sugestões neutras de upgrade
- Sem menção a custos, preços, infra, tokens, API

Autor: JURIS_IA_CORE_V1 - Engenheiro de Enforcement
Data: 2025-12-19
================================================================================
"""

from typing import Dict


class EnforcementMessages:
    """Catálogo de mensagens pedagógicas para enforcement"""

    def __init__(self):
        """Inicializa catálogo de mensagens"""
        self._messages = {
            # ======== SESSÕES ========
            "LIMIT_SESSIONS_DAILY": {
                "title": "Limite de sessões diárias atingido",
                "body": (
                    "Você completou suas sessões de estudo de hoje! "
                    "Para consolidar o aprendizado, recomendamos: "
                    "\n• Revisar os erros das sessões anteriores"
                    "\n• Estudar conteúdo teórico (lei seca, doutrina)"
                    "\n• Descansar e voltar amanhã com mente fresca"
                    "\n\nUma rotina consistente é mais eficaz que maratonas esporádicas."
                ),
                "upgrade": "Precisa de mais sessões? Planos Mensal e Semestral oferecem mais flexibilidade para seu ritmo de estudo.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            "LIMIT_SESSIONS_CONTINUOUS_STUDY_NOT_ALLOWED": {
                "title": "Modo revisão não disponível",
                "body": (
                    "Seu plano atual permite apenas sessões cronometradas. "
                    "O modo de revisão ilimitada ajuda a consolidar o aprendizado "
                    "sem consumir suas sessões diárias, permitindo que você: "
                    "\n• Revise erros sem limite de tempo"
                    "\n• Estude teoria relacionada às questões"
                    "\n• Aprofunde conceitos no seu próprio ritmo"
                ),
                "upgrade": "Planos Mensal e Semestral incluem modo revisão ilimitada para aprendizado mais profundo.",
                "plan_recommendation": "OAB_MENSAL"
            },

            # ======== QUESTÕES ========
            "LIMIT_QUESTIONS_SESSION": {
                "title": "Limite de questões da sessão atingido",
                "body": (
                    "Você completou o conjunto de questões desta sessão. "
                    "Para melhor absorção do conteúdo: "
                    "\n• Revise as questões que errou"
                    "\n• Anote os conceitos que precisa reforçar"
                    "\n• Finalize a sessão para ver seu desempenho"
                    "\n\nQualidade de estudo supera quantidade de questões."
                ),
                "upgrade": "Precisa resolver mais questões por sessão? O Plano Semestral oferece 25 questões por sessão.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            "LIMIT_QUESTIONS_DAILY": {
                "title": "Limite diário de questões atingido",
                "body": (
                    "Excelente! Você atingiu seu limite diário de questões. "
                    "Agora é hora de consolidar o aprendizado: "
                    "\n• Revise seus erros de hoje"
                    "\n• Estude a fundamentação teórica"
                    "\n• Descanse para melhor retenção"
                    "\n\nEstudar todos os dias é melhor que estudar muito em um dia."
                ),
                "upgrade": "Quer aumentar sua capacidade diária? Planos superiores oferecem mais questões e sessões.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            # ======== PEÇAS ========
            "LIMIT_PIECE_MONTHLY": {
                "title": "Limite mensal de peças atingido",
                "body": (
                    "Você utilizou todas as práticas de peça deste mês. "
                    "Para manter o ritmo de preparação: "
                    "\n• Revise as peças já elaboradas"
                    "\n• Estude os erros apontados nas correções"
                    "\n• Treine estrutura e argumentação mentalmente"
                    "\n\nNo próximo mês você terá novas oportunidades de prática."
                ),
                "upgrade": "Precisa praticar mais peças? O Plano Semestral oferece 10 práticas por mês.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            # ======== RELATÓRIOS ========
            "FEATURE_REPORT_COMPLETE_NOT_ALLOWED": {
                "title": "Relatório completo não disponível",
                "body": (
                    "Seu plano atual oferece relatórios básicos de desempenho. "
                    "Relatórios completos incluem: "
                    "\n• Análise detalhada por disciplina"
                    "\n• Evolução temporal com gráficos"
                    "\n• Recomendações personalizadas de estudo"
                    "\n• Mapa de calor de conhecimento"
                    "\n• Previsão de aprovação"
                ),
                "upgrade": "Planos Mensal e Semestral incluem relatórios completos para acompanhamento profundo.",
                "plan_recommendation": "OAB_MENSAL"
            },

            # ======== ASSINATURA ========
            "NO_ACTIVE_SUBSCRIPTION": {
                "title": "Nenhuma assinatura ativa",
                "body": (
                    "Você não possui uma assinatura ativa no momento. "
                    "Para acessar o sistema de estudo: "
                    "\n• Ative um plano de estudos"
                    "\n• Escolha o ritmo que se encaixa na sua rotina"
                    "\n• Comece sua jornada de aprovação"
                ),
                "upgrade": "Conheça nossos planos e escolha o ideal para sua preparação.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            "SUBSCRIPTION_EXPIRED": {
                "title": "Assinatura expirada",
                "body": (
                    "Sua assinatura expirou. Para continuar seus estudos: "
                    "\n• Renove sua assinatura"
                    "\n• Seus dados e progresso estão preservados"
                    "\n• Retome de onde parou assim que reativar"
                    "\n\nNão perca o ritmo de preparação que você construiu!"
                ),
                "upgrade": "Renove agora e continue sua preparação sem interrupções.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            # ======== FEATURES PROFISSIONAIS ========
            "FEATURE_MODE_PROFESSIONAL_NOT_ALLOWED": {
                "title": "Modo profissional não disponível",
                "body": (
                    "O modo profissional oferece funcionalidades avançadas: "
                    "\n• Questões comentadas por professores"
                    "\n• Vídeo-aulas explicativas"
                    "\n• Simulados oficiais"
                    "\n• Suporte prioritário"
                ),
                "upgrade": "Acesse recursos profissionais com planos superiores.",
                "plan_recommendation": "OAB_SEMESTRAL"
            },

            # ======== HEAVY USER ESCAPE VALVE ========
            "HEAVY_USER_EXTRA_SESSION_GRANTED": {
                "title": "🎯 Sessão extra liberada!",
                "body": (
                    "Parabéns pelo uso consistente! Detectamos seu ritmo intenso de estudos "
                    "nos últimos 7 dias e liberamos +1 sessão extra para hoje. "
                    "\n\n💪 Continue aproveitando esse momento de alta produtividade!"
                    "\n\n✨ Este benefício é renovado automaticamente quando você mantém "
                    "seu padrão de estudo consistente."
                    "\n\nObservação: Esta sessão extra não altera seu plano permanentemente. "
                    "É um reconhecimento do seu engajamento excepcional."
                ),
                "upgrade": "Você já está maximizando seu plano! Continue assim.",
                "plan_recommendation": "OAB_SEMESTRAL"
            }
        }

    def get_message(self, reason_code: str) -> Dict[str, str]:
        """
        Obtém mensagem formatada para um código de bloqueio.

        Args:
            reason_code: Código do motivo de bloqueio

        Returns:
            Dict com title, body, upgrade, plan_recommendation
        """
        return self._messages.get(
            reason_code,
            {
                "title": "Limite atingido",
                "body": "Você atingiu um limite do seu plano atual. Por favor, tente novamente mais tarde.",
                "upgrade": "Considere fazer upgrade para ter mais recursos.",
                "plan_recommendation": "OAB_SEMESTRAL"
            }
        )

    def get_all_messages(self) -> Dict[str, Dict[str, str]]:
        """Retorna todas as mensagens do catálogo"""
        return self._messages.copy()

    def add_custom_message(
        self,
        reason_code: str,
        title: str,
        body: str,
        upgrade: str,
        plan_recommendation: str = "OAB_SEMESTRAL"
    ) -> None:
        """
        Adiciona mensagem personalizada ao catálogo.

        Args:
            reason_code: Código único do motivo
            title: Título da mensagem
            body: Corpo da mensagem
            upgrade: Sugestão de upgrade
            plan_recommendation: Plano recomendado
        """
        self._messages[reason_code] = {
            "title": title,
            "body": body,
            "upgrade": upgrade,
            "plan_recommendation": plan_recommendation
        }
