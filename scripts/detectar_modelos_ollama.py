"""
================================================================================
SCRIPT: DETECTAR E CONFIGURAR MODELOS OLLAMA EXISTENTES
================================================================================
Objetivo: Usar modelos já instalados e facilitar instalação progressiva
Data: 2025-12-17
================================================================================

Este script:
1. Detecta modelos Ollama já instalados
2. Recomenda o melhor modelo disponível
3. Lista os 7 modelos recomendados para o sistema
4. Permite instalação incremental
5. Atualiza configuração automaticamente

================================================================================
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional
from pathlib import Path

# Cores para output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


# ================================================================================
# CONFIGURAÇÃO DOS 7 MODELOS RECOMENDADOS
# ================================================================================

MODELOS_SISTEMA = {
    # EMBEDDINGS (escolher 1)
    "embeddings": [
        {
            "nome": "nomic-embed-text",
            "tipo": "embedding",
            "dimensoes": 768,
            "tamanho_gb": 1.5,
            "prioridade": 1,
            "descricao": "Melhor embedding para português jurídico"
        },
        {
            "nome": "mxbai-embed-large",
            "tipo": "embedding",
            "dimensoes": 1024,
            "tamanho_gb": 0.67,
            "prioridade": 2,
            "descricao": "Alternativa rápida e eficiente"
        },
        {
            "nome": "all-minilm",
            "tipo": "embedding",
            "dimensoes": 384,
            "tamanho_gb": 0.12,
            "prioridade": 3,
            "descricao": "Mais leve, para testes rápidos"
        }
    ],

    # LLM PRINCIPAL (escolher 1)
    "llm_principal": [
        {
            "nome": "llama3.2:3b",
            "tipo": "llm",
            "parametros": "3B",
            "tamanho_gb": 2.0,
            "prioridade": 3,
            "descricao": "Rápido, bom para começar",
            "tokens_por_seg_rtx3090": "150-200"
        },
        {
            "nome": "llama3.1:8b",
            "tipo": "llm",
            "parametros": "8B",
            "tamanho_gb": 4.7,
            "prioridade": 1,
            "descricao": "Melhor custo-benefício (RECOMENDADO)",
            "tokens_por_seg_rtx3090": "100-150"
        },
        {
            "nome": "llama3:70b-q4_K_M",
            "tipo": "llm",
            "parametros": "70B",
            "tamanho_gb": 40,
            "prioridade": 2,
            "descricao": "Máxima qualidade (requer 24GB VRAM)",
            "tokens_por_seg_rtx3090": "30-50"
        }
    ],

    # MODELOS ESPECIALIZADOS (opcional)
    "especializados": [
        {
            "nome": "llama3.1:8b-instruct-q8_0",
            "tipo": "llm_instruct",
            "parametros": "8B",
            "tamanho_gb": 8.5,
            "prioridade": 1,
            "descricao": "Versão instruída do 8B, melhor para explicações",
            "tokens_por_seg_rtx3090": "80-120"
        },
        {
            "nome": "codellama:13b",
            "tipo": "llm_code",
            "parametros": "13B",
            "tamanho_gb": 7.3,
            "prioridade": 2,
            "descricao": "Especializado em código (opcional)",
            "tokens_por_seg_rtx3090": "60-90"
        }
    ]
}


def verificar_ollama_disponivel(host: str = "http://localhost:11434") -> bool:
    """Verifica se Ollama está rodando."""
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def listar_modelos_instalados(host: str = "http://localhost:11434") -> List[Dict]:
    """Lista modelos já instalados no Ollama."""
    try:
        response = requests.get(f"{host}/api/tags", timeout=5)
        if response.status_code == 200:
            modelos = response.json().get("models", [])
            return [
                {
                    "nome": m["name"],
                    "tamanho_bytes": m.get("size", 0),
                    "tamanho_gb": m.get("size", 0) / (1024**3),
                    "modificado": m.get("modified_at", "")
                }
                for m in modelos
            ]
        return []
    except:
        return []


def detectar_tipo_modelo(nome_modelo: str) -> Optional[str]:
    """Detecta tipo do modelo pelo nome."""
    nome_lower = nome_modelo.lower()

    if "embed" in nome_lower:
        return "embedding"
    elif "code" in nome_lower:
        return "llm_code"
    elif "instruct" in nome_lower:
        return "llm_instruct"
    elif "llama" in nome_lower or "mistral" in nome_lower:
        return "llm"

    return None


def recomendar_modelos(
    modelos_instalados: List[Dict],
    rtx_3090: bool = True
) -> Dict:
    """
    Recomenda modelos baseado no que já está instalado.

    Returns:
        Dict com recomendações organizadas
    """
    # Extrair nomes dos modelos instalados
    nomes_instalados = [m["nome"].split(":")[0] for m in modelos_instalados]

    recomendacoes = {
        "usar_agora": [],
        "instalar_proximos": [],
        "instalar_depois": []
    }

    # Verificar embeddings
    embedding_encontrado = False
    for config in MODELOS_SISTEMA["embeddings"]:
        if any(config["nome"] in nome for nome in nomes_instalados):
            embedding_encontrado = True
            recomendacoes["usar_agora"].append({
                **config,
                "categoria": "Embedding",
                "instalado": True
            })
            break

    if not embedding_encontrado:
        # Recomendar o de maior prioridade
        melhor = min(MODELOS_SISTEMA["embeddings"], key=lambda x: x["prioridade"])
        recomendacoes["instalar_proximos"].append({
            **melhor,
            "categoria": "Embedding",
            "instalado": False
        })

    # Verificar LLM principal
    llm_encontrado = False
    for config in MODELOS_SISTEMA["llm_principal"]:
        nome_base = config["nome"].split(":")[0]
        if any(nome_base in nome for nome in nomes_instalados):
            llm_encontrado = True
            recomendacoes["usar_agora"].append({
                **config,
                "categoria": "LLM Principal",
                "instalado": True
            })
            break

    if not llm_encontrado:
        # Recomendar baseado em RTX 3090
        if rtx_3090:
            # Recomendar 8B instruct
            melhor = next(
                (m for m in MODELOS_SISTEMA["llm_principal"]
                 if m["nome"] == "llama3.1:8b"),
                MODELOS_SISTEMA["llm_principal"][0]
            )
        else:
            # Recomendar 3B para GPUs menores
            melhor = MODELOS_SISTEMA["llm_principal"][-1]

        recomendacoes["instalar_proximos"].append({
            **melhor,
            "categoria": "LLM Principal",
            "instalado": False
        })

    # Modelos especializados (opcional)
    for config in MODELOS_SISTEMA["especializados"]:
        nome_base = config["nome"].split(":")[0]
        if any(nome_base in nome for nome in nomes_instalados):
            recomendacoes["usar_agora"].append({
                **config,
                "categoria": "Especializado",
                "instalado": True
            })
        else:
            recomendacoes["instalar_depois"].append({
                **config,
                "categoria": "Especializado",
                "instalado": False
            })

    return recomendacoes


def gerar_config_automatica(recomendacoes: Dict) -> Dict:
    """Gera configuração automática baseado em modelos disponíveis."""
    config = {
        "EMBEDDING_MODEL": None,
        "LLM_MODEL": None,
        "LLM_INSTRUCT_MODEL": None
    }

    for modelo in recomendacoes["usar_agora"]:
        if modelo["tipo"] == "embedding":
            config["EMBEDDING_MODEL"] = modelo["nome"]
        elif modelo["tipo"] == "llm":
            config["LLM_MODEL"] = modelo["nome"]
        elif modelo["tipo"] == "llm_instruct":
            config["LLM_INSTRUCT_MODEL"] = modelo["nome"]

    return config


def atualizar_env_file(config: Dict, env_path: str = ".env") -> bool:
    """Atualiza arquivo .env com configurações detectadas."""
    try:
        env_file = Path(env_path)

        if env_file.exists():
            # Ler conteúdo atual
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        else:
            lines = []

        # Atualizar ou adicionar variáveis
        vars_atualizadas = set()
        new_lines = []

        for line in lines:
            atualizado = False
            for key, value in config.items():
                if value and line.startswith(f"{key}="):
                    new_lines.append(f"{key}={value}\n")
                    vars_atualizadas.add(key)
                    atualizado = True
                    break

            if not atualizado:
                new_lines.append(line)

        # Adicionar variáveis que não existiam
        for key, value in config.items():
            if value and key not in vars_atualizadas:
                new_lines.append(f"\n# Auto-configurado\n{key}={value}\n")

        # Salvar
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        return True

    except Exception as e:
        print(f"{RED}Erro ao atualizar .env: {e}{RESET}")
        return False


def exibir_relatorio(
    modelos_instalados: List[Dict],
    recomendacoes: Dict,
    config: Dict
):
    """Exibe relatório completo."""
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}RELATÓRIO: MODELOS OLLAMA PARA JURIS_IA{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    # Modelos instalados
    print(f"{GREEN}📦 MODELOS JÁ INSTALADOS:{RESET}")
    if modelos_instalados:
        for modelo in modelos_instalados:
            print(f"  ✓ {modelo['nome']} ({modelo['tamanho_gb']:.2f} GB)")
    else:
        print(f"  {YELLOW}Nenhum modelo instalado ainda{RESET}")

    print()

    # Usar agora
    if recomendacoes["usar_agora"]:
        print(f"{GREEN}✅ USAR AGORA (já instalados):{RESET}")
        for modelo in recomendacoes["usar_agora"]:
            print(f"  • {modelo['categoria']}: {GREEN}{modelo['nome']}{RESET}")
            print(f"    {modelo['descricao']}")
            if modelo.get('tokens_por_seg_rtx3090'):
                print(f"    Performance RTX 3090: {modelo['tokens_por_seg_rtx3090']} tokens/seg")
        print()

    # Instalar próximos (prioridade)
    if recomendacoes["instalar_proximos"]:
        print(f"{YELLOW}🔥 INSTALAR PRÓXIMOS (prioridade):{RESET}")
        for i, modelo in enumerate(recomendacoes["instalar_proximos"], 1):
            print(f"\n  {i}. {modelo['categoria']}: {YELLOW}{modelo['nome']}{RESET}")
            print(f"     {modelo['descricao']}")
            print(f"     Tamanho: {modelo['tamanho_gb']} GB")
            if modelo.get('tokens_por_seg_rtx3090'):
                print(f"     Performance RTX 3090: {modelo['tokens_por_seg_rtx3090']} tokens/seg")
            print(f"     Comando: {BLUE}ollama pull {modelo['nome']}{RESET}")
        print()

    # Instalar depois (opcional)
    if recomendacoes["instalar_depois"]:
        print(f"{BLUE}💡 INSTALAR DEPOIS (opcional, para escalar):{RESET}")
        for i, modelo in enumerate(recomendacoes["instalar_depois"], 1):
            print(f"\n  {i}. {modelo['categoria']}: {modelo['nome']}")
            print(f"     {modelo['descricao']}")
            print(f"     Tamanho: {modelo['tamanho_gb']} GB")
            if modelo.get('tokens_por_seg_rtx3090'):
                print(f"     Performance RTX 3090: {modelo['tokens_por_seg_rtx3090']} tokens/seg")
        print()

    # Configuração gerada
    print(f"{GREEN}⚙️  CONFIGURAÇÃO AUTO-DETECTADA:{RESET}")
    for key, value in config.items():
        if value:
            print(f"  {key}={GREEN}{value}{RESET}")
        else:
            print(f"  {key}={RED}(não configurado){RESET}")

    print(f"\n{BLUE}{'='*80}{RESET}\n")


def main():
    """Função principal."""
    print(f"{GREEN}Detectando modelos Ollama...{RESET}\n")

    # Verificar Ollama
    if not verificar_ollama_disponivel():
        print(f"{RED}✗ Ollama não está rodando!{RESET}")
        print(f"\nPara iniciar:")
        print(f"  Windows: ollama serve")
        print(f"  Linux: systemctl start ollama")
        print(f"  Docker: docker-compose up -d ollama")
        sys.exit(1)

    print(f"{GREEN}✓ Ollama rodando{RESET}\n")

    # Listar modelos instalados
    modelos_instalados = listar_modelos_instalados()

    # Recomendar modelos
    recomendacoes = recomendar_modelos(modelos_instalados, rtx_3090=True)

    # Gerar configuração
    config = gerar_config_automatica(recomendacoes)

    # Exibir relatório
    exibir_relatorio(modelos_instalados, recomendacoes, config)

    # Perguntar se quer atualizar .env
    if any(config.values()):
        resposta = input(f"Deseja atualizar o arquivo .env com esta configuração? (s/n): ")
        if resposta.lower() == 's':
            if atualizar_env_file(config):
                print(f"\n{GREEN}✓ Arquivo .env atualizado com sucesso!{RESET}")
            else:
                print(f"\n{RED}✗ Erro ao atualizar .env{RESET}")
        else:
            print(f"\n{YELLOW}Configuração não salva. Para salvar manualmente:{RESET}")
            for key, value in config.items():
                if value:
                    print(f"  {key}={value}")

    # Comandos de instalação
    if recomendacoes["instalar_proximos"]:
        print(f"\n{YELLOW}PRÓXIMOS PASSOS:{RESET}")
        print(f"\n1. Instalar modelos prioritários:")
        for modelo in recomendacoes["instalar_proximos"]:
            print(f"   ollama pull {modelo['nome']}")

        print(f"\n2. Executar este script novamente para atualizar configuração:")
        print(f"   python scripts/detectar_modelos_ollama.py")

        print(f"\n3. Popular embeddings:")
        print(f"   python scripts/popular_embeddings_ollama.py")


if __name__ == "__main__":
    main()
