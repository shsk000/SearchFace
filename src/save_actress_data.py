#!/usr/bin/env python3
"""
DMM.com 女優APIを使用して女優情報をSQLiteデータベースに保存するスクリプト

使用方法:
    python src/save_actress_data.py [--dry-run]

環境変数:
    DMM_API_ID: DMM API ID
    DMM_AFFILIATE_ID: DMM アフィリエイトID
"""

import os
import sys
import json
import time
import requests
import argparse
from pathlib import Path
from typing import Dict, Optional
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


class DMMActressDataSaver:
    """DMM女優データベース保存クラス"""

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
            'saved': 0,
            'skipped': 0,
            'errors': 0,
            'profiles_created': 0,
            'profiles_updated': 0,
            'profile_errors': 0
        }

        # 環境変数チェック
        if not self.api_id or not self.affiliate_id:
            raise ValueError("DMM_API_ID と DMM_AFFILIATE_ID の環境変数が必要です")

        logger.info(f"初期化完了 - DryRun: {self.dry_run}")

    def _sanitize_filename(self, name: str) -> str:
        """ファイル名として使用できない文字を除去・置換"""
        # 使用できない文字を置換
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        # 制御文字を除去
        sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
        # 末尾のピリオドとスペースを除去
        sanitized = sanitized.rstrip('. ')
        # 空文字列の場合はデフォルト名を使用
        if not sanitized:
            sanitized = 'unknown_actress'
        return sanitized

    def _make_api_request(self, offset: int = 1) -> Optional[Dict]:
        """DMM APIにリクエストを送信"""
        params = {
            'api_id': self.api_id,
            'affiliate_id': self.affiliate_id,
            # 'gte_birthday': '2000-01-01',
            # 'lte_birthday': '2000-12-31',
            'hits': 100,  # テスト用に少なく
            'offset': offset,
            'output': 'json'
        }

        try:
            logger.info(f"API リクエスト送信 - offset: {offset}")
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # ステータスコードチェック
            if data.get('result', {}).get('status') != '200':
                logger.error(f"API エラー - status: {data.get('result', {}).get('status')}")
                return None

            return data

        except requests.RequestException as e:
            logger.error(f"API リクエストエラー: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON パースエラー: {e}")
            return None


    def _write_error_log(self, error_msg: str, url: str, file_path: str) -> None:
        """エラー情報を専用ファイルに出力"""
        error_log_path = Path('actress_save_errors.log')

        try:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {error_msg}\n")
                f.write(f"  URL: {url}\n")
                f.write(f"  ファイルパス: {file_path}\n")
                f.write("---\n")

        except IOError as e:
            logger.error(f"エラーログ書き込み失敗: {e}")

    def _create_person_data(self, actress: Dict) -> Optional[int]:
        """女優データからperson情報を作成"""
        name = actress.get('name', '').strip()
        dmm_actress_id = actress.get('id')

        if not name:
            logger.warning(f"女優名が空です - ID: {dmm_actress_id}")
            return None

        if not dmm_actress_id:
            logger.warning(f"DMM女優IDが空です - name: {name}")
            return None

        # 既存のDMM女優IDをチェック
        if not self.dry_run:
            existing_person = self._get_person_by_dmm_id(dmm_actress_id)
            if existing_person:
                logger.info(f"既存の女優をスキップ: {name} (DMM ID: {dmm_actress_id})")
                self.stats['skipped'] += 1
                return existing_person['person_id']

        # 画像URLチェック
        image_url = actress.get('imageURL', {}).get('large')
        if not image_url:
            error_msg = f"画像URLが見つかりません: {name} (DMM ID: {dmm_actress_id})"
            logger.warning(error_msg)
            self._write_error_log(error_msg, "N/A", "N/A")
            self.stats['errors'] += 1
            return None

        # 画像URLをDBに保存（ローカルダウンロードは不要）
        base_image_path = image_url

        # メタデータは一旦不要
        metadata = None

        if self.dry_run:
            logger.info(f"[DRY RUN] 女優データ保存: {name} (DMM ID: {dmm_actress_id}) URL: {image_url}")
            return 999  # DRY RUNの場合はダミーID

        try:
            # データベースに保存
            person_id = self._save_person_to_db(
                name=name,
                dmm_actress_id=dmm_actress_id,
                base_image_path=base_image_path,
                metadata=metadata
            )

            # プロフィールデータを保存
            self._save_profile_data(person_id, actress)

            logger.info(f"女優データ保存完了: {name} (DMM ID: {dmm_actress_id}, Person ID: {person_id})")
            self.stats['saved'] += 1
            
            return person_id

        except Exception as e:
            error_msg = f"データベース保存エラー: {name} (DMM ID: {dmm_actress_id}) - {e}"
            logger.error(error_msg)
            self._write_error_log(error_msg, image_url, "N/A")
            self.stats['errors'] += 1
            return None

    def _get_person_by_dmm_id(self, dmm_actress_id: int) -> Optional[Dict]:
        """DMM女優IDで人物を検索"""
        try:
            self.db.cursor.execute(
                "SELECT person_id, name, dmm_actress_id FROM persons WHERE dmm_actress_id = ?",
                (dmm_actress_id,)
            )
            row = self.db.cursor.fetchone()

            if row:
                return {
                    'person_id': row['person_id'],
                    'name': row['name'],
                    'dmm_actress_id': row['dmm_actress_id']
                }
            return None

        except Exception as e:
            logger.error(f"DMM ID検索エラー: {e}")
            return None

    def _save_person_to_db(self, name: str, dmm_actress_id: int, base_image_path: str, metadata: Dict) -> int:
        """人物データをデータベースに保存"""
        try:
            # personsテーブルに挿入
            self.db.cursor.execute("""
                INSERT INTO persons (name, dmm_actress_id, base_image_path, metadata)
                VALUES (?, ?, ?, ?)
            """, (name, dmm_actress_id, base_image_path, json.dumps(metadata)))

            person_id = self.db.cursor.lastrowid
            self.db.conn.commit()

            # person_profilesテーブルにも記録を作成
            self.db.create_person_profile(person_id)

            return person_id

        except Exception as e:
            self.db.conn.rollback()
            raise Exception(f"データベース保存に失敗: {str(e)}")

    def _process_actress(self, actress: Dict) -> bool:
        """女優データを処理"""
        person_id = self._create_person_data(actress)
        self.stats['total_processed'] += 1

        return person_id is not None

    def run(self) -> None:
        """メイン処理を実行"""
        logger.info("DMM女優データ保存開始")

        offset = 1
        total_count = None

        try:
            while True:
                # API リクエスト
                data = self._make_api_request(offset)
                if not data:
                    logger.error("API リクエストが失敗しました")
                    break

                result = data.get('result', {})
                result_count = result.get('result_count', 0)

                if total_count is None:
                    total_count = result.get('total_count', 0)
                    logger.info(f"総件数: {total_count}")

                # 結果が0件の場合は終了
                if result_count == 0:
                    logger.info("検索結果が0件になりました。処理を終了します。")
                    break

                actresses = result.get('actress', [])
                logger.info(f"取得件数: {len(actresses)} (offset: {offset})")

                # 各女優を処理
                for actress in actresses:
                    self._process_actress(actress)

                    # レート制限（画像ダウンロードがないため短縮）
                    if not self.dry_run:
                        time.sleep(0.05)  # 50ms待機

                # 進捗表示
                logger.info(f"進捗: {self.stats['total_processed']}/{total_count} "
                           f"(保存: {self.stats['saved']}, "
                           f"スキップ: {self.stats['skipped']}, "
                           f"エラー: {self.stats['errors']}, "
                           f"プロフィール: {self.stats['profiles_created']+self.stats['profiles_updated']})")

                # 次のページへ
                offset += result_count

                # 少し待機してからAPI呼び出し
                time.sleep(1.0)

        finally:
            # データベース接続を閉じる
            self.db.close()

        # 最終統計表示
        logger.info("=" * 50)
        logger.info("処理完了")
        logger.info(f"総処理件数: {self.stats['total_processed']}")
        logger.info(f"保存: {self.stats['saved']}")
        logger.info(f"スキップ: {self.stats['skipped']}")
        logger.info(f"エラー: {self.stats['errors']}")
        logger.info(f"プロフィール作成: {self.stats['profiles_created']}")
        logger.info(f"プロフィール更新: {self.stats['profiles_updated']}")
        logger.info(f"プロフィールエラー: {self.stats['profile_errors']}")

        # エラーログファイルの確認
        error_log_path = Path('actress_save_errors.log')
        if error_log_path.exists() and self.stats['errors'] > 0:
            logger.info(f"詳細なエラー情報は {error_log_path} を確認してください")

        logger.info("=" * 50)

    def _parse_dmm_profile_data(self, actress: Dict) -> Dict:
        """DMM APIレスポンスからプロフィールデータを抽出・構造化
        
        Args:
            actress (Dict): DMM APIからの女優データ
            
        Returns:
            Dict: 構造化されたプロフィールデータ
        """
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
        """数値文字列を整数に変換（エラーハンドリング付き）
        
        Args:
            value: 変換対象の値
            
        Returns:
            Optional[int]: 変換された整数値、変換できない場合はNone
        """
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

    def _clean_empty_values(self, data: Dict) -> Dict:
        """辞書から空の値を再帰的に除去
        
        Args:
            data (Dict): クリーニング対象の辞書
            
        Returns:
            Dict: クリーニング後の辞書
        """
        if not isinstance(data, dict):
            return data
            
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, dict):
                cleaned_nested = self._clean_empty_values(value)
                if cleaned_nested:  # 空でない場合のみ追加
                    cleaned[key] = cleaned_nested
            elif value is not None and value != '':
                cleaned[key] = value
                
        return cleaned

    def _save_profile_data(self, person_id: int, actress: Dict) -> bool:
        """プロフィールデータをperson_profilesテーブルに保存
        
        Args:
            person_id (int): 人物ID
            actress (Dict): DMM APIからの女優データ
            
        Returns:
            bool: 保存成功の場合True
        """
        try:
            # プロフィールデータを解析
            profile_data = self._parse_dmm_profile_data(actress)
            
            if self.dry_run:
                logger.info(f"[DRY RUN] プロフィールデータ保存: person_id={person_id}")
                return True
            
            # 既存プロフィールを確認（統計のため）
            existing_profile = self.db.get_person_profile(person_id)
            had_existing_profile = existing_profile is not None
            
            # プロフィールデータを保存（upsert操作）
            profile_id = self.db.upsert_person_profile(person_id, profile_data)
            
            # 統計を更新
            if had_existing_profile:
                self.stats['profiles_updated'] += 1
            else:
                self.stats['profiles_created'] += 1
            
            logger.info(f"プロフィールデータ保存完了: person_id={person_id}, profile_id={profile_id}")
            return True
            
        except Exception as e:
            error_msg = f"プロフィールデータ保存エラー: person_id={person_id} - {e}"
            logger.error(error_msg)
            self._write_error_log(error_msg, "N/A", "N/A")
            self.stats['profile_errors'] += 1
            return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='DMM女優データ保存スクリプト')
    parser.add_argument('--dry-run', action='store_true',
                       help='実際の保存を行わずにテスト実行')

    args = parser.parse_args()

    try:
        saver = DMMActressDataSaver(dry_run=args.dry_run)
        saver.run()
    except KeyboardInterrupt:
        logger.info("ユーザーにより処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()