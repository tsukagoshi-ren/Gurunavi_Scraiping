@echo off
title ぐるなびスクレイピングツール - 最終ビルド
color 0A

echo =====================================
echo  ぐるなびスクレイピングツール v2.0
echo     Professional Edition
echo        最終ビルドスクリプト  
echo =====================================
echo.

echo [準備] 既存のビルドファイルをクリーンアップ中...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo [1/6] Python環境確認中...
python --version
if errorlevel 1 (
    echo エラー: Pythonが見つかりません
    pause
    exit /b 1
)

echo [2/6] 依存関係をインストール中...
pip install -r requirements_full.txt
if errorlevel 1 (
    echo エラー: 依存関係のインストールに失敗しました
    pause
    exit /b 1
)

echo [3/6] ChromeDriverをセットアップ中...
python chromedriver_setup.py
if errorlevel 1 (
    echo 警告: ChromeDriverのセットアップに失敗しました（継続）
)

echo [4/6] アプリケーションをexe化中...
pyinstaller --clean ^
    --onefile ^
    --windowed ^
    --name="GurunaviScraperPro" ^
    --icon=app.ico ^
    --add-data "scraper_config.json;." ^
    --hidden-import=selenium.webdriver.chrome.service ^
    --hidden-import=selenium.webdriver.chrome.options ^
    --hidden-import=selenium.webdriver.common.by ^
    --hidden-import=selenium.webdriver.support.ui ^
    --hidden-import=selenium.webdriver.support.expected_conditions ^
    --hidden-import=webdriver_manager.chrome ^
    --hidden-import=openpyxl.cell ^
    --hidden-import=openpyxl.styles ^
    --exclude-module=matplotlib ^
    --exclude-module=numpy ^
    --exclude-module=scipy ^
    production_ready_scraper.py

if errorlevel 1 (
    echo エラー: exe化に失敗しました
    pause
    exit /b 1
)

echo [5/6] 配布パッケージを作成中...
python deploy.py
if errorlevel 1 (
    echo エラー: 配布パッケージの作成に失敗しました
    pause
    exit /b 1
)

echo [6/6] インストーラーを作成中...
python installer_wizard.py

echo.
echo =====================================
echo  ✅ ビルド完了!
echo =====================================
echo.
echo 📦 実行ファイル: dist\GurunaviScraperPro.exe
echo 📁 配布パッケージ: GurunaviScraper_Professional_v2.0.zip
echo 🚀 インストーラー: installer_wizard.py
echo.
echo すべての成果物が正常に作成されました。
echo 配布前に動作テストを実施してください。
echo.
pause