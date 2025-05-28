import os
from database.face_database import FaceDatabase
from face import face_utils
from utils import image_utils
import argparse
from datetime import datetime
from utils import log_utils

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

def register_faces_from_directory(db: FaceDatabase, directory: str, source_type: str):
    """
    指定されたディレクトリ内のすべての人物ディレクトリの画像を登録する
    
    Args:
        db: FaceDatabaseインスタンス
        directory: 処理対象のディレクトリパス
        source_type: 画像のソースタイプ（'base'または'collected'）
    """
    # ディレクトリ内のすべての人物ディレクトリを処理
    for person_dir in os.listdir(directory):
        person_path = os.path.join(directory, person_dir)
        
        # ディレクトリの場合のみ処理
        if not os.path.isdir(person_path):
            continue
            
        logger.info(f"人物ディレクトリを処理中: {person_dir}")
        
        # 人物ディレクトリ内の画像を処理
        for filename in os.listdir(person_path):
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue
                
            image_path = os.path.join(person_path, filename)
            logger.info(f"画像を処理中: {filename}")
            
            # 画像のハッシュ値を計算
            image_hash = image_utils.calculate_image_hash(image_path)
            if not image_hash:
                logger.error(f"画像ハッシュの計算に失敗しました: {filename}")
                continue
            
            # 顔のエンコーディングを取得
            encoding = face_utils.get_face_encoding(image_path)
            if encoding is not None:
                # 画像を登録
                db.add_face(
                    name=person_dir,
                    image_path=image_path,
                    encoding=encoding,
                    image_hash=image_hash,
                    metadata={"source": filename, "type": source_type}
                )
                logger.info(f"画像を登録しました: {filename}")
            else:
                logger.warning(f"顔を検出できませんでした: {filename}")

def register_single_face(image_path: str, name: str, source_type: str = "test"):
    """
    指定された1枚の画像を登録する
    
    Args:
        image_path: 登録する画像のパス
        name: 人物名
        source_type: 画像のソースタイプ（デフォルト: "test"）
    """
    # 画像ファイルの存在確認
    if not os.path.exists(image_path):
        logger.error(f"指定された画像ファイルが存在しません: {image_path}")
        return False
        
    # 顔データベースの初期化
    db = FaceDatabase()
    
    try:
        logger.info(f"画像を処理中: {image_path}")
        
        # 画像のハッシュ値を計算
        image_hash = image_utils.calculate_image_hash(image_path)
        if not image_hash:
            logger.error(f"画像ハッシュの計算に失敗しました: {image_path}")
            return False
        
        # 顔のエンコーディングを取得
        encoding = face_utils.get_face_encoding(image_path)
        if encoding is not None:
            # 画像を登録
            image_id = db.add_face(
                name=name,
                image_path=image_path,
                encoding=encoding,
                image_hash=image_hash,
                metadata={
                    "source": os.path.basename(image_path),
                    "type": source_type,
                    "registered_at": datetime.now().isoformat()
                }
            )
            logger.info(f"画像を登録しました: {image_path}")
            logger.info(f"登録された画像ID: {image_id}")
            return True
        else:
            logger.warning(f"顔を検出できませんでした: {image_path}")
            return False
    
    finally:
        db.close()

def register_all_faces():
    """
    baseディレクトリとcollectedディレクトリ内のすべての人物ディレクトリの画像を登録する
    """
    # データディレクトリの作成
    os.makedirs("data/images", exist_ok=True)
    
    # 顔データベースの初期化
    db = FaceDatabase()
    
    try:
        # baseディレクトリの処理
        base_dir = "data/images/base"
        if os.path.exists(base_dir):
            logger.info("baseディレクトリの画像を処理中...")
            register_faces_from_directory(db, base_dir, "base")
        
        # collectedディレクトリの処理
        collected_dir = "data/images/collected"
        if os.path.exists(collected_dir):
            logger.info("collectedディレクトリの画像を処理中...")
            register_faces_from_directory(db, collected_dir, "collected")
        
        # 登録された顔データの表示
        logger.info("\n登録されている顔データ:")
        for face in db.get_all_faces():
            logger.info(f"ID: {face['person_id']}, 名前: {face['name']}, タイプ: {face['image_metadata'].get('type', 'unknown') if face['image_metadata'] else 'unknown'}")
    
    finally:
        db.close()

def main():
    # コマンドライン引数の設定
    parser = argparse.ArgumentParser(description='顔画像の登録')
    parser.add_argument('--single', action='store_true', help='1枚の画像のみを登録')
    parser.add_argument('--image', help='登録する画像のパス（--single指定時必須）')
    parser.add_argument('--name', help='人物名（--single指定時必須）')
    parser.add_argument('--type', default='test', help='画像のソースタイプ（デフォルト: test）')
    
    args = parser.parse_args()
    
    if args.single:
        if not args.image or not args.name:
            logger.error("--single指定時は--imageと--nameが必須です")
            return
        register_single_face(args.image, args.name, args.type)
    else:
        register_all_faces()

if __name__ == "__main__":
    main()
