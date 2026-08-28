# EchoScape - one-command dev startup (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ECHOSCAPE - the `$0-budget spatial radar" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "[ERROR] Python not found. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# 2. Check Node
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) {
    Write-Host "[ERROR] Node.js not found. Install Node 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# 3. Backend venv + deps
if (-not (Test-Path "backend\.venv")) {
    Write-Host "[1/3] Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv backend\.venv
}
Write-Host "[1/3] Installing backend dependencies..." -ForegroundColor Yellow
& backend\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt
if ($LASTEXITCODE -ne 0) { Write-Host "[ERROR] Backend install failed" -ForegroundColor Red; exit 1 }

# 4. Frontend deps
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "[2/3] Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location frontend
    npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { Pop-Location; Write-Host "[ERROR] Frontend install failed" -ForegroundColor Red; exit 1 }
    Pop-Location
} else {
    Write-Host "[2/3] Frontend dependencies found." -ForegroundColor Yellow
}

# 5. Start both processes
Write-Host "[3/3] Starting EchoScape..." -ForegroundColor Yellow
Write-Host "   - backend  : http://127.0.0.1:5001"
Write-Host "   - frontend : http://localhost:5173"
Write-Host "   - press Ctrl+C in this window to stop everything"
Write-Host ""

$backend = Start-Process -FilePath "backend\.venv\Scripts\python.exe" -ArgumentList "app.py" -WorkingDirectory (Join-Path (Get-Location) "backend") -PassThru -WindowStyle Hidden
try {
    Push-Location frontend
    npm run dev
    Pop-Location
} finally {
    if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
}
