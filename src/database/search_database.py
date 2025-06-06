import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils import log_utils
import libsql_client
# ロギングの設定
logger = log_utils.get_logger(__name__)

class SearchDatabase:
    """検索履歴を管理するデータベースクラス"""

    def __init__(self):
        """検索履歴データベースの初期化

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


    def record_search_results(self, search_results: List[Dict[str, Any]],
                            metadata: Optional[Dict] = None) -> str:
        """検索結果を記録（1～3位まで）

        Args:
            search_results: 検索結果のリスト（各要素は person_id, name, distance, image_path を持つ）
            metadata: 追加のメタデータ

        Returns:
            str: 記録されたsearch_session_id
        """
        try:
            # セッションIDを生成
            search_session_id = str(uuid.uuid4())

            # 各順位の結果を記録
            for rank, result in enumerate(search_results[:3], 1):  # 最大3位まで
                self.conn.execute("""
                    INSERT INTO search_history
                    (search_session_id, result_rank, person_id, distance, image_path, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [
                    search_session_id,
                    rank,
                    result['person_id'],
                    result['distance'],
                    result['image_path'],
                    json.dumps(metadata) if metadata else None
                ])

            logger.info(f"検索結果を記録しました: {len(search_results)}件 (セッション: {search_session_id})")

            return search_session_id

        except Exception as e:
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
            result = self.conn.execute("""
                SELECT sh.*, p.name
                FROM search_history sh
                JOIN persons p ON sh.person_id = p.person_id
                WHERE sh.person_id = ?
                ORDER BY sh.search_timestamp DESC
                LIMIT ?
            """, [person_id, limit])
        else:
            result = self.conn.execute("""
                SELECT sh.*, p.name
                FROM search_history sh
                JOIN persons p ON sh.person_id = p.person_id
                ORDER BY sh.search_timestamp DESC
                LIMIT ?
            """, [limit])

        rows = result.rows

        return [{
            'history_id': row[0],
            'search_session_id': row[1],
            'result_rank': row[2],
            'person_id': row[3],
            'distance': row[4],
            'image_path': row[5],
            'search_timestamp': row[6],
            'metadata': json.loads(row[7]) if row[7] else None,
            'name': row[8]  # persons テーブルからの名前
        } for row in rows]

    def get_search_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """検索セッション一覧を取得（1回の検索として）

        Args:
            limit (int): 取得する件数

        Returns:
            List[Dict[str, Any]]: 検索セッション一覧
        """
        result = self.conn.execute("""
            SELECT
                search_session_id,
                search_timestamp,
                COUNT(*) as result_count
            FROM search_history
            GROUP BY search_session_id, search_timestamp
            ORDER BY search_timestamp DESC
            LIMIT ?
        """, [limit])

        sessions = []
        for row in result.rows:
            session_id = row[0]

            # 各セッションの詳細結果を取得
            detail_result = self.conn.execute("""
                SELECT sh.result_rank, sh.person_id, p.name, sh.distance, sh.image_path
                FROM search_history sh
                JOIN persons p ON sh.person_id = p.person_id
                WHERE sh.search_session_id = ?
                ORDER BY sh.result_rank
            """, [session_id])

            results = []
            for result_row in detail_result.rows:
                results.append({
                    'rank': result_row[0],
                    'person_id': result_row[1],
                    'name': result_row[2],
                    'distance': result_row[3],
                    'image_path': result_row[4]
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
        result = self.conn.execute("SELECT COUNT(DISTINCT search_session_id) FROM search_history")
        total_search_sessions = result.rows[0][0]

        # 総検索結果数
        result = self.conn.execute("SELECT COUNT(*) FROM search_history")
        total_search_results = result.rows[0][0]

        # 最初の検索日
        result = self.conn.execute("SELECT MIN(search_timestamp) FROM search_history")
        first_search = result.rows[0][0]

        # 最新の検索日
        result = self.conn.execute("SELECT MAX(search_timestamp) FROM search_history")
        latest_search = result.rows[0][0]

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
        result = self.conn.execute("""
            SELECT sh.person_id, p.name
            FROM search_history sh
            JOIN persons p ON sh.person_id = p.person_id
            WHERE sh.search_session_id = ? AND sh.result_rank = 1
        """, [session_id])

        if result.rows:
            row = result.rows[0]
            return {
                'person_id': row[0],
                'name': row[1]
            }
        return None

    def close(self):
        """データベース接続を閉じる"""
        pass  # libsql_clientでは明示的なclose不要
