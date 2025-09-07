@echo off
echo ぐるなびスクレイピングツールを起動中...
call scraper_env\Scripts\activate.bat
python production_ready_scraper.py
pause