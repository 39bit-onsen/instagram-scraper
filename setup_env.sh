#!/bin/bash
# Instagram スクレイパー環境セットアップスクリプト

echo "Instagram スクレイパー環境をセットアップします..."

# Pythonバージョン確認
python3 --version

# 仮想環境の作成
echo "仮想環境を作成します..."
python3 -m venv venv

# 仮想環境の有効化
echo "仮想環境を有効化します..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストールします..."
pip install -r requirements.txt

echo "セットアップが完了しました！"
echo "使用方法: source venv/bin/activate"