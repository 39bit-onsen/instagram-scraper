#!/usr/bin/env python3
"""
Instagram ハッシュタグ情報取得
メインのスクレイピング機能を提供
"""

import re
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .utils import (
    setup_logger, human_sleep, wait_for_element, safe_click,
    get_element_text, get_element_attribute, extract_number_from_text,
    clean_text, retry_on_failure, safe_find_elements,
    exponential_backoff_sleep, handle_instagram_errors, get_error_recovery_suggestions
)
from .login import InstagramLogin


class InstagramHashtagScraper:
    """Instagram ハッシュタグスクレイパー"""
    
    def __init__(self, headless: bool = False, cookies_dir: str = "cookies"):
        """
        初期化
        
        Args:
            headless: ヘッドレスモード
            cookies_dir: Cookie保存ディレクトリ
        """
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.login_manager = InstagramLogin(cookies_dir)
        self.logger = setup_logger("hashtag_scraper")
        
    def setup_driver(self) -> webdriver.Chrome:
        """WebDriverをセットアップ"""
        return self.login_manager.setup_driver(self.headless)
    
    def initialize_session(self) -> bool:
        """
        セッションを初期化（ログイン状態の確立）
        
        Returns:
            初期化成功かどうか
        """
        try:
            self.logger.info("セッションを初期化しています...")
            
            # ドライバー起動
            self.driver = self.setup_driver()
            
            # Cookie認証を試行
            if self.login_manager.load_cookies(self.driver):
                self.logger.info("✅ Cookie認証に成功しました")
                return True
            else:
                self.logger.warning("❌ Cookie認証に失敗しました")
                self.logger.info("手動ログインが必要です: python src/scraper/login.py")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ セッション初期化エラー: {e}")
            return False
    
    def fetch_hashtag_info(self, hashtag: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        ハッシュタグ情報を取得
        
        Args:
            hashtag: ハッシュタグ名（#は不要）
            
        Returns:
            取得されたハッシュタグ情報
        """
        if not self.driver:
            raise Exception("セッションが初期化されていません")
        
        # ハッシュタグ名のクリーニング
        clean_hashtag = hashtag.lstrip('#').strip()
        
        # データ構造の初期化
        hashtag_data = {
            "hashtag": clean_hashtag,
            "url": f"https://www.instagram.com/explore/tags/{clean_hashtag}/",
            "post_count": 0,
            "related_tags": [],
            "top_posts": [],
            "error": None,
            "scraped_at": time.time()
        }
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"ハッシュタグ情報を取得します: #{clean_hashtag} (試行 {attempt + 1}/{max_retries})")
                
                # ハッシュタグページにアクセス
                self.driver.get(hashtag_data["url"])
                human_sleep(5.0, 5.0)  # 固定で5秒待機
                
                # エラー状態チェック
                error_type = handle_instagram_errors(self.driver, self.logger)
                
                if error_type == 'login_required':
                    hashtag_data["error"] = "ログインセッションが切れています"
                    return hashtag_data
                    
                elif error_type == 'rate_limited':
                    if attempt < max_retries - 1:
                        suggestion = get_error_recovery_suggestions(error_type)
                        self.logger.warning(f"レート制限検知。{suggestion['wait_time']}秒待機します")
                        exponential_backoff_sleep(attempt, base_delay=suggestion['wait_time'])
                        continue
                    else:
                        hashtag_data["error"] = "レート制限により取得できませんでした"
                        return hashtag_data
                        
                elif error_type == 'blocked':
                    hashtag_data["error"] = "アカウントがブロックされています"
                    return hashtag_data
                
                # データ取得実行
                hashtag_data["post_count"] = self._extract_post_count()
                hashtag_data["related_tags"] = self._extract_related_tags()
                hashtag_data["top_posts"] = self._extract_top_posts()
                
                self.logger.info(f"✅ データ取得完了: #{clean_hashtag} ({hashtag_data['post_count']:,} 投稿)")
                return hashtag_data
                
            except Exception as e:
                error_msg = f"データ取得エラー (試行 {attempt + 1}): {e}"
                self.logger.error(f"❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    exponential_backoff_sleep(attempt)
                else:
                    hashtag_data["error"] = f"最大リトライ回数に達しました: {e}"
        
        return hashtag_data
    
    def _extract_post_count(self) -> int:
        """投稿数を抽出"""
        try:
            # 複数のセレクタパターンを試行
            selectors = [
                "//header//span[contains(text(), 'posts') or contains(text(), '投稿')]",
                "//span[contains(text(), 'posts')]",
                "//div[contains(@class, '_ac69')]//span",
                "//header//div//span[contains(text(), ',')]"
            ]
            
            for selector in selectors:
                try:
                    element = wait_for_element(
                        self.driver, 
                        (By.XPATH, selector), 
                        timeout=5
                    )
                    
                    if element:
                        text = element.text
                        if text and ('post' in text.lower() or '投稿' in text or ',' in text):
                            count = extract_number_from_text(text)
                            if count > 0:
                                self.logger.info(f"投稿数取得成功: {count:,}")
                                return count
                                
                except Exception:
                    continue
            
            # セレクタが見つからない場合の代替手段
            self.logger.warning("⚠️ 投稿数セレクタが見つかりません")
            
            # ページソースから直接検索
            page_source = self.driver.page_source
            post_patterns = [
                r'(\d{1,3}(?:,\d{3})*)\s*posts',
                r'(\d{1,3}(?:,\d{3})*)\s*投稿',
                r'"edge_hashtag_to_media":{"count":(\d+)'
            ]
            
            for pattern in post_patterns:
                matches = re.findall(pattern, page_source, re.IGNORECASE)
                if matches:
                    count_str = matches[0]
                    count = extract_number_from_text(count_str)
                    if count > 0:
                        self.logger.info(f"投稿数をページソースから取得: {count:,}")
                        return count
            
            self.logger.warning("投稿数を取得できませんでした")
            return 0
            
        except Exception as e:
            self.logger.error(f"投稿数取得エラー: {e}")
            return 0
    
    def _extract_related_tags(self) -> List[str]:
        """関連タグを抽出"""
        try:
            related_tags = []
            
            # 関連タグのセレクタパターン
            selectors = [
                "//a[contains(@href, '/explore/tags/')]",
                "//div[contains(@class, 'related')]//a",
                "//span[contains(text(), '#')]//parent::a"
            ]
            
            for selector in selectors:
                try:
                    elements = safe_find_elements(
                        self.driver, 
                        (By.XPATH, selector), 
                        timeout=5
                    )
                    
                    for element in elements[:10]:  # 最大10個まで
                        try:
                            href = element.get_attribute('href')
                            if href and '/explore/tags/' in href:
                                tag_name = href.split('/explore/tags/')[-1].rstrip('/')
                                if tag_name and tag_name not in related_tags:
                                    related_tags.append(tag_name)
                        except Exception:
                            continue
                    
                    if related_tags:
                        break
                        
                except Exception:
                    continue
            
            # 重複除去とソート
            unique_tags = list(set(related_tags))[:10]
            self.logger.info(f"関連タグ取得: {len(unique_tags)}個")
            
            return unique_tags
            
        except Exception as e:
            self.logger.error(f"関連タグ取得エラー: {e}")
            return []
    
    def _extract_top_posts(self) -> List[Dict[str, Any]]:
        """トップ投稿を抽出"""
        try:
            top_posts = []
            
            # トップ投稿セクションまでスクロール
            try:
                self.driver.execute_script("window.scrollTo(0, 500);")
                human_sleep(2.0, 3.0)
            except Exception:
                pass
            
            # 投稿要素のセレクタパターン
            selectors = [
                "//article//a[contains(@href, '/p/')]",
                "//div[contains(@class, '_aabd')]//a",
                "//div[contains(@class, 'v1Nh3')]//a"
            ]
            
            for selector in selectors:
                try:
                    post_elements = safe_find_elements(
                        self.driver, 
                        (By.XPATH, selector), 
                        timeout=5
                    )
                    
                    if post_elements:
                        break
                        
                except Exception:
                    continue
            
            # 投稿情報を抽出（最大12個）
            for i, post_element in enumerate(post_elements[:12]):
                try:
                    post_data = self._extract_post_data(post_element)
                    if post_data:
                        top_posts.append(post_data)
                        
                except Exception as e:
                    self.logger.warning(f"投稿 {i+1} の取得に失敗: {e}")
                    continue
            
            self.logger.info(f"トップ投稿取得: {len(top_posts)}個")
            return top_posts
            
        except Exception as e:
            self.logger.error(f"トップ投稿取得エラー: {e}")
            return []
    
    def _extract_post_data(self, post_element) -> Optional[Dict[str, Any]]:
        """個別投稿のデータを抽出"""
        try:
            post_data = {}
            
            # 投稿URL
            post_url = post_element.get_attribute('href')
            if post_url:
                post_data['url'] = post_url
                post_data['post_id'] = post_url.split('/p/')[-1].rstrip('/')
            
            # 画像URL
            img_element = post_element.find_element(By.TAG_NAME, 'img')
            if img_element:
                img_url = img_element.get_attribute('src')
                if img_url:
                    post_data['image_url'] = img_url
                
                # alt属性からキャプション情報
                alt_text = img_element.get_attribute('alt')
                if alt_text and alt_text != 'Instagram':
                    post_data['alt_text'] = clean_text(alt_text)
            
            # 投稿タイプの判定
            post_data['type'] = self._determine_post_type(post_element)
            
            return post_data if post_data else None
            
        except Exception as e:
            self.logger.warning(f"投稿データ抽出エラー: {e}")
            return None
    
    def _determine_post_type(self, post_element) -> str:
        """投稿タイプを判定"""
        try:
            # 動画インジケーターをチェック
            video_indicators = post_element.find_elements(
                By.XPATH, ".//span[contains(@aria-label, 'Video') or contains(@aria-label, '動画')]"
            )
            if video_indicators:
                return "video"
            
            # カルーセル（複数画像）インジケーターをチェック
            carousel_indicators = post_element.find_elements(
                By.XPATH, ".//span[contains(@aria-label, 'Carousel') or contains(@aria-label, 'Album')]"
            )
            if carousel_indicators:
                return "carousel"
            
            # リールインジケーターをチェック
            reel_indicators = post_element.find_elements(
                By.XPATH, ".//span[contains(@aria-label, 'Reel') or contains(@aria-label, 'リール')]"
            )
            if reel_indicators:
                return "reel"
            
            # デフォルトは画像
            return "image"
            
        except Exception:
            return "image"
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        if hasattr(self.login_manager, 'cleanup'):
            self.login_manager.cleanup()


def fetch_hashtag_data(hashtag: str, headless: bool = True) -> Dict[str, Any]:
    """
    ハッシュタグデータを取得する便利関数
    
    Args:
        hashtag: ハッシュタグ名
        headless: ヘッドレスモード
        
    Returns:
        ハッシュタグデータ
    """
    scraper = InstagramHashtagScraper(headless=headless)
    
    try:
        # セッション初期化
        if not scraper.initialize_session():
            return {
                "hashtag": hashtag.lstrip('#'),
                "error": "セッション初期化に失敗しました。ログインが必要です。",
                "post_count": 0,
                "related_tags": [],
                "top_posts": []
            }
        
        # データ取得
        return scraper.fetch_hashtag_info(hashtag)
        
    finally:
        scraper.cleanup()


def main():
    """メイン関数 - テスト実行"""
    print("=== Instagram ハッシュタグスクレイパー テスト ===")
    
    # テスト用ハッシュタグ
    test_hashtag = input("テストするハッシュタグを入力してください（#不要）: ").strip()
    
    if not test_hashtag:
        test_hashtag = "test"
        print(f"デフォルトハッシュタグを使用: #{test_hashtag}")
    
    print(f"\nハッシュタグ #{test_hashtag} の情報を取得します...")
    
    # データ取得実行
    result = fetch_hashtag_data(test_hashtag, headless=False)
    
    # 結果表示
    print("\n=== 取得結果 ===")
    print(f"ハッシュタグ: #{result['hashtag']}")
    print(f"投稿数: {result['post_count']:,}")
    print(f"関連タグ数: {len(result['related_tags'])}")
    print(f"トップ投稿数: {len(result['top_posts'])}")
    
    if result.get('error'):
        print(f"エラー: {result['error']}")
    
    if result['related_tags']:
        print(f"関連タグ: {', '.join(result['related_tags'][:5])}")
    
    print("\n✅ テストが完了しました")


if __name__ == "__main__":
    main()