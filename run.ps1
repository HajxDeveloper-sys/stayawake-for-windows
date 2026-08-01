Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -ErrorAction SilentlyContinue

Write-Host "StayAwake PC Başlatılıyor..." -ForegroundColor Green

if (Test-Path "venv\Scripts\pythonw.exe") {
    Start-Process ".\venv\Scripts\pythonw.exe" -ArgumentList "main.py" -WindowStyle Hidden
} elseif (Test-Path "venv\Scripts\python.exe") {
    Start-Process ".\venv\Scripts\python.exe" -ArgumentList "main.py"
} else {
    Start-Process "pythonw.exe" -ArgumentList "main.py" -ErrorAction SilentlyContinue
}
