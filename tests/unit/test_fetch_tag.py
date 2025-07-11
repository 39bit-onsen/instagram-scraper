#!/usr/bin/env python3
"""
fetch_tagモジュールのユニットテスト
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import time

from src.scraper.fetch_tag import InstagramHashtagScraper, fetch_hashtag_data
from tests.fixtures.mock_data import MOCK_HASHTAG_DATA, MOCK_HASHTAG_PAGE_HTML


class TestInstagramHashtagScraper:
    """InstagramHashtagScraperクラスのテスト"""
    
    @pytest.fixture
    def scraper(self):
        """スクレイパーインスタンスを作成"""
        with patch('src.scraper.fetch_tag.InstagramLogin'):
            scraper = InstagramHashtagScraper(headless=True)
            return scraper
    
    def test_init(self, scraper):
        """初期化のテスト"""
        assert scraper.headless is True
        assert scraper.driver is None
        assert scraper.login_manager is not None
        assert scraper.logger is not None
    
    @patch('src.scraper.fetch_tag.webdriver')
    def test_setup_driver(self, mock_webdriver, scraper):
        """WebDriverセットアップのテスト"""
        mock_driver = MagicMock()
        scraper.login_manager.setup_driver.return_value = mock_driver
        
        driver = scraper.setup_driver()
        
        assert driver == mock_driver
        scraper.login_manager.setup_driver.assert_called_once_with(True)
    
    def test_initialize_session_success(self, scraper, mock_driver):
        """セッション初期化のテスト（成功）"""
        scraper.login_manager.setup_driver.return_value = mock_driver
        scraper.login_manager.load_cookies.return_value = True
        
        with patch('src.scraper.fetch_tag.handle_instagram_errors', return_value='none'):
            with patch('src.scraper.fetch_tag.human_sleep'):
                result = scraper.initialize_session()
        
        assert result is True
        assert scraper.driver == mock_driver
    
    def test_initialize_session_cookie_failed(self, scraper, mock_driver):
        """セッション初期化のテスト（Cookie認証失敗）"""
        scraper.login_manager.setup_driver.return_value = mock_driver
        scraper.login_manager.load_cookies.return_value = False
        
        result = scraper.initialize_session()
        
        assert result is False
    
    def test_initialize_session_login_required(self, scraper, mock_driver):
        """セッション初期化のテスト（ログイン必要）"""
        scraper.login_manager.setup_driver.return_value = mock_driver
        scraper.login_manager.load_cookies.return_value = True
        
        with patch('src.scraper.fetch_tag.handle_instagram_errors', return_value='login_required'):
            with patch('src.scraper.fetch_tag.get_error_recovery_suggestions') as mock_suggestions:
                mock_suggestions.return_value = {
                    'message': 'ログインが必要です',
                    'action': 'ログインしてください'
                }
                with patch('src.scraper.fetch_tag.human_sleep'):
                    result = scraper.initialize_session()
        
        assert result is False
    
    def test_fetch_hashtag_info_success(self, scraper, mock_driver, mock_selenium_elements):
        """ハッシュタグ情報取得のテスト（成功）"""
        scraper.driver = mock_driver
        
        # モック設定
        with patch('src.scraper.fetch_tag.handle_instagram_errors', return_value='none'):
            with patch('src.scraper.fetch_tag.human_sleep'):
                with patch.object(scraper, '_extract_post_count', return_value=1234567):
                    with patch.object(scraper, '_extract_related_tags', return_value=['test1', 'test2']):
                        with patch.object(scraper, '_extract_top_posts', return_value=[]):
                            result = scraper.fetch_hashtag_info('test')
        
        assert result['hashtag'] == 'test'
        assert result['post_count'] == 1234567
        assert result['related_tags'] == ['test1', 'test2']
        assert result['error'] is None
    
    def test_fetch_hashtag_info_no_driver(self, scraper):
        """ハッシュタグ情報取得のテスト（ドライバー未初期化）"""
        scraper.driver = None
        
        with pytest.raises(Exception) as exc_info:
            scraper.fetch_hashtag_info('test')
        
        assert "セッションが初期化されていません" in str(exc_info.value)
    
    def test_fetch_hashtag_info_rate_limited(self, scraper, mock_driver):
        """ハッシュタグ情報取得のテスト（レート制限）"""
        scraper.driver = mock_driver
        
        with patch('src.scraper.fetch_tag.handle_instagram_errors', return_value='rate_limited'):
            with patch('src.scraper.fetch_tag.get_error_recovery_suggestions') as mock_suggestions:
                mock_suggestions.return_value = {'wait_time': 60}
                with patch('src.scraper.fetch_tag.exponential_backoff_sleep'):
                    with patch('src.scraper.fetch_tag.human_sleep'):
                        result = scraper.fetch_hashtag_info('test', max_retries=1)
        
        assert result['error'] == 'レート制限により取得できませんでした'
    
    def test_extract_post_count_success(self, scraper, mock_driver):
        """投稿数抽出のテスト（成功）"""
        scraper.driver = mock_driver
        
        # モック要素の設定
        mock_element = MagicMock()
        mock_element.text = "1,234,567 posts"
        
        with patch('src.scraper.fetch_tag.wait_for_element', return_value=mock_element):
            result = scraper._extract_post_count()
        
        assert result == 1234567
    
    def test_extract_post_count_from_page_source(self, scraper, mock_driver):
        """投稿数抽出のテスト（ページソースから）"""
        scraper.driver = mock_driver
        mock_driver.page_source = 'Some content "edge_hashtag_to_media":{"count":9876543} more content'
        
        with patch('src.scraper.fetch_tag.wait_for_element', return_value=None):
            with patch('src.scraper.utils.detect_dom_changes', return_value=[]):
                result = scraper._extract_post_count()
        
        assert result == 9876543
    
    def test_extract_related_tags(self, scraper, mock_driver):
        """関連タグ抽出のテスト"""
        scraper.driver = mock_driver
        
        # モック要素の設定
        mock_elements = []
        for tag in ['tag1', 'tag2', 'tag3']:
            elem = MagicMock()
            elem.get_attribute.return_value = f'/explore/tags/{tag}/'
            mock_elements.append(elem)
        
        with patch('src.scraper.fetch_tag.safe_find_elements', return_value=mock_elements):
            result = scraper._extract_related_tags()
        
        assert len(result) == 3
        assert 'tag1' in result
        assert 'tag2' in result
        assert 'tag3' in result
    
    def test_extract_top_posts(self, scraper, mock_driver):
        """トップ投稿抽出のテスト"""
        scraper.driver = mock_driver
        
        # モック投稿要素の設定
        mock_posts = []
        for i in range(3):
            post_elem = MagicMock()
            post_elem.get_attribute.return_value = f'https://www.instagram.com/p/POST{i}/'
            
            img_elem = MagicMock()
            img_elem.get_attribute.side_effect = lambda attr: {
                'src': f'https://example.com/img{i}.jpg',
                'alt': f'Post {i} description'
            }.get(attr)
            
            post_elem.find_element.return_value = img_elem
            post_elem.find_elements.return_value = []  # タイプインジケーターなし
            
            mock_posts.append(post_elem)
        
        with patch('src.scraper.fetch_tag.safe_find_elements', return_value=mock_posts):
            with patch('src.scraper.fetch_tag.human_sleep'):
                result = scraper._extract_top_posts()
        
        assert len(result) == 3
        assert result[0]['post_id'] == 'POST0'
        assert result[1]['image_url'] == 'https://example.com/img1.jpg'
        assert result[2]['type'] == 'image'
    
    def test_determine_post_type(self, scraper):
        """投稿タイプ判定のテスト"""
        # 画像投稿
        mock_element = MagicMock()
        mock_element.find_elements.return_value = []
        assert scraper._determine_post_type(mock_element) == 'image'
        
        # 動画投稿
        mock_video_element = MagicMock()
        mock_video_indicator = MagicMock()
        mock_video_element.find_elements.side_effect = [[mock_video_indicator], [], []]
        assert scraper._determine_post_type(mock_video_element) == 'video'
    
    def test_cleanup(self, scraper, mock_driver):
        """クリーンアップのテスト"""
        scraper.driver = mock_driver
        scraper.login_manager.cleanup = MagicMock()
        
        scraper.cleanup()
        
        mock_driver.quit.assert_called_once()
        assert scraper.driver is None
        scraper.login_manager.cleanup.assert_called_once()


class TestFetchHashtagDataFunction:
    """fetch_hashtag_data関数のテスト"""
    
    @patch('src.scraper.fetch_tag.InstagramHashtagScraper')
    def test_fetch_hashtag_data_success(self, mock_scraper_class):
        """fetch_hashtag_data関数のテスト（成功）"""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.initialize_session.return_value = True
        mock_scraper.fetch_hashtag_info.return_value = MOCK_HASHTAG_DATA
        
        result = fetch_hashtag_data('test', headless=True)
        
        assert result == MOCK_HASHTAG_DATA
        mock_scraper.initialize_session.assert_called_once()
        mock_scraper.fetch_hashtag_info.assert_called_once_with('test')
        mock_scraper.cleanup.assert_called_once()
    
    @patch('src.scraper.fetch_tag.InstagramHashtagScraper')
    def test_fetch_hashtag_data_session_failed(self, mock_scraper_class):
        """fetch_hashtag_data関数のテスト（セッション初期化失敗）"""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.initialize_session.return_value = False
        
        result = fetch_hashtag_data('test', headless=False)
        
        assert result['hashtag'] == 'test'
        assert result['error'] == 'セッション初期化に失敗しました。ログインが必要です。'
        assert result['post_count'] == 0
        mock_scraper.cleanup.assert_called_once()
    
    @patch('src.scraper.fetch_tag.InstagramHashtagScraper')
    def test_fetch_hashtag_data_with_exception(self, mock_scraper_class):
        """fetch_hashtag_data関数のテスト（例外発生時のクリーンアップ）"""
        mock_scraper = MagicMock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.initialize_session.side_effect = Exception("Test error")
        
        with pytest.raises(Exception):
            fetch_hashtag_data('test')
        
        # クリーンアップが呼ばれることを確認
        mock_scraper.cleanup.assert_called_once()