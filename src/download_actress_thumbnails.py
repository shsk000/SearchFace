#!/usr/bin/env python3
"""
DMM.com 女優APIを使用して女優のサムネイル画像をダウンロードするスクリプト

使用方法:
    python src/download_actress_thumbnails.py [--dry-run]

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

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('actress_download.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class DMMActressDownloader:
    """DMM女優サムネイルダウンローダー"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.api_id = os.getenv('DMM_API_ID')
        self.affiliate_id = os.getenv('DMM_AFFILIATE_ID')
        self.base_url = 'https://api.dmm.com/affiliate/v3/ActressSearch'
        self.base_dir = Path('data/images/base-tmp')

        # 統計情報
        self.stats = {
            'total_processed': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0
        }

        # 環境変数チェック
        if not self.api_id or not self.affiliate_id:
            raise ValueError("DMM_API_ID と DMM_AFFILIATE_ID の環境変数が必要です")

        # ディレクトリ作成
        self.base_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"初期化完了 - DryRun: {self.dry_run}")
        logger.info(f"保存先ディレクトリ: {self.base_dir.absolute()}")

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
            'gte_birthday': '1995-01-01',
            # 'lte_birthday': '1999-12-31',
            'hits': 100,
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

    def _download_image(self, url: str, file_path: Path) -> bool:
        """画像をダウンロード"""
        if self.dry_run:
            logger.info(f"[DRY RUN] 画像ダウンロード: {url} -> {file_path}")
            return True

        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"画像ダウンロード完了: {file_path}")
            return True

        except requests.RequestException as e:
            error_msg = f"画像ダウンロードエラー {url}: {e}"
            logger.error(error_msg)
            self._write_error_log(error_msg, url, file_path)
            return False
        except IOError as e:
            error_msg = f"ファイル書き込みエラー {file_path}: {e}"
            logger.error(error_msg)
            self._write_error_log(error_msg, url, file_path)
            return False

    def _write_error_log(self, error_msg: str, url: str, file_path: Path) -> None:
        """エラー情報を専用ファイルに出力"""
        error_log_path = Path('actress_download_errors.log')

        try:
            with open(error_log_path, 'a', encoding='utf-8') as f:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {error_msg}\n")
                f.write(f"  URL: {url}\n")
                f.write(f"  ファイルパス: {file_path}\n")
                f.write("---\n")

        except IOError as e:
            logger.error(f"エラーログ書き込み失敗: {e}")

    def _process_actress(self, actress: Dict) -> bool:
        """女優データを処理"""
        name = actress.get('name', '').strip()
        if not name:
            logger.warning(f"女優名が空です - ID: {actress.get('id', 'unknown')}")
            return False

        # ファイル名をサニタイズ
        sanitized_name = self._sanitize_filename(name)
        actress_dir = self.base_dir / sanitized_name
        image_path = actress_dir / 'base.jpg'

        # 既存ファイルチェック
        if image_path.exists():
            logger.info(f"スキップ（既存ファイル）: {name}")
            self.stats['skipped'] += 1
            return True

        # 画像URLチェック
        image_url = actress.get('imageURL', {}).get('large')
        if not image_url:
            error_msg = f"画像URLが見つかりません: {name}"
            logger.warning(error_msg)
            self._write_error_log(error_msg, "N/A", image_path)
            self.stats['errors'] += 1
            return False

        # ディレクトリ作成
        if not self.dry_run:
            actress_dir.mkdir(parents=True, exist_ok=True)

        # 画像ダウンロード
        if self._download_image(image_url, image_path):
            logger.info(f"処理完了: {name}")
            self.stats['downloaded'] += 1
            return True
        else:
            self.stats['errors'] += 1
            return False

    def run(self) -> None:
        """メイン処理を実行"""
        logger.info("女優サムネイルダウンロード開始")

        offset = 1
        total_count = None

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
                self.stats['total_processed'] += 1

                # レート制限
                if not self.dry_run:
                    time.sleep(0.1)  # 100ms待機

            # 進捗表示
            logger.info(f"進捗: {self.stats['total_processed']}/{total_count} "
                       f"(ダウンロード: {self.stats['downloaded']}, "
                       f"スキップ: {self.stats['skipped']}, "
                       f"エラー: {self.stats['errors']})")

            # 次のページへ
            offset += result_count

            # 少し待機してからAPI呼び出し
            time.sleep(1.0)

        # 最終統計表示
        logger.info("=" * 50)
        logger.info("処理完了")
        logger.info(f"総処理件数: {self.stats['total_processed']}")
        logger.info(f"ダウンロード: {self.stats['downloaded']}")
        logger.info(f"スキップ: {self.stats['skipped']}")
        logger.info(f"エラー: {self.stats['errors']}")

        # エラーログファイルの確認
        error_log_path = Path('actress_download_errors.log')
        if error_log_path.exists() and self.stats['errors'] > 0:
            logger.info(f"詳細なエラー情報は {error_log_path} を確認してください")

        logger.info("=" * 50)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='DMM女優サムネイルダウンローダー')
    parser.add_argument('--dry-run', action='store_true',
                       help='実際のダウンロードを行わずにテスト実行')

    args = parser.parse_args()

    try:
        downloader = DMMActressDownloader(dry_run=args.dry_run)
        downloader.run()
    except KeyboardInterrupt:
        logger.info("ユーザーにより処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()