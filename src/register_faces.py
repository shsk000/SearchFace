import os
from database.face_database import FaceDatabase
from face import face_utils
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
            
            # 顔のエンコーディングを取得
            encoding = face_utils.get_face_encoding(image_path)
            if encoding is not None:
                # 画像を登録
                db.add_face(
                    name=person_dir,
                    image_path=image_path,
                    encoding=encoding,
                    metadata={"source": filename, "type": source_type}
                )
                logger.info(f"画像を登録しました: {filename}")
            else:
                logger.warning(f"顔を検出できませんでした: {filename}")

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
    register_all_faces()

if __name__ == "__main__":
    main() 