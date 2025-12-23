# ================================================================================
# SCRIPT DE INSTALAÇÃO - DOCKER ENGINE NO WSL2 (SEM DOCKER DESKTOP)
# ================================================================================
# Alternativa ao Docker Desktop para evitar bugs
# EXECUTAR COMO ADMINISTRADOR
# ================================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "INSTALAÇÃO DOCKER ENGINE - WSL2 NATIVO" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Esta opção instala Docker diretamente no WSL2, sem Docker Desktop." -ForegroundColor Yellow
Write-Host "Vantagens: Mais estável, sem bugs do Desktop" -ForegroundColor Green
Write-Host "Desvantagens: Sem GUI, configuração manual" -ForegroundColor Yellow
Write-Host ""

$confirm = Read-Host "Continuar? (s/n)"
if ($confirm -ne 's') {
    Write-Host "Instalação cancelada." -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "[1/5] Desinstalando Docker Desktop (se existir)..." -ForegroundColor Yellow

# Parar Docker Desktop
Get-Process "*docker*" | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5

# Tentar desinstalar
$dockerDesktop = Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -like "*Docker Desktop*" }
if ($dockerDesktop) {
    Write-Host "  Desinstalando Docker Desktop..." -ForegroundColor Gray
    $dockerDesktop.Uninstall() | Out-Null
    Write-Host "OK - Docker Desktop removido" -ForegroundColor Green
} else {
    Write-Host "OK - Docker Desktop não instalado" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/5] Parando WSL2..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 5
Write-Host "OK" -ForegroundColor Green

Write-Host ""
Write-Host "[3/5] Instalando Docker Engine no WSL2..." -ForegroundColor Yellow
Write-Host "  (Executando comandos dentro do Ubuntu WSL2)" -ForegroundColor Gray

# Script de instalação dentro do WSL2
$installScript = @'
#!/bin/bash
set -e

echo "=== Atualizando pacotes ==="
sudo apt-get update

echo "=== Removendo Docker antigo (se existir) ==="
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

echo "=== Instalando dependências ==="
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

echo "=== Adicionando repositório Docker ==="
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

echo "=== Instalando Docker Engine ==="
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== Configurando usuário ==="
sudo usermod -aG docker $USER

echo "=== Iniciando Docker ==="
sudo service docker start

echo "=== Testando instalação ==="
sudo docker run --rm hello-world

echo "=== Docker Engine instalado com sucesso! ==="
'@

# Salvar script temporário
$tempScript = "$env:TEMP\install_docker_wsl.sh"
$installScript | Out-File -FilePath $tempScript -Encoding UTF8

# Copiar para WSL e executar
wsl bash -c "dos2unix < /mnt/c/Users/$env:USERNAME/AppData/Local/Temp/install_docker_wsl.sh > /tmp/install_docker.sh && chmod +x /tmp/install_docker.sh && /tmp/install_docker.sh"

Write-Host "OK - Docker Engine instalado no WSL2" -ForegroundColor Green

Write-Host ""
Write-Host "[4/5] Configurando auto-start do Docker..." -ForegroundColor Yellow

# Adicionar ao .bashrc
wsl bash -c "echo '# Auto-start Docker' >> ~/.bashrc"
wsl bash -c "echo 'if ! service docker status > /dev/null 2>&1; then' >> ~/.bashrc"
wsl bash -c "echo '  sudo service docker start > /dev/null 2>&1' >> ~/.bashrc"
wsl bash -c "echo 'fi' >> ~/.bashrc"

Write-Host "OK - Auto-start configurado" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] Testando instalação..." -ForegroundColor Yellow

wsl bash -c "sudo service docker start"
Start-Sleep -Seconds 5

$dockerVersion = wsl bash -c "docker version"
if ($dockerVersion -match "Server:") {
    Write-Host "OK - Docker funcionando!" -ForegroundColor Green
    Write-Host ""
    wsl bash -c "docker version" | Select-String -Pattern "Version:" | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }
} else {
    Write-Host "ERRO - Docker não respondeu" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "SUCESSO - DOCKER ENGINE INSTALADO NO WSL2!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANTE - Como usar:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Para executar comandos Docker:" -ForegroundColor Yellow
Write-Host "   wsl docker ps" -ForegroundColor White
Write-Host "   wsl docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "2. Para entrar no WSL2:" -ForegroundColor Yellow
Write-Host "   wsl" -ForegroundColor White
Write-Host "   cd /mnt/d/JURIS_IA_CORE_V1" -ForegroundColor White
Write-Host "   docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "3. Continuar deploy P0:" -ForegroundColor Yellow
Write-Host "   wsl" -ForegroundColor White
Write-Host "   cd /mnt/d/JURIS_IA_CORE_V1" -ForegroundColor White
Write-Host "   docker-compose up -d postgres redis ollama" -ForegroundColor White
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
