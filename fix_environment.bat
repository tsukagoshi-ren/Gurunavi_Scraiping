@echo off
echo =========================================
echo  環境修正スクリプト
echo =========================================
echo.

echo [1/5] 仮想環境を作成中...
python -m venv scraper_env
if errorlevel 1 (
    echo エラー: 仮想環境の作成に失敗しました
    pause
    exit /b 1
)

echo [2/5] 仮想環境をアクティベート中...
call scraper_env\Scripts\activate.bat

echo [3/5] pipをアップグレード中...
python -m pip install --upgrade pip

echo [4/5] 互換性のある依存関係をインストール中...
pip install numpy==1.24.3
pip install pandas==2.0.3
pip install beautifulsoup4==4.12.2
pip install requests==2.31.0
pip install openpyxl==3.1.2
pip install lxml==4.9.3
pip install selenium==4.15.0
pip install webdriver-manager==4.0.1

echo [5/5] ChromeDriverをセットアップ中...
python chromedriver_setup.py

echo.
echo =========================================
echo  修正完了！
echo =========================================
echo.
echo 次回からは以下のコマンドで実行してください：
echo   scraper_env\Scripts\activate.bat
echo   python production_ready_scraper.py
echo.
pause
