import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import log_utils

# ロギングの設定
logger = log_utils.get_logger(__name__)

class RankingDatabase:
    """ランキング集計を管理するデータベースクラス"""

    def __init__(self, db_path: str = "data/face_database.db"):
        """ランキングデータベースの初期化

        Args:
            db_path (str): データベースファイルのパス
        """
        self.db_path = db_path

        # データディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_ranking_tables()

    def _create_ranking_tables(self):
        """ランキング関連のテーブルを作成"""

        # 人物ランキングテーブル（集計データ）
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS person_ranking (
                ranking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL UNIQUE,
                win_count INTEGER DEFAULT 0,
                last_win_timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
            )
        """)

        # インデックス作成
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_ranking_person_id ON person_ranking(person_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_person_ranking_win_count ON person_ranking(win_count DESC)")

        self.conn.commit()
        logger.info("ランキングテーブルの初期化が完了しました")

    def update_ranking(self, person_id: int) -> None:
        """ランキングテーブルを更新（1位結果用）

        Args:
            person_id (int): 人物ID
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            # 既存レコードをチェック
            self.cursor.execute(
                "SELECT win_count FROM person_ranking WHERE person_id = ?",
                (person_id,)
            )

            result = self.cursor.fetchone()

            if result:
                # 既存レコードを更新
                win_count = result[0] + 1

                self.cursor.execute("""
                    UPDATE person_ranking
                    SET win_count = ?,
                        last_win_timestamp = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE person_id = ?
                """, (win_count, person_id))
            else:
                # 新規レコードを挿入
                self.cursor.execute("""
                    INSERT INTO person_ranking
                    (person_id, win_count, last_win_timestamp)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                """, (person_id,))

            self.conn.commit()
            logger.info(f"ランキングを更新しました: person_id={person_id}")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"ランキングの更新に失敗: {str(e)}")
            raise

    def get_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """ランキングを取得

        Args:
            limit (int): 取得する件数

        Returns:
            List[Dict[str, Any]]: ランキング結果
        """
        self.cursor.execute("""
            SELECT pr.person_id, p.name, pr.win_count, pr.last_win_timestamp
            FROM person_ranking pr
            JOIN persons p ON pr.person_id = p.person_id
            ORDER BY pr.win_count DESC
            LIMIT ?
        """, (limit,))

        results = []
        for idx, row in enumerate(self.cursor.fetchall()):
            # 人物の代表画像を取得（最新の画像）
            self.cursor.execute("""
                SELECT fi.image_path
                FROM face_images fi
                WHERE fi.person_id = ?
                ORDER BY fi.created_at DESC
                LIMIT 1
            """, (row[0],))

            image_result = self.cursor.fetchone()
            image_path = image_result[0] if image_result else None

            results.append({
                'rank': idx + 1,
                'person_id': row[0],
                'name': row[1],
                'win_count': row[2],
                'last_win_date': row[3],
                'image_path': image_path
            })

        return results

    def get_ranking_stats(self) -> Dict[str, Any]:
        """ランキング統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        # 総人物数（ランキングに登録されている）
        self.cursor.execute("SELECT COUNT(*) FROM person_ranking")
        total_persons = self.cursor.fetchone()[0]

        # 総勝利数
        self.cursor.execute("SELECT SUM(win_count) FROM person_ranking")
        total_wins = self.cursor.fetchone()[0] or 0

        # トップ人物
        self.cursor.execute("""
            SELECT pr.person_id, p.name, pr.win_count
            FROM person_ranking pr
            JOIN persons p ON pr.person_id = p.person_id
            ORDER BY pr.win_count DESC
            LIMIT 1
        """)
        top_person_row = self.cursor.fetchone()
        top_person = {
            'person_id': top_person_row[0],
            'name': top_person_row[1],
            'win_count': top_person_row[2]
        } if top_person_row else None

        return {
            'total_persons': total_persons,
            'total_wins': total_wins,
            'top_person': top_person
        }

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close()
