"""
エラーコードとメッセージの定義

このモジュールは以下の機能を提供します：
1. アプリケーション全体で使用するエラーコードの定義
2. エラーメッセージの管理
3. エラーレスポンスの標準化
"""

from enum import Enum
from typing import Dict, Any

class ErrorCode(str, Enum):
    """エラーコードの定義"""
    
    # 画像検証エラー
    INVALID_IMAGE_FORMAT = "INVALID_IMAGE_FORMAT"
    IMAGE_TOO_LARGE = "IMAGE_TOO_LARGE"
    IMAGE_CORRUPTED = "IMAGE_CORRUPTED"
    NO_FACE_DETECTED = "NO_FACE_DETECTED"
    MULTIPLE_FACES = "MULTIPLE_FACES"
    
    # データベースエラー
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_QUERY_ERROR = "DATABASE_QUERY_ERROR"
    
    # サーバーエラー
    SERVER_ERROR = "SERVER_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"

# エラーメッセージの定義
ERROR_MESSAGES: Dict[str, str] = {
    ErrorCode.INVALID_IMAGE_FORMAT: "無効な画像形式です",
    ErrorCode.IMAGE_TOO_LARGE: "画像サイズが大きすぎます（500KB以下にしてください）",
    ErrorCode.IMAGE_CORRUPTED: "画像が破損しています",
    ErrorCode.NO_FACE_DETECTED: "画像から顔が検出できませんでした",
    ErrorCode.MULTIPLE_FACES: "画像に複数の顔が検出されました",
    
    ErrorCode.DATABASE_ERROR: "データベースエラーが発生しました",
    ErrorCode.DATABASE_CONNECTION_ERROR: "データベースへの接続に失敗しました",
    ErrorCode.DATABASE_QUERY_ERROR: "データベースクエリの実行に失敗しました",
    
    ErrorCode.SERVER_ERROR: "サーバーエラーが発生しました",
    ErrorCode.INTERNAL_ERROR: "内部エラーが発生しました",
    ErrorCode.SERVICE_UNAVAILABLE: "サービスが利用できません"
}

def get_error_response(error_code: ErrorCode) -> Dict[str, Any]:
    """エラーレスポンスを生成する
    
    Args:
        error_code (ErrorCode): エラーコード
        
    Returns:
        Dict[str, Any]: エラーレスポンス
    """
    return {
        "error": {
            "code": error_code,
            "message": ERROR_MESSAGES.get(error_code, "不明なエラーが発生しました")
        }
    } 