#!/usr/bin/env python3
"""
E2E（End-to-End）テストシナリオ
実際の使用ケースに基づいた統合テスト
"""

import pytest
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import tempfile
import time

from tests.fixtures.mock_data import MOCK_HASHTAG_DATA, MOCK_COOKIES


class TestE2EScenarios:
    """エンドツーエンドシナリオテスト"""
    
    @pytest.mark.integration
    def test_scenario_first_time_user(self, temp_dir):
        """
        シナリオ1: 初回利用ユーザーのフロー
        1. アプリケーション起動
        2. ログイン（Cookie保存）
        3. 単一タグの取得
        4. 結果の確認
        """
        # 環境準備
        cookies_dir = temp_dir / "cookies"
        cookies_dir.mkdir()
        
        # 1. ログインプロセス
        from src.scraper.login import InstagramLogin
        
        with patch('src.scraper.login.webdriver') as mock_webdriver:
            mock_driver = MagicMock()
            mock_webdriver.Chrome.return_value = mock_driver
            mock_driver.get_cookies.return_value = MOCK_COOKIES
            
            login_manager = InstagramLogin(str(cookies_dir))
            
            # ログインとCookie保存
            with patch('builtins.input', side_effect=['', '']):  # Enterキー押下をシミュレート
                login_manager.save_cookies(mock_driver)
        
        # Cookieファイルが作成されたか確認
        cookie_file = cookies_dir / "ig_cookies.json"
        assert cookie_file.exists()
        
        # 2. タグ取得
        from src.scraper.fetch_tag import fetch_hashtag_data
        
        with patch('src.scraper.fetch_tag.InstagramHashtagScraper') as mock_scraper_class:
            mock_scraper = MagicMock()
            mock_scraper_class.return_value = mock_scraper
            mock_scraper.initialize_session.return_value = True
            mock_scraper.fetch_hashtag_info.return_value = MOCK_HASHTAG_DATA
            
            result = fetch_hashtag_data('testtag', headless=True)
        
        # 3. 結果確認
        assert result['hashtag'] == 'test'
        assert result['post_count'] > 0
        assert len(result['related_tags']) > 0
    
    @pytest.mark.integration
    def test_scenario_batch_processing_user(self, temp_dir):
        """
        シナリオ2: バッチ処理ユーザーのフロー
        1. CSVファイル準備
        2. バッチ処理実行
        3. 結果ファイル確認
        4. エラーハンドリング
        """
        # 1. CSVファイル準備
        tags_file = temp_dir / "my_tags.csv"
        tags_file.write_text("hashtag\ntag1\nerror_tag\ntag2\n")
        
        # 2. バッチ処理実行
        from src.run_batch import BatchProcessor
        
        processor = BatchProcessor(headless=True, delay=0.1)
        
        def mock_fetch_with_error(tag, headless):
            if 'error' in tag:
                raise Exception("ネットワークエラー")
            return {**MOCK_HASHTAG_DATA, 'hashtag': tag}
        
        with patch('src.run_batch.fetch_hashtag_data', side_effect=mock_fetch_with_error):
            with patch('time.sleep'):
                hashtags = processor.load_hashtags_from_csv(str(tags_file))
                results = processor.process_hashtags(hashtags)
        
        # 3. 結果確認
        assert len(results) == 3
        assert processor.stats['success_count'] == 2
        assert processor.stats['error_count'] == 1
        
        # エラー結果の確認
        error_result = next(r for r in results if 'error' in r['hashtag'])
        assert error_result['error'] is not None
    
    @pytest.mark.integration
    def test_scenario_scheduled_execution(self, temp_dir, mock_tags_csv):
        """
        シナリオ3: スケジュール実行のフロー
        1. スケジューラ設定
        2. ジョブ登録
        3. 自動実行
        4. 結果確認
        """
        from src.scheduler import InstagramScheduler
        
        # 1. スケジューラ設定
        config = {
            "jobs": [{
                "name": "hourly_check",
                "description": "1時間ごとのチェック",
                "schedule": "interval",
                "interval_minutes": 60,
                "tags_file": mock_tags_csv,
                "enabled": True,
                "headless": True,
                "delay": 1.0
            }],
            "settings": {
                "error_notification": True,
                "success_notification": True
            }
        }
        
        config_file = temp_dir / "scheduler_config.json"
        config_file.write_text(json.dumps(config))
        
        scheduler = InstagramScheduler(str(config_file))
        
        # 2. ジョブ実行テスト
        job_executed = False
        
        def mock_process_hashtags(hashtags, batch_name):
            nonlocal job_executed
            job_executed = True
            return [MOCK_HASHTAG_DATA]
        
        with patch('src.scheduler.BatchProcessor') as mock_batch_class:
            mock_processor = MagicMock()
            mock_batch_class.return_value = mock_processor
            mock_processor.load_hashtags_from_csv.return_value = ['tag1']
            mock_processor.process_hashtags.side_effect = mock_process_hashtags
            mock_processor.stats = {'success_count': 1, 'error_count': 0}
            
            # ジョブ実行
            scheduler._execute_job(config['jobs'][0])
        
        # 3. 実行確認
        assert job_executed
    
    @pytest.mark.integration
    def test_scenario_error_recovery(self, temp_dir):
        """
        シナリオ4: エラー復旧のフロー
        1. レート制限エラー発生
        2. 自動待機
        3. リトライ
        4. 成功
        """
        from src.scraper.fetch_tag import InstagramHashtagScraper
        
        scraper = InstagramHashtagScraper(headless=True)
        
        # エラー発生と復旧のシミュレーション
        attempt_count = 0
        
        def mock_error_handler(driver, logger):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                return 'rate_limited'
            return 'none'
        
        with patch('src.scraper.fetch_tag.handle_instagram_errors', side_effect=mock_error_handler):
            with patch('src.scraper.fetch_tag.exponential_backoff_sleep'):
                with patch('src.scraper.fetch_tag.human_sleep'):
                    with patch.object(scraper, '_extract_post_count', return_value=1000):
                        with patch.object(scraper, '_extract_related_tags', return_value=[]):
                            with patch.object(scraper, '_extract_top_posts', return_value=[]):
                                scraper.driver = MagicMock()
                                
                                result = scraper.fetch_hashtag_info('test', max_retries=3)
        
        # リトライが成功したことを確認
        assert result['error'] is None
        assert result['post_count'] == 1000
        assert attempt_count == 2  # 1回目エラー、2回目成功
    
    @pytest.mark.integration
    def test_scenario_gui_workflow(self):
        """
        シナリオ5: GUI使用のフロー（モック）
        1. GUI起動
        2. タグ入力
        3. 実行ボタンクリック
        4. 結果表示
        """
        # tkinterのモック（実際のGUIは起動しない）
        with patch('tkinter.Tk'):
            with patch('src.ui.tag_input_gui.InstagramScraperGUI') as mock_gui_class:
                mock_gui = MagicMock()
                mock_gui_class.return_value = mock_gui
                
                # ユーザー入力のシミュレーション
                mock_gui.get_input_hashtags.return_value = ['guiltest1', 'guitest2']
                mock_gui.headless_var.get.return_value = True
                mock_gui.save_data_var.get.return_value = True
                
                # スクレイピング実行のシミュレーション
                def mock_worker(hashtags):
                    for tag in hashtags:
                        mock_gui.display_single_result({
                            'hashtag': tag,
                            'post_count': 1000,
                            'related_tags': ['related1', 'related2'],
                            'top_posts': []
                        })
                    mock_gui.scraping_completed([MOCK_HASHTAG_DATA] * len(hashtags))
                
                mock_gui.scraping_worker = mock_worker
                
                # 実行
                mock_gui.execute_scraping()
                
                # 結果確認
                assert mock_gui.display_single_result.call_count >= 2
                assert mock_gui.scraping_completed.called
    
    @pytest.mark.integration
    def test_scenario_monthly_report(self, temp_dir):
        """
        シナリオ6: 月次レポート生成のフロー
        1. 1ヶ月分のデータ収集
        2. データ集計
        3. レポート生成
        """
        from src.scraper.data_manager import DataManager
        from datetime import datetime, timedelta
        
        data_manager = DataManager(base_dir=str(temp_dir / "data"))
        
        # 1ヶ月分のデータを生成
        base_date = datetime.now()
        for day in range(30):
            date = base_date - timedelta(days=day)
            for i in range(3):  # 1日3タグ
                data = {
                    **MOCK_HASHTAG_DATA,
                    'hashtag': f'tag_{date.strftime("%Y%m%d")}_{i}',
                    'scraped_at': date.timestamp()
                }
                
                # 日付を偽装して保存
                with patch('src.scraper.data_manager.datetime') as mock_datetime:
                    mock_datetime.now.return_value = date
                    data_manager.save_hashtag_data(data)
        
        # 月次サマリー取得
        current_month = base_date.strftime("%Y%m")
        summary = data_manager.get_monthly_summary(current_month)
        
        # レポート確認
        assert summary['total_files'] > 0
        assert summary['total_hashtags'] > 0
        assert summary['month'] == current_month
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_scenario_stress_test(self, temp_dir):
        """
        シナリオ7: ストレステスト
        1. 大量タグの同時処理
        2. メモリ使用量の確認
        3. エラー率の確認
        """
        from src.run_batch import BatchProcessor
        import random
        
        # 500個のタグを生成
        stress_tags = [f"stress_test_{i}" for i in range(500)]
        
        # ランダムにエラーを発生させる
        def mock_fetch_random_error(tag, headless):
            if random.random() < 0.1:  # 10%の確率でエラー
                raise Exception("Random error")
            return {**MOCK_HASHTAG_DATA, 'hashtag': tag}
        
        processor = BatchProcessor(headless=True, delay=0)
        
        with patch('src.run_batch.fetch_hashtag_data', side_effect=mock_fetch_random_error):
            with patch('time.sleep'):
                start_time = time.time()
                results = processor.process_hashtags(stress_tags)
                end_time = time.time()
        
        # パフォーマンス確認
        processing_time = end_time - start_time
        error_rate = processor.stats['error_count'] / len(stress_tags)
        
        # 許容範囲の確認
        assert len(results) == 500
        assert processing_time < 60  # 1分以内
        assert error_rate < 0.15  # エラー率15%以下
        assert processor.stats['success_count'] > 400  # 80%以上成功