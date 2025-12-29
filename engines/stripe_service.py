"""
Serviço de Integração com Stripe
================================

Gerencia todas as operações de pagamento via Stripe:
- Criação de clientes
- Sessões de checkout
- Gerenciamento de assinaturas
- Processamento de webhooks
- Cancelamento e reembolsos

Autor: Sistema JURIS_IA_CORE_V1
Data: 2025-12-28
"""

import os
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class StripeConfig:
    """Configuração do Stripe"""
    api_key: str
    webhook_secret: str
    price_id_premium: str
    price_id_pro: str
    success_url: str
    cancel_url: str


class StripeService:
    """Serviço de integração com Stripe"""

    PLANOS = {
        'GRATUITO': {
            'nome': 'Plano Gratuito',
            'preco': 0.00,
            'sessoes_por_dia': 5,
            'questoes_por_sessao': 10,
            'acesso_chat_ia': False,
            'acesso_pecas': False,
            'acesso_relatorios': False,
            'acesso_simulados': True,
        },
        'PREMIUM': {
            'nome': 'Plano Premium',
            'preco': 49.90,
            'sessoes_por_dia': 15,
            'questoes_por_sessao': 30,
            'acesso_chat_ia': True,
            'acesso_pecas': True,
            'acesso_relatorios': True,
            'acesso_simulados': True,
        },
        'PRO': {
            'nome': 'Plano Pro',
            'preco': 99.90,
            'sessoes_por_dia': -1,  # Ilimitado
            'questoes_por_sessao': -1,  # Ilimitado
            'acesso_chat_ia': True,
            'acesso_pecas': True,
            'acesso_relatorios': True,
            'acesso_simulados': True,
        }
    }

    def __init__(self, config: StripeConfig):
        """Inicializa o serviço Stripe"""
        self.config = config
        stripe.api_key = config.api_key

    def criar_cliente(
        self,
        email: str,
        nome: str,
        user_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Cria um cliente no Stripe

        Args:
            email: Email do usuário
            nome: Nome do usuário
            user_id: ID do usuário no sistema
            metadata: Metadados adicionais

        Returns:
            Dados do cliente criado
        """
        try:
            customer_metadata = {'user_id': user_id}
            if metadata:
                customer_metadata.update(metadata)

            customer = stripe.Customer.create(
                email=email,
                name=nome,
                metadata=customer_metadata
            )

            return {
                'success': True,
                'customer_id': customer.id,
                'customer': customer
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def criar_checkout_session(
        self,
        customer_id: str,
        plano: str,
        user_id: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Cria uma sessão de checkout para assinatura

        Args:
            customer_id: ID do cliente no Stripe
            plano: Plano escolhido (PREMIUM ou PRO)
            user_id: ID do usuário
            metadata: Metadados adicionais

        Returns:
            Dados da sessão de checkout
        """
        try:
            if plano not in ['PREMIUM', 'PRO']:
                return {
                    'success': False,
                    'error': 'Plano inválido. Use PREMIUM ou PRO.'
                }

            # Selecionar price_id correto
            price_id = (
                self.config.price_id_premium if plano == 'PREMIUM'
                else self.config.price_id_pro
            )

            session_metadata = {
                'user_id': user_id,
                'plano': plano
            }
            if metadata:
                session_metadata.update(metadata)

            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=self.config.success_url,
                cancel_url=self.config.cancel_url,
                metadata=session_metadata,
                allow_promotion_codes=True,
                billing_address_collection='auto',
                subscription_data={
                    'metadata': session_metadata,
                    'trial_period_days': 7,  # 7 dias de teste grátis
                }
            )

            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url,
                'session': session
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def obter_assinatura(self, subscription_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes de uma assinatura

        Args:
            subscription_id: ID da assinatura no Stripe

        Returns:
            Dados da assinatura
        """
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)

            return {
                'success': True,
                'subscription': subscription,
                'status': subscription.status,
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def cancelar_assinatura(
        self,
        subscription_id: str,
        imediatamente: bool = False
    ) -> Dict[str, Any]:
        """
        Cancela uma assinatura

        Args:
            subscription_id: ID da assinatura no Stripe
            imediatamente: Se True, cancela imediatamente. Se False, cancela ao fim do período

        Returns:
            Resultado do cancelamento
        """
        try:
            if imediatamente:
                subscription = stripe.Subscription.delete(subscription_id)
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )

            return {
                'success': True,
                'subscription': subscription,
                'cancelado_em': datetime.now(),
                'valido_ate': datetime.fromtimestamp(subscription.current_period_end) if not imediatamente else None
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def reativar_assinatura(self, subscription_id: str) -> Dict[str, Any]:
        """
        Reativa uma assinatura que estava marcada para cancelamento

        Args:
            subscription_id: ID da assinatura no Stripe

        Returns:
            Resultado da reativação
        """
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )

            return {
                'success': True,
                'subscription': subscription,
                'mensagem': 'Assinatura reativada com sucesso'
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def processar_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """
        Processa webhooks do Stripe

        Args:
            payload: Payload bruto do webhook
            signature: Assinatura do webhook

        Returns:
            Evento processado
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.config.webhook_secret
            )

            return {
                'success': True,
                'event': event,
                'type': event['type'],
                'data': event['data']['object']
            }
        except ValueError as e:
            return {
                'success': False,
                'error': f'Payload inválido: {str(e)}'
            }
        except stripe.error.SignatureVerificationError as e:
            return {
                'success': False,
                'error': f'Assinatura inválida: {str(e)}'
            }

    def criar_portal_cliente(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """
        Cria sessão do portal do cliente (gerenciamento de assinatura)

        Args:
            customer_id: ID do cliente no Stripe
            return_url: URL para retornar após gerenciamento

        Returns:
            URL do portal
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )

            return {
                'success': True,
                'portal_url': session.url
            }
        except stripe.error.StripeError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def obter_plano_info(self, plano: str) -> Optional[Dict[str, Any]]:
        """
        Retorna informações de um plano

        Args:
            plano: Nome do plano (GRATUITO, PREMIUM, PRO)

        Returns:
            Informações do plano ou None
        """
        return self.PLANOS.get(plano)

    def listar_todos_planos(self) -> Dict[str, Dict[str, Any]]:
        """Retorna todos os planos disponíveis"""
        return self.PLANOS


# ============================================================================
# Singleton Pattern
# ============================================================================

_stripe_service_instance: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    """
    Retorna instância singleton do StripeService

    Configuração via variáveis de ambiente:
    - STRIPE_API_KEY: Chave secreta da API Stripe
    - STRIPE_WEBHOOK_SECRET: Secret para validação de webhooks
    - STRIPE_PRICE_ID_PREMIUM: Price ID do plano Premium
    - STRIPE_PRICE_ID_PRO: Price ID do plano Pro
    - FRONTEND_URL: URL do frontend
    """
    global _stripe_service_instance

    if _stripe_service_instance is None:
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

        config = StripeConfig(
            api_key=os.getenv('STRIPE_API_KEY', ''),
            webhook_secret=os.getenv('STRIPE_WEBHOOK_SECRET', ''),
            price_id_premium=os.getenv('STRIPE_PRICE_ID_PREMIUM', ''),
            price_id_pro=os.getenv('STRIPE_PRICE_ID_PRO', ''),
            success_url=f'{frontend_url}/pagamento/sucesso?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{frontend_url}/planos?cancelado=true'
        )

        _stripe_service_instance = StripeService(config)

    return _stripe_service_instance
