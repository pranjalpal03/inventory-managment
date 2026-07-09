# Production deployment without Docker (Windows)
# API: http://localhost:8000  |  Dashboard: http://localhost:3000

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "==> Checking MongoDB..." -ForegroundColor Cyan
$mongo = Get-Service MongoDB -ErrorAction SilentlyContinue
if ($mongo -and $mongo.Status -ne "Running") {
    Start-Service MongoDB
    Write-Host "    Started MongoDB service"
}

Write-Host "==> Installing frontend dependencies..." -ForegroundColor Cyan
Set-Location "$Root\frontend"
if (-not (Test-Path node_modules)) { npm install }

Write-Host "==> Building frontend for production..." -ForegroundColor Cyan
npm run build

Write-Host "==> Starting backend (port 8000)..." -ForegroundColor Cyan
Set-Location "$Root\backend"
Start-Process py -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -WindowStyle Minimized

Start-Sleep -Seconds 3

Write-Host "==> Starting production frontend (port 3000)..." -ForegroundColor Cyan
Set-Location "$Root\frontend"
Write-Host ""
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor Green
Write-Host "  API:       http://localhost:8000" -ForegroundColor Green
Write-Host "  Login:     admin@inventory.com / admin123" -ForegroundColor Yellow
Write-Host ""
npm run preview
