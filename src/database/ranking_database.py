import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import log_utils
import libsql_client
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

        self.conn = libsql_client.create_client_sync(
            url=self.db_url,
            auth_token=self.db_token
        )

    def update_ranking(self, person_id: int) -> None:
        """ランキングテーブルを更新（1位結果用）

        Args:
            person_id (int): 人物ID
        """
        try:
            # 既存レコードをチェック
            result = self.conn.execute(
                "SELECT win_count FROM person_ranking WHERE person_id = ?",
                [person_id]
            )

            if result.rows:
                # 既存レコードを更新
                win_count = result.rows[0][0] + 1

                self.conn.execute("""
                    UPDATE person_ranking
                    SET win_count = ?,
                        last_win_timestamp = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE person_id = ?
                """, [win_count, person_id])
            else:
                # 新規レコードを挿入
                self.conn.execute("""
                    INSERT INTO person_ranking
                    (person_id, win_count, last_win_timestamp)
                    VALUES (?, 1, CURRENT_TIMESTAMP)
                """, [person_id])

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
        result = self.conn.execute("""
            SELECT pr.person_id, p.name, pr.win_count, pr.last_win_timestamp
            FROM person_ranking pr
            JOIN persons p ON pr.person_id = p.person_id
            ORDER BY pr.win_count DESC
            LIMIT ?
        """, [limit])

        results = []
        for idx, row in enumerate(result.rows):
            # 人物の代表画像を取得（最新の画像）
            image_result = self.conn.execute("""
                SELECT fi.image_path
                FROM face_images fi
                WHERE fi.person_id = ?
                ORDER BY fi.created_at DESC
                LIMIT 1
            """, [row[0]])

            image_path = image_result.rows[0][0] if image_result.rows else None

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
        result = self.conn.execute("SELECT COUNT(*) FROM person_ranking")
        total_persons = result.rows[0][0]

        # 総勝利数
        result = self.conn.execute("SELECT SUM(win_count) FROM person_ranking")
        total_wins = result.rows[0][0] or 0

        # トップ人物
        result = self.conn.execute("""
            SELECT pr.person_id, p.name, pr.win_count
            FROM person_ranking pr
            JOIN persons p ON pr.person_id = p.person_id
            ORDER BY pr.win_count DESC
            LIMIT 1
        """)
        top_person = {
            'person_id': result.rows[0][0],
            'name': result.rows[0][1],
            'win_count': result.rows[0][2]
        } if result.rows else None

        return {
            'total_persons': total_persons,
            'total_wins': total_wins,
            'top_person': top_person
        }

    def close(self):
        """データベース接続を閉じる"""
        pass  # libsql_clientでは明示的なclose不要
