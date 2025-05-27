import os
import json
import faiss
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from . import db_utils
from face import face_utils
import sqlite3
import logging

# ロギングの設定
logger = logging.getLogger(__name__)

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
        # 人物情報テーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                person_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        # 顔画像情報テーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (person_id) REFERENCES persons(person_id)
            )
        """)

        # FAISSインデックス情報テーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_indexes (
                index_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                index_position INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES face_images(image_id)
            )
        """)

        # 検索用インデックス
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_images_person_id ON face_images(person_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_indexes_image_id ON face_indexes(image_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_indexes_position ON face_indexes(index_position)")

        self.conn.commit()

    def _load_index(self):
        """FAISSインデックスをロードまたは新規作成"""
        try:
            logger.info("既存のインデックスを読み込み中...")
            self.index = faiss.read_index(self.INDEX_PATH)
            # インデックスが空でないことを確認
            if self.index.ntotal == 0:
                logger.warning("インデックスが空です。再構築を開始します。")
                raise RuntimeError("インデックスが空です")
            logger.info(f"インデックスの読み込み完了。登録ベクトル数: {self.index.ntotal}")
        except (RuntimeError, FileNotFoundError):
            logger.info("インデックスの再構築を開始します...")
            # データベースから既存のエンコーディングを取得
            self.cursor.execute("""
                SELECT fi.image_id, fi.person_id, p.name, fi.image_path, fi.metadata
                FROM face_images fi
                JOIN persons p ON fi.person_id = p.person_id
            """)
            faces = self.cursor.fetchall()
            
            if not faces:
                logger.warning("データベースに登録されている画像がありません。空のインデックスを作成します。")
                self.index = faiss.IndexFlatL2(self.VECTOR_DIMENSION)
            else:
                logger.info(f"データベースから {len(faces)} 件の画像情報を取得しました。")
                # 既存のデータからインデックスを再構築
                encodings = []
                successful_encodings = 0
                failed_encodings = 0
                
                for face in faces:
                    logger.info(f"画像のエンコーディングを取得中: {face[3]}")  # image_path
                    encoding = face_utils.get_face_encoding(face[3])
                    if encoding is not None:
                        encodings.append(encoding)
                        successful_encodings += 1
                    else:
                        failed_encodings += 1
                        logger.warning(f"エンコーディングの取得に失敗: {face[3]}")
                
                logger.info(f"エンコーディングの取得結果: 成功 {successful_encodings}件, 失敗 {failed_encodings}件")
                
                if encodings:
                    # エンコーディングが存在する場合は、それらを使用してインデックスを構築
                    logger.info("インデックスの構築を開始します...")
                    encodings = np.array(encodings, dtype=np.float32)
                    self.index = faiss.IndexFlatL2(self.VECTOR_DIMENSION)
                    self.index.add(encodings)
                    logger.info(f"インデックスの構築が完了しました。登録ベクトル数: {self.index.ntotal}")
                else:
                    logger.warning("有効なエンコーディングがありません。空のインデックスを作成します。")
                    self.index = faiss.IndexFlatL2(self.VECTOR_DIMENSION)
            
            # インデックスを保存
            logger.info("インデックスを保存中...")
            os.makedirs(os.path.dirname(self.INDEX_PATH), exist_ok=True)
            faiss.write_index(self.index, self.INDEX_PATH)
            logger.info(f"インデックスの保存が完了しました。保存先: {self.INDEX_PATH}")

    def add_face(self, name: str, image_path: str, encoding: np.ndarray, metadata: Optional[Dict] = None) -> int:
        """顔データをデータベースに追加

        Args:
            name (str): 人物名
            image_path (str): 画像ファイルのパス
            encoding (np.ndarray): 顔エンコーディング
            metadata (Optional[Dict]): メタデータ

        Returns:
            int: 追加された顔画像のID
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            # 画像が既に登録済みかチェック
            self.cursor.execute("SELECT image_id FROM face_images WHERE image_path = ?", (image_path,))
            existing_image = self.cursor.fetchone()
            if existing_image:
                self.conn.rollback()
                return existing_image[0]  # 既存の画像IDを返す

            # 人物情報の取得または作成
            self.cursor.execute("SELECT person_id FROM persons WHERE name = ?", (name,))
            person = self.cursor.fetchone()
            if person:
                person_id = person[0]
            else:
                self.cursor.execute(
                    "INSERT INTO persons (name, metadata) VALUES (?, ?)",
                    (name, json.dumps(metadata) if metadata else None)
                )
                person_id = self.cursor.lastrowid

            # 画像情報の追加
            self.cursor.execute(
                "INSERT INTO face_images (person_id, image_path, metadata) VALUES (?, ?, ?)",
                (person_id, image_path, json.dumps(metadata) if metadata else None)
            )
            image_id = self.cursor.lastrowid

            # FAISSインデックスに追加（個別のインデックスとして）
            self.index.add(np.array([encoding], dtype=np.float32))
            index_position = self.index.ntotal - 1

            # インデックス情報の追加
            self.cursor.execute(
                "INSERT INTO face_indexes (image_id, index_position) VALUES (?, ?)",
                (image_id, index_position)
            )

            self.conn.commit()
            return image_id

        except Exception as e:
            self.conn.rollback()
            raise Exception(f"顔データの追加に失敗しました: {str(e)}")

    def search_similar_faces(self, query_encoding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """類似する顔を検索する（人物単位で集約）

        Args:
            query_encoding (np.ndarray): クエリの顔エンコーディング
            top_k (int): 取得する結果の数

        Returns:
            List[Dict[str, Any]]: 検索結果のリスト（人物単位で集約）
        """
        # FAISSで検索（より多くの候補を取得）
        distances, indices = self.index.search(np.array([query_encoding]), top_k * 3)

        # 人物ごとに最良の結果を選択
        person_results = {}
        for distance, index in zip(distances[0], indices[0]):
            # インデックス情報から画像情報を取得
            self.cursor.execute("""
                SELECT fi2.image_id, fi2.person_id, p.name, fi2.image_path, fi2.metadata
                FROM face_indexes fi
                JOIN face_images fi2 ON fi.image_id = fi2.image_id
                JOIN persons p ON fi2.person_id = p.person_id
                WHERE fi.index_position = ?
            """, (int(index),))
            face_data = self.cursor.fetchone()

            if face_data:
                person_id = face_data[1]
                # 同一人物の場合は、最も距離が小さい（類似度が高い）結果を保持
                if person_id not in person_results or distance < person_results[person_id]['distance']:
                    person_results[person_id] = {
                        'person_id': person_id,
                        'name': face_data[2],
                        'distance': float(distance),
                        'image_path': face_data[3],
                        'metadata': json.loads(face_data[4]) if face_data[4] else None
                    }

        # 距離でソートして上位top_kを返す
        return sorted(person_results.values(), key=lambda x: x['distance'])[:top_k]

    def get_all_faces(self) -> List[Dict[str, Any]]:
        """すべての顔データを取得する

        Returns:
            List[Dict[str, Any]]: 顔データのリスト
        """
        self.cursor.execute("""
            SELECT p.person_id, p.name, p.metadata as person_metadata,
                   fi.image_id, fi.image_path, fi.metadata as image_metadata,
                   fxi.index_position
            FROM persons p
            JOIN face_images fi ON p.person_id = fi.person_id
            JOIN face_indexes fxi ON fi.image_id = fxi.image_id
            ORDER BY p.person_id, fi.image_id
        """)
        rows = self.cursor.fetchall()
        return [{
            'person_id': row[0],
            'name': row[1],
            'person_metadata': json.loads(row[2]) if row[2] else None,
            'image_id': row[3],
            'image_path': row[4],
            'image_metadata': json.loads(row[5]) if row[5] else None,
            'index_position': row[6]
        } for row in rows]

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close() 