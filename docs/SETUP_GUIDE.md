# Instagram ハッシュタグスクレイパー セットアップガイド

このガイドでは、Instagram ハッシュタグスクレイパーの詳細なセットアップ手順を説明します。

## 📋 目次

1. [動作環境要件](#動作環境要件)
2. [事前準備](#事前準備)
3. [インストール手順](#インストール手順)
4. [初期設定](#初期設定)
5. [動作確認](#動作確認)
6. [オプション設定](#オプション設定)

---

## 🖥️ 動作環境要件

### 必須要件

| 項目 | 要件 |
|------|------|
| OS | Windows 10/11, Ubuntu 22.04 LTS, macOS 12以降 |
| Python | 3.10以降 |
| メモリ | 4GB以上（推奨: 8GB以上） |
| ストレージ | 1GB以上の空き容量 |
| ブラウザ | Google Chrome（最新版） |
| インターネット | 安定した接続環境 |

### 推奨環境

- **CPU**: Intel Core i5以上 または AMD Ryzen 5以上
- **ディスプレイ**: 1920x1080以上の解像度（GUI使用時）
- **ネットワーク**: 10Mbps以上の回線速度

---

## 🛠️ 事前準備

### 1. Pythonのインストール確認

```bash
# Pythonバージョン確認
python --version
# または
python3 --version
```

Pythonがインストールされていない場合:
- **Windows**: [Python公式サイト](https://www.python.org/downloads/)からダウンロード
- **Ubuntu**: `sudo apt install python3.10 python3.10-venv python3-pip`
- **macOS**: `brew install python@3.10`

### 2. Google Chromeのインストール

```bash
# バージョン確認
google-chrome --version
```

インストールされていない場合:
- [Google Chrome公式サイト](https://www.google.com/chrome/)からダウンロード

### 3. Gitのインストール（任意）

```bash
# Gitバージョン確認
git --version
```

---

## 📦 インストール手順

### 方法1: Gitを使用したインストール

```bash
# 1. リポジトリのクローン
git clone https://github.com/39bit-onsen/instagram-scraper.git
cd instagram-scraper

# 2. 仮想環境の作成
python -m venv venv

# 3. 仮想環境の有効化
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 4. 依存関係のインストール
pip install -r requirements.txt
```

### 方法2: ZIPファイルからのインストール

1. GitHubからZIPファイルをダウンロード
2. 任意のディレクトリに展開
3. ターミナル/コマンドプロンプトで展開したディレクトリに移動
4. 上記の手順2〜4を実行

### ChromeDriverの設定

#### 自動設定（推奨）

```bash
# webdriver-managerを使用（requirements.txtに含まれています）
# 自動的に適切なバージョンがダウンロードされます
```

#### 手動設定

1. Chromeのバージョンを確認
   ```bash
   google-chrome --version
   ```

2. [ChromeDriver公式サイト](https://chromedriver.chromium.org/)から対応バージョンをダウンロード

3. ChromeDriverを配置
   ```bash
   # Windowsの場合
   # C:\chromedriver\chromedriver.exe に配置し、環境変数PATHに追加
   
   # Linux/macOSの場合
   sudo mv chromedriver /usr/local/bin/
   sudo chmod +x /usr/local/bin/chromedriver
   ```

---

## ⚙️ 初期設定

### 1. 環境変数の設定（オプション）

`.env`ファイルを作成:

```bash
# config/.envを作成
cd config
cp .env.example .env
```

`.env`の内容を編集:
```env
# Instagram認証情報（手動ログイン推奨のため通常は不要）
IG_ID=your_instagram_id
IG_PASS=your_instagram_password

# ChromeDriverパス（自動検出されない場合）
CHROME_DRIVER_PATH=/path/to/chromedriver

# ログレベル
LOG_LEVEL=INFO
```

### 2. ディレクトリ構造の確認

```bash
# 必要なディレクトリが作成されているか確認
ls -la

# 以下のディレクトリが存在することを確認
# - config/
# - cookies/
# - data/
# - src/
```

### 3. 初回ログイン（必須）

```bash
# Instagramへの初回ログイン
python src/scraper/login.py
```

1. ブラウザが自動的に起動します
2. Instagramのログイン画面が表示されます
3. 手動でログイン情報を入力してください
4. 2段階認証が有効な場合は、認証コードを入力
5. ログイン成功後、Enterキーを押してください
6. `cookies/ig_cookies.json`が作成されます

⚠️ **セキュリティ注意事項**:
- cookieファイルには認証情報が含まれます
- 他人と共有しないでください
- 定期的に更新することを推奨します

---

## ✅ 動作確認

### 1. 基本動作テスト

```bash
# 単一タグのテスト取得
python src/scraper/fetch_tag.py
# プロンプトが表示されたら「test」と入力
```

### 2. GUI動作確認

```bash
# GUIアプリケーションの起動
python src/ui/tag_input_gui.py
```

- ウィンドウが表示されることを確認
- 「ヘルプ」ボタンをクリックして説明を確認

### 3. バッチ処理テスト

```bash
# サンプルCSVファイルの作成
python src/run_batch.py --create-sample

# バッチ処理の実行
python src/run_batch.py -f config/tags.csv
```

### 4. テストスイートの実行

```bash
# ユニットテストの実行
pytest tests/unit -v

# 統合テストの実行（ネットワーク不要）
pytest tests/integration -v --no-network
```

---

## 🔧 オプション設定

### スケジューラの設定

1. 設定ファイルの編集
   ```bash
   # config/scheduler.jsonを編集
   ```

2. スケジュール例:
   ```json
   {
     "jobs": [
       {
         "name": "daily_scraping",
         "description": "毎日の定期取得",
         "schedule": "daily",
         "time": "09:00",
         "tags_file": "config/tags.csv",
         "enabled": true,
         "headless": true,
         "delay": 3.0
       }
     ]
   }
   ```

3. スケジューラの起動:
   ```bash
   python src/scheduler.py --run
   ```

### プロキシ設定（企業環境向け）

```python
# src/scraper/utils.pyに追加
PROXY_CONFIG = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}
```

### ログ設定

```bash
# ログレベルの変更
export LOG_LEVEL=DEBUG  # Linux/macOS
set LOG_LEVEL=DEBUG     # Windows

# ログファイル出力
python src/run_batch.py > logs/batch_$(date +%Y%m%d).log 2>&1
```

---

## 🚀 次のステップ

セットアップが完了したら、以下のドキュメントを参照してください:

- [使用方法](../README.md#使用方法)
- [トラブルシューティング](TROUBLESHOOTING.md)
- [FAQ](FAQ.md)
- [開発者向けガイド](DEVELOPER.md)

---

## 📞 サポート

問題が発生した場合:

1. [トラブルシューティングガイド](TROUBLESHOOTING.md)を確認
2. [FAQ](FAQ.md)を確認
3. [GitHubのIssues](https://github.com/39bit-onsen/instagram-scraper/issues)で既知の問題を検索
4. 新しいIssueを作成して報告

---

最終更新日: 2025年1月