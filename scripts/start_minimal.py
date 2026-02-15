#!/usr/bin/env python3
"""Script de inicialização MÍNIMO para debug (Railway)"""
import os
import sys

print("=" * 80, flush=True)
print("INICIANDO CONTAINER", flush=True)
print("=" * 80, flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"CWD: {os.getcwd()}", flush=True)
print(f"ENV PORT: {os.getenv('PORT', 'NÃO DEFINIDA')}", flush=True)
print("=" * 80, flush=True)

try:
    from fastapi import FastAPI
    print("✅ FastAPI importado", flush=True)
except Exception as e:
    print(f"❌ Erro ao importar FastAPI: {e}", flush=True)
    sys.exit(1)

try:
    import uvicorn
    print("✅ Uvicorn importado", flush=True)
except Exception as e:
    print(f"❌ Erro ao importar uvicorn: {e}", flush=True)
    sys.exit(1)

# App mínimo sem deps
app = FastAPI(title="JURIS IA Health Check")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "port": os.getenv("PORT", "não definida"),
        "message": "Container iniciado com sucesso"
    }

@app.get("/")
def root():
    return {"message": "JURIS IA API - Container OK", "port": os.getenv("PORT", "?")}

# Ler porta com fallback absoluto
port_str = os.getenv("PORT", "8000")
try:
    port = int(port_str)
    print(f"✅ Porta: {port}", flush=True)
except:
    port = 8000
    print(f"⚠️ Porta padrão: {port}", flush=True)

print(f"🚀 Iniciando uvicorn em 0.0.0.0:{port}", flush=True)
print("=" * 80, flush=True)

# Iniciar com try/except
try:
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="debug")
except Exception as e:
    print(f"❌ ERRO FATAL: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
