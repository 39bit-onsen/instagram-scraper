#!/usr/bin/env python3
"""
統合テスト - 複数モジュール間の連携テスト
"""

import pytest
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile

from src.run_batch import BatchProcessor
from src.scheduler import InstagramScheduler
from src.scraper.data_manager import DataManager
from tests.fixtures.mock_data import (
    MOCK_HASHTAG_DATA,
    ERROR_HASHTAG_DATA,
    MOCK_CSV_CONTENT,
    MOCK_SCHEDULER_CONFIG
)


class TestBatchProcessorIntegration:
    """BatchProcessorの統合テスト"""
    
    @pytest.fixture
    def batch_processor(self):
        """BatchProcessorインスタンスを作成"""
        with patch('src.run_batch.fetch_hashtag_data') as mock_fetch:
            mock_fetch.side_effect = lambda tag, headless: {
                **MOCK_HASHTAG_DATA,
                'hashtag': tag
            }
            processor = BatchProcessor(headless=True, delay=0.1)
            yield processor
    
    def test_batch_processing_workflow(self, batch_processor, mock_tags_csv, temp_dir):
        """バッチ処理の全体ワークフローテスト"""
        # CSVからタグ読み込み
        hashtags = batch_processor.load_hashtags_from_csv(mock_tags_csv)
        assert len(hashtags) > 0
        
        # バッチ処理実行
        with patch('src.run_batch.fetch_hashtag_data') as mock_fetch:
            mock_fetch.return_value = MOCK_HASHTAG_DATA
            with patch('time.sleep'):  # 待機時間をスキップ
                results = batch_processor.process_hashtags(hashtags, "test_batch")
        
        # 結果の検証
        assert len(results) == len(hashtags)
        assert batch_processor.stats['success_count'] == len(hashtags)
        assert batch_processor.stats['error_count'] == 0
    
    def test_batch_processing_with_errors(self, batch_processor, temp_dir):
        """エラーを含むバッチ処理テスト"""
        hashtags = ['success1', 'error1', 'success2']
        
        def mock_fetch_side_effect(tag, headless):
            if 'error' in tag:
                return ERROR_HASHTAG_DATA
            return {**MOCK_HASHTAG_DATA, 'hashtag': tag}
        
        with patch('src.run_batch.fetch_hashtag_data', side_effect=mock_fetch_side_effect):
            with patch('time.sleep'):
                results = batch_processor.process_hashtags(hashtags)
        
        assert len(results) == 3
        assert batch_processor.stats['success_count'] == 2
        assert batch_processor.stats['error_count'] == 1
    
    def test_batch_processing_keyboard_interrupt(self, batch_processor):
        """キーボード割り込みのテスト"""
        hashtags = ['tag1', 'tag2', 'tag3']
        
        # 2番目のタグでKeyboardInterruptを発生させる
        call_count = 0
        def mock_fetch_interrupt(tag, headless):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise KeyboardInterrupt()
            return MOCK_HASHTAG_DATA
        
        with patch('src.run_batch.fetch_hashtag_data', side_effect=mock_fetch_interrupt):
            with patch('time.sleep'):
                results = batch_processor.process_hashtags(hashtags)
        
        # 1つ目のタグのみ処理されることを確認
        assert len(results) == 1


class TestSchedulerIntegration:
    """Schedulerの統合テスト"""
    
    @pytest.fixture
    def scheduler(self, mock_config_file):
        """Schedulerインスタンスを作成"""
        scheduler = InstagramScheduler(config_file=mock_config_file)
        return scheduler
    
    def test_scheduler_job_execution(self, scheduler, mock_tags_csv):
        """スケジューラのジョブ実行テスト"""
        # ジョブ設定
        job_config = {
            "name": "test_job",
            "description": "テストジョブ",
            "schedule": "interval",
            "interval_minutes": 1,
            "tags_file": mock_tags_csv,
            "enabled": True,
            "headless": True,
            "delay": 0.1
        }
        
        with patch('src.scheduler.BatchProcessor') as mock_batch_class:
            mock_processor = MagicMock()
            mock_batch_class.return_value = mock_processor
            mock_processor.load_hashtags_from_csv.return_value = ['tag1', 'tag2']
            mock_processor.process_hashtags.return_value = [MOCK_HASHTAG_DATA]
            mock_processor.stats = {'success_count': 2, 'error_count': 0}
            
            # ジョブ実行
            scheduler._execute_job(job_config)
            
            # 検証
            mock_processor.load_hashtags_from_csv.assert_called_once_with(mock_tags_csv)
            mock_processor.process_hashtags.assert_called_once()
    
    def test_scheduler_add_remove_job(self, scheduler):
        """ジョブの追加・削除テスト"""
        initial_job_count = len(scheduler.config['jobs'])
        
        # ジョブ追加
        new_job = {
            "name": "new_test_job",
            "description": "新規テストジョブ",
            "schedule": "daily",
            "time": "12:00",
            "tags_file": "test.csv",
            "enabled": True
        }
        
        scheduler.add_job(new_job)
        assert len(scheduler.config['jobs']) == initial_job_count + 1
        
        # ジョブ削除
        scheduler.remove_job("new_test_job")
        assert len(scheduler.config['jobs']) == initial_job_count
    
    @patch('schedule.run_pending')
    @patch('time.sleep')
    def test_scheduler_run_loop(self, mock_sleep, mock_run_pending, scheduler):
        """スケジューラのメインループテスト"""
        # 3回実行後に停止
        call_count = 0
        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                scheduler.is_running = False
        
        mock_sleep.side_effect = side_effect
        
        # ジョブセットアップとループ実行
        scheduler.run()
        
        # run_pendingが少なくとも3回呼ばれることを確認
        assert mock_run_pending.call_count >= 3


class TestDataFlowIntegration:
    """データフロー全体の統合テスト"""
    
    def test_complete_data_flow(self, temp_dir):
        """データ収集から保存までの完全なフローテスト"""
        # 1. データ収集（モック）
        collected_data = MOCK_HASHTAG_DATA
        
        # 2. データ保存
        data_manager = DataManager(base_dir=str(temp_dir / "data"))
        csv_path, json_path = data_manager.save_hashtag_data(collected_data)
        
        # 3. 保存されたデータの読み込み
        loaded_data = data_manager.load_hashtag_data(json_path)
        
        # 4. データの整合性確認
        assert loaded_data['hashtag'] == collected_data['hashtag']
        assert loaded_data['post_count'] == collected_data['post_count']
        assert len(loaded_data['related_tags']) == len(collected_data['related_tags'])
        
        # 5. CSVデータの確認
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_data = next(reader)
            assert csv_data['hashtag'] == collected_data['hashtag']
            assert int(csv_data['post_count']) == collected_data['post_count']
    
    def test_error_recovery_flow(self):
        """エラー復旧フローのテスト"""
        from src.scraper.utils import handle_instagram_errors, get_error_recovery_suggestions
        
        # モックドライバーとロガー
        mock_driver = MagicMock()
        mock_logger = MagicMock()
        
        # 各種エラーシナリオ
        error_scenarios = [
            ('login_required', False),  # (error_type, retry_recommended)
            ('rate_limited', True),
            ('blocked', False)
        ]
        
        for error_type, should_retry in error_scenarios:
            with patch('src.scraper.utils.check_instagram_login_status') as mock_login:
                with patch('src.scraper.utils.detect_rate_limiting') as mock_rate:
                    with patch('src.scraper.utils.check_account_blocked') as mock_blocked:
                        # エラータイプに応じたモック設定
                        mock_login.return_value = (error_type != 'login_required')
                        mock_rate.return_value = (error_type == 'rate_limited')
                        mock_blocked.return_value = (error_type == 'blocked')
                        
                        # エラー検知
                        detected_error = handle_instagram_errors(mock_driver, mock_logger)
                        assert detected_error == error_type
                        
                        # 復旧提案取得
                        suggestions = get_error_recovery_suggestions(detected_error)
                        assert suggestions['retry_recommended'] == should_retry


class TestPerformanceIntegration:
    """パフォーマンステスト"""
    
    @pytest.mark.slow
    def test_large_batch_processing(self):
        """大量タグのバッチ処理テスト"""
        # 100個のタグを生成
        large_tag_list = [f"testtag{i}" for i in range(100)]
        
        processor = BatchProcessor(headless=True, delay=0)
        
        with patch('src.run_batch.fetch_hashtag_data') as mock_fetch:
            mock_fetch.return_value = MOCK_HASHTAG_DATA
            with patch('time.sleep'):
                import time
                start_time = time.time()
                
                # 処理実行
                results = processor.process_hashtags(large_tag_list)
                
                end_time = time.time()
                processing_time = end_time - start_time
        
        # 結果の検証
        assert len(results) == 100
        assert processor.stats['success_count'] == 100
        
        # パフォーマンスの確認（100タグを10秒以内で処理）
        assert processing_time < 10.0
    
    @pytest.mark.slow
    def test_concurrent_data_saving(self, temp_dir):
        """並行データ保存のテスト"""
        import threading
        import time
        
        data_manager = DataManager(base_dir=str(temp_dir / "data"))
        errors = []
        
        def save_data(tag_name):
            try:
                data = {**MOCK_HASHTAG_DATA, 'hashtag': tag_name}
                data_manager.save_hashtag_data(data)
            except Exception as e:
                errors.append(e)
        
        # 10個の並行保存スレッドを作成
        threads = []
        for i in range(10):
            thread = threading.Thread(target=save_data, args=(f"tag{i}",))
            threads.append(thread)
            thread.start()
        
        # すべてのスレッドの完了を待機
        for thread in threads:
            thread.join()
        
        # エラーがないことを確認
        assert len(errors) == 0
        
        # 保存されたファイル数を確認
        saved_files = list(data_manager.hashtags_dir.rglob("*.csv"))
        assert len(saved_files) >= 10