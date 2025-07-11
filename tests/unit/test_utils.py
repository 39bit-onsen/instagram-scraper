#!/usr/bin/env python3
"""
utilsモジュールのユニットテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.scraper.utils import (
    setup_logger,
    human_sleep,
    extract_number_from_text,
    clean_text,
    check_instagram_login_status,
    detect_rate_limiting,
    handle_instagram_errors,
    exponential_backoff_sleep,
    get_error_recovery_suggestions,
    retry_on_failure
)


class TestSetupLogger:
    """ロガー設定のテスト"""
    
    def test_setup_logger_default(self):
        """デフォルト設定でのロガー作成"""
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"
        assert logger.level == 20  # INFO
        assert len(logger.handlers) > 0
    
    def test_setup_logger_with_level(self):
        """ログレベル指定でのロガー作成"""
        logger = setup_logger("test_logger", level="DEBUG")
        assert logger.level == 10  # DEBUG
    
    def test_setup_logger_with_file(self, temp_dir):
        """ファイル出力設定でのロガー作成"""
        log_file = temp_dir / "test.log"
        logger = setup_logger("test_logger", log_file=str(log_file))
        
        # ログ出力テスト
        logger.info("テストメッセージ")
        assert log_file.exists()


class TestTextProcessing:
    """テキスト処理関数のテスト"""
    
    @pytest.mark.parametrize("text,expected", [
        ("1,234 posts", 1234),
        ("500K posts", 500),
        ("1.5M posts", 1),
        ("123456", 123456),
        ("no numbers here", 0),
        ("", 0),
    ])
    def test_extract_number_from_text(self, text, expected):
        """数値抽出のテスト"""
        result = extract_number_from_text(text)
        assert result == expected
    
    @pytest.mark.parametrize("text,expected", [
        ("  Hello\n\tWorld  ", "Hello World"),
        ("Multiple   spaces", "Multiple spaces"),
        ("\n\nNew\nlines\n\n", "New lines"),
        ("Already clean", "Already clean"),
        ("", ""),
        (None, ""),
    ])
    def test_clean_text(self, text, expected):
        """テキストクリーニングのテスト"""
        result = clean_text(text)
        assert result == expected


class TestSleepFunctions:
    """待機関数のテスト"""
    
    @patch('time.sleep')
    @patch('random.uniform')
    def test_human_sleep(self, mock_uniform, mock_sleep):
        """人間らしい待機のテスト"""
        mock_uniform.return_value = 2.5
        
        human_sleep(1.0, 3.0)
        
        mock_uniform.assert_called_once_with(1.0, 3.0)
        mock_sleep.assert_called_once_with(2.5)
    
    @patch('time.sleep')
    def test_exponential_backoff_sleep(self, mock_sleep):
        """指数的バックオフ待機のテスト"""
        with patch('random.uniform', return_value=0):
            exponential_backoff_sleep(0, base_delay=1.0)
            exponential_backoff_sleep(1, base_delay=1.0)
            exponential_backoff_sleep(2, base_delay=1.0)
        
        # 待機時間が指数的に増加することを確認
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == 1.0  # 2^0 * 1.0
        assert calls[1][0][0] == 2.0  # 2^1 * 1.0
        assert calls[2][0][0] == 4.0  # 2^2 * 1.0


class TestInstagramErrorHandling:
    """Instagramエラー処理のテスト"""
    
    def test_check_instagram_login_status_logged_in(self, mock_driver):
        """ログイン状態のチェック（ログイン済み）"""
        mock_driver.current_url = "https://www.instagram.com/explore/"
        mock_driver.find_elements.return_value = [Mock()]  # ナビゲーション要素あり
        
        result = check_instagram_login_status(mock_driver)
        assert result is True
    
    def test_check_instagram_login_status_not_logged_in(self, mock_driver):
        """ログイン状態のチェック（未ログイン）"""
        mock_driver.current_url = "https://www.instagram.com/accounts/login/"
        
        result = check_instagram_login_status(mock_driver)
        assert result is False
    
    def test_detect_rate_limiting_detected(self, mock_driver):
        """レート制限検知（制限あり）"""
        mock_driver.page_source = "Please wait a few minutes before trying again"
        
        result = detect_rate_limiting(mock_driver)
        assert result is True
    
    def test_detect_rate_limiting_not_detected(self, mock_driver):
        """レート制限検知（制限なし）"""
        mock_driver.page_source = "Normal page content"
        mock_driver.find_element.side_effect = Exception("Element not found")
        
        result = detect_rate_limiting(mock_driver)
        assert result is False
    
    def test_handle_instagram_errors_login_required(self, mock_driver, mock_logger):
        """Instagramエラー処理（ログイン必要）"""
        with patch('src.scraper.utils.check_instagram_login_status', return_value=False):
            result = handle_instagram_errors(mock_driver, mock_logger)
            assert result == 'login_required'
    
    def test_handle_instagram_errors_rate_limited(self, mock_driver, mock_logger):
        """Instagramエラー処理（レート制限）"""
        with patch('src.scraper.utils.check_instagram_login_status', return_value=True):
            with patch('src.scraper.utils.detect_rate_limiting', return_value=True):
                result = handle_instagram_errors(mock_driver, mock_logger)
                assert result == 'rate_limited'


class TestErrorRecovery:
    """エラー復旧機能のテスト"""
    
    @pytest.mark.parametrize("error_type,expected_key", [
        ('login_required', 'login_required'),
        ('rate_limited', 'rate_limited'),
        ('blocked', 'blocked'),
        ('dom_changed', 'dom_changed'),
        ('unknown_error', 'unknown'),
    ])
    def test_get_error_recovery_suggestions(self, error_type, expected_key):
        """エラー復旧提案の取得"""
        suggestions = get_error_recovery_suggestions(error_type)
        
        assert 'message' in suggestions
        assert 'action' in suggestions
        assert 'wait_time' in suggestions
        assert 'retry_recommended' in suggestions
        
        # 特定のエラータイプの確認
        if expected_key == 'login_required':
            assert suggestions['retry_recommended'] is False
        elif expected_key == 'rate_limited':
            assert suggestions['wait_time'] > 0
            assert suggestions['retry_recommended'] is True


class TestRetryDecorator:
    """リトライデコレータのテスト"""
    
    def test_retry_on_failure_success(self):
        """リトライデコレータ（成功）"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure_eventual_success(self):
        """リトライデコレータ（最終的に成功）"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def eventually_successful_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("一時的なエラー")
            return "success"
        
        with patch('time.sleep'):
            result = eventually_successful_function()
        
        assert result == "success"
        assert call_count == 3
    
    def test_retry_on_failure_all_failed(self):
        """リトライデコレータ（すべて失敗）"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise Exception("永続的なエラー")
        
        with patch('time.sleep'):
            with pytest.raises(Exception) as exc_info:
                always_failing_function()
        
        assert str(exc_info.value) == "永続的なエラー"
        assert call_count == 3