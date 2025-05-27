import os
import argparse
from database.face_database import FaceDatabase
from face import face_utils
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def search_similar_faces(query_image_path: str, top_k: int = 5):
    """
    指定された画像に類似する顔を検索する
    
    Args:
        query_image_path: クエリ画像のパス
        top_k: 取得する結果の数
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
            similarity = 1.0 - (result['distance'] / 2.0)  # 距離を類似度に変換（0-1の範囲）
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
    
    args = parser.parse_args()
    
    # 画像ファイルの存在確認
    if not os.path.exists(args.query_image):
        logger.error(f"指定された画像ファイルが存在しません: {args.query_image}")
        return
    
    # 類似検索の実行
    search_similar_faces(args.query_image, args.top_k)

if __name__ == "__main__":
    main() 