import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from . import db_utils
from src.face import face_utils

class FaceDatabase:
    def __init__(self, db_path: str = "data/face_database.db", index_path: str = "data/face.index"):
        """
        顔データベースを初期化する
        
        Args:
            db_path (str): データベースファイルのパス
            index_path (str): FAISSインデックスファイルのパス
        """
        self.db_path = db_path
        self.index_path = index_path
        
        # データベース接続を作成
        self.conn = db_utils.create_connection(db_path)
        db_utils.init_database(self.conn)
        
        # FAISSインデックスを初期化
        self.dimension = 128  # face_recognitionのエンコーディング次元
        self.index = self._load_or_create_index()
    
    def _load_or_create_index(self) -> faiss.IndexFlatL2:
        """
        FAISSインデックスを読み込むか新規作成する
        
        Returns:
            faiss.IndexFlatL2: FAISSインデックス
        """
        if os.path.exists(self.index_path):
            print("既存のインデックスを読み込みます")
            return faiss.read_index(self.index_path)
        else:
            print("新しいインデックスを作成します")
            return faiss.IndexFlatL2(self.dimension)
    
    def add_face(self, name: str, image_path: str, metadata: Dict[str, Any] = None) -> bool:
        """
        顔データを追加する
        
        Args:
            name (str): 名前
            image_path (str): 画像ファイルのパス
            metadata (Dict[str, Any], optional): メタデータ
            
        Returns:
            bool: 追加に成功したかどうか
        """
        # 既に登録されているかチェック
        if db_utils.get_face_by_name(self.conn, name):
            print(f"既に登録されています: {name}")
            return False
        
        # 顔のエンコーディングを取得
        encoding = face_utils.get_face_encoding(image_path)
        if encoding is None:
            return False
        
        # FAISSインデックスに追加
        index_position = self.index.ntotal
        self.index.add(np.array([encoding]))
        
        # データベースに追加
        metadata_str = json.dumps(metadata) if metadata else None
        db_utils.insert_face(self.conn, name, image_path, index_position, metadata_str)
        
        # インデックスを保存
        faiss.write_index(self.index, self.index_path)
        
        print(f"顔データを追加しました: {name}")
        return True
    
    def search_similar_faces(self, query_encoding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        類似する顔を検索する
        
        Args:
            query_encoding (np.ndarray): クエリの顔エンコーディング
            top_k (int): 取得する結果の数
            
        Returns:
            List[Dict[str, Any]]: 検索結果のリスト
        """
        print(f"インデックス内の顔データ数: {self.index.ntotal}")
        
        # FAISSで検索
        distances, indices = self.index.search(np.array([query_encoding]), top_k)
        print(f"検索結果 - インデックス: {indices[0]}, 距離: {distances[0]}")
        
        # データベースから全ての顔データを取得
        all_faces = db_utils.get_all_faces(self.conn)
        face_dict = {face['index_position']: face for face in all_faces}
        
        results = []
        for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
            # インデックスに対応する顔データを取得
            face_data = face_dict.get(index)
            if face_data:
                print(f"顔データが見つかりました - インデックス: {index}, 名前: {face_data['name']}")
                results.append({
                    'name': face_data['name'],
                    'distance': float(distance),
                    'metadata': json.loads(face_data['metadata']) if face_data['metadata'] else None
                })
            else:
                print(f"顔データが見つかりませんでした - インデックス: {index}")
        
        return results
    
    def get_all_faces(self) -> List[Dict[str, Any]]:
        """
        すべての顔データを取得する
        
        Returns:
            List[Dict[str, Any]]: 顔データのリスト
        """
        return db_utils.get_all_faces(self.conn)
    
    def close(self):
        """
        データベース接続を閉じる
        """
        self.conn.close() 