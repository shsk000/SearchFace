import json
import sqlite3
from typing import List, Dict, Any, Optional
from src.utils import log_utils

# ロギングの設定
logger = log_utils.get_logger(__name__)


class PersonDatabase:
    """人物（女優）情報管理に特化したデータベースクラス
    
    責務:
    - persons テーブルの管理
    - person_profiles テーブルの管理
    - 人物情報の CRUD 操作
    """
    
    # データベース関連の設定
    DB_PATH = "data/face_database.db"
    
    def __init__(self, db_path: Optional[str] = None):
        """人物データベースの初期化
        
        Args:
            db_path (Optional[str]): データベースファイルのパス（テスト用）
        """
        self.db_path = db_path or self.DB_PATH
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable dict-style column access
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """人物関連のテーブルを作成"""
        # 人物情報テーブル
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                person_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dmm_actress_id INTEGER UNIQUE,
                base_image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # 人物プロフィールテーブル（検索用に構造化）
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS person_profiles (
                profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL UNIQUE,
                
                -- 基本情報
                ruby TEXT,
                birthday DATE,
                birth_year INTEGER,
                blood_type TEXT,
                hobby TEXT,
                prefectures TEXT,
                
                -- 身体情報
                height INTEGER,
                bust INTEGER,
                waist INTEGER,
                hip INTEGER,
                cup TEXT,
                
                -- 画像URL
                image_small_url TEXT,
                image_large_url TEXT,
                
                -- DMM情報
                dmm_list_url_digital TEXT,
                dmm_list_url_monthly_premium TEXT,
                dmm_list_url_mono TEXT,
                
                -- システム情報
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- 追加メタデータ（柔軟性のため残す）
                metadata TEXT,
                
                FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
            )
        """)
        
        # 検索用インデックス（最小限）
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_persons_name ON persons(name)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_persons_dmm_actress_id ON persons(dmm_actress_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_profiles_person_id ON person_profiles(person_id)")
        
        # プロフィール検索用インデックス（身体情報中心）
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_ruby ON person_profiles(ruby)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_height ON person_profiles(height)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_bust ON person_profiles(bust)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_cup ON person_profiles(cup)")
        
        # 複合インデックス（身体情報での絞り込み用）
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_measurements ON person_profiles(height, cup, bust)")
        
        self.conn.commit()
    
    def create_person(self, name: str, metadata: Optional[Dict] = None) -> int:
        """新しい人物を作成
        
        Args:
            name (str): 人物名
            metadata (Optional[Dict]): メタデータ
            
        Returns:
            int: 作成された人物のID
        """
        try:
            self.cursor.execute(
                "INSERT INTO persons (name, metadata) VALUES (?, ?)",
                (name, json.dumps(metadata) if metadata else None)
            )
            person_id = self.cursor.lastrowid
            self.conn.commit()
            
            logger.info(f"新しい人物を作成: {name} (ID: {person_id})")
            return person_id
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"人物の作成に失敗: {str(e)}")
    
    def get_person_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """名前で人物を検索
        
        Args:
            name (str): 人物名
            
        Returns:
            Optional[Dict[str, Any]]: 人物情報、存在しない場合はNone
        """
        self.cursor.execute(
            "SELECT person_id, name, dmm_actress_id, base_image_path, created_at, metadata FROM persons WHERE name = ?",
            (name,)
        )
        row = self.cursor.fetchone()
        
        if row:
            return {
                'person_id': row['person_id'],
                'name': row['name'],
                'dmm_actress_id': row['dmm_actress_id'],
                'base_image_path': row['base_image_path'],
                'created_at': row['created_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            }
        return None
    
    def get_person_by_id(self, person_id: int) -> Optional[Dict[str, Any]]:
        """IDで人物を検索
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            Optional[Dict[str, Any]]: 人物情報、存在しない場合はNone
        """
        self.cursor.execute(
            "SELECT person_id, name, dmm_actress_id, base_image_path, created_at, metadata FROM persons WHERE person_id = ?",
            (person_id,)
        )
        row = self.cursor.fetchone()
        
        if row:
            return {
                'person_id': row['person_id'],
                'name': row['name'],
                'dmm_actress_id': row['dmm_actress_id'],
                'base_image_path': row['base_image_path'],
                'created_at': row['created_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            }
        return None
    
    def get_person_names(self, person_ids: List[int]) -> Dict[int, str]:
        """複数の人物IDから名前を取得
        
        Args:
            person_ids: 人物IDのリスト
            
        Returns:
            Dict[int, str]: person_id -> name のマッピング
        """
        if not person_ids:
            return {}
            
        placeholders = ",".join("?" * len(person_ids))
        query = f"SELECT person_id, name FROM persons WHERE person_id IN ({placeholders})"
        
        self.cursor.execute(query, person_ids)
        rows = self.cursor.fetchall()
        
        return {row['person_id']: row['name'] for row in rows}
    
    def create_person_profile(self, person_id: int, metadata: Optional[Dict] = None) -> int:
        """人物プロフィールを作成
        
        Args:
            person_id (int): 人物ID
            metadata (Optional[Dict]): メタデータ
            
        Returns:
            int: 作成されたプロフィールID
        """
        try:
            self.cursor.execute(
                "INSERT INTO person_profiles (person_id, metadata) VALUES (?, ?)",
                (person_id, json.dumps(metadata) if metadata else None)
            )
            profile_id = self.cursor.lastrowid
            self.conn.commit()
            
            logger.info(f"人物プロフィールを作成: person_id={person_id}, profile_id={profile_id}")
            return profile_id
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"人物プロフィールの作成に失敗: {str(e)}")
    
    def get_person_profile(self, person_id: int) -> Optional[Dict[str, Any]]:
        """人物プロフィールを取得
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            Optional[Dict[str, Any]]: プロフィール情報、存在しない場合はNone
        """
        self.cursor.execute(
            "SELECT profile_id, person_id, created_at, metadata FROM person_profiles WHERE person_id = ?",
            (person_id,)
        )
        row = self.cursor.fetchone()
        
        if row:
            return {
                'profile_id': row['profile_id'],
                'person_id': row['person_id'],
                'created_at': row['created_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else None
            }
        return None
    
    def get_person_detail(self, person_id: int) -> Optional[Dict[str, Any]]:
        """人物の詳細情報を取得（person + profile の結合）
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            Optional[Dict[str, Any]]: 人物詳細情報、存在しない場合はNone
        """
        self.cursor.execute("""
            SELECT p.person_id, p.name, p.base_image_path, p.dmm_actress_id
            FROM persons p
            WHERE p.person_id = ?
        """, (person_id,))
        
        row = self.cursor.fetchone()
        if row:
            return {
                'person_id': row['person_id'],
                'name': row['name'],
                'image_path': row['base_image_path'],
                'dmm_actress_id': row['dmm_actress_id']
            }
        return None
    
    def get_or_create_person(self, name: str, metadata: Optional[Dict] = None) -> int:
        """人物を取得または作成（既存の場合は取得、新規の場合は作成）
        
        Args:
            name (str): 人物名
            metadata (Optional[Dict]): メタデータ（新規作成時のみ使用）
            
        Returns:
            int: 人物ID
        """
        # 既存の人物を検索
        person = self.get_person_by_name(name)
        if person:
            return person['person_id']
        
        # 新規作成
        person_id = self.create_person(name, metadata)
        
        # プロフィールも作成
        self.create_person_profile(person_id)
        
        return person_id
    
    def update_person(self, person_id: int, name: Optional[str] = None, metadata: Optional[Dict] = None) -> bool:
        """人物情報を更新
        
        Args:
            person_id (int): 人物ID
            name (Optional[str]): 新しい名前
            metadata (Optional[Dict]): 新しいメタデータ
            
        Returns:
            bool: 更新成功の場合True
        """
        try:
            updates = []
            params = []
            
            if name is not None:
                updates.append("name = ?")
                params.append(name)
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata))
            
            if not updates:
                return True  # 更新項目がない場合は成功扱い
            
            params.append(person_id)
            query = f"UPDATE persons SET {', '.join(updates)} WHERE person_id = ?"
            
            self.cursor.execute(query, params)
            success = self.cursor.rowcount > 0
            self.conn.commit()
            
            if success:
                logger.info(f"人物情報を更新: person_id={person_id}")
            
            return success
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"人物情報の更新に失敗: {str(e)}")
    
    def delete_person(self, person_id: int) -> bool:
        """人物を削除（CASCADE により関連データも削除）
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            bool: 削除成功の場合True
        """
        try:
            self.cursor.execute("DELETE FROM persons WHERE person_id = ?", (person_id,))
            success = self.cursor.rowcount > 0
            self.conn.commit()
            
            if success:
                logger.info(f"人物を削除: person_id={person_id}")
            
            return success
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"人物の削除に失敗: {str(e)}")
    
    def update_person_profile(self, person_id: int, metadata: Dict[str, Any]) -> bool:
        """人物プロフィールのメタデータを更新
        
        Args:
            person_id (int): 人物ID
            metadata (Dict[str, Any]): 新しいメタデータ
            
        Returns:
            bool: 更新成功の場合True
        """
        try:
            self.cursor.execute(
                "UPDATE person_profiles SET metadata = ? WHERE person_id = ?",
                (json.dumps(metadata), person_id)
            )
            success = self.cursor.rowcount > 0
            self.conn.commit()
            
            if success:
                logger.info(f"人物プロフィールを更新: person_id={person_id}")
            
            return success
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"人物プロフィールの更新に失敗: {str(e)}")
    
    def upsert_person_profile(self, person_id: int, profile_data: Dict[str, Any]) -> int:
        """人物プロフィールを作成または更新（個別カラム対応）
        
        Args:
            person_id (int): 人物ID
            profile_data (Dict[str, Any]): プロフィールデータ（個別カラム用）
            
        Returns:
            int: プロフィールID
        """
        try:
            # 既存プロフィールを確認
            existing_profile = self.get_person_profile(person_id)
            
            if existing_profile:
                # 既存プロフィールを更新
                self._update_person_profile_columns(person_id, profile_data)
                return existing_profile['profile_id']
            else:
                # 新規作成
                return self._create_person_profile_with_columns(person_id, profile_data)
                
        except Exception as e:
            raise Exception(f"人物プロフィールのupsertに失敗: {str(e)}")
    
    def _create_person_profile_with_columns(self, person_id: int, profile_data: Dict[str, Any]) -> int:
        """個別カラムでプロフィールを新規作成
        
        Args:
            person_id (int): 人物ID
            profile_data (Dict[str, Any]): プロフィールデータ
            
        Returns:
            int: 作成されたプロフィールID
        """
        try:
            columns = [
                'person_id', 'ruby', 'birthday', 'blood_type', 'hobby', 'prefectures',
                'height', 'bust', 'waist', 'hip', 'cup',
                'image_small_url', 'image_large_url',
                'dmm_list_url_digital', 'dmm_list_url_monthly_premium', 'dmm_list_url_mono',
                'metadata'
            ]
            
            placeholders = ', '.join(['?'] * len(columns))
            column_names = ', '.join(columns)
            
            values = [person_id]
            for col in columns[1:]:  # person_id以外
                values.append(profile_data.get(col))
            
            self.cursor.execute(
                f"INSERT INTO person_profiles ({column_names}) VALUES ({placeholders})",
                values
            )
            
            profile_id = self.cursor.lastrowid
            self.conn.commit()
            
            logger.info(f"個別カラムで人物プロフィールを作成: person_id={person_id}, profile_id={profile_id}")
            return profile_id
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"個別カラムでのプロフィール作成に失敗: {str(e)}")
    
    def _update_person_profile_columns(self, person_id: int, profile_data: Dict[str, Any]) -> bool:
        """個別カラムでプロフィールを更新
        
        Args:
            person_id (int): 人物ID
            profile_data (Dict[str, Any]): プロフィールデータ
            
        Returns:
            bool: 更新成功の場合True
        """
        try:
            columns = [
                'ruby', 'birthday', 'blood_type', 'hobby', 'prefectures',
                'height', 'bust', 'waist', 'hip', 'cup',
                'image_small_url', 'image_large_url',
                'dmm_list_url_digital', 'dmm_list_url_monthly_premium', 'dmm_list_url_mono',
                'metadata'
            ]
            
            set_clauses = []
            values = []
            
            for col in columns:
                if col in profile_data:
                    set_clauses.append(f"{col} = ?")
                    values.append(profile_data[col])
            
            if not set_clauses:
                return True  # 更新項目がない場合は成功扱い
            
            # last_updatedも更新
            set_clauses.append("last_updated = CURRENT_TIMESTAMP")
            values.append(person_id)
            
            query = f"UPDATE person_profiles SET {', '.join(set_clauses)} WHERE person_id = ?"
            
            self.cursor.execute(query, values)
            success = self.cursor.rowcount > 0
            self.conn.commit()
            
            if success:
                logger.info(f"個別カラムで人物プロフィールを更新: person_id={person_id}")
            
            return success
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"個別カラムでのプロフィール更新に失敗: {str(e)}")
    
    def _deep_merge_dict(self, base_dict: Dict, update_dict: Dict) -> Dict:
        """辞書の深いマージを実行
        
        Args:
            base_dict (Dict): ベース辞書
            update_dict (Dict): 更新辞書
            
        Returns:
            Dict: マージされた辞書
        """
        result = base_dict.copy()
        
        for key, value in update_dict.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_dict(result[key], value)
            else:
                result[key] = value
                
        return result

    def get_all_persons(self) -> List[Dict[str, Any]]:
        """すべての人物情報を取得
        
        Returns:
            List[Dict[str, Any]]: 人物情報のリスト
        """
        self.cursor.execute("""
            SELECT person_id, name, dmm_actress_id, base_image_path, created_at, metadata
            FROM persons
            ORDER BY person_id
        """)
        rows = self.cursor.fetchall()
        
        return [{
            'person_id': row['person_id'],
            'name': row['name'],
            'dmm_actress_id': row['dmm_actress_id'],
            'base_image_path': row['base_image_path'],
            'created_at': row['created_at'],
            'metadata': json.loads(row['metadata']) if row['metadata'] else None
        } for row in rows]
    
    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()
            logger.debug("PersonDatabase 接続を閉じました")