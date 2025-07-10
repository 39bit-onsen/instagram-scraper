#!/usr/bin/env python3
"""
Instagram スクレイパー データ管理
CSV/JSON形式でのデータ保存・読み込み機能を提供
"""

import json
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from .utils import create_directory_if_not_exists, get_current_month_dir, setup_logger


class DataManager:
    """データ保存・管理クラス"""
    
    def __init__(self, base_dir: str = "data/hashtags"):
        """
        初期化
        
        Args:
            base_dir: データ保存ベースディレクトリ
        """
        self.base_dir = Path(base_dir)
        self.logger = setup_logger("data_manager")
        
        # ベースディレクトリ作成
        create_directory_if_not_exists(self.base_dir)
    
    def save_hashtag_data(self, hashtag_data: Dict[str, Any], 
                         custom_filename: Optional[str] = None) -> tuple[str, str]:
        """
        ハッシュタグデータをCSV/JSON形式で保存
        
        Args:
            hashtag_data: 保存するハッシュタグデータ
            custom_filename: カスタムファイル名（拡張子なし）
            
        Returns:
            (CSV filepath, JSON filepath)
        """
        try:
            # 現在の年月ディレクトリを取得
            month_dir = get_current_month_dir(self.base_dir)
            
            # ファイル名生成
            if custom_filename:
                base_filename = custom_filename
            else:
                hashtag = hashtag_data.get('hashtag', 'unknown')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename = f"{hashtag}_{timestamp}"
            
            csv_filepath = month_dir / f"{base_filename}.csv"
            json_filepath = month_dir / f"{base_filename}.json"
            
            # CSV形式で保存
            csv_path = self._save_to_csv(hashtag_data, csv_filepath)
            
            # JSON形式でバックアップ保存
            json_path = self._save_to_json(hashtag_data, json_filepath)
            
            self.logger.info(f"✅ データ保存完了: {base_filename}")
            self.logger.info(f"   CSV: {csv_path}")
            self.logger.info(f"   JSON: {json_path}")
            
            return str(csv_path), str(json_path)
            
        except Exception as e:
            self.logger.error(f"❌ データ保存エラー: {e}")
            raise
    
    def _save_to_csv(self, hashtag_data: Dict[str, Any], filepath: Path) -> str:
        """CSV形式でデータ保存"""
        try:
            # CSVデータの準備
            csv_rows = []
            
            # メインデータ行
            main_row = {
                'hashtag': hashtag_data.get('hashtag', ''),
                'url': hashtag_data.get('url', ''),
                'post_count': hashtag_data.get('post_count', 0),
                'related_tags_count': len(hashtag_data.get('related_tags', [])),
                'top_posts_count': len(hashtag_data.get('top_posts', [])),
                'related_tags': '|'.join(hashtag_data.get('related_tags', [])),
                'scraped_at': datetime.fromtimestamp(
                    hashtag_data.get('scraped_at', 0)
                ).strftime('%Y-%m-%d %H:%M:%S') if hashtag_data.get('scraped_at') else '',
                'error': hashtag_data.get('error', ''),
                'top_post_urls': '|'.join([
                    post.get('url', '') for post in hashtag_data.get('top_posts', [])
                ]),
                'top_post_types': '|'.join([
                    post.get('type', '') for post in hashtag_data.get('top_posts', [])
                ])
            }
            csv_rows.append(main_row)
            
            # DataFrameに変換して保存
            df = pd.DataFrame(csv_rows)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"CSV保存エラー: {e}")
            raise
    
    def _save_to_json(self, hashtag_data: Dict[str, Any], filepath: Path) -> str:
        """JSON形式でデータ保存"""
        try:
            # 日時を文字列に変換
            json_data = hashtag_data.copy()
            if 'scraped_at' in json_data and json_data['scraped_at']:
                json_data['scraped_at_formatted'] = datetime.fromtimestamp(
                    json_data['scraped_at']
                ).strftime('%Y-%m-%d %H:%M:%S')
            
            # JSON保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"JSON保存エラー: {e}")
            raise
    
    def save_batch_results(self, hashtag_results: List[Dict[str, Any]], 
                          batch_name: Optional[str] = None) -> tuple[str, str]:
        """
        複数ハッシュタグの結果を一括保存
        
        Args:
            hashtag_results: ハッシュタグ結果のリスト
            batch_name: バッチ名
            
        Returns:
            (CSV filepath, JSON filepath)
        """
        try:
            # 現在の年月ディレクトリを取得
            month_dir = get_current_month_dir(self.base_dir)
            
            # ファイル名生成
            if batch_name:
                base_filename = f"batch_{batch_name}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_filename = f"batch_{timestamp}"
            
            csv_filepath = month_dir / f"{base_filename}.csv"
            json_filepath = month_dir / f"{base_filename}.json"
            
            # CSV形式で保存
            csv_path = self._save_batch_to_csv(hashtag_results, csv_filepath)
            
            # JSON形式でバックアップ保存
            json_path = self._save_batch_to_json(hashtag_results, json_filepath)
            
            self.logger.info(f"✅ バッチデータ保存完了: {len(hashtag_results)}件")
            self.logger.info(f"   CSV: {csv_path}")
            self.logger.info(f"   JSON: {json_path}")
            
            return str(csv_path), str(json_path)
            
        except Exception as e:
            self.logger.error(f"❌ バッチデータ保存エラー: {e}")
            raise
    
    def _save_batch_to_csv(self, hashtag_results: List[Dict[str, Any]], 
                          filepath: Path) -> str:
        """バッチ結果をCSV形式で保存"""
        try:
            csv_rows = []
            
            for hashtag_data in hashtag_results:
                row = {
                    'hashtag': hashtag_data.get('hashtag', ''),
                    'url': hashtag_data.get('url', ''),
                    'post_count': hashtag_data.get('post_count', 0),
                    'related_tags_count': len(hashtag_data.get('related_tags', [])),
                    'top_posts_count': len(hashtag_data.get('top_posts', [])),
                    'related_tags': '|'.join(hashtag_data.get('related_tags', [])),
                    'scraped_at': datetime.fromtimestamp(
                        hashtag_data.get('scraped_at', 0)
                    ).strftime('%Y-%m-%d %H:%M:%S') if hashtag_data.get('scraped_at') else '',
                    'error': hashtag_data.get('error', ''),
                    'success': 'Yes' if not hashtag_data.get('error') else 'No'
                }
                csv_rows.append(row)
            
            # DataFrameに変換して保存
            df = pd.DataFrame(csv_rows)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"バッチCSV保存エラー: {e}")
            raise
    
    def _save_batch_to_json(self, hashtag_results: List[Dict[str, Any]], 
                           filepath: Path) -> str:
        """バッチ結果をJSON形式で保存"""
        try:
            # メタデータ付きで保存
            batch_data = {
                'batch_info': {
                    'total_hashtags': len(hashtag_results),
                    'successful_count': len([r for r in hashtag_results if not r.get('error')]),
                    'failed_count': len([r for r in hashtag_results if r.get('error')]),
                    'saved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'results': hashtag_results
            }
            
            # 日時を文字列に変換
            for result in batch_data['results']:
                if 'scraped_at' in result and result['scraped_at']:
                    result['scraped_at_formatted'] = datetime.fromtimestamp(
                        result['scraped_at']
                    ).strftime('%Y-%m-%d %H:%M:%S')
            
            # JSON保存
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"バッチJSON保存エラー: {e}")
            raise
    
    def load_csv_data(self, filepath: Union[str, Path]) -> pd.DataFrame:
        """
        CSVファイルからデータを読み込み
        
        Args:
            filepath: CSVファイルパス
            
        Returns:
            DataFrameオブジェクト
        """
        try:
            df = pd.read_csv(filepath, encoding='utf-8-sig')
            self.logger.info(f"✅ CSVデータ読み込み完了: {len(df)}行")
            return df
            
        except Exception as e:
            self.logger.error(f"❌ CSV読み込みエラー: {e}")
            raise
    
    def load_json_data(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        """
        JSONファイルからデータを読み込み
        
        Args:
            filepath: JSONファイルパス
            
        Returns:
            辞書オブジェクト
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"✅ JSONデータ読み込み完了")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ JSON読み込みエラー: {e}")
            raise
    
    def list_saved_files(self, month: Optional[str] = None) -> Dict[str, List[str]]:
        """
        保存済みファイルの一覧を取得
        
        Args:
            month: 対象月（YYYYMM形式、未指定時は全月）
            
        Returns:
            ファイル一覧の辞書
        """
        try:
            files = {'csv': [], 'json': []}
            
            if month:
                # 特定月のファイル
                month_dir = self.base_dir / month
                if month_dir.exists():
                    files['csv'] = list(month_dir.glob('*.csv'))
                    files['json'] = list(month_dir.glob('*.json'))
            else:
                # 全月のファイル
                for month_dir in self.base_dir.iterdir():
                    if month_dir.is_dir():
                        files['csv'].extend(month_dir.glob('*.csv'))
                        files['json'].extend(month_dir.glob('*.json'))
            
            # パスを文字列に変換
            files['csv'] = [str(f) for f in files['csv']]
            files['json'] = [str(f) for f in files['json']]
            
            self.logger.info(f"保存済みファイル: CSV {len(files['csv'])}個, JSON {len(files['json'])}個")
            
            return files
            
        except Exception as e:
            self.logger.error(f"❌ ファイル一覧取得エラー: {e}")
            return {'csv': [], 'json': []}
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        保存データの統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        try:
            stats = {
                'total_files': 0,
                'total_hashtags': 0,
                'months': [],
                'largest_hashtag': None,
                'most_recent': None
            }
            
            # 月別ディレクトリを走査
            for month_dir in self.base_dir.iterdir():
                if month_dir.is_dir():
                    month_name = month_dir.name
                    stats['months'].append(month_name)
                    
                    # CSVファイルを確認
                    csv_files = list(month_dir.glob('*.csv'))
                    stats['total_files'] += len(csv_files)
                    
                    # サンプルファイルから統計を取得
                    for csv_file in csv_files:
                        try:
                            df = pd.read_csv(csv_file, encoding='utf-8-sig')
                            stats['total_hashtags'] += len(df)
                            
                            # 最大投稿数のハッシュタグを記録
                            if not df.empty and 'post_count' in df.columns:
                                max_posts_row = df.loc[df['post_count'].idxmax()]
                                if (not stats['largest_hashtag'] or 
                                    max_posts_row['post_count'] > stats['largest_hashtag']['post_count']):
                                    stats['largest_hashtag'] = {
                                        'hashtag': max_posts_row.get('hashtag', ''),
                                        'post_count': max_posts_row.get('post_count', 0)
                                    }
                        except Exception:
                            continue
            
            # 最新月をソート
            if stats['months']:
                stats['months'].sort(reverse=True)
                stats['most_recent'] = stats['months'][0]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ 統計情報取得エラー: {e}")
            return {}


def create_sample_tags_csv(filepath: str = "config/sample_tags.csv") -> str:
    """
    サンプルタグCSVファイルを作成
    
    Args:
        filepath: 作成するCSVファイルパス
        
    Returns:
        作成されたファイルパス
    """
    sample_tags = [
        "citywalkhk",
        "japantravel", 
        "foodie",
        "photography",
        "nature",
        "streetart",
        "sunset",
        "coffee",
        "workout",
        "art"
    ]
    
    # ディレクトリ作成
    file_path = Path(filepath)
    create_directory_if_not_exists(file_path.parent)
    
    # CSV作成
    with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['hashtag'])  # ヘッダー
        for tag in sample_tags:
            writer.writerow([tag])
    
    print(f"✅ サンプルタグCSVを作成しました: {filepath}")
    return str(file_path)


def main():
    """メイン関数 - テスト実行"""
    print("=== データ管理機能テスト ===")
    
    # データマネージャー初期化
    dm = DataManager()
    
    # サンプルデータ作成
    sample_data = {
        'hashtag': 'test',
        'url': 'https://www.instagram.com/explore/tags/test/',
        'post_count': 12345,
        'related_tags': ['testdata', 'sample', 'demo'],
        'top_posts': [
            {'url': 'https://www.instagram.com/p/test1/', 'type': 'image'},
            {'url': 'https://www.instagram.com/p/test2/', 'type': 'video'}
        ],
        'scraped_at': time.time(),
        'error': None
    }
    
    try:
        # データ保存テスト
        csv_path, json_path = dm.save_hashtag_data(sample_data, "test_data")
        print(f"✅ テストデータを保存しました")
        print(f"   CSV: {csv_path}")
        print(f"   JSON: {json_path}")
        
        # データ読み込みテスト
        loaded_df = dm.load_csv_data(csv_path)
        print(f"✅ CSVデータを読み込みました: {len(loaded_df)}行")
        
        # 統計情報テスト
        stats = dm.get_summary_stats()
        print(f"✅ 統計情報:")
        print(f"   総ファイル数: {stats.get('total_files', 0)}")
        print(f"   総ハッシュタグ数: {stats.get('total_hashtags', 0)}")
        
        # サンプルタグCSV作成
        sample_csv = create_sample_tags_csv()
        
        print("\n🎉 データ管理機能のテストが完了しました！")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")


if __name__ == "__main__":
    import time
    main()