# データ保存ディレクトリ

このディレクトリにはInstagramスクレイピングで取得したデータが保存されます。

## 構造

```
data/
└── hashtags/
    └── YYYYMM/          # 年月フォルダ
        ├── tag_data.csv # メインデータ
        └── tag_data.json # バックアップ
```

## 注意事項

- 取得したデータは個人情報を含まない公開情報のみです
- データの商用利用は各自でInstagramの利用規約を確認してください
- このディレクトリは自動生成されます