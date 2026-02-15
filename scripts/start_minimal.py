#!/usr/bin/env python3
"""Script de inicialização MÍNIMO para debug (Railway)"""
import os
from fastapi import FastAPI
import uvicorn

# App mínimo sem deps
app = FastAPI(title="JURIS IA Health Check")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "port": os.getenv("PORT", "?"),
        "message": "Container iniciado com sucesso"
    }

@app.get("/")
def root():
    return {"message": "JURIS IA API - Container OK"}

# Ler porta
port = int(os.getenv("PORT", "8000"))
print(f"🚀 Iniciando app mínimo na porta {port}")

# Iniciar
uvicorn.run(app, host="0.0.0.0", port=port)
