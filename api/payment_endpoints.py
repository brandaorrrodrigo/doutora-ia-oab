"""
Endpoints de Pagamento e Assinaturas
====================================

API REST para gerenciamento de pagamentos via Stripe:
- Criação de checkout
- Processamento de webhooks
- Gerenciamento de assinaturas
- Portal do cliente

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-28
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database.connection import get_db_session
from database.models import User, Assinatura, Pagamento, PlanoStatus
from engines.stripe_service import get_stripe_service
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
stripe_service = get_stripe_service()


# ============================================================================
# SCHEMAS
# ============================================================================

class CriarCheckoutRequest(BaseModel):
    """Request para criar sessão de checkout"""
    user_id: str
    plano: str  # PREMIUM ou PRO
    metadata: Optional[Dict[str, str]] = None


class CancelarAssinaturaRequest(BaseModel):
    """Request para cancelar assinatura"""
    user_id: str
    imediatamente: bool = False


class ReativarAssinaturaRequest(BaseModel):
    """Request para reativar assinatura"""
    user_id: str


class PortalClienteRequest(BaseModel):
    """Request para acessar portal do cliente"""
    user_id: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/pagamento/criar-checkout")
async def criar_checkout(request: CriarCheckoutRequest, db: Session = Depends(get_db_session)):
    """
    Cria uma sessão de checkout do Stripe

    Fluxo:
    1. Valida usuário existe
    2. Cria/obtém cliente Stripe
    3. Cria sessão de checkout
    4. Retorna URL de checkout
    """
    try:
        # Validar usuário
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # Validar plano
        if request.plano not in ['PREMIUM', 'PRO']:
            raise HTTPException(status_code=400, detail="Plano inválido. Use PREMIUM ou PRO.")

        # Obter ou criar assinatura
        assinatura = db.query(Assinatura).filter(Assinatura.user_id == user.id).first()

        # Criar/Obter cliente Stripe
        if assinatura and assinatura.stripe_customer_id:
            customer_id = assinatura.stripe_customer_id
        else:
            customer_result = stripe_service.criar_cliente(
                email=user.email,
                nome=user.nome,
                user_id=str(user.id),
                metadata=request.metadata
            )

            if not customer_result['success']:
                raise HTTPException(status_code=500, detail=customer_result['error'])

            customer_id = customer_result['customer_id']

            # Atualizar assinatura com customer_id
            if not assinatura:
                plano_info = stripe_service.obter_plano_info(request.plano)
                assinatura = Assinatura(
                    user_id=user.id,
                    plano='GRATUITO',
                    status=PlanoStatus.ATIVO,
                    preco_mensal=0.00,
                    sessoes_por_dia=plano_info['sessoes_por_dia'],
                    questoes_por_sessao=plano_info['questoes_por_sessao'],
                    acesso_chat_ia=plano_info['acesso_chat_ia'],
                    acesso_pecas=plano_info['acesso_pecas'],
                    acesso_relatorios=plano_info['acesso_relatorios'],
                    acesso_simulados=plano_info['acesso_simulados'],
                    stripe_customer_id=customer_id
                )
                db.add(assinatura)
            else:
                assinatura.stripe_customer_id = customer_id

            db.commit()

        # Criar sessão de checkout
        checkout_result = stripe_service.criar_checkout_session(
            customer_id=customer_id,
            plano=request.plano,
            user_id=str(user.id),
            metadata=request.metadata
        )

        if not checkout_result['success']:
            raise HTTPException(status_code=500, detail=checkout_result['error'])

        return {
            'success': True,
            'checkout_url': checkout_result['checkout_url'],
            'session_id': checkout_result['session_id']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar checkout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao criar checkout: {str(e)}")


@router.post("/pagamento/webhook")
async def webhook_stripe(request: Request, db: Session = Depends(get_db_session)):
    """
    Processa webhooks do Stripe

    Eventos tratados:
    - checkout.session.completed: Assinatura criada
    - customer.subscription.updated: Assinatura atualizada
    - customer.subscription.deleted: Assinatura cancelada
    - invoice.payment_succeeded: Pagamento bem-sucedido
    - invoice.payment_failed: Pagamento falhou
    """
    try:
        payload = await request.body()
        signature = request.headers.get('stripe-signature')

        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")

        # Processar webhook
        webhook_result = stripe_service.processar_webhook(payload, signature)

        if not webhook_result['success']:
            raise HTTPException(status_code=400, detail=webhook_result['error'])

        event_type = webhook_result['type']
        event_data = webhook_result['data']

        logger.info(f"Webhook recebido: {event_type}")

        # Processar eventos
        if event_type == 'checkout.session.completed':
            await _processar_checkout_completo(event_data, db)

        elif event_type == 'customer.subscription.updated':
            await _processar_assinatura_atualizada(event_data, db)

        elif event_type == 'customer.subscription.deleted':
            await _processar_assinatura_cancelada(event_data, db)

        elif event_type == 'invoice.payment_succeeded':
            await _processar_pagamento_sucesso(event_data, db)

        elif event_type == 'invoice.payment_failed':
            await _processar_pagamento_falha(event_data, db)

        return {'success': True, 'processed': event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pagamento/assinatura/{user_id}")
async def obter_assinatura(user_id: str, db: Session = Depends(get_db_session)):
    """Obtém assinatura do usuário"""
    try:
        assinatura = db.query(Assinatura).filter(Assinatura.user_id == user_id).first()

        if not assinatura:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")

        # Sincronizar com Stripe se tiver subscription_id
        stripe_info = None
        if assinatura.stripe_subscription_id:
            stripe_result = stripe_service.obter_assinatura(assinatura.stripe_subscription_id)
            if stripe_result['success']:
                stripe_info = {
                    'status': stripe_result['status'],
                    'current_period_end': stripe_result['current_period_end'].isoformat(),
                    'cancel_at_period_end': stripe_result['cancel_at_period_end']
                }

        return {
            'success': True,
            'data': {
                'id': str(assinatura.id),
                'plano': assinatura.plano,
                'status': assinatura.status.value,
                'preco_mensal': float(assinatura.preco_mensal),
                'sessoes_por_dia': assinatura.sessoes_por_dia,
                'questoes_por_sessao': assinatura.questoes_por_sessao,
                'acesso_chat_ia': assinatura.acesso_chat_ia,
                'acesso_pecas': assinatura.acesso_pecas,
                'acesso_relatorios': assinatura.acesso_relatorios,
                'acesso_simulados': assinatura.acesso_simulados,
                'data_inicio': assinatura.data_inicio.isoformat() if assinatura.data_inicio else None,
                'proxima_cobranca': assinatura.proxima_cobranca.isoformat() if assinatura.proxima_cobranca else None,
                'cancelado_em': assinatura.cancelado_em.isoformat() if assinatura.cancelado_em else None,
                'stripe_info': stripe_info
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter assinatura: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pagamento/cancelar")
async def cancelar_assinatura(request: CancelarAssinaturaRequest, db: Session = Depends(get_db_session)):
    """Cancela assinatura do usuário"""
    try:
        assinatura = db.query(Assinatura).filter(Assinatura.user_id == request.user_id).first()

        if not assinatura:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")

        if not assinatura.stripe_subscription_id:
            raise HTTPException(status_code=400, detail="Assinatura não possui ID do Stripe")

        # Cancelar no Stripe
        cancel_result = stripe_service.cancelar_assinatura(
            subscription_id=assinatura.stripe_subscription_id,
            imediatamente=request.imediatamente
        )

        if not cancel_result['success']:
            raise HTTPException(status_code=500, detail=cancel_result['error'])

        # Atualizar banco de dados
        if request.imediatamente:
            assinatura.status = PlanoStatus.CANCELADO
            assinatura.data_fim = datetime.now()
            assinatura.cancelado_em = datetime.now()

            # Reverter para plano gratuito
            plano_gratuito = stripe_service.obter_plano_info('GRATUITO')
            assinatura.plano = 'GRATUITO'
            assinatura.preco_mensal = plano_gratuito['preco']
            assinatura.sessoes_por_dia = plano_gratuito['sessoes_por_dia']
            assinatura.questoes_por_sessao = plano_gratuito['questoes_por_sessao']
            assinatura.acesso_chat_ia = plano_gratuito['acesso_chat_ia']
            assinatura.acesso_pecas = plano_gratuito['acesso_pecas']
            assinatura.acesso_relatorios = plano_gratuito['acesso_relatorios']
        else:
            assinatura.cancelado_em = datetime.now()
            # Status permanece ATIVO até o fim do período

        db.commit()

        return {
            'success': True,
            'mensagem': 'Assinatura cancelada com sucesso',
            'cancelado_imediatamente': request.imediatamente,
            'valido_ate': cancel_result.get('valido_ate').isoformat() if cancel_result.get('valido_ate') else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar assinatura: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pagamento/reativar")
async def reativar_assinatura(request: ReativarAssinaturaRequest, db: Session = Depends(get_db_session)):
    """Reativa assinatura cancelada"""
    try:
        assinatura = db.query(Assinatura).filter(Assinatura.user_id == request.user_id).first()

        if not assinatura:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")

        if not assinatura.stripe_subscription_id:
            raise HTTPException(status_code=400, detail="Assinatura não possui ID do Stripe")

        # Reativar no Stripe
        reactivate_result = stripe_service.reativar_assinatura(assinatura.stripe_subscription_id)

        if not reactivate_result['success']:
            raise HTTPException(status_code=500, detail=reactivate_result['error'])

        # Atualizar banco de dados
        assinatura.status = PlanoStatus.ATIVO
        assinatura.cancelado_em = None
        db.commit()

        return {
            'success': True,
            'mensagem': 'Assinatura reativada com sucesso'
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao reativar assinatura: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pagamento/portal")
async def obter_portal_cliente(request: PortalClienteRequest, db: Session = Depends(get_db_session)):
    """Obtém URL do portal do cliente Stripe"""
    try:
        assinatura = db.query(Assinatura).filter(Assinatura.user_id == request.user_id).first()

        if not assinatura:
            raise HTTPException(status_code=404, detail="Assinatura não encontrada")

        if not assinatura.stripe_customer_id:
            raise HTTPException(status_code=400, detail="Cliente não possui ID do Stripe")

        # Criar sessão do portal
        portal_result = stripe_service.criar_portal_cliente(
            customer_id=assinatura.stripe_customer_id,
            return_url='http://localhost:3000/dashboard'
        )

        if not portal_result['success']:
            raise HTTPException(status_code=500, detail=portal_result['error'])

        return {
            'success': True,
            'portal_url': portal_result['portal_url']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter portal: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pagamento/planos")
async def listar_planos():
    """Lista todos os planos disponíveis"""
    try:
        planos = stripe_service.listar_todos_planos()

        return {
            'success': True,
            'data': planos
        }

    except Exception as e:
        logger.error(f"Erro ao listar planos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usuario/limites/{user_id}")
async def obter_limites_usuario(user_id: str, db: Session = Depends(get_db_session)):
    """Obtém todos os limites e uso atual do usuário"""
    try:
        from engines.plan_enforcement import PlanEnforcementService

        enforcement = PlanEnforcementService(db)
        limites = enforcement.obter_limites_usuario(user_id)

        return {
            'success': True,
            'data': limites
        }

    except Exception as e:
        logger.error(f"Erro ao obter limites: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FUNÇÕES AUXILIARES - PROCESSAMENTO DE WEBHOOKS
# ============================================================================

async def _processar_checkout_completo(data: Dict[str, Any], db: Session):
    """Processa checkout.session.completed"""
    user_id = data.get('metadata', {}).get('user_id')
    plano = data.get('metadata', {}).get('plano')
    subscription_id = data.get('subscription')

    if not user_id or not plano:
        logger.warning("Checkout sem user_id ou plano nos metadados")
        return

    assinatura = db.query(Assinatura).filter(Assinatura.user_id == user_id).first()

    if assinatura:
        plano_info = stripe_service.obter_plano_info(plano)

        assinatura.plano = plano
        assinatura.status = PlanoStatus.ATIVO
        assinatura.preco_mensal = plano_info['preco']
        assinatura.sessoes_por_dia = plano_info['sessoes_por_dia']
        assinatura.questoes_por_sessao = plano_info['questoes_por_sessao']
        assinatura.acesso_chat_ia = plano_info['acesso_chat_ia']
        assinatura.acesso_pecas = plano_info['acesso_pecas']
        assinatura.acesso_relatorios = plano_info['acesso_relatorios']
        assinatura.stripe_subscription_id = subscription_id
        assinatura.data_inicio = datetime.now()

        db.commit()
        logger.info(f"Assinatura {plano} ativada para usuário {user_id}")


async def _processar_assinatura_atualizada(data: Dict[str, Any], db: Session):
    """Processa customer.subscription.updated"""
    subscription_id = data.get('id')
    status = data.get('status')

    assinatura = db.query(Assinatura).filter(
        Assinatura.stripe_subscription_id == subscription_id
    ).first()

    if assinatura:
        if status == 'active':
            assinatura.status = PlanoStatus.ATIVO
        elif status == 'canceled':
            assinatura.status = PlanoStatus.CANCELADO
        elif status == 'past_due':
            assinatura.status = PlanoStatus.PAUSADO

        db.commit()


async def _processar_assinatura_cancelada(data: Dict[str, Any], db: Session):
    """Processa customer.subscription.deleted"""
    subscription_id = data.get('id')

    assinatura = db.query(Assinatura).filter(
        Assinatura.stripe_subscription_id == subscription_id
    ).first()

    if assinatura:
        # Reverter para plano gratuito
        plano_gratuito = stripe_service.obter_plano_info('GRATUITO')
        assinatura.plano = 'GRATUITO'
        assinatura.status = PlanoStatus.CANCELADO
        assinatura.preco_mensal = plano_gratuito['preco']
        assinatura.sessoes_por_dia = plano_gratuito['sessoes_por_dia']
        assinatura.questoes_por_sessao = plano_gratuito['questoes_por_sessao']
        assinatura.acesso_chat_ia = plano_gratuito['acesso_chat_ia']
        assinatura.acesso_pecas = plano_gratuito['acesso_pecas']
        assinatura.acesso_relatorios = plano_gratuito['acesso_relatorios']
        assinatura.data_fim = datetime.now()

        db.commit()
        logger.info(f"Assinatura cancelada e revertida para GRATUITO: {assinatura.user_id}")


async def _processar_pagamento_sucesso(data: Dict[str, Any], db: Session):
    """Processa invoice.payment_succeeded"""
    subscription_id = data.get('subscription')
    amount = data.get('amount_paid') / 100  # Centavos para reais
    payment_intent = data.get('payment_intent')

    assinatura = db.query(Assinatura).filter(
        Assinatura.stripe_subscription_id == subscription_id
    ).first()

    if assinatura:
        # Criar registro de pagamento
        pagamento = Pagamento(
            assinatura_id=assinatura.id,
            user_id=assinatura.user_id,
            valor=amount,
            moeda='BRL',
            status='PAGO',
            metodo_pagamento='card',
            stripe_payment_intent_id=payment_intent,
            stripe_invoice_id=data.get('id'),
            data_pagamento=datetime.now(),
            metadata=data
        )
        db.add(pagamento)

        # Atualizar próxima cobrança
        current_period_end = datetime.fromtimestamp(data.get('period_end', 0))
        assinatura.proxima_cobranca = current_period_end

        db.commit()
        logger.info(f"Pagamento registrado: R$ {amount} - Usuário {assinatura.user_id}")


async def _processar_pagamento_falha(data: Dict[str, Any], db: Session):
    """Processa invoice.payment_failed"""
    subscription_id = data.get('subscription')
    amount = data.get('amount_due') / 100

    assinatura = db.query(Assinatura).filter(
        Assinatura.stripe_subscription_id == subscription_id
    ).first()

    if assinatura:
        # Criar registro de pagamento falhado
        pagamento = Pagamento(
            assinatura_id=assinatura.id,
            user_id=assinatura.user_id,
            valor=amount,
            moeda='BRL',
            status='FALHOU',
            metodo_pagamento='card',
            stripe_invoice_id=data.get('id'),
            mensagem_erro=data.get('last_payment_error', {}).get('message', 'Pagamento falhou'),
            metadata=data
        )
        db.add(pagamento)

        # Marcar assinatura como pausada
        assinatura.status = PlanoStatus.PAUSADO

        db.commit()
        logger.warning(f"Pagamento falhou: R$ {amount} - Usuário {assinatura.user_id}")
