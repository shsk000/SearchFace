import os
import time
import libsql_experimental as libsql
from src.utils import log_utils

logger = log_utils.get_logger(__name__)

db_connections = {}
_is_sync_complete = False

def connect_to_databases():
    """アプリケーション起動時にデータベースに接続・同期する"""
    global _is_sync_complete
    logger.info("データベース接続と初回同期を開始します...")

    db_url = os.getenv('TURSO_DATABASE_URL')
    db_token = os.getenv('TURSO_AUTH_TOKEN')
    if not db_url:
        raise ValueError("TURSO_DATABASE_URLが設定されていません")

    # Search Database
    logger.info("Turso search_history DBへ接続・同期します...")
    sync_start_time = time.time()
    try:
        search_conn = libsql.connect("search_history.db", sync_url=db_url, auth_token=db_token)
        search_conn.sync()
        sync_duration = time.time() - sync_start_time
        logger.info(f"Turso search_history DBの同期が完了しました。所要時間: {sync_duration:.4f}秒")
        db_connections["search"] = search_conn
    except Exception as e:
        logger.error(f"Search Databaseの接続/同期に失敗: {e}")
        db_connections["search"] = None

    # Ranking Database
    logger.info("Turso ranking DBへ接続・同期します...")
    sync_start_time = time.time()
    try:
        ranking_conn = libsql.connect("ranking.db", sync_url=db_url, auth_token=db_token)
        ranking_conn.sync()
        sync_duration = time.time() - sync_start_time
        logger.info(f"Turso ranking DBの同期が完了しました。所要時間: {sync_duration:.4f}秒")
        db_connections["ranking"] = ranking_conn
    except Exception as e:
        logger.error(f"Ranking Databaseの接続/同期に失敗: {e}")
        db_connections["ranking"] = None

    logger.info("データベース接続処理が完了しました。")
    _is_sync_complete = True

def close_database_connections():
    """アプリケーション終了時にデータベース接続を閉じる"""
    logger.info("データベース接続を閉じます...")
    search_conn = db_connections.get("search")
    if search_conn:
        search_conn.close()
    ranking_conn = db_connections.get("ranking")
    if ranking_conn:
        ranking_conn.close()
    logger.info("データベース接続を閉じました。")

def get_search_db_connection():
    """Searchデータベースへの接続を取得する"""
    return db_connections.get("search")

def get_ranking_db_connection():
    """Rankingデータベースへの接続を取得する"""
    return db_connections.get("ranking")

def is_sync_complete():
    """データベースの初回同期が完了したかどうかを返す"""
    return _is_sync_complete
