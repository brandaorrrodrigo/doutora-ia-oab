#!/usr/bin/env python3
"""Script de inicialização para produção (Railway)"""
import os
import sys
import traceback

print("=" * 80)
print("JURIS IA - Inicialização")
print("=" * 80)

# Adicionar diretórios ao PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT_DIR, "api")
sys.path.insert(0, API_DIR)
sys.path.insert(1, ROOT_DIR)

print(f"📂 ROOT_DIR: {ROOT_DIR}")
print(f"📂 API_DIR: {API_DIR}")
print(f"🐍 Python: {sys.version}")
print(f"📍 sys.path: {sys.path[:3]}")

# Ler porta do ambiente
port_str = os.getenv("PORT", "8000")
print(f"🔌 PORT env var: {port_str}")

try:
    port = int(port_str)
    print(f"✅ Porta convertida: {port}")
except ValueError as e:
    print(f"❌ Erro ao converter PORT: {e}")
    print(f"Usando porta padrão 8000")
    port = 8000

# Testar importação do app
print("\n📦 Testando importação do módulo api.main...")
try:
    from api.main import app
    print("✅ app importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar app: {e}")
    traceback.print_exc()
    sys.exit(1)

# Iniciar uvicorn
print(f"\n🚀 Iniciando uvicorn em 0.0.0.0:{port}")
print("=" * 80)

try:
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
except Exception as e:
    print(f"❌ Erro ao iniciar uvicorn: {e}")
    traceback.print_exc()
    sys.exit(1)
