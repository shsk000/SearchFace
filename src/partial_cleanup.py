#!/usr/bin/env python3
"""
部分的データ削除スクリプト

FAISSインデックスから特定範囲のベクトルを削除し、
データベースとの整合性を保ちながら部分削除を実行します。
"""

import sqlite3
import sys
import os
import numpy as np

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import faiss
from src.utils import log_utils

logger = log_utils.get_logger(__name__)

def get_deletion_range(db_path: str = "data/face_database.db", threshold_image_id: int = 22549):
    """削除対象のindex_position範囲を取得"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 削除対象のindex_position範囲を取得
        cursor.execute("""
            SELECT MIN(index_position), MAX(index_position), COUNT(*)
            FROM face_indexes 
            WHERE image_id >= ?
        """, (threshold_image_id,))
        
        result = cursor.fetchone()
        min_pos, max_pos, count = result
        
        if min_pos is None:
            logger.info(f"image_id >= {threshold_image_id} のデータは見つかりませんでした")
            return None, None, 0
        
        logger.info(f"削除対象範囲: index_position {min_pos} - {max_pos} ({count}件)")
        return min_pos, max_pos, count
        
    finally:
        conn.close()

def partial_cleanup_faiss(index_path: str = "data/face.index", 
                         min_pos: int = None, max_pos: int = None,
                         db_path: str = "data/face_database.db"):
    """FAISSインデックスから部分的にベクトルを削除"""
    
    if not os.path.exists(index_path):
        logger.error(f"FAISSインデックスファイルが存在しません: {index_path}")
        return False
    
    try:
        # 既存インデックスを読み込み
        logger.info(f"FAISSインデックスを読み込み中: {index_path}")
        original_index = faiss.read_index(index_path)
        total_vectors = original_index.ntotal
        logger.info(f"読み込み完了: {total_vectors}ベクトル")
        
        # 削除対象以外のベクトルを特定
        keep_positions = []
        
        # データベースから保持するindex_positionを取得
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if min_pos is not None and max_pos is not None:
            cursor.execute("""
                SELECT DISTINCT index_position
                FROM face_indexes
                WHERE index_position < ? OR index_position > ?
                ORDER BY index_position
            """, (min_pos, max_pos))
        else:
            # 全てのindex_positionを取得（削除なし）
            cursor.execute("""
                SELECT DISTINCT index_position
                FROM face_indexes
                ORDER BY index_position
            """)
        
        keep_positions = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"保持するベクトル数: {len(keep_positions)}")
        
        if len(keep_positions) == 0:
            logger.warning("保持するベクトルがありません")
            return False
        
        # 新しいインデックスを作成
        logger.info("新しいFAISSインデックスを作成中...")
        new_index = faiss.IndexFlatL2(128)  # face_recognitionは128次元
        
        # バッチサイズで処理（メモリ効率）
        batch_size = 1000
        new_vectors = []
        
        for i in range(0, len(keep_positions), batch_size):
            batch_positions = keep_positions[i:i + batch_size]
            
            # 対象ベクトルを取得
            batch_vectors = np.zeros((len(batch_positions), 128), dtype=np.float32)
            for j, pos in enumerate(batch_positions):
                if pos < total_vectors:
                    # 単一ベクトルを取得
                    vector = original_index.reconstruct(pos)
                    batch_vectors[j] = vector
            
            new_vectors.extend(batch_vectors)
            logger.debug(f"バッチ処理: {i+1}-{min(i+batch_size, len(keep_positions))}/{len(keep_positions)}")
        
        # 新しいインデックスにベクトルを追加
        if new_vectors:
            vectors_array = np.array(new_vectors, dtype=np.float32)
            new_index.add(vectors_array)
            logger.info(f"新しいインデックスに{new_index.ntotal}ベクトルを追加")
        
        # バックアップ作成
        backup_path = index_path + ".backup"
        logger.info(f"既存インデックスをバックアップ: {backup_path}")
        os.rename(index_path, backup_path)
        
        # 新しいインデックスを保存
        logger.info(f"新しいインデックスを保存: {index_path}")
        faiss.write_index(new_index, index_path)
        
        logger.info(f"FAISSインデックスの部分削除が完了")
        logger.info(f"削除前: {total_vectors}ベクトル → 削除後: {new_index.ntotal}ベクトル")
        
        return True
        
    except Exception as e:
        logger.error(f"FAISSインデックスの部分削除でエラー: {str(e)}")
        return False

def update_database_positions(db_path: str = "data/face_database.db", threshold_image_id: int = 22549):
    """データベースから対象データを削除し、index_positionを再割り当て"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        logger.info("データベースから対象データを削除中...")
        
        # トランザクション開始
        cursor.execute("BEGIN TRANSACTION")
        
        # face_indexesから削除
        cursor.execute("""
            DELETE FROM face_indexes 
            WHERE image_id >= ?
        """, (threshold_image_id,))
        deleted_indexes = cursor.rowcount
        
        # face_imagesから削除
        cursor.execute("""
            DELETE FROM face_images 
            WHERE image_id >= ?
        """, (threshold_image_id,))
        deleted_images = cursor.rowcount
        
        logger.info(f"削除されたレコード: face_images={deleted_images}, face_indexes={deleted_indexes}")
        
        # index_positionを0から連番で再割り当て
        logger.info("index_positionを再割り当て中...")
        
        cursor.execute("""
            SELECT index_id
            FROM face_indexes
            ORDER BY image_id
        """)
        remaining_records = cursor.fetchall()
        
        # 各レコードに新しいindex_positionを割り当て
        for new_position, (index_id,) in enumerate(remaining_records):
            cursor.execute("""
                UPDATE face_indexes 
                SET index_position = ? 
                WHERE index_id = ?
            """, (new_position, index_id))
        
        cursor.execute("COMMIT")
        logger.info(f"index_positionの再割り当て完了: 0-{len(remaining_records)-1}")
        
        return True
        
    except Exception as e:
        logger.error(f"データベース更新でエラー: {str(e)}")
        cursor.execute("ROLLBACK")
        return False
    finally:
        conn.close()

def verify_consistency(db_path: str = "data/face_database.db", index_path: str = "data/face.index"):
    """データベースとFAISSインデックスの整合性確認"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # データベースの統計
        cursor.execute("SELECT COUNT(*) FROM face_images")
        db_images = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM face_indexes")
        db_indexes = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(index_position), MAX(index_position) FROM face_indexes")
        result = cursor.fetchone()
        min_pos, max_pos = result if result[0] is not None else (None, None)
        
        # FAISSインデックスの統計
        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            faiss_vectors = index.ntotal
        else:
            faiss_vectors = 0
        
        logger.info(f"\n=== 整合性確認 ===")
        logger.info(f"face_images: {db_images}件")
        logger.info(f"face_indexes: {db_indexes}件")
        logger.info(f"FAISSベクトル: {faiss_vectors}件")
        
        if min_pos is not None:
            logger.info(f"index_position範囲: {min_pos} - {max_pos}")
        
        # 整合性判定
        if db_images == db_indexes == faiss_vectors and min_pos == 0 and max_pos == db_indexes - 1:
            logger.info("✅ 整合性確認: 正常")
            return True
        else:
            logger.warning("⚠️ 整合性に問題があります")
            return False
            
    finally:
        conn.close()

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='部分的データ削除とFAISSインデックス更新')
    parser.add_argument('--threshold', type=int, default=22549,
                       help='削除するimage_idの閾値（この値以降を削除）')
    parser.add_argument('--confirm', action='store_true',
                       help='削除を確認せずに実行')
    
    args = parser.parse_args()
    
    logger.info(f"部分削除スクリプトを開始します")
    logger.info(f"削除対象: image_id >= {args.threshold}")
    
    # 1. 削除範囲の確認
    min_pos, max_pos, count = get_deletion_range(threshold_image_id=args.threshold)
    
    if count == 0:
        logger.info("削除対象のデータがありません")
        return
    
    if not args.confirm:
        print(f"\n削除対象:")
        print(f"  image_id >= {args.threshold}: {count}件")
        print(f"  index_position範囲: {min_pos} - {max_pos}")
        response = input(f"\n⚠️  この範囲のデータを削除しますか？ (yes/no): ")
        if response.lower() != 'yes':
            logger.info("操作がキャンセルされました")
            return
    
    # 2. FAISSインデックスから部分削除
    if not partial_cleanup_faiss(min_pos=min_pos, max_pos=max_pos):
        logger.error("FAISSインデックスの部分削除に失敗しました")
        return
    
    # 3. データベースの更新
    if not update_database_positions(threshold_image_id=args.threshold):
        logger.error("データベースの更新に失敗しました")
        return
    
    # 4. 整合性確認
    verify_consistency()

if __name__ == "__main__":
    main()