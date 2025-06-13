#!/usr/bin/env python3
"""
DMM API 女優顔写真収集スクリプト

DMM APIを使用して女優の商品画像から顔写真を収集し、
ローカルに保存するスクリプトです。

使用方法:
    # 単一女優を指定して実行
    python src/scripts/collect_dmm_faces.py --person-id 123

    # 女優名を指定して実行
    python src/scripts/collect_dmm_faces.py --actress-name "上原亜衣"

    # 全女優を対象に実行
    python src/scripts/collect_dmm_faces.py --all

    # ドライラン（実際の処理はしない）
    python src/scripts/collect_dmm_faces.py --all --dry-run

    # 統計情報のみ表示
    python src/scripts/collect_dmm_faces.py --stats

環境変数:
    DMM_API_ID: DMM API ID
    DMM_AFFILIATE_ID: DMM アフィリエイトID
"""

import os
import sys
import argparse
import time
from pathlib import Path
from typing import List, Optional

# 環境変数読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("python-dotenvがインストールされていません。pipでインストールしてください。")
    sys.exit(1)

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.dmm.actress_image_collector import DmmActressImageCollector
from src.dmm.models import CollectionConfig, CollectionStatus
from src.database.person_database import PersonDatabase
from src.utils import log_utils

# ログ設定
logger = log_utils.get_logger(__name__)


class DmmFaceCollectionRunner:
    """DMM顔写真収集実行クラス"""

    def __init__(self, dry_run: bool = False, config: Optional[CollectionConfig] = None):
        """初期化

        Args:
            dry_run (bool): ドライラン実行フラグ
            config (Optional[CollectionConfig]): 収集設定
        """
        self.dry_run = dry_run
        self.config = config or CollectionConfig()
        self.db = PersonDatabase()

        # stats表示やdry_runの場合はCollectorを初期化しない
        self.collector = None
        if not dry_run:
            try:
                self.collector = DmmActressImageCollector(self.config)
            except ValueError as e:
                # 環境変数未設定の場合はエラーとして扱わない（統計表示時など）
                logger.warning(f"Collector初期化スキップ: {str(e)}")
                self.collector = None

        # 統計情報
        self.stats = {
            'total_processed': 0,
            'success': 0,
            'already_processed': 0,
            'no_dmm_id': 0,
            'no_base_image': 0,
            'no_valid_images': 0,
            'errors': 0,
            'processing_time': 0.0
        }

        logger.info(f"収集実行クラス初期化完了 - DryRun: {dry_run}")

    def run_single_actress(self, person_id: int) -> bool:
        """単一女優の収集実行

        Args:
            person_id (int): 人物ID

        Returns:
            bool: 成功した場合True
        """
        try:
            # 女優情報確認
            person_detail = self.db.get_person_detail(person_id)
            if not person_detail:
                print(f"❌ 女優が見つかりません (ID: {person_id})")
                return False

            actress_name = person_detail['name']
            print(f"🎯 収集対象: {actress_name} (ID: {person_id})")

            if self.dry_run:
                print("📋 [DRY-RUN] 実際の処理はスキップします")
                return True

            # 収集実行
            start_time = time.time()
            result = self.collector.collect_actress_images(person_id)
            processing_time = time.time() - start_time

            # 結果表示
            self._display_result(result)
            self._update_stats(result, processing_time)

            return result.is_success

        except Exception as e:
            logger.error(f"単一女優収集エラー: {str(e)}")
            print(f"❌ エラーが発生しました: {str(e)}")
            return False

    def run_actress_by_name(self, actress_name: str) -> bool:
        """女優名指定で収集実行

        Args:
            actress_name (str): 女優名

        Returns:
            bool: 成功した場合True
        """
        try:
            # 女優情報検索
            person = self.db.get_person_by_name(actress_name)
            if not person:
                print(f"❌ 女優が見つかりません: {actress_name}")
                return False

            return self.run_single_actress(person['person_id'])

        except Exception as e:
            logger.error(f"女優名指定収集エラー: {str(e)}")
            print(f"❌ エラーが発生しました: {str(e)}")
            return False

    def run_all_actresses(self, limit: Optional[int] = None) -> dict:
        """全女優対象で収集実行

        Args:
            limit (Optional[int]): 処理数制限

        Returns:
            dict: 実行結果統計
        """
        try:
            # 対象女優取得
            candidates = self._get_collection_candidates()

            if not candidates:
                print("📭 収集対象の女優が見つかりません")
                return self.stats

            total_candidates = len(candidates)
            if limit:
                candidates = candidates[:limit]
                print(f"📋 収集対象: {len(candidates)}名 (全{total_candidates}名中)")
            else:
                print(f"📋 収集対象: {total_candidates}名")

            if self.dry_run:
                print("📋 [DRY-RUN] 実際の処理はスキップします")
                self._display_candidates(candidates)
                return self.stats

            # 順次実行
            overall_start_time = time.time()

            for i, person in enumerate(candidates, 1):
                person_id = person['person_id']
                actress_name = person['name']

                print(f"\\n[{i}/{len(candidates)}] 🎯 {actress_name} (ID: {person_id})")

                try:
                    result = self.collector.collect_actress_images(person_id)
                    self._display_result(result, compact=True)
                    self._update_stats(result)

                    # 進捗表示
                    if i % 10 == 0:
                        self._display_progress_stats()

                except Exception as e:
                    logger.error(f"女優処理エラー ({actress_name}): {str(e)}")
                    print(f"❌ エラー: {str(e)}")
                    self.stats['errors'] += 1

                finally:
                    self.stats['total_processed'] += 1

            # 最終統計
            overall_time = time.time() - overall_start_time
            self.stats['processing_time'] = overall_time

            print("\\n" + "="*60)
            print("📊 最終結果")
            print("="*60)
            self._display_final_stats()

            return self.stats

        except Exception as e:
            logger.error(f"全女優収集エラー: {str(e)}")
            print(f"❌ エラーが発生しました: {str(e)}")
            return self.stats

    def display_stats(self):
        """統計情報を表示"""
        if self.collector:
            stats = self.collector.get_collection_stats()
        else:
            # ドライラン時は簡易統計
            candidates = self._get_collection_candidates()
            stats = {
                "total_actresses": len(self.db.get_all_persons()),
                "collection_candidates": len(candidates),
                "processed_actresses": 0,
                "total_images": 0,
                "config": self.config.__dict__
            }

        print("\\n📊 DMM顔写真収集統計")
        print("="*50)
        print(f"全女優数: {stats.get('total_actresses', 0)}名")
        print(f"収集対象: {stats.get('collection_candidates', len(self._get_collection_candidates()))}名")
        print(f"処理済み: {stats.get('processed_actresses', 0)}名")
        print(f"収集画像: {stats.get('total_images', 0)}枚")
        print("\\n⚙️ 収集設定")
        print("-"*30)
        config = stats.get('config', self.config.__dict__)
        print(f"類似度閾値: {config.get('similarity_threshold', 0.55)}")
        print(f"最大収集数/女優: {config.get('max_faces_per_actress', 3)}枚")
        print(f"DMM商品取得数: {config.get('dmm_products_limit', 50)}件")
        print(f"保存先: {config.get('save_directory_template', 'data/images/base/{actress_name}')}")

    def _get_collection_candidates(self) -> List[dict]:
        """収集対象女優リストを取得

        Returns:
            List[dict]: 収集対象女優リスト
        """
        try:
            all_persons = self.db.get_all_persons()

            # DMM IDが設定されている女優のみ
            candidates = []
            for person in all_persons:
                if person['dmm_actress_id']:
                    # ローカル基準画像ファイル存在確認
                    local_path = Path(f"data/images/base/{person['name']}/base.jpg")
                    if local_path.exists():
                        candidates.append(person)

            return candidates

        except Exception as e:
            logger.error(f"収集対象取得エラー: {str(e)}")
            return []

    def _display_candidates(self, candidates: List[dict]):
        """収集対象を表示（ドライラン用）"""
        print("\\n📋 収集対象女優一覧")
        print("-"*40)
        for i, person in enumerate(candidates, 1):
            print(f"{i:3d}. {person['name']} (ID: {person['person_id']}, DMM ID: {person['dmm_actress_id']})")

    def _display_result(self, result, compact: bool = False):
        """収集結果を表示

        Args:
            result: 収集結果
            compact (bool): コンパクト表示フラグ
        """
        status_icons = {
            CollectionStatus.SUCCESS: "✅",
            CollectionStatus.ALREADY_PROCESSED: "⏭️",
            CollectionStatus.NO_DMM_ID: "❌",
            CollectionStatus.NO_BASE_IMAGE: "❌",
            CollectionStatus.NO_VALID_IMAGES: "📭",
            CollectionStatus.API_ERROR: "🔧",
            CollectionStatus.ERROR: "❌"
        }

        icon = status_icons.get(result.status, "❓")

        if compact:
            # コンパクト表示
            if result.status == CollectionStatus.SUCCESS:
                print(f"{icon} 成功: {result.success_count}枚保存 ({result.processing_time:.1f}s)")
            else:
                print(f"{icon} {result.status.value}: {result.error_message}")
        else:
            # 詳細表示
            print(f"\\n{icon} 結果: {result.status.value}")
            print(f"処理時間: {result.processing_time:.2f}秒")

            if result.status == CollectionStatus.SUCCESS:
                print(f"商品数: {result.total_products}")
                print(f"保存数: {result.success_count}枚")
                if result.saved_faces:
                    print("\\n💾 保存ファイル:")
                    for face in result.saved_faces:
                        filename = Path(face.file_path).name
                        print(f"  - {filename} (類似度: {face.similarity_score:.3f})")

            elif result.error_message:
                print(f"エラー: {result.error_message}")

    def _update_stats(self, result, processing_time: float = 0.0):
        """統計を更新"""
        self.stats['total_processed'] += 1

        if result.status == CollectionStatus.SUCCESS:
            self.stats['success'] += 1
        elif result.status == CollectionStatus.ALREADY_PROCESSED:
            self.stats['already_processed'] += 1
        elif result.status == CollectionStatus.NO_DMM_ID:
            self.stats['no_dmm_id'] += 1
        elif result.status == CollectionStatus.NO_BASE_IMAGE:
            self.stats['no_base_image'] += 1
        elif result.status == CollectionStatus.NO_VALID_IMAGES:
            self.stats['no_valid_images'] += 1
        else:
            self.stats['errors'] += 1

        if processing_time > 0:
            self.stats['processing_time'] += processing_time

    def _display_progress_stats(self):
        """進捗統計を表示"""
        total = self.stats['total_processed']
        success = self.stats['success']
        print(f"\\n📊 進捗: {total}名処理済み | 成功: {success}名")

    def _display_final_stats(self):
        """最終統計を表示"""
        total = self.stats['total_processed']
        success = self.stats['success']
        already = self.stats['already_processed']
        no_dmm = self.stats['no_dmm_id']
        no_base = self.stats['no_base_image']
        no_images = self.stats['no_valid_images']
        errors = self.stats['errors']
        total_time = self.stats['processing_time']

        print(f"処理総数: {total}名")
        print(f"✅ 成功: {success}名")
        print(f"⏭️ 処理済み: {already}名")
        print(f"❌ DMM ID未設定: {no_dmm}名")
        print(f"❌ 基準画像なし: {no_base}名")
        print(f"📭 有効画像なし: {no_images}名")
        print(f"❌ エラー: {errors}名")
        print(f"⏱️ 総処理時間: {total_time:.1f}秒")

        if total > 0:
            avg_time = total_time / total
            print(f"⏱️ 平均処理時間: {avg_time:.1f}秒/女優")

    def close(self):
        """リソースを閉じる"""
        if self.collector:
            self.collector.close()
        self.db.close()


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="DMM API 女優顔写真収集スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # 実行モード
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--person-id', type=int, help='人物IDを指定して実行')
    group.add_argument('--actress-name', type=str, help='女優名を指定して実行')
    group.add_argument('--all', action='store_true', help='全女優を対象に実行')
    group.add_argument('--stats', action='store_true', help='統計情報のみ表示')

    # オプション
    parser.add_argument('--dry-run', action='store_true', help='ドライラン実行（実際の処理はしない）')
    parser.add_argument('--limit', type=int, help='処理数制限（--all使用時）')
    parser.add_argument('--similarity-threshold', type=float, default=0.55, help='類似度閾値 (default: 0.55)')
    parser.add_argument('--max-faces', type=int, default=3, help='最大収集数/女優 (default: 3)')
    parser.add_argument('--save-products', action='store_true', help='商品画像も保存する（検証用）')
    parser.add_argument('--no-right-priority', action='store_true', help='右側顔優先を無効にする（デフォルトは右側優先）')
    parser.add_argument('--face-expand-ratio', type=float, default=0.2, help='顔領域拡張率 (default: 0.2)')
    parser.add_argument('--min-face-size', type=int, default=150, help='最小顔画像サイズ (default: 150)')
    parser.add_argument('--verbose', action='store_true', help='詳細ログ出力')

    args = parser.parse_args()

    # ログレベル設定
    if args.verbose:
        log_utils.set_log_level("DEBUG")

    # 収集設定
    config = CollectionConfig(
        similarity_threshold=args.similarity_threshold,
        max_faces_per_actress=args.max_faces,
        save_product_images=args.save_products,
        prioritize_right_faces=not args.no_right_priority,  # --no-right-priorityが指定されていない場合は右側優先
        face_expand_ratio=args.face_expand_ratio,
        min_face_size=args.min_face_size
    )

    # 実行クラス初期化
    runner = DmmFaceCollectionRunner(dry_run=args.dry_run, config=config)

    try:
        print("🚀 DMM API 女優顔写真収集スクリプト")
        print("="*50)

        # 環境変数チェック（実際の処理が必要な場合のみ）
        if not args.stats and not args.dry_run and not runner.collector:
            api_id = os.getenv('DMM_API_ID')
            affiliate_id = os.getenv('DMM_AFFILIATE_ID')

            if not api_id or not affiliate_id:
                print("❌ 環境変数が設定されていません:")
                print("   DMM_API_ID, DMM_AFFILIATE_ID を設定してください")
                return 1

        # 実行
        if args.stats:
            runner.display_stats()
        elif args.person_id:
            success = runner.run_single_actress(args.person_id)
            return 0 if success else 1
        elif args.actress_name:
            success = runner.run_actress_by_name(args.actress_name)
            return 0 if success else 1
        elif args.all:
            runner.run_all_actresses(limit=args.limit)

        return 0

    except KeyboardInterrupt:
        print("\\n⚠️ ユーザーによって中断されました")
        return 1
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}")
        print(f"❌ 予期しないエラーが発生しました: {str(e)}")
        return 1
    finally:
        runner.close()


if __name__ == "__main__":
    sys.exit(main())