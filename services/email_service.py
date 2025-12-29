"""
Serviço de envio de emails usando SendGrid
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import Optional
import logging

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'noreply@doutoraia.com')
FROM_NAME = os.getenv('FROM_NAME', 'Doutora IA OAB')

sg = SendGridAPIClient(api_key=SENDGRID_API_KEY) if SENDGRID_API_KEY else None


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Envia email usando SendGrid

    Args:
        to_email: Email do destinatário
        subject: Assunto do email
        html_content: Conteúdo HTML do email
        text_content: Conteúdo texto plano (fallback)

    Returns:
        bool: True se enviado com sucesso
    """
    if not sg:
        logger.error("SendGrid API key não configurada")
        return False

    try:
        message = Mail(
            from_email=Email(FROM_EMAIL, FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", html_content)
        )

        if text_content:
            message.add_content(Content("text/plain", text_content))

        response = sg.send(message)

        if response.status_code in [200, 201, 202]:
            logger.info(f"Email enviado para {to_email}: {subject}")
            return True
        else:
            logger.error(f"Erro ao enviar email: {response.status_code} - {response.body}")
            return False

    except Exception as e:
        logger.error(f"Exceção ao enviar email para {to_email}: {str(e)}")
        return False


def send_welcome_email(user_name: str, user_email: str) -> bool:
    """
    Envia email de boas-vindas para novo usuário
    """
    subject = "Bem-vindo à Doutora IA OAB! 🎉"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 40px 20px;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #7c3aed; font-size: 28px; margin: 0;">
                    ⚖️ Doutora IA OAB
                </h1>
            </div>

            <!-- Content -->
            <div style="color: #333; line-height: 1.6;">
                <h2 style="color: #7c3aed; font-size: 24px;">
                    Olá, {user_name}! 👋
                </h2>

                <p style="font-size: 16px; margin: 20px 0;">
                    Seja muito bem-vindo à <strong>Doutora IA OAB</strong>! 🎓
                </p>

                <p style="font-size: 16px; margin: 20px 0;">
                    Sua conta foi criada com sucesso. Agora você tem acesso a:
                </p>

                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <ul style="margin: 0; padding-left: 20px;">
                        <li style="margin: 10px 0;">✅ <strong>8.261 questões</strong> da OAB comentadas pela IA</li>
                        <li style="margin: 10px 0;">✅ <strong>Sistema de estudo adaptativo</strong> com inteligência artificial</li>
                        <li style="margin: 10px 0;">✅ <strong>Simulados</strong> e revisão espaçada</li>
                        <li style="margin: 10px 0;">✅ <strong>Sistema de gamificação</strong> com FP (Functional Points)</li>
                    </ul>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://doutoraia.com/login"
                       style="display: inline-block; background-color: #7c3aed; color: white;
                              padding: 14px 28px; text-decoration: none; border-radius: 6px;
                              font-weight: bold; font-size: 16px;">
                        Fazer Primeiro Login
                    </a>
                </div>

                <p style="font-size: 14px; color: #666; margin: 20px 0;">
                    <strong>Dica:</strong> Complete seu perfil para personalizar ainda mais sua experiência!
                </p>
            </div>

            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb;
                        text-align: center; color: #6b7280; font-size: 12px;">
                <p style="margin: 5px 0;">
                    Equipe Doutora IA OAB<br>
                    Sua aprovação é nossa missão!
                </p>
                <p style="margin: 10px 0;">
                    <a href="https://doutoraia.com" style="color: #7c3aed; text-decoration: none;">doutoraia.com</a> |
                    <a href="mailto:suporte@doutoraia.com" style="color: #7c3aed; text-decoration: none;">suporte@doutoraia.com</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Olá, {user_name}!

    Seja muito bem-vindo à Doutora IA OAB!

    Sua conta foi criada com sucesso. Agora você tem acesso a:

    - 8.261 questões da OAB comentadas pela IA
    - Sistema de estudo adaptativo com inteligência artificial
    - Simulados e revisão espaçada
    - Sistema de gamificação com FP (Functional Points)

    Acesse: https://doutoraia.com/login

    Dica: Complete seu perfil para personalizar ainda mais sua experiência!

    --
    Equipe Doutora IA OAB
    Sua aprovação é nossa missão!
    """

    return send_email(user_email, subject, html_content, text_content)


def send_password_reset_email(user_name: str, user_email: str, reset_token: str) -> bool:
    """
    Envia email de recuperação de senha
    """
    reset_url = f"https://doutoraia.com/recuperar-senha?token={reset_token}"

    subject = "Recuperação de Senha - Doutora IA OAB"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 40px 20px;">
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #7c3aed; font-size: 28px; margin: 0;">
                    ⚖️ Doutora IA OAB
                </h1>
            </div>

            <!-- Content -->
            <div style="color: #333; line-height: 1.6;">
                <h2 style="color: #7c3aed; font-size: 24px;">
                    Recuperação de Senha
                </h2>

                <p style="font-size: 16px; margin: 20px 0;">
                    Olá, {user_name}!
                </p>

                <p style="font-size: 16px; margin: 20px 0;">
                    Recebemos uma solicitação para redefinir a senha da sua conta.
                </p>

                <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b;
                            padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px; color: #92400e;">
                        <strong>⚠️ Atenção:</strong> Este link é válido por apenas <strong>1 hora</strong>.
                    </p>
                </div>

                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}"
                       style="display: inline-block; background-color: #7c3aed; color: white;
                              padding: 14px 28px; text-decoration: none; border-radius: 6px;
                              font-weight: bold; font-size: 16px;">
                        Redefinir Senha
                    </a>
                </div>

                <p style="font-size: 14px; color: #666; margin: 20px 0;">
                    Ou copie e cole este link no seu navegador:
                </p>

                <div style="background-color: #f9f9f9; padding: 12px; border-radius: 4px;
                            word-break: break-all; font-size: 12px; color: #666;">
                    {reset_url}
                </div>

                <div style="background-color: #fee2e2; border-left: 4px solid #ef4444;
                            padding: 15px; margin: 20px 0; border-radius: 4px;">
                    <p style="margin: 0; font-size: 14px; color: #991b1b;">
                        <strong>🔒 Não solicitou?</strong> Ignore este email. Sua senha permanecerá inalterada.
                    </p>
                </div>
            </div>

            <!-- Footer -->
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb;
                        text-align: center; color: #6b7280; font-size: 12px;">
                <p style="margin: 5px 0;">
                    Equipe Doutora IA OAB<br>
                    Sua aprovação é nossa missão!
                </p>
                <p style="margin: 10px 0;">
                    <a href="https://doutoraia.com" style="color: #7c3aed; text-decoration: none;">doutoraia.com</a> |
                    <a href="mailto:suporte@doutoraia.com" style="color: #7c3aed; text-decoration: none;">suporte@doutoraia.com</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    Recuperação de Senha - Doutora IA OAB

    Olá, {user_name}!

    Recebemos uma solicitação para redefinir a senha da sua conta.

    ⚠️ Este link é válido por apenas 1 hora.

    Clique no link abaixo para redefinir sua senha:
    {reset_url}

    🔒 Não solicitou? Ignore este email. Sua senha permanecerá inalterada.

    --
    Equipe Doutora IA OAB
    Sua aprovação é nossa missão!
    """

    return send_email(user_email, subject, html_content, text_content)
