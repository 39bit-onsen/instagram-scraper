#!/usr/bin/env python3
"""
Instagram接続テストスクリプト
Seleniumでの基本的なアクセスを確認します
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException


def test_instagram_connection():
    """Instagramへの基本接続テスト"""
    
    print("=== Instagram接続テスト開始 ===")
    
    # Chrome オプション設定
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User-Agent設定（Instagram対策）
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    # ヘッドレスモードの設定（テスト用にコメントアウト）
    # chrome_options.add_argument("--headless")
    
    driver = None
    
    try:
        print("1. ChromeDriverを起動しています...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("2. Instagramトップページにアクセスしています...")
        driver.get("https://www.instagram.com/")
        
        print("3. ページの読み込みを待機しています...")
        wait = WebDriverWait(driver, 10)
        
        # Instagramのロゴまたはログインボタンを待機
        try:
            login_element = wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
            )
            print("✅ ログイン画面が正常に表示されました")
            
        except TimeoutException:
            print("⚠️  ログイン要素が見つかりませんが、ページは読み込まれました")
        
        # ページタイトル確認
        title = driver.title
        print(f"4. ページタイトル: {title}")
        
        if "Instagram" in title:
            print("✅ Instagramページへの接続に成功しました")
            return True
        else:
            print("❌ 予期しないページです")
            return False
            
    except WebDriverException as e:
        print(f"❌ WebDriverエラー: {e}")
        print("ChromeDriverのインストールまたはパスを確認してください")
        return False
        
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False
        
    finally:
        if driver:
            print("5. ブラウザを終了しています...")
            time.sleep(2)  # 確認のため少し待機
            driver.quit()


def test_headless_mode():
    """ヘッドレスモードのテスト"""
    
    print("\n=== ヘッドレスモード接続テスト開始 ===")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    driver = None
    
    try:
        print("1. ヘッドレスモードでChromeDriverを起動...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("2. Instagramにアクセス...")
        driver.get("https://www.instagram.com/")
        
        print("3. ページタイトルを確認...")
        title = driver.title
        print(f"   ページタイトル: {title}")
        
        if "Instagram" in title:
            print("✅ ヘッドレスモードでの接続に成功しました")
            return True
        else:
            print("❌ ヘッドレスモードでの接続に失敗しました")
            return False
            
    except Exception as e:
        print(f"❌ ヘッドレスモードエラー: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    print("Instagram スクレイパー接続テストを開始します\n")
    
    # 基本接続テスト
    gui_success = test_instagram_connection()
    
    # ヘッドレスモードテスト
    headless_success = test_headless_mode()
    
    print("\n=== テスト結果 ===")
    print(f"GUIモード: {'成功' if gui_success else '失敗'}")
    print(f"ヘッドレスモード: {'成功' if headless_success else '失敗'}")
    
    if gui_success and headless_success:
        print("\n🎉 すべてのテストが成功しました！Seleniumの設定は正常です")
    else:
        print("\n⚠️  一部のテストが失敗しました。ChromeDriverの設定を確認してください")
        print("   - ChromeDriverがインストールされているか確認")
        print("   - ChromeDriverのバージョンがChromeブラウザと一致するか確認")
        print("   - PATHが正しく設定されているか確認")