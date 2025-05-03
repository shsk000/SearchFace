import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
from face_comparison import get_face_encodings
import faiss
import sqlite3
from datetime import datetime
import json

def _calculate_similarity_percentage(distance: float) -> float:
    """
    距離から類似率（パーセンテージ）を計算します
    
    Args:
        distance (float): FAISSによって計算された距離
        
    Returns:
        float: 類似率（0-100%）
    
    Note:
        - 距離0.4以上：異なる人物の可能性が高い
        - 距離0.6以上：ほぼ確実に異なる人物
    """
    # 閾値の設定
    max_similar_distance = 0.4    # この距離以上は異なる人物の可能性が高い（50%未満）
    max_distance = 0.6           # この距離以上は完全に異なる人物（0%）
    
    if distance >= max_distance:
        return 0.0
    elif distance >= max_similar_distance:
        # 0.4-0.6の範囲を0-50%にマッピング
        ratio = (max_distance - distance) / (max_distance - max_similar_distance)
        return ratio * 50.0
    else:
        # 0-0.4の範囲を50-100%にマッピング
        ratio = (max_similar_distance - distance) / max_similar_distance
        return 50.0 + (ratio * 50.0)

class FaceDatabase:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, index_path: str = "data/face.index", 
                 db_path: str = "data/face_database.db"):
        if not hasattr(self, 'initialized'):
            self.index_path = index_path
            self.db_path = db_path
            self.index = None
            self._init_database()
            self._load_database()
            self.initialized = True
    
    def _init_database(self):
        """SQLiteデータベースの初期化"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # テーブルが存在しない場合のみ作成
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS faces (
                    face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    image_path TEXT NOT NULL,
                    index_position INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')
            conn.commit()
    
    def _load_database(self):
        """インデックスとデータベースをロード"""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            print(f"既存のインデックスをロードしました（登録済みデータ数: {self.index.ntotal}）")
    
    def is_name_registered(self, name: str) -> bool:
        """指定された名前が既にデータベースに登録されているか確認"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM faces WHERE name = ?', (name,))
            count = cursor.fetchone()[0]
            return count > 0
    
    def add_face(self, encoding: np.ndarray, name: str, image_path: str, metadata: Optional[Dict] = None) -> bool:
        """新しい顔を追加"""
        try:
            if self.index is None:
                self.index = faiss.IndexFlatL2(encoding.shape[0])
            
            # インデックスに追加
            self.index.add(np.array([encoding]).astype('float32'))
            index_position = self.index.ntotal - 1
            
            print(f"追加された顔のインデックス位置: {index_position}")  # デバッグ用
            
            # データベースに追加
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO faces (name, image_path, index_position, metadata)
                    VALUES (?, ?, ?, ?)
                ''', (name, image_path, index_position, 
                     json.dumps(metadata) if metadata else None))
                conn.commit()
            
            self._save_database()
            return True
        except Exception as e:
            print(f"エラー: {str(e)}")
            return False
    
    def _save_database(self):
        """インデックスを保存"""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
    
    def search_similar_faces(self, query_encoding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """類似顔を検索"""
        if self.index is None:
            raise ValueError("データベースに顔データが登録されていません。先にadd_face()で顔データを追加してください。")
        
        print(f"\nデータベース内の顔データ数: {self.index.ntotal}")
        
        query = np.array([query_encoding]).astype('float32')
        distances, indices = self.index.search(query, min(top_k, self.index.ntotal))
        
        print(f"検索結果のインデックス: {indices}")
        print(f"検索結果の距離: {distances}")
        
        results = []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # データベース内の全レコードを表示（デバッグ用）
            cursor.execute('SELECT * FROM faces ORDER BY index_position')
            all_faces = cursor.fetchall()
            print("\nデータベース内の全レコード:")
            for face in all_faces:
                print(f"face_id: {face['face_id']}, name: {face['name']}, index_position: {face['index_position']}")
            
            for idx, dist in zip(indices[0], distances[0]):
                if idx == -1:
                    continue
                
                print(f"\n検索中のインデックス: {idx}")
                # インデックス位置から顔データを検索（完全一致）
                cursor.execute('''
                    SELECT * FROM faces WHERE index_position = ? ORDER BY face_id LIMIT 1
                ''', (int(idx),))
                face_data = cursor.fetchone()
                
                if face_data:
                    similarity = _calculate_similarity_percentage(dist)
                    result = {
                        "face_id": face_data["face_id"],
                        "name": face_data["name"],
                        "image_path": face_data["image_path"],
                        "distance": float(dist),
                        "similarity": float(similarity),
                        "created_at": face_data["created_at"]
                    }
                    if face_data["metadata"]:
                        result["metadata"] = json.loads(face_data["metadata"])
                    
                    results.append(result)
                    print(f"検出結果: インデックス={idx}, 距離={dist:.2f}, 類似率={similarity:.1f}%, 名前={face_data['name']}")
                else:
                    print(f"警告: インデックス {idx} に対応する顔データが見つかりません")
        
        if not results:
            print("\n警告: 検索結果が0件でした")
        
        return results

def batch_add_faces(database: FaceDatabase, image_dir: str, name_mapping: Dict[str, str]):
    """
    ディレクトリ内の画像を一括でデータベースに追加します
    既に登録済みの名前はスキップします
    
    Args:
        database (FaceDatabase): 顔データベース
        image_dir (str): 画像が保存されているディレクトリ
        name_mapping (Dict[str, str]): ファイル名から人物名へのマッピング
    """
    print("\nデータベースに追加する画像:")
    for filename in name_mapping.keys():
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(image_dir, filename)
            name = name_mapping[filename]
            
            # 既に登録済みの場合はスキップ
            if database.is_name_registered(name):
                print(f"- {filename} -> {name} (スキップ: 既に登録済み)")
                continue
                
            print(f"- {filename} -> {name}")
            
            # 画像から顔エンコーディングを取得
            encodings, _ = get_face_encodings(image_path)
            if encodings:
                # 最初に検出された顔のみを使用
                database.add_face(encodings[0], name, image_path)
                print(f"  追加成功: {name}")
            else:
                print(f"  警告: {filename}から顔を検出できませんでした")

if __name__ == "__main__":
    # データベースの初期化
    db = FaceDatabase()
    
    # テスト用の画像ディレクトリと名前のマッピング
    image_dir = "data/images"
    name_mapping = {
        "person1.jpg": "石原さとみ",
        "person2.jpg": "橋本環奈",
        "person3.jpg": "広瀬すず"
    }
    
    # 画像を一括で追加
    batch_add_faces(db, image_dir, name_mapping)
    
    # クエリ画像で検索
    query_image = "data/images/input.jpg"
    encodings, _ = get_face_encodings(query_image)
    if encodings:
        results = db.search_similar_faces(encodings[0], top_k=3)
        
        # 結果を表示
        print("\n検索結果:")
        for result in results:
            print(f"名前: {result['name']}")
            print(f"類似率: {result['similarity']:.1f}%")
            print("---")
    else:
        print("クエリ画像から顔を検出できませんでした") 