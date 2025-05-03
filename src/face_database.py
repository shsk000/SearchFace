import os
import pickle
import numpy as np
from typing import List, Dict, Tuple, Optional
from face_comparison import get_face_encodings
import faiss  # 高速な類似度検索ライブラリ
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
    _instance = None  # シングルトン用
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, index_path: str = "data/face.index", 
                 metadata_path: str = "data/face_metadata.json"):
        if not hasattr(self, 'initialized'):  # 初期化済みかチェック
            self.index_path = index_path
            self.metadata_path = metadata_path
            self.index = None
            self.metadata = {}  # 辞書型に変更
            self._load_database()
            self.initialized = True
    
    def _load_database(self):
        """インデックスとメタデータをロード"""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
    
    def add_face(self, encoding: np.ndarray, name: str, metadata: Optional[Dict] = None) -> bool:
        """新しい顔を追加"""
        try:
            if self.index is None:
                self.index = faiss.IndexFlatL2(encoding.shape[0])
            
            # IDを生成（現在のメタデータの最大ID + 1）
            face_id = str(max([int(k) for k in self.metadata.keys()] + [0]) + 1)
            
            # インデックスに追加
            self.index.add(np.array([encoding]).astype('float32'))
            
            # メタデータを追加
            self.metadata[face_id] = {
                "name": name,
                "metadata": metadata or {},
                "index_position": self.index.ntotal - 1  # インデックス内の位置を保存
            }
            
            self._save_database()
            return True
        except Exception as e:
            print(f"エラー: {str(e)}")
            return False
    
    def _save_database(self):
        """インデックスとメタデータを保存"""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False)
    
    def search_similar_faces(self, query_encoding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """類似顔を検索"""
        if self.index is None:
            raise ValueError("データベースに顔データが登録されていません。先にadd_face()で顔データを追加してください。")
        
        print(f"\nデータベース内の顔データ数: {self.index.ntotal}")
        
        query = np.array([query_encoding]).astype('float32')
        distances, indices = self.index.search(query, min(top_k, self.index.ntotal))
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            
            # インデックス位置からface_idを検索
            face_id = next((k for k, v in self.metadata.items() 
                          if v["index_position"] == idx), None)
            
            if face_id:
                similarity = _calculate_similarity_percentage(dist)
                results.append({
                    **self.metadata[face_id],
                    "face_id": face_id,
                    "distance": float(dist),
                    "similarity": float(similarity)
                })
                print(f"検出結果: インデックス={idx}, 距離={dist:.2f}, 類似率={similarity:.1f}%, 名前={self.metadata[face_id]['name']}")
        
        return results

def batch_add_faces(database: FaceDatabase, image_dir: str, name_mapping: Dict[str, str]):
    """
    ディレクトリ内の画像を一括でデータベースに追加します
    
    Args:
        database (FaceDatabase): 顔データベース
        image_dir (str): 画像が保存されているディレクトリ
        name_mapping (Dict[str, str]): ファイル名から人物名へのマッピング
    """
    print("\nデータベースに追加する画像:")
    for filename in name_mapping.keys():  # name_mappingのキーのみを処理
        if filename.endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(image_dir, filename)
            name = name_mapping[filename]
            print(f"- {filename} -> {name}")
            
            # 画像から顔エンコーディングを取得
            encodings, _ = get_face_encodings(image_path)
            if encodings:
                # 最初に検出された顔のみを使用
                database.add_face(encodings[0], name)
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