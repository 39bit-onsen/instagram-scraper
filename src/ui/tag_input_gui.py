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
VERSION = "v2.2.1"

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
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
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
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
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
        
    def create_result_section(self, parent):
        """結果表示セクション"""
        result_frame = ttk.LabelFrame(parent, text="実行結果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
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
        parent.rowconfigure(5, weight=1)
        
    def create_status_bar(self, parent):
        """ステータスバー"""
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
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
                csv_path, json_path = self.data_manager.save_batch_results(
                    results, 
                    filename if filename else None
                )
            
            self.append_result(f"\n💾 データを保存しました:")
            self.append_result(f"   CSV: {csv_path}")
            self.append_result(f"   JSON: {json_path}")
            if len(results) == 1:
                self.append_result(f"   Tags JSON: {tags_json_path}")
            
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
• トップ投稿（最大12個）
• 投稿のURL、画像URL、投稿タイプ

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
        app.append_result("Instagram ハッシュタグスクレイパー v1.0 へようこそ！")
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