import os
from database.face_database import FaceDatabase
from face import face_utils

def main():
    # データディレクトリの作成
    os.makedirs("data/images", exist_ok=True)
    
    # 顔データベースの初期化
    db = FaceDatabase()
    
    try:
        # 画像ディレクトリのパス
        image_dir = "data/images"
        
        # 名前と画像ファイルの対応
        name_mapping = {
            "person1.jpg": "石原さとみ",
            "person2.jpg": "橋本環奈",
            "person3.jpg": "広瀬すず"
        }
        
        # 画像を登録
        for filename in name_mapping.keys():
            image_path = os.path.join(image_dir, filename)
            if os.path.exists(image_path):
                # 顔のエンコーディングを取得
                encoding = face_utils.get_face_encoding(image_path)
                if encoding is not None:
                    db.add_face(
                        name=name_mapping[filename],
                        image_path=image_path,
                        encoding=encoding,
                        metadata={"source": filename}
                    )
        
        # 登録された顔データの表示
        print("\n登録されている顔データ:")
        for face in db.get_all_faces():
            print(f"ID: {face['face_id']}, 名前: {face['name']}")
        
        # 検索用の画像
        query_image = "data/images/input.jpg"
        
        # 検索用の顔エンコーディングを取得
        query_encoding = face_utils.get_face_encoding(query_image)
        if query_encoding is not None:
            # 類似する顔を検索
            results = db.search_similar_faces(query_encoding, top_k=3)
            
            print("\n検索結果:")
            for result in results:
                # 距離が0.4以下なら同一人物の可能性が高い
                # 距離が0.6以上なら異なる人物
                distance = result['distance']
                if distance <= 0.4:
                    similarity = "同一人物の可能性が高い"
                elif distance <= 0.6:
                    similarity = "異なる人物の可能性がある"
                else:
                    similarity = "異なる人物"
                print(f"名前: {result['name']}, 距離: {distance:.3f}, 判定: {similarity}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main() 