import os
import sys
import shutil
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def fix_chromedriver():
    """ChromeDriverの問題を修正"""
    print("=" * 50)
    print("ChromeDriver修正スクリプト")
    print("=" * 50)
    
    try:
        # 1. 既存のChromeDriverキャッシュをクリア
        print("\n[1/6] 既存のChromeDriverキャッシュをクリア中...")
        wdm_path = Path.home() / ".wdm"
        if wdm_path.exists():
            shutil.rmtree(wdm_path)
            print("✅ キャッシュをクリアしました")
        else:
            print("ℹ️ キャッシュは存在しませんでした")
        
        # 2. Chromeのバージョンを確認
        print("\n[2/6] Chromeブラウザのバージョンを確認中...")
        try:
            result = subprocess.run([
                "reg", "query", 
                "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", 
                "/v", "version"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                chrome_version = result.stdout.split()[-1]
                print(f"✅ Chrome バージョン: {chrome_version}")
            else:
                print("⚠️ Chromeのバージョンを自動検出できませんでした")
        except Exception as e:
            print(f"⚠️ Chromeバージョン確認エラー: {e}")
        
        # 3. 新しいChromeDriverをダウンロード
        print("\n[3/6] 新しいChromeDriverをダウンロード中...")
        chrome_manager = ChromeDriverManager()
        driver_path = chrome_manager.install()
        print(f"✅ ChromeDriverをダウンロードしました: {driver_path}")
        
        # 4. ダウンロードしたドライバーの確認
        print("\n[4/6] ドライバーファイルを確認中...")
        driver_file = Path(driver_path)
        if driver_file.exists():
            file_size = driver_file.stat().st_size
            print(f"✅ ドライバーファイル存在: {driver_file}")
            print(f"✅ ファイルサイズ: {file_size:,} bytes")
            
            # 実行可能かチェック
            if driver_file.suffix.lower() == '.exe' or file_size > 1000000:  # 1MB以上
                print("✅ ドライバーファイルは正常です")
            else:
                print("❌ ドライバーファイルが破損している可能性があります")
                return False
        else:
            print("❌ ドライバーファイルが見つかりません")
            return False
        
        # 5. テスト実行
        print("\n[5/6] ドライバーのテスト実行中...")
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("✅ WebDriverの初期化成功")
        
        # 簡単なテスト
        driver.get("https://www.google.com")
        title = driver.title
        print(f"✅ テストページ取得成功: {title}")
        
        driver.quit()
        print("✅ WebDriverテスト完了")
        
        # 6. 設定ファイル更新
        print("\n[6/6] 設定ファイルを更新中...")
        update_config_file(driver_path)
        
        print("\n" + "=" * 50)
        print("✅ ChromeDriver修正完了！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        print("\n代替案を試行中...")
        return try_alternative_setup()

def try_alternative_setup():
    """代替セットアップ方法を試行"""
    try:
        print("\n[代替案] Chromeの手動検出を試行中...")
        
        # Chrome実行ファイルのパスを検索
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME'))
        ]
        
        chrome_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_path = path
                break
        
        if chrome_path:
            print(f"✅ Chrome実行ファイル発見: {chrome_path}")
            
            # Chromeのバージョンを取得
            result = subprocess.run([chrome_path, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.strip()
                print(f"✅ Chrome バージョン: {version_line}")
                
                # 特定バージョンのChromeDriverを取得
                try:
                    chrome_options = Options()
                    chrome_options.add_argument("--headless")
                    chrome_options.binary_location = chrome_path
                    
                    # ChromeDriverManager with specific version
                    manager = ChromeDriverManager()
                    driver_path = manager.install()
                    
                    service = Service(driver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver.get("https://www.google.com")
                    driver.quit()
                    
                    print("✅ 代替セットアップ成功！")
                    return True
                    
                except Exception as e:
                    print(f"❌ 代替セットアップ失敗: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ 代替セットアップエラー: {e}")
        return False

def update_config_file(driver_path):
    """設定ファイルにドライバーパスを記録"""
    try:
        import json
        config_file = Path("scraper_config.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config["chromedriver_path"] = str(driver_path)
        config["last_driver_update"] = str(Path().cwd())
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("✅ 設定ファイルを更新しました")
        
    except Exception as e:
        print(f"⚠️ 設定ファイル更新エラー: {e}")

def manual_download_instructions():
    """手動ダウンロードの手順を表示"""
    print("\n" + "=" * 60)
    print("📖 手動でChromeDriverをダウンロードする場合:")
    print("=" * 60)
    print("1. https://chromedriver.chromium.org/ にアクセス")
    print("2. お使いのChromeのバージョンに対応するChromeDriverをダウンロード")
    print("3. ダウンロードしたchromedriver.exeを以下のフォルダに配置:")
    print(f"   {Path.cwd()}")
    print("4. ファイル名を 'chromedriver.exe' にリネーム")
    print("5. アプリケーションを再実行")
    print("=" * 60)

if __name__ == "__main__":
    success = fix_chromedriver()
    
    if not success:
        print("\n⚠️ 自動修正に失敗しました")
        manual_download_instructions()
        
        print("\n以下のトラブルシューティングもお試しください:")
        print("- Chromeブラウザを最新版に更新")
        print("- Windowsを再起動")
        print("- ウイルス対策ソフトの除外設定を確認")
        print("- 管理者権限でコマンドプロンプトを実行")
    
    input("\nEnterキーを押して終了...")