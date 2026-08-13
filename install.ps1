$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   StayAwake PC - Dependency Installer" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Python not found! Please install Python 3.12 or later." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "Python detected. Installing required libraries..." -ForegroundColor Yellow

if (Test-Path (Join-Path $PSScriptRoot "venv\Scripts\python.exe")) {
    Write-Host "The existing virtual environment is being used..." -ForegroundColor Yellow
} else {
    Write-Host "Creating a new virtual environment venv..." -ForegroundColor Yellow
    python -m venv (Join-Path $PSScriptRoot "venv")
}

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n===================================================" -ForegroundColor Green
    Write-Host "[SUCCESS] All dependencies installed successfully!" -ForegroundColor Green
    Write-Host "Launching run.ps1 automatically..." -ForegroundColor Green
    Write-Host "===================================================" -ForegroundColor Green
    Start-Process powershell.exe -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $PSScriptRoot "run.ps1")) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
    [System.Environment]::Exit(0)
} else {
    Write-Host "`n[ERROR] An error occurred during library installation." -ForegroundColor Red
    Read-Host "Press Enter to continue..."
    [System.Environment]::Exit(1)
}
