#!/usr/bin/env python3
"""
Instagram スクレイパー ユーティリティ関数
共通的な機能を提供
"""

import os
import time
import random
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# セレクタ定義（DOM変更に対応しやすくするため）
SELECTORS = {
    "login": {
        "username": "input[name='username']",
        "password": "input[name='password']",
        "submit": "button[type='submit']",
        "verification_code": "input[name='verificationCode']"
    },
    "hashtag": {
        "post_count": "span:contains('posts')",
        "post_count_alt": "header section div span",
        "related_tags": "a[href*='/explore/tags/']",
        "top_posts": "article a",
        "top_images": "article img",
        "post_link": "a[href*='/p/']"
    },
    "post": {
        "likes": "section span[class*='_aami']",
        "comments": "section span[class*='_aacl']",
        "caption": "article div[class*='_a9zs'] span",
        "timestamp": "time[datetime]"
    },
    "navigation": {
        "next_button": "button[aria-label='次へ']",
        "close_button": "button[aria-label='閉じる']"
    }
}


def setup_logger(name: str = "instagram_scraper", level: str = "INFO", 
                log_file: Optional[str] = None) -> logging.Logger:
    """
    ログ設定を初期化
    
    Args:
        name: ロガー名
        level: ログレベル
        log_file: ログファイルパス
        
    Returns:
        設定済みロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 既存のハンドラーをクリア
    logger.handlers.clear()
    
    # フォーマッター設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラー（指定時のみ）
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def human_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """
    人間らしいランダムな待機
    
    Args:
        min_seconds: 最小待機時間
        max_seconds: 最大待機時間
    """
    sleep_time = random.uniform(min_seconds, max_seconds)
    time.sleep(sleep_time)


def wait_for_element(driver: webdriver.Chrome, locator: tuple, 
                    timeout: int = 10, poll_frequency: float = 0.5) -> Optional[any]:
    """
    要素の出現を待機
    
    Args:
        driver: WebDriverインスタンス
        locator: 要素のロケーター (By.XPATH, "//div")
        timeout: 待機時間上限
        poll_frequency: ポーリング間隔
        
    Returns:
        見つかった要素、またはNone
    """
    try:
        wait = WebDriverWait(driver, timeout, poll_frequency)
        element = wait.until(EC.presence_of_element_located(locator))
        return element
    except TimeoutException:
        return None


def wait_for_clickable(driver: webdriver.Chrome, locator: tuple, 
                      timeout: int = 10) -> Optional[any]:
    """
    クリック可能な要素を待機
    
    Args:
        driver: WebDriverインスタンス
        locator: 要素のロケーター
        timeout: 待機時間上限
        
    Returns:
        クリック可能な要素、またはNone
    """
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        return element
    except TimeoutException:
        return None


def safe_click(driver: webdriver.Chrome, element: any, 
               max_retries: int = 3) -> bool:
    """
    安全なクリック実行（リトライ機能付き）
    
    Args:
        driver: WebDriverインスタンス
        element: クリック対象要素
        max_retries: 最大リトライ回数
        
    Returns:
        クリック成功かどうか
    """
    for attempt in range(max_retries):
        try:
            # 要素が見えるまでスクロール
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            human_sleep(0.5, 1.0)
            
            # クリック実行
            element.click()
            human_sleep(0.5, 1.0)
            return True
            
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"⚠️ クリック失敗: {e}")
                return False
            human_sleep(1.0, 2.0)
    
    return False


def get_element_text(driver: webdriver.Chrome, locator: tuple, 
                    default: str = "") -> str:
    """
    要素のテキストを安全に取得
    
    Args:
        driver: WebDriverインスタンス
        locator: 要素のロケーター
        default: 要素が見つからない場合のデフォルト値
        
    Returns:
        要素のテキスト
    """
    try:
        element = wait_for_element(driver, locator, timeout=5)
        if element:
            return element.text.strip()
        return default
    except Exception:
        return default


def get_element_attribute(driver: webdriver.Chrome, locator: tuple, 
                         attribute: str, default: str = "") -> str:
    """
    要素の属性値を安全に取得
    
    Args:
        driver: WebDriverインスタンス
        locator: 要素のロケーター
        attribute: 属性名
        default: 要素が見つからない場合のデフォルト値
        
    Returns:
        属性値
    """
    try:
        element = wait_for_element(driver, locator, timeout=5)
        if element:
            return element.get_attribute(attribute) or default
        return default
    except Exception:
        return default


def scroll_to_bottom(driver: webdriver.Chrome, max_scrolls: int = 3) -> None:
    """
    ページの最下部まで段階的にスクロール
    
    Args:
        driver: WebDriverインスタンス
        max_scrolls: 最大スクロール回数
    """
    for i in range(max_scrolls):
        # 現在のページ高さを取得
        current_height = driver.execute_script("return document.body.scrollHeight")
        
        # スクロール実行
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # 新しいコンテンツの読み込み待機
        human_sleep(2.0, 3.0)
        
        # 新しいページ高さを取得
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        # スクロール完了チェック
        if new_height == current_height:
            break


def extract_number_from_text(text: str) -> int:
    """
    テキストから数値を抽出
    
    Args:
        text: 対象テキスト（例: "1,234 posts"）
        
    Returns:
        抽出された数値
    """
    import re
    
    # カンマを除去して数値を抽出
    numbers = re.findall(r'[\d,]+', text)
    if numbers:
        # 最初の数値を取得してカンマを除去
        return int(numbers[0].replace(',', ''))
    return 0


def clean_text(text: str) -> str:
    """
    テキストのクリーニング
    
    Args:
        text: 対象テキスト
        
    Returns:
        クリーニング済みテキスト
    """
    if not text:
        return ""
    
    # 余分な空白を除去
    text = ' '.join(text.split())
    
    # 特殊文字の除去
    text = text.replace('\n', ' ').replace('\t', ' ')
    
    return text.strip()


def create_directory_if_not_exists(path: Union[str, Path]) -> Path:
    """
    ディレクトリが存在しない場合は作成
    
    Args:
        path: ディレクトリパス
        
    Returns:
        作成されたディレクトリのPathオブジェクト
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_month_dir(base_dir: Union[str, Path]) -> Path:
    """
    現在の年月のディレクトリを取得・作成
    
    Args:
        base_dir: ベースディレクトリ
        
    Returns:
        年月ディレクトリのPathオブジェクト
    """
    from datetime import datetime
    
    base_path = Path(base_dir)
    current_month = datetime.now().strftime("%Y%m")
    month_dir = base_path / current_month
    
    return create_directory_if_not_exists(month_dir)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    失敗時のリトライデコレーター
    
    Args:
        max_retries: 最大リトライ回数
        delay: リトライ間隔
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # 指数的バックオフ
                    continue
            
            # 全てのリトライが失敗した場合
            raise last_exception
        return wrapper
    return decorator


def safe_find_elements(driver: webdriver.Chrome, locator: tuple, 
                      timeout: int = 5) -> List[any]:
    """
    要素の安全な検索（複数要素）
    
    Args:
        driver: WebDriverインスタンス
        locator: 要素のロケーター
        timeout: 待機時間上限
        
    Returns:
        見つかった要素のリスト
    """
    try:
        wait = WebDriverWait(driver, timeout)
        elements = wait.until(EC.presence_of_all_elements_located(locator))
        return elements
    except TimeoutException:
        return []


def get_selector(category: str, key: str) -> str:
    """
    セレクタを取得
    
    Args:
        category: セレクタのカテゴリ
        key: セレクタのキー
        
    Returns:
        セレクタ文字列
    """
    return SELECTORS.get(category, {}).get(key, "")


def is_element_visible(driver: webdriver.Chrome, locator: tuple) -> bool:
    """
    要素が表示されているかチェック
    
    Args:
        driver: WebDriverインスタンス
        locator: 要素のロケーター
        
    Returns:
        要素が表示されているかどうか
    """
    try:
        element = driver.find_element(*locator)
        return element.is_displayed()
    except NoSuchElementException:
        return False


def wait_for_page_load(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """
    ページの読み込み完了を待機
    
    Args:
        driver: WebDriverインスタンス
        timeout: 待機時間上限
        
    Returns:
        読み込み完了かどうか
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        return True
    except TimeoutException:
        return False


# ログ設定の初期化
logger = setup_logger()

# 使用例のためのサンプル関数
def demo_usage():
    """ユーティリティ関数の使用例"""
    print("=== Instagram スクレイパー ユーティリティ関数のデモ ===")
    
    # ログ設定
    logger.info("ログ設定のテスト")
    
    # 数値抽出テスト
    test_text = "1,234 posts"
    number = extract_number_from_text(test_text)
    print(f"数値抽出: '{test_text}' -> {number}")
    
    # テキストクリーニングテスト
    dirty_text = "  Hello\n\tWorld  "
    clean = clean_text(dirty_text)
    print(f"テキストクリーニング: '{dirty_text}' -> '{clean}'")
    
    # ディレクトリ作成テスト
    test_dir = get_current_month_dir("test_data")
    print(f"月別ディレクトリ: {test_dir}")
    
    print("✅ デモが完了しました")


if __name__ == "__main__":
    demo_usage()