Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -ErrorAction SilentlyContinue

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "   StayAwake PC - Installer" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[HATA] Python bulunamadı! Lütfen Python 3.12+ kurup PATH'e ekleyin." -ForegroundColor Red
    Read-Host "Devam etmek için Enter'a basın..."
    exit 1
}

Write-Host "Python tespit edildi. Sanal ortam (venv) kontrol ediliyor..." -ForegroundColor Yellow

if (-not (Test-Path "venv")) {
    Write-Host "Sanal ortam (venv) oluşturuluyor..." -ForegroundColor Yellow
    python -m venv venv
}

Write-Host "Bağımlılıklar venv içerisine kuruluyor..." -ForegroundColor Green
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[BAŞARILI] Kurulum tamamlandı! Uygulamayı çalıştırmak için .\run.ps1 dosyasını çalıştırabilirsiniz." -ForegroundColor Green
} else {
    Write-Host "`n[HATA] Kurulum sırasında bir hata oluştu." -ForegroundColor Red
}

Read-Host "Devam etmek için Enter'a basın..."
