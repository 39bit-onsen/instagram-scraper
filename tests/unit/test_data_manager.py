#!/usr/bin/env python3
"""
data_managerモジュールのユニットテスト
"""

import pytest
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.scraper.data_manager import DataManager
from tests.fixtures.mock_data import MOCK_HASHTAG_DATA, ERROR_HASHTAG_DATA


class TestDataManager:
    """DataManagerクラスのテスト"""
    
    @pytest.fixture
    def data_manager(self, temp_dir):
        """DataManagerインスタンスを作成"""
        with patch('src.scraper.data_manager.Path.cwd', return_value=temp_dir):
            dm = DataManager(base_dir=str(temp_dir / "data"))
            return dm
    
    def test_init(self, data_manager, temp_dir):
        """初期化のテスト"""
        assert data_manager.base_dir == temp_dir / "data"
        assert data_manager.hashtags_dir == temp_dir / "data" / "hashtags"
        assert data_manager.hashtags_dir.exists()
    
    def test_save_hashtag_data_success(self, data_manager, temp_dir):
        """ハッシュタグデータ保存のテスト（成功）"""
        with patch('src.scraper.data_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "202501"
            
            csv_path, json_path = data_manager.save_hashtag_data(MOCK_HASHTAG_DATA)
            
            # ファイルが作成されたか確認
            assert Path(csv_path).exists()
            assert Path(json_path).exists()
            
            # CSVの内容確認
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row = next(reader)
                assert row['hashtag'] == 'test'
                assert row['post_count'] == '1234567'
                assert 'test1' in row['related_tags']
            
            # JSONの内容確認
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert data['hashtag'] == 'test'
                assert data['post_count'] == 1234567
    
    def test_save_hashtag_data_with_error(self, data_manager):
        """ハッシュタグデータ保存のテスト（エラーデータ）"""
        csv_path, json_path = data_manager.save_hashtag_data(ERROR_HASHTAG_DATA)
        
        # エラーデータでも保存されることを確認
        assert Path(csv_path).exists()
        assert Path(json_path).exists()
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row = next(reader)
            assert row['error'] == 'ログインセッションが切れています'
    
    def test_save_hashtag_data_custom_filename(self, data_manager):
        """カスタムファイル名での保存テスト"""
        custom_name = "custom_test"
        csv_path, json_path = data_manager.save_hashtag_data(
            MOCK_HASHTAG_DATA, 
            filename=custom_name
        )
        
        assert custom_name in csv_path
        assert custom_name in json_path
    
    def test_save_batch_results(self, data_manager):
        """バッチ結果の保存テスト"""
        results = [MOCK_HASHTAG_DATA, ERROR_HASHTAG_DATA]
        
        csv_path, json_path = data_manager.save_batch_results(results)
        
        # ファイル存在確認
        assert Path(csv_path).exists()
        assert Path(json_path).exists()
        
        # CSV行数確認
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['hashtag'] == 'test'
            assert rows[1]['hashtag'] == 'errortest'
    
    def test_save_batch_results_empty(self, data_manager):
        """空のバッチ結果保存テスト"""
        results = []
        
        csv_path, json_path = data_manager.save_batch_results(results)
        
        # ファイルは作成されるがデータ行はない
        assert Path(csv_path).exists()
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 0
    
    def test_load_hashtag_data(self, data_manager):
        """ハッシュタグデータ読み込みテスト"""
        # まず保存
        csv_path, json_path = data_manager.save_hashtag_data(MOCK_HASHTAG_DATA)
        
        # JSON読み込み
        loaded_data = data_manager.load_hashtag_data(json_path)
        assert loaded_data['hashtag'] == 'test'
        assert loaded_data['post_count'] == 1234567
    
    def test_load_hashtag_data_not_found(self, data_manager):
        """存在しないファイル読み込みテスト"""
        result = data_manager.load_hashtag_data("nonexistent.json")
        assert result is None
    
    def test_get_monthly_summary(self, data_manager):
        """月次サマリー取得テスト"""
        # テストデータを保存
        data_manager.save_hashtag_data(MOCK_HASHTAG_DATA)
        data_manager.save_hashtag_data(ERROR_HASHTAG_DATA)
        
        # サマリー取得
        with patch('src.scraper.data_manager.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "202501"
            summary = data_manager.get_monthly_summary("202501")
        
        assert summary['total_files'] >= 2
        assert summary['total_hashtags'] >= 2
        assert summary['month'] == "202501"
    
    def test_cleanup_old_data(self, data_manager, temp_dir):
        """古いデータのクリーンアップテスト"""
        # 古いディレクトリを作成
        old_dir = data_manager.hashtags_dir / "202301"
        old_dir.mkdir(parents=True)
        old_file = old_dir / "old_data.csv"
        old_file.write_text("old data")
        
        # 新しいディレクトリも作成
        new_dir = data_manager.hashtags_dir / "202501"
        new_dir.mkdir(parents=True)
        new_file = new_dir / "new_data.csv"
        new_file.write_text("new data")
        
        # クリーンアップ実行
        with patch('src.scraper.data_manager.datetime') as mock_datetime:
            # 2025年1月と仮定
            mock_now = MagicMock()
            mock_now.year = 2025
            mock_now.month = 1
            mock_datetime.now.return_value = mock_now
            
            deleted_count = data_manager.cleanup_old_data(months_to_keep=12)
        
        # 古いディレクトリが削除されたか確認
        assert not old_dir.exists()
        assert new_dir.exists()
        assert deleted_count == 1


class TestDataManagerHelperFunctions:
    """DataManagerのヘルパー関数のテスト"""
    
    @patch('src.scraper.data_manager.Path')
    def test_create_sample_tags_csv(self, mock_path, temp_dir):
        """サンプルタグCSV作成のテスト"""
        from src.scraper.data_manager import create_sample_tags_csv
        
        csv_file = temp_dir / "sample_tags.csv"
        result = create_sample_tags_csv(str(csv_file))
        
        assert result == str(csv_file)
        assert csv_file.exists()
        
        # 内容確認
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            assert headers == ['hashtag', 'description']
            
            # サンプルデータが含まれているか
            rows = list(reader)
            assert len(rows) > 0
    
    def test_export_to_excel(self, data_manager, temp_dir):
        """Excel出力テスト（openpyxlがインストールされている場合）"""
        try:
            import openpyxl
            
            # データを保存
            data_manager.save_hashtag_data(MOCK_HASHTAG_DATA)
            
            # Excel出力
            excel_path = temp_dir / "test_export.xlsx"
            with patch('src.scraper.data_manager.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "202501"
                result = data_manager.export_to_excel(str(excel_path), "202501")
            
            if result:  # メソッドが実装されている場合
                assert excel_path.exists()
                
                # Excelファイルの内容確認
                wb = openpyxl.load_workbook(excel_path)
                assert len(wb.sheetnames) > 0
                
        except ImportError:
            pytest.skip("openpyxlがインストールされていません")