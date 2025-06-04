"""
カスタム例外クラス

このモジュールは以下の機能を提供します：
1. アプリケーション固有の例外クラスの定義
2. エラーコードとメッセージの管理
3. 例外ハンドリングの標準化
"""

from typing import Optional
from src.core.errors import ErrorCode

class BaseException(Exception):
    """アプリケーションの基底例外クラス"""
    
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500
    ):
        """例外の初期化
        
        Args:
            code (str): エラーコード
            message (str): エラーメッセージ
            status_code (int): HTTPステータスコード（デフォルト: 500）
        """
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class ImageValidationException(BaseException):
    """画像検証に関する例外"""
    
    def __init__(
        self,
        code: str,
        message: Optional[str] = None,
        status_code: int = 400
    ):
        """画像検証例外の初期化
        
        Args:
            code (str): エラーコード
            message (str, optional): エラーメッセージ
            status_code (int): HTTPステータスコード（デフォルト: 400）
        """
        if message is None:
            message = "画像の検証に失敗しました"
        super().__init__(code, message, status_code)

class ServerException(BaseException):
    """サーバーエラーに関する例外"""
    
    def __init__(
        self,
        code: str = ErrorCode.SERVER_ERROR,
        message: Optional[str] = None,
        status_code: int = 500
    ):
        """サーバー例外の初期化
        
        Args:
            code (str): エラーコード（デフォルト: SERVER_ERROR）
            message (str, optional): エラーメッセージ
            status_code (int): HTTPステータスコード（デフォルト: 500）
        """
        if message is None:
            message = "サーバーエラーが発生しました"
        super().__init__(code, message, status_code) 