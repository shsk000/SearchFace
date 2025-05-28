"""
ログユーティリティモジュール

プロジェクト全体で統一されたログ出力を提供します。
"""

import logging
import sys
from typing import Optional, Any

# グローバル変数
_is_initialized = False

def setup_logging(level: int = logging.INFO, 
                 format_str: str = '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                 log_file: Optional[str] = None) -> None:
    """ロギングシステムの初期化

    Args:
        level: ログレベル（デフォルト: INFO）
        format_str: ログフォーマット
        log_file: ログファイルパス（指定しない場合は標準出力のみ）
    """
    global _is_initialized
    if _is_initialized:
        return

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 既存のハンドラをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # フォーマッタの作成
    formatter = logging.Formatter(format_str)

    # コンソールハンドラの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ファイル出力が指定されている場合
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _is_initialized = True

def get_logger(name: str) -> logging.Logger:
    """名前付きロガーを取得

    Args:
        name: ロガー名（通常は__name__を使用）

    Returns:
        設定済みのロガーインスタンス
    """
    # 初期化されていない場合はデフォルト設定で初期化
    if not _is_initialized:
        setup_logging()
    
    return logging.getLogger(name)

# 便利なラッパー関数
def debug(msg: Any, *args, **kwargs) -> None:
    """DEBUGレベルのログを出力"""
    get_logger("root").debug(msg, *args, **kwargs)

def info(msg: Any, *args, **kwargs) -> None:
    """INFOレベルのログを出力"""
    get_logger("root").info(msg, *args, **kwargs)

def warning(msg: Any, *args, **kwargs) -> None:
    """WARNINGレベルのログを出力"""
    get_logger("root").warning(msg, *args, **kwargs)

def error(msg: Any, *args, **kwargs) -> None:
    """ERRORレベルのログを出力"""
    get_logger("root").error(msg, *args, **kwargs)

def critical(msg: Any, *args, **kwargs) -> None:
    """CRITICALレベルのログを出力"""
    get_logger("root").critical(msg, *args, **kwargs)

def exception(msg: Any, *args, **kwargs) -> None:
    """例外情報付きのエラーログを出力"""
    get_logger("root").exception(msg, *args, **kwargs)
