"""
Cliente para Chat Server Multi-Tenant
Integração do Doutora IA OAB com o servidor de chat centralizado
"""

import os
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ChatServerClient:
    """Cliente para comunicação com o Chat Server Multi-Tenant"""

    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Inicializa o cliente do chat server

        Args:
            server_url: URL do servidor de chat (padrão: variável CHAT_SERVER_URL)
            api_key: API key do projeto (padrão: variável CHAT_API_KEY)
        """
        self.server_url = server_url or os.getenv(
            'CHAT_SERVER_URL',
            'http://localhost:3001'
        )
        self.api_key = api_key or os.getenv(
            'CHAT_API_KEY',
            'doutoraia-oab-2025-secret-key-ultra-secure'
        )

        # Remover trailing slash
        self.server_url = self.server_url.rstrip('/')

        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        })

    def chat(
        self,
        user_name: str,
        message: str,
        context_type: str = 'general',
        timeout: int = 45
    ) -> Dict[str, Any]:
        """
        Envia mensagem para o chat server

        Args:
            user_name: Nome do usuário
            message: Mensagem a ser processada
            context_type: Tipo de contexto (general, legal, etc)
            timeout: Timeout em segundos

        Returns:
            Dict com a resposta do servidor:
            {
                'success': True,
                'message': 'Resposta da IA...',
                'tokens': 123,
                'model': 'llama3.1:8b',
                'project': 'Doutora IA OAB'
            }
        """
        try:
            response = self.session.post(
                f'{self.server_url}/api/chat',
                json={
                    'userName': user_name,
                    'message': message,
                    'contextType': context_type
                },
                timeout=timeout
            )

            response.raise_for_status()
            data = response.json()

            logger.info(
                f"Chat response received: {data.get('tokens', 0)} tokens, "
                f"model: {data.get('model', 'unknown')}"
            )

            return data

        except requests.exceptions.Timeout:
            logger.error(f"Chat server timeout after {timeout}s")
            return self._fallback_response(message)

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to chat server at {self.server_url}")
            return self._fallback_response(message)

        except requests.exceptions.RequestException as e:
            logger.error(f"Chat server error: {str(e)}")
            return self._fallback_response(message)

    def get_welcome_message(self) -> Optional[str]:
        """
        Obtém mensagem de boas-vindas do projeto

        Returns:
            Mensagem de boas-vindas ou None em caso de erro
        """
        try:
            response = self.session.get(
                f'{self.server_url}/api/chat/welcome',
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            return data.get('welcome')

        except Exception as e:
            logger.error(f"Failed to get welcome message: {str(e)}")
            return None

    def health_check(self) -> bool:
        """
        Verifica se o chat server está online

        Returns:
            True se o servidor está respondendo, False caso contrário
        """
        try:
            response = self.session.get(
                f'{self.server_url}/health',
                timeout=3
            )
            return response.status_code == 200

        except Exception:
            return False

    def _fallback_response(self, message: str) -> Dict[str, Any]:
        """
        Retorna resposta de fallback quando o servidor está offline

        Args:
            message: Mensagem original do usuário

        Returns:
            Resposta de fallback
        """
        fallback_messages = [
            "Consulte um advogado para seu caso específico! ⚖️",
            "Legislação pode mudar - confirme com profissional! 📜",
            "Esta informação é apenas educacional! 👨‍⚖️",
            "Para casos concretos, procure orientação jurídica profissional.",
            "Estou aqui para auxiliar nos estudos. Para casos reais, consulte um advogado."
        ]

        # Selecionar resposta baseada no tamanho da mensagem
        index = len(message) % len(fallback_messages)

        return {
            'success': True,
            'message': fallback_messages[index],
            'tokens': 0,
            'source': 'fallback',
            'project': 'Doutora IA OAB'
        }


# Instância global (singleton)
_chat_client: Optional[ChatServerClient] = None


def get_chat_client() -> ChatServerClient:
    """
    Obtém instância singleton do cliente de chat

    Returns:
        Instância do ChatServerClient
    """
    global _chat_client

    if _chat_client is None:
        _chat_client = ChatServerClient()

        # Verificar se o servidor está acessível
        if _chat_client.health_check():
            logger.info(
                f"Chat server connected: {_chat_client.server_url}"
            )
        else:
            logger.warning(
                f"Chat server not accessible: {_chat_client.server_url}. "
                "Fallback responses will be used."
            )

    return _chat_client


# Exemplo de uso
if __name__ == '__main__':
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    # Criar cliente
    client = get_chat_client()

    # Testar conexão
    if client.health_check():
        print("✅ Chat server online!")

        # Obter mensagem de boas-vindas
        welcome = client.get_welcome_message()
        if welcome:
            print(f"📝 Welcome: {welcome}")

        # Enviar mensagem de teste
        response = client.chat(
            user_name="Teste",
            message="O que é LGPD?",
            context_type="legal"
        )

        print(f"\n💬 Response:")
        print(f"   Success: {response['success']}")
        print(f"   Message: {response['message']}")
        print(f"   Tokens: {response.get('tokens', 0)}")
        print(f"   Model: {response.get('model', 'fallback')}")

    else:
        print("❌ Chat server offline - usando fallback")

        response = client.chat(
            user_name="Teste",
            message="O que é LGPD?"
        )

        print(f"\n💬 Fallback Response:")
        print(f"   Message: {response['message']}")
