"""
Sistema de Envio de Emails - JURIS_IA_CORE_V1
==============================================

Serviço de envio de emails usando SendGrid.
Suporta templates HTML e envio transacional.

Autor: JURIS_IA_CORE_V1
Data: 2025-12-28
"""

import os
from typing import Optional, List, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    """Configuração de email"""
    sendgrid_api_key: str
    from_email: str
    from_name: str
    reply_to: Optional[str] = None


class EmailService:
    """Serviço de envio de emails"""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.client = SendGridAPIClient(api_key=config.sendgrid_api_key)

    def enviar_email(
        self,
        para: str,
        assunto: str,
        conteudo_html: str,
        conteudo_texto: Optional[str] = None
    ) -> bool:
        """
        Envia email simples

        Args:
            para: Email do destinatário
            assunto: Assunto do email
            conteudo_html: Conteúdo HTML do email
            conteudo_texto: Conteúdo em texto plano (fallback)

        Returns:
            True se enviado com sucesso
        """
        try:
            message = Mail(
                from_email=Email(self.config.from_email, self.config.from_name),
                to_emails=To(para),
                subject=assunto,
                html_content=Content("text/html", conteudo_html)
            )

            if conteudo_texto:
                message.add_content(Content("text/plain", conteudo_texto))

            if self.config.reply_to:
                message.reply_to = Email(self.config.reply_to)

            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email enviado com sucesso para {para}")
                return True
            else:
                logger.error(f"Erro ao enviar email: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            logger.error(f"Exceção ao enviar email: {str(e)}")
            return False

    def enviar_recuperacao_senha(
        self,
        para: str,
        nome: str,
        token: str,
        frontend_url: str
    ) -> bool:
        """
        Envia email de recuperação de senha

        Args:
            para: Email do usuário
            nome: Nome do usuário
            token: Token de recuperação
            frontend_url: URL base do frontend

        Returns:
            True se enviado com sucesso
        """
        reset_url = f"{frontend_url}/resetar-senha/{token}"

        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recuperação de Senha - Doutora IA OAB</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #5B21B6 0%, #3B82F6 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🎓 Doutora IA OAB</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
        <h2 style="color: #5B21B6; margin-top: 0;">Olá, {nome}!</h2>

        <p style="font-size: 16px; margin: 20px 0;">
            Recebemos uma solicitação para redefinir sua senha. Se você não fez essa solicitação,
            pode ignorar este email com segurança.
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}"
               style="background: linear-gradient(135deg, #5B21B6 0%, #3B82F6 100%);
                      color: white;
                      padding: 15px 40px;
                      text-decoration: none;
                      border-radius: 8px;
                      font-size: 18px;
                      font-weight: bold;
                      display: inline-block;">
                Redefinir Senha
            </a>
        </div>

        <p style="font-size: 14px; color: #6b7280; margin: 20px 0;">
            Ou copie e cole este link no seu navegador:<br>
            <a href="{reset_url}" style="color: #3B82F6; word-break: break-all;">{reset_url}</a>
        </p>

        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                ⚠️ <strong>Importante:</strong> Este link expira em <strong>1 hora</strong> por questões de segurança.
            </p>
        </div>

        <p style="font-size: 14px; color: #6b7280; margin: 20px 0 0 0;">
            Se você tiver alguma dúvida ou problema, entre em contato conosco.
        </p>
    </div>

    <div style="background: #f3f4f6; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280;">
        <p style="margin: 5px 0;">
            © 2024 Doutora IA OAB - Sua plataforma de preparação para a OAB
        </p>
        <p style="margin: 5px 0;">
            Este é um email automático, por favor não responda.
        </p>
    </div>
</body>
</html>
        """

        texto = f"""
Olá, {nome}!

Recebemos uma solicitação para redefinir sua senha.

Clique no link abaixo para criar uma nova senha:
{reset_url}

⚠️ Este link expira em 1 hora por questões de segurança.

Se você não fez essa solicitação, pode ignorar este email.

---
Doutora IA OAB
        """

        return self.enviar_email(
            para=para,
            assunto="Recuperação de Senha - Doutora IA OAB",
            conteudo_html=html,
            conteudo_texto=texto
        )

    def enviar_boas_vindas(
        self,
        para: str,
        nome: str,
        frontend_url: str
    ) -> bool:
        """Envia email de boas-vindas após cadastro"""
        login_url = f"{frontend_url}/login"

        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bem-vindo à Doutora IA OAB</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #5B21B6 0%, #3B82F6 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🎓 Bem-vindo à Doutora IA OAB!</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
        <h2 style="color: #5B21B6; margin-top: 0;">Olá, {nome}!</h2>

        <p style="font-size: 16px; margin: 20px 0;">
            Estamos muito felizes em tê-lo(a) conosco! 🎉
        </p>

        <p style="font-size: 16px; margin: 20px 0;">
            Você agora tem acesso à plataforma mais completa de preparação para a OAB, com:
        </p>

        <ul style="font-size: 15px; line-height: 2; color: #4b5563;">
            <li>✅ Mais de <strong>8.000 questões</strong> da OAB</li>
            <li>🎯 Sistema de <strong>revisão espaçada</strong> inteligente</li>
            <li>🤖 <strong>Chat com IA</strong> especializada em Direito</li>
            <li>⚖️ <strong>Prática de peças</strong> processuais</li>
            <li>📊 <strong>Relatórios detalhados</strong> do seu progresso</li>
            <li>🏆 <strong>Gamificação</strong> com conquistas e níveis</li>
        </ul>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{login_url}"
               style="background: linear-gradient(135deg, #5B21B6 0%, #3B82F6 100%);
                      color: white;
                      padding: 15px 40px;
                      text-decoration: none;
                      border-radius: 8px;
                      font-size: 18px;
                      font-weight: bold;
                      display: inline-block;">
                Começar a Estudar
            </a>
        </div>

        <div style="background: #dbeafe; border-left: 4px solid #3B82F6; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0; font-size: 14px; color: #1e40af;">
                💡 <strong>Dica:</strong> Estabeleça uma rotina diária de estudos. Mesmo 30 minutos por dia fazem diferença!
            </p>
        </div>

        <p style="font-size: 14px; color: #6b7280; margin: 20px 0 0 0;">
            Qualquer dúvida, estamos aqui para ajudar!
        </p>
    </div>

    <div style="background: #f3f4f6; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280;">
        <p style="margin: 5px 0;">
            © 2024 Doutora IA OAB
        </p>
        <p style="margin: 5px 0;">
            <a href="{frontend_url}" style="color: #3B82F6; text-decoration: none;">Acessar Plataforma</a>
        </p>
    </div>
</body>
</html>
        """

        return self.enviar_email(
            para=para,
            assunto="🎓 Bem-vindo à Doutora IA OAB!",
            conteudo_html=html
        )

    def enviar_lembrete_estudos(
        self,
        para: str,
        nome: str,
        dias_sem_estudar: int,
        frontend_url: str
    ) -> bool:
        """Envia lembrete para usuário que não estuda há dias"""
        dashboard_url = f"{frontend_url}/dashboard"

        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sentimos sua falta!</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #5B21B6 0%, #3B82F6 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">📚 Sentimos sua falta!</h1>
    </div>

    <div style="background: #f9fafb; padding: 30px; border: 1px solid #e5e7eb; border-top: none;">
        <h2 style="color: #5B21B6; margin-top: 0;">Olá, {nome}!</h2>

        <p style="font-size: 16px; margin: 20px 0;">
            Notamos que você não estuda há <strong>{dias_sem_estudar} dias</strong>.
        </p>

        <p style="font-size: 16px; margin: 20px 0;">
            A consistência é a chave para a aprovação na OAB! Que tal retomar seus estudos hoje?
        </p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{dashboard_url}"
               style="background: linear-gradient(135deg, #5B21B6 0%, #3B82F6 100%);
                      color: white;
                      padding: 15px 40px;
                      text-decoration: none;
                      border-radius: 8px;
                      font-size: 18px;
                      font-weight: bold;
                      display: inline-block;">
                Voltar a Estudar
            </a>
        </div>

        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                ⏰ <strong>Lembrete:</strong> Estudar um pouco todos os dias é melhor do que estudar muito de vez em quando!
            </p>
        </div>
    </div>

    <div style="background: #f3f4f6; padding: 20px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #6b7280;">
        <p style="margin: 5px 0;">
            © 2024 Doutora IA OAB
        </p>
    </div>
</body>
</html>
        """

        return self.enviar_email(
            para=para,
            assunto=f"📚 Sentimos sua falta, {nome}!",
            conteudo_html=html
        )


# Singleton do serviço de email
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Retorna instância singleton do serviço de email"""
    global _email_service

    if _email_service is None:
        config = EmailConfig(
            sendgrid_api_key=os.getenv("SENDGRID_API_KEY", ""),
            from_email=os.getenv("FROM_EMAIL", "noreply@doutoraia.com"),
            from_name=os.getenv("FROM_NAME", "Doutora IA OAB"),
            reply_to=os.getenv("REPLY_TO_EMAIL")
        )
        _email_service = EmailService(config)

    return _email_service
