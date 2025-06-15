#!/usr/bin/env python3
"""
FAISSインデックス整合性の簡易確認スクリプト
"""

import os
import sys
import sqlite3
import numpy as np
import faiss

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.face import face_utils
from src.utils import log_utils

logger = log_utils.get_logger(__name__)

def quick_integrity_test():
    """簡易整合性テスト"""
    
    print("=== FAISSインデックス整合性確認 ===")
    
    # 1. ファイル存在確認
    index_path = "data/face.index"
    if not os.path.exists(index_path):
        print("❌ FAISSインデックスファイルが存在しません")
        return False
    
    file_size = os.path.getsize(index_path)
    print(f"✅ FAISSインデックスファイル存在: {index_path} ({file_size:,} bytes)")
    
    # 2. FAISSインデックス読み込み
    try:
        index = faiss.read_index(index_path)
        print(f"✅ FAISSインデックス読み込み成功: {index.ntotal}ベクトル")
    except Exception as e:
        print(f"❌ FAISSインデックス読み込み失敗: {str(e)}")
        return False
    
    # 3. データベース確認
    db_path = "data/face_database.db"
    if not os.path.exists(db_path):
        print("❌ データベースファイルが存在しません")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 永瀬ゆいのデータ確認
    cursor.execute("""
        SELECT fi.image_id, fi.image_path, fxi.index_position, p.name
        FROM face_images fi
        JOIN face_indexes fxi ON fi.image_id = fxi.image_id
        JOIN persons p ON fi.person_id = p.person_id
        WHERE p.name = '永瀬ゆい' AND fi.image_path LIKE '%mlmm00078%'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("❌ 永瀬ゆいのテスト画像データが見つかりません")
        conn.close()
        return False
    
    image_id, image_path, index_position, name = result
    print(f"✅ テスト画像データ確認: {name}, position {index_position}")
    
    # 4. 顔エンコーディング取得
    test_image_path = image_path
    print(f"📷 テスト画像: {test_image_path}")
    
    try:
        encoding = face_utils.get_face_encoding(test_image_path)
        if encoding is None:
            print("❌ 顔エンコーディング取得失敗")
            conn.close()
            return False
        print("✅ 顔エンコーディング取得成功")
    except Exception as e:
        print(f"❌ 顔エンコーディング取得でエラー: {str(e)}")
        conn.close()
        return False
    
    # 5. FAISS検索実行
    try:
        distances, indices = index.search(np.array([encoding]), 3)
        print("✅ FAISS検索実行成功")
        
        print("\n=== 検索結果 ===")
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0:
                # データベースから該当するindex_positionの情報を取得
                cursor.execute("""
                    SELECT fi.image_path, p.name
                    FROM face_indexes fxi
                    JOIN face_images fi ON fxi.image_id = fi.image_id
                    JOIN persons p ON fi.person_id = p.person_id
                    WHERE fxi.index_position = ?
                """, (int(idx),))
                
                db_result = cursor.fetchone()
                if db_result:
                    db_image_path, db_name = db_result
                    print(f"{i+1}. Index: {idx}, Distance: {distance:.6f}, Person: {db_name}")
                    if 'mlmm00078' in db_image_path:
                        print("   🎯 これは検索に使った同じ画像です！")
                else:
                    print(f"{i+1}. Index: {idx}, Distance: {distance:.6f}, Person: データなし")
        
        # 6. 整合性判定
        closest_idx = indices[0][0]
        closest_distance = distances[0][0]
        
        if closest_idx == index_position and closest_distance < 0.1:
            print(f"\n🎉 整合性確認成功！")
            print(f"   期待されたindex_position: {index_position}")
            print(f"   実際の検索結果: {closest_idx}")
            print(f"   距離: {closest_distance:.6f}")
            conn.close()
            return True
        else:
            print(f"\n❌ 整合性確認失敗")
            print(f"   期待されたindex_position: {index_position}")
            print(f"   実際の検索結果: {closest_idx}")
            print(f"   距離: {closest_distance:.6f}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ FAISS検索でエラー: {str(e)}")
        conn.close()
        return False

if __name__ == "__main__":
    success = quick_integrity_test()
    if success:
        print("\n✅ 全ての整合性チェックに合格しました！")
    else:
        print("\n❌ 整合性チェックに失敗しました")