#!/usr/bin/env python3
"""
Instagram ハッシュタグスクレイパー スケジューラ
定期実行機能を提供
"""

import os
import sys
import time
import signal
import argparse
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# パッケージのインポートパスを設定
sys.path.append(os.path.dirname(__file__))

try:
    import schedule
    from run_batch import BatchProcessor
    from scraper.utils import setup_logger, create_directory_if_not_exists
    from scraper.data_manager import create_sample_tags_csv
except ImportError as e:
    print(f"❌ モジュールのインポートに失敗しました: {e}")
    print("以下のコマンドで依存関係をインストールしてください:")
    print("pip install schedule")
    sys.exit(1)


class InstagramScheduler:
    """Instagram スクレイパー スケジューラ"""
    
    def __init__(self, config_file: str = "config/scheduler.json"):
        """
        初期化
        
        Args:
            config_file: 設定ファイルパス
        """
        self.config_file = config_file
        self.logger = setup_logger("scheduler")
        self.is_running = False
        self.jobs = []
        self.current_job = None
        
        # 設定を読み込み
        self.config = self._load_config()
        
        # シグナルハンドラ設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        import json
        
        default_config = {
            "jobs": [
                {
                    "name": "daily_scraping",
                    "description": "毎日の定期スクレイピング",
                    "schedule": "daily",
                    "time": "08:00",
                    "tags_file": "config/tags.csv",
                    "enabled": True,
                    "headless": True,
                    "delay": 3.0
                },
                {
                    "name": "weekly_full_scraping", 
                    "description": "週次の完全スクレイピング",
                    "schedule": "weekly",
                    "day": "sunday",
                    "time": "02:00",
                    "tags_file": "config/weekly_tags.csv",
                    "enabled": False,
                    "headless": True,
                    "delay": 5.0
                }
            ],
            "settings": {
                "max_concurrent_jobs": 1,
                "log_retention_days": 30,
                "error_notification": True,
                "success_notification": False
            }
        }
        
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"設定ファイルを読み込みました: {config_path}")
                return config
            else:
                # デフォルト設定で新規作成
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                self.logger.info(f"デフォルト設定ファイルを作成しました: {config_path}")
                return default_config
                
        except Exception as e:
            self.logger.error(f"設定ファイル読み込みエラー: {e}")
            return default_config
    
    def _save_config(self):
        """設定ファイルを保存"""
        import json
        
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"設定ファイルを保存しました: {config_path}")
            
        except Exception as e:
            self.logger.error(f"設定ファイル保存エラー: {e}")
    
    def setup_jobs(self):
        """ジョブのセットアップ"""
        self.logger.info("スケジュールジョブをセットアップしています...")
        
        # 既存のジョブをクリア
        schedule.clear()
        self.jobs.clear()
        
        # 設定からジョブを作成
        for job_config in self.config.get("jobs", []):
            if not job_config.get("enabled", False):
                self.logger.info(f"ジョブ '{job_config['name']}' は無効化されています")
                continue
                
            try:
                self._create_job(job_config)
                self.jobs.append(job_config)
                self.logger.info(f"✅ ジョブ '{job_config['name']}' を登録しました")
                
            except Exception as e:
                self.logger.error(f"❌ ジョブ '{job_config['name']}' の登録に失敗: {e}")
        
        self.logger.info(f"合計 {len(self.jobs)} 個のジョブを登録しました")
    
    def _create_job(self, job_config: Dict[str, Any]):
        """個別ジョブの作成"""
        job_name = job_config["name"]
        schedule_type = job_config["schedule"]
        job_time = job_config["time"]
        
        # ジョブ実行関数を作成
        def job_function():
            self._execute_job(job_config)
        
        # スケジュールタイプに応じてジョブを設定
        if schedule_type == "daily":
            schedule.every().day.at(job_time).do(job_function).tag(job_name)
            
        elif schedule_type == "weekly":
            day = job_config.get("day", "monday").lower()
            if day == "monday":
                schedule.every().monday.at(job_time).do(job_function).tag(job_name)
            elif day == "tuesday":
                schedule.every().tuesday.at(job_time).do(job_function).tag(job_name)
            elif day == "wednesday":
                schedule.every().wednesday.at(job_time).do(job_function).tag(job_name)
            elif day == "thursday":
                schedule.every().thursday.at(job_time).do(job_function).tag(job_name)
            elif day == "friday":
                schedule.every().friday.at(job_time).do(job_function).tag(job_name)
            elif day == "saturday":
                schedule.every().saturday.at(job_time).do(job_function).tag(job_name)
            elif day == "sunday":
                schedule.every().sunday.at(job_time).do(job_function).tag(job_name)
                
        elif schedule_type == "hourly":
            schedule.every().hour.do(job_function).tag(job_name)
            
        elif schedule_type == "interval":
            interval = job_config.get("interval_minutes", 60)
            schedule.every(interval).minutes.do(job_function).tag(job_name)
            
        else:
            raise ValueError(f"サポートされていないスケジュールタイプ: {schedule_type}")
    
    def _execute_job(self, job_config: Dict[str, Any]):
        """ジョブを実行"""
        job_name = job_config["name"]
        self.current_job = job_name
        
        try:
            self.logger.info(f"=== ジョブ実行開始: {job_name} ===")
            start_time = datetime.now()
            
            # タグファイルの存在確認
            tags_file = job_config.get("tags_file", "config/tags.csv")
            if not Path(tags_file).exists():
                self.logger.warning(f"タグファイルが見つかりません。作成します: {tags_file}")
                create_sample_tags_csv(tags_file)
            
            # バッチ処理実行
            processor = BatchProcessor(
                headless=job_config.get("headless", True),
                delay=job_config.get("delay", 2.0)
            )
            
            hashtags = processor.load_hashtags_from_csv(tags_file)
            if not hashtags:
                self.logger.warning(f"ジョブ {job_name}: 処理するハッシュタグがありません")
                return
            
            batch_name = f"{job_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            results = processor.process_hashtags(hashtags, batch_name)
            
            # 実行結果のログ
            end_time = datetime.now()
            duration = end_time - start_time
            
            success_count = processor.stats.get('success_count', 0)
            error_count = processor.stats.get('error_count', 0)
            
            self.logger.info(f"=== ジョブ実行完了: {job_name} ===")
            self.logger.info(f"実行時間: {duration}")
            self.logger.info(f"成功: {success_count}件, 失敗: {error_count}件")
            
            # 通知送信
            if self.config.get("settings", {}).get("success_notification", False):
                self._send_notification(f"ジョブ {job_name} が完了しました", 
                                     f"成功: {success_count}件, 失敗: {error_count}件")
            
        except Exception as e:
            error_msg = f"ジョブ {job_name} でエラーが発生: {e}"
            self.logger.error(f"❌ {error_msg}")
            
            # エラー通知送信
            if self.config.get("settings", {}).get("error_notification", True):
                self._send_notification(f"ジョブエラー: {job_name}", error_msg)
                
        finally:
            self.current_job = None
    
    def _send_notification(self, title: str, message: str):
        """通知送信（将来の拡張用）"""
        # 現在はログ出力のみ
        self.logger.info(f"📢 通知: {title} - {message}")
        # 将来的にはSlack、Discord、メール等の通知機能を追加可能
    
    def run(self):
        """スケジューラを実行"""
        self.logger.info("Instagram スケジューラを開始します...")
        self.is_running = True
        
        # ジョブをセットアップ
        self.setup_jobs()
        
        # 次の実行予定を表示
        self._show_next_runs()
        
        # メインループ
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(30)  # 30秒ごとにチェック
                
        except KeyboardInterrupt:
            self.logger.info("ユーザーによって停止されました")
        finally:
            self.stop()
    
    def _show_next_runs(self):
        """次の実行予定を表示"""
        jobs = schedule.get_jobs()
        if not jobs:
            self.logger.info("登録されているジョブがありません")
            return
        
        self.logger.info("=== 次の実行予定 ===")
        for job in jobs:
            next_run = job.next_run
            if next_run:
                self.logger.info(f"  {job.tags}: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def stop(self):
        """スケジューラを停止"""
        self.logger.info("スケジューラを停止しています...")
        self.is_running = False
        
        # 実行中のジョブがあれば待機
        if self.current_job:
            self.logger.info(f"実行中のジョブ '{self.current_job}' の完了を待機中...")
            # 実際の実装では、ジョブの停止メカニズムを追加
        
        # 設定を保存
        self._save_config()
        
        self.logger.info("スケジューラが停止しました")
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"シグナル {signum} を受信しました")
        self.stop()
    
    def add_job(self, job_config: Dict[str, Any]):
        """ジョブを追加"""
        try:
            # 設定に追加
            self.config["jobs"].append(job_config)
            
            # 有効なジョブであればスケジュールに追加
            if job_config.get("enabled", False):
                self._create_job(job_config)
                self.jobs.append(job_config)
            
            # 設定を保存
            self._save_config()
            
            self.logger.info(f"ジョブ '{job_config['name']}' を追加しました")
            
        except Exception as e:
            self.logger.error(f"ジョブ追加エラー: {e}")
    
    def remove_job(self, job_name: str):
        """ジョブを削除"""
        try:
            # スケジュールから削除
            schedule.clear(job_name)
            
            # 設定から削除
            self.config["jobs"] = [job for job in self.config["jobs"] 
                                 if job.get("name") != job_name]
            
            # ローカルリストから削除
            self.jobs = [job for job in self.jobs if job.get("name") != job_name]
            
            # 設定を保存
            self._save_config()
            
            self.logger.info(f"ジョブ '{job_name}' を削除しました")
            
        except Exception as e:
            self.logger.error(f"ジョブ削除エラー: {e}")
    
    def list_jobs(self):
        """ジョブ一覧を表示"""
        self.logger.info("=== 登録済みジョブ一覧 ===")
        
        if not self.config.get("jobs"):
            self.logger.info("登録されているジョブがありません")
            return
        
        for job in self.config["jobs"]:
            status = "有効" if job.get("enabled", False) else "無効"
            schedule_info = f"{job.get('schedule', 'unknown')}"
            if job.get('time'):
                schedule_info += f" {job['time']}"
            if job.get('day'):
                schedule_info += f" ({job['day']})"
                
            self.logger.info(f"  {job['name']}: {status} - {schedule_info}")
            self.logger.info(f"    説明: {job.get('description', 'なし')}")
            self.logger.info(f"    タグファイル: {job.get('tags_file', 'なし')}")


def create_cron_job(scheduler_script_path: str, cron_schedule: str = "0 8 * * *"):
    """
    cron形式でのジョブ作成支援
    
    Args:
        scheduler_script_path: スケジューラスクリプトのパス
        cron_schedule: cron形式のスケジュール
    """
    print("=== cron ジョブ作成支援 ===")
    print(f"以下のcrontabエントリを追加してください:")
    print()
    print(f"{cron_schedule} cd {Path.cwd()} && python {scheduler_script_path} --run >> /var/log/instagram_scheduler.log 2>&1")
    print()
    print("crontabへの追加方法:")
    print("1. crontab -e")
    print("2. 上記の行を追加")
    print("3. 保存して終了")
    print()
    print("スケジュール例:")
    print("  毎日8時: 0 8 * * *")
    print("  毎週日曜2時: 0 2 * * 0")
    print("  毎時: 0 * * * *")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="Instagram ハッシュタグスクレイパー スケジューラ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python src/scheduler.py --run                      # スケジューラ実行
  python src/scheduler.py --list                     # ジョブ一覧表示
  python src/scheduler.py --add-job daily.json       # ジョブ追加
  python src/scheduler.py --remove-job daily_job     # ジョブ削除
  python src/scheduler.py --cron                     # cron設定支援
        """
    )
    
    parser.add_argument(
        "--run",
        action="store_true",
        help="スケジューラを実行"
    )
    
    parser.add_argument(
        "--list",
        action="store_true", 
        help="ジョブ一覧を表示"
    )
    
    parser.add_argument(
        "--config",
        default="config/scheduler.json",
        help="設定ファイルパス (デフォルト: config/scheduler.json)"
    )
    
    parser.add_argument(
        "--add-job",
        help="ジョブ設定ファイル（JSON）からジョブを追加"
    )
    
    parser.add_argument(
        "--remove-job",
        help="指定されたジョブ名のジョブを削除"
    )
    
    parser.add_argument(
        "--cron",
        action="store_true",
        help="cron設定支援を表示"
    )
    
    args = parser.parse_args()
    
    if args.cron:
        create_cron_job(__file__)
        return
    
    # スケジューラインスタンス作成
    scheduler = InstagramScheduler(args.config)
    
    try:
        if args.run:
            scheduler.run()
            
        elif args.list:
            scheduler.list_jobs()
            
        elif args.add_job:
            import json
            try:
                with open(args.add_job, 'r', encoding='utf-8') as f:
                    job_config = json.load(f)
                scheduler.add_job(job_config)
                print(f"✅ ジョブを追加しました: {job_config.get('name', 'unknown')}")
            except Exception as e:
                print(f"❌ ジョブ追加エラー: {e}")
                
        elif args.remove_job:
            scheduler.remove_job(args.remove_job)
            print(f"✅ ジョブを削除しました: {args.remove_job}")
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")


if __name__ == "__main__":
    main()