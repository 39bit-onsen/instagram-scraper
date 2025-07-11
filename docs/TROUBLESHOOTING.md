# トラブルシューティングガイド

Instagram ハッシュタグスクレイパーの使用中に発生する可能性のある問題と解決方法を説明します。

## 📋 目次

1. [インストール関連の問題](#インストール関連の問題)
2. [ログイン・認証の問題](#ログイン認証の問題)
3. [データ取得の問題](#データ取得の問題)
4. [パフォーマンスの問題](#パフォーマンスの問題)
5. [エラーメッセージ一覧](#エラーメッセージ一覧)
6. [高度なトラブルシューティング](#高度なトラブルシューティング)

---

## 🔧 インストール関連の問題

### 問題: pip install でエラーが発生する

#### 症状
```
ERROR: Could not find a version that satisfies the requirement...
```

#### 解決方法
1. Pythonバージョンを確認
   ```bash
   python --version
   # 3.10以降であることを確認
   ```

2. pipをアップグレード
   ```bash
   python -m pip install --upgrade pip
   ```

3. 仮想環境を再作成
   ```bash
   deactivate
   rm -rf venv  # Windows: rmdir /s venv
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### 問題: ModuleNotFoundError

#### 症状
```
ModuleNotFoundError: No module named 'selenium'
```

#### 解決方法
1. 仮想環境が有効か確認
   ```bash
   which python  # Windows: where python
   # venv内のpythonが表示されることを確認
   ```

2. 依存関係を再インストール
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### 問題: ChromeDriverが見つからない

#### 症状
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

#### 解決方法
1. ChromeDriverの自動管理を使用
   ```bash
   pip install webdriver-manager
   ```

2. 手動でPATHに追加
   ```bash
   # Linux/macOS
   export PATH=$PATH:/path/to/chromedriver
   
   # Windows
   set PATH=%PATH%;C:\path\to\chromedriver
   ```

---

## 🔐 ログイン・認証の問題

### 問題: ログインできない

#### 症状
- ログイン画面でフリーズ
- 「ユーザー名またはパスワードが正しくありません」エラー

#### 解決方法
1. 手動ログインを使用
   ```bash
   python src/scraper/login.py
   ```

2. ブラウザのセキュリティ設定を確認
   - JavaScriptが有効になっているか
   - Cookieが許可されているか

3. VPNを使用している場合は一時的に無効化

### 問題: Cookie認証が失敗する

#### 症状
```
❌ Cookie認証に失敗しました
```

#### 解決方法
1. Cookieファイルを削除して再ログイン
   ```bash
   rm cookies/ig_cookies.json
   python src/scraper/login.py
   ```

2. Cookieの有効期限を確認（通常2週間）

3. ブラウザのプロファイルをクリア
   ```python
   # src/scraper/login.pyで以下を追加
   options.add_argument('--disable-blink-features=AutomationControlled')
   ```

### 問題: 2段階認証でタイムアウト

#### 症状
- 認証コード入力画面でタイムアウト

#### 解決方法
1. タイムアウト時間を延長
   ```python
   # login.pyの該当箇所を修正
   WebDriverWait(driver, 300)  # 5分に延長
   ```

2. 認証アプリの時刻同期を確認

---

## 📊 データ取得の問題

### 問題: 投稿数が0になる

#### 症状
```
投稿数を取得できませんでした
```

#### 解決方法
1. DOM構造の変更を確認
   ```bash
   # デバッグモードで実行
   LOG_LEVEL=DEBUG python src/scraper/fetch_tag.py
   ```

2. セレクタを更新
   ```python
   # src/scraper/utils.py のSELECTORSを確認・更新
   ```

3. ページの読み込み待機時間を増やす
   ```python
   human_sleep(5.0, 7.0)  # 待機時間を延長
   ```

### 問題: レート制限エラー

#### 症状
```
⚠️ レート制限が検知されました
```

#### 解決方法
1. リクエスト間隔を増やす
   ```bash
   python src/run_batch.py --delay 10
   ```

2. バッチサイズを減らす
   ```python
   # 一度に処理するタグ数を減らす
   # CSVファイルを分割
   ```

3. 時間帯を変更
   - 深夜〜早朝の利用を推奨
   - 週末は避ける

### 問題: タグが見つからない

#### 症状
```
404 - このページはご利用いただけません
```

#### 解決方法
1. タグ名の確認
   - 特殊文字が含まれていないか
   - 実際に存在するタグか

2. URLエンコーディング
   ```python
   from urllib.parse import quote
   clean_hashtag = quote(hashtag)
   ```

---

## ⚡ パフォーマンスの問題

### 問題: 処理が遅い

#### 症状
- 1タグの処理に1分以上かかる

#### 解決方法
1. ヘッドレスモードを使用
   ```bash
   python src/run_batch.py --gui  # これを外す
   ```

2. 並列処理を検討（上級者向け）
   ```python
   from concurrent.futures import ThreadPoolExecutor
   ```

3. 不要な待機時間を削減
   ```python
   # 最小限の待機時間に調整
   human_sleep(1.0, 2.0)
   ```

### 問題: メモリ使用量が多い

#### 症状
- メモリ使用量が1GB以上

#### 解決方法
1. ブラウザインスタンスの再利用
   ```python
   # バッチ処理で同じドライバーを使い回す
   ```

2. 定期的なガベージコレクション
   ```python
   import gc
   gc.collect()
   ```

3. 画像の読み込みを無効化
   ```python
   options.add_experimental_option("prefs", {
       "profile.managed_default_content_settings.images": 2
   })
   ```

---

## ❌ エラーメッセージ一覧

### 一般的なエラー

| エラーメッセージ | 原因 | 解決方法 |
|-----------------|------|---------|
| `SessionNotCreatedException` | ChromeDriverバージョン不一致 | ChromeとDriverのバージョンを合わせる |
| `TimeoutException` | 要素が見つからない | 待機時間を延長、セレクタを確認 |
| `NoSuchElementException` | DOM要素が存在しない | ページ構造の変更を確認 |
| `WebDriverException` | ブラウザがクラッシュ | メモリ不足を確認、再起動 |
| `StaleElementReferenceException` | 要素が更新された | 要素を再取得 |

### Instagram固有のエラー

| 状況 | 症状 | 対処法 |
|------|------|--------|
| アカウントブロック | 「このアクションはブロックされています」 | 24時間待機 |
| 一時的な制限 | 「しばらくしてからもう一度実行してください」 | 1時間待機 |
| ログアウト | ログイン画面にリダイレクト | 再ログイン |
| チャレンジ要求 | 「本人確認が必要です」 | 手動で確認 |

---

## 🔍 高度なトラブルシューティング

### デバッグモードの有効化

```bash
# 詳細ログを有効化
export DEBUG=1
export LOG_LEVEL=DEBUG

# Seleniumのログを有効化
export SELENIUM_LOG_LEVEL=DEBUG
```

### ネットワークトラフィックの確認

```python
# プロキシ経由でトラフィックを確認
from selenium.webdriver.common.proxy import Proxy, ProxyType

proxy = Proxy()
proxy.proxy_type = ProxyType.MANUAL
proxy.http_proxy = "localhost:8888"
```

### ブラウザコンソールログの取得

```python
# JavaScriptエラーを確認
logs = driver.get_log('browser')
for log in logs:
    print(f"{log['level']}: {log['message']}")
```

### スクリーンショットの保存

```python
# エラー時にスクリーンショットを保存
driver.save_screenshot('error_screenshot.png')
```

### プロファイリング

```python
import cProfile
import pstats

# パフォーマンスプロファイリング
profiler = cProfile.Profile()
profiler.enable()
# 処理実行
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

---

## 🆘 それでも解決しない場合

1. **ログファイルの確認**
   ```bash
   tail -f logs/scraper.log
   ```

2. **環境情報の収集**
   ```bash
   python -m pip list
   python --version
   google-chrome --version
   uname -a  # OS情報
   ```

3. **Issue作成時に含める情報**
   - エラーメッセージ全文
   - 実行したコマンド
   - 環境情報
   - ログファイル（個人情報は除去）
   - 再現手順

4. **コミュニティサポート**
   - [GitHub Issues](https://github.com/39bit-onsen/instagram-scraper/issues)
   - [Discussions](https://github.com/39bit-onsen/instagram-scraper/discussions)

---

## 📚 関連ドキュメント

- [セットアップガイド](SETUP_GUIDE.md)
- [FAQ](FAQ.md)
- [開発者向けガイド](DEVELOPER.md)

---

最終更新日: 2025年1月