#!/usr/bin/env python3
"""
base_image_pathのURLからFAISSデータベースに顔画像を登録するスクリプト

このスクリプトは、personsテーブルのbase_image_path（URL）から顔画像を取得し、
FAISSデータベースに登録します。重複チェックやバッチ処理機能を含みます。
"""

import argparse
import gc
import hashlib
import logging
import time
from typing import Optional, List, Dict, Any
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.person_database import PersonDatabase
from src.database.face_index_database import FaceIndexDatabase
from src.face import face_utils
from src.utils import log_utils
# from src.utils.safe_operations import create_backup  # モジュールが見つからないためコメントアウト
from src.core.exceptions import ImageValidationException
from src.core.errors import ErrorCode

# ロガーの設定
logger = log_utils.get_logger(__name__)


class BaseImageRegistrar:
    """base_image_pathのURLをFAISSデータベースに登録するクラス"""
    
    def __init__(self, db_path: Optional[str] = None, index_path: Optional[str] = None):
        """
        Args:
            db_path (Optional[str]): データベースファイルのパス（テスト用）
            index_path (Optional[str]): FAISSインデックスファイルのパス（テスト用）
        """
        self.db_path = db_path
        self.index_path = index_path
        self.person_db = PersonDatabase(db_path)
        self.face_db = FaceIndexDatabase(db_path, index_path)
        self.stats = {
            'total': 0,
            'success': 0,
            'skipped': 0,
            'errors': 0,
            'error_details': []
        }
    
    def generate_image_hash(self, image_url: str, person_id: int) -> str:
        """画像URLとperson_idから一意のハッシュを生成
        
        Args:
            image_url (str): 画像のURL
            person_id (int): 人物ID
            
        Returns:
            str: 生成されたハッシュ値
        """
        # URLとperson_idを組み合わせてハッシュ化
        hash_input = f"{image_url}_{person_id}".encode('utf-8')
        return hashlib.sha256(hash_input).hexdigest()
    
    def is_image_already_registered(self, image_path: str, image_hash: str) -> bool:
        """画像が既にFAISSデータベースに登録されているかチェック
        
        Args:
            image_path (str): 画像のURL/パス
            image_hash (str): 画像のハッシュ値
            
        Returns:
            bool: 既に登録されている場合True
        """
        return self._is_image_already_registered_db(image_path, image_hash, self.face_db)

    def _is_image_already_registered_db(self, image_path: str, image_hash: str, face_db: FaceIndexDatabase) -> bool:
        """画像が既にFAISSデータベースに登録されているかチェック（DB指定版）
        
        Args:
            image_path (str): 画像のURL/パス
            image_hash (str): 画像のハッシュ値
            face_db (FaceIndexDatabase): FaceIndexDatabaseインスタンス
            
        Returns:
            bool: 既に登録されている場合True
        """
        # image_pathで検索
        face_db.cursor.execute(
            "SELECT COUNT(*) as count FROM face_images WHERE image_path = ?",
            (image_path,)
        )
        path_result = face_db.cursor.fetchone()
        if path_result and path_result['count'] > 0:
            return True
        
        # image_hashで検索
        face_db.cursor.execute(
            "SELECT COUNT(*) as count FROM face_images WHERE image_hash = ?",
            (image_hash,)
        )
        hash_result = face_db.cursor.fetchone()
        return hash_result and hash_result['count'] > 0
    
    def _update_stats(self, stat_type: str, error_detail: Optional[Dict[str, Any]] = None):
        """統計更新"""
        self.stats[stat_type] += 1
        if error_detail and stat_type == 'errors':
            self.stats['error_details'].append(error_detail)

    def register_single_person(self, person: Dict[str, Any], skip_if_registered: bool = True) -> bool:
        """単一の人物をFAISSデータベースに登録
        
        Args:
            person (Dict[str, Any]): 人物情報
            skip_if_registered (bool): 既に登録済みの場合スキップするか
            
        Returns:
            bool: 登録に成功した場合True
        """
        return self._register_single_person_internal(
            person, skip_if_registered, self.face_db
        )

    def _register_single_person_internal(self, person: Dict[str, Any], skip_if_registered: bool, 
                                       face_db: FaceIndexDatabase) -> bool:
        """単一の人物をFAISSデータベースに登録（内部実装）
        
        Args:
            person (Dict[str, Any]): 人物情報
            skip_if_registered (bool): 既に登録済みの場合スキップするか
            face_db (FaceIndexDatabase): FaceIndexDatabaseインスタンス
            
        Returns:
            bool: 登録に成功した場合True
        """
        person_id = person['person_id']
        person_name = person['name']
        base_image_path = person['base_image_path']
        
        logger.info(f"人物の処理を開始: {person_name} (ID: {person_id})")
        
        # 画像ハッシュを事前生成（重複チェック用）
        image_hash = self.generate_image_hash(base_image_path, person_id)
        
        # 既に登録済みかチェック（画像ベース）
        if skip_if_registered and self._is_image_already_registered_db(base_image_path, image_hash, face_db):
            logger.info(f"同じ画像が既に登録済みのためスキップ: {person_name} (ID: {person_id}, URL: {base_image_path})")
            self._update_stats('skipped')
            return False
        
        try:
            # URLから顔エンコーディングを取得
            logger.debug(f"URLから顔エンコーディングを取得: {base_image_path}")
            encoding = face_utils.get_face_encoding(base_image_path)
            
            if encoding is None:
                logger.warning(f"顔エンコーディングの取得に失敗: {person_name} (URL: {base_image_path})")
                self._update_stats('errors', {
                    'person_id': person_id,
                    'name': person_name,
                    'url': base_image_path,
                    'error': '顔エンコーディングの取得に失敗'
                })
                return False
            
            # 画像ハッシュは既に生成済み
            
            # FAISSデータベースに追加
            logger.debug(f"FAISSデータベースに追加: {person_name}")
            image_id = face_db.add_face_image(
                person_id=person_id,
                image_path=base_image_path,
                encoding=encoding,
                image_hash=image_hash,
                metadata={'source': 'base_image_path', 'registered_by': 'register_base_images.py'}
            )
            
            if image_id:
                logger.info(f"登録完了: {person_name} (ID: {person_id}, image_id: {image_id})")
                self._update_stats('success')
                return True
            else:
                logger.error(f"FAISSデータベースへの追加に失敗: {person_name}")
                self._update_stats('errors', {
                    'person_id': person_id,
                    'name': person_name,
                    'url': base_image_path,
                    'error': 'FAISSデータベースへの追加に失敗'
                })
                return False
                
        except ImageValidationException as e:
            if e.code == ErrorCode.MULTIPLE_FACES:
                logger.warning(f"複数の顔が検出されました: {person_name} (URL: {base_image_path})")
                self._update_stats('errors', {
                    'person_id': person_id,
                    'name': person_name,
                    'url': base_image_path,
                    'error': '複数の顔が検出された'
                })
            else:
                logger.error(f"画像検証エラー: {person_name} - {str(e)}")
                self._update_stats('errors', {
                    'person_id': person_id,
                    'name': person_name,
                    'url': base_image_path,
                    'error': f'画像検証エラー: {str(e)}'
                })
            return False
            
        except Exception as e:
            logger.error(f"予期しないエラー: {person_name} - {str(e)}")
            self._update_stats('errors', {
                'person_id': person_id,
                'name': person_name,
                'url': base_image_path,
                'error': f'予期しないエラー: {str(e)}'
            })
            return False

    
    def register_batch(self, batch_size: int = 10, max_persons: Optional[int] = None, 
                      skip_if_registered: bool = True, dry_run: bool = False) -> Dict[str, Any]:
        """バッチ処理でbase_image_pathを持つ人物を登録
        
        Args:
            batch_size (int): バッチサイズ
            max_persons (Optional[int]): 処理する最大人数
            skip_if_registered (bool): 既に登録済みの場合スキップするか
            dry_run (bool): ドライランモード（実際の登録は行わない）
            
        Returns:
            Dict[str, Any]: 処理結果の統計情報
        """
        # 対象人物の総数を取得
        total_count = self.person_db.get_persons_with_base_image_count(exclude_registered=skip_if_registered)
        
        if max_persons:
            total_count = min(total_count, max_persons)
        
        logger.info(f"登録対象人物数: {total_count}")
        
        if dry_run:
            logger.info("--- ドライランモード ---")
        
        self.stats['total'] = total_count
        start_time = time.time()
        
        # バッチ処理
        offset = 0
        while offset < total_count:
            current_batch_size = min(batch_size, total_count - offset)
            
            # バッチ取得
            persons = self.person_db.get_persons_with_base_image(
                exclude_registered=skip_if_registered,
                limit=current_batch_size,
                offset=offset
            )
            
            if not persons:
                break
            
            logger.info(f"バッチ処理中... ({offset + 1}-{offset + len(persons)}/{total_count})")
            
            # バッチ内の各人物を処理
            if dry_run:
                # ドライランの場合
                for person in persons:
                    logger.info(f"[DRY RUN] 処理対象: {person['name']} (ID: {person['person_id']})")
                    self._update_stats('success')
            else:
                # 直列処理
                for person in persons:
                    self.register_single_person(person, skip_if_registered)
            
            offset += len(persons)
            
            # メモリクリーンアップ（一定間隔で実行）
            if offset % (batch_size * 10) == 0:
                gc.collect()
                logger.debug(f"メモリクリーンアップを実行: {offset}件処理済み")
            
            # 進捗表示
            elapsed_time = time.time() - start_time
            if elapsed_time > 0:
                rate = (offset / elapsed_time)
                remaining_time = (total_count - offset) / rate if rate > 0 else 0
                logger.info(f"進捗: {offset}/{total_count} ({offset/total_count*100:.1f}%) - "
                          f"処理速度: {rate:.2f}件/秒 - 残り時間: {remaining_time:.0f}秒")
        
        # 最終統計
        total_time = time.time() - start_time
        self.stats['total_time'] = total_time
        
        return self.stats
    
    def print_stats(self):
        """処理結果の統計情報を表示"""
        print("\n=== 処理結果 ===")
        print(f"総処理件数: {self.stats['total']}")
        print(f"成功: {self.stats['success']}")
        print(f"スキップ: {self.stats['skipped']}")
        print(f"エラー: {self.stats['errors']}")
        
        if 'total_time' in self.stats:
            print(f"処理時間: {self.stats['total_time']:.2f}秒")
            if self.stats['total_time'] > 0:
                print(f"処理速度: {self.stats['total']/self.stats['total_time']:.2f}件/秒")
        
        # エラー詳細
        if self.stats['error_details']:
            print(f"\n=== エラー詳細 (最初の10件) ===")
            for i, error in enumerate(self.stats['error_details'][:10]):
                print(f"{i+1}. {error['name']} (ID: {error['person_id']})")
                print(f"   URL: {error['url']}")
                print(f"   エラー: {error['error']}")
    
    def close(self):
        """データベース接続を閉じる"""
        self.person_db.close()
        self.face_db.close()


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='base_image_pathのURLをFAISSデータベースに登録')
    parser.add_argument('--batch-size', type=int, default=10, help='バッチサイズ（デフォルト: 10）')
    parser.add_argument('--max-persons', type=int, help='処理する最大人数')
    parser.add_argument('--skip-registered', action='store_true', default=True, 
                       help='既に登録済みの人物をスキップ（デフォルト: True）')
    parser.add_argument('--force', action='store_true', 
                       help='既に登録済みの人物も再登録する')
    parser.add_argument('--dry-run', action='store_true', 
                       help='ドライランモード（実際の登録は行わない）')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='詳細ログを出力')
    parser.add_argument('--no-backup', action='store_true',
                       help='自動バックアップを無効にする')
    parser.add_argument('--backup-before-start', action='store_true',
                       help='処理開始前にFAISSインデックスをバックアップ')
    
    args = parser.parse_args()
    
    # ログレベル設定
    if args.verbose:
        log_utils.setup_logging(level=logging.DEBUG)
    else:
        log_utils.setup_logging(level=logging.INFO)
    
    # skip_registeredの設定
    skip_registered = not args.force if args.force else args.skip_registered
    
    registrar = BaseImageRegistrar()
    
    try:
        logger.info("base_image_path登録処理を開始します")
        
        # 事前バックアップ（機能は無効化）
        if args.backup_before_start and not args.no_backup:
            logger.warning("バックアップ機能は現在無効です（safe_operationsモジュールが見つかりません）")
        
        logger.info("処理モード: 直列処理")
        
        # バッチ処理実行
        registrar.register_batch(
            batch_size=args.batch_size,
            max_persons=args.max_persons,
            skip_if_registered=skip_registered,
            dry_run=args.dry_run
        )
        
        # 結果表示
        registrar.print_stats()
        
        # FAISSインデックスの統計情報
        index_stats = registrar.face_db.get_index_stats()
        print(f"\n=== FAISSインデックス統計 ===")
        print(f"登録ベクトル数: {index_stats['faiss_vector_count']}")
        print(f"DB画像数: {index_stats['db_image_count']}")
        print(f"DBインデックス数: {index_stats['db_index_count']}")
        
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
        registrar.print_stats()
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {str(e)}")
        raise
    finally:
        registrar.close()


if __name__ == "__main__":
    main()