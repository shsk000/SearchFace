import cv2
import face_recognition
import numpy as np

def detect_faces(image_path):
    # 画像を読み込む
    image = cv2.imread(image_path)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 顔の位置を検出
    face_locations = face_recognition.face_locations(rgb_image)
    
    # 検出された顔の数
    print(f"検出された顔の数: {len(face_locations)}")
    
    # 顔の特徴を抽出
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
    
    # 結果を表示
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # 顔の周りに四角形を描画
        cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # 特徴ベクトルの次元数を表示
        print(f"特徴ベクトルの次元数: {len(face_encoding)}")
    
    # 結果を保存
    output_path = "data/images/detected_faces.jpg"
    cv2.imwrite(output_path, image)
    print(f"結果を保存しました: {output_path}")

if __name__ == "__main__":
    # テスト用の画像パスを指定
    test_image_path = "data/images/test.jpg"
    detect_faces(test_image_path) 