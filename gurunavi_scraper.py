"""
ぐるなび店舗情報スクレイピングツール v2.0 (統合版)
ChromeDriverエラーを修正した本格運用版
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import re
from urllib.parse import urljoin, quote, urlparse
import threading
from datetime import datetime
import random
import json
import logging
from pathlib import Path
import subprocess
import shutil
import zipfile

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False

class ChromeDriverFixer:
    """ChromeDriver修正クラス"""
    
    @staticmethod
    def fix_chromedriver():
        """ChromeDriverの完全修正"""
        print("=" * 50)
        print("ChromeDriver完全修正開始")
        print("=" * 50)
        
        try:
            # 1. キャッシュクリア
            print("\n[1/7] 既存のChromeDriverキャッシュをクリア中...")
            wdm_path = Path.home() / ".wdm"
            if wdm_path.exists():
                shutil.rmtree(wdm_path, ignore_errors=True)
                print("✅ webdriver-managerキャッシュをクリアしました")
            
            # ローカルのchromedriver.exeも削除
            local_drivers = [Path.cwd() / "chromedriver.exe", Path.cwd() / "chromedriver"]
            for driver_path in local_drivers:
                if driver_path.exists():
                    driver_path.unlink()
                    print(f"✅ ローカルドライバーを削除: {driver_path}")
            
            # 2. Chromeバージョン取得
            print("\n[2/7] Chromeブラウザのバージョン確認中...")
            chrome_version = ChromeDriverFixer.get_chrome_version()
            if chrome_version:
                print(f"✅ Chrome バージョン: {chrome_version}")
            else:
                print("⚠️ Chromeのバージョンを自動検出できませんでした")
                chrome_version = "139.0.7258.154"  # デフォルト
            
            # 3. 手動ダウンロード
            print("\n[3/7] ChromeDriverを手動ダウンロード中...")
            driver_path = ChromeDriverFixer.manual_download_chromedriver(chrome_version)
            
            if not driver_path:
                print("❌ 手動ダウンロードに失敗しました")
                return False
            
            # 4. ファイル検証
            print("\n[4/7] ダウンロードファイルを検証中...")
            if not ChromeDriverFixer.validate_chromedriver(driver_path):
                print("❌ ChromeDriverファイルが無効です")
                return False
            
            # 5. ローカルにコピー
            print("\n[5/7] ChromeDriverをローカルディレクトリにコピー中...")
            local_driver_path = Path.cwd() / "chromedriver.exe"
            shutil.copy2(driver_path, local_driver_path)
            print(f"✅ ローカルにコピー完了: {local_driver_path}")
            
            # 6. テスト実行
            print("\n[6/7] ChromeDriverのテスト実行中...")
            if ChromeDriverFixer.test_chromedriver(local_driver_path):
                print("✅ ChromeDriverテスト成功")
            else:
                print("❌ ChromeDriverテスト失敗")
                return False
            
            # 7. 設定ファイル更新
            print("\n[7/7] 設定ファイルを更新中...")
            ChromeDriverFixer.update_config_file(str(local_driver_path))
            
            print("\n" + "=" * 50)
            print("✅ ChromeDriver修正完了！")
            print(f"📁 ChromeDriverパス: {local_driver_path}")
            print("=" * 50)
            return True
            
        except Exception as e:
            print(f"\n❌ 修正中にエラーが発生しました: {e}")
            return False
        finally:
            ChromeDriverFixer.cleanup_temp_files()
    
    @staticmethod
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
                        version = version_line.split()[-1]
                        return version
            
            return None
            
        except Exception as e:
            print(f"Chromeバージョン取得エラー: {e}")
            return None
    
    @staticmethod
    def manual_download_chromedriver(chrome_version):
        """ChromeDriverを手動でダウンロード"""
        try:
            major_version = chrome_version.split('.')[0]
            print(f"Chrome {major_version} 用のChromeDriverを検索中...")
            
            # 複数バージョンを試行
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
                        return ChromeDriverFixer.download_and_extract_chromedriver(url, version)
                except requests.RequestException:
                    continue
            
            print("❌ 利用可能なChromeDriverが見つかりませんでした")
            return None
            
        except Exception as e:
            print(f"手動ダウンロードエラー: {e}")
            return None
    
    @staticmethod
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
    
    @staticmethod
    def validate_chromedriver(driver_path):
        """ChromeDriverファイルを検証"""
        try:
            if not driver_path or not Path(driver_path).exists():
                print("❌ ファイルが存在しません")
                return False
            
            file_size = Path(driver_path).stat().st_size
            print(f"✅ ファイルサイズ: {file_size:,} bytes")
            
            # ファイルサイズチェック
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
    
    @staticmethod
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
    
    @staticmethod
    def update_config_file(driver_path):
        """設定ファイルを更新"""
        try:
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
    
    @staticmethod
    def cleanup_temp_files():
        """一時ファイルをクリーンアップ"""
        try:
            temp_dir = Path.cwd() / "temp_chromedriver"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
                print("✅ 一時ファイルをクリーンアップしました")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")

class GurunaviScraper:
    """ぐるなびスクレイピングメインクラス"""
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("ぐるなび店舗情報スクレイピングツール v2.0")
        self.window.geometry("950x750")
        self.window.resizable(True, True)
        
        # アプリケーション設定
        self.app_dir = Path.cwd()
        self.config_file = self.app_dir / "scraper_config.json"
        self.log_file = self.app_dir / "scraper.log"
        
        # ログ設定
        self.setup_logging()
        
        # 初期化
        self.default_save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.is_scraping = False
        self.scraped_data = []
        self.driver = None
        self.total_found = 0
        
        # 設定読み込み
        self.load_config()
        
        # Selenium利用可能性チェック
        if not SELENIUM_AVAILABLE:
            self.logger.warning("Seleniumが利用できません。基本機能のみ利用可能です。")
        
        self.setup_ui()
    
    def setup_logging(self):
        """ログ設定"""
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("アプリケーション開始")
    
    def load_config(self):
        """設定ファイルから設定を読み込み"""
        default_config = {
            "last_save_path": self.default_save_path,
            "delay_min": 2.0,
            "delay_max": 5.0,
            "timeout": 15,
            "headless": True,
            "window_size": "1920,1080",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "max_retries": 3,
            "implicit_wait": 10,
            "page_load_timeout": 30,
            "chromedriver_path": ""
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
        
        self.config = default_config
    
    def save_config(self):
        """設定ファイルに設定を保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            self.logger.info("設定を保存しました")
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
    
    def setup_ui(self):
        """UI設定"""
        # メインフレーム
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="ぐるなび店舗情報スクレイピングツール v2.0", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Seleniumステータス表示
        status_color = "green" if SELENIUM_AVAILABLE else "red"
        status_text = "Selenium: 利用可能" if SELENIUM_AVAILABLE else "Selenium: 利用不可（pip install selenium）"
        status_label = ttk.Label(main_frame, text=status_text, foreground=status_color)
        status_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))
        
        # ChromeDriverステータス
        chromedriver_status = self.check_chromedriver_status()
        chromedriver_color = "green" if chromedriver_status["available"] else "orange"
        chromedriver_label = ttk.Label(main_frame, text=chromedriver_status["message"], 
                                     foreground=chromedriver_color)
        chromedriver_label.grid(row=2, column=0, columnspan=4, pady=(0, 10))
        
        # ノートブック（タブ）
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タブ作成
        self.main_tab = ttk.Frame(notebook)
        self.config_tab = ttk.Frame(notebook)
        self.log_tab = ttk.Frame(notebook)
        
        notebook.add(self.main_tab, text="検索・実行")
        notebook.add(self.config_tab, text="詳細設定")
        notebook.add(self.log_tab, text="ログ")
        
        self.setup_main_tab()
        self.setup_config_tab()
        self.setup_log_tab()
        
        # グリッド設定
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def check_chromedriver_status(self):
        """ChromeDriverの状態をチェック"""
        # ローカルのchromedriver.exeをチェック
        local_driver = Path.cwd() / "chromedriver.exe"
        if local_driver.exists():
            return {
                "available": True,
                "message": f"ChromeDriver: ローカル版利用可能"
            }
        
        # 設定ファイルのパスをチェック
        config_path = self.config.get("chromedriver_path", "")
        if config_path and Path(config_path).exists():
            return {
                "available": True,
                "message": f"ChromeDriver: 設定版利用可能"
            }
        
        # webdriver-managerをチェック
        if WEBDRIVER_MANAGER_AVAILABLE:
            return {
                "available": True,
                "message": "ChromeDriver: webdriver-manager経由で利用可能"
            }
        
        return {
            "available": False,
            "message": "ChromeDriver: 利用不可 - 「ChromeDriver修正」ボタンを押してください"
        }
    
    def setup_main_tab(self):
        """メインタブのUI設定"""
        # 検索条件フレーム
        search_frame = ttk.LabelFrame(self.main_tab, text="検索条件", padding="15")
        search_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 都道府県・市区町村
        ttk.Label(search_frame, text="都道府県:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.prefecture_var = tk.StringVar()
        self.prefecture_combo = ttk.Combobox(search_frame, textvariable=self.prefecture_var, width=18)
        self.prefecture_combo['values'] = self.get_prefecture_list()
        self.prefecture_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(search_frame, text="市区町村:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(search_frame, textvariable=self.city_var, width=18)
        self.city_entry.grid(row=0, column=3, padx=(0, 20))
        
        # ジャンル・駅
        ttk.Label(search_frame, text="ジャンル:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        self.genre_var = tk.StringVar()
        self.genre_combo = ttk.Combobox(search_frame, textvariable=self.genre_var, width=18)
        self.genre_combo['values'] = self.get_genre_list()
        self.genre_combo.grid(row=1, column=1, pady=(10, 0), padx=(0, 20))
        
        ttk.Label(search_frame, text="最寄り駅:").grid(row=1, column=2, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        self.station_var = tk.StringVar()
        self.station_entry = ttk.Entry(search_frame, textvariable=self.station_var, width=18)
        self.station_entry.grid(row=1, column=3, pady=(10, 0), padx=(0, 20))
        
        # キーワード・件数
        ttk.Label(search_frame, text="キーワード:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        self.keyword_var = tk.StringVar()
        self.keyword_entry = ttk.Entry(search_frame, textvariable=self.keyword_var, width=40)
        self.keyword_entry.grid(row=2, column=1, columnspan=2, pady=(10, 0), padx=(0, 20))
        
        ttk.Label(search_frame, text="最大件数:").grid(row=2, column=2, sticky=tk.W, pady=(10, 0), padx=(20, 10))
        self.max_count_var = tk.StringVar(value="100")
        max_count_spinbox = ttk.Spinbox(search_frame, textvariable=self.max_count_var, 
                                       from_=1, to=1000, width=10)
        max_count_spinbox.grid(row=2, column=3, pady=(10, 0))
        
        # 保存設定フレーム
        save_frame = ttk.LabelFrame(self.main_tab, text="保存設定", padding="15")
        save_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(save_frame, text="保存先:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.save_path_var = tk.StringVar(value=self.config.get("last_save_path", self.default_save_path))
        self.save_path_entry = ttk.Entry(save_frame, textvariable=self.save_path_var, width=60)
        self.save_path_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(save_frame, text="参照", command=self.browse_save_path).grid(row=0, column=2)
        
        ttk.Label(save_frame, text="ファイル名:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_var = tk.StringVar(value=f"gurunavi_data_{timestamp}")
        self.filename_entry = ttk.Entry(save_frame, textvariable=self.filename_var, width=60)
        self.filename_entry.grid(row=1, column=1, pady=(10, 0), padx=(0, 10))
        ttk.Label(save_frame, text=".xlsx").grid(row=1, column=2, pady=(10, 0))
        
        # 実行制御フレーム
        control_frame = ttk.Frame(self.main_tab)
        control_frame.grid(row=2, column=0, columnspan=4, pady=(0, 15))
        
        self.start_button = ttk.Button(control_frame, text="スクレイピング開始", 
                                      command=self.start_scraping)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止", 
                                     command=self.stop_scraping, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_button = ttk.Button(control_frame, text="Excelエクスポート", 
                                       command=self.manual_export)
        self.export_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(control_frame, text="結果クリア", 
                                      command=self.clear_results)
        self.clear_button.pack(side=tk.LEFT)
        
        # プログレス・ステータスフレーム
        progress_frame = ttk.Frame(self.main_tab)
        progress_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 15))
        
        # ステータス情報
        status_info_frame = ttk.Frame(progress_frame)
        status_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar(value="準備完了")
        self.status_label = ttk.Label(status_info_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)
        
        self.count_var = tk.StringVar(value="取得件数: 0")
        self.count_label = ttk.Label(status_info_frame, textvariable=self.count_var)
        self.count_label.pack(anchor=tk.W)
        
        # 結果表示フレーム
        result_frame = ttk.LabelFrame(self.main_tab, text="取得結果", padding="10")
        result_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 結果テーブル
        columns = ('No.', '店舗名', '電話番号', '住所', 'ジャンル', '最寄り駅')
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=10)
        
        # 列設定
        column_widths = {'No.': 50, '店舗名': 200, '電話番号': 120, '住所': 250, 'ジャンル': 100, '最寄り駅': 120}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # スクロールバー
        v_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # グリッド重み設定
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.main_tab.columnconfigure(3, weight=1)
        self.main_tab.rowconfigure(4, weight=1)
    
    def setup_config_tab(self):
        """設定タブのUI設定"""
        # ブラウザ設定
        browser_frame = ttk.LabelFrame(self.config_tab, text="ブラウザ設定", padding="15")
        browser_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.headless_var = tk.BooleanVar(value=self.config.get("headless", True))
        ttk.Checkbutton(browser_frame, text="ヘッドレスモード（ブラウザを表示しない）", 
                       variable=self.headless_var).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(browser_frame, text="ウィンドウサイズ:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        self.window_size_var = tk.StringVar(value=self.config.get("window_size", "1920,1080"))
        ttk.Entry(browser_frame, textvariable=self.window_size_var, width=15).grid(row=1, column=1, pady=(10, 0))
        
        # タイミング設定
        timing_frame = ttk.LabelFrame(self.config_tab, text="アクセス制御設定", padding="15")
        timing_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        timing_labels = ["最小間隔(秒):", "最大間隔(秒):", "タイムアウト(秒):", "暗黙的待機(秒):"]
        self.delay_min_var = tk.StringVar(value=str(self.config.get("delay_min", 2.0)))
        self.delay_max_var = tk.StringVar(value=str(self.config.get("delay_max", 5.0)))
        self.timeout_var = tk.StringVar(value=str(self.config.get("timeout", 15)))
        self.implicit_wait_var = tk.StringVar(value=str(self.config.get("implicit_wait", 10)))
        timing_vars = [self.delay_min_var, self.delay_max_var, self.timeout_var, self.implicit_wait_var]
        
        for i, (label, var) in enumerate(zip(timing_labels, timing_vars)):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(timing_frame, text=label).grid(row=row, column=col, sticky=tk.W, padx=(0, 10))
            ttk.Entry(timing_frame, textvariable=var, width=10).grid(row=row, column=col+1, padx=(0, 20))
        
        # ユーザーエージェント設定
        ua_frame = ttk.LabelFrame(self.config_tab, text="ユーザーエージェント", padding="15")
        ua_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.user_agent_var = tk.StringVar(value=self.config.get("user_agent", ""))
        ua_entry = ttk.Entry(ua_frame, textvariable=self.user_agent_var, width=80)
        ua_entry.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # ChromeDriver設定
        driver_frame = ttk.LabelFrame(self.config_tab, text="ChromeDriver設定", padding="15")
        driver_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(driver_frame, text="ドライバーパス:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.driver_path_var = tk.StringVar(value=self.config.get("chromedriver_path", ""))
        driver_entry = ttk.Entry(driver_frame, textvariable=self.driver_path_var, width=60)
        driver_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(driver_frame, text="参照", command=self.browse_driver_path).grid(row=0, column=2)
        
        # 設定ボタン
        button_frame = ttk.Frame(self.config_tab)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(15, 0))
        
        ttk.Button(button_frame, text="設定を保存", command=self.save_current_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="デフォルトに戻す", command=self.reset_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="ChromeDriver修正", command=self.fix_chromedriver).pack(side=tk.LEFT)
    
    def setup_log_tab(self):
        """ログタブのUI設定"""
        log_frame = ttk.Frame(self.log_tab)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ログ表示エリア
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ログ制御ボタン
        log_button_frame = ttk.Frame(self.log_tab)
        log_button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(log_button_frame, text="ログ更新", command=self.update_log_display).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_button_frame, text="ログクリア", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(log_button_frame, text="ログ保存", command=self.save_log).pack(side=tk.LEFT)
        
        # 初期ログ表示
        self.update_log_display()
    
    def get_prefecture_list(self):
        """都道府県リストを取得"""
        return [
            '', '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
            '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
            '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
            '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
    
    def get_genre_list(self):
        """ジャンルリストを取得"""
        return [
            '', '居酒屋', '焼肉・ホルモン', 'ラーメン', '寿司', 'イタリアン', 'フレンチ',
            '中華', '和食', '洋食', 'カフェ・喫茶店', 'ファストフード', '韓国料理',
            'タイ料理', 'インド料理', 'ピザ', 'ハンバーガー', 'お好み焼き・もんじゃ',
            'うどん・そば', '天ぷら', '鍋料理', 'しゃぶしゃぶ', 'すき焼き', '海鮮料理',
            '串焼き・串カツ', 'とんかつ', 'ステーキ', 'ハンバーグ', 'オムライス'
        ]
    
    def browse_save_path(self):
        """保存先フォルダを選択"""
        folder_path = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if folder_path:
            self.save_path_var.set(folder_path)
    
    def browse_driver_path(self):
        """ChromeDriverファイルを選択"""
        file_path = filedialog.askopenfilename(
            title="ChromeDriverを選択",
            filetypes=[("実行ファイル", "*.exe"), ("全てのファイル", "*.*")],
            initialdir=str(Path.cwd())
        )
        if file_path:
            self.driver_path_var.set(file_path)
    
    def fix_chromedriver(self):
        """ChromeDriverを修正"""
        result = messagebox.askyesno(
            "ChromeDriver修正", 
            "ChromeDriverの修正を実行しますか？\n\n"
            "この処理により：\n"
            "1. 既存のChromeDriverキャッシュがクリアされます\n"
            "2. 新しいChromeDriverがダウンロードされます\n"
            "3. プロジェクトフォルダにchromedriver.exeが配置されます\n\n"
            "続行しますか？"
        )
        
        if result:
            try:
                self.status_var.set("ChromeDriver修正中...")
                self.window.update()
                
                # ChromeDriverFixerを使用して修正
                success = ChromeDriverFixer.fix_chromedriver()
                
                if success:
                    messagebox.showinfo("修正完了", "ChromeDriverの修正が完了しました。")
                    self.logger.info("ChromeDriver修正完了")
                else:
                    messagebox.showerror("修正失敗", "ChromeDriverの修正に失敗しました。")
                    
            except Exception as e:
                messagebox.showerror("エラー", f"ChromeDriver修正中にエラーが発生しました:\n{e}")
            finally:
                self.status_var.set("準備完了")
    
    def save_current_config(self):
        """現在の設定を保存"""
        try:
            self.config.update({
                "last_save_path": self.save_path_var.get(),
                "headless": self.headless_var.get(),
                "window_size": self.window_size_var.get(),
                "delay_min": float(self.delay_min_var.get()),
                "delay_max": float(self.delay_max_var.get()),
                "timeout": int(self.timeout_var.get()),
                "implicit_wait": int(self.implicit_wait_var.get()),
                "user_agent": self.user_agent_var.get(),
                "chromedriver_path": self.driver_path_var.get()
            })
            self.save_config()
            messagebox.showinfo("設定保存", "設定が保存されました。")
        except Exception as e:
            messagebox.showerror("設定エラー", f"設定保存中にエラーが発生しました: {e}")
    
    def reset_config(self):
        """設定をデフォルトに戻す"""
        if messagebox.askyesno("確認", "設定をデフォルトに戻しますか？"):
            self.load_config()
            # UI要素を更新
            self.headless_var.set(self.config.get("headless", True))
            self.window_size_var.set(self.config.get("window_size", "1920,1080"))
            self.delay_min_var.set(str(self.config.get("delay_min", 2.0)))
            self.delay_max_var.set(str(self.config.get("delay_max", 5.0)))
            self.timeout_var.set(str(self.config.get("timeout", 15)))
            self.implicit_wait_var.set(str(self.config.get("implicit_wait", 10)))
            self.user_agent_var.set(self.config.get("user_agent", ""))
            self.driver_path_var.set(self.config.get("chromedriver_path", ""))
            messagebox.showinfo("設定リセット", "設定をデフォルトに戻しました。")
    
    def update_log_display(self):
        """ログ表示を更新"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, log_content)
                self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"ログ読み込みエラー: {e}\n")
    
    def clear_log(self):
        """ログをクリア"""
        if messagebox.askyesno("確認", "ログをクリアしますか？"):
            self.log_text.delete(1.0, tk.END)
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    f.write("")
                self.logger.info("ログがクリアされました")
            except Exception as e:
                self.logger.error(f"ログクリアエラー: {e}")
    
    def save_log(self):
        """ログを別名で保存"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("ログファイル", "*.log"), ("テキストファイル", "*.txt"), ("全てのファイル", "*.*")]
            )
            if file_path:
                with open(self.log_file, 'r', encoding='utf-8') as src:
                    with open(file_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                messagebox.showinfo("保存完了", f"ログが保存されました:\n{file_path}")
        except Exception as e:
            messagebox.showerror("保存エラー", f"ログ保存中にエラーが発生しました:\n{e}")
    
    def start_scraping(self):
        """スクレイピング開始"""
        if not self.validate_inputs():
            return
        
        self.set_scraping_state(True)
        self.scraped_data = []
        self.total_found = 0
        self.clear_results()
        
        # スレッドでスクレイピング実行
        thread = threading.Thread(target=self.scrape_worker)
        thread.daemon = True
        thread.start()
    
    def validate_inputs(self):
        """入力値検証"""
        if not any([self.prefecture_var.get(), self.city_var.get(), self.station_var.get(), self.keyword_var.get()]):
            messagebox.showerror("エラー", "検索条件を最低一つは入力してください。")
            return False
        
        try:
            max_count = int(self.max_count_var.get())
            if max_count <= 0 or max_count > 10000:
                raise ValueError
        except ValueError:
            messagebox.showerror("エラー", "最大件数は1-10000の範囲で入力してください。")
            return False
        
        if not self.filename_var.get().strip():
            messagebox.showerror("エラー", "ファイル名を入力してください。")
            return False
        
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("エラー", "Seleniumが利用できません。\npip install selenium で インストールしてください。")
            return False
        
        driver_status = self.check_chromedriver_status()
        if not driver_status["available"]:
            messagebox.showerror("エラー", "ChromeDriverが利用できません。\n「ChromeDriver修正」ボタンを押してください。")
            return False
        
        return True
    
    def set_scraping_state(self, is_scraping):
        """スクレイピング状態の制御"""
        self.is_scraping = is_scraping
        self.start_button.config(state='disabled' if is_scraping else 'normal')
        self.stop_button.config(state='normal' if is_scraping else 'disabled')
    
    def stop_scraping(self):
        """スクレイピング停止"""
        self.is_scraping = False
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
        self.set_scraping_state(False)
        self.status_var.set("停止されました")
        self.logger.info("スクレイピングが停止されました")
    
    def clear_results(self):
        """結果をクリア"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.scraped_data = []
        self.total_found = 0
        self.count_var.set("取得件数: 0")
        self.progress_var.set(0)
    
    def manual_export(self):
        """手動でExcelエクスポート"""
        self.save_to_excel()
    
    def scrape_worker(self):
        """スクレイピングワーカー（メインロジック）"""
        try:
            self.logger.info("スクレイピング開始")
            self.status_var.set("初期化中...")
            
            if not self.setup_driver():
                return
            
            max_count = int(self.max_count_var.get())
            self.perform_scraping(max_count)
            
            if self.is_scraping:
                self.save_to_excel()
                self.status_var.set(f"完了: {len(self.scraped_data)}件取得")
                messagebox.showinfo("完了", f"{len(self.scraped_data)}件の店舗情報を取得してExcelファイルに保存しました。")
            
        except Exception as e:
            self.logger.error(f"スクレイピングエラー: {e}")
            messagebox.showerror("エラー", f"スクレイピング中にエラーが発生しました:\n{str(e)}")
        finally:
            self.cleanup_driver()
            self.set_scraping_state(False)
    
    def setup_driver(self):
        """Seleniumドライバー設定"""
        try:
            chrome_options = Options()
            
            if self.config.get("headless", True):
                chrome_options.add_argument("--headless")
            
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            window_size = self.config.get("window_size", "1920,1080")
            chrome_options.add_argument(f"--window-size={window_size}")
            
            user_agent = self.config.get("user_agent")
            if user_agent:
                chrome_options.add_argument(f"--user-agent={user_agent}")
            
            driver_path = self.get_chromedriver_path()
            if not driver_path:
                raise Exception("ChromeDriverが見つかりません。「ChromeDriver修正」ボタンを押してください。")
            
            service = Service(driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(self.config.get("implicit_wait", 10))
            self.driver.set_page_load_timeout(self.config.get("page_load_timeout", 30))
            
            self.logger.info("Webドライバーが正常に初期化されました")
            return True
            
        except Exception as e:
            self.logger.error(f"ドライバー初期化エラー: {e}")
            messagebox.showerror("エラー", f"ブラウザドライバーの初期化に失敗しました:\n{e}")
            return False
    
    def get_chromedriver_path(self):
        """ChromeDriverのパスを取得"""
        # 1. 設定ファイルのパスをチェック
        config_path = self.config.get("chromedriver_path", "")
        if config_path and Path(config_path).exists():
            self.logger.info(f"設定からChromeDriverを使用: {config_path}")
            return config_path
        
        # 2. ローカルのchromedriver.exeをチェック
        local_driver = Path.cwd() / "chromedriver.exe"
        if local_driver.exists():
            self.logger.info(f"ローカルChromeDriverを使用: {local_driver}")
            return str(local_driver)
        
        # 3. webdriver-managerを使用（最後の手段）
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                self.logger.info("webdriver-managerを使用してChromeDriverを取得")
                driver_path = ChromeDriverManager().install()
                return driver_path
            except Exception as e:
                self.logger.error(f"webdriver-managerエラー: {e}")
        
        return None
    
    def cleanup_driver(self):
        """ドライバーのクリーンアップ"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def perform_scraping(self, max_count):
        """実際のスクレイピング処理"""
        try:
            search_url = self.build_search_url()
            self.logger.info(f"検索URL: {search_url}")
            
            self.status_var.set("検索ページにアクセス中...")
            self.driver.get(search_url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            page_num = 1
            collected_count = 0
            
            while self.is_scraping and collected_count < max_count:
                self.status_var.set(f"ページ {page_num} を処理中... ({collected_count}/{max_count})")
                self.logger.info(f"ページ {page_num} の処理開始")
                
                store_links = self.extract_store_links()
                
                if not store_links:
                    self.logger.info("店舗リンクが見つかりませんでした。検索終了。")
                    break
                
                for i, link in enumerate(store_links):
                    if not self.is_scraping or collected_count >= max_count:
                        break
                    
                    self.status_var.set(f"店舗 {i+1}/{len(store_links)} を処理中... (ページ{page_num})")
                    
                    store_data = self.scrape_store_detail(link)
                    if store_data:
                        collected_count += 1
                        self.scraped_data.append(store_data)
                        
                        self.update_result_display(store_data, collected_count)
                        
                        progress = min((collected_count / max_count) * 100, 100)
                        self.progress_var.set(progress)
                        self.count_var.set(f"取得件数: {collected_count}")
                        
                        self.window.update_idletasks()
                    
                    self.smart_delay()
                
                if collected_count < max_count and self.has_next_page():
                    self.go_to_next_page()
                    page_num += 1
                    time.sleep(random.uniform(2, 4))
                else:
                    break
            
            self.logger.info(f"スクレイピング完了: {collected_count}件取得")
            
        except Exception as e:
            self.logger.error(f"スクレイピング処理エラー: {e}")
            raise
    
    def build_search_url(self):
        """検索URLを構築"""
        base_url = "https://r.gnavi.co.jp/area/jp/rs/"
        
        params = []
        prefecture = self.prefecture_var.get()
        city = self.city_var.get()
        genre = self.genre_var.get()
        station = self.station_var.get()
        keyword = self.keyword_var.get()
        
        if prefecture:
            params.append(f"pref={quote(prefecture)}")
        if city:
            params.append(f"area={quote(city)}")
        if genre:
            params.append(f"category={quote(genre)}")
        if station:
            params.append(f"station={quote(station)}")
        if keyword:
            params.append(f"freeword={quote(keyword)}")
        
        if params:
            return f"{base_url}?{'&'.join(params)}"
        else:
            return base_url
    
    def extract_store_links(self):
        """ページから店舗リンクを抽出"""
        try:
            link_selectors = [
                "a[href*='r.gnavi.co.jp/'][href*='/']",
                ".item-name a",
                ".shop-name a",
                ".restaurant-link a"
            ]
            
            links = []
            for selector in link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and self.is_valid_store_url(href):
                            links.append(href)
                except:
                    continue
            
            unique_links = list(set(links))
            self.logger.info(f"ページから {len(unique_links)} 件の店舗リンクを抽出")
            
            return unique_links[:20]
            
        except Exception as e:
            self.logger.error(f"店舗リンク抽出エラー: {e}")
            return []
    
    def is_valid_store_url(self, url):
        """有効な店舗URLかチェック"""
        if not url:
            return False
        
        patterns = [
            r'r\.gnavi\.co\.jp/[a-zA-Z0-9]+/?',
            r'r\.gnavi\.co\.jp/[a-zA-Z0-9]+/\w*/?'
        ]
        
        return any(re.search(pattern, url) for pattern in patterns)
    
    def scrape_store_detail(self, url):
        """店舗詳細情報を取得"""
        try:
            self.logger.debug(f"店舗詳細取得開始: {url}")
            
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            store_data = {
                'URL': url,
                '店舗名': self.extract_store_name(),
                '電話番号': self.extract_phone_number(),
                '住所': self.extract_address(),
                'ジャンル': self.extract_genre(),
                '最寄り駅': self.extract_station(),
                '営業時間': self.extract_business_hours(),
                '定休日': self.extract_holiday(),
                '座席数': self.extract_seats(),
                '予算': self.extract_budget(),
                '個室': self.extract_private_room(),
                '禁煙・喫煙': self.extract_smoking(),
                '駐車場': self.extract_parking(),
                'クレジットカード': self.extract_credit_card(),
                '取得日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            for key, value in store_data.items():
                if isinstance(value, str):
                    store_data[key] = value.strip()
            
            self.logger.debug(f"店舗情報取得完了: {store_data.get('店舗名', 'Unknown')}")
            return store_data
            
        except Exception as e:
            self.logger.error(f"店舗詳細取得エラー ({url}): {e}")
            return None
    
    def extract_store_name(self):
        """店舗名を抽出"""
        selectors = ['h1.shop-name', 'h1[class*="name"]', '.restaurant-name h1', '.shop-title h1', '.store-name', 'h1']
        return self.extract_text_by_selectors(selectors)
    
    def extract_phone_number(self):
        """電話番号を抽出"""
        selectors = ['a[href^="tel:"]', '.phone', '.tel', '[class*="phone"]', '[class*="tel"]']
        text = self.extract_text_by_selectors(selectors)
        if text:
            phone_match = re.search(r'(\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4})', text)
            if phone_match:
                return phone_match.group(1)
        return text
    
    def extract_address(self):
        """住所を抽出"""
        selectors = ['.address', '.shop-address', '[class*="address"]', '.location']
        return self.extract_text_by_selectors(selectors)
    
    def extract_genre(self):
        """ジャンルを抽出"""
        selectors = ['.genre', '.category', '[class*="genre"]', '[class*="category"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_station(self):
        """最寄り駅を抽出"""
        selectors = ['.station', '.access', '[class*="station"]', '[class*="access"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_business_hours(self):
        """営業時間を抽出"""
        selectors = ['.business-hours', '.opening-hours', '[class*="hours"]', '[class*="time"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_holiday(self):
        """定休日を抽出"""
        selectors = ['.holiday', '.closed', '[class*="holiday"]', '[class*="closed"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_seats(self):
        """座席数を抽出"""
        selectors = ['.seats', '.capacity', '[class*="seat"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_budget(self):
        """予算を抽出"""
        selectors = ['.budget', '.price', '[class*="budget"]', '[class*="price"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_private_room(self):
        """個室情報を抽出"""
        selectors = ['.private-room', '[class*="private"]', '[class*="room"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_smoking(self):
        """喫煙情報を抽出"""
        selectors = ['.smoking', '[class*="smoking"]', '[class*="smoke"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_parking(self):
        """駐車場情報を抽出"""
        selectors = ['.parking', '[class*="parking"]', '[class*="park"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_credit_card(self):
        """クレジットカード情報を抽出"""
        selectors = ['.credit-card', '[class*="credit"]', '[class*="card"]']
        return self.extract_text_by_selectors(selectors)
    
    def extract_text_by_selectors(self, selectors):
        """複数のセレクタを試してテキストを抽出"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
            except Exception as e:
                self.logger.debug(f"セレクタ {selector} でエラー: {e}")
                continue
        return ''
    
    def has_next_page(self):
        """次のページが存在するかチェック"""
        try:
            next_selectors = ["a[class*='next']", ".pager_next a", ".next a", "a[href*='page=']"]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_enabled():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"次ページチェックエラー: {e}")
            return False
    
    def go_to_next_page(self):
        """次のページに移動"""
        try:
            next_selectors = ["a[class*='next']", ".pager_next a", ".next a"]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except Exception as e:
            self.logger.error(f"ページ移動エラー: {e}")
            return False
    
    def smart_delay(self):
        """インテリジェントな遅延制御"""
        min_delay = self.config.get("delay_min", 2.0)
        max_delay = self.config.get("delay_max", 5.0)
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def update_result_display(self, store_data, count):
        """結果表示を更新"""
        self.tree.insert('', 'end', values=(
            count,
            store_data.get('店舗名', ''),
            store_data.get('電話番号', ''),
            store_data.get('住所', ''),
            store_data.get('ジャンル', ''),
            store_data.get('最寄り駅', '')
        ))
        
        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])
    
    def save_to_excel(self):
        """Excelファイルに保存"""
        try:
            if not self.scraped_data:
                messagebox.showwarning("警告", "保存するデータがありません。")
                return
            
            df = pd.DataFrame(self.scraped_data)
            
            save_path = self.save_path_var.get()
            filename = self.filename_var.get().strip()
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            full_path = os.path.join(save_path, filename)
            
            with pd.ExcelWriter(full_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='店舗データ', index=False)
                self.create_statistics_sheet(df, writer)
                self.create_genre_summary_sheet(df, writer)
                self.create_area_summary_sheet(df, writer)
                self.adjust_column_width(writer)
            
            self.config["last_save_path"] = save_path
            self.save_config()
            
            self.logger.info(f"Excelファイル保存完了: {full_path}")
            messagebox.showinfo("保存完了", f"ファイルが保存されました:\n{full_path}\n\n取得件数: {len(df)}件")
            
        except Exception as e:
            self.logger.error(f"Excel保存エラー: {e}")
            messagebox.showerror("保存エラー", f"ファイル保存中にエラーが発生しました:\n{str(e)}")
    
    def create_statistics_sheet(self, df, writer):
        """統計情報シートを作成"""
        stats_data = {
            '項目': ['総取得件数', '電話番号あり', '住所あり', 'ジャンル情報あり', '営業時間あり', '最寄り駅あり'],
            '件数': [
                len(df),
                df['電話番号'].notna().sum() if '電話番号' in df.columns else 0,
                df['住所'].notna().sum() if '住所' in df.columns else 0,
                df['ジャンル'].notna().sum() if 'ジャンル' in df.columns else 0,
                df['営業時間'].notna().sum() if '営業時間' in df.columns else 0,
                df['最寄り駅'].notna().sum() if '最寄り駅' in df.columns else 0
            ],
            '割合(%)': []
        }
        
        total = len(df)
        for count in stats_data['件数']:
            percentage = (count / total * 100) if total > 0 else 0
            stats_data['割合(%)'].append(f"{percentage:.1f}%")
        
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='統計情報', index=False)
    
    def create_genre_summary_sheet(self, df, writer):
        """ジャンル別集計シートを作成"""
        if 'ジャンル' in df.columns:
            genre_counts = df['ジャンル'].value_counts().reset_index()
            genre_counts.columns = ['ジャンル', '件数']
            
            total = len(df)
            genre_counts['割合(%)'] = (genre_counts['件数'] / total * 100).round(1)
            
            genre_counts.to_excel(writer, sheet_name='ジャンル別集計', index=False)
    
    def create_area_summary_sheet(self, df, writer):
        """エリア別集計シートを作成"""
        if '住所' in df.columns:
            prefecture_pattern = r'(.*?[都道府県])'
            df_copy = df.copy()
            df_copy['都道府県'] = df_copy['住所'].str.extract(prefecture_pattern)[0]
            
            area_counts = df_copy['都道府県'].value_counts().reset_index()
            area_counts.columns = ['都道府県', '件数']
            
            total = len(df_copy)
            area_counts['割合(%)'] = (area_counts['件数'] / total * 100).round(1)
            
            area_counts.to_excel(writer, sheet_name='エリア別集計', index=False)
    
    def adjust_column_width(self, writer):
        """列幅を調整"""
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 60)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def run(self):
        """アプリケーション実行"""
        try:
            self.window.mainloop()
        except KeyboardInterrupt:
            self.logger.info("アプリケーションが中断されました")
        finally:
            self.cleanup_driver()
            self.logger.info("アプリケーション終了")

def main():
    """メイン関数"""
    try:
        app = GurunaviScraper()
        app.run()
    except Exception as e:
        logging.error(f"アプリケーション起動エラー: {e}")
        messagebox.showerror("起動エラー", f"アプリケーションの起動に失敗しました:\n{e}")

if __name__ == "__main__":
    main()