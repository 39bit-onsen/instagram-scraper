#!/usr/bin/env python3
"""
Instagram ログイン機能
手動ログイン、cookie保存・復元機能を提供
"""

import os
import json
import time
import getpass
from pathlib import Path
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class InstagramLogin:
    """Instagram ログイン管理クラス"""
    
    def __init__(self, cookies_dir: str = "cookies"):
        """
        初期化
        
        Args:
            cookies_dir: Cookie保存ディレクトリ
        """
        self.cookies_dir = Path(cookies_dir)
        self.cookies_file = self.cookies_dir / "ig_cookies.json"
        self.driver: Optional[webdriver.Chrome] = None
        
        # Cookie保存ディレクトリ作成
        self.cookies_dir.mkdir(exist_ok=True)
        
    def setup_driver(self, headless: bool = False) -> webdriver.Chrome:
        """
        ChromeDriverをセットアップ
        
        Args:
            headless: ヘッドレスモードで実行するか
            
        Returns:
            WebDriverインスタンス
        """
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
            
        # 基本設定
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User-Agent設定
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # 自動制御検知を無効化
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def manual_login(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        手動ログイン実行
        
        Args:
            username: ユーザー名（未指定時は入力プロンプト）
            password: パスワード（未指定時は入力プロンプト）
            
        Returns:
            ログイン成功かどうか
        """
        print("=== Instagram 手動ログイン ===")
        
        try:
            # ドライバー起動
            print("1. ブラウザを起動しています...")
            self.driver = self.setup_driver(headless=False)
            
            # Instagramにアクセス
            print("2. Instagramにアクセスしています...")
            self.driver.get("https://www.instagram.com/")
            
            # ページ読み込み待機
            wait = WebDriverWait(self.driver, 10)
            
            # ログイン画面の確認
            try:
                username_input = wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                print("3. ログイン画面が表示されました")
                
            except TimeoutException:
                print("❌ ログイン画面が表示されませんでした")
                return False
            
            # ユーザー名・パスワード入力
            if not username:
                username = input("ユーザー名を入力してください: ")
            if not password:
                password = getpass.getpass("パスワードを入力してください: ")
            
            print("4. ログイン情報を入力しています...")
            
            # ユーザー名入力
            username_input.clear()
            username_input.send_keys(username)
            time.sleep(1)
            
            # パスワード入力
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
            
            # ログインボタンクリック
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            print("5. ログインを実行しています...")
            
            # ログイン成功の確認
            success = self._verify_login()
            
            if success:
                print("✅ ログインに成功しました")
                
                # 2段階認証の確認
                if self._handle_two_factor():
                    print("6. 2段階認証を完了しました")
                
                # Cookie保存
                self.save_cookies()
                return True
            else:
                print("❌ ログインに失敗しました")
                return False
                
        except Exception as e:
            print(f"❌ ログイン処理中にエラーが発生しました: {e}")
            return False
            
    def _verify_login(self) -> bool:
        """ログイン成功を確認"""
        try:
            wait = WebDriverWait(self.driver, 15)
            
            # ホーム画面の要素を確認
            # フィード、プロフィール、または通知の要素が表示されるまで待機
            wait.until(
                lambda d: "/accounts/onetap/" in d.current_url or 
                         any(url in d.current_url for url in ["/", "/explore/", "/reels/"])
            )
            
            # URLでログイン状態を確認
            current_url = self.driver.current_url
            if "instagram.com/accounts/login" in current_url:
                return False
                
            return True
            
        except TimeoutException:
            return False
    
    def _handle_two_factor(self) -> bool:
        """2段階認証の処理"""
        try:
            # 2段階認証画面の確認
            wait = WebDriverWait(self.driver, 5)
            
            # 認証コード入力画面
            code_input = wait.until(
                EC.presence_of_element_located((By.NAME, "verificationCode"))
            )
            
            print("📱 2段階認証が必要です")
            auth_code = input("認証コードを入力してください: ")
            
            code_input.clear()
            code_input.send_keys(auth_code)
            
            # 確認ボタンクリック
            confirm_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            confirm_button.click()
            
            # 認証完了の確認
            time.sleep(3)
            return True
            
        except TimeoutException:
            # 2段階認証が不要の場合
            return True
        except Exception as e:
            print(f"⚠️ 2段階認証でエラーが発生: {e}")
            return False
    
    def save_cookies(self) -> bool:
        """現在のセッションのCookieを保存"""
        try:
            if not self.driver:
                print("❌ ドライバーが初期化されていません")
                return False
                
            cookies = self.driver.get_cookies()
            
            # Cookie情報を保存
            cookie_data = {
                "cookies": cookies,
                "saved_at": time.time(),
                "url": self.driver.current_url
            }
            
            with open(self.cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookie_data, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Cookieを保存しました: {self.cookies_file}")
            return True
            
        except Exception as e:
            print(f"❌ Cookie保存に失敗しました: {e}")
            return False
    
    def load_cookies(self, driver: webdriver.Chrome) -> bool:
        """保存されたCookieを読み込み"""
        try:
            if not self.cookies_file.exists():
                print("❌ Cookie ファイルが見つかりません")
                return False
                
            with open(self.cookies_file, "r", encoding="utf-8") as f:
                cookie_data = json.load(f)
                
            # Cookie有効期限チェック（7日間）
            saved_time = cookie_data.get("saved_at", 0)
            if time.time() - saved_time > 7 * 24 * 3600:
                print("⚠️ Cookieの有効期限が切れています")
                return False
                
            # Instagramにアクセス
            driver.get("https://www.instagram.com/")
            time.sleep(2)
            
            # Cookie設定
            for cookie in cookie_data["cookies"]:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Cookie設定エラー: {e}")
                    continue
                    
            # ページ更新
            driver.refresh()
            time.sleep(3)
            
            # ログイン状態確認
            if self._verify_login_by_url(driver):
                print("✅ Cookie認証に成功しました")
                return True
            else:
                print("❌ Cookie認証に失敗しました")
                return False
                
        except Exception as e:
            print(f"❌ Cookie読み込みに失敗しました: {e}")
            return False
    
    def _verify_login_by_url(self, driver: webdriver.Chrome) -> bool:
        """URLでログイン状態を確認"""
        current_url = driver.current_url
        return "instagram.com/accounts/login" not in current_url
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        if self.driver:
            self.driver.quit()
            self.driver = None


def main():
    """メイン関数 - 手動ログイン実行"""
    print("Instagram スクレイパー - 初回ログイン設定")
    print("=" * 50)
    
    login_manager = InstagramLogin()
    
    try:
        # 手動ログイン実行
        success = login_manager.manual_login()
        
        if success:
            print("\n🎉 ログインとCookie保存が完了しました！")
            print("今後は自動的にログイン状態を復元します。")
            
            # 動作確認
            print("\n5秒後にブラウザを閉じます...")
            time.sleep(5)
            
        else:
            print("\n❌ ログインに失敗しました。もう一度お試しください。")
            
    except KeyboardInterrupt:
        print("\n⚠️ ログイン処理が中断されました")
        
    finally:
        login_manager.cleanup()


if __name__ == "__main__":
    main()