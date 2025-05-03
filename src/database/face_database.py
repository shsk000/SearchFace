import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from . import db_utils
from face import face_utils
import sqlite3

class FaceDatabase:
    # データベース関連の設定
    DB_PATH = "data/face_database.db"
    INDEX_PATH = "data/face.index"
    VECTOR_DIMENSION = 128  # face_recognitionのエンコーディング次元

    def __init__(self):
        """顔データベースの初期化"""
        self.conn = sqlite3.connect(self.DB_PATH)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._load_index()

    def _create_tables(self):
        """データベースのテーブルを作成"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS faces (
                face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                image_path TEXT NOT NULL,
                index_position INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        self.conn.commit()

    def _load_index(self):
        """FAISSインデックスをロードまたは新規作成"""
        try:
            self.index = faiss.read_index(self.INDEX_PATH)
        except (RuntimeError, FileNotFoundError):
            # インデックスが存在しない場合は新規作成
            self.index = faiss.IndexFlatL2(self.VECTOR_DIMENSION)
            faiss.write_index(self.index, self.INDEX_PATH)

    def add_face(self, name: str, image_path: str, encoding: np.ndarray, metadata: Optional[Dict] = None) -> int:
        """顔データをデータベースに追加

        Args:
            name (str): 人物名
            image_path (str): 画像ファイルのパス
            encoding (np.ndarray): 顔エンコーディング
            metadata (Optional[Dict]): メタデータ

        Returns:
            int: 追加された顔のID（既存の場合は既存のID）
        """
        try:
            # 既に登録されているかチェック
            self.cursor.execute("SELECT face_id FROM faces WHERE name = ?", (name,))
            existing_face = self.cursor.fetchone()
            if existing_face:
                print(f"既に登録されています: {name}")
                return existing_face[0]

            # トランザクション開始
            self.conn.execute("BEGIN TRANSACTION")
            
            # データベースに追加
            self.cursor.execute(
                "INSERT INTO faces (name, image_path, index_position, metadata) VALUES (?, ?, ?, ?)",
                (name, image_path, self.index.ntotal, json.dumps(metadata) if metadata else None)
            )
            face_id = self.cursor.lastrowid
            
            # FAISSインデックスに追加
            self.index.add(np.array([encoding], dtype=np.float32))
            
            # インデックスを保存
            faiss.write_index(self.index, self.INDEX_PATH)
            
            # トランザクションコミット
            self.conn.commit()
            
            return face_id
            
        except Exception as e:
            # エラー発生時はロールバック
            self.conn.rollback()
            raise Exception(f"顔データの追加に失敗しました: {str(e)}")
    
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