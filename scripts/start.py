#!/usr/bin/env python3
"""Script de inicialização para produção (Railway)"""
import os
import sys
import uvicorn

# Adicionar diretórios ao PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(ROOT_DIR, "api")
sys.path.insert(0, API_DIR)
sys.path.insert(1, ROOT_DIR)

# Ler porta do ambiente (Railway injeta PORT automaticamente)
port = int(os.getenv("PORT", "8000"))

print(f"🚀 Iniciando JURIS IA API na porta {port}...")
print(f"📂 ROOT_DIR: {ROOT_DIR}")
print(f"📂 API_DIR: {API_DIR}")

# Iniciar uvicorn programaticamente
uvicorn.run(
    "api.main:app",
    host="0.0.0.0",
    port=port,
    log_level="info",
    access_log=True
)
