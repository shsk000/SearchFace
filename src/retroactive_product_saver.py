#!/usr/bin/env python3
"""
既存の顔写真から商品画像を追加保存するスクリプト

--allと--save-productsを指定するはずが、--allだけを実行した場合の補完用スクリプト。
既存の顔写真ファイル（search-dmm-{content_id}-{hash}.jpg）からproduct IDを抽出し、
対応する商品画像をDMM APIから取得して保存します。

使用方法:
    # 特定の女優の商品画像を保存
    python src/retroactive_product_saver.py --actress-name "上原亜衣"

    # 全女優の商品画像を保存
    python src/retroactive_product_saver.py --all

    # ドライラン
    python src/retroactive_product_saver.py --all --dry-run

環境変数:
    DMM_API_ID: DMM API ID
    DMM_AFFILIATE_ID: DMM アフィリエイトID
"""

import os
import sys
import argparse
import time
import re
from pathlib import Path
from typing import List, Optional, Set

# 環境変数読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenvがインストールされていません。pipでインストールしてください。")
    sys.exit(1)

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.dmm.dmm_api_client import DmmApiClient
from src.dmm.image_downloader import DmmImageDownloader
from src.dmm.models import CollectionConfig
from src.database.person_database import PersonDatabase
from src.utils import log_utils

# ログ設定
logger = log_utils.get_logger(__name__)


class RetroactiveProductSaver:
    """既存顔写真に対応する商品画像保存クラス"""

    def __init__(self, dry_run: bool = False, config: Optional[CollectionConfig] = None):
        """初期化

        Args:
            dry_run (bool): ドライラン実行フラグ
            config (Optional[CollectionConfig]): 収集設定
        """
        self.dry_run = dry_run
        self.config = config or CollectionConfig()
        self.db = PersonDatabase()

        # APIクライアントと画像ダウンローダー
        if not dry_run:
            try:
                self.api_client = DmmApiClient()
                self.downloader = DmmImageDownloader()
            except ValueError as e:
                logger.error(f"API初期化エラー: {str(e)}")
                raise
        else:
            self.api_client = None
            self.downloader = None

        # DMM女優IDと商品キャッシュ（API呼び出し削減用）
        self.actress_dmm_ids = {}
        self.product_cache = {}

        # 統計情報
        self.stats = {
            'actresses_processed': 0,
            'face_files_found': 0,
            'product_ids_extracted': 0,
            'products_saved': 0,
            'products_skipped': 0,
            'api_errors': 0,
            'save_errors': 0
        }

        logger.info(f"商品画像追加保存クラス初期化完了 - DryRun: {dry_run}")

    def process_actress(self, actress_name: str) -> bool:
        """女優の商品画像を保存

        Args:
            actress_name (str): 女優名

        Returns:
            bool: 成功した場合True
        """
        try:
            logger.info(f"🎯 処理開始: {actress_name}")
            self.stats['actresses_processed'] += 1

            # 1. 既存顔写真ファイル検索
            face_files = self._find_existing_face_files(actress_name)
            if not face_files:
                logger.info(f"📭 顔写真ファイルが見つかりません: {actress_name}")
                return True

            self.stats['face_files_found'] += len(face_files)
            logger.info(f"📸 顔写真ファイル発見: {len(face_files)}件")

            # 2. Product IDを抽出
            product_ids = self._extract_product_ids(face_files)
            if not product_ids:
                logger.info(f"📭 Product IDが抽出できません: {actress_name}")
                return True

            self.stats['product_ids_extracted'] += len(product_ids)
            logger.info(f"🔍 Product ID抽出: {len(product_ids)}件")

            # 3. 既存商品画像確認
            existing_products = self._get_existing_product_files(actress_name)
            new_product_ids = product_ids - existing_products

            if not new_product_ids:
                logger.info(f"✅ 全ての商品画像は既に保存済み: {actress_name}")
                self.stats['products_skipped'] += len(product_ids)
                return True

            logger.info(f"💾 新規保存対象: {len(new_product_ids)}件 (既存: {len(existing_products)}件)")

            if self.dry_run:
                logger.info(f"📋 [DRY-RUN] 商品画像保存対象: {new_product_ids}")
                return True

            # 4. 商品画像をダウンロード・保存
            saved_count = 0
            for product_id in new_product_ids:
                if self._save_product_image(actress_name, product_id):
                    saved_count += 1
                    self.stats['products_saved'] += 1
                else:
                    self.stats['save_errors'] += 1

                # レート制限
                time.sleep(0.1)

            logger.info(f"✅ 処理完了: {actress_name} - {saved_count}/{len(new_product_ids)}件保存")
            return True

        except Exception as e:
            logger.error(f"女優処理エラー ({actress_name}): {str(e)}")
            return False

    def process_all_actresses(self) -> dict:
        """全女優の商品画像を保存

        Returns:
            dict: 実行結果統計
        """
        try:
            # 商品画像が保存可能な女優を取得
            actresses = self._get_target_actresses()

            if not actresses:
                logger.info("📭 処理対象の女優が見つかりません")
                return self.stats

            logger.info(f"📋 処理対象: {len(actresses)}名")

            if self.dry_run:
                logger.info("📋 [DRY-RUN] 実際の処理はスキップします")
                for actress in actresses[:5]:  # 最初の5名だけ表示
                    logger.info(f"  - {actress}")
                if len(actresses) > 5:
                    logger.info(f"  ... 他 {len(actresses) - 5}名")
                return self.stats

            # 順次処理
            start_time = time.time()

            for i, actress_name in enumerate(actresses, 1):
                logger.info(f"\n[{i}/{len(actresses)}] 🎯 {actress_name}")

                try:
                    self.process_actress(actress_name)

                    # 進捗表示
                    if i % 10 == 0:
                        self._display_progress()

                except Exception as e:
                    logger.error(f"女優処理エラー ({actress_name}): {str(e)}")
                    continue

            # 最終統計
            processing_time = time.time() - start_time

            logger.info("\n" + "="*60)
            logger.info("📊 最終結果")
            logger.info("="*60)
            self._display_final_stats(processing_time)

            return self.stats

        except Exception as e:
            logger.error(f"全女優処理エラー: {str(e)}")
            return self.stats

    def _find_existing_face_files(self, actress_name: str) -> List[Path]:
        """既存の顔写真ファイルを検索

        Args:
            actress_name (str): 女優名

        Returns:
            List[Path]: 顔写真ファイルリスト
        """
        try:
            save_dir = Path(self.config.get_save_directory(actress_name))

            if not save_dir.exists():
                return []

            # search-dmm-*.jpg ファイルを検索
            face_files = list(save_dir.glob("search-dmm-*.jpg"))
            return sorted(face_files)

        except Exception as e:
            logger.error(f"顔写真ファイル検索エラー ({actress_name}): {str(e)}")
            return []

    def _extract_product_ids(self, face_files: List[Path]) -> Set[str]:
        """顔写真ファイル名からProduct IDを抽出

        Args:
            face_files (List[Path]): 顔写真ファイルリスト

        Returns:
            Set[str]: Product IDセット
        """
        product_ids = set()

        # ファイル名パターン: search-dmm-{content_id}-{hash}.jpg
        pattern = re.compile(r'^search-dmm-([^-]+)-[^-]+\.jpg$')

        for file_path in face_files:
            match = pattern.match(file_path.name)
            if match:
                product_id = match.group(1)
                product_ids.add(product_id)
                logger.debug(f"Product ID抽出: {product_id} (ファイル: {file_path.name})")
            else:
                logger.warning(f"Product ID抽出失敗: {file_path.name}")

        return product_ids

    def _get_existing_product_files(self, actress_name: str) -> Set[str]:
        """既存の商品画像ファイルからProduct IDを取得

        Args:
            actress_name (str): 女優名

        Returns:
            Set[str]: 既存Product IDセット
        """
        try:
            product_dir = Path(self.config.get_product_images_directory(actress_name))

            if not product_dir.exists():
                return set()

            product_ids = set()

            # product-{product_id}.jpg ファイルを検索
            pattern = re.compile(r'^product-([^.]+)\.jpg$')

            for file_path in product_dir.glob("product-*.jpg"):
                match = pattern.match(file_path.name)
                if match:
                    product_id = match.group(1)
                    product_ids.add(product_id)

            return product_ids

        except Exception as e:
            logger.error(f"既存商品画像確認エラー ({actress_name}): {str(e)}")
            return set()

    def _save_product_image(self, actress_name: str, product_id: str) -> bool:
        """商品画像を保存

        Args:
            actress_name (str): 女優名
            product_id (str): Product ID

        Returns:
            bool: 保存成功の場合True
        """
        try:
            # 1. DMM女優IDを取得
            dmm_actress_id = self._get_dmm_actress_id(actress_name)
            if not dmm_actress_id:
                logger.warning(f"DMM女優IDが見つかりません: {actress_name}")
                self.stats['api_errors'] += 1
                return False

            # 2. キャッシュから商品情報を取得または API で取得
            product_image_url = None

            if product_id in self.product_cache:
                product_image_url = self.product_cache[product_id]
                logger.debug(f"キャッシュから商品画像URL取得: {product_id}")
            else:
                # DMM APIで女優の商品を検索
                api_response = self.api_client.search_actress_products(dmm_actress_id, limit=100)
                if api_response and api_response.has_products:
                    # 該当するproduct_idの商品を検索
                    for product in api_response.products:
                        if product.content_id == product_id:
                            product_image_url = product.primary_image_url
                            # キャッシュに保存
                            self.product_cache[product_id] = product_image_url
                            logger.debug(f"API から商品画像URL取得: {product_id}")
                            break

                    # 見つからない商品もキャッシュ（None で保存）
                    if product_image_url is None:
                        self.product_cache[product_id] = None

            if not product_image_url:
                logger.warning(f"商品画像URLが取得できません: {product_id}")
                self.stats['api_errors'] += 1
                return False

            # 3. 画像をダウンロード
            image_data = self.downloader.download_image(product_image_url)
            if not image_data:
                logger.warning(f"画像ダウンロード失敗: {product_id} (URL: {product_image_url})")
                self.stats['api_errors'] += 1
                return False

            # 4. 保存ディレクトリ作成
            product_dir = Path(self.config.get_product_images_directory(actress_name))
            product_dir.mkdir(parents=True, exist_ok=True)

            # 5. ファイル名とパス
            filename = f"product-{product_id}.jpg"
            file_path = product_dir / filename

            # 6. 重複チェック
            if file_path.exists():
                logger.debug(f"商品画像は既に存在: {file_path}")
                self.stats['products_skipped'] += 1
                return True

            # 7. 画像保存
            with open(file_path, 'wb') as f:
                f.write(image_data)

            logger.info(f"💾 商品画像保存成功: {filename}")
            return True

        except Exception as e:
            logger.error(f"商品画像保存エラー ({product_id}): {str(e)}")
            return False

    def _get_target_actresses(self) -> List[str]:
        """処理対象の女優名リストを取得

        Returns:
            List[str]: 女優名リスト
        """
        try:
            # 顔写真ファイルが存在する女優を検索
            base_dir = Path("data/images/dmm")

            if not base_dir.exists():
                return []

            actresses = []

            for actress_dir in base_dir.iterdir():
                if actress_dir.is_dir():
                    # search-dmm-*.jpg ファイルが存在するかチェック
                    face_files = list(actress_dir.glob("search-dmm-*.jpg"))
                    if face_files:
                        actresses.append(actress_dir.name)

            return sorted(actresses)

        except Exception as e:
            logger.error(f"対象女優取得エラー: {str(e)}")
            return []

    def _display_progress(self):
        """進捗表示"""
        logger.info(f"📊 進捗: 女優{self.stats['actresses_processed']}名処理 | "
                   f"商品画像{self.stats['products_saved']}件保存")

    def _display_final_stats(self, processing_time: float):
        """最終統計表示"""
        logger.info(f"処理女優数: {self.stats['actresses_processed']}名")
        logger.info(f"📸 顔写真ファイル: {self.stats['face_files_found']}件")
        logger.info(f"🔍 Product ID抽出: {self.stats['product_ids_extracted']}件")
        logger.info(f"💾 商品画像保存: {self.stats['products_saved']}件")
        logger.info(f"⏭️ スキップ: {self.stats['products_skipped']}件")
        logger.info(f"❌ API エラー: {self.stats['api_errors']}件")
        logger.info(f"❌ 保存エラー: {self.stats['save_errors']}件")
        logger.info(f"⏱️ 総処理時間: {processing_time:.1f}秒")

        if self.stats['actresses_processed'] > 0:
            avg_time = processing_time / self.stats['actresses_processed']
            logger.info(f"⏱️ 平均処理時間: {avg_time:.1f}秒/女優")

    def _get_dmm_actress_id(self, actress_name: str) -> Optional[int]:
        """女優名からDMM女優IDを取得

        Args:
            actress_name (str): 女優名

        Returns:
            Optional[int]: DMM女優ID、見つからない場合None
        """
        try:
            # キャッシュから取得
            if actress_name in self.actress_dmm_ids:
                return self.actress_dmm_ids[actress_name]

            # データベースから女優情報を取得
            person_info = self.db.get_person_by_name(actress_name)
            if person_info and person_info.get('dmm_actress_id'):
                dmm_id = person_info['dmm_actress_id']
                # キャッシュに保存
                self.actress_dmm_ids[actress_name] = dmm_id
                return dmm_id

            logger.warning(f"DMM女優IDが見つかりません: {actress_name}")
            # キャッシュにNoneを保存（再検索を避ける）
            self.actress_dmm_ids[actress_name] = None
            return None

        except Exception as e:
            logger.error(f"DMM女優ID取得エラー ({actress_name}): {str(e)}")
            return None

    def close(self):
        """リソースを閉じる"""
        self.db.close()


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="既存顔写真に対応する商品画像保存スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # 実行モード
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--actress-name', type=str, help='女優名を指定して実行')
    group.add_argument('--all', action='store_true', help='全女優を対象に実行')

    # オプション
    parser.add_argument('--dry-run', action='store_true', help='ドライラン実行（実際の処理はしない）')
    parser.add_argument('--verbose', action='store_true', help='詳細ログ出力')

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        log_utils.set_log_level("DEBUG")

    # 収集設定（商品画像保存用）
    config = CollectionConfig(
        save_product_images=True,
        product_images_subdir="products"
    )

    # 実行クラス初期化
    try:
        saver = RetroactiveProductSaver(dry_run=args.dry_run, config=config)
    except ValueError as e:
        if not args.dry_run:
            logger.error(f"初期化エラー: {str(e)}")
            logger.error("環境変数 DMM_API_ID, DMM_AFFILIATE_ID を設定してください")
            return 1
        else:
            # ドライランの場合はAPI設定なしでも継続
            logger.warning("ドライランモード: API設定なしで実行")
            config_dry = CollectionConfig()
            saver = RetroactiveProductSaver(dry_run=True, config=config_dry)

    try:
        logger.info("🚀 商品画像追加保存スクリプト")
        logger.info("="*50)

        # 環境変数チェック（実際の処理が必要な場合のみ）
        if not args.dry_run:
            api_id = os.getenv('DMM_API_ID')
            affiliate_id = os.getenv('DMM_AFFILIATE_ID')

            if not api_id or not affiliate_id:
                logger.error("❌ 環境変数が設定されていません:")
                logger.error("   DMM_API_ID, DMM_AFFILIATE_ID を設定してください")
                return 1

        # 実行
        if args.actress_name:
            success = saver.process_actress(args.actress_name)
            return 0 if success else 1
        elif args.all:
            saver.process_all_actresses()

        return 0

    except KeyboardInterrupt:
        logger.info("\n⚠️ ユーザーによって中断されました")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}")
        return 1
    finally:
        saver.close()


if __name__ == "__main__":
    sys.exit(main())