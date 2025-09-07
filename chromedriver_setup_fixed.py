import os
import sys
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_chromedriver_fixed():
    """修正版ChromeDriverセットアップ"""
    try:
        print("修正版ChromeDriverをセットアップ中...")
        
        # システム情報表示
        print(f"OS: {platform.system()} {platform.architecture()}")
        print(f"Python: {sys.version}")
        
        # ChromeDriverManagerの設定
        manager = ChromeDriverManager()
        
        # キャッシュを無視して新しいドライバーを取得
        driver_path = manager.install()
        print(f"ChromeDriverパス: {driver_path}")
        
        # ファイル詳細確認
        if os.path.exists(driver_path):
            file_size = os.path.getsize(driver_path)
            print(f"ファイルサイズ: {file_size} bytes")
            
            # 実行可能かチェック
            is_executable = os.access(driver_path, os.X_OK)
            print(f"実行可能: {is_executable}")
        else:
            print("❌ ファイルが存在しません")
            return False
        
        # テスト実行
        print("テスト実行中...")
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()
        
        print("✅ ChromeDriverセットアップ完了")
        return True
        
    except Exception as e:
        print(f"❌ セットアップエラー: {e}")
        return False

if __name__ == "__main__":
    setup_chromedriver_fixed()