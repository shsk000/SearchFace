import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils import log_utils
import libsql_experimental as libsql

# ロギングの設定
logger = log_utils.get_logger(__name__)

class RankingDatabase:
    """ランキング集計を管理するデータベースクラス"""

    def __init__(self):
        """ランキングデータベースの初期化

        Args:
            db_url (str): TursoデータベースURL（環境変数から取得）
        """
        self.db_url = os.getenv('TURSO_DATABASE_URL')
        self.db_token = os.getenv('TURSO_AUTH_TOKEN')

        if not self.db_url:
            raise ValueError("TURSO_DATABASE_URL環境変数が設定されていません")

        # Embedded Replicas方式で接続
        self.conn = libsql.connect("ranking.db", sync_url=self.db_url, auth_token=self.db_token)
        self.conn.sync()  # 初回同期

    def update_ranking(self, person_id: int) -> None:
        """ランキングテーブルを更新（1位結果用）

        Args:
            person_id (int): 人物ID
        """
        try:
            # 既存レコードをチェック
            result = self.conn.execute(
                "SELECT win_count FROM person_ranking WHERE person_id = ?",
                (person_id,)
            )

            rows = result.fetchall()
            if rows:
                # 既存レコードを更新
                win_count = rows[0][0] + 1

                self.conn.execute("""
                    UPDATE person_ranking
                    SET win_count = ?,
                        last_win_timestamp = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE person_id = ?
                """, (win_count, person_id))

                self.conn.commit()
                self.conn.sync()
            else:
                # 新規レコードを挿入
                self.conn.execute("""
                    INSERT INTO person_ranking
                    (person_id, win_count, last_win_timestamp)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                """, (person_id,))

            self.conn.commit()
            self.conn.sync()

            logger.info(f"ランキングを更新しました: person_id={person_id}")

        except Exception as e:
            logger.error(f"ランキングの更新に失敗: {str(e)}")
            raise

    def get_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """ランキングを取得

        Args:
            limit (int): 取得する件数

        Returns:
            List[Dict[str, Any]]: ランキング結果
        """
        import sqlite3
        
        # Tursoからランキングデータを取得
        result = self.conn.execute("""
            SELECT person_id, win_count, last_win_timestamp
            FROM person_ranking
            ORDER BY win_count DESC
            LIMIT ?
        """, (limit,))

        ranking_data = result.fetchall()
        
        # ローカルSQLiteから人物情報を取得
        local_conn = sqlite3.connect("data/face_database.db")
        local_cursor = local_conn.cursor()
        
        results = []
        for idx, row in enumerate(ranking_data):
            person_id = row[0]
            
            # 人物名とベース画像パスを取得
            local_cursor.execute("""
                SELECT p.name, p.base_image_path
                FROM persons p
                WHERE p.person_id = ?
            """, (person_id,))
            
            person_data = local_cursor.fetchone()
            
            if person_data:
                results.append({
                    'rank': idx + 1,
                    'person_id': person_id,
                    'name': person_data[0],
                    'win_count': row[1],
                    'last_win_date': row[2],
                    'image_path': person_data[1]  # ベース画像パス
                })
        
        local_conn.close()
        return results

    def get_ranking_stats(self) -> Dict[str, Any]:
        """ランキング統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        import sqlite3
        
        # 総人物数（ランキングに登録されている）
        result = self.conn.execute("SELECT COUNT(*) FROM person_ranking")
        total_persons = result.fetchall()[0][0]

        # 総勝利数
        result = self.conn.execute("SELECT SUM(win_count) FROM person_ranking")
        total_wins = result.fetchall()[0][0] or 0

        # トップ人物
        result = self.conn.execute("""
            SELECT person_id, win_count
            FROM person_ranking
            ORDER BY win_count DESC
            LIMIT 1
        """)
        rows = result.fetchall()
        
        top_person = None
        if rows:
            # ローカルSQLiteから人物名を取得
            local_conn = sqlite3.connect("data/face_database.db")
            local_cursor = local_conn.cursor()
            
            local_cursor.execute("SELECT name FROM persons WHERE person_id = ?", (rows[0][0],))
            person_data = local_cursor.fetchone()
            
            if person_data:
                top_person = {
                    'person_id': rows[0][0],
                    'name': person_data[0],
                    'win_count': rows[0][1]
                }
            
            local_conn.close()

        return {
            'total_persons': total_persons,
            'total_wins': total_wins,
            'top_person': top_person
        }

    def get_person_search_count(self, person_id: int) -> int:
        """特定の人物の検索回数を取得する
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            int: 検索回数（レコードが存在しない場合は0を返す）
        """
        try:
            result = self.conn.execute(
                "SELECT win_count FROM person_ranking WHERE person_id = ?",
                (person_id,)
            )
            
            rows = result.fetchall()
            if rows:
                return rows[0][0]
            return 0
            
        except Exception as e:
            logger.error(f"検索回数の取得に失敗: {str(e)}")
            return 0

    def close(self):
        """データベース接続を閉じる"""
        pass  # libsql_clientでは明示的なclose不要
