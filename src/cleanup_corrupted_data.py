#!/usr/bin/env python3
"""
破損したface_imagesデータ（image_id 22549以降）を削除するスクリプト

face_images、face_indexes、FAISSインデックスから該当データを削除します。
"""

import sqlite3
import sys
import os

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils import log_utils

logger = log_utils.get_logger(__name__)

def cleanup_corrupted_data(db_path: str = "data/face_database.db", threshold_image_id: int = 22549):
    """image_id閾値以降の破損データを削除"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 削除対象の確認
        cursor.execute("SELECT COUNT(*) FROM face_images WHERE image_id >= ?", (threshold_image_id,))
        face_images_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM face_indexes 
            WHERE image_id >= ?
        """, (threshold_image_id,))
        face_indexes_count = cursor.fetchone()[0]
        
        logger.info(f"削除対象の確認:")
        logger.info(f"  face_images (image_id >= {threshold_image_id}): {face_images_count}件")
        logger.info(f"  face_indexes (image_id >= {threshold_image_id}): {face_indexes_count}件")
        
        if face_images_count == 0 and face_indexes_count == 0:
            logger.info("削除対象のデータがありません。")
            return True
        
        # 削除前の全体統計
        cursor.execute("SELECT COUNT(*) FROM face_images")
        total_face_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM face_indexes")
        total_face_indexes = cursor.fetchone()[0]
        
        logger.info(f"削除前の全体統計:")
        logger.info(f"  face_images総数: {total_face_images}")
        logger.info(f"  face_indexes総数: {total_face_indexes}")
        
        # トランザクション開始
        cursor.execute("BEGIN TRANSACTION")
        
        # face_indexesから削除（外部キー制約のため先に削除）
        logger.info(f"face_indexesから削除中...")
        cursor.execute("""
            DELETE FROM face_indexes 
            WHERE image_id >= ?
        """, (threshold_image_id,))
        deleted_indexes = cursor.rowcount
        
        # face_imagesから削除
        logger.info(f"face_imagesから削除中...")
        cursor.execute("""
            DELETE FROM face_images 
            WHERE image_id >= ?
        """, (threshold_image_id,))
        deleted_images = cursor.rowcount
        
        # 削除後の確認
        cursor.execute("SELECT COUNT(*) FROM face_images")
        remaining_face_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM face_indexes")
        remaining_face_indexes = cursor.fetchone()[0]
        
        logger.info(f"削除結果:")
        logger.info(f"  削除されたface_images: {deleted_images}件")
        logger.info(f"  削除されたface_indexes: {deleted_indexes}件")
        logger.info(f"  残存face_images: {remaining_face_images}件")
        logger.info(f"  残存face_indexes: {remaining_face_indexes}件")
        
        # コミット
        cursor.execute("COMMIT")
        logger.info("データベースの削除が完了しました")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")
        cursor.execute("ROLLBACK")
        return False
    finally:
        conn.close()
    
    return True

def cleanup_faiss_index(index_path: str = "data/face.index"):
    """FAISSインデックスファイルを削除"""
    
    if os.path.exists(index_path):
        logger.info(f"FAISSインデックスファイルを削除中: {index_path}")
        try:
            os.remove(index_path)
            logger.info("FAISSインデックスファイルを削除しました")
            return True
        except Exception as e:
            logger.error(f"FAISSインデックスファイルの削除に失敗: {str(e)}")
            return False
    else:
        logger.info("FAISSインデックスファイルは存在しません")
        return True

def resequence_index_positions(db_path: str = "data/face_database.db"):
    """index_positionを0から連番で再割り当て"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        logger.info("index_positionを0から連番で再割り当て中...")
        
        # 残存するレコードを取得（image_idでソート）
        cursor.execute("""
            SELECT index_id
            FROM face_indexes
            ORDER BY image_id
        """)
        all_records = cursor.fetchall()
        
        # トランザクション開始
        cursor.execute("BEGIN TRANSACTION")
        
        # 各レコードに新しいindex_positionを割り当て
        for new_position, (index_id,) in enumerate(all_records):
            cursor.execute("""
                UPDATE face_indexes 
                SET index_position = ? 
                WHERE index_id = ?
            """, (new_position, index_id))
        
        cursor.execute("COMMIT")
        logger.info(f"index_positionの再割り当てが完了: 0-{len(all_records)-1}")
        
    except Exception as e:
        logger.error(f"index_position再割り当てでエラー: {str(e)}")
        cursor.execute("ROLLBACK")
        return False
    finally:
        conn.close()
    
    return True

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='破損データの削除とクリーンアップ')
    parser.add_argument('--threshold', type=int, default=22549,
                       help='削除するimage_idの閾値（この値以降を削除）')
    parser.add_argument('--confirm', action='store_true',
                       help='削除を確認せずに実行')
    
    args = parser.parse_args()
    
    logger.info(f"破損データクリーンアップスクリプトを開始します")
    logger.info(f"削除対象: image_id >= {args.threshold}")
    
    if not args.confirm:
        response = input(f"\n⚠️  image_id {args.threshold}以降のデータを削除しますか？ (yes/no): ")
        if response.lower() != 'yes':
            logger.info("操作がキャンセルされました")
            return
    
    # 1. データベースから削除
    if not cleanup_corrupted_data(threshold_image_id=args.threshold):
        logger.error("データベースの削除に失敗しました")
        return
    
    # 2. FAISSインデックスファイルを削除
    if not cleanup_faiss_index():
        logger.error("FAISSインデックスファイルの削除に失敗しました")
        return
    
    # 3. index_positionを再割り当て
    if not resequence_index_positions():
        logger.error("index_positionの再割り当てに失敗しました")
        return
    
    # 4. 最終確認
    conn = sqlite3.connect("data/face_database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM face_images")
    total_images = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM face_indexes")
    total_indexes = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(index_position), MAX(index_position) FROM face_indexes")
    result = cursor.fetchone()
    min_pos, max_pos = result if result[0] is not None else (None, None)
    
    conn.close()
    
    logger.info(f"\n=== 最終確認 ===")
    logger.info(f"残存face_images: {total_images}件")
    logger.info(f"残存face_indexes: {total_indexes}件")
    
    if min_pos is not None:
        logger.info(f"index_position範囲: {min_pos} - {max_pos}")
        
        if total_images == total_indexes and min_pos == 0 and max_pos == total_images - 1:
            logger.info("✅ データ整合性が正常に修復されました")
            logger.info("\n次のコマンドでFAISSインデックスを再構築してください:")
            logger.info("python src/rebuild_faiss_index.py --batch-size=50 --verbose")
        else:
            logger.warning("⚠️ データ整合性に問題がある可能性があります")
    else:
        logger.info("index_positionのデータがありません")

if __name__ == "__main__":
    main()