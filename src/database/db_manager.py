import os
from src.utils import log_utils

logger = log_utils.get_logger(__name__)

_is_sync_complete = True  # リモートモードでは常に利用可能

def connect_to_databases():
    """軽量な初期化処理（リモートモード用）"""
    logger.info("データベース初期化完了（リモートモード）")

def close_database_connections():
    """データベース接続を閉じる（何もしない）"""
    logger.info("データベース接続処理完了")

def get_search_db_connection():
    """Searchデータベースへの接続を取得する（使用されない）"""
    return None

def get_ranking_db_connection():
    """Rankingデータベースへの接続を取得する（使用されない）"""
    return None

def is_sync_complete():
    """データベースの同期状態を返す（リモートモードでは常にTrue）"""
    return _is_sync_complete
