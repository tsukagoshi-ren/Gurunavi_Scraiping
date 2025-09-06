# deploy.py - 自動デプロイメントスクリプト
import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile

def run_command(command, check=True):
    """コマンドを実行"""
    print(f"実行中: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"エラー: {e}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def create_deployment_package():
    """デプロイメントパッケージを作成"""
    print("=" * 50)
    print("ぐるなびスクレイピングツール デプロイメント")
    print("=" * 50)
    
    # 作業ディレクトリ
    work_dir = Path("deployment_work")
    work_dir.mkdir(exist_ok=True)
    
    # ステップ1: 仮想環境作成
    print("\n[1/8] 仮想環境を作成中...")
    if not run_command(f"python -m venv {work_dir}/venv"):
        print("仮想環境の作成に失敗しました")
        return False
    
    # ステップ2: 依存関係インストール
    print("\n[2/8] 依存関係をインストール中...")
    venv_python = work_dir / "venv" / "Scripts" / "python.exe"
    venv_pip = work_dir / "venv" / "Scripts" / "pip.exe"
    
    if not run_command(f'"{venv_pip}" install --upgrade pip'):
        print("pipのアップグレードに失敗しました")
        return False
    
    if not run_command(f'"{venv_pip}" install -r requirements_full.txt'):
        print("依存関係のインストールに失敗しました")
        return False
    
    # ステップ3: ChromeDriverセットアップ
    print("\n[3/8] ChromeDriverをセットアップ中...")
    if not run_command(f'"{venv_python}" chromedriver_setup.py'):
        print("ChromeDriverのセットアップに失敗しました")
        return False
    
    # ステップ4: PyInstallerでexe化
    print("\n[4/8] アプリケーションをexe化中...")
    pyinstaller_cmd = f'''"{work_dir}/venv/Scripts/pyinstaller.exe" ^
        --clean ^
        --onefile ^
        --windowed ^
        --name="GurunaviScraperPro" ^
        --icon=app.ico ^
        --add-data "scraper_config.json;." ^
        --hidden-import=selenium.webdriver.chrome.service ^
        --hidden-import=selenium.webdriver.common.keys ^
        --hidden-import=webdriver_manager.chrome ^
        --hidden-import=openpyxl ^
        --exclude-module=matplotlib ^
        --exclude-module=numpy ^
        production_ready_scraper.py'''
    
    if not run_command(pyinstaller_cmd):
        print("exe化に失敗しました")
        return False
    
    # ステップ5: 配布フォルダ作成
    print("\n[5/8] 配布パッケージを作成中...")
    dist_dir = Path("GurunaviScraper_Distribution")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()
    
    # ファイルをコピー
    files_to_copy = [
        ("dist/GurunaviScraperPro.exe", "GurunaviScraperPro.exe"),
        ("scraper_config.json", "scraper_config.json"),
        ("使用方法.txt", "使用方法.txt"),
        ("README.md", "README.md")
    ]
    
    for src, dst in files_to_copy:
        if Path(src).exists():
            shutil.copy2(src, dist_dir / dst)
    
    # ステップ6: バッチファイル作成
    print("\n[6/8] 実行用バッチファイルを作成中...")
    with open(dist_dir / "スクレイピングツール実行.bat", "w", encoding="shift_jis") as f:
        f.write("""@echo off
title ぐるなびスクレイピングツール
cd /d "%~dp0"
echo ぐるなびスクレイピングツールを起動中...
start GurunaviScraperPro.exe
""")
    
    # ステップ7: ドキュメント作成
    print("\n[7/8] ドキュメントを作成中...")
    create_user_manual(dist_dir)
    create_technical_manual(dist_dir)
    
    # ステップ8: ZIP圧縮
    print("\n[8/8] 最終パッケージを作成中...")
    zip_name = "GurunaviScraper_Professional_v2.0.zip"
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in dist_dir.rglob("*"):
            if file.is_file():
                zipf.write(file, file.relative_to(dist_dir))
    
    print(f"\n✅ デプロイメント完了!")
    print(f"📦 パッケージ: {zip_name}")
    print(f"📁 展開先: {dist_dir}")
    print(f"🚀 実行方法: 「スクレイピングツール実行.bat」をダブルクリック")
    
    return True

def create_user_manual(dist_dir):
    """ユーザーマニュアルを作成"""
    manual_content = """
=====================================
ぐるなび店舗情報スクレイピングツール
        Professional v2.0
         ユーザーマニュアル
=====================================

■ 概要
このツールは、日本最大級のグルメサイト「ぐるなび」から
店舗情報を効率的に収集するための専用アプリケーションです。

■ 動作環境
- OS: Windows 10/11 (64bit)
- RAM: 4GB以上推奨
- HDD: 1GB以上の空き容量
- インターネット接続: 必須
- Google Chrome: 最新版推奨

■ インストール方法
1. ZIPファイルを適当なフォルダに展開
2. 「スクレイピングツール実行.bat」をダブルクリック
3. 初回起動時にChromeDriverが自動インストールされます

■ 基本操作
【検索条件設定】
1. 「検索・実行」タブを選択
2. 以下の条件を設定:
   - 都道府県: 必須（プルダウンから選択）
   - 市区町村: 任意（詳細地域指定）
   - ジャンル: 任意（料理カテゴリ）
   - 最寄り駅: 任意（駅名）
   - キーワード: 任意（自由検索語）
   - 最大件数: 1-1000件（推奨: 100件以下）

【保存設定】
- 保存先: デフォルトはダウンロードフォルダ
- ファイル名: 自動で日時が付与されます

【実行】
1. 「スクレイピング開始」ボタンをクリック
2. 進行状況を確認
3. 完了後、Excelファイルが保存されます

■ 取得できる情報
- 店舗名          - 営業時間
- 電話番号        - 定休日
- 住所           - 座席数
- ジャンル        - 予算
- 最寄り駅        - 個室情報
- 駐車場情報      - 禁煙・喫煙
- クレジットカード対応

■ 詳細設定
「詳細設定」タブで以下を調整可能:

【ブラウザ設定】
- ヘッドレスモード: ON推奨（処理高速化）
- ウィンドウサイズ: デフォルト1920x1080

【アクセス制御】
- 最小間隔: 2秒（サーバー負荷軽減）
- 最大間隔: 5秒
- タイムアウト: 15秒
- 暗黙的待機: 10秒

■ トラブルシューティング

【起動しない場合】
- Windows Defenderの除外設定を確認
- 管理者権限で実行
- Chromeブラウザを最新版に更新

【取得できない場合】
- インターネット接続を確認
- ファイアウォール設定を確認
- 検索条件を変更して再試行
- 「ChromeDriver更新」ボタンを実行

【動作が重い場合】
- 最大取得件数を50件以下に設定
- 他のアプリケーションを終了
- PCを再起動

【エラーが発生した場合】
- 「ログ」タブでエラー内容を確認
- アプリを再起動
- 設定をデフォルトに戻す

■ 注意事項
⚠️ 重要: 利用規約と法律の遵守
- 取得したデータの商用利用は慎重に検討してください
- 大量アクセスによるサーバー負荷を避けてください
- 個人情報の取り扱いには十分注意してください
- 著作権法、個人情報保護法等を遵守してください

⚠️ 技術的注意事項
- 一度に大量のデータを取得すると時間がかかります
- ネットワーク環境により取得速度が変わります
- サイト仕様変更により動作しない場合があります

■ ライセンス
このソフトウェアは教育・研究目的での使用を想定しています。
商用利用については開発者までお問い合わせください。

■ サポート
- バグ報告: 開発者までご連絡ください
- 機能要望: GitHubのIssuesをご利用ください
- 技術サポート: 有償サポートも承ります

=====================================
© 2024 Gurunavi Scraper Project
Version 2.0 Professional Edition
=====================================
"""
    
    with open(dist_dir / "ユーザーマニュアル.txt", "w", encoding="utf-8") as f:
        f.write(manual_content)

def create_technical_manual(dist_dir):
    """技術マニュアルを作成"""
    tech_content = """
=====================================
ぐるなびスクレイピングツール v2.0
        技術仕様書
=====================================

■ アーキテクチャ概要
- 言語: Python 3.8+
- GUI Framework: tkinter
- Web Automation: Selenium WebDriver
- HTTP Client: requests + BeautifulSoup4
- Data Processing: pandas
- Excel Output: openpyxl
- Packaging: PyInstaller

■ 主要コンポーネント

【ProductionGurunaviScraper クラス】
- メインアプリケーションクラス
- GUI管理とイベント処理
- 設定管理とログ機能

【スクレイピングエンジン】
- Selenium-based automation
- 動的コンテンツ対応
- エラーハンドリング
- レート制限機能

【データ処理パイプライン】
1. URL構築
2. ページナビゲーション
3. 要素抽出
4. データクリーニング
5. Excel出力

■ 設定ファイル (scraper_config.json)
```json
{
  "last_save_path": "C:/Users/Username/Downloads",
  "delay_min": 2.0,
  "delay_max": 5.0,
  "timeout": 15,
  "headless": true,
  "window_size": "1920,1080",
  "user_agent": "Mozilla/5.0...",
  "max_retries": 3,
  "implicit_wait": 10,
  "page_load_timeout": 30
}
```

■ 抽出セレクタ定義
【店舗名】
- h1.shop-name
- h1[class*="name"]
- .restaurant-name h1

【電話番号】
- a[href^="tel:"]
- .phone, .tel
- [class*="phone"]

【住所】
- .address
- .shop-address
- [class*="address"]

■ エラーハンドリング
- NoSuchElementException: 要素が見つからない
- TimeoutException: ページ読み込みタイムアウト
- WebDriverException: ブラウザエラー
- 自動リトライ機能搭載

■ パフォーマンス最適化
- ヘッドレスブラウザ使用
- 画像・JavaScript無効化オプション
- 適応的遅延制御
- メモリ効率的なデータ処理

■ セキュリティ対策
- User-Agent ローテーション
- リクエスト間隔ランダム化
- IP制限回避機能
- robots.txt 準拠チェック

■ ログ機能
- レベル別ログ出力 (INFO, WARNING, ERROR)
- ファイルとコンソール同時出力
- 日本語対応
- エラートレースバック記録

■ Excel出力仕様
【シート構成】
1. 店舗データ: 全取得データ
2. 統計情報: データ品質統計
3. ジャンル別集計: カテゴリ分析
4. エリア別集計: 地域分析

【列幅自動調整】
- 最大60文字まで
- 内容に応じて動的調整

■ 拡張性
- プラグインアーキテクチャ対応
- 新サイト対応容易
- カスタムセレクタ追加可能
- 出力フォーマット拡張可能

■ 依存関係
```
requests==2.31.0
beautifulsoup4==4.12.2
pandas==2.0.3
openpyxl==3.1.2
selenium==4.15.0
webdriver-manager==4.0.1
```

■ ビルド環境
- Python 3.8-3.11
- PyInstaller 5.13.0
- Windows 10/11 SDK

■ デプロイメント
```bash
# 1. 環境構築
python -m venv venv
venv\Scripts\activate
pip install -r requirements_full.txt

# 2. exe化
pyinstaller production_ready_scraper.spec

# 3. パッケージング
python deploy.py
```

■ カスタマイズ方法
【新しいサイト対応】
1. extract_*メソッドの実装
2. セレクタ定義の追加
3. URL構築ロジックの修正

【新しい出力形式】
1. save_to_*メソッドの追加
2. UI要素の追加
3. 設定項目の拡張

■ パフォーマンスチューニング
【推奨設定（高速）】
- headless: true
- disable-images: true
- page_load_timeout: 20
- delay_min: 1.0

【推奨設定（安定）】
- headless: false
- delay_min: 3.0
- max_retries: 5
- implicit_wait: 15

■ 開発者向け情報
- GitHub: [リポジトリURL]
- Issues: バグ報告・機能要望
- Wiki: 詳細ドキュメント
- API Reference: コード内docstring参照

=====================================
"""
    
    with open(dist_dir / "技術仕様書.txt", "w", encoding="utf-8") as f:
        f.write(tech_content)

if __name__ == "__main__":
    if create_deployment_package():
        print("\n🎉 デプロイメント成功!")
        input("Enterキーを押して終了...")
    else:
        print("\n❌ デプロイメント失敗")
        input("Enterキーを押して終了...")

# installer_wizard.py - インストールウィザード
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import sys
from pathlib import Path
import shutil

class InstallWizard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ぐるなびスクレイピングツール インストールウィザード")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        self.install_dir = Path.home() / "GurunaviScraper"
        self.create_desktop_shortcut = tk.BooleanVar(value=True)
        self.create_start_menu = tk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # タイトル
        title_label = ttk.Label(main_frame, text="ぐるなびスクレイピングツール", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(main_frame, text="Professional Edition v2.0 インストールウィザード",
                                  font=('Arial', 10))
        subtitle_label.pack(pady=(0, 20))
        
        # インストール先選択
        install_frame = ttk.LabelFrame(main_frame, text="インストール先", padding="10")
        install_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.install_path_var = tk.StringVar(value=str(self.install_dir))
        path_entry = ttk.Entry(install_frame, textvariable=self.install_path_var, width=60)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        ttk.Button(install_frame, text="参照", command=self.browse_install_dir).pack(side=tk.RIGHT)
        
        # オプション
        options_frame = ttk.LabelFrame(main_frame, text="インストールオプション", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Checkbutton(options_frame, text="デスクトップにショートカットを作成",
                       variable=self.create_desktop_shortcut).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="スタートメニューに追加",
                       variable=self.create_start_menu).pack(anchor=tk.W, pady=(5, 0))
        
        # プログレスバー
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(15, 10))
        
        # ステータス
        self.status_var = tk.StringVar(value="インストール準備完了")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack()
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.install_button = ttk.Button(button_frame, text="インストール", 
                                        command=self.start_install)
        self.install_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        ttk.Button(button_frame, text="キャンセル", 
                  command=self.root.quit).pack(side=tk.RIGHT)
    
    def browse_install_dir(self):
        dir_path = filedialog.askdirectory(initialdir=self.install_path_var.get())
        if dir_path:
            self.install_path_var.set(dir_path)
    
    def start_install(self):
        try:
            self.install_button.config(state='disabled')
            self.install_dir = Path(self.install_path_var.get())
            
            # ステップ1: ディレクトリ作成
            self.status_var.set("インストールディレクトリを作成中...")
            self.progress['value'] = 20
            self.root.update()
            
            self.install_dir.mkdir(parents=True, exist_ok=True)
            
            # ステップ2: ファイルコピー
            self.status_var.set("ファイルをコピー中...")
            self.progress['value'] = 40
            self.root.update()
            
            # 実行ファイルとリソースをコピー
            files_to_copy = [
                "GurunaviScraperPro.exe",
                "scraper_config.json",
                "ユーザーマニュアル.txt",
                "技術仕様書.txt"
            ]
            
            for file in files_to_copy:
                if Path(file).exists():
                    shutil.copy2(file, self.install_dir / file)
            
            # ステップ3: ショートカット作成
            self.status_var.set("ショートカットを作成中...")
            self.progress['value'] = 60
            self.root.update()
            
            if self.create_desktop_shortcut.get():
                self.create_shortcut("desktop")
            
            if self.create_start_menu.get():
                self.create_shortcut("start_menu")
            
            # ステップ4: 完了
            self.progress['value'] = 100
            self.status_var.set("インストール完了!")
            self.root.update()
            
            messagebox.showinfo("完了", f"インストールが完了しました!\n\nインストール先:\n{self.install_dir}")
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("エラー", f"インストール中にエラーが発生しました:\n{e}")
            self.install_button.config(state='normal')
    
    def create_shortcut(self, location):
        """ショートカットを作成"""
        try:
            if location == "desktop":
                desktop = Path.home() / "Desktop"
                shortcut_path = desktop / "ぐるなびスクレイピングツール.lnk"
            else:  # start_menu
                start_menu = Path.home() / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs"
                shortcut_path = start_menu / "ぐるなびスクレイピングツール.lnk"
            
            # PowerShellスクリプトでショートカット作成
            ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{self.install_dir / 'GurunaviScraperPro.exe'}"
$Shortcut.WorkingDirectory = "{self.install_dir}"
$Shortcut.Description = "ぐるなび店舗情報スクレイピングツール"
$Shortcut.Save()
'''
            
            subprocess.run(["powershell", "-Command", ps_script], 
                          capture_output=True, text=True)
            
        except Exception as e:
            print(f"ショートカット作成エラー: {e}")
    
    def run(self):
        self.root.mainloop()

# requirements_full.txt - 完全版依存関係
"""
# Core dependencies
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3

# Data processing
pandas==2.0.3
openpyxl==3.1.2

# Web automation
selenium==4.15.0
webdriver-manager==4.0.1

# Packaging
pyinstaller==5.13.0

# Optional dependencies
Pillow==10.0.0  # For image processing if needed
python-dateutil==2.8.2  # For date parsing
urllib3==2.0.4  # HTTP library
certifi==2023.7.22  # SSL certificates
"""

# final_build.bat - 最終ビルドスクリプト
"""
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
"""