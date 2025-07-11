#!/usr/bin/env python3
"""
テスト実行スクリプト
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, description):
    """コマンドを実行して結果を表示"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("⚠️ エラー出力:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} 完了")
        else:
            print(f"❌ {description} 失敗 (終了コード: {result.returncode})")
            return False
            
    except Exception as e:
        print(f"❌ コマンド実行エラー: {e}")
        return False
    
    return True


def check_dependencies():
    """依存関係をチェック"""
    try:
        import pytest
        import selenium
        print("✅ 必要な依存関係がインストールされています")
        return True
    except ImportError as e:
        print(f"❌ 依存関係が不足しています: {e}")
        print("pip install -r requirements.txt を実行してください")
        return False


def main():
    parser = argparse.ArgumentParser(description="テスト実行スクリプト")
    parser.add_argument("--unit", action="store_true", help="ユニットテストのみ実行")
    parser.add_argument("--integration", action="store_true", help="統合テストのみ実行")
    parser.add_argument("--coverage", action="store_true", help="カバレッジレポート生成")
    parser.add_argument("--no-slow", action="store_true", help="時間のかかるテストをスキップ")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    
    args = parser.parse_args()
    
    print("Instagram ハッシュタグスクレイパー テスト実行")
    print("=" * 50)
    
    # 依存関係チェック
    if not check_dependencies():
        sys.exit(1)
    
    # プロジェクトルートディレクトリに移動
    project_root = Path(__file__).parent
    import os
    os.chdir(project_root)
    
    # テストコマンドの構築
    test_commands = []
    
    if args.unit:
        # ユニットテストのみ
        cmd = "pytest tests/unit/"
        if args.verbose:
            cmd += " -v"
        if args.coverage:
            cmd += " --cov=src --cov-report=html --cov-report=term"
        test_commands.append((cmd, "ユニットテスト"))
        
    elif args.integration:
        # 統合テストのみ
        cmd = "pytest tests/integration/"
        if args.verbose:
            cmd += " -v"
        if args.no_slow:
            cmd += " -m 'not slow'"
        test_commands.append((cmd, "統合テスト"))
        
    else:
        # 全テスト実行
        cmd = "pytest"
        if args.verbose:
            cmd += " -v"
        if args.coverage:
            cmd += " --cov=src --cov-report=html --cov-report=term"
        if args.no_slow:
            cmd += " -m 'not slow'"
        test_commands.append((cmd, "全テスト"))
    
    # コードスタイルチェック（オプション）
    style_commands = []
    
    # black のチェック
    if Path("src").exists():
        style_commands.append(("black --check src/", "コードフォーマットチェック (black)"))
    
    # flake8 のチェック
    if Path("src").exists():
        style_commands.append(("flake8 src/ --max-line-length=88 --ignore=E203,W503", "コードスタイルチェック (flake8)"))
    
    # テスト実行
    all_passed = True
    
    for cmd, description in test_commands:
        if not run_command(cmd, description):
            all_passed = False
    
    # スタイルチェック実行（失敗してもテスト結果には影響しない）
    print(f"\n{'='*50}")
    print("📝 コードスタイルチェック")
    print(f"{'='*50}")
    
    for cmd, description in style_commands:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {description} 合格")
            else:
                print(f"⚠️ {description} に問題があります:")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
        except Exception as e:
            print(f"⚠️ {description} の実行に失敗: {e}")
    
    # 結果サマリー
    print(f"\n{'='*50}")
    print("📊 テスト結果サマリー")
    print(f"{'='*50}")
    
    if all_passed:
        print("🎉 すべてのテストが成功しました！")
        
        if args.coverage:
            print("\n📈 カバレッジレポートが生成されました:")
            print("- HTML: htmlcov/index.html")
            print("- ターミナル: 上記参照")
        
        print("\n次のステップ:")
        print("- 新機能の開発")
        print("- ドキュメントの更新")
        print("- プルリクエストの作成")
        
        sys.exit(0)
    else:
        print("❌ 一部のテストが失敗しました")
        print("\n修正が必要な項目:")
        print("- 失敗したテストを確認")
        print("- エラーメッセージを分析")
        print("- コードを修正して再実行")
        
        sys.exit(1)


if __name__ == "__main__":
    main()