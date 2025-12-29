"""
Script de Teste de Integração - Doutora IA OAB
Testa fluxo completo: Registro → Login → Questões
"""

import requests
import json
from datetime import datetime

# Configuração
BASE_URL = "http://localhost:8000"

def print_result(title, result):
    """Imprime resultado formatado"""
    print(f"\n{'='*60}")
    print(f"[INFO] {title}")
    print(f"{'='*60}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def test_health():
    """Testa endpoint de health"""
    print("\n[TEST] Testando Health Check...")
    response = requests.get(f"{BASE_URL}/health")
    print_result("Health Check", response.json())
    return response.status_code == 200


def test_root():
    """Testa endpoint raiz"""
    print("\n[TEST] Testando Root Endpoint...")
    response = requests.get(f"{BASE_URL}/")
    result = response.json()
    print_result("Root Info", result)
    return response.status_code == 200


def test_stats():
    """Testa estatísticas do banco"""
    print("\n[TEST] Testando Database Stats...")
    try:
        response = requests.get(f"{BASE_URL}/admin/stats")
        if response.status_code == 200:
            result = response.json()
            print_result("Database Stats", result)
            return True
        else:
            print(f"[ERROR] Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Erro ao acessar stats: {e}")
        return False


def test_register():
    """Testa registro de novo usuário"""
    print("\n[TEST] Testando Registro de Usuario...")

    test_user = {
        "nome": f"Teste User {datetime.now().strftime('%H%M%S')}",
        "email": f"teste{datetime.now().strftime('%H%M%S')}@example.com",
        "senha": "senha123",
        "cpf": None,
        "telefone": None
    }

    try:
        response = requests.post(
            f"{BASE_URL}/admin/register",
            json=test_user,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 201:
            result = response.json()
            print_result("Registro Bem-Sucedido", result)
            return result
        else:
            print(f" Erro: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f" Erro ao registrar: {e}")
        return None


def test_login(email, senha):
    """Testa login"""
    print("\n Testando Login...")

    try:
        response = requests.post(
            f"{BASE_URL}/admin/login",
            json={"email": email, "senha": senha},
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print_result("Login Bem-Sucedido", result)
            return result
        else:
            print(f" Erro: Status {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f" Erro ao fazer login: {e}")
        return None


def run_full_test():
    """Executa teste completo do fluxo"""
    print("\n" + "="*60)
    print(" INICIANDO TESTES DE INTEGRAÇÃO")
    print("="*60)

    results = {
        "health": False,
        "root": False,
        "stats": False,
        "register": False,
        "login": False
    }

    # 1. Health Check
    results["health"] = test_health()

    # 2. Root Endpoint
    results["root"] = test_root()

    # 3. Database Stats
    results["stats"] = test_stats()

    # 4. Registro
    register_result = test_register()
    if register_result and register_result.get("success"):
        results["register"] = True

        # Extrair dados do usuário registrado
        user_data = register_result.get("data", {})
        token = user_data.get("token")
        user_info = user_data.get("user", {})
        email = user_info.get("email")

        # 5. Login (testar com usuário recém-criado)
        if email:
            # Para login, precisamos da senha que foi usada no registro
            # Como geramos dinamicamente, vamos usar a senha padrão
            login_result = test_login(email, "senha123")
            if login_result and login_result.get("success"):
                results["login"] = True

    # Resumo
    print("\n" + "="*60)
    print(" RESUMO DOS TESTES")
    print("="*60)

    for test_name, passed in results.items():
        status = " PASSOU" if passed else " FALHOU"
        print(f"{test_name.upper():20s} {status}")

    total = len(results)
    passed = sum(results.values())

    print("\n" + "="*60)
    print(f"Total: {passed}/{total} testes passaram")
    print(f"Taxa de sucesso: {(passed/total)*100:.1f}%")
    print("="*60)

    return results


if __name__ == "__main__":
    run_full_test()
