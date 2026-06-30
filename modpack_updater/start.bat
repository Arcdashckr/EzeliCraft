@echo off
chcp 65001 > nul
title Modpack Güncelleyici Başlatıcı

echo [BİLGİ] Python scripti başlatılıyor...
echo --------------------------------------------------

pyinstaller --onefile --noconsole --icon=logo.ico --name="Modpack_Guncelleyici" updater.py

echo --------------------------------------------------
echo [BİLGİ] İşlem sona erdi veya script durduruldu.
echo CMD ekranının kapanmaması için bekletiliyor...
echo.

pause