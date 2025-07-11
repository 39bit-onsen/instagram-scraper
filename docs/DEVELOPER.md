# 開発者向けガイド

Instagram ハッシュタグスクレイパーの開発に参加する方向けのガイドです。

## 📋 目次

1. [開発環境セットアップ](#開発環境セットアップ)
2. [プロジェクト構造](#プロジェクト構造)
3. [コーディング規約](#コーディング規約)
4. [テスト](#テスト)
5. [デバッグ](#デバッグ)
6. [拡張方法](#拡張方法)
7. [コントリビューション](#コントリビューション)

---

## 🛠️ 開発環境セットアップ

### 前提条件

- Python 3.10+
- Git
- VS Code または PyCharm（推奨）

### セットアップ手順

```bash
# 1. リポジトリのクローン
git clone https://github.com/39bit-onsen/instagram-scraper.git
cd instagram-scraper

# 2. 開発用仮想環境の作成
python -m venv venv-dev
source venv-dev/bin/activate  # Windows: venv-dev\Scripts\activate

# 3. 開発依存関係のインストール
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. pre-commitフックの設定
pre-commit install

# 5. 初期テストの実行
pytest
```

### 開発用依存関係

```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.10.0
black>=23.7.0
flake8>=6.0.0
isort>=5.12.0
mypy>=1.5.0
pre-commit>=3.3.0
sphinx>=7.1.0
```

---

## 📁 プロジェクト構造

```
instagram-scraper/
├── src/                    # ソースコード
│   ├── scraper/           # スクレイピング関連
│   │   ├── __init__.py
│   │   ├── fetch_tag.py   # メインロジック
│   │   ├── login.py       # 認証処理
│   │   ├── utils.py       # ユーティリティ
│   │   └── data_manager.py # データ管理
│   ├── ui/                # GUI関連
│   │   └── tag_input_gui.py
│   ├── run_batch.py       # バッチ処理
│   └── scheduler.py       # スケジューラ
├── tests/                 # テストコード
│   ├── unit/             # ユニットテスト
│   ├── integration/      # 統合テスト
│   ├── fixtures/         # テストデータ
│   └── conftest.py       # pytest設定
├── docs/                 # ドキュメント
├── config/               # 設定ファイル
├── cookies/              # Cookie保存
├── data/                 # 出力データ
└── logs/                 # ログファイル
```

### モジュール構成

#### scraper パッケージ

| ファイル | 役割 |
|----------|------|
| `fetch_tag.py` | ハッシュタグ情報取得のメインロジック |
| `login.py` | Instagram認証・Cookie管理 |
| `utils.py` | 共通ユーティリティ関数 |
| `data_manager.py` | データ保存・読み込み |

#### 主要クラス

```python
# InstagramHashtagScraper
class InstagramHashtagScraper:
    def __init__(self, headless: bool = False)
    def initialize_session(self) -> bool
    def fetch_hashtag_info(self, hashtag: str) -> Dict[str, Any]
    def cleanup(self)

# DataManager
class DataManager:
    def save_hashtag_data(self, data: Dict) -> Tuple[str, str]
    def load_hashtag_data(self, file_path: str) -> Optional[Dict]
    def get_monthly_summary(self, month: str) -> Dict
```

---

## 📝 コーディング規約

### Python スタイルガイド

- **PEP 8** に準拠
- **Black** でフォーマット
- **型ヒント** を必須使用
- **docstring** を必須記載

### 例

```python
#!/usr/bin/env python3
"""
モジュールの説明
"""

from typing import Dict, List, Optional
import logging


class ExampleClass:
    """クラスの説明"""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        初期化
        
        Args:
            config: 設定辞書
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def process_data(self, data: List[str]) -> Optional[Dict[str, int]]:
        """
        データを処理
        
        Args:
            data: 処理対象のデータリスト
            
        Returns:
            処理結果の辞書、エラー時はNone
            
        Raises:
            ValueError: 不正なデータが含まれている場合
        """
        try:
            result = {}
            for item in data:
                if not isinstance(item, str):
                    raise ValueError(f"文字列が期待されます: {type(item)}")
                result[item] = len(item)
            return result
            
        except Exception as e:
            self.logger.error(f"データ処理エラー: {e}")
            return None
```

### 命名規則

- **クラス**: CapitalCase
- **関数・変数**: snake_case
- **定数**: UPPER_SNAKE_CASE
- **プライベートメソッド**: _leading_underscore

### インポート順序

```python
# 1. 標準ライブラリ
import os
import time
from typing import Dict, List

# 2. サードパーティ
import pytest
from selenium import webdriver

# 3. ローカルモジュール
from .utils import setup_logger
from .data_manager import DataManager
```

---

## 🧪 テスト

### テスト構成

```
tests/
├── unit/                  # ユニットテスト
│   ├── test_utils.py
│   ├── test_data_manager.py
│   └── test_fetch_tag.py
├── integration/           # 統合テスト
│   ├── test_integration.py
│   └── test_e2e_scenarios.py
├── fixtures/              # テストデータ
│   └── mock_data.py
└── conftest.py           # 共通設定
```

### テストの実行

```bash
# 全テスト実行
pytest

# ユニットテストのみ
pytest tests/unit/

# カバレッジ付き
pytest --cov=src --cov-report=html

# 特定のテスト
pytest tests/unit/test_utils.py::TestSetupLogger::test_setup_logger_default

# マーカー指定
pytest -m "not slow"
```

### テストの書き方

```python
import pytest
from unittest.mock import Mock, patch

from src.scraper.utils import extract_number_from_text


class TestUtilFunctions:
    """ユーティリティ関数のテスト"""
    
    @pytest.mark.parametrize("text,expected", [
        ("1,234 posts", 1234),
        ("500K posts", 500),
        ("no numbers", 0),
    ])
    def test_extract_number_from_text(self, text, expected):
        """数値抽出のパラメータ化テスト"""
        result = extract_number_from_text(text)
        assert result == expected
    
    @patch('src.scraper.utils.webdriver.Chrome')
    def test_scraper_with_mock(self, mock_driver):
        """モックを使用したテスト"""
        mock_driver.return_value.page_source = "<html>test</html>"
        # テストロジック
```

### フィクスチャの使用

```python
@pytest.fixture
def sample_data():
    """テスト用データを提供"""
    return {
        'hashtag': 'test',
        'post_count': 1000,
        'related_tags': ['tag1', 'tag2']
    }

def test_data_processing(sample_data):
    """フィクスチャを使用したテスト"""
    assert sample_data['hashtag'] == 'test'
```

---

## 🐛 デバッグ

### ログ設定

```python
import logging

# 開発時のログレベル設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("デバッグ情報")
```

### Seleniumデバッグ

```python
# ヘッドレスモードを無効化
scraper = InstagramHashtagScraper(headless=False)

# スクリーンショット保存
driver.save_screenshot('debug.png')

# ページソース保存
with open('debug.html', 'w') as f:
    f.write(driver.page_source)

# ブレークポイント設定
import pdb; pdb.set_trace()
```

### プロファイリング

```python
import cProfile
import pstats

# パフォーマンス測定
profiler = cProfile.Profile()
profiler.enable()

# 処理実行
result = fetch_hashtag_data('test')

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

---

## 🔧 拡張方法

### 新しいデータフィールドの追加

1. **データ構造の拡張**
```python
# fetch_tag.py
def _extract_additional_info(self) -> Dict[str, Any]:
    """新しい情報を抽出"""
    return {
        'hashtag_category': self._get_category(),
        'trending_score': self._calculate_trending()
    }
```

2. **保存形式の更新**
```python
# data_manager.py
CSV_HEADERS = [
    'hashtag', 'post_count', 'related_tags', 
    'top_posts', 'hashtag_category', 'trending_score'  # 追加
]
```

### 新しい出力形式の追加

```python
class DataManager:
    def export_to_excel(self, data: List[Dict], filename: str) -> str:
        """Excel形式でエクスポート"""
        import pandas as pd
        
        df = pd.DataFrame(data)
        excel_path = self.get_file_path(filename, '.xlsx')
        df.to_excel(excel_path, index=False)
        return str(excel_path)
```

### 新しいスケジュールタイプの追加

```python
# scheduler.py
elif schedule_type == "monthly":
    day_of_month = job_config.get("day_of_month", 1)
    schedule.every().month.do(job_function).tag(job_name)
```

---

## 🤝 コントリビューション

### プルリクエストの手順

1. **Issue の作成**
   - 機能追加や バグ修正の前に Issue を作成
   - 変更内容と理由を明記

2. **ブランチの作成**
```bash
git checkout -b feature/new-feature
# または
git checkout -b fix/bug-description
```

3. **開発とテスト**
```bash
# コード変更
# テスト追加
pytest
black src/
flake8 src/
```

4. **コミット**
```bash
git add .
git commit -m "feat: 新機能の追加"
# コミットメッセージは Conventional Commits に従う
```

5. **プルリクエスト作成**
   - 変更内容の説明
   - テスト結果
   - 関連 Issue の番号

### コミットメッセージ規約

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `style`: フォーマット変更
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: その他

**例:**
```
feat(scraper): Instagram Stories の取得機能を追加

- Stories API エンドポイントの実装
- 24時間以内の Stories を取得
- JSON 形式でのデータ保存

Closes #123
```

### コードレビューのポイント

- **機能性**: 要件を満たしているか
- **品質**: バグがないか、エラーハンドリングは適切か
- **保守性**: 読みやすく拡張しやすいか
- **パフォーマンス**: 効率的に動作するか
- **セキュリティ**: 脆弱性がないか
- **テスト**: 適切なテストが含まれているか

---

## 📚 参考資料

### 外部ドキュメント

- [Selenium Documentation](https://selenium-python.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [Type Hints - PEP 484](https://peps.python.org/pep-0484/)

### 内部ドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [FAQ](FAQ.md)

---

最終更新日: 2025年1月