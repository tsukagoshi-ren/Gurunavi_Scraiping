@echo off
echo =========================================
echo  ChromeDriver クイック修正
echo =========================================
echo.

echo [1/3] ChromeDriverキャッシュをクリア中...
rmdir /s /q "%USERPROFILE%\.wdm" 2>nul
echo キャッシュクリア完了

echo [2/3] 新しいChromeDriverをセットアップ中...
python fix_chromedriver.py

echo [3/3] アプリケーションを再実行中...
python production_ready_scraper.py

pause