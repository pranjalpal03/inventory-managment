# Configure MongoDB Atlas URI locally and print Render environment values.
param(
    [Parameter(Mandatory = $true)]
    [string]$MongoUri,

    [string]$EnvFile = ".env.production"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "Testing MongoDB connection..." -ForegroundColor Cyan
$env:MONGODB_URI = $MongoUri
py scripts/test-mongodb-uri.py $MongoUri
if ($LASTEXITCODE -ne 0) {
    Write-Host "Connection test failed. Fix Atlas credentials before deploying." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    Copy-Item ".env.production.example" $EnvFile
}

$content = Get-Content $EnvFile -Raw
if ($content -match "(?m)^MONGODB_URI=.*$") {
    $content = $content -replace "(?m)^MONGODB_URI=.*$", "MONGODB_URI=$MongoUri"
} else {
    $content += "`nMONGODB_URI=$MongoUri`n"
}
Set-Content -Path $EnvFile -Value $content.TrimEnd() -NoNewline
Add-Content -Path $EnvFile -Value ""

Write-Host ""
Write-Host "Updated $EnvFile" -ForegroundColor Green
Write-Host ""
Write-Host "=== Paste these into Render → smart-inventory-api → Environment ===" -ForegroundColor Cyan

$vars = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') {
        $vars[$Matches[1]] = $Matches[2]
    }
}

@(
    "MONGODB_URI",
    "MONGODB_DB_NAME",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "JWT_EXPIRE_MINUTES",
    "DEMO_ADMIN_EMAIL",
    "DEMO_ADMIN_PASSWORD",
    "DEMO_ADMIN_NAME",
    "CORS_ORIGINS",
    "DEBUG",
    "SEED_DEMO_DATA",
    "SEED_DEMO_ADMIN"
) | ForEach-Object {
    if ($vars.ContainsKey($_)) {
        Write-Host "$_=$($vars[$_])"
    }
}

Write-Host ""
Write-Host "Then: Render → Manual Deploy → Deploy latest commit" -ForegroundColor Yellow
