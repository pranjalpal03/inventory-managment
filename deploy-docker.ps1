# Docker Compose production deployment
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed. Install Docker Desktop or run deploy.ps1 for local production mode."
}

if (-not (Test-Path ".env.production")) {
    Copy-Item ".env.production.example" ".env.production"
    Write-Host "Created .env.production from example — update JWT_SECRET and passwords before public deploy." -ForegroundColor Yellow
}

docker compose --env-file .env.production up -d --build
Write-Host ""
Write-Host "Dashboard: http://localhost" -ForegroundColor Green
Write-Host "API docs:  http://localhost/api/docs (proxied via nginx)" -ForegroundColor Green
