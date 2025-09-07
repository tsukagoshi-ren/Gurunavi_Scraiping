import os
import sys
import shutil
import subprocess
import zipfile
import requests
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def fix_chromedriver_ultimate():
    """ChromeDriverの完全修正スクリプト"""
    print("=" * 50)
    print("ChromeDriver完全修正スクリプト")
    print("=" * 50)
    
    try:
        # 1. 既存のChromeDriverキャッシュを完全クリア
        print("\n[1/7] 既存のChromeDriverキャッシュを完全クリア中...")
        wdm_path = Path.home() / ".wdm"
        if wdm_path.exists():
            shutil.rmtree(wdm_path, ignore_errors=True)
            print("✅ webdriver-managerキャッシュをクリアしました")
        
        # ローカルのchromedriver.exeも削除
        local_drivers = [
            Path.cwd() / "chromedriver.exe",
            Path.cwd() / "chromedriver"
        ]
        for driver_path in local_drivers:
            if driver_path.exists():
                driver_path.unlink()
                print(f"✅ ローカルドライバーを削除: {driver_path}")
        
        # 2. Chromeのバージョンを取得
        print("\n[2/7] Chromeブラウザのバージョンを確認中...")
        chrome_version = get_chrome_version()
        if chrome_version:
            print(f"✅ Chrome バージョン: {chrome_version}")
            major_version = chrome_version.split('.')[0]
        else:
            print("⚠️ Chromeのバージョンを自動検出できませんでした")
            major_version = "139"  # デフォルト
        
        # 3. 手動でChromeDriverをダウンロード
        print("\n[3/7] ChromeDriverを手動ダウンロード中...")
        driver_path = manual_download_chromedriver(chrome_version or "139.0.7258.154")
        
        if not driver_path:
            print("❌ 手動ダウンロードに失敗しました")
            return False
        
        # 4. ダウンロードしたファイルの検証
        print("\n[4/7] ダウンロードファイルを検証中...")
        if not validate_chromedriver(driver_path):
            print("❌ ChromeDriverファイルが無効です")
            return False
        
        # 5. ローカルディレクトリにコピー
        print("\n[5/7] ChromeDriverをローカルディレクトリにコピー中...")
        local_driver_path = Path.cwd() / "chromedriver.exe"
        shutil.copy2(driver_path, local_driver_path)
        print(f"✅ ローカルにコピー完了: {local_driver_path}")
        
        # 6. テスト実行
        print("\n[6/7] ChromeDriverのテスト実行中...")
        if test_chromedriver(local_driver_path):
            print("✅ ChromeDriverテスト成功")
        else:
            print("❌ ChromeDriverテスト失敗")
            return False
        
        # 7. 設定ファイル更新
        print("\n[7/7] 設定ファイルを更新中...")
        update_config_file(str(local_driver_path))
        
        print("\n" + "=" * 50)
        print("✅ ChromeDriver修正完了！")
        print(f"📁 ChromeDriverパス: {local_driver_path}")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n❌ 修正中にエラーが発生しました: {e}")
        return False

def get_chrome_version():
    """Chromeのバージョンを取得"""
    try:
        # Windows Registry から取得
        result = subprocess.run([
            "reg", "query", 
            "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon", 
            "/v", "version"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            return result.stdout.split()[-1]
        
        # Chrome実行ファイルから取得
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
        
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                result = subprocess.run([chrome_path, "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    version_line = result.stdout.strip()
                    # "Google Chrome 139.0.7258.155" から "139.0.7258.155" を抽出
                    version = version_line.split()[-1]
                    return version
        
        return None
        
    except Exception as e:
        print(f"Chromeバージョン取得エラー: {e}")
        return None

def manual_download_chromedriver(chrome_version):
    """ChromeDriverを手動でダウンロード"""
    try:
        # Chrome for Testing APIを使用
        major_version = chrome_version.split('.')[0]
        
        # 利用可能なバージョンを取得
        print(f"Chrome {major_version} 用のChromeDriverを検索中...")
        
        # いくつかの安定版バージョンを試す
        test_versions = [
            chrome_version,
            f"{major_version}.0.7258.154",
            f"{major_version}.0.7258.149", 
            f"{major_version}.0.7258.125",
            "138.0.7138.140",  # フォールバック
            "137.0.7187.125"   # フォールバック
        ]
        
        for version in test_versions:
            print(f"バージョン {version} を試行中...")
            url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
            
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ バージョン {version} が利用可能です")
                    return download_and_extract_chromedriver(url, version)
            except requests.RequestException:
                continue
        
        print("❌ 利用可能なChromeDriverが見つかりませんでした")
        return None
        
    except Exception as e:
        print(f"手動ダウンロードエラー: {e}")
        return None

def download_and_extract_chromedriver(url, version):
    """ChromeDriverをダウンロードして展開"""
    try:
        print(f"ダウンロード中: {url}")
        
        # ダウンロード
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 一時ファイルに保存
        temp_dir = Path.cwd() / "temp_chromedriver"
        temp_dir.mkdir(exist_ok=True)
        zip_path = temp_dir / f"chromedriver_{version}.zip"
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ ダウンロード完了: {len(response.content):,} bytes")
        
        # ZIPファイルを展開
        extract_dir = temp_dir / f"chromedriver_{version}"
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # chromedriver.exe を検索
        chromedriver_paths = list(extract_dir.rglob("chromedriver.exe"))
        
        if chromedriver_paths:
            driver_path = chromedriver_paths[0]
            print(f"✅ ChromeDriverを発見: {driver_path}")
            return driver_path
        else:
            print("❌ 展開したファイルにchromedriver.exeが見つかりません")
            return None
            
    except Exception as e:
        print(f"ダウンロード・展開エラー: {e}")
        return None

def validate_chromedriver(driver_path):
    """ChromeDriverファイルを検証"""
    try:
        if not driver_path or not Path(driver_path).exists():
            print("❌ ファイルが存在しません")
            return False
        
        file_size = Path(driver_path).stat().st_size
        print(f"✅ ファイルサイズ: {file_size:,} bytes")
        
        # ファイルサイズチェック（ChromeDriverは通常5MB以上）
        if file_size < 1000000:  # 1MB未満は異常
            print("❌ ファイルサイズが小さすぎます")
            return False
        
        # 実行可能ファイルかチェック
        if not str(driver_path).endswith('.exe'):
            print("❌ 実行可能ファイルではありません")
            return False
        
        print("✅ ファイル検証成功")
        return True
        
    except Exception as e:
        print(f"ファイル検証エラー: {e}")
        return False

def test_chromedriver(driver_path):
    """ChromeDriverをテスト実行"""
    try:
        print("ChromeDriverテスト実行中...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--remote-debugging-port=9222")
        
        service = Service(str(driver_path))
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 簡単なテスト
        driver.get("https://www.google.com")
        title = driver.title
        
        driver.quit()
        
        print(f"✅ テスト成功: {title}")
        return True
        
    except Exception as e:
        print(f"テスト実行エラー: {e}")
        return False

def update_config_file(driver_path):
    """設定ファイルを更新"""
    try:
        import json
        config_file = Path("scraper_config.json")
        
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        config["chromedriver_path"] = driver_path
        config["last_chromedriver_update"] = str(Path().cwd())
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print("✅ 設定ファイルを更新しました")
        
    except Exception as e:
        print(f"⚠️ 設定ファイル更新エラー: {e}")

def cleanup_temp_files():
    """一時ファイルをクリーンアップ"""
    try:
        temp_dir = Path.cwd() / "temp_chromedriver"
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print("✅ 一時ファイルをクリーンアップしました")
    except Exception as e:
        print(f"⚠️ クリーンアップエラー: {e}")

if __name__ == "__main__":
    try:
        success = fix_chromedriver_ultimate()
        
        if success:
            print("\n🎉 ChromeDriver修正完了！")
            print("アプリケーションを再実行してください。")
        else:
            print("\n❌ ChromeDriver修正に失敗しました")
            print("\n手動での対処方法:")
            print("1. https://googlechromelabs.github.io/chrome-for-testing/ にアクセス")
            print("2. お使いのChromeバージョンに対応するChromeDriverをダウンロード")
            print("3. chromedriver.exe をプロジェクトフォルダに配置")
        
    finally:
        cleanup_temp_files()
        input("\nEnterキーを押して終了...")