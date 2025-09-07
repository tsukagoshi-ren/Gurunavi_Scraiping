@echo off
title ぐるなびスクレイピングツール v2.0
color 0A

echo =========================================
echo  ぐるなびスクレイピングツール v2.0
echo =========================================
echo.

echo [1/3] Python環境確認中...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ エラー: Pythonが見つかりません
    echo Pythonをインストールしてください
    pause
    exit /b 1
)
echo ✅ Python環境確認完了

echo.
echo [2/3] 必要パッケージの確認中...
python -c "import selenium, pandas, requests, bs4" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 必要パッケージが不足しています
    echo 自動インストールしますか？ (Y/N)
    set /p choice="選択: "
    if /i "%choice%"=="Y" (
        echo パッケージをインストール中...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ パッケージインストールに失敗しました
            pause
            exit /b 1
        )
        echo ✅ パッケージインストール完了
    ) else (
        echo インストールがスキップされました
        echo 手動でインストールしてください: pip install -r requirements.txt
        pause
        exit /b 1
    )
) else (
    echo ✅ 必要パッケージ確認完了
)

echo.
echo [3/3] アプリケーション起動中...
echo 📱 ぐるなびスクレイピングツールを起動します...
echo.

python gurunavi_scraper.py

echo.
echo アプリケーションが終了しました
pause