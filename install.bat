@echo off
title StayAwake PC - Install Script
echo ===================================================
echo   StayAwake PC - Bagimlik Yukleyici Installer
echo ===================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python 3.12 veya uzerini yukleyin.
    pause
    exit /b 1
)

echo Python tespit edildi. Gerekli kutuphaneler yukleniyor...
if exist "venv\Scripts\python.exe" (
    echo Mevcut sanal ortam kullaniliyor...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo Yeni sanal ortam venv oluşturuluyor...
    python -m venv venv
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
)

if %errorlevel% equ 0 (
    echo.
    echo ===================================================
    echo [BASARILI] Tum bagimliklar basariyla yuklendi!
    echo Uygulamayi baslatmak icin run.bat dosyasini calistirabilirsiniz.
    echo ===================================================
) else (
    echo.
    echo [HATA] Kutuphane kurulumu sirasinda bir hata olustu.
)

echo.
pause
