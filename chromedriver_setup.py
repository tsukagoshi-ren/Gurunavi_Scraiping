import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def setup_chromedriver():
    """ChromeDriverを自動でセットアップ"""
    try:
        print("ChromeDriverをセットアップ中...")
        driver_path = ChromeDriverManager().install()
        print(f"ChromeDriverセットアップ完了: {driver_path}")
        
        # テスト実行
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()
        print("ChromeDriverテスト完了")
        return True
    except Exception as e:
        print(f"ChromeDriverセットアップエラー: {e}")
        return False

if __name__ == "__main__":
    setup_chromedriver()