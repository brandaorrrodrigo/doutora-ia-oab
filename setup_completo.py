"""
Setup Completo - Tenta todas as opções automaticamente
"""

import subprocess
import sys
import os

print("="*60)
print(" SETUP COMPLETO - JURIS_IA")
print("="*60)

# Opção 1: Tentar Docker
print("\n[Opção 1] Verificando Docker...")
try:
    result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ Docker encontrado!")
        print("\nSubindo PostgreSQL no Docker...")

        subprocess.run(["docker-compose", "up", "-d", "postgres"], check=True)
        print("✓ PostgreSQL rodando no Docker")

        print("\nAguardando PostgreSQL inicializar (15 segundos)...")
        import time
        time.sleep(15)

        print("\nCriando tabelas...")
        subprocess.run([sys.executable, "init_database.py"], check=True)

        print("\n" + "="*60)
        print(" SETUP COMPLETO!")
        print("="*60)
        print("\nRodando testes...")
        subprocess.run([sys.executable, "test_integration.py"])
        sys.exit(0)

except Exception as e:
    print(f"✗ Docker não disponível: {e}")

# Opção 2: Usar DATABASE_URL do Railway (se existir)
print("\n[Opção 2] Verificando Railway DATABASE_URL...")
railway_db = os.getenv("RAILWAY_DATABASE_URL")
if railway_db:
    print("✓ Railway DATABASE_URL encontrada!")

    # Atualizar .env.local
    with open(".env.local", "w") as f:
        f.write(f"DATABASE_URL={railway_db}\n")

    print("\nCriando tabelas no Railway...")
    subprocess.run([sys.executable, "init_database.py"], check=True)

    print("\nRodando testes...")
    subprocess.run([sys.executable, "test_integration.py"])
    sys.exit(0)
else:
    print("✗ Railway DATABASE_URL não encontrada")

# Opção 3: Instruções manuais
print("\n" + "="*60)
print(" SETUP MANUAL NECESSÁRIO")
print("="*60)
print("""
Nenhuma opção automática funcionou. Escolha uma das opções:

OPÇÃO A - Docker (Recomendado):
  1. Instale Docker Desktop: https://www.docker.com/products/docker-desktop
  2. Rode: docker-compose up -d postgres
  3. Rode: python init_database.py
  4. Rode: python test_integration.py

OPÇÃO B - Railway Database:
  1. Acesse Railway dashboard
  2. Copie a DATABASE_URL
  3. Cole no arquivo .env.local
  4. Rode: python init_database.py
  5. Rode: python test_integration.py

OPÇÃO C - PostgreSQL Local (Avançado):
  Problema: encoding UTF-8 incompatível
  Solução: Reconfigurar PostgreSQL com encoding correto

  OU criar banco manualmente com:
  1. Abra pgAdmin
  2. Crie database "juris_ia"
  3. Crie user "juris_ia_user" com senha "changeme123"
  4. Rode: python init_database.py
""")

print("\nQual opção você quer seguir?")
