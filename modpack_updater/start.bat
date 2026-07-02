@echo off
chcp 65001 > nul
title Modpack Güncelleyici Başlatıcı

echo [BİLGİ] Python scripti başlatılıyor...
echo --------------------------------------------------

pyinstaller --onefile --noconsole --icon=logo.ico --name="Modpack_Guncelleyici_v2" updater.py
:: pyinstaller --onefile --noconsole --icon=logo.ico --name="Modpack_Guncelleyici_OTOMATİK" updater_auto_dynamic.py
::pyinstaller --onefile --noconsole --icon=logo.ico --name="Modpack_Guncelleyici_MANUEL" updater_legacy.py

echo --------------------------------------------------
echo [BİLGİ] İşlem sona erdi veya script durduruldu.
echo CMD ekranının kapanmaması için bekletiliyor...
echo.

pause