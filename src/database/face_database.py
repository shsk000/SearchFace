import numpy as np
from typing import List, Dict, Any, Optional
from .person_database import PersonDatabase
from .face_index_database import FaceIndexDatabase
from src.utils import log_utils

# ロギングの設定
logger = log_utils.get_logger(__name__)

class FaceDatabase:
    """顔認識データベースのファサードクラス
    
    PersonDatabase と FaceIndexDatabase を統合して、
    既存のAPIとの互換性を保ちながら、責務を分離したアーキテクチャを提供する。
    """
    
    # データベース関連の設定（後方互換性のため保持）
    DB_PATH = "data/face_database.db"
    INDEX_PATH = "data/face.index"
    VECTOR_DIMENSION = 128  # face_recognitionのエンコーディング次元

    def __init__(self, db_path: Optional[str] = None, index_path: Optional[str] = None):
        """顔データベースの初期化（ファサードパターン）
        
        Args:
            db_path (Optional[str]): データベースファイルのパス（テスト用）
            index_path (Optional[str]): FAISSインデックスファイルのパス（テスト用）
        """
        # 内部的に分離されたデータベースクラスを使用
        self.person_db = PersonDatabase(db_path or self.DB_PATH)
        self.face_index_db = FaceIndexDatabase(db_path or self.DB_PATH, index_path or self.INDEX_PATH)
        
        # 後方互換性のため、プロパティを追加
        self.conn = self.person_db.conn
        self.cursor = self.person_db.cursor
        self.index = self.face_index_db.index

    def _create_tables(self):
        """データベースのテーブルを作成（後方互換性のため）
        
        Note: 実際のテーブル作成は PersonDatabase と FaceIndexDatabase で行われる
        """
        # 分離されたクラスで既に作成済み
        pass

    def _load_index(self):
        """FAISSインデックスをロードまたは新規作成（後方互換性のため）
        
        Note: 実際のインデックス処理は FaceIndexDatabase で行われる
        """
        # 分離されたクラスで既に処理済み
        pass

    def add_face(self, name: str, image_path: str, encoding: np.ndarray, image_hash: str, metadata: Optional[Dict] = None) -> int:
        """顔データをデータベースに追加（ファサードメソッド）

        Args:
            name (str): 人物名
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
            # 人物情報の取得または作成
            person_id = self.person_db.get_or_create_person(name, metadata)
            
            # 顔画像データの追加
            image_id = self.face_index_db.add_face_image(
                person_id=person_id,
                image_path=image_path,
                encoding=encoding,
                image_hash=image_hash,
                metadata=metadata
            )
            
            # 後方互換性のため、インデックスを更新
            self.index = self.face_index_db.index
            
            return image_id
            
        except Exception as e:
            raise Exception(f"顔データの追加に失敗しました: {str(e)}")

    def search_similar_faces(self, query_encoding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """類似する顔を検索する（人物単位で集約）（ファサードメソッド）

        Args:
            query_encoding (np.ndarray): クエリの顔エンコーディング
            top_k (int): 取得する結果の数

        Returns:
            List[Dict[str, Any]]: 検索結果のリスト（人物単位で集約）
        """
        return self.face_index_db.search_similar_faces(query_encoding, top_k)

    def get_all_faces(self) -> List[Dict[str, Any]]:
        """すべての顔データを取得する（ファサードメソッド）

        Returns:
            List[Dict[str, Any]]: 顔データのリスト
        """
        # 顔画像データを取得
        face_images = self.face_index_db.get_all_face_images()
        
        # 人物情報を取得して結合
        person_ids = list(set(face['person_id'] for face in face_images))
        person_names = self.person_db.get_person_names(person_ids)
        
        # データを結合
        result = []
        for face in face_images:
            result.append({
                'person_id': face['person_id'],
                'name': person_names.get(face['person_id'], 'Unknown'),
                'person_metadata': None,  # 後方互換性のため
                'image_id': face['image_id'],
                'image_path': face['image_path'],
                'image_metadata': face['image_metadata'],
                'index_position': face['index_position']
            })
        
        return result

    def get_person_names(self, person_ids: List[int]) -> Dict[int, str]:
        """複数の人物IDから名前を取得する（ファサードメソッド）
        
        Args:
            person_ids: 人物IDのリスト
            
        Returns:
            Dict[int, str]: person_id -> name のマッピング
        """
        return self.person_db.get_person_names(person_ids)

    def get_person_detail(self, person_id: int) -> Optional[Dict[str, Any]]:
        """特定の人物の詳細情報を取得する（ファサードメソッド）
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            Optional[Dict[str, Any]]: 人物詳細情報、存在しない場合はNone
        """
        return self.person_db.get_person_detail(person_id)

    def close(self):
        """データベース接続を閉じる（ファサードメソッド）"""
        if hasattr(self, 'person_db') and self.person_db:
            self.person_db.close()
        if hasattr(self, 'face_index_db') and self.face_index_db:
            self.face_index_db.close()
