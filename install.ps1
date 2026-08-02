Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -ErrorAction SilentlyContinue

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   StayAwake PC - Installer" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found! Please install Python 3.12+ and add it to the PATH." -ForegroundColor Red
    Read-Host "Devam etmek için Enter'a basın..."
    exit 1
}

Write-Host "Python detected. Checking virtual environment (venv)..." -ForegroundColor Yellow

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment (venv)..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Dependencies are being installed into the venv..." -ForegroundColor Green
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Installation complete! You can run the .\run.ps1 file to launch the application." -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] An error occurred during installation." -ForegroundColor Red
}

Read-Host "Press Enter to continue..."
