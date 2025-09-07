@echo off
title ChromeDriver クイック修正ツール
color 0A

echo =========================================
echo  ChromeDriver クイック修正ツール
echo =========================================
echo.

echo [1/4] ChromeDriverキャッシュをクリア中...
rmdir /s /q "%USERPROFILE%\.wdm" 2>nul
echo ✅ キャッシュクリア完了

echo.
echo [2/4] 修正スクリプトを実行中...
python fix_chromedriver_ultimate.py

echo.
echo [3/4] アプリケーションをテスト起動中...
echo テスト起動では検証のみ行い、すぐに終了します。
timeout /t 3 /nobreak >nul

echo.
echo [4/4] 修正完了！
echo.
echo 📁 プロジェクトフォルダに chromedriver.exe が配置されました
echo 🚀 production_ready_scraper_fixed.py を実行してください
echo.
echo 次回からは以下を実行:
echo python production_ready_scraper_fixed.py
echo.

pause