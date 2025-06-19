#!/usr/bin/env python3
"""
既存女優のプロフィール情報をDMM APIから取得してperson_profilesテーブルに追加するスクリプト
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path
from typing import Dict, Optional, List
import re

# 環境変数読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenvがインストールされていません。pipでインストールしてください。")
    sys.exit(1)

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.database.person_database import PersonDatabase
from src.utils import log_utils

# ログ設定
logger = log_utils.get_logger(__name__)


class ExistingProfileUpdater:
    """既存女優のプロフィール更新クラス"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.api_id = os.getenv('DMM_API_ID')
        self.affiliate_id = os.getenv('DMM_AFFILIATE_ID')
        self.base_url = 'https://api.dmm.com/affiliate/v3/ActressSearch'

        # データベース接続
        self.db = PersonDatabase()

        # 統計情報
        self.stats = {
            'total_processed': 0,
            'profiles_created': 0,
            'profiles_updated': 0,
            'errors': 0,
            'api_not_found': 0
        }

        # 環境変数チェック
        if not self.api_id or not self.affiliate_id:
            raise ValueError("DMM_API_ID と DMM_AFFILIATE_ID の環境変数が必要です")

        logger.info(f"初期化完了 - DryRun: {self.dry_run}")

    def get_existing_actresses(self) -> List[Dict]:
        """既存の女優データを取得"""
        self.db.cursor.execute("""
            SELECT person_id, name, dmm_actress_id 
            FROM persons 
            WHERE dmm_actress_id IS NOT NULL
            ORDER BY person_id
        """)
        
        actresses = []
        for row in self.db.cursor.fetchall():
            actresses.append({
                'person_id': row['person_id'],
                'name': row['name'],
                'dmm_actress_id': row['dmm_actress_id']
            })
        
        return actresses

    def fetch_actress_profile_from_api(self, dmm_actress_id: int) -> Optional[Dict]:
        """DMM APIから特定の女優のプロフィール情報を取得"""
        params = {
            'api_id': self.api_id,
            'affiliate_id': self.affiliate_id,
            'actress_id': dmm_actress_id,
            'output': 'json'
        }

        try:
            logger.debug(f"API リクエスト: actress_id={dmm_actress_id}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # ステータスコードチェック
            if data.get('result', {}).get('status') != '200':
                logger.warning(f"API エラー - actress_id: {dmm_actress_id}, status: {data.get('result', {}).get('status')}")
                return None

            actresses = data.get('result', {}).get('actress', [])
            if actresses:
                return actresses[0]  # 最初の結果を返す
            else:
                logger.warning(f"女優が見つかりません - actress_id: {dmm_actress_id}")
                return None

        except requests.RequestException as e:
            logger.error(f"API リクエストエラー (actress_id: {dmm_actress_id}): {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON パースエラー (actress_id: {dmm_actress_id}): {e}")
            return None

    def _parse_dmm_profile_data(self, actress: Dict) -> Dict:
        """DMM APIレスポンスからプロフィールデータを抽出・構造化"""
        # 個別カラム用のデータ構造
        profile_data = {
            # 基本情報
            'ruby': self._safe_strip(actress.get('ruby')),
            'birthday': self._safe_strip(actress.get('birthday')),
            'blood_type': self._safe_strip(actress.get('blood_type')),
            'hobby': self._safe_strip(actress.get('hobby')),
            'prefectures': self._safe_strip(actress.get('prefectures')),
            
            # 身体情報
            'height': self._parse_numeric_value(actress.get('height')),
            'bust': self._parse_numeric_value(actress.get('bust')),
            'waist': self._parse_numeric_value(actress.get('waist')),
            'hip': self._parse_numeric_value(actress.get('hip')),
            'cup': self._safe_strip(actress.get('cup')),
            
            # 画像URL
            'image_small_url': self._safe_strip(actress.get('imageURL', {}).get('small')),
            'image_large_url': self._safe_strip(actress.get('imageURL', {}).get('large')),
            
            # DMM情報（カテゴリ別）
            'dmm_list_url_digital': self._safe_strip(actress.get('listURL', {}).get('digital')),
            'dmm_list_url_monthly_premium': self._safe_strip(actress.get('listURL', {}).get('monthly_premium')),
            'dmm_list_url_mono': self._safe_strip(actress.get('listURL', {}).get('mono')),
            
            # 追加メタデータ（参考のため残す）
            'metadata': json.dumps({
                'dmm_source': {
                    'actress_id': actress.get('id'),
                    'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        }
        
        return profile_data

    def _safe_strip(self, value) -> Optional[str]:
        """安全にstrip処理を行う（None値対応）
        
        Args:
            value: 処理対象の値
            
        Returns:
            Optional[str]: strip処理後の文字列、空文字またはNoneの場合はNone
        """
        if value is None:
            return None
        
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        
        # 文字列以外の場合は文字列に変換してからstrip
        try:
            stripped = str(value).strip()
            return stripped if stripped else None
        except (ValueError, TypeError):
            return None

    def _parse_numeric_value(self, value) -> Optional[int]:
        """数値文字列を整数に変換（エラーハンドリング付き）"""
        if not value:
            return None
            
        try:
            # 文字列から数字のみを抽出
            if isinstance(value, str):
                numeric_str = re.sub(r'[^\d]', '', value)
                if numeric_str:
                    return int(numeric_str)
            elif isinstance(value, (int, float)):
                return int(value)
        except (ValueError, TypeError):
            pass
            
        return None

    def update_actress_profile(self, person_id: int, dmm_actress_id: int, name: str) -> bool:
        """特定の女優のプロフィール情報を更新"""
        try:
            # DMM APIからプロフィール情報を取得
            actress_data = self.fetch_actress_profile_from_api(dmm_actress_id)
            
            if not actress_data:
                self.stats['api_not_found'] += 1
                return False

            # プロフィールデータを解析
            profile_data = self._parse_dmm_profile_data(actress_data)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] プロフィール更新: {name} (person_id: {person_id})")
                return True

            # 既存プロフィールを確認
            existing_profile = self.db.get_person_profile(person_id)
            had_existing_profile = existing_profile is not None
            
            # プロフィールデータを保存（upsert操作）
            profile_id = self.db.upsert_person_profile(person_id, profile_data)
            
            # 統計を更新
            if had_existing_profile:
                self.stats['profiles_updated'] += 1
            else:
                self.stats['profiles_created'] += 1
            
            logger.info(f"プロフィール更新完了: {name} (person_id: {person_id}, profile_id: {profile_id})")
            return True
            
        except Exception as e:
            logger.error(f"プロフィール更新エラー: {name} (person_id: {person_id}) - {e}")
            self.stats['errors'] += 1
            return False

    def run(self):
        """メイン処理を実行"""
        logger.info("既存女優プロフィール更新開始")

        # 既存女優データを取得
        actresses = self.get_existing_actresses()
        total_count = len(actresses)
        
        logger.info(f"更新対象女優数: {total_count}")

        try:
            for i, actress in enumerate(actresses, 1):
                person_id = actress['person_id']
                dmm_actress_id = actress['dmm_actress_id']
                name = actress['name']
                
                logger.info(f"処理中 ({i}/{total_count}): {name} (DMM ID: {dmm_actress_id})")
                
                # プロフィール更新
                self.update_actress_profile(person_id, dmm_actress_id, name)
                self.stats['total_processed'] += 1
                
                # 進捗表示（10件ごと）
                if i % 10 == 0:
                    logger.info(f"進捗: {i}/{total_count} "
                               f"(作成: {self.stats['profiles_created']}, "
                               f"更新: {self.stats['profiles_updated']}, "
                               f"エラー: {self.stats['errors']}, "
                               f"API未発見: {self.stats['api_not_found']})")
                
                # API制限を考慮した待機
                if not self.dry_run:
                    time.sleep(0.5)  # 500ms待機

        finally:
            # データベース接続を閉じる
            self.db.close()

        # 最終統計表示
        logger.info("=" * 50)
        logger.info("プロフィール更新完了")
        logger.info(f"総処理件数: {self.stats['total_processed']}")
        logger.info(f"プロフィール作成: {self.stats['profiles_created']}")
        logger.info(f"プロフィール更新: {self.stats['profiles_updated']}")
        logger.info(f"エラー: {self.stats['errors']}")
        logger.info(f"API未発見: {self.stats['api_not_found']}")
        logger.info("=" * 50)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='既存女優プロフィール更新スクリプト')
    parser.add_argument('--dry-run', action='store_true',
                       help='実際の保存を行わずにテスト実行')

    args = parser.parse_args()

    try:
        updater = ExistingProfileUpdater(dry_run=args.dry_run)
        updater.run()
    except KeyboardInterrupt:
        logger.info("ユーザーにより処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()