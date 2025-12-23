# ================================================================================
# SCRIPT DE CORREÇÃO - DOCKER DESKTOP ERRO 500
# ================================================================================
# Este script automatiza a correção do Docker Desktop
# EXECUTAR COMO ADMINISTRADOR
# ================================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "CORREÇÃO AUTOMÁTICA - DOCKER DESKTOP" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

# ================================================================================
# PASSO 1: PARAR DOCKER DESKTOP
# ================================================================================
Write-Host "[1/7] Parando Docker Desktop..." -ForegroundColor Yellow
Get-Process "*docker*" | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 5
Write-Host "OK - Docker Desktop parado" -ForegroundColor Green
Write-Host ""

# ================================================================================
# PASSO 2: PARAR WSL2
# ================================================================================
Write-Host "[2/7] Parando WSL2..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 5
Write-Host "OK - WSL2 parado" -ForegroundColor Green
Write-Host ""

# ================================================================================
# PASSO 3: LIMPAR CACHES E DADOS TEMPORÁRIOS
# ================================================================================
Write-Host "[3/7] Limpando caches do Docker..." -ForegroundColor Yellow

$paths = @(
    "$env:APPDATA\Docker",
    "$env:LOCALAPPDATA\Docker\log",
    "$env:TEMP\docker*"
)

foreach ($path in $paths) {
    if (Test-Path $path) {
        Write-Host "  - Limpando: $path"
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "OK - Caches limpos" -ForegroundColor Green
Write-Host ""

# ================================================================================
# PASSO 4: LIMPAR CONTAINERS E VOLUMES ÓRFÃOS (se Docker responder)
# ================================================================================
Write-Host "[4/7] Tentando limpar containers órfãos..." -ForegroundColor Yellow

# Tentar via WSL2 direto
try {
    wsl docker ps -aq 2>$null | ForEach-Object { wsl docker rm -f $_ 2>$null }
    wsl docker volume prune -f 2>$null
    wsl docker network prune -f 2>$null
    Write-Host "OK - Containers e volumes limpos via WSL" -ForegroundColor Green
} catch {
    Write-Host "AVISO - Não foi possível limpar via WSL (normal se Docker não estava rodando)" -ForegroundColor Yellow
}
Write-Host ""

# ================================================================================
# PASSO 5: REINICIAR WSL2
# ================================================================================
Write-Host "[5/7] Reiniciando WSL2..." -ForegroundColor Yellow
wsl --shutdown
Start-Sleep -Seconds 3
# Forçar start do WSL2
wsl echo "WSL2 iniciado" | Out-Null
Start-Sleep -Seconds 5
Write-Host "OK - WSL2 reiniciado" -ForegroundColor Green
Write-Host ""

# ================================================================================
# PASSO 6: INICIAR DOCKER DESKTOP
# ================================================================================
Write-Host "[6/7] Iniciando Docker Desktop..." -ForegroundColor Yellow
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
Write-Host "Aguardando Docker Desktop inicializar (90 segundos)..." -ForegroundColor Yellow

# Aguardar até 90 segundos
$timeout = 90
$elapsed = 0
$dockerReady = $false

while ($elapsed -lt $timeout -and -not $dockerReady) {
    Start-Sleep -Seconds 5
    $elapsed += 5

    # Testar se Docker responde
    $result = docker ps 2>&1
    if ($result -notmatch "error" -and $result -notmatch "500") {
        $dockerReady = $true
        Write-Host "OK - Docker Desktop iniciado em $elapsed segundos" -ForegroundColor Green
    } else {
        Write-Host "  Aguardando... ($elapsed/$timeout s)" -ForegroundColor Gray
    }
}

if (-not $dockerReady) {
    Write-Host "AVISO - Docker pode não ter inicializado completamente" -ForegroundColor Yellow
    Write-Host "        Aguarde mais 30 segundos e execute: docker ps" -ForegroundColor Yellow
}
Write-Host ""

# ================================================================================
# PASSO 7: VALIDAR DOCKER
# ================================================================================
Write-Host "[7/7] Validando Docker..." -ForegroundColor Yellow

$dockerVersion = docker version 2>&1
if ($dockerVersion -match "Server:") {
    Write-Host "OK - Docker Server respondendo" -ForegroundColor Green

    # Mostrar versão
    docker version | Select-String -Pattern "Version:" | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }

    # Testar docker ps
    Write-Host ""
    Write-Host "Testando 'docker ps'..." -ForegroundColor Yellow
    docker ps

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "SUCESSO - DOCKER DESKTOP CORRIGIDO!" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Próximos passos:" -ForegroundColor Cyan
        Write-Host "1. Voltar para o deploy: cd D:\JURIS_IA_CORE_V1" -ForegroundColor White
        Write-Host "2. Subir containers: docker-compose up -d postgres redis ollama" -ForegroundColor White
        Write-Host "3. Continuar deploy P0" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "ERRO - 'docker ps' ainda falha" -ForegroundColor Red
        Write-Host "Executar solução AVANÇADA (reinstalação)" -ForegroundColor Red
    }

} else {
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "FALHA - DOCKER NÃO RESPONDEU" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "SOLUÇÕES ALTERNATIVAS:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OPÇÃO A - Reinstalar Docker Desktop:" -ForegroundColor Cyan
    Write-Host "  1. Desinstalar via Painel de Controle" -ForegroundColor White
    Write-Host "  2. Reiniciar Windows" -ForegroundColor White
    Write-Host "  3. Baixar versão LTS: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
    Write-Host "  4. Instalar e reiniciar" -ForegroundColor White
    Write-Host ""
    Write-Host "OPÇÃO B - Downgrade para versão estável:" -ForegroundColor Cyan
    Write-Host "  1. Desinstalar Docker Desktop 28.4.0" -ForegroundColor White
    Write-Host "  2. Baixar versão 27.x de: https://docs.docker.com/desktop/release-notes/" -ForegroundColor White
    Write-Host "  3. Instalar versão antiga" -ForegroundColor White
    Write-Host ""
    Write-Host "OPÇÃO C - Docker via WSL2 nativo (sem Desktop):" -ForegroundColor Cyan
    Write-Host "  Execute: .\INSTALAR_DOCKER_WSL2.ps1" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "Script finalizado em: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""
