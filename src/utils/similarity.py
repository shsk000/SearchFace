"""
顔画像の類似度計算ユーティリティ

このモジュールは、顔認識における距離から類似度への変換関数を提供します。
線形変換と複数の非線形変換方法を実装しています。

類似度計算方法の特徴:
- linear: 線形変換。距離に比例して類似度が減少します。
  - 特徴: 直感的でシンプル、距離の違いがそのまま類似度に反映される
  - 欠点: 小さな距離の違いが類似度に十分に反映されない

- sigmoid: シグモイド関数による変換。中間点付近で急激に変化します。
  - 特徴: 閾値を境に類似度が大きく変わる、明確な区別が可能
  - 用途: 「同一人物か否か」のような二値的な判断に適している

- exponential: 指数関数による変換。距離が小さいときに類似度が急速に減少します。
  - 特徴: 小さな距離の違いを強調できる、高い類似度の範囲が狭くなる
  - 用途: 非常に似ている顔同士の微妙な違いを区別したい場合に最適

- quadratic: 二次関数による変換。距離が大きくなるにつれて類似度が急速に減少します。
  - 特徴: 線形よりも差異を強調できる、中程度の非線形性
  - 用途: バランスの取れた非線形変換が必要な場合

- threshold: 閾値を使用した変換。閾値以下では線形、閾値以上では急速に減少します。
  - 特徴: 閾値以下の距離では細かい区別が可能、閾値以上では大まかな区別
  - 用途: 特定の距離を境に異なる変換方法を適用したい場合
"""

import math
from typing import Callable, Dict, Any

def linear_similarity(distance: float, max_distance: float = 2.0) -> float:
    """
    線形変換で距離を類似度に変換（現在の実装）
    
    Args:
        distance: 顔エンコーディング間の距離
        max_distance: 最大距離（この値で類似度が0%になる）
        
    Returns:
        float: 0.0〜1.0の範囲の類似度
    """
    return max(0.0, 1.0 - (distance / max_distance))

def sigmoid_similarity(distance: float, steepness: float = 10.0, midpoint: float = 0.5) -> float:
    """
    シグモイド関数を使用して距離を類似度に変換
    
    Args:
        distance: 顔エンコーディング間の距離
        steepness: シグモイド関数の急峻さ（値が大きいほど急峻になる）
        midpoint: シグモイド関数の中間点（この値で類似度が50%になる）
        
    Returns:
        float: 0.0〜1.0の範囲の類似度
    """
    return 1.0 / (1.0 + math.exp(steepness * (distance - midpoint)))

def exponential_similarity(distance: float, scale: float = 2.0) -> float:
    """
    指数関数を使用して距離を類似度に変換
    
    Args:
        distance: 顔エンコーディング間の距離
        scale: 指数関数のスケール（値が大きいほど急速に減少）
            - 小さい値（0.5〜1.0）: 緩やかな減少、広い範囲で高い類似度を維持
            - 中間の値（2.0〜5.0）: バランスの取れた減少、一般的な用途に推奨
            - 大きい値（8.0〜10.0）: 急速な減少、非常に小さな距離の違いを強調
    
    scaleの値の決め方:
    1. データセットの特性に基づいて調整:
       - 同一人物の顔の距離が平均的に0.4前後の場合、scale=5.0で類似度は約13%
       - 同一人物の顔の距離が平均的に0.2前後の場合、scale=5.0で類似度は約37%
    
    2. 経験則:
       - scale = -ln(desired_similarity) / typical_distance
       - 例: 距離0.3で類似度50%にしたい場合、scale = -ln(0.5) / 0.3 ≈ 2.3
    
    3. 実験的アプローチ:
       - 複数のscale値（1.0, 3.0, 5.0, 8.0など）で試して結果を比較
       - 同一人物と異なる人物の類似度の差が最も明確になる値を選択
        
    Returns:
        float: 0.0〜1.0の範囲の類似度
    """
    return math.exp(-scale * distance)

def quadratic_similarity(distance: float, max_distance: float = 2.0) -> float:
    """
    二次関数を使用して距離を類似度に変換
    
    Args:
        distance: 顔エンコーディング間の距離
        max_distance: 最大距離（この値で類似度が0%になる）
        
    Returns:
        float: 0.0〜1.0の範囲の類似度
    """
    normalized_distance = min(distance, max_distance) / max_distance
    return 1.0 - (normalized_distance ** 2)

def threshold_similarity(distance: float, threshold: float = 0.5, max_distance: float = 2.0) -> float:
    """
    閾値を使用して距離を類似度に変換
    
    Args:
        distance: 顔エンコーディング間の距離
        threshold: 閾値（この値を境に計算方法が変わる）
        max_distance: 最大距離（この値で類似度が0%になる）
        
    Returns:
        float: 0.0〜1.0の範囲の類似度
    """
    if distance <= threshold:
        # 閾値以下の場合は線形変換
        return 1.0 - (distance / threshold)
    else:
        # 閾値以上の場合は急速に減少
        remaining_distance = distance - threshold
        remaining_range = max_distance - threshold
        remaining_similarity = 0.5 * (1.0 - (remaining_distance / remaining_range))
        return max(0.0, remaining_similarity)

# デフォルトの類似度計算関数
default_similarity_function = exponential_similarity

# 利用可能な類似度計算関数の辞書
similarity_functions: Dict[str, Callable[[float], float]] = {
    'linear': linear_similarity,
    'sigmoid': sigmoid_similarity,
    'exponential': exponential_similarity,
    'quadratic': quadratic_similarity,
    'threshold': threshold_similarity
}

def get_similarity_function(name: str) -> Callable[[float, float], float]:
    """
    名前から類似度計算関数を取得
    
    Args:
        name: 関数名（'linear', 'sigmoid', 'exponential', 'quadratic', 'threshold'）
        
    Returns:
        Callable: 類似度計算関数
        
    Raises:
        ValueError: 指定された名前の関数が存在しない場合
    """
    if name not in similarity_functions:
        raise ValueError(f"Unknown similarity function: {name}. Available functions: {list(similarity_functions.keys())}")
    return similarity_functions[name]

def calculate_similarity(result: Dict[str, Any], method: str = 'exponential') -> float:
    """
    検索結果の距離から類似度を計算
    
    Args:
        result: 検索結果の辞書（'distance'キーを含む）
        method: 使用する類似度計算方法
        
    Returns:
        float: 0.0〜1.0の範囲の類似度
    """
    similarity_func = get_similarity_function(method)
    return similarity_func(result['distance'])
