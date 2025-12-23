# ================================================================================
# SCRIPT DE ESPERA E VALIDAÇÃO - DOCKER DESKTOP
# DOUTORA IA/OAB - JURIS_IA_CORE_V1
# ================================================================================
# Uso: powershell -ExecutionPolicy Bypass -File scripts\wait_for_docker.ps1
# Descrição: Aguarda Docker Desktop ficar pronto e oferece iniciar deploy
# ================================================================================

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "DEPLOY CONTROLADO P0 - DOUTORA IA/OAB" -ForegroundColor Cyan
Write-Host "Validação de Docker Desktop" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$MAX_ATTEMPTS = 60  # 60 tentativas = 2 minutos
$ATTEMPT = 0
$DOCKER_READY = $false

Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Verificando Docker Desktop..." -ForegroundColor Yellow

while ($ATTEMPT -lt $MAX_ATTEMPTS) {
    $ATTEMPT++

    # Tentar executar docker ps
    try {
        $null = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[$(Get-Date -Format 'HH:mm:ss')] ✓ Docker Desktop está pronto!" -ForegroundColor Green
            $DOCKER_READY = $true
            break
        }
    }
    catch {
        # Ignora erro e tenta novamente
    }

    # Mostrar progresso
    Write-Host "." -NoNewline
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host ""

if (-not $DOCKER_READY) {
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host "ERRO: Docker Desktop não inicializou em 2 minutos" -ForegroundColor Red
    Write-Host "================================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Ações sugeridas:" -ForegroundColor Yellow
    Write-Host "  1. Verifique se Docker Desktop está instalado" -ForegroundColor White
    Write-Host "  2. Abra Docker Desktop manualmente" -ForegroundColor White
    Write-Host "  3. Aguarde até o ícone ficar verde" -ForegroundColor White
    Write-Host "  4. Execute este script novamente" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Docker está pronto - mostrar informações
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "Docker Desktop: PRONTO" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""

# Mostrar versão
Write-Host "Versão do Docker:" -ForegroundColor Cyan
docker version --format "{{.Server.Version}}"
Write-Host ""

# Mostrar containers existentes
Write-Host "Containers existentes:" -ForegroundColor Cyan
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

# Oferecer iniciar deploy
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "PRÓXIMA ETAPA: Inicialização de Serviços" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "O script vai inicializar:" -ForegroundColor White
Write-Host "  ✓ PostgreSQL + pgvector" -ForegroundColor White
Write-Host "  ✓ Redis (cache)" -ForegroundColor White
Write-Host "  ✓ Ollama (IA com GPU)" -ForegroundColor White
Write-Host "  ✓ Download de modelos IA (~10-20 minutos)" -ForegroundColor White
Write-Host ""
Write-Host "Tempo estimado: 10-20 minutos" -ForegroundColor Yellow
Write-Host ""

$response = Read-Host "Iniciar deploy automaticamente? (s/n)"

if ($response -eq "s" -or $response -eq "S") {
    Write-Host ""
    Write-Host "Iniciando deploy..." -ForegroundColor Green
    Write-Host ""

    # Executar script de inicialização
    bash scripts/deploy_p0_init.sh

    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host "ETAPA 13.1 CONCLUÍDA COM SUCESSO!" -ForegroundColor Green
        Write-Host "================================================================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Próximo passo:" -ForegroundColor Cyan
        Write-Host "  bash scripts/deploy_p0_migrations.sh" -ForegroundColor White
        Write-Host ""
    }
    else {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Red
        Write-Host "ERRO na inicialização" -ForegroundColor Red
        Write-Host "================================================================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Verifique os logs em: LOGS_DEPLOY_P0.txt" -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}
else {
    Write-Host ""
    Write-Host "Deploy não iniciado." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Para iniciar manualmente:" -ForegroundColor Cyan
    Write-Host "  bash scripts/deploy_p0_init.sh" -ForegroundColor White
    Write-Host ""
}

# ================================================================================
# FIM
# ================================================================================
