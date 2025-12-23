#!/usr/bin/env python3
"""
================================================================================
VALIDADOR DE AMBIENTE - DEPLOY P0
================================================================================
Valida todas as variáveis de ambiente necessárias para o deploy P0
Data: 2025-12-18
================================================================================
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Cores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(msg: str):
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{msg.center(80)}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

def print_success(msg: str):
    print(f"{GREEN}[OK]{RESET} {msg}")

def print_error(msg: str):
    print(f"{RED}[ERRO]{RESET} {msg}")

def print_warning(msg: str):
    print(f"{YELLOW}[AVISO]{RESET} {msg}")

def print_info(msg: str):
    print(f"{BLUE}[INFO]{RESET} {msg}")

# Variáveis obrigatórias para P0
REQUIRED_VARS = {
    # Database
    'DATABASE_URL': {
        'description': 'URL de conexão PostgreSQL',
        'example': 'postgresql://user:pass@host:5432/db',
        'critical': True
    },
    'POSTGRES_PASSWORD': {
        'description': 'Senha do PostgreSQL',
        'example': 'strong_password_here',
        'critical': True
    },

    # Redis
    'REDIS_URL': {
        'description': 'URL de conexão Redis',
        'example': 'redis://redis:6379/0',
        'critical': True
    },

    # Ollama/LLM
    'OLLAMA_HOST': {
        'description': 'URL do servidor Ollama',
        'example': 'http://ollama:11434',
        'critical': True
    },
    'EMBEDDING_MODEL': {
        'description': 'Modelo de embeddings',
        'example': 'nomic-embed-text',
        'critical': True
    },
    'LLM_MODEL': {
        'description': 'Modelo de linguagem',
        'example': 'llama3.1:8b-instruct-q8_0',
        'critical': True
    },

    # Segurança
    'JWT_SECRET_KEY': {
        'description': 'Secret para tokens JWT',
        'example': 'long_random_string_64_chars',
        'critical': True,
        'check_placeholder': True
    },
    'JWT_REFRESH_SECRET': {
        'description': 'Secret para refresh tokens',
        'example': 'another_long_random_string',
        'critical': True,
        'check_placeholder': True
    },
    'JWT_ALGORITHM': {
        'description': 'Algoritmo JWT',
        'example': 'HS256',
        'critical': True
    },

    # API
    'API_HOST': {
        'description': 'Host da API',
        'example': '0.0.0.0',
        'critical': True
    },
    'API_PORT': {
        'description': 'Porta da API',
        'example': '8000',
        'critical': True
    },

    # Ambiente
    'ENVIRONMENT': {
        'description': 'Ambiente de execução',
        'example': 'production',
        'critical': True
    },
    'LOG_LEVEL': {
        'description': 'Nível de log',
        'example': 'INFO',
        'critical': True
    },
}

# Valores inseguros que não devem ser usados em produção
INSECURE_VALUES = [
    'changeme',
    'password',
    'secret',
    'your-secret-key-here',
    'change-in-production',
    'example',
    'test',
    '123456'
]

def load_env_file(env_path: Path) -> Dict[str, str]:
    """Carrega variáveis do arquivo .env"""
    env_vars = {}

    if not env_path.exists():
        print_error(f"Arquivo .env não encontrado: {env_path}")
        return env_vars

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars

def check_insecure_value(var_name: str, value: str) -> bool:
    """Verifica se o valor é inseguro"""
    value_lower = value.lower()
    for insecure in INSECURE_VALUES:
        if insecure in value_lower:
            return True
    return False

def validate_jwt_secret(value: str) -> Tuple[bool, str]:
    """Valida a qualidade do JWT secret"""
    if len(value) < 32:
        return False, "JWT secret deve ter pelo menos 32 caracteres"

    if check_insecure_value('JWT_SECRET', value):
        return False, "JWT secret contém valor inseguro/placeholder"

    return True, "OK"

def validate_environment() -> Tuple[bool, List[str], List[str]]:
    """
    Valida todas as variáveis de ambiente
    Retorna: (sucesso, erros, avisos)
    """
    print_header("VALIDAÇÃO DE VARIÁVEIS DE AMBIENTE - DEPLOY P0")

    # Carregar .env
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'

    print_info(f"Carregando variáveis de: {env_path}")
    env_vars = load_env_file(env_path)

    if not env_vars:
        return False, ["Falha ao carregar arquivo .env"], []

    print_success(f"Arquivo .env carregado ({len(env_vars)} variáveis encontradas)\n")

    # Validar variáveis
    errors = []
    warnings = []
    success_count = 0

    print_header("VALIDAÇÃO DE VARIÁVEIS OBRIGATÓRIAS")

    for var_name, config in REQUIRED_VARS.items():
        desc = config['description']
        critical = config.get('critical', False)

        if var_name not in env_vars:
            msg = f"{var_name}: AUSENTE - {desc}"
            if critical:
                errors.append(msg)
                print_error(msg)
            else:
                warnings.append(msg)
                print_warning(msg)
            continue

        value = env_vars[var_name]

        if not value:
            msg = f"{var_name}: VAZIO - {desc}"
            if critical:
                errors.append(msg)
                print_error(msg)
            else:
                warnings.append(msg)
                print_warning(msg)
            continue

        # Validações especiais
        if config.get('check_placeholder'):
            if 'JWT' in var_name:
                valid, msg = validate_jwt_secret(value)
                if not valid:
                    errors.append(f"{var_name}: {msg}")
                    print_error(f"{var_name}: {msg}")
                    continue

        # Sucesso
        # Mascarar valores sensíveis no output
        display_value = value
        if any(x in var_name.upper() for x in ['SECRET', 'PASSWORD', 'KEY']):
            display_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'

        print_success(f"{var_name}: OK ({display_value})")
        success_count += 1

    # Resumo
    print_header("RESUMO DA VALIDAÇÃO")

    total_vars = len(REQUIRED_VARS)
    print(f"\n{BLUE}Variáveis validadas:{RESET} {success_count}/{total_vars}")

    if errors:
        print(f"\n{RED}Erros criticos:{RESET} {len(errors)}")
        for error in errors:
            print(f"  {RED}-{RESET} {error}")

    if warnings:
        print(f"\n{YELLOW}Avisos:{RESET} {len(warnings)}")
        for warning in warnings:
            print(f"  {YELLOW}-{RESET} {warning}")

    # Resultado final
    print()
    if errors:
        print_error("VALIDAÇÃO FALHOU - Corrija os erros críticos antes de prosseguir")
        return False, errors, warnings
    elif warnings:
        print_warning("VALIDAÇÃO PASSOU COM AVISOS - Revise os avisos")
        return True, errors, warnings
    else:
        print_success("VALIDAÇÃO PASSOU - Ambiente configurado corretamente")
        return True, errors, warnings

def main():
    """Função principal"""
    try:
        success, errors, warnings = validate_environment()

        # Exit code
        if not success:
            sys.exit(1)
        elif warnings:
            sys.exit(0)  # Avisos não bloqueiam
        else:
            sys.exit(0)

    except Exception as e:
        print_error(f"Erro durante validação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
