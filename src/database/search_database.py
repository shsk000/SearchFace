import sqlite3
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import log_utils

# ロギングの設定
logger = log_utils.get_logger(__name__)

class SearchDatabase:
    """検索履歴を管理するデータベースクラス"""

    def __init__(self, db_path: str = "data/face_database.db"):
        """検索履歴データベースの初期化

        Args:
            db_path (str): データベースファイルのパス
        """
        self.db_path = db_path

        # データディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_search_tables()

    def _create_search_tables(self):
        """検索履歴関連のテーブルを作成"""

        # 検索履歴テーブル（1回の検索で複数行記録）
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_session_id TEXT NOT NULL,
                result_rank INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                similarity REAL NOT NULL,
                distance REAL NOT NULL,
                image_path TEXT NOT NULL,
                search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE CASCADE
            )
        """)

        # インデックス作成
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_history_person_id ON search_history(person_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_history_timestamp ON search_history(search_timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_search_history_session_rank ON search_history(search_session_id, result_rank)")

        self.conn.commit()
        logger.info("検索履歴テーブルの初期化が完了しました")

    def record_search_results(self, search_results: List[Dict[str, Any]],
                            metadata: Optional[Dict] = None) -> str:
        """検索結果を記録（1～3位まで）

        Args:
            search_results: 検索結果のリスト（各要素は person_id, name, similarity, distance, image_path を持つ）
            metadata: 追加のメタデータ

        Returns:
            str: 記録されたsearch_session_id
        """
        try:
            self.conn.execute("BEGIN TRANSACTION")

            # セッションIDを生成
            search_session_id = str(uuid.uuid4())

            # 各順位の結果を記録
            for rank, result in enumerate(search_results[:3], 1):  # 最大3位まで
                self.cursor.execute("""
                    INSERT INTO search_history
                    (search_session_id, result_rank, person_id, similarity, distance, image_path, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    search_session_id,
                    rank,
                    result['person_id'],
                    result['similarity'],
                    result['distance'],
                    result['image_path'],
                    json.dumps(metadata) if metadata else None
                ))

            self.conn.commit()
            logger.info(f"検索結果を記録しました: {len(search_results)}件 (セッション: {search_session_id})")

            return search_session_id

        except Exception as e:
            self.conn.rollback()
            logger.error(f"検索結果の記録に失敗: {str(e)}")
            raise

    def get_search_history(self, limit: int = 50, person_id: int = None) -> List[Dict[str, Any]]:
        """検索履歴を取得

        Args:
            limit (int): 取得する件数
            person_id (int, optional): 特定の人物の履歴のみ取得

        Returns:
            List[Dict[str, Any]]: 検索履歴
        """
        if person_id:
            self.cursor.execute("""
                SELECT sh.*, p.name
                FROM search_history sh
                JOIN persons p ON sh.person_id = p.person_id
                WHERE sh.person_id = ?
                ORDER BY sh.search_timestamp DESC
                LIMIT ?
            """, (person_id, limit))
        else:
            self.cursor.execute("""
                SELECT sh.*, p.name
                FROM search_history sh
                JOIN persons p ON sh.person_id = p.person_id
                ORDER BY sh.search_timestamp DESC
                LIMIT ?
            """, (limit,))

        rows = self.cursor.fetchall()

        return [{
            'history_id': row[0],
            'search_session_id': row[1],
            'result_rank': row[2],
            'person_id': row[3],
            'similarity': row[4],
            'distance': row[5],
            'image_path': row[6],
            'search_timestamp': row[7],
            'metadata': json.loads(row[8]) if row[8] else None,
            'name': row[9]  # persons テーブルからの名前
        } for row in rows]

    def get_search_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """検索セッション一覧を取得（1回の検索として）

        Args:
            limit (int): 取得する件数

        Returns:
            List[Dict[str, Any]]: 検索セッション一覧
        """
        self.cursor.execute("""
            SELECT
                search_session_id,
                search_timestamp,
                COUNT(*) as result_count
            FROM search_history
            GROUP BY search_session_id, search_timestamp
            ORDER BY search_timestamp DESC
            LIMIT ?
        """, (limit,))

        sessions = []
        for row in self.cursor.fetchall():
            session_id = row[0]

            # 各セッションの詳細結果を取得
            self.cursor.execute("""
                SELECT sh.result_rank, sh.person_id, p.name, sh.similarity, sh.distance, sh.image_path
                FROM search_history sh
                JOIN persons p ON sh.person_id = p.person_id
                WHERE sh.search_session_id = ?
                ORDER BY sh.result_rank
            """, (session_id,))

            results = []
            for result_row in self.cursor.fetchall():
                results.append({
                    'rank': result_row[0],
                    'person_id': result_row[1],
                    'name': result_row[2],
                    'similarity': result_row[3],
                    'distance': result_row[4],
                    'image_path': result_row[5]
                })

            sessions.append({
                'session_id': session_id,
                'timestamp': row[1],
                'result_count': row[2],
                'results': results
            })

        return sessions

    def get_search_stats(self) -> Dict[str, Any]:
        """検索統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        # 総検索セッション数
        self.cursor.execute("SELECT COUNT(DISTINCT search_session_id) FROM search_history")
        total_search_sessions = self.cursor.fetchone()[0]

        # 総検索結果数
        self.cursor.execute("SELECT COUNT(*) FROM search_history")
        total_search_results = self.cursor.fetchone()[0]

        # 最初の検索日
        self.cursor.execute("SELECT MIN(search_timestamp) FROM search_history")
        first_search = self.cursor.fetchone()[0]

        # 最新の検索日
        self.cursor.execute("SELECT MAX(search_timestamp) FROM search_history")
        latest_search = self.cursor.fetchone()[0]

        return {
            'total_search_sessions': total_search_sessions,
            'total_search_results': total_search_results,
            'first_search_date': first_search,
            'latest_search_date': latest_search
        }

    def get_winner_for_ranking(self, session_id: str) -> Optional[Dict[str, Any]]:
        """指定セッションの1位結果を取得（ランキング更新用）

        Args:
            session_id (str): 検索セッションID

        Returns:
            Optional[Dict[str, Any]]: 1位の結果、存在しない場合はNone
        """
        self.cursor.execute("""
            SELECT sh.person_id, p.name, sh.similarity
            FROM search_history sh
            JOIN persons p ON sh.person_id = p.person_id
            WHERE sh.search_session_id = ? AND sh.result_rank = 1
        """, (session_id,))

        result = self.cursor.fetchone()
        if result:
            return {
                'person_id': result[0],
                'name': result[1],
                'similarity': result[2]
            }
        return None

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close()
