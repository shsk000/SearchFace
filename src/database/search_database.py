import json
import os
import uuid
import time
from typing import List, Dict, Any, Optional
from src.utils import log_utils
import libsql_experimental as libsql

# ロギングの設定
logger = log_utils.get_logger(__name__)

class SearchDatabase:
    """検索履歴を管理するデータベースクラス"""

    def __init__(self, conn: libsql.Connection):
        """検索履歴データベースの初期化

        Args:
            conn (libsql.Connection): データベース接続オブジェクト
        """
        if conn is None:
            raise ValueError("データベース接続が提供されていません")
        self.conn = conn

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
                """, (
                    search_session_id,
                    rank,
                    result['person_id'],
                    result['distance'],
                    result['image_path'],
                    json.dumps(metadata) if metadata else None
                ))

            self.conn.commit()
            self.conn.sync()

            logger.info(f"検索結果を記録しました: {len(search_results)}件 (セッション: {search_session_id})")

            return search_session_id

        except Exception as e:
            logger.error(f"検索結果の記録に失敗: {str(e)}")
            return None

    def get_search_history(self, limit: int = 50, person_id: int = None) -> List[Dict[str, Any]]:
        """検索履歴を取得

        Args:
            limit (int): 取得する件数
            person_id (int, optional): 特定の人物の履歴のみ取得

        Returns:
            List[Dict[str, Any]]: 検索履歴
        """
        # Tursoから検索履歴を取得
        if person_id:
            result = self.conn.execute("""
                SELECT history_id, search_session_id, result_rank, person_id, distance, image_path, search_timestamp, metadata
                FROM search_history
                WHERE person_id = ?
                ORDER BY search_timestamp DESC
                LIMIT ?
            """, (person_id, limit))
        else:
            result = self.conn.execute("""
                SELECT history_id, search_session_id, result_rank, person_id, distance, image_path, search_timestamp, metadata
                FROM search_history
                ORDER BY search_timestamp DESC
                LIMIT ?
            """, (limit,))

        rows = result.fetchall()

        # 人物IDリストを抽出
        person_ids = list(set(row[3] for row in rows))  # 重複除去

        # ローカルSQLiteから人物名を取得
        import sqlite3
        import os

        db_path = os.path.abspath("data/face_database.db")

        if os.path.exists(db_path) and person_ids:
            try:
                local_conn = sqlite3.connect(db_path)
                local_cursor = local_conn.cursor()
                placeholders = ",".join("?" * len(person_ids))
                query = f"SELECT person_id, name FROM persons WHERE person_id IN ({placeholders})"
                local_cursor.execute(query, person_ids)
                name_rows = local_cursor.fetchall()
                person_names = {row[0]: row[1] for row in name_rows}
                local_conn.close()
            except Exception as e:
                logger.error(f"ローカルSQLiteクエリエラー: {str(e)}")
                person_names = {}
        else:
            person_names = {}

        return [{
            'history_id': row[0],
            'search_session_id': row[1],
            'result_rank': row[2],
            'person_id': row[3],
            'distance': row[4],
            'image_path': row[5],
            'search_timestamp': row[6],
            'metadata': json.loads(row[7]) if row[7] else None,
            'name': person_names.get(row[3], f"Unknown({row[3]})")
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
        """, (limit,))

        sessions = []
        for row in result.fetchall():
            session_id = row[0]

            # 各セッションの詳細結果を取得（Tursoから）
            detail_result = self.conn.execute("""
                SELECT result_rank, person_id, distance, image_path
                FROM search_history
                WHERE search_session_id = ?
                ORDER BY result_rank
            """, (session_id,))

            detail_rows = detail_result.fetchall()

            # 人物IDリストを抽出
            session_person_ids = [row[1] for row in detail_rows]

            # ローカルSQLiteから人物名を取得
            import sqlite3
            import os

            db_path = os.path.abspath("data/face_database.db")

            if os.path.exists(db_path) and session_person_ids:
                try:
                    local_conn = sqlite3.connect(db_path)
                    local_cursor = local_conn.cursor()
                    placeholders = ",".join("?" * len(session_person_ids))
                    query = f"SELECT person_id, name FROM persons WHERE person_id IN ({placeholders})"
                    local_cursor.execute(query, session_person_ids)
                    name_rows = local_cursor.fetchall()
                    session_person_names = {row[0]: row[1] for row in name_rows}
                    local_conn.close()
                except Exception as e:
                    logger.error(f"ローカルSQLiteクエリエラー: {str(e)}")
                    session_person_names = {}
            else:
                session_person_names = {}

            results = []
            for result_row in detail_rows:
                rank, person_id, distance, image_path = result_row
                results.append({
                    'rank': rank,
                    'person_id': person_id,
                    'name': session_person_names.get(person_id, f"Unknown({person_id})"),
                    'distance': distance,
                    'image_path': image_path
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
        total_search_sessions = result.fetchall()[0][0]

        # 総検索結果数
        result = self.conn.execute("SELECT COUNT(*) FROM search_history")
        total_search_results = result.fetchall()[0][0]

        # 最初の検索日
        result = self.conn.execute("SELECT MIN(search_timestamp) FROM search_history")
        first_search = result.fetchall()[0][0]

        # 最新の検索日
        result = self.conn.execute("SELECT MAX(search_timestamp) FROM search_history")
        latest_search = result.fetchall()[0][0]

        return {
            'total_search_sessions': total_search_sessions,
            'total_search_results': total_search_results,
            'first_search_date': first_search,
            'latest_search_date': latest_search
        }

    def get_search_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """指定セッションの検索結果を取得

        Args:
            session_id (str): 検索セッションID

        Returns:
            Optional[Dict[str, Any]]: 検索セッション結果、存在しない場合はNone
        """
        # セッションの基本情報とメタデータを取得
        session_result = self.conn.execute("""
            SELECT search_timestamp, metadata
            FROM search_history
            WHERE search_session_id = ?
            LIMIT 1
        """, (session_id,))

        session_rows = session_result.fetchall()
        if not session_rows:
            return None

        session_row = session_rows[0]
        search_timestamp = session_row[0]
        metadata = json.loads(session_row[1]) if session_row[1] else {}

        # セッションの全結果を取得（Tursoから）
        results_query = self.conn.execute("""
            SELECT result_rank, person_id, distance, image_path
            FROM search_history
            WHERE search_session_id = ?
            ORDER BY result_rank
        """, (session_id,))

        turso_results = results_query.fetchall()

        # 人物IDリストを抽出
        person_ids = [row[1] for row in turso_results]

        # ローカルSQLiteから人物名を取得
        import sqlite3
        import os

        # 絶対パスでローカルSQLiteに接続
        db_path = os.path.abspath("data/face_database.db")
        logger.info(f"ローカルSQLite接続先: {db_path}")

        if not os.path.exists(db_path):
            logger.error(f"ローカルSQLiteファイルが見つかりません: {db_path}")
            person_names = {}
        else:
            try:
                local_conn = sqlite3.connect(db_path)
                local_cursor = local_conn.cursor()

                if person_ids:
                    placeholders = ",".join("?" * len(person_ids))
                    query = f"SELECT person_id, name FROM persons WHERE person_id IN ({placeholders})"
                    local_cursor.execute(query, person_ids)
                    rows = local_cursor.fetchall()
                    person_names = {row[0]: row[1] for row in rows}
                else:
                    person_names = {}

                local_conn.close()
                logger.info(f"人物名を取得しました: {len(person_names)}件")

            except Exception as e:
                logger.error(f"ローカルSQLiteクエリエラー: {str(e)}")
                person_names = {}

        # 結果をマージ
        results = []
        for row in turso_results:
            rank, person_id, distance, image_path = row
            results.append({
                'rank': rank,
                'person_id': person_id,
                'name': person_names.get(person_id, f"Unknown({person_id})"),
                'distance': distance,
                'image_path': image_path
            })

        return {
            'session_id': session_id,
            'search_timestamp': search_timestamp,
            'metadata': metadata,
            'results': results
        }

    def get_winner_for_ranking(self, session_id: str) -> Optional[Dict[str, Any]]:
        """指定セッションの1位結果を取得（ランキング更新用）

        Args:
            session_id (str): 検索セッションID

        Returns:
            Optional[Dict[str, Any]]: 1位の結果、存在しない場合はNone
        """
        # Tursoから1位の結果を取得
        result = self.conn.execute("""
            SELECT person_id
            FROM search_history
            WHERE search_session_id = ? AND result_rank = 1
        """, (session_id,))

        rows = result.fetchall()
        if rows:
            person_id = rows[0][0]

            # ローカルSQLiteから人物名を取得
            import sqlite3
            import os

            db_path = os.path.abspath("data/face_database.db")

            if os.path.exists(db_path):
                try:
                    local_conn = sqlite3.connect(db_path)
                    local_cursor = local_conn.cursor()
                    local_cursor.execute("SELECT name FROM persons WHERE person_id = ?", (person_id,))
                    name_row = local_cursor.fetchone()
                    name = name_row[0] if name_row else f"Unknown({person_id})"
                    local_conn.close()
                except Exception as e:
                    logger.error(f"ローカルSQLiteクエリエラー: {str(e)}")
                    name = f"Unknown({person_id})"
            else:
                name = f"Unknown({person_id})"

            return {
                'person_id': person_id,
                'name': name
            }
        return None

    def close(self):
        """データベース接続を閉じる (何もしない、接続管理は外部で行う)"""
        pass
