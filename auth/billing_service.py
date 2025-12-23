#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
BILLING SERVICE - ETAPA 10.4
================================================================================

Serviço de billing com integração Stripe:
- Criação de customers
- Criação de subscriptions
- Processamento de webhooks
- Gestão de invoices
- Cancelamento e reativação

NOTA: Requer instalação de 'stripe' package:
    pip install stripe

Autor: JURIS IA CORE V1
Data: 2025-12-17
================================================================================
"""

import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from uuid import UUID, uuid4
from sqlalchemy import text
from database.connection import DatabaseConnection
from auth.subscription_service import SubscriptionService

# Stripe será importado condicionalmente
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    print("WARNING: Stripe não instalado. Instale com: pip install stripe")


class BillingService:
    """Serviço de billing com integração Stripe."""

    def __init__(self):
        self.db = DatabaseConnection()
        self.subscription_service = SubscriptionService()

        # Configurar Stripe (se disponível)
        if STRIPE_AVAILABLE:
            # Obter API key de variável de ambiente
            self.stripe_api_key = os.getenv("STRIPE_API_KEY")
            self.stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

            if self.stripe_api_key:
                stripe.api_key = self.stripe_api_key
            else:
                print("WARNING: STRIPE_API_KEY não configurada")

    # ============================================================================
    # CUSTOMERS (CLIENTES)
    # ============================================================================

    def criar_stripe_customer(
        self,
        usuario_id: UUID,
        email: str,
        nome_completo: str,
        cpf: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Cria customer no Stripe.

        Args:
            usuario_id: ID do usuário
            email: Email do usuário
            nome_completo: Nome completo
            cpf: CPF (para tax ID)

        Returns:
            Tupla (sucesso, customer_id, erro)
        """
        if not STRIPE_AVAILABLE:
            return False, None, "Stripe não disponível"

        if not self.stripe_api_key:
            return False, None, "Stripe API key não configurada"

        try:
            # Criar customer no Stripe
            customer_data = {
                "email": email,
                "name": nome_completo,
                "metadata": {
                    "usuario_id": str(usuario_id)
                }
            }

            # Adicionar CPF como tax ID (se fornecido)
            if cpf:
                customer_data["tax_id_data"] = [{
                    "type": "br_cpf",
                    "value": cpf
                }]

            customer = stripe.Customer.create(**customer_data)

            # Atualizar usuário com customer_id
            with self.db.get_session() as session:
                session.execute(
                    text("""
                        UPDATE usuario
                        SET stripe_customer_id = :customer_id
                        WHERE id = :usuario_id
                    """),
                    {
                        "customer_id": customer.id,
                        "usuario_id": usuario_id
                    }
                )
                session.commit()

            return True, customer.id, None

        except Exception as e:
            return False, None, str(e)

    def obter_stripe_customer_id(self, usuario_id: UUID) -> Optional[str]:
        """
        Obtém Stripe customer ID do usuário.

        Args:
            usuario_id: ID do usuário

        Returns:
            Customer ID ou None
        """
        with self.db.get_session() as session:
            result = session.execute(
                text("""
                    SELECT stripe_customer_id
                    FROM usuario
                    WHERE id = :usuario_id
                """),
                {"usuario_id": usuario_id}
            ).fetchone()

            return result[0] if result and result[0] else None

    # ============================================================================
    # SUBSCRIPTIONS (ASSINATURAS)
    # ============================================================================

    def criar_stripe_subscription(
        self,
        usuario_id: UUID,
        codigo_plano: str,
        periodo: str = "monthly",
        payment_method_id: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Cria subscription no Stripe e assinatura local.

        Args:
            usuario_id: ID do usuário
            codigo_plano: Código do plano (BASIC, PRO)
            periodo: Período (monthly, yearly)
            payment_method_id: ID do método de pagamento Stripe

        Returns:
            Tupla (sucesso, dados, erro)
        """
        if not STRIPE_AVAILABLE:
            return False, None, "Stripe não disponível"

        # Validações
        if codigo_plano == "FREE":
            # Plano FREE não usa Stripe
            sucesso, assinatura_id, erro = self.subscription_service.criar_assinatura(
                usuario_id, "FREE", "monthly"
            )
            if sucesso:
                return True, {"assinatura_id": assinatura_id}, None
            return False, None, erro

        # Obter plano
        plano = self.subscription_service.obter_plano(codigo_plano)
        if not plano:
            return False, None, f"Plano {codigo_plano} não encontrado"

        # Obter customer ID (ou criar)
        customer_id = self.obter_stripe_customer_id(usuario_id)

        if not customer_id:
            # Buscar dados do usuário
            with self.db.get_session() as session:
                result = session.execute(
                    text("""
                        SELECT email, nome_completo, cpf
                        FROM usuario
                        WHERE id = :usuario_id
                    """),
                    {"usuario_id": usuario_id}
                ).fetchone()

                if not result:
                    return False, None, "Usuário não encontrado"

                email, nome_completo, cpf = result

            # Criar customer
            sucesso, customer_id, erro = self.criar_stripe_customer(
                usuario_id, email, nome_completo, cpf
            )

            if not sucesso:
                return False, None, f"Erro ao criar customer: {erro}"

        try:
            # Determinar price ID baseado no plano e período
            # NOTA: Price IDs devem ser criados previamente no Stripe Dashboard
            # Formato: price_PLANO_PERIODO (ex: price_BASIC_monthly, price_PRO_yearly)
            price_id_mapping = {
                ("BASIC", "monthly"): os.getenv("STRIPE_PRICE_BASIC_MONTHLY"),
                ("BASIC", "yearly"): os.getenv("STRIPE_PRICE_BASIC_YEARLY"),
                ("PRO", "monthly"): os.getenv("STRIPE_PRICE_PRO_MONTHLY"),
                ("PRO", "yearly"): os.getenv("STRIPE_PRICE_PRO_YEARLY"),
            }

            price_id = price_id_mapping.get((codigo_plano, periodo))

            if not price_id:
                return False, None, f"Price ID não configurado para {codigo_plano}/{periodo}"

            # Criar subscription no Stripe
            subscription_data = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "metadata": {
                    "usuario_id": str(usuario_id),
                    "plano_codigo": codigo_plano
                }
            }

            # Adicionar método de pagamento se fornecido
            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id

            # Criar subscription
            subscription = stripe.Subscription.create(**subscription_data)

            # Criar assinatura local
            sucesso, assinatura_id, erro = self.subscription_service.criar_assinatura(
                usuario_id,
                codigo_plano,
                periodo,
                em_trial=False,
                stripe_subscription_id=subscription.id
            )

            if not sucesso:
                # Cancelar subscription no Stripe se falhar localmente
                stripe.Subscription.delete(subscription.id)
                return False, None, f"Erro ao criar assinatura local: {erro}"

            return True, {
                "assinatura_id": assinatura_id,
                "stripe_subscription_id": subscription.id,
                "stripe_customer_id": customer_id,
                "status": subscription.status
            }, None

        except Exception as e:
            return False, None, str(e)

    def cancelar_stripe_subscription(
        self,
        assinatura_id: UUID,
        motivo: Optional[str] = None,
        cancelar_imediatamente: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Cancela subscription no Stripe e assinatura local.

        Args:
            assinatura_id: ID da assinatura local
            motivo: Motivo do cancelamento
            cancelar_imediatamente: Se True, cancela imediatamente. Se False, cancela ao fim do período.

        Returns:
            Tupla (sucesso, erro)
        """
        if not STRIPE_AVAILABLE:
            # Apenas cancelar localmente
            return self.subscription_service.cancelar_assinatura(assinatura_id, motivo)

        with self.db.get_session() as session:
            # Obter Stripe subscription ID
            result = session.execute(
                text("""
                    SELECT stripe_subscription_id
                    FROM assinatura
                    WHERE id = :assinatura_id
                """),
                {"assinatura_id": assinatura_id}
            ).fetchone()

            if not result or not result[0]:
                # Sem Stripe subscription, apenas cancelar localmente
                return self.subscription_service.cancelar_assinatura(assinatura_id, motivo)

            stripe_subscription_id = result[0]

            try:
                # Cancelar no Stripe
                if cancelar_imediatamente:
                    stripe.Subscription.delete(stripe_subscription_id)
                else:
                    stripe.Subscription.modify(
                        stripe_subscription_id,
                        cancel_at_period_end=True
                    )

                # Cancelar localmente
                return self.subscription_service.cancelar_assinatura(assinatura_id, motivo)

            except Exception as e:
                return False, str(e)

    # ============================================================================
    # WEBHOOKS
    # ============================================================================

    def processar_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Processa webhook do Stripe.

        Args:
            payload: Raw payload do webhook
            signature: Assinatura do webhook (header Stripe-Signature)

        Returns:
            Tupla (sucesso, erro)
        """
        if not STRIPE_AVAILABLE:
            return False, "Stripe não disponível"

        if not self.stripe_webhook_secret:
            return False, "Webhook secret não configurado"

        try:
            # Verificar assinatura
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )

            # Processar evento
            event_type = event["type"]
            event_data = event["data"]["object"]

            if event_type == "customer.subscription.created":
                return self._handle_subscription_created(event_data)

            elif event_type == "customer.subscription.updated":
                return self._handle_subscription_updated(event_data)

            elif event_type == "customer.subscription.deleted":
                return self._handle_subscription_deleted(event_data)

            elif event_type == "invoice.payment_succeeded":
                return self._handle_payment_succeeded(event_data)

            elif event_type == "invoice.payment_failed":
                return self._handle_payment_failed(event_data)

            else:
                # Evento não tratado
                return True, None

        except Exception as e:
            return False, str(e)

    def _handle_subscription_created(self, subscription) -> Tuple[bool, Optional[str]]:
        """Processa criação de subscription."""
        # Subscription já criada pelo endpoint, apenas logar
        return True, None

    def _handle_subscription_updated(self, subscription) -> Tuple[bool, Optional[str]]:
        """Processa atualização de subscription."""
        stripe_subscription_id = subscription["id"]
        status = subscription["status"]

        with self.db.get_session() as session:
            # Atualizar status local
            session.execute(
                text("""
                    UPDATE assinatura
                    SET status = :status
                    WHERE stripe_subscription_id = :stripe_subscription_id
                """),
                {
                    "status": status,
                    "stripe_subscription_id": stripe_subscription_id
                }
            )
            session.commit()

        return True, None

    def _handle_subscription_deleted(self, subscription) -> Tuple[bool, Optional[str]]:
        """Processa cancelamento de subscription."""
        stripe_subscription_id = subscription["id"]

        with self.db.get_session() as session:
            # Marcar como cancelada
            session.execute(
                text("""
                    UPDATE assinatura
                    SET status = 'canceled',
                        data_cancelamento = NOW(),
                        motivo_cancelamento = 'Cancelada via Stripe'
                    WHERE stripe_subscription_id = :stripe_subscription_id
                """),
                {"stripe_subscription_id": stripe_subscription_id}
            )
            session.commit()

        return True, None

    def _handle_payment_succeeded(self, invoice) -> Tuple[bool, Optional[str]]:
        """Processa pagamento bem-sucedido."""
        stripe_subscription_id = invoice.get("subscription")

        if not stripe_subscription_id:
            return True, None

        with self.db.get_session() as session:
            # Atualizar data de renovação
            session.execute(
                text("""
                    UPDATE assinatura
                    SET data_renovacao = NOW(),
                        status = 'active'
                    WHERE stripe_subscription_id = :stripe_subscription_id
                """),
                {"stripe_subscription_id": stripe_subscription_id}
            )
            session.commit()

        return True, None

    def _handle_payment_failed(self, invoice) -> Tuple[bool, Optional[str]]:
        """Processa falha de pagamento."""
        stripe_subscription_id = invoice.get("subscription")

        if not stripe_subscription_id:
            return True, None

        with self.db.get_session() as session:
            # Marcar como past_due
            session.execute(
                text("""
                    UPDATE assinatura
                    SET status = 'past_due'
                    WHERE stripe_subscription_id = :stripe_subscription_id
                """),
                {"stripe_subscription_id": stripe_subscription_id}
            )
            session.commit()

        return True, None

    # ============================================================================
    # PAYMENT METHODS
    # ============================================================================

    def criar_payment_intent(
        self,
        usuario_id: UUID,
        valor: float,
        moeda: str = "brl",
        descricao: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Cria Payment Intent para pagamento único.

        Args:
            usuario_id: ID do usuário
            valor: Valor em reais
            moeda: Moeda (brl)
            descricao: Descrição do pagamento

        Returns:
            Tupla (sucesso, dados, erro)
        """
        if not STRIPE_AVAILABLE:
            return False, None, "Stripe não disponível"

        # Obter customer ID
        customer_id = self.obter_stripe_customer_id(usuario_id)

        try:
            # Criar Payment Intent
            intent = stripe.PaymentIntent.create(
                amount=int(valor * 100),  # Converter para centavos
                currency=moeda,
                customer=customer_id,
                description=descricao,
                metadata={"usuario_id": str(usuario_id)}
            )

            return True, {
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
                "status": intent.status
            }, None

        except Exception as e:
            return False, None, str(e)
