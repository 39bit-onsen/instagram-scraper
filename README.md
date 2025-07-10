````markdown
# Instagram Hashtag Scraper

Instagramのハッシュタグページから投稿情報を取得し、CSV/JSON形式で保存するPythonツールです。
Seleniumによるブラウザ操作を利用し、tkinterで簡易GUIを提供しています。

---

## 🚀 機能概要
- Instagramの特定ハッシュタグページからデータを取得
- 投稿数、関連タグ、トップ投稿の画像URLなどを抽出
- 結果をCSV形式で保存（JSONバックアップあり）
- GUIによるタグ入力＆実行（非エンジニアでも操作可）

---

## 📁 ディレクトリ構成
```
project_root/
├─ config/           # .envファイル（認証情報）
├─ cookies/          # Instagramログイン済セッションクッキー
├─ data/             # 出力データ保存（CSV/JSON）
├─ src/
│   ├─ ui/           # GUI（tkinter）
│   ├─ scraper/      # スクレイピング処理
│   └─ run_batch.py  # バッチ処理
├─ requirements.txt
└─ README.md
```

---

## 💻 動作環境
- OS: Windows 10/11 または Ubuntu 22.04
- Python: 3.10 以降
- ブラウザ: Google Chrome（ChromeDriverとバージョン一致）

---

## 🔧 初期セットアップ

### 1. Python環境作成
```powershell
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. ChromeDriverの配置
- ご利用のChromeと同じバージョンの [ChromeDriver](https://chromedriver.chromium.org/) をダウンロード
- 環境変数 `PATH` に追加 または `src/scraper/utils.py` 内で直接パス指定

### 3. 初回ログイン（cookie保存）
```bash
python src/scraper/login.py
```
- Seleniumが起動 → Instagramログイン
- 成功後、`cookies/ig_cookies.json` が生成されます

---

## ▶️ GUI実行方法
```bash
python src/ui/tag_input_gui.py
```
1. タグを入力（例：citywalkhk）
2. 実行ボタンを押す
3. 自動でInstagramアクセス → 結果CSVを `data/hashtags/` に保存

---

## 🔁 バッチ処理の実行（任意）
```bash
python src/run_batch.py
```
`config/tags.csv` に複数タグを記述して一括取得可能

---

## 🛠 エラーハンドリング
- cookie切れ → 再ログインを要求
- DOM構造変化 → セレクタNotFoundとしてログ出力
- 過剰リクエスト → ランダムスリープ＋再試行

---

## 📝 出力サンプル（CSV）
| tag        | post_count | top_image_urls              | related_tags        |
|------------|-------------|-----------------------------|----------------------|
| citywalkhk | 15800       | ["https://...", ...]        | ["citywalk", "hk"]   |

---

## 🔒 セキュリティ
- 認証情報は `.env` に記載し、`.gitignore` で除外
- 取得対象は公開データのみ
- 2段階認証対応（手動コード入力）

---

## 📌 注意事項
- 本ツールはInstagramの利用規約に準拠する範囲でご利用ください
- 過度なアクセスやBot検知に注意し、常識的な頻度での利用を推奨します

---

## 🧑‍💻 開発者
- 最終更新：2025年7月10日

````

