"""
顔画像の類似検索スクリプト

このスクリプトは以下の機能を提供します：
1. 指定された画像に類似する顔を検索
2. FAISSインデックスとSQLiteデータベースを使用した高速な類似検索
3. 検索結果の表示（類似度、画像パス、メタデータ）

使用方法：
- 基本的な使用: python src/search_similar_faces.py <画像パス>
- 結果数の指定: python src/search_similar_faces.py <画像パス> --top-k <数値>
- 類似度計算方法の指定: python src/search_similar_faces.py <画像パス> --similarity-method <方法>

検索結果の表示形式：
- 類似度: 0-100%の範囲で表示（距離を類似度に変換、複数の変換方法を選択可能）
- 画像パス: 検索結果の画像ファイルのパス
- メタデータ: 画像に関連付けられた追加情報（存在する場合）

注意事項：
- 入力画像から顔が検出できない場合はエラーを表示
- 類似する顔が見つからない場合は警告を表示
- データベース接続は自動的にクローズ

依存関係：
- face_recognition: 顔の検出とエンコーディング
- FAISS: 高速な類似検索
- SQLite: 画像メタデータの管理
"""

import os
import argparse
from database.face_database import FaceDatabase
from face import face_utils
from utils import log_utils
from utils.similarity import calculate_similarity, similarity_functions

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

def search_similar_faces(query_image_path: str, top_k: int = 5, similarity_method: str = 'exponential'):
    """
    指定された画像に類似する顔を検索する
    
    Args:
        query_image_path: クエリ画像のパス
        top_k: 取得する結果の数
        similarity_method: 類似度計算方法
            - 'linear': 線形変換（距離に比例して類似度が減少）
            - 'sigmoid': シグモイド関数（中間点付近で急激に変化、二値的な判断に適している）
            - 'exponential': 指数関数（距離が小さいときに類似度が急速に減少、微妙な違いを区別）
            - 'quadratic': 二次関数（線形よりも差異を強調、バランスの取れた非線形性）
            - 'threshold': 閾値を使用（閾値以下では線形、閾値以上では急速に減少）
    """
    # 顔データベースの初期化
    db = FaceDatabase()
    
    try:
        logger.info(f"画像を読み込んでいます: {query_image_path}")
        
        # クエリ画像から顔のエンコーディングを取得
        query_encoding = face_utils.get_face_encoding(query_image_path)
        if query_encoding is None:
            logger.error("クエリ画像から顔を検出できませんでした")
            return
            
        logger.info("顔のエンコーディングを取得しました")
        
        # 類似する顔を検索
        logger.info("類似検索を実行中...")
        results = db.search_similar_faces(query_encoding, top_k=top_k)
        
        # デバッグ情報の表示
        logger.info(f"検索結果の数: {len(results)}")
        
        if not results:
            logger.warning("類似する顔が見つかりませんでした")
            return
        
        # 結果の表示
        logger.info("\n検索結果:")
        for i, result in enumerate(results, 1):
            # 新しいモジュールを使用して類似度を計算
            similarity = calculate_similarity(result, method=similarity_method)
            logger.info(f"{i}位: {result['name']} (類似度: {similarity:.2%})")
            logger.info(f"  画像パス: {result['image_path']}")
            if result['metadata']:
                logger.info(f"  メタデータ: {result['metadata']}")
            logger.info("")
    
    finally:
        db.close()

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='顔画像の類似検索')
    parser.add_argument('query_image', help='検索対象の画像パス')
    parser.add_argument('--top-k', type=int, default=5, help='取得する結果の数（デフォルト: 5）')
    parser.add_argument('--similarity-method', type=str, default='exponential',
                        choices=list(similarity_functions.keys()),
                        help='''類似度計算方法（デフォルト: exponential）
                        - linear: 線形変換（シンプルだが小さな違いが反映されにくい）
                        - sigmoid: シグモイド関数（二値的な判断に適している）
                        - exponential: 指数関数（微妙な違いを強調、推奨）
                          * scaleパラメータの調整方法は utils/similarity.py を参照
                          * scale値が大きいほど距離の小さな違いが強調される
                          * 一般的には2.0〜5.0の範囲が推奨される
                        - quadratic: 二次関数（バランスの取れた非線形性）
                        - threshold: 閾値を使用（閾値を境に計算方法が変わる）''')
    
    args = parser.parse_args()
    
    # 画像ファイルの存在確認
    if not os.path.exists(args.query_image):
        logger.error(f"指定された画像ファイルが存在しません: {args.query_image}")
        return
    
    # 類似検索の実行
    search_similar_faces(args.query_image, args.top_k, args.similarity_method)

if __name__ == "__main__":
    main()
