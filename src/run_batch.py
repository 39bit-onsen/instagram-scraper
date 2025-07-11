#!/usr/bin/env python3
"""
Instagram ハッシュタグスクレイパー バッチ処理
CSVファイルから複数ハッシュタグを読み込み、一括処理を実行
"""

import sys
import os
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import time

# パッケージのインポートパスを設定
sys.path.append(os.path.dirname(__file__))

try:
    from scraper.fetch_tag import fetch_hashtag_data
    from scraper.data_manager import DataManager, create_sample_tags_csv
    from scraper.utils import setup_logger
    from tqdm import tqdm
except ImportError as e:
    print(f"❌ モジュールのインポートに失敗しました: {e}")
    print("仮想環境がアクティベートされ、依存関係がインストールされていることを確認してください")
    sys.exit(1)


class BatchProcessor:
    """バッチ処理クラス"""
    
    def __init__(self, headless: bool = True, delay: float = 2.0):
        """
        初期化
        
        Args:
            headless: ヘッドレスモード
            delay: タグ間の待機時間（秒）
        """
        self.headless = headless
        self.delay = delay
        self.data_manager = DataManager()
        self.logger = setup_logger("batch_processor")
        
        # 統計情報
        self.stats = {
            'total_tags': 0,
            'success_count': 0,
            'error_count': 0,
            'start_time': None,
            'end_time': None
        }
        
    def load_hashtags_from_csv(self, csv_file: str) -> List[str]:
        """
        CSVファイルからハッシュタグリストを読み込み
        
        Args:
            csv_file: CSVファイルパス
            
        Returns:
            ハッシュタグのリスト
        """
        hashtags = []
        
        try:
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                # CSVフォーマットを自動検出
                sample = f.read(1024)
                f.seek(0)
                
                sniffer = csv.Sniffer()
                has_header = sniffer.has_header(sample)
                
                reader = csv.reader(f)
                
                # ヘッダーをスキップ
                if has_header:
                    next(reader)
                
                # ハッシュタグを読み込み
                for row in reader:
                    if row and len(row) > 0:
                        hashtag = row[0].strip().lstrip('#')
                        if hashtag:
                            hashtags.append(hashtag)
                            
            self.logger.info(f"✅ CSVファイルから {len(hashtags)} 個のハッシュタグを読み込みました")
            return hashtags
            
        except FileNotFoundError:
            self.logger.error(f"❌ CSVファイルが見つかりません: {csv_file}")
            return []
        except Exception as e:
            self.logger.error(f"❌ CSV読み込みエラー: {e}")
            return []
    
    def process_hashtags(self, hashtags: List[str], batch_name: str = None) -> List[Dict[str, Any]]:
        """
        ハッシュタグの一括処理
        
        Args:
            hashtags: 処理するハッシュタグのリスト
            batch_name: バッチ名（ファイル名に使用）
            
        Returns:
            処理結果のリスト
        """
        if not hashtags:
            self.logger.warning("処理するハッシュタグがありません")
            return []
        
        # 統計情報初期化
        self.stats['total_tags'] = len(hashtags)
        self.stats['start_time'] = datetime.now()
        
        self.logger.info(f"=== バッチ処理開始 ===")
        self.logger.info(f"処理対象: {len(hashtags)} 個のハッシュタグ")
        self.logger.info(f"ヘッドレスモード: {'有効' if self.headless else '無効'}")
        self.logger.info(f"タグ間待機時間: {self.delay} 秒")
        
        results = []
        
        # プログレスバー付きで処理
        with tqdm(total=len(hashtags), desc="ハッシュタグ処理", unit="tags") as pbar:
            for i, hashtag in enumerate(hashtags):
                try:
                    # 進捗表示
                    pbar.set_description(f"処理中: #{hashtag}")
                    self.logger.info(f"[{i+1}/{len(hashtags)}] #{hashtag} を処理中...")
                    
                    # データ取得
                    result = fetch_hashtag_data(hashtag, self.headless)
                    results.append(result)
                    
                    # 結果ログ
                    if result.get('error'):
                        self.logger.warning(f"❌ #{hashtag}: {result['error']}")
                        self.stats['error_count'] += 1
                    else:
                        post_count = result.get('post_count', 0)
                        self.logger.info(f"✅ #{hashtag}: {post_count:,} 投稿")
                        self.stats['success_count'] += 1
                    
                    # プログレスバー更新
                    pbar.update(1)
                    
                    # 待機（最後のタグ以外）
                    if i < len(hashtags) - 1:
                        self.logger.debug(f"{self.delay} 秒待機中...")
                        time.sleep(self.delay)
                        
                except KeyboardInterrupt:
                    self.logger.warning("⚠️ ユーザーによって中断されました")
                    break
                    
                except Exception as e:
                    error_msg = f"予期しないエラー: {str(e)}"
                    self.logger.error(f"❌ #{hashtag}: {error_msg}")
                    
                    # エラー結果を記録
                    error_result = {
                        'hashtag': hashtag,
                        'error': error_msg,
                        'post_count': 0,
                        'related_tags': [],
                        'top_posts': [],
                        'scraped_at': time.time()
                    }
                    results.append(error_result)
                    self.stats['error_count'] += 1
                    
                    pbar.update(1)
        
        # 統計情報更新
        self.stats['end_time'] = datetime.now()
        
        # 結果保存
        if results:
            try:
                csv_path, json_path = self.data_manager.save_batch_results(results, batch_name)
                self.logger.info(f"💾 結果を保存しました:")
                self.logger.info(f"   CSV: {csv_path}")
                self.logger.info(f"   JSON: {json_path}")
            except Exception as e:
                self.logger.error(f"❌ 結果保存エラー: {e}")
        
        # 処理完了ログ
        self.print_summary()
        
        return results
    
    def print_summary(self):
        """処理結果のサマリー表示"""
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
            duration_str = str(duration).split('.')[0]  # 秒以下を切り捨て
        else:
            duration_str = "不明"
        
        self.logger.info("=== 処理結果サマリー ===")
        self.logger.info(f"総ハッシュタグ数: {self.stats['total_tags']}")
        self.logger.info(f"成功: {self.stats['success_count']}")
        self.logger.info(f"失敗: {self.stats['error_count']}")
        self.logger.info(f"成功率: {(self.stats['success_count'] / max(self.stats['total_tags'], 1)) * 100:.1f}%")
        self.logger.info(f"処理時間: {duration_str}")
        
        if self.stats['success_count'] > 0:
            avg_time = duration.total_seconds() / self.stats['success_count']
            self.logger.info(f"平均処理時間: {avg_time:.1f}秒/タグ")


def create_default_tags_file():
    """デフォルトのタグファイルを作成"""
    config_dir = Path("config")
    tags_file = config_dir / "tags.csv"
    
    if not tags_file.exists():
        print("デフォルトのタグファイルを作成しています...")
        create_sample_tags_csv(str(tags_file))
        print(f"✅ タグファイルを作成しました: {tags_file}")
        print("このファイルを編集して、取得したいハッシュタグを設定してください。")
        return str(tags_file)
    else:
        return str(tags_file)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Instagram ハッシュタグスクレイパー バッチ処理",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python src/run_batch.py                          # デフォルトファイル使用
  python src/run_batch.py -f config/my_tags.csv   # カスタムファイル使用
  python src/run_batch.py --gui                   # GUI表示モード
  python src/run_batch.py --delay 5               # 5秒間隔で実行
        """
    )
    
    parser.add_argument(
        "-f", "--file",
        help="ハッシュタグCSVファイルのパス (デフォルト: config/tags.csv)",
        default=None
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="GUIモードで実行（ブラウザを表示）"
    )
    
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="タグ間の待機時間（秒、デフォルト: 2.0）"
    )
    
    parser.add_argument(
        "--batch-name",
        help="バッチ名（ファイル名に使用）"
    )
    
    parser.add_argument(
        "--create-sample",
        action="store_true",
        help="サンプルタグファイルを作成して終了"
    )
    
    args = parser.parse_args()
    
    # サンプルファイル作成モード
    if args.create_sample:
        sample_file = create_sample_tags_csv()
        print(f"サンプルタグファイルを作成しました: {sample_file}")
        return
    
    # ファイルパスの決定
    if args.file:
        csv_file = args.file
    else:
        csv_file = create_default_tags_file()
    
    # ファイル存在チェック
    if not Path(csv_file).exists():
        print(f"❌ CSVファイルが見つかりません: {csv_file}")
        print("--create-sample オプションでサンプルファイルを作成できます")
        return
    
    print("=== Instagram ハッシュタグスクレイパー バッチ処理 ===")
    print(f"CSVファイル: {csv_file}")
    print(f"実行モード: {'GUI表示' if args.gui else 'ヘッドレス'}")
    print(f"待機時間: {args.delay}秒")
    
    # 確認プロンプト
    try:
        response = input("\n処理を開始しますか？ (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("処理を中止しました。")
            return
    except KeyboardInterrupt:
        print("\n処理を中止しました。")
        return
    
    # バッチ処理実行
    try:
        processor = BatchProcessor(
            headless=not args.gui,
            delay=args.delay
        )
        
        # ハッシュタグ読み込み
        hashtags = processor.load_hashtags_from_csv(csv_file)
        
        if not hashtags:
            print("❌ 処理するハッシュタグがありません")
            return
        
        # 処理実行
        results = processor.process_hashtags(hashtags, args.batch_name)
        
        if results:
            print(f"\n🎉 バッチ処理が完了しました！")
            print(f"成功: {processor.stats['success_count']}件")
            print(f"失敗: {processor.stats['error_count']}件")
        else:
            print("❌ 処理結果がありません")
            
    except KeyboardInterrupt:
        print("\n⚠️ 処理が中断されました")
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")


if __name__ == "__main__":
    main()