# Verify production stack health
$ErrorActionPreference = "Continue"

Write-Host "=== Production Health Check ===" -ForegroundColor Cyan

$checks = @(
    @{ Name = "Local prod frontend"; Url = "http://localhost:3000" },
    @{ Name = "Docker frontend";    Url = "http://localhost" },
    @{ Name = "API health";         Url = "http://localhost:8000/api/health" },
    @{ Name = "Docker API proxy";   Url = "http://localhost/api/health" }
)

foreach ($check in $checks) {
    try {
        $r = Invoke-WebRequest -Uri $check.Url -UseBasicParsing -TimeoutSec 5
        Write-Host "[OK] $($check.Name) -> $($r.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "[--] $($check.Name) -> unavailable" -ForegroundColor DarkGray
    }
}

if (Test-Path ".env.production") {
    $env = Get-Content ".env.production" -Raw
    if ($env -match "REPLACE_ATLAS") {
        Write-Host "[!!] MONGODB_URI not configured for Atlas" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] MONGODB_URI configured" -ForegroundColor Green
    }
}

if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "[OK] Docker: $(docker --version)" -ForegroundColor Green
} else {
    Write-Host "[!!] Docker not installed" -ForegroundColor Yellow
}
