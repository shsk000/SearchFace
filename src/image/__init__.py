"""
画像収集モジュール

このモジュールは、Google Custom Search APIを使用して画像を収集し、
顔認識と類似度計算を行って適切な画像を保存する機能を提供します。
"""

from .collector import ImageCollector

__all__ = ['ImageCollector'] 