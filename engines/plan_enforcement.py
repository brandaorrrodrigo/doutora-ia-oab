"""
Plan Enforcement Service
========================

Serviço para validar e aplicar limites de planos de assinatura.
Integra-se com o sistema de assinaturas e valida acessos aos recursos.

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-28
"""

from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from database.models import Assinatura, SessaoEstudo, PlanoStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LimitType(str, Enum):
    """Tipos de limite"""
    SESSOES_DIARIAS = "sessoes_diarias"
    QUESTOES_POR_SESSAO = "questoes_por_sessao"
    CHAT_IA = "chat_ia"
    PECAS = "pecas"
    RELATORIOS = "relatorios"
    SIMULADOS = "simulados"


class EnforcementError(Exception):
    """Exceção customizada para erros de enforcement"""
    def __init__(self, message: str, limit_type: LimitType, current: int, limit: int, plano: str):
        self.message = message
        self.limit_type = limit_type
        self.current = current
        self.limit = limit
        self.plano = plano
        super().__init__(self.message)


class PlanEnforcementService:
    """Serviço de enforcement de limites por plano"""

    def __init__(self, db: Session):
        self.db = db

    def obter_assinatura(self, user_id: str) -> Optional[Assinatura]:
        """
        Obtém a assinatura ativa do usuário

        Args:
            user_id: ID do usuário

        Returns:
            Assinatura ou None
        """
        return self.db.query(Assinatura).filter(
            and_(
                Assinatura.user_id == user_id,
                Assinatura.status.in_([PlanoStatus.ATIVO, PlanoStatus.TRIAL])
            )
        ).first()

    def verificar_sessoes_diarias(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica se o usuário pode iniciar uma nova sessão de estudo hoje

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com resultado da verificação

        Raises:
            EnforcementError: Se o limite foi atingido
        """
        assinatura = self.obter_assinatura(user_id)

        if not assinatura:
            raise EnforcementError(
                message="Nenhuma assinatura ativa encontrada",
                limit_type=LimitType.SESSOES_DIARIAS,
                current=0,
                limit=0,
                plano="NENHUM"
            )

        # Plano ilimitado (-1 sessões)
        if assinatura.sessoes_por_dia == -1:
            return {
                'allowed': True,
                'unlimited': True,
                'plano': assinatura.plano
            }

        # Contar sessões de hoje
        hoje = date.today()
        sessoes_hoje = self.db.query(func.count(SessaoEstudo.id)).filter(
            and_(
                SessaoEstudo.aluno_id == user_id,
                func.date(SessaoEstudo.data_inicio) == hoje
            )
        ).scalar() or 0

        if sessoes_hoje >= assinatura.sessoes_por_dia:
            raise EnforcementError(
                message=f"Limite diário de sessões atingido. Seu plano {assinatura.plano} permite {assinatura.sessoes_por_dia} sessões por dia.",
                limit_type=LimitType.SESSOES_DIARIAS,
                current=sessoes_hoje,
                limit=assinatura.sessoes_por_dia,
                plano=assinatura.plano
            )

        return {
            'allowed': True,
            'sessoes_usadas': sessoes_hoje,
            'sessoes_restantes': assinatura.sessoes_por_dia - sessoes_hoje,
            'limite': assinatura.sessoes_por_dia,
            'plano': assinatura.plano
        }

    def verificar_questoes_por_sessao(self, user_id: str, questoes_ja_respondidas: int = 0) -> Dict[str, Any]:
        """
        Verifica se o usuário pode responder mais questões nesta sessão

        Args:
            user_id: ID do usuário
            questoes_ja_respondidas: Quantas questões já foram respondidas nesta sessão

        Returns:
            Dicionário com resultado da verificação

        Raises:
            EnforcementError: Se o limite foi atingido
        """
        assinatura = self.obter_assinatura(user_id)

        if not assinatura:
            raise EnforcementError(
                message="Nenhuma assinatura ativa encontrada",
                limit_type=LimitType.QUESTOES_POR_SESSAO,
                current=0,
                limit=0,
                plano="NENHUM"
            )

        # Plano ilimitado (-1 questões)
        if assinatura.questoes_por_sessao == -1:
            return {
                'allowed': True,
                'unlimited': True,
                'plano': assinatura.plano
            }

        if questoes_ja_respondidas >= assinatura.questoes_por_sessao:
            raise EnforcementError(
                message=f"Limite de questões por sessão atingido. Seu plano {assinatura.plano} permite {assinatura.questoes_por_sessao} questões por sessão.",
                limit_type=LimitType.QUESTOES_POR_SESSAO,
                current=questoes_ja_respondidas,
                limit=assinatura.questoes_por_sessao,
                plano=assinatura.plano
            )

        return {
            'allowed': True,
            'questoes_respondidas': questoes_ja_respondidas,
            'questoes_restantes': assinatura.questoes_por_sessao - questoes_ja_respondidas,
            'limite': assinatura.questoes_por_sessao,
            'plano': assinatura.plano
        }

    def verificar_acesso_chat_ia(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica se o usuário tem acesso ao chat com IA

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com resultado da verificação

        Raises:
            EnforcementError: Se não tiver acesso
        """
        assinatura = self.obter_assinatura(user_id)

        if not assinatura:
            raise EnforcementError(
                message="Nenhuma assinatura ativa encontrada",
                limit_type=LimitType.CHAT_IA,
                current=0,
                limit=0,
                plano="NENHUM"
            )

        if not assinatura.acesso_chat_ia:
            raise EnforcementError(
                message=f"Chat com IA não disponível no plano {assinatura.plano}. Faça upgrade para PREMIUM ou PRO para ter acesso.",
                limit_type=LimitType.CHAT_IA,
                current=0,
                limit=1,
                plano=assinatura.plano
            )

        return {
            'allowed': True,
            'plano': assinatura.plano
        }

    def verificar_acesso_pecas(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica se o usuário tem acesso à prática de peças

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com resultado da verificação

        Raises:
            EnforcementError: Se não tiver acesso
        """
        assinatura = self.obter_assinatura(user_id)

        if not assinatura:
            raise EnforcementError(
                message="Nenhuma assinatura ativa encontrada",
                limit_type=LimitType.PECAS,
                current=0,
                limit=0,
                plano="NENHUM"
            )

        if not assinatura.acesso_pecas:
            raise EnforcementError(
                message=f"Prática de peças não disponível no plano {assinatura.plano}. Faça upgrade para PREMIUM ou PRO para ter acesso.",
                limit_type=LimitType.PECAS,
                current=0,
                limit=1,
                plano=assinatura.plano
            )

        return {
            'allowed': True,
            'plano': assinatura.plano
        }

    def verificar_acesso_relatorios(self, user_id: str) -> Dict[str, Any]:
        """
        Verifica se o usuário tem acesso a relatórios detalhados

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com resultado da verificação

        Raises:
            EnforcementError: Se não tiver acesso
        """
        assinatura = self.obter_assinatura(user_id)

        if not assinatura:
            raise EnforcementError(
                message="Nenhuma assinatura ativa encontrada",
                limit_type=LimitType.RELATORIOS,
                current=0,
                limit=0,
                plano="NENHUM"
            )

        if not assinatura.acesso_relatorios:
            raise EnforcementError(
                message=f"Relatórios detalhados não disponíveis no plano {assinatura.plano}. Faça upgrade para PREMIUM ou PRO para ter acesso.",
                limit_type=LimitType.RELATORIOS,
                current=0,
                limit=1,
                plano=assinatura.plano
            )

        return {
            'allowed': True,
            'plano': assinatura.plano
        }

    def obter_limites_usuario(self, user_id: str) -> Dict[str, Any]:
        """
        Retorna todos os limites e acessos do usuário

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com todos os limites
        """
        assinatura = self.obter_assinatura(user_id)

        if not assinatura:
            return {
                'plano': 'NENHUM',
                'status': 'INATIVO',
                'limites': {}
            }

        # Contar uso de hoje
        hoje = date.today()
        sessoes_hoje = self.db.query(func.count(SessaoEstudo.id)).filter(
            and_(
                SessaoEstudo.aluno_id == user_id,
                func.date(SessaoEstudo.data_inicio) == hoje
            )
        ).scalar() or 0

        return {
            'plano': assinatura.plano,
            'status': assinatura.status.value,
            'preco_mensal': float(assinatura.preco_mensal),
            'limites': {
                'sessoes_por_dia': {
                    'limite': assinatura.sessoes_por_dia,
                    'usado_hoje': sessoes_hoje,
                    'restante': assinatura.sessoes_por_dia - sessoes_hoje if assinatura.sessoes_por_dia > 0 else -1,
                    'ilimitado': assinatura.sessoes_por_dia == -1
                },
                'questoes_por_sessao': {
                    'limite': assinatura.questoes_por_sessao,
                    'ilimitado': assinatura.questoes_por_sessao == -1
                }
            },
            'acessos': {
                'chat_ia': assinatura.acesso_chat_ia,
                'pecas': assinatura.acesso_pecas,
                'relatorios': assinatura.acesso_relatorios,
                'simulados': assinatura.acesso_simulados
            },
            'datas': {
                'data_inicio': assinatura.data_inicio.isoformat() if assinatura.data_inicio else None,
                'proxima_cobranca': assinatura.proxima_cobranca.isoformat() if assinatura.proxima_cobranca else None,
                'cancelado_em': assinatura.cancelado_em.isoformat() if assinatura.cancelado_em else None
            }
        }


# ============================================================================
# DECORADOR PARA ENDPOINTS
# ============================================================================

def enforce_plan_limits(limit_type: LimitType):
    """
    Decorador para aplicar enforcement em endpoints

    Usage:
        @enforce_plan_limits(LimitType.SESSOES_DIARIAS)
        async def iniciar_sessao(user_id: str, db: Session = Depends(get_db)):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extrair user_id e db dos argumentos
            user_id = kwargs.get('user_id') or (args[0] if len(args) > 0 else None)
            db = kwargs.get('db')

            if not db:
                raise ValueError("DB session não fornecida ao decorador")

            enforcement = PlanEnforcementService(db)

            try:
                # Verificar limite baseado no tipo
                if limit_type == LimitType.SESSOES_DIARIAS:
                    enforcement.verificar_sessoes_diarias(user_id)
                elif limit_type == LimitType.CHAT_IA:
                    enforcement.verificar_acesso_chat_ia(user_id)
                elif limit_type == LimitType.PECAS:
                    enforcement.verificar_acesso_pecas(user_id)
                elif limit_type == LimitType.RELATORIOS:
                    enforcement.verificar_acesso_relatorios(user_id)

                # Se passou na verificação, executar função
                return await func(*args, **kwargs)

            except EnforcementError as e:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=403,
                    detail={
                        'error': e.message,
                        'limit_type': e.limit_type.value,
                        'current': e.current,
                        'limit': e.limit,
                        'plano_atual': e.plano,
                        'upgrade_url': '/planos'
                    }
                )

        return wrapper
    return decorator
