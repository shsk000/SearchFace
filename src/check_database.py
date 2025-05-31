from database.face_database import FaceDatabase
from utils import log_utils

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

def check_database():
    """
    データベースの状態を確認する
    """
    # 顔データベースの初期化
    db = FaceDatabase()
    
    try:
        # 登録されている顔データの取得
        faces = db.get_all_faces()
        
        if not faces:
            logger.info("データベースに登録されている顔データがありません")
            return
            
        # 登録データの表示
        logger.info(f"\n登録されている顔データの数: {len(faces)}")
        logger.info("\n登録データの詳細:")
        
        # 人物ごとに集計
        person_count = {}
        for face in faces:
            name = face['name']
            if name not in person_count:
                person_count[name] = 0
            person_count[name] += 1
        
        # 集計結果の表示
        for name, count in person_count.items():
            logger.info(f"人物: {name}")
            logger.info(f"  登録画像数: {count}")
            logger.info("")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
