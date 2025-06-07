#!/usr/bin/env python3
"""
Person Profilesテーブルにデータを登録するスクリプト

既存のpersonsテーブルのデータを基に、ベース画像が存在する人物について
person_profilesテーブルにデータを登録する。
"""

import os
import sqlite3
from typing import List, Tuple
from utils import log_utils

# ロギングの設定
logger = log_utils.get_logger(__name__)

class PersonProfilePopulator:
    def __init__(self, db_path: str = "data/face_database.db"):
        """初期化"""
        self.db_path = db_path
        self.base_image_dir = "data/images/base"
        
    def create_person_profiles_table(self):
        """person_profilesテーブルを作成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # person_profilesテーブルを作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS person_profiles (
                    profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_id INTEGER NOT NULL UNIQUE,
                    base_image_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
                )
            """)
            
            # インデックスも作成
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_profiles_person_id ON person_profiles(person_id)")
            
            conn.commit()
            logger.info("person_profilesテーブルの作成が完了しました")
            
        except Exception as e:
            logger.error(f"person_profilesテーブルの作成に失敗: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_existing_persons(self) -> List[Tuple[int, str]]:
        """既存のpersonsデータを取得"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT person_id, name FROM persons ORDER BY person_id")
            persons = cursor.fetchall()
            logger.info(f"既存のpersonsデータを{len(persons)}件取得しました")
            return persons
        except Exception as e:
            logger.error(f"personsデータの取得に失敗: {str(e)}")
            raise
        finally:
            conn.close()
    
    def check_base_image_exists(self, person_name: str) -> str:
        """ベース画像の存在確認とパス取得"""
        # base.jpg形式のパスを確認
        base_jpg_path = os.path.join(self.base_image_dir, person_name, "base.jpg")
        if os.path.exists(base_jpg_path):
            return base_jpg_path
        
        # .jpgファイルがディレクトリ内に存在するか確認
        person_dir = os.path.join(self.base_image_dir, person_name)
        if os.path.exists(person_dir):
            jpg_files = [f for f in os.listdir(person_dir) if f.lower().endswith('.jpg')]
            if jpg_files:
                return os.path.join(person_dir, jpg_files[0])
        
        return None
    
    def populate_person_profiles(self):
        """person_profilesテーブルにデータを登録"""
        # まず、person_profilesテーブルを作成
        self.create_person_profiles_table()
        
        # 既存のpersonsデータを取得
        persons = self.get_existing_persons()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        successful_count = 0
        skipped_count = 0
        failed_count = 0
        
        try:
            for person_id, person_name in persons:
                # ベース画像の存在確認
                base_image_path = self.check_base_image_exists(person_name)
                
                if base_image_path:
                    try:
                        # person_profilesテーブルに登録
                        cursor.execute("""
                            INSERT OR IGNORE INTO person_profiles (person_id, base_image_path)
                            VALUES (?, ?)
                        """, (person_id, base_image_path))
                        
                        if cursor.rowcount > 0:
                            logger.info(f"登録完了: {person_name} (ID: {person_id}) -> {base_image_path}")
                            successful_count += 1
                        else:
                            logger.info(f"スキップ（既存）: {person_name} (ID: {person_id})")
                            skipped_count += 1
                            
                    except Exception as e:
                        logger.error(f"登録失敗: {person_name} (ID: {person_id}) - {str(e)}")
                        failed_count += 1
                else:
                    logger.warning(f"ベース画像なし: {person_name} (ID: {person_id})")
                    failed_count += 1
            
            conn.commit()
            
            # 結果を表示
            logger.info("=" * 50)
            logger.info("person_profiles登録結果")
            logger.info("=" * 50)
            logger.info(f"登録成功: {successful_count}件")
            logger.info(f"スキップ: {skipped_count}件")
            logger.info(f"失敗: {failed_count}件")
            logger.info(f"合計: {len(persons)}件")
            logger.info("=" * 50)
            
        except Exception as e:
            conn.rollback()
            logger.error(f"person_profilesの登録中にエラーが発生: {str(e)}")
            raise
        finally:
            conn.close()
    
    def verify_registration(self):
        """登録結果の確認"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # person_profilesテーブルの件数確認
            cursor.execute("SELECT COUNT(*) FROM person_profiles")
            profile_count = cursor.fetchone()[0]
            
            # personsテーブルの件数確認
            cursor.execute("SELECT COUNT(*) FROM persons")
            person_count = cursor.fetchone()[0]
            
            logger.info(f"登録確認: person_profiles {profile_count}件 / persons {person_count}件")
            
            # 登録されたprofilesの一部を表示
            cursor.execute("""
                SELECT pp.profile_id, pp.person_id, p.name, pp.base_image_path
                FROM person_profiles pp
                JOIN persons p ON pp.person_id = p.person_id
                ORDER BY pp.person_id
                LIMIT 10
            """)
            
            profiles = cursor.fetchall()
            logger.info("登録されたprofilesの例:")
            for profile in profiles:
                logger.info(f"  ID: {profile[0]}, Person: {profile[2]} ({profile[1]}), Image: {profile[3]}")
                
        except Exception as e:
            logger.error(f"登録確認中にエラーが発生: {str(e)}")
        finally:
            conn.close()

def main():
    """メイン処理"""
    logger.info("Person Profiles登録スクリプトを開始します")
    
    try:
        populator = PersonProfilePopulator()
        populator.populate_person_profiles()
        populator.verify_registration()
        
        logger.info("Person Profiles登録スクリプトが正常に完了しました")
        
    except Exception as e:
        logger.error(f"スクリプトの実行中にエラーが発生: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())