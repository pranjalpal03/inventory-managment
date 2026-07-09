# Production deployment orchestrator
param(
    [ValidateSet("local", "docker", "cloud", "install-docker")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Test-EnvProduction {
    if (-not (Test-Path ".env.production")) {
        Copy-Item ".env.production.example" ".env.production"
        Write-Host "Created .env.production — fill MONGODB_URI before cloud deploy." -ForegroundColor Yellow
    }
    $envContent = Get-Content ".env.production" -Raw
    if ($envContent -match "REPLACE_ATLAS") {
        Write-Host "WARNING: MONGODB_URI still contains placeholders. Update .env.production for cloud." -ForegroundColor Yellow
    }
}

function Install-DockerDesktop {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        Write-Host "Docker already installed: $(docker --version)" -ForegroundColor Green
        return
    }
    Write-Host "Installing Docker Desktop via winget (may take several minutes)..." -ForegroundColor Cyan
    winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
    Write-Host "Docker Desktop installed. Restart your PC, then re-run: .\deploy-production.ps1 -Mode docker" -ForegroundColor Yellow
}

function Start-LocalProduction {
    Test-EnvProduction
    $mongo = Get-Service MongoDB -ErrorAction SilentlyContinue
    if ($mongo -and $mongo.Status -ne "Running") { Start-Service MongoDB }

    # Override Atlas URI for local MongoDB when placeholders remain
    $env:MONGODB_URI = "mongodb://localhost:27017"
    Get-Content ".env.production" | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=(.*)$') { Set-Item -Path "env:$($Matches[1])" -Value $Matches[2] }
    }
    $env:MONGODB_URI = "mongodb://localhost:27017"

    Set-Location "$Root\frontend"
    if (-not (Test-Path node_modules)) { npm install }
    npm run build

    Set-Location "$Root\backend"
    Get-Process -Name "python","py" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*app.main*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue

    Start-Process py -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -WindowStyle Minimized
    Start-Sleep -Seconds 3

    Set-Location "$Root\frontend"
    Write-Host ""
    Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Green
    Write-Host "  API:       http://localhost:8000" -ForegroundColor Green
    Write-Host "  Admin:     admin@inventory.com (see .env.production for password)" -ForegroundColor Yellow
    .\node_modules\.bin\vite.cmd preview --port 3000 --host 0.0.0.0
}

function Start-DockerProduction {
    Test-EnvProduction
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Install-DockerDesktop
        return
    }
    docker compose --env-file .env.production up -d --build
    Write-Host ""
    Write-Host "  Dashboard: http://localhost" -ForegroundColor Green
    Write-Host "  Health:    http://localhost/api/health" -ForegroundColor Green
}

function Start-CloudDocker {
    Test-EnvProduction
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Install-DockerDesktop
        return
    }
    docker compose -f docker-compose.cloud.yml --env-file .env.production up -d --build
    Write-Host ""
    Write-Host "  Dashboard: http://localhost (Atlas-backed)" -ForegroundColor Green
}

switch ($Mode) {
    "install-docker" { Install-DockerDesktop }
    "local"          { Start-LocalProduction }
    "docker"         { Start-DockerProduction }
    "cloud"          { Start-CloudDocker }
}
