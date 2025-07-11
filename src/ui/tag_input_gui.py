#!/usr/bin/env python3
"""
Instagram ハッシュタグスクレイパー GUI
tkinterを使用した非エンジニア向けインターフェース
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import os
from pathlib import Path
from datetime import datetime
import sys

# バージョン情報
VERSION = "v3.0.0"

# パッケージのインポートパスを設定
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from scraper.fetch_tag import fetch_hashtag_data
    from scraper.data_manager import DataManager
    from scraper.utils import setup_logger
except ImportError as e:
    print(f"⚠️ モジュールのインポートに失敗しました: {e}")
    print("仮想環境がアクティベートされていることを確認してください")


class InstagramScraperGUI:
    """Instagram スクレイパー GUI アプリケーション"""
    
    def __init__(self, root):
        """
        GUI初期化
        
        Args:
            root: tkinter のルートウィンドウ
        """
        self.root = root
        self.data_manager = DataManager()
        self.logger = setup_logger("gui")
        
        # GUI設定
        self.setup_window()
        self.create_widgets()
        
        # 実行状態管理
        self.is_running = False
        self.current_thread = None
        
        # 時間管理
        self.start_time = None
        self.last_update_time = None
        self.time_update_job = None
        
    def setup_window(self):
        """ウィンドウの基本設定"""
        self.root.title("Instagram ハッシュタグスクレイパー v1.0")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # アイコン設定（オプション）
        try:
            # 将来的にアイコンファイルを追加する場合
            # self.root.iconbitmap("icon.ico")
            pass
        except:
            pass
        
        # 終了時の処理設定
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        """ウィジェットの作成"""
        # タブノートブック作成
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # メインタブ
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="メイン")
        
        # 統計タブ
        self.stats_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_tab, text="統計情報")
        
        # 詳細タブ
        self.details_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.details_tab, text="詳細情報")
        
        # メインタブの内容を作成
        self.create_main_tab_content()
        
        # 統計タブの内容を作成
        self.create_stats_tab_content()
        
        # 詳細タブの内容を作成
        self.create_details_tab_content()
        
    def create_main_tab_content(self):
        """メインタブの内容を作成"""
        # メインフレーム
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.main_tab.columnconfigure(0, weight=1)
        self.main_tab.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # タイトル
        title_label = ttk.Label(
            main_frame, 
            text="Instagram ハッシュタグスクレイパー",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # ハッシュタグ入力セクション
        self.create_input_section(main_frame)
        
        # オプション設定セクション
        self.create_options_section(main_frame)
        
        # 実行ボタンセクション
        self.create_button_section(main_frame)
        
        # 進捗表示セクション
        self.create_progress_section(main_frame)
        
        # 結果表示セクション
        self.create_result_section(main_frame)
        
        # ステータスバー
        self.create_status_bar(main_frame)
        
    def create_stats_tab_content(self):
        """統計タブの内容を作成"""
        # 統計フレーム
        stats_frame = ttk.Frame(self.stats_tab, padding="10")
        stats_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.stats_tab.columnconfigure(0, weight=1)
        self.stats_tab.rowconfigure(0, weight=1)
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.rowconfigure(1, weight=1)
        
        # タイトル
        stats_title = ttk.Label(
            stats_frame,
            text="ハッシュタグ統計情報",
            font=("Arial", 14, "bold")
        )
        stats_title.grid(row=0, column=0, pady=(0, 20))
        
        # 統計情報表示エリア
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            height=25,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("Consolas", 10)
        )
        self.stats_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
    def create_details_tab_content(self):
        """詳細タブの内容を作成"""
        # 詳細フレーム
        details_frame = ttk.Frame(self.details_tab, padding="10")
        details_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.details_tab.columnconfigure(0, weight=1)
        self.details_tab.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(1, weight=1)
        
        # タイトル
        details_title = ttk.Label(
            details_frame,
            text="投稿詳細情報",
            font=("Arial", 14, "bold")
        )
        details_title.grid(row=0, column=0, pady=(0, 10))
        
        # Treeview for 投稿一覧
        columns = ("hashtag", "post_url", "caption", "tags", "datetime")
        self.details_tree = ttk.Treeview(details_frame, columns=columns, show="headings", height=20)
        
        # カラムヘッダー設定
        self.details_tree.heading("hashtag", text="ハッシュタグ")
        self.details_tree.heading("post_url", text="投稿URL")
        self.details_tree.heading("caption", text="キャプション")
        self.details_tree.heading("tags", text="抽出タグ")
        self.details_tree.heading("datetime", text="投稿日時")
        
        # カラム幅設定
        self.details_tree.column("hashtag", width=120)
        self.details_tree.column("post_url", width=200)
        self.details_tree.column("caption", width=300)
        self.details_tree.column("tags", width=250)
        self.details_tree.column("datetime", width=150)
        
        # Treeviewとスクロールバー
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_tree.yview)
        self.details_tree.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
    def create_input_section(self, parent):
        """ハッシュタグ入力セクション"""
        # セクションフレーム
        input_frame = ttk.LabelFrame(parent, text="ハッシュタグ入力", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        # 単一タグ入力
        ttk.Label(input_frame, text="ハッシュタグ:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.hashtag_var = tk.StringVar()
        hashtag_entry = ttk.Entry(input_frame, textvariable=self.hashtag_var, width=30)
        hashtag_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 説明ラベル
        help_label = ttk.Label(
            input_frame, 
            text="例: citywalkhk, japantravel, photography (#は不要)",
            foreground="gray"
        )
        help_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
        
        # 複数タグ入力
        ttk.Label(input_frame, text="複数タグ入力:").grid(row=2, column=0, sticky=(tk.W, tk.N), pady=(15, 0), padx=(0, 10))
        
        self.multi_tags_text = tk.Text(input_frame, height=4, width=50)
        self.multi_tags_text.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(15, 0), padx=(0, 10))
        
        # スクロールバー
        scrollbar = ttk.Scrollbar(input_frame, orient="vertical", command=self.multi_tags_text.yview)
        scrollbar.grid(row=2, column=2, sticky=(tk.N, tk.S), pady=(15, 0))
        self.multi_tags_text.configure(yscrollcommand=scrollbar.set)
        
        # 複数タグの説明
        multi_help_label = ttk.Label(
            input_frame, 
            text="複数のタグを改行で区切って入力（単一タグ入力よりも優先されます）",
            foreground="gray"
        )
        multi_help_label.grid(row=3, column=1, sticky=tk.W, pady=(5, 0))
        
    def create_options_section(self, parent):
        """オプション設定セクション"""
        options_frame = ttk.LabelFrame(parent, text="オプション設定", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # ヘッドレスモード
        self.headless_var = tk.BooleanVar(value=True)
        headless_check = ttk.Checkbutton(
            options_frame, 
            text="ヘッドレスモード（ブラウザを表示しない）", 
            variable=self.headless_var
        )
        headless_check.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # データ保存設定
        self.save_data_var = tk.BooleanVar(value=True)
        save_check = ttk.Checkbutton(
            options_frame, 
            text="データを自動保存（CSV/JSON形式）", 
            variable=self.save_data_var
        )
        save_check.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # ファイル名設定
        filename_frame = ttk.Frame(options_frame)
        filename_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(filename_frame, text="ファイル名:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.filename_var = tk.StringVar()
        filename_entry = ttk.Entry(filename_frame, textvariable=self.filename_var, width=25)
        filename_entry.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(filename_frame, text="（空白時は自動生成）", foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # 投稿確認数設定
        posts_frame = ttk.Frame(options_frame)
        posts_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(posts_frame, text="投稿確認数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.max_posts_var = tk.StringVar(value="20")
        posts_entry = ttk.Entry(posts_frame, textvariable=self.max_posts_var, width=10)
        posts_entry.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Label(posts_frame, text="（取得する投稿の最大数）", foreground="gray").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
    def create_button_section(self, parent):
        """実行ボタンセクション"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        # 実行ボタン
        self.execute_button = ttk.Button(
            button_frame, 
            text="スクレイピング実行", 
            command=self.execute_scraping,
            style="Accent.TButton"
        )
        self.execute_button.grid(row=0, column=0, padx=(0, 10))
        
        # 停止ボタン
        self.stop_button = ttk.Button(
            button_frame, 
            text="停止", 
            command=self.stop_scraping,
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        # クリアボタン
        clear_button = ttk.Button(
            button_frame, 
            text="クリア", 
            command=self.clear_all
        )
        clear_button.grid(row=0, column=2, padx=(0, 10))
        
        # ヘルプボタン
        help_button = ttk.Button(
            button_frame, 
            text="ヘルプ", 
            command=self.show_help
        )
        help_button.grid(row=0, column=3)
        
    def create_progress_section(self, parent):
        """進捗表示セクション"""
        progress_frame = ttk.LabelFrame(parent, text="実行状況", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 進捗バー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 進捗ラベル
        self.progress_label = ttk.Label(progress_frame, text="待機中...")
        self.progress_label.grid(row=1, column=0, sticky=tk.W)
        
        # 時間情報フレーム
        time_info_frame = ttk.Frame(progress_frame)
        time_info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        time_info_frame.columnconfigure(1, weight=1)
        
        # 経過時間ラベル
        self.elapsed_time_label = ttk.Label(time_info_frame, text="経過時間: --:--:--")
        self.elapsed_time_label.grid(row=0, column=0, sticky=tk.W)
        
        # 推定残り時間ラベル
        self.remaining_time_label = ttk.Label(time_info_frame, text="推定残り時間: --:--:--")
        self.remaining_time_label.grid(row=0, column=1, sticky=tk.E)
        
    def create_result_section(self, parent):
        """結果表示セクション"""
        result_frame = ttk.LabelFrame(parent, text="実行結果", padding="10")
        result_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        # 結果テキストエリア
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            height=15, 
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 親フレームのグリッド重み設定
        parent.rowconfigure(6, weight=1)
        
    def create_status_bar(self, parent):
        """ステータスバー"""
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 時刻表示
        self.time_label = ttk.Label(status_frame, text="")
        self.time_label.grid(row=0, column=1, padx=(10, 0))
        
        # バージョン表示
        self.version_label = ttk.Label(status_frame, text=VERSION, foreground="gray")
        self.version_label.grid(row=0, column=2, padx=(10, 0))
        
        # 時刻更新
        self.update_time()
        
    def update_time(self):
        """時刻表示の更新"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)  # 1秒後に再実行
        
    def update_progress_time(self, current_index: int, total_count: int):
        """進捗時間情報の更新"""
        if not self.is_running or not self.start_time:
            return
            
        import time
        current_time = time.time()
        elapsed_seconds = current_time - self.start_time
        
        # 経過時間を表示
        elapsed_str = self._format_time(elapsed_seconds)
        self.elapsed_time_label.config(text=f"経過時間: {elapsed_str}")
        
        # 推定残り時間を計算
        if current_index > 0:
            # 1つあたりの平均処理時間を計算
            avg_time_per_item = elapsed_seconds / current_index
            remaining_items = total_count - current_index
            estimated_remaining = avg_time_per_item * remaining_items
            
            remaining_str = self._format_time(estimated_remaining)
            self.remaining_time_label.config(text=f"推定残り時間: {remaining_str}")
        else:
            self.remaining_time_label.config(text="推定残り時間: 計算中...")
    
    def _format_time(self, seconds: float) -> str:
        """秒数を時:分:秒形式に変換"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def start_time_tracking(self):
        """時間追跡を開始"""
        import time
        self.start_time = time.time()
        self._update_time_display()
    
    def _update_time_display(self):
        """時間表示の定期更新"""
        if self.is_running:
            import time
            current_time = time.time()
            elapsed_seconds = current_time - self.start_time if self.start_time else 0
            
            elapsed_str = self._format_time(elapsed_seconds)
            self.elapsed_time_label.config(text=f"経過時間: {elapsed_str}")
            
            # 1秒後に再実行
            self.time_update_job = self.root.after(1000, self._update_time_display)
    
    def stop_time_tracking(self):
        """時間追跡を停止"""
        if self.time_update_job:
            self.root.after_cancel(self.time_update_job)
            self.time_update_job = None
        
        # 表示をリセット
        self.elapsed_time_label.config(text="経過時間: --:--:--")
        self.remaining_time_label.config(text="推定残り時間: --:--:--")
        
    def execute_scraping(self):
        """スクレイピング実行"""
        if self.is_running:
            return
        
        # 入力チェック
        hashtags = self.get_input_hashtags()
        if not hashtags:
            messagebox.showwarning("入力エラー", "ハッシュタグを入力してください。")
            return
        
        # UI状態更新
        self.is_running = True
        self.execute_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_var.set(0)
        self.update_status("実行中...")
        
        # 時間追跡開始
        self.start_time_tracking()
        
        # バックグラウンドで実行
        self.current_thread = threading.Thread(
            target=self.scraping_worker,
            args=(hashtags,),
            daemon=True
        )
        self.current_thread.start()
        
    def get_input_hashtags(self):
        """入力されたハッシュタグを取得"""
        hashtags = []
        
        # 複数タグ入力を優先
        multi_text = self.multi_tags_text.get("1.0", tk.END).strip()
        if multi_text:
            hashtags = [tag.strip().lstrip('#') for tag in multi_text.split('\n') if tag.strip()]
        else:
            # 単一タグ入力
            single_tag = self.hashtag_var.get().strip().lstrip('#')
            if single_tag:
                hashtags = [single_tag]
        
        return hashtags
        
    def scraping_worker(self, hashtags):
        """スクレイピング処理ワーカー"""
        try:
            results = []
            total_tags = len(hashtags)
            
            for i, hashtag in enumerate(hashtags):
                if not self.is_running:  # 停止チェック
                    break
                
                # 進捗更新
                progress = (i / total_tags) * 100
                self.root.after(0, lambda: self.progress_var.set(progress))
                self.root.after(0, lambda tag=hashtag: self.update_status(f"処理中: #{tag}"))
                
                # 時間情報更新
                self.root.after(0, lambda idx=i, total=total_tags: self.update_progress_time(idx, total))
                
                # ログ出力
                self.root.after(0, lambda tag=hashtag: self.append_result(f"\n=== #{tag} の処理を開始 ==="))
                
                # データ取得
                try:
                    # 投稿確認数を取得（無効な値の場合はデフォルト20を使用）
                    try:
                        max_posts = int(self.max_posts_var.get())
                        if max_posts <= 0:
                            max_posts = 20
                    except (ValueError, AttributeError):
                        max_posts = 20
                    
                    result = fetch_hashtag_data(hashtag, self.headless_var.get(), max_posts)
                    results.append(result)
                    
                    # 結果表示
                    self.root.after(0, lambda r=result: self.display_single_result(r))
                    
                except Exception as e:
                    error_msg = f"#{hashtag} の取得に失敗: {str(e)}"
                    self.root.after(0, lambda msg=error_msg: self.append_result(f"❌ {msg}"))
                    
                    # エラー結果も保存
                    error_result = {
                        'hashtag': hashtag,
                        'error': str(e),
                        'post_count': 0,
                        'related_tags': [],
                        'top_posts': []
                    }
                    results.append(error_result)
            
            # 完了処理
            if self.is_running:
                self.root.after(0, lambda: self.scraping_completed(results))
                
        except Exception as e:
            error_msg = f"予期しないエラーが発生しました: {str(e)}"
            self.root.after(0, lambda: self.append_result(f"❌ {error_msg}"))
            self.root.after(0, self.scraping_finished)
            
    def display_single_result(self, result):
        """単一結果の表示"""
        hashtag = result.get('hashtag', 'unknown')
        
        if result.get('error'):
            self.append_result(f"❌ エラー: {result['error']}")
        else:
            post_count = result.get('post_count', 0)
            related_count = len(result.get('related_tags', []))
            top_posts_count = len(result.get('top_posts', []))
            
            self.append_result(f"✅ 取得完了:")
            self.append_result(f"   投稿数: {post_count:,}")
            self.append_result(f"   関連タグ: {related_count}個")
            self.append_result(f"   トップ投稿: {top_posts_count}個")
            
            if result.get('related_tags'):
                tags_str = ', '.join(result['related_tags'][:5])
                self.append_result(f"   関連タグ例: {tags_str}")
                
    def scraping_completed(self, results):
        """スクレイピング完了処理"""
        try:
            # データ保存
            if self.save_data_var.get() and results:
                self.save_results(results)
            
            # 完了メッセージ
            success_count = len([r for r in results if not r.get('error')])
            total_count = len(results)
            
            self.append_result(f"\n🎉 すべての処理が完了しました！")
            self.append_result(f"成功: {success_count}件, 失敗: {total_count - success_count}件")
            
            self.progress_var.set(100)
            self.update_status("完了")
            
            # 完了ダイアログ
            messagebox.showinfo(
                "処理完了", 
                f"ハッシュタグの取得が完了しました。\n\n"
                f"成功: {success_count}件\n"
                f"失敗: {total_count - success_count}件"
            )
            
        except Exception as e:
            self.append_result(f"❌ 完了処理エラー: {str(e)}")
            
        finally:
            self.scraping_finished()
            
    def save_results(self, results):
        """結果を保存"""
        try:
            filename = self.filename_var.get().strip()
            
            if len(results) == 1:
                # 単一結果
                csv_path, json_path, tags_json_path = self.data_manager.save_hashtag_data(
                    results[0], 
                    filename if filename else None
                )
            else:
                # 複数結果
                csv_path, json_path, tags_json_path = self.data_manager.save_batch_results(
                    results, 
                    filename if filename else None
                )
            
            self.append_result(f"\n💾 データを保存しました:")
            self.append_result(f"   CSV: {csv_path}")
            self.append_result(f"   JSON: {json_path}")
            self.append_result(f"   Tags JSON: {tags_json_path}")
            
            # Tags JSONデータを読み込んで統計・詳細タブを更新
            self.load_and_display_tags_data(tags_json_path)
            
        except Exception as e:
            self.append_result(f"❌ データ保存エラー: {str(e)}")
            
    def stop_scraping(self):
        """スクレイピング停止"""
        self.is_running = False
        self.update_status("停止中...")
        self.append_result("\n⚠️ ユーザーによって停止されました")
        
    def scraping_finished(self):
        """スクレイピング終了処理"""
        self.is_running = False
        self.execute_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.update_status("準備完了")
        
        # 時間追跡停止
        self.stop_time_tracking()
        
    def update_stats_display(self, tags_data):
        """統計タブの表示を更新"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        
        try:
            if isinstance(tags_data, dict):
                # 単一ハッシュタグの場合
                if 'statistics' in tags_data:
                    self._display_single_hashtag_stats(tags_data)
                # バッチの場合
                elif 'batch_statistics' in tags_data:
                    self._display_batch_stats(tags_data)
                else:
                    self.stats_text.insert(tk.END, "統計データが見つかりませんでした。")
            else:
                self.stats_text.insert(tk.END, "無効なデータ形式です。")
                
        except Exception as e:
            self.stats_text.insert(tk.END, f"統計表示エラー: {e}")
        
        self.stats_text.config(state=tk.DISABLED)
    
    def _display_single_hashtag_stats(self, tags_data):
        """単一ハッシュタグの統計表示"""
        hashtag = tags_data.get('hashtag', '不明')
        stats = tags_data.get('statistics', {})
        
        self.stats_text.insert(tk.END, f"=== #{hashtag} の統計情報 ===\\n\\n")
        
        # 基本統計
        self.stats_text.insert(tk.END, "【基本統計】\\n")
        self.stats_text.insert(tk.END, f"タグ付き投稿数: {stats.get('total_posts_with_tags', 0)}件\\n")
        self.stats_text.insert(tk.END, f"ユニークタグ数: {stats.get('unique_tags_count', 0)}個\\n\\n")
        
        # 人気タグランキング
        most_common = stats.get('most_common_tags', [])
        if most_common:
            self.stats_text.insert(tk.END, "【人気タグ TOP10】\\n")
            for i, (tag, count) in enumerate(most_common[:10], 1):
                self.stats_text.insert(tk.END, f"{i:2d}. {tag:<25} ({count}回)\\n")
            self.stats_text.insert(tk.END, "\\n")
        
        # 全ユニークタグ
        all_tags = stats.get('all_unique_tags', [])
        if all_tags:
            self.stats_text.insert(tk.END, f"【全ユニークタグ ({len(all_tags)}個)】\\n")
            # 5個ずつ改行して表示
            for i in range(0, len(all_tags), 5):
                line_tags = all_tags[i:i+5]
                self.stats_text.insert(tk.END, ", ".join(line_tags) + "\\n")
    
    def _display_batch_stats(self, batch_data):
        """バッチ統計の表示"""
        batch_info = batch_data.get('batch_info', {})
        batch_stats = batch_data.get('batch_statistics', {})
        hashtags = batch_data.get('hashtags', [])
        
        self.stats_text.insert(tk.END, "=== バッチ処理統計情報 ===\\n\\n")
        
        # バッチ基本情報
        self.stats_text.insert(tk.END, "【バッチ情報】\\n")
        self.stats_text.insert(tk.END, f"処理ハッシュタグ数: {batch_info.get('total_hashtags', 0)}個\\n")
        self.stats_text.insert(tk.END, f"タグ有り投稿数: {batch_stats.get('total_posts_with_tags', 0)}件\\n")
        self.stats_text.insert(tk.END, f"全体ユニークタグ数: {batch_stats.get('total_unique_tags', 0)}個\\n\\n")
        
        # 全体人気タグランキング
        overall_common = batch_stats.get('most_common_tags_overall', [])
        if overall_common:
            self.stats_text.insert(tk.END, "【全体人気タグ TOP20】\\n")
            for i, (tag, count) in enumerate(overall_common[:20], 1):
                self.stats_text.insert(tk.END, f"{i:2d}. {tag:<25} ({count}回)\\n")
            self.stats_text.insert(tk.END, "\\n")
        
        # ハッシュタグ別統計
        self.stats_text.insert(tk.END, "【ハッシュタグ別統計】\\n")
        for hashtag_data in hashtags:
            hashtag = hashtag_data.get('hashtag', '不明')
            h_stats = hashtag_data.get('statistics', {})
            posts_count = h_stats.get('total_posts_with_tags', 0)
            unique_count = h_stats.get('unique_tags_count', 0)
            
            self.stats_text.insert(tk.END, f"#{hashtag:<20} | 投稿:{posts_count:3d}件 | タグ:{unique_count:3d}個\\n")
            
            # トップ3タグを表示
            top_tags = h_stats.get('most_common_tags', [])[:3]
            if top_tags:
                tag_list = [f"{tag}({count})" for tag, count in top_tags]
                self.stats_text.insert(tk.END, f"{'':23} | トップ3: {', '.join(tag_list)}\\n")
            self.stats_text.insert(tk.END, "\\n")
    
    def update_details_display(self, tags_data):
        """詳細タブの表示を更新"""
        # 既存のデータをクリア
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        
        try:
            if isinstance(tags_data, dict):
                if 'posts_with_tags' in tags_data:
                    # 単一ハッシュタグの場合
                    hashtag = tags_data.get('hashtag', '不明')
                    self._add_posts_to_tree(hashtag, tags_data.get('posts_with_tags', []))
                elif 'hashtags' in tags_data:
                    # バッチの場合
                    for hashtag_data in tags_data.get('hashtags', []):
                        hashtag = hashtag_data.get('hashtag', '不明')
                        posts = hashtag_data.get('posts_with_tags', [])
                        self._add_posts_to_tree(hashtag, posts)
        except Exception as e:
            # エラー行を追加
            self.details_tree.insert("", "end", values=(f"エラー: {e}", "", "", "", ""))
    
    def _add_posts_to_tree(self, hashtag, posts):
        """投稿データをTreeviewに追加"""
        for post in posts:
            # データの準備
            post_url = post.get('post_url', '')
            caption = (post.get('caption', '')[:50] + '...') if len(post.get('caption', '')) > 50 else post.get('caption', '')
            tags = ', '.join(post.get('tags', []))
            if len(tags) > 40:
                tags = tags[:40] + '...'
            datetime_str = post.get('datetime', '')
            
            # Treeviewに行を追加
            self.details_tree.insert("", "end", values=(
                hashtag,
                post_url,
                caption,
                tags,
                datetime_str
            ))
    
    def clear_stats_and_details(self):
        """統計・詳細タブをクリア"""
        # 統計タブクリア
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert(tk.END, "スクレイピング実行後に統計情報が表示されます。")
        self.stats_text.config(state=tk.DISABLED)
        
        # 詳細タブクリア
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
    
    def load_and_display_tags_data(self, tags_json_path):
        """Tags JSONデータを読み込んで統計・詳細タブを更新"""
        try:
            import json
            with open(tags_json_path, 'r', encoding='utf-8') as f:
                tags_data = json.load(f)
            
            # 統計タブを更新
            self.update_stats_display(tags_data)
            
            # 詳細タブを更新
            self.update_details_display(tags_data)
            
            # 統計タブに自動切り替え
            self.notebook.select(1)  # 統計タブのインデックス
            
            self.append_result(f"\n📊 統計・詳細情報を表示しました。「統計情報」タブをご確認ください。")
            
        except Exception as e:
            self.append_result(f"❌ 統計データ読み込みエラー: {str(e)}")
    
    def clear_all(self):
        """全クリア"""
        if self.is_running:
            if not messagebox.askyesno("確認", "実行中ですが、本当にクリアしますか？"):
                return
            self.stop_scraping()
        
        self.hashtag_var.set("")
        self.multi_tags_text.delete("1.0", tk.END)
        self.filename_var.set("")
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.update_status("準備完了")
        
        # 時間追跡停止
        self.stop_time_tracking()
        
        # 統計・詳細タブをクリア
        self.clear_stats_and_details()
        
    def show_help(self):
        """ヘルプダイアログ"""
        help_text = """Instagram ハッシュタグスクレイパー ヘルプ

【基本的な使い方】
1. ハッシュタグを入力（#は不要）
2. オプションを設定
3. 「スクレイピング実行」ボタンをクリック

【入力方法】
• 単一タグ: 上部の入力欄に1つのタグを入力
• 複数タグ: 下部のテキストエリアに改行区切りで入力

【取得される情報】
• 投稿数
• 関連タグ（最大10個）
• トップ投稿（設定可能、デフォルト20個）
• 投稿のURL、画像URL、投稿タイプ
• キャプションから抽出されたハッシュタグ

【タブ機能】
• メインタブ: 実行・設定・結果表示
• 統計情報タブ: 人気タグランキング、ユニークタグ一覧
• 詳細情報タブ: 投稿一覧とタグ詳細

【注意事項】
• 初回利用時は事前にログインが必要です
• 過度なアクセスはアカウント制限の原因になります
• 取得は公開データのみに限定されます

【ファイル保存】
データは data/hashtags/YYYYMM/ フォルダに保存されます
• CSV形式: 分析用
• JSON形式: バックアップ用

【トラブルシューティング】
• ログインエラー: python src/scraper/login.py を実行
• 接続エラー: ChromeDriverの確認
• データ取得失敗: しばらく時間を空けて再試行"""

        # ヘルプウィンドウ
        help_window = tk.Toplevel(self.root)
        help_window.title("ヘルプ")
        help_window.geometry("600x500")
        help_window.transient(self.root)
        help_window.grab_set()
        
        # ヘルプテキスト
        help_text_widget = scrolledtext.ScrolledText(
            help_window, 
            wrap=tk.WORD, 
            font=("Arial", 10)
        )
        help_text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state=tk.DISABLED)
        
        # 閉じるボタン
        close_button = ttk.Button(
            help_window, 
            text="閉じる", 
            command=help_window.destroy
        )
        close_button.pack(pady=10)
        
    def append_result(self, text):
        """結果テキストに追加"""
        self.result_text.config(state=tk.NORMAL)
        self.result_text.insert(tk.END, text + "\n")
        self.result_text.see(tk.END)
        self.result_text.config(state=tk.DISABLED)
        
    def update_status(self, text):
        """ステータス更新"""
        self.status_var.set(text)
        self.progress_label.config(text=text)
        
    def on_closing(self):
        """ウィンドウ終了時の処理"""
        if self.is_running:
            if messagebox.askyesno("確認", "スクレイピングが実行中です。本当に終了しますか？"):
                self.stop_scraping()
                # 少し待ってから終了
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()


def main():
    """メイン関数"""
    try:
        # tkinterの初期化
        root = tk.Tk()
        
        # テーマ設定（利用可能な場合）
        try:
            style = ttk.Style()
            # 使用可能なテーマを確認
            available_themes = style.theme_names()
            if 'clam' in available_themes:
                style.theme_use('clam')
            elif 'alt' in available_themes:
                style.theme_use('alt')
        except:
            pass
        
        # アプリケーション起動
        app = InstagramScraperGUI(root)
        
        # 初期メッセージ
        app.append_result("Instagram ハッシュタグスクレイパー v3.0.0 へようこそ！")
        app.append_result("新機能: タブ表示、統計情報、詳細分析が追加されました。")
        app.append_result("使用方法については「ヘルプ」ボタンをクリックしてください。")
        app.append_result("\n初回利用時は以下のコマンドでログインしてください:")
        app.append_result("python src/scraper/login.py")
        
        # メインループ開始
        root.mainloop()
        
    except ImportError:
        print("❌ 必要なモジュールがインストールされていません")
        print("以下のコマンドで依存関係をインストールしてください:")
        print("pip install -r requirements.txt")
        
    except Exception as e:
        print(f"❌ アプリケーション起動エラー: {e}")


if __name__ == "__main__":
    main()