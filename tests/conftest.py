#!/usr/bin/env python3
"""
pytest共通設定とフィクスチャ
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# テストデータのインポート
from tests.fixtures.mock_data import (
    MOCK_HASHTAG_DATA,
    ERROR_HASHTAG_DATA,
    MOCK_CSV_CONTENT,
    MOCK_SCHEDULER_CONFIG,
    MOCK_COOKIES
)


@pytest.fixture
def mock_driver():
    """モックWebDriverを提供"""
    driver = MagicMock()
    driver.current_url = "https://www.instagram.com/"
    driver.page_source = "<html><body>Mock page</body></html>"
    driver.get_cookies.return_value = MOCK_COOKIES
    return driver


@pytest.fixture
def temp_dir():
    """一時ディレクトリを提供"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_tags_csv(temp_dir):
    """モックタグCSVファイルを作成"""
    csv_path = temp_dir / "tags.csv"
    csv_path.write_text(MOCK_CSV_CONTENT)
    return str(csv_path)


@pytest.fixture
def mock_cookies_file(temp_dir):
    """モックcookieファイルを作成"""
    cookies_dir = temp_dir / "cookies"
    cookies_dir.mkdir()
    cookies_file = cookies_dir / "ig_cookies.json"
    cookies_file.write_text(json.dumps(MOCK_COOKIES))
    return str(cookies_file)


@pytest.fixture
def mock_config_file(temp_dir):
    """モック設定ファイルを作成"""
    config_file = temp_dir / "scheduler.json"
    config_file.write_text(json.dumps(MOCK_SCHEDULER_CONFIG))
    return str(config_file)


@pytest.fixture
def mock_logger():
    """モックロガーを提供"""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    return logger


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, temp_dir):
    """テスト環境をセットアップ"""
    # 環境変数の設定
    monkeypatch.setenv("IG_ID", "test_user")
    monkeypatch.setenv("IG_PASS", "test_password")
    
    # データディレクトリの設定
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    monkeypatch.setattr("pathlib.Path.cwd", lambda: temp_dir)
    
    yield
    
    # クリーンアップは自動的に行われる


@pytest.fixture
def mock_selenium_elements():
    """Selenium要素のモックを提供"""
    # 投稿数要素
    post_count_element = MagicMock()
    post_count_element.text = "1,234,567 posts"
    
    # 関連タグ要素
    tag_elements = []
    for i, tag in enumerate(["test1", "test2", "test3"]):
        elem = MagicMock()
        elem.get_attribute.return_value = f"/explore/tags/{tag}/"
        tag_elements.append(elem)
    
    # トップ投稿要素
    post_elements = []
    for i in range(2):
        elem = MagicMock()
        elem.get_attribute.return_value = f"https://www.instagram.com/p/TEST{i}/"
        img = MagicMock()
        img.get_attribute.side_effect = lambda attr: {
            'src': f"https://example.com/image{i}.jpg",
            'alt': f"Test post {i}"
        }.get(attr)
        elem.find_element.return_value = img
        post_elements.append(elem)
    
    return {
        'post_count': post_count_element,
        'tags': tag_elements,
        'posts': post_elements
    }


@pytest.fixture
def mock_time():
    """時間関連のモックを提供"""
    with patch('time.time', return_value=1234567890.0):
        with patch('time.sleep'):
            yield


# テストマーカーの設定
def pytest_configure(config):
    """pytest設定のカスタマイズ"""
    config.addinivalue_line(
        "markers", "requires_instagram: Instagramアカウントが必要なテスト"
    )


# テスト実行前後のフック
def pytest_runtest_setup(item):
    """各テスト実行前の処理"""
    # ネットワーク関連のテストをスキップする設定
    if 'network' in item.keywords and item.config.getoption("--no-network"):
        pytest.skip("ネットワークテストはスキップされました")


# カスタムコマンドラインオプション
def pytest_addoption(parser):
    """カスタムオプションの追加"""
    parser.addoption(
        "--no-network",
        action="store_true",
        default=False,
        help="ネットワークを使用するテストをスキップ"
    )
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="実行時間の長いテストも実行"
    )