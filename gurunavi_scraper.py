"""
ぐるなび店舗情報スクレイピングツール v2.1 (要件対応完全版)
都道府県のおすすめ店舗から指定数を取得
取得項目: URL、店舗名、電話番号、住所、ジャンル、営業時間、定休日、クレジットカード、取得日時
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

class GurunaviURLGenerator:
    """ぐるなびURL自動生成クラス"""
    
    def __init__(self):
        self.base_url = "https://r.gnavi.co.jp"
        
        # 都道府県マッピング
        self.prefecture_map = {
            '北海道': 'hokkaido', '青森県': 'aomori', '岩手県': 'iwate',
            '宮城県': 'miyagi', '秋田県': 'akita', '山形県': 'yamagata',
            '福島県': 'fukushima', '茨城県': 'ibaraki', '栃木県': 'tochigi',
            '群馬県': 'gunma', '埼玉県': 'saitama', '千葉県': 'chiba',
            '東京都': 'tokyo', '神奈川県': 'kanagawa', '新潟県': 'niigata',
            '富山県': 'toyama', '石川県': 'ishikawa', '福井県': 'fukui',
            '山梨県': 'yamanashi', '長野県': 'nagano', '岐阜県': 'gifu',
            '静岡県': 'shizuoka', '愛知県': 'aichi', '三重県': 'mie',
            '滋賀県': 'shiga', '京都府': 'kyoto', '大阪府': 'osaka',
            '兵庫県': 'hyogo', '奈良県': 'nara', '和歌山県': 'wakayama',
            '鳥取県': 'tottori', '島根県': 'shimane', '岡山県': 'okayama',
            '広島県': 'hiroshima', '山口県': 'yamaguchi', '徳島県': 'tokushima',
            '香川県': 'kagawa', '愛媛県': 'ehime', '高知県': 'kochi',
            '福岡県': 'fukuoka', '佐賀県': 'saga', '長崎県': 'nagasaki',
            '熊本県': 'kumamoto', '大分県': 'oita', '宮崎県': 'miyazaki',
            '鹿児島県': 'kagoshima', '沖縄県': 'okinawa'
        }
        
        # 市区町村コードマッピング（主要都市）
        self.city_codes = {
            # 東京23区
            '千代田区': 'cwtav1010000', '中央区': 'cwtav1020000', '港区': 'cwtav1050000',
            '新宿区': 'cwtav1130000', '文京区': 'cwtav1140000', '台東区': 'cwtav1150000',
            '墨田区': 'cwtav1160000', '江東区': 'cwtav1170000', '品川区': 'cwtav1180000',
            '目黒区': 'cwtav1190000', '大田区': 'cwtav1210000', '世田谷区': 'cwtav1540000',
            '渋谷区': 'cwtav1510000', '中野区': 'cwtav1520000', '杉並区': 'cwtav1530000',
            '豊島区': 'cwtav1220000', '北区': 'cwtav1230000', '荒川区': 'cwtav1240000',
            '板橋区': 'cwtav1250000', '練馬区': 'cwtav1260000', '足立区': 'cwtav1200000',
            '葛飾区': 'cwtav1310000', '江戸川区': 'cwtav1320000',
            
            # 政令指定都市
            '札幌市中央区': 'cwtav0020000', '札幌市北区': 'cwtav0010000',
            '横浜市西区': 'cwtav2330000', '横浜市中区': 'cwtav2340000',
            '名古屋市中区': 'cwtav4560000', '名古屋市東区': 'cwtav4510000',
            '大阪市北区': 'cwtav5490000', '大阪市中央区': 'cwtav5500000',
            '福岡市中央区': 'cwtav8130000', '福岡市博多区': 'cwtav8120000'
        }
    
    def generate_prefecture_url(self, prefecture):
        """都道府県レベル検索URL生成"""
        if prefecture not in self.prefecture_map:
            raise ValueError(f"未対応の都道府県: {prefecture}")
        
        pref_code = self.prefecture_map[prefecture]
        return f"{self.base_url}/area/{pref_code}/rs/"
    
    def generate_city_url(self, prefecture, city):
        """市区町村レベル検索URL生成"""
        if prefecture not in self.prefecture_map:
            raise ValueError(f"未対応の都道府県: {prefecture}")
        
        pref_code = self.prefecture_map[prefecture]
        
        # 市区町村コードが登録されている場合
        if city in self.city_codes:
            city_code = self.city_codes[city]
            return f"{self.base_url}/city/{city_code}/rs/"
        
        # 未登録の場合はフリーワード検索
        from urllib.parse import urlencode
        params = {'fwp': city}
        query_string = urlencode(params)
        return f"{self.base_url}/area/{pref_code}/rs/?{query_string}"
    
    def get_supported_cities(self, prefecture):
        """指定都道府県でサポートされている市区町村を取得"""
        if prefecture == '東京都':
            return [city for city in self.city_codes.keys() if '区' in city and not any(x in city for x in ['市', '町', '村'])]
        elif prefecture in ['神奈川県']:
            return [city for city in self.city_codes.keys() if city.startswith('横浜市')]
        elif prefecture in ['愛知県']:
            return [city for city in self.city_codes.keys() if city.startswith('名古屋市')]
        elif prefecture in ['大阪府']:
            return [city for city in self.city_codes.keys() if city.startswith('大阪市')]
        elif prefecture in ['福岡県']:
            return [city for city in self.city_codes.keys() if city.startswith('福岡市')]
        elif prefecture in ['北海道']:
            return [city for city in self.city_codes.keys() if city.startswith('札幌市')]
        else:
            return []

class ChromeDriverFixer:
    """ChromeDriver修正クラス"""
    
    @staticmethod
    def fix_chromedriver():
        """ChromeDriverの完全修正"""
        print("=" * 50)
        print("ChromeDriver完全修正開始")
        print("=" * 50)
        
        try:
            # キャッシュクリア
            print("\n[1/4] 既存キャッシュクリア中...")
            wdm_path = Path.home() / ".wdm"
            if wdm_path.exists():
                shutil.rmtree(wdm_path, ignore_errors=True)
            
            # Chromeバージョン取得
            print("\n[2/4] Chromeバージョン確認中...")
            chrome_version = ChromeDriverFixer.get_chrome_version()
            if not chrome_version:
                chrome_version = "139.0.7258.154"
            
            # ダウンロード
            print("\n[3/4] ChromeDriverダウンロード中...")
            driver_path = ChromeDriverFixer.download_chromedriver(chrome_version)
            
            if driver_path:
                # ローカルにコピー
                print("\n[4/4] ローカルにコピー中...")
                local_path = Path.cwd() / "chromedriver.exe"
                shutil.copy2(driver_path, local_path)
                print(f"✅ 修正完了: {local_path}")
                return True
            else:
                print("❌ ダウンロード失敗")
                return False
                
        except Exception as e:
            print(f"❌ エラー: {e}")
            return False
    
    @staticmethod
    def get_chrome_version():
        """Chromeバージョン取得"""
        try:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    result = subprocess.run([chrome_path, "--version"], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip().split()[-1]
            return None
        except:
            return None
    
    @staticmethod
    def download_chromedriver(version):
        """ChromeDriverダウンロード"""
        try:
            major_version = version.split('.')[0]
            url = f"https://storage.googleapis.com/chrome-for-testing-public/{version}/win64/chromedriver-win64.zip"
            
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                return None
            
            temp_dir = Path.cwd() / "temp_chromedriver"
            temp_dir.mkdir(exist_ok=True)
            zip_path = temp_dir / "chromedriver.zip"
            
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            chromedriver_paths = list(temp_dir.rglob("chromedriver.exe"))
            if chromedriver_paths:
                return chromedriver_paths[0]
            return None
            
        except Exception as e:
            print(f"ダウンロードエラー: {e}")
            return None

class GurunaviScraper:
    """ぐるなびスクレイピングメインクラス"""
    
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("ぐるなびおすすめ店舗取得ツール v2.1")
        self.window.geometry("950x750")
        self.window.resizable(True, True)
        
        # 設定
        self.app_dir = Path.cwd()
        self.config_file = self.app_dir / "scraper_config.json"
        self.log_file = self.app_dir / "scraper.log"
        
        # 初期化
        self.default_save_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.is_scraping = False
        self.scraped_data = []
        self.driver = None
        
        # URL生成器
        self.url_generator = GurunaviURLGenerator()
        
        # ログ・設定
        self.setup_logging()
        self.load_config()
        
        self.setup_ui()
    
    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("アプリケーション開始 v2.1")
    
    def load_config(self):
        """設定読み込み"""
        default_config = {
            "last_save_path": self.default_save_path,
            "delay_min": 0.5,
            "delay_max": 1.0,
            "timeout": 15,
            "headless": True,
            "window_size": "1280,720",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "chromedriver_path": ""
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
        
        self.config = default_config
    
    def save_config(self):
        """設定保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
    
    def setup_ui(self):
        """UI設定"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # タイトル
        title_label = ttk.Label(main_frame, text="ぐるなびおすすめ店舗取得ツール v2.1", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # ステータス
        status_color = "green" if SELENIUM_AVAILABLE else "red"
        status_text = "Selenium: 利用可能" if SELENIUM_AVAILABLE else "Selenium: 利用不可"
        status_label = ttk.Label(main_frame, text=status_text, foreground=status_color)
        status_label.grid(row=1, column=0, columnspan=4, pady=(0, 10))
        
        # タブ
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.main_tab = ttk.Frame(notebook)
        self.config_tab = ttk.Frame(notebook)
        self.log_tab = ttk.Frame(notebook)
        
        notebook.add(self.main_tab, text="検索・実行")
        notebook.add(self.config_tab, text="設定")
        notebook.add(self.log_tab, text="ログ")
        
        self.setup_main_tab()
        self.setup_config_tab()
        self.setup_log_tab()
        
        # グリッド設定
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def setup_main_tab(self):
        """メインタブ設定"""
        # 検索条件
        search_frame = ttk.LabelFrame(self.main_tab, text="検索条件", padding="15")
        search_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # 都道府県
        ttk.Label(search_frame, text="都道府県:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.prefecture_var = tk.StringVar()
        self.prefecture_combo = ttk.Combobox(search_frame, textvariable=self.prefecture_var, width=18)
        self.prefecture_combo['values'] = self.get_prefecture_list()
        self.prefecture_combo.grid(row=0, column=1, padx=(0, 20))
        self.prefecture_combo.bind('<<ComboboxSelected>>', self.on_prefecture_changed)
        
        # 市区町村
        ttk.Label(search_frame, text="市区町村:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(search_frame, textvariable=self.city_var, width=18)
        self.city_combo.grid(row=0, column=3)
        
        # 取得件数
        ttk.Label(search_frame, text="取得店舗数:").grid(row=1, column=0, sticky=tk.W, pady=(15, 0), padx=(0, 10))
        self.max_count_var = tk.StringVar(value="30")
        max_count_spinbox = ttk.Spinbox(search_frame, textvariable=self.max_count_var, 
                                       from_=1, to=300, width=15)
        max_count_spinbox.grid(row=1, column=1, pady=(15, 0))
        
        # URL表示
        ttk.Label(search_frame, text="検索URL:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        self.url_var = tk.StringVar(value="都道府県を選択してください")
        url_display = ttk.Entry(search_frame, textvariable=self.url_var, width=60, state='readonly')
        url_display.grid(row=2, column=1, columnspan=3, pady=(10, 0), sticky=(tk.W, tk.E))
        
        # 保存設定
        save_frame = ttk.LabelFrame(self.main_tab, text="保存設定", padding="15")
        save_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(save_frame, text="保存先:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.save_path_var = tk.StringVar(value=self.config.get("last_save_path", self.default_save_path))
        self.save_path_entry = ttk.Entry(save_frame, textvariable=self.save_path_var, width=50)
        self.save_path_entry.grid(row=0, column=1, padx=(0, 10))
        ttk.Button(save_frame, text="参照", command=self.browse_save_path).grid(row=0, column=2)
        
        ttk.Label(save_frame, text="ファイル名:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0), padx=(0, 10))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename_var = tk.StringVar(value=f"gurunavi_recommend_{timestamp}")
        self.filename_entry = ttk.Entry(save_frame, textvariable=self.filename_var, width=50)
        self.filename_entry.grid(row=1, column=1, pady=(10, 0), padx=(0, 10))
        ttk.Label(save_frame, text=".xlsx").grid(row=1, column=2, pady=(10, 0))
        
        # 実行制御
        control_frame = ttk.Frame(self.main_tab)
        control_frame.grid(row=2, column=0, columnspan=4, pady=(0, 15))
        
        self.start_button = ttk.Button(control_frame, text="おすすめ店舗取得開始", 
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
        
        # プログレス・ステータス
        progress_frame = ttk.Frame(self.main_tab)
        progress_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(side=tk.LEFT, padx=(0, 15))
        
        status_info_frame = ttk.Frame(progress_frame)
        status_info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.status_var = tk.StringVar(value="準備完了")
        self.status_label = ttk.Label(status_info_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)
        
        self.count_var = tk.StringVar(value="取得件数: 0")
        self.count_label = ttk.Label(status_info_frame, textvariable=self.count_var)
        self.count_label.pack(anchor=tk.W)
        
        self.time_var = tk.StringVar(value="処理時間: 0秒")
        self.time_label = ttk.Label(status_info_frame, textvariable=self.time_var)
        self.time_label.pack(anchor=tk.W)
        
        # 結果表示
        result_frame = ttk.LabelFrame(self.main_tab, text="取得結果", padding="10")
        result_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        columns = ('No.', '店舗名', '電話番号', '住所', 'ジャンル', '営業時間')
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings', height=8)
        
        column_widths = {'No.': 50, '店舗名': 200, '電話番号': 120, '住所': 250, 'ジャンル': 100, '営業時間': 150}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        v_scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.main_tab.columnconfigure(3, weight=1)
        self.main_tab.rowconfigure(4, weight=1)
        search_frame.columnconfigure(3, weight=1)
    
    def setup_config_tab(self):
        """設定タブ設定"""
        # Chrome設定
        chrome_frame = ttk.LabelFrame(self.config_tab, text="Chrome設定", padding="15")
        chrome_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.headless_var = tk.BooleanVar(value=self.config.get("headless", True))
        ttk.Checkbutton(chrome_frame, text="ヘッドレスモード", 
                       variable=self.headless_var).grid(row=0, column=0, sticky=tk.W)
        
        # ChromeDriver修正ボタン
        ttk.Button(chrome_frame, text="ChromeDriver修正", command=self.fix_chromedriver).grid(row=1, column=0, pady=(10, 0))
        
        # 設定保存
        ttk.Button(self.config_tab, text="設定保存", command=self.save_current_config).grid(row=1, column=0, pady=(15, 0))
    
    def setup_log_tab(self):
        """ログタブ設定"""
        log_frame = ttk.Frame(self.log_tab)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=20)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ログ更新
        self.update_log_display()
    
    def get_prefecture_list(self):
        """都道府県リスト"""
        return [
            '', '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
            '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
            '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
            '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
    
    def on_prefecture_changed(self, event):
        """都道府県変更時処理"""
        prefecture = self.prefecture_var.get()
        
        # 市区町村更新
        supported_cities = self.url_generator.get_supported_cities(prefecture)
        self.city_combo['values'] = [''] + supported_cities
        self.city_var.set('')
        
        # URL更新
        self.update_search_url()
    
    def update_search_url(self):
        """検索URL更新"""
        try:
            prefecture = self.prefecture_var.get()
            city = self.city_var.get()
            
            if not prefecture:
                self.url_var.set("都道府県を選択してください")
                return
            
            if city:
                url = self.url_generator.generate_city_url(prefecture, city)
            else:
                url = self.url_generator.generate_prefecture_url(prefecture)
            
            self.url_var.set(url)
            
        except Exception as e:
            pass
    
    def browse_save_path(self):
        """保存先選択"""
        folder_path = filedialog.askdirectory(initialdir=self.save_path_var.get())
        if folder_path:
            self.save_path_var.set(folder_path)
    
    def fix_chromedriver(self):
        """ChromeDriver修正"""
        result = messagebox.askyesno("ChromeDriver修正", "ChromeDriverを修正しますか？")
        
        if result:
            try:
                self.status_var.set("ChromeDriver修正中...")
                self.window.update()
                
                success = ChromeDriverFixer.fix_chromedriver()
                
                if success:
                    messagebox.showinfo("修正完了", "ChromeDriverの修正が完了しました。")
                else:
                    messagebox.showerror("修正失敗", "ChromeDriverの修正に失敗しました。")
                    
            except Exception as e:
                messagebox.showerror("エラー", f"修正中にエラーが発生しました:\n{e}")
            finally:
                self.status_var.set("準備完了")
    
    def save_current_config(self):
        """現在設定保存"""
        try:
            self.config.update({
                "last_save_path": self.save_path_var.get(),
                "headless": self.headless_var.get()
            })
            self.save_config()
            messagebox.showinfo("設定保存", "設定が保存されました。")
        except Exception as e:
            messagebox.showerror("設定エラー", f"設定保存エラー: {e}")
    
    def update_log_display(self):
        """ログ表示更新"""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, log_content)
                self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"ログ読み込みエラー: {e}\n")
    
    def start_scraping(self):
        """スクレイピング開始"""
        if not self.validate_inputs():
            return
        
        self.set_scraping_state(True)
        self.scraped_data = []
        self.clear_results()
        
        # スレッドで実行
        thread = threading.Thread(target=self.scrape_worker)
        thread.daemon = True
        thread.start()
    
    def validate_inputs(self):
        """入力値検証"""
        if not self.prefecture_var.get():
            messagebox.showerror("エラー", "都道府県を選択してください。")
            return False
        
        try:
            max_count = int(self.max_count_var.get())
            if max_count <= 0 or max_count > 300:
                raise ValueError
        except ValueError:
            messagebox.showerror("エラー", "取得店舗数は1-300の範囲で入力してください。")
            return False
        
        if not self.filename_var.get().strip():
            messagebox.showerror("エラー", "ファイル名を入力してください。")
            return False
        
        if not SELENIUM_AVAILABLE:
            messagebox.showerror("エラー", "Seleniumが利用できません。")
            return False
        
        return True
    
    def set_scraping_state(self, is_scraping):
        """スクレイピング状態制御"""
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
        self.logger.info("スクレイピング停止")
    
    def clear_results(self):
        """結果クリア"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.scraped_data = []
        self.count_var.set("取得件数: 0")
        self.progress_var.set(0)
    
    def manual_export(self):
        """手動エクスポート"""
        self.save_to_excel()
    
    def scrape_worker(self):
        """スクレイピングワーカー"""
        start_time = time.time()
        try:
            self.logger.info("おすすめ店舗取得開始")
            self.status_var.set("初期化中...")
            
            if not self.setup_driver():
                return
            
            max_count = int(self.max_count_var.get())
            prefecture = self.prefecture_var.get()
            
            self.perform_scraping(max_count)
            
            if self.is_scraping:
                self.save_to_excel()
                elapsed_time = time.time() - start_time
                self.time_var.set(f"処理時間: {elapsed_time:.1f}秒")
                self.status_var.set(f"完了: {len(self.scraped_data)}件取得")
                
                messagebox.showinfo("完了", 
                    f"【{prefecture}のおすすめ店舗取得完了】\n\n"
                    f"取得件数: {len(self.scraped_data)}件\n"
                    f"処理時間: {elapsed_time:.1f}秒\n\n"
                    f"Excelファイルに保存されました。")
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.time_var.set(f"エラー時間: {elapsed_time:.1f}秒")
            self.logger.error(f"スクレイピングエラー: {e}")
            messagebox.showerror("エラー", f"エラーが発生しました:\n{str(e)}")
        finally:
            self.cleanup_driver()
            self.set_scraping_state(False)
    
    def setup_driver(self):
        """ドライバー設定"""
        try:
            chrome_options = Options()
            
            if self.config.get("headless", True):
                chrome_options.add_argument("--headless")
            
            # 高速化オプション
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--ignore-ssl-errors")
            chrome_options.add_argument("--ignore-certificate-errors")
            
            window_size = self.config.get("window_size", "1280,720")
            chrome_options.add_argument(f"--window-size={window_size}")
            
            user_agent = self.config.get("user_agent", "")
            if user_agent:
                chrome_options.add_argument(f"--user-agent={user_agent}")
            
            driver_path = self.get_chromedriver_path()
            if not driver_path:
                raise Exception("ChromeDriverが見つかりません。")
            
            service = Service(driver_path, log_path='nul')
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(20)
            
            self.logger.info("Webドライバー初期化完了")
            return True
            
        except Exception as e:
            self.logger.error(f"ドライバー初期化エラー: {e}")
            messagebox.showerror("エラー", f"ブラウザドライバー初期化失敗:\n{e}")
            return False
    
    def get_chromedriver_path(self):
        """ChromeDriverパス取得"""
        # ローカル
        local_driver = Path.cwd() / "chromedriver.exe"
        if local_driver.exists():
            return str(local_driver)
        
        # 設定ファイル
        config_path = self.config.get("chromedriver_path", "")
        if config_path and Path(config_path).exists():
            return config_path
        
        # webdriver-manager
        if WEBDRIVER_MANAGER_AVAILABLE:
            try:
                return ChromeDriverManager().install()
            except:
                pass
        
        return None
    
    def cleanup_driver(self):
        """ドライバークリーンアップ"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
    
    def perform_scraping(self, max_count):
        """スクレイピング実行"""
        try:
            prefecture = self.prefecture_var.get()
            city = self.city_var.get()
            
            if city:
                search_url = self.url_generator.generate_city_url(prefecture, city)
                search_target = f"{prefecture} {city}"
            else:
                search_url = self.url_generator.generate_prefecture_url(prefecture)
                search_target = prefecture
            
            self.logger.info(f"検索URL: {search_url}")
            self.logger.info(f"目標取得数: {max_count}件")
            
            self.status_var.set(f"{search_target}のおすすめ店舗にアクセス中...")
            
            start_time = time.time()
            self.driver.get(search_url)
            
            # ページ読み込み待機
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            collected_count = 0
            page_num = 1
            
            while self.is_scraping and collected_count < max_count:
                self.status_var.set(f"ページ {page_num} 処理中... ({collected_count}/{max_count})")
                self.logger.info(f"ページ {page_num} 処理開始")
                
                # 店舗リンク抽出
                store_links = self.extract_store_links()
                
                if not store_links:
                    self.logger.info("店舗リンクが見つかりません")
                    if self.has_next_page() and page_num < 10:
                        self.go_to_next_page()
                        page_num += 1
                        time.sleep(2)
                        continue
                    else:
                        break
                
                self.logger.info(f"ページ {page_num} で {len(store_links)} 件発見")
                
                # 各店舗の詳細取得
                for i, link in enumerate(store_links):
                    if not self.is_scraping or collected_count >= max_count:
                        break
                    
                    self.status_var.set(f"店舗 {i+1}/{len(store_links)} 処理中...")
                    
                    store_data = self.scrape_store_detail(link)
                    if store_data:
                        collected_count += 1
                        self.scraped_data.append(store_data)
                        
                        self.update_result_display(store_data, collected_count)
                        
                        progress = min((collected_count / max_count) * 100, 100)
                        self.progress_var.set(progress)
                        self.count_var.set(f"取得件数: {collected_count}")
                        
                        elapsed_time = time.time() - start_time
                        self.time_var.set(f"処理時間: {elapsed_time:.1f}秒")
                        
                        self.window.update_idletasks()
                    
                    # 待機
                    self.smart_delay()
                
                # 目標達成チェック
                if collected_count >= max_count:
                    break
                
                # 次ページ移動
                if self.has_next_page() and page_num < 10:
                    self.logger.info("次ページに移動")
                    self.go_to_next_page()
                    page_num += 1
                    time.sleep(2)
                else:
                    break
            
            total_time = time.time() - start_time
            self.logger.info(f"取得完了: {collected_count}件 (時間: {total_time:.2f}秒)")
            
        except Exception as e:
            self.logger.error(f"スクレイピングエラー: {e}")
            raise
    
    def extract_store_links(self):
        """店舗リンク抽出"""
        try:
            selectors = [
                "a[href*='r.gnavi.co.jp/'][href*='/']",
                ".shop-info a",
                ".restaurant-item a",
                ".shop-list a",
                ".shop-name a",
                "li a[href*='r.gnavi.co.jp']"
            ]
            
            links = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and self.is_valid_store_url(href):
                            if href not in links:
                                links.append(href)
                                if len(links) >= 30:
                                    break
                except:
                    continue
                
                if len(links) >= 30:
                    break
            
            self.logger.info(f"店舗リンク抽出: {len(links)} 件")
            return links
            
        except Exception as e:
            self.logger.error(f"店舗リンク抽出エラー: {e}")
            return []
    
    def is_valid_store_url(self, url):
        """有効店舗URLチェック"""
        if not url:
            return False
        
        # 除外パターン
        exclude_patterns = ['/rs/', '/area/', '/search', '/guide', '/api/']
        for pattern in exclude_patterns:
            if pattern in url:
                return False
        
        # 有効パターン
        valid_patterns = [
            r'r\.gnavi\.co\.jp/[a-zA-Z0-9]+/?',
            r'r\.gnavi\.co\.jp/[a-zA-Z0-9]+/[a-zA-Z0-9]*/?'
        ]
        
        return any(re.search(pattern, url) for pattern in valid_patterns)
    
    def scrape_store_detail(self, url):
        """店舗詳細取得"""
        try:
            self.logger.debug(f"店舗詳細取得: {url}")
            
            self.driver.get(url)
            time.sleep(0.5)
            
            # 要件に合わせた9項目を取得
            store_data = {
                'URL': url,
                '店舗名': self.extract_text(['h1', '.shop-name', '.restaurant-name']),
                '電話番号': self.extract_phone_number(),
                '住所': self.extract_text(['.address', '.shop-address', '[class*="address"]']),
                'ジャンル': self.extract_text(['.genre', '.category', '[class*="genre"]']),
                '営業時間': self.extract_text(['.business-hours', '.opening-hours', '[class*="hours"]']),
                '定休日': self.extract_text(['.holiday', '.closed', '[class*="holiday"]']),
                'クレジットカード': self.extract_text(['.credit-card', '[class*="credit"]', '[class*="card"]']),
                '取得日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 空の場合は「-」を設定
            for key, value in store_data.items():
                if key in ['URL', '取得日時']:
                    continue
                if not value or (isinstance(value, str) and not value.strip()):
                    store_data[key] = '-'
                elif isinstance(value, str):
                    store_data[key] = value.strip()
            
            self.logger.debug(f"取得完了: {store_data.get('店舗名', '-')}")
            return store_data
            
        except Exception as e:
            self.logger.warning(f"店舗詳細取得エラー ({url}): {e}")
            # エラー時も基本構造を返す
            return {
                'URL': url,
                '店舗名': '-',
                '電話番号': '-',
                '住所': '-',
                'ジャンル': '-',
                '営業時間': '-',
                '定休日': '-',
                'クレジットカード': '-',
                '取得日時': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def extract_phone_number(self):
        """電話番号抽出"""
        selectors = ['a[href^="tel:"]', '.phone', '.tel', '[class*="phone"]']
        text = self.extract_text(selectors)
        if text:
            phone_match = re.search(r'(\d{2,4}[-\s]?\d{2,4}[-\s]?\d{4})', text)
            if phone_match:
                return phone_match.group(1)
        return text
    
    def extract_text(self, selectors):
        """テキスト抽出"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
                text = element.get_attribute('textContent')
                if text and text.strip():
                    return text.strip()
            except:
                continue
        return ''
    
    def has_next_page(self):
        """次ページ存在チェック"""
        try:
            selectors = ["a[class*='next']", ".pager_next a", ".next a"]
            for selector in selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_enabled():
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def go_to_next_page(self):
        """次ページ移動"""
        try:
            selectors = ["a[class*='next']", ".pager_next a", ".next a"]
            for selector in selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)
                        return True
                except:
                    continue
            return False
        except:
            return False
    
    def smart_delay(self):
        """遅延制御"""
        delay = random.uniform(0.5, 1.0)
        time.sleep(delay)
    
    def update_result_display(self, store_data, count):
        """結果表示更新"""
        self.tree.insert('', 'end', values=(
            count,
            store_data.get('店舗名', '-'),
            store_data.get('電話番号', '-'),
            store_data.get('住所', '-'),
            store_data.get('ジャンル', '-'),
            store_data.get('営業時間', '-')
        ))
        
        if count % 5 == 0:  # 5件ごとにスクロール
            children = self.tree.get_children()
            if children:
                self.tree.see(children[-1])
    
    def save_to_excel(self):
        """Excel保存"""
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
                df.to_excel(writer, sheet_name='おすすめ店舗データ', index=False)
                
                # 統計シート
                prefecture = self.prefecture_var.get()
                stats_data = {
                    '項目': [
                        '対象都道府県',
                        '総取得件数', 
                        '店舗名あり', 
                        '電話番号あり', 
                        '住所あり',
                        'ジャンルあり',
                        '営業時間あり',
                        'クレジットカード情報あり'
                    ],
                    '値': [
                        prefecture,
                        len(df),
                        (df['店舗名'] != '-').sum(),
                        (df['電話番号'] != '-').sum(),
                        (df['住所'] != '-').sum(),
                        (df['ジャンル'] != '-').sum(),
                        (df['営業時間'] != '-').sum(),
                        (df['クレジットカード'] != '-').sum()
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='取得統計', index=False)
                
                # 概要シート
                summary_data = {
                    '設定項目': ['検索対象', '検索URL', '取得店舗数', '取得日時'],
                    '内容': [
                        f"{prefecture}のおすすめ店舗",
                        f"https://r.gnavi.co.jp/area/{self.url_generator.prefecture_map.get(prefecture, '')}/rs/",
                        f"{len(df)}件",
                        datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='取得概要', index=False)
                
                # 列幅調整
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
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            self.config["last_save_path"] = save_path
            self.save_config()
            
            self.logger.info(f"Excel保存完了: {full_path}")
            
        except Exception as e:
            self.logger.error(f"Excel保存エラー: {e}")
            messagebox.showerror("保存エラー", f"ファイル保存エラー:\n{str(e)}")
    
    def run(self):
        """アプリケーション実行"""
        try:
            # 初期URL更新
            self.city_combo.bind('<<ComboboxSelected>>', lambda e: self.update_search_url())
            self.update_search_url()
            
            self.window.mainloop()
        except KeyboardInterrupt:
            self.logger.info("アプリケーション中断")
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
        messagebox.showerror("起動エラー", f"アプリケーション起動失敗:\n{e}")

if __name__ == "__main__":
    main()