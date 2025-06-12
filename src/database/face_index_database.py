import os
import json
import faiss
import numpy as np
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from src.face import face_utils
from src.utils import log_utils

# ロギングの設定
logger = log_utils.get_logger(__name__)


class FaceIndexDatabase:
    """顔インデックス管理に特化したデータベースクラス
    
    責務:
    - face_images テーブルの管理
    - face_indexes テーブルの管理
    - FAISS インデックスの管理
    - 類似検索処理
    """
    
    # データベース関連の設定
    DB_PATH = "data/face_database.db"
    INDEX_PATH = "data/face.index"
    VECTOR_DIMENSION = 128  # face_recognitionのエンコーディング次元
    
    def __init__(self, db_path: Optional[str] = None, index_path: Optional[str] = None):
        """顔インデックスデータベースの初期化
        
        Args:
            db_path (Optional[str]): データベースファイルのパス（テスト用）
            index_path (Optional[str]): FAISSインデックスファイルのパス（テスト用）
        """
        self.db_path = db_path or self.DB_PATH
        self.index_path = index_path or self.INDEX_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-style column access
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._load_index()
    
    def _create_tables(self):
        """顔インデックス関連のテーブルを作成"""
        # 顔画像情報テーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                image_hash TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
            )
        """)
        
        # FAISSインデックス情報テーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_indexes (
                index_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                index_position INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES face_images(image_id) ON DELETE CASCADE,
                UNIQUE(image_id, index_position)
            )
        """)
        
        # 検索用インデックス
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_images_person_id ON face_images(person_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_indexes_image_id ON face_indexes(image_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_face_indexes_position ON face_indexes(index_position)")
        # image_hashはUNIQUE制約があるため、インデックスは不要
        
        self.conn.commit()
    
    def _load_index(self):
        """FAISSインデックスをロードまたは新規作成"""
        try:
            logger.info("既存のインデックスを読み込み中...")
            if not os.path.exists(self.index_path):
                logger.warning(f"インデックスファイルが存在しません: {self.index_path}")
                raise FileNotFoundError("インデックスファイルが存在しません")
            
            self.index = faiss.read_index(self.index_path)
            logger.info(f"インデックスの読み込み完了。登録ベクトル数: {self.index.ntotal}")
            
            # インデックスが空の場合は再構築
            if self.index.ntotal == 0:
                logger.warning("インデックスが空です。再構築を開始します。")
                raise RuntimeError("インデックスが空です")
                
        except (RuntimeError, FileNotFoundError) as e:
            logger.info(f"インデックスの再構築を開始します... (理由: {str(e)})")
            self._rebuild_index()
    
    def _rebuild_index(self):
        """データベースからFAISSインデックスを再構築"""
        # データベースから既存のエンコーディングを取得（index_positionでソート）
        self.cursor.execute("""
            SELECT fi.image_id, fi.person_id, fi.image_path, fi.metadata, fxi.index_position
            FROM face_images fi
            JOIN face_indexes fxi ON fi.image_id = fxi.image_id
            ORDER BY fxi.index_position
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
                logger.info(f"画像のエンコーディングを取得中: {face['image_path']} (index_position: {face['index_position']})")
                encoding = face_utils.get_face_encoding(face['image_path'])
                if encoding is not None:
                    encodings.append(encoding)
                    successful_encodings += 1
                else:
                    failed_encodings += 1
                    logger.warning(f"エンコーディングの取得に失敗: {face['image_path']}")
            
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
        self._save_index()
    
    def _save_index(self):
        """FAISSインデックスをファイルに保存"""
        logger.info("インデックスを保存中...")
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        logger.info(f"インデックスの保存が完了しました。保存先: {self.index_path}")
        logger.info(f"最終的なインデックスの状態: ベクトル数 = {self.index.ntotal}")
    
    def add_face_image(self, person_id: int, image_path: str, encoding: np.ndarray, 
                      image_hash: str, metadata: Optional[Dict] = None) -> int:
        """顔画像をデータベースとインデックスに追加
        
        Args:
            person_id (int): 人物ID
            image_path (str): 画像ファイルのパス
            encoding (np.ndarray): 顔エンコーディング
            image_hash (str): 画像のハッシュ値
            metadata (Optional[Dict]): メタデータ
            
        Returns:
            int: 追加された顔画像のID
            
        Raises:
            sqlite3.IntegrityError: 同じハッシュ値の画像が既に存在する場合
            Exception: その他のエラーが発生した場合
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            try:
                # 画像情報の追加（UNIQUE制約により重複時はエラー）
                self.cursor.execute(
                    "INSERT INTO face_images (person_id, image_path, image_hash, metadata) VALUES (?, ?, ?, ?)",
                    (person_id, image_path, image_hash, json.dumps(metadata) if metadata else None)
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
                
                # インデックスを保存
                self._save_index()
                
                self.conn.commit()
                logger.info(f"顔画像を追加: image_id={image_id}, index_position={index_position}")
                return image_id
                
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed: face_images.image_hash" in str(e):
                    logger.info(f"同じ画像が既に登録されています: {image_path}")
                    # 既存の画像IDを取得
                    self.cursor.execute("SELECT image_id FROM face_images WHERE image_hash = ?", (image_hash,))
                    existing_image = self.cursor.fetchone()
                    self.conn.rollback()
                    return existing_image['image_id'] if existing_image else None
                raise
                
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"顔画像データの追加に失敗しました: {str(e)}")
    
    def search_similar_faces(self, query_encoding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """類似する顔を検索する（人物単位で集約）
        
        Args:
            query_encoding (np.ndarray): クエリの顔エンコーディング
            top_k (int): 取得する結果の数
            
        Returns:
            List[Dict[str, Any]]: 検索結果のリスト（人物単位で集約）
        """
        import time
        start_time = time.time()
        
        # FAISSで検索（より多くの候補を取得）
        faiss_start = time.time()
        distances, indices = self.index.search(np.array([query_encoding]), top_k * 3)
        faiss_time = time.time() - faiss_start
        logger.debug(f"FAISS検索時間: {faiss_time:.4f}秒")
        
        # 有効なインデックス位置のみを抽出
        valid_indices = [int(idx) for idx in indices[0] if idx >= 0]
        
        if not valid_indices:
            return []
        
        # 単一のSQLクエリですべての必要なデータを取得（N+1問題を解決）
        placeholders = ",".join("?" * len(valid_indices))
        query = f"""
            SELECT fi.index_position, fi2.image_id, fi2.person_id, p.name, 
                   fi2.image_path, fi2.metadata, p.base_image_path
            FROM face_indexes fi
            JOIN face_images fi2 ON fi.image_id = fi2.image_id
            JOIN persons p ON fi2.person_id = p.person_id
            WHERE fi.index_position IN ({placeholders})
              AND p.base_image_path IS NOT NULL
        """
        
        sql_start = time.time()
        self.cursor.execute(query, valid_indices)
        face_data_list = self.cursor.fetchall()
        sql_time = time.time() - sql_start
        logger.debug(f"SQL実行時間: {sql_time:.4f}秒")
        
        # インデックス位置をキーとした辞書を作成
        dict_start = time.time()
        face_data_dict = {row['index_position']: row for row in face_data_list}
        dict_time = time.time() - dict_start
        logger.debug(f"辞書作成時間: {dict_time:.4f}秒")
        
        # 人物ごとに最良の結果を選択
        person_results = {}
        for distance, index in zip(distances[0], indices[0]):
            if index < 0:  # 無効なインデックスをスキップ
                continue
                
            face_data = face_data_dict.get(int(index))
            if face_data:
                person_id = face_data['person_id']
                # 同一人物の場合は、最も距離が小さい（類似度が高い）結果を保持
                if person_id not in person_results or distance < person_results[person_id]['distance']:
                    person_results[person_id] = {
                        'person_id': person_id,
                        'name': face_data['name'],
                        'distance': float(distance),
                        'image_path': face_data['base_image_path'],  # ベース画像パスのみ返却
                        'metadata': json.loads(face_data['metadata']) if face_data['metadata'] else None
                    }
        
        # 距離でソートして上位top_kを返す
        sort_start = time.time()
        results = sorted(person_results.values(), key=lambda x: x['distance'])[:top_k]
        sort_time = time.time() - sort_start
        
        total_time = time.time() - start_time
        logger.debug(f"ソート時間: {sort_time:.4f}秒")
        logger.debug(f"search_similar_faces総時間: {total_time:.4f}秒")
        
        return results
    
    def get_face_image(self, image_id: int) -> Optional[Dict[str, Any]]:
        """画像IDで顔画像情報を取得
        
        Args:
            image_id (int): 画像ID
            
        Returns:
            Optional[Dict[str, Any]]: 顔画像情報、存在しない場合はNone
        """
        self.cursor.execute(
            "SELECT image_id, person_id, image_path, image_hash, created_at, metadata FROM face_images WHERE image_id = ?",
            (image_id,)
        )
        row = self.cursor.fetchone()
        
        if row:
            return {
                'image_id': row['image_id'],
                'person_id': row['person_id'],
                'image_path': row['image_path'],
                'image_hash': row['image_hash'],
                'created_at': row['created_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            }
        return None
    
    def get_faces_by_person(self, person_id: int) -> List[Dict[str, Any]]:
        """人物IDで顔画像一覧を取得
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            List[Dict[str, Any]]: 顔画像情報のリスト
        """
        self.cursor.execute("""
            SELECT fi.image_id, fi.person_id, fi.image_path, fi.image_hash, 
                   fi.created_at, fi.metadata, fxi.index_position
            FROM face_images fi
            LEFT JOIN face_indexes fxi ON fi.image_id = fxi.image_id
            WHERE fi.person_id = ?
            ORDER BY fi.image_id
        """, (person_id,))
        rows = self.cursor.fetchall()
        
        return [{
            'image_id': row['image_id'],
            'person_id': row['person_id'],
            'image_path': row['image_path'],
            'image_hash': row['image_hash'],
            'created_at': row['created_at'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else None,
            'index_position': row['index_position']
        } for row in rows]
    
    def get_all_face_images(self) -> List[Dict[str, Any]]:
        """すべての顔画像データを取得する
        
        Returns:
            List[Dict[str, Any]]: 顔画像データのリスト
        """
        self.cursor.execute("""
            SELECT fi.image_id, fi.person_id, fi.image_path, fi.image_hash,
                   fi.created_at, fi.metadata as image_metadata, fxi.index_position
            FROM face_images fi
            JOIN face_indexes fxi ON fi.image_id = fxi.image_id
            ORDER BY fi.person_id, fi.image_id
        """)
        rows = self.cursor.fetchall()
        
        return [{
            'image_id': row['image_id'],
            'person_id': row['person_id'],
            'image_path': row['image_path'],
            'image_hash': row['image_hash'],
            'created_at': row['created_at'],
            'image_metadata': json.loads(row['image_metadata']) if row['image_metadata'] else None,
            'index_position': row['index_position']
        } for row in rows]
    
    def delete_face_image(self, image_id: int) -> bool:
        """顔画像を削除（CASCADE により関連データも削除）
        
        Args:
            image_id (int): 画像ID
            
        Returns:
            bool: 削除成功の場合True
            
        Note:
            この操作後はFAISSインデックスの再構築が必要です
        """
        try:
            self.cursor.execute("DELETE FROM face_images WHERE image_id = ?", (image_id,))
            success = self.cursor.rowcount > 0
            self.conn.commit()
            
            if success:
                logger.info(f"顔画像を削除: image_id={image_id}")
                logger.warning("FAISSインデックスの再構築が必要です")
            
            return success
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"顔画像の削除に失敗: {str(e)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """インデックスの統計情報を取得
        
        Returns:
            Dict[str, Any]: インデックス統計情報
        """
        # データベースの統計
        self.cursor.execute("SELECT COUNT(*) as image_count FROM face_images")
        db_stats = self.cursor.fetchone()
        
        self.cursor.execute("SELECT COUNT(*) as index_count FROM face_indexes")
        index_stats = self.cursor.fetchone()
        
        return {
            'faiss_vector_count': self.index.ntotal,
            'db_image_count': db_stats['image_count'],
            'db_index_count': index_stats['index_count'],
            'vector_dimension': self.VECTOR_DIMENSION,
            'index_file_exists': os.path.exists(self.index_path)
        }
    
    def rebuild_index(self):
        """FAISSインデックスを手動で再構築"""
        logger.info("手動でのインデックス再構築を開始します")
        self._rebuild_index()
    
    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
            logger.debug("FaceIndexDatabase 接続を閉じました")