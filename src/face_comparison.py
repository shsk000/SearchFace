import cv2
import face_recognition
import numpy as np
from typing import Tuple, List, Optional

def get_face_encodings(image_path: str) -> Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]:
    """
    画像から顔の特徴ベクトルと位置を抽出します
    
    Args:
        image_path (str): 画像ファイルのパス
        
    Returns:
        Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]: 
            - 顔の特徴ベクトルのリスト
            - 顔の位置（top, right, bottom, left）のリスト
    """
    # 画像を読み込む
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"画像を読み込めませんでした: {image_path}")
    
    # RGBに変換
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # 顔の位置を検出
    face_locations = face_recognition.face_locations(rgb_image)
    
    if not face_locations:
        raise ValueError(f"顔が検出されませんでした: {image_path}")
    
    # 顔の特徴ベクトルを抽出
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
    
    return face_encodings, face_locations

def interpret_similarity(similarity: float, threshold: float = 0.6) -> str:
    """
    類似度を解釈し、説明を返します
    
    Args:
        similarity (float): 類似度（0.0から1.0）
        threshold (float): 同一人物と判定する閾値
        
    Returns:
        str: 類似度の解釈
    """
    percentage = similarity * 100
    
    if similarity >= threshold:
        confidence = "高い"
        if similarity > 0.8:
            confidence = "非常に高い"
        return f"同一人物である可能性が{confidence}（類似度: {percentage:.1f}%）"
    elif similarity > 0.5:
        return f"同一人物の可能性があるが、確信度は中程度（類似度: {percentage:.1f}%）"
    else:
        return f"別人である可能性が高い（類似度: {percentage:.1f}%）"

def compare_faces(image1_path: str, image2_path: str, threshold: float = 0.6) -> Tuple[float, Optional[np.ndarray], Optional[np.ndarray]]:
    """
    2つの画像の顔の類似度を計算します
    
    Args:
        image1_path (str): 1つ目の画像ファイルのパス
        image2_path (str): 2つ目の画像ファイルのパス
        threshold (float): 同一人物と判定する閾値（デフォルト: 0.6）
        
    Returns:
        Tuple[float, Optional[np.ndarray], Optional[np.ndarray]]:
            - 類似度（0.0から1.0の間の値）
            - 1つ目の画像の特徴ベクトル
            - 2つ目の画像の特徴ベクトル
    """
    try:
        # 両方の画像から顔の特徴ベクトルを取得
        encodings1, _ = get_face_encodings(image1_path)
        encodings2, _ = get_face_encodings(image2_path)
        
        # 最初に検出された顔のみを使用
        encoding1 = encodings1[0]
        encoding2 = encodings2[0]
        
        # 類似度を計算（0.0から1.0の間の値）
        similarity = face_recognition.face_distance([encoding1], encoding2)[0]
        similarity = 1.0 - similarity  # 距離を類似度に変換
        
        # 類似度の解釈を表示
        interpretation = interpret_similarity(similarity, threshold)
        print(interpretation)
        
        return similarity, encoding1, encoding2
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return 0.0, None, None

def resize_image(image: np.ndarray, max_size: int = 800) -> np.ndarray:
    """
    画像のサイズを調整します
    
    Args:
        image (np.ndarray): 入力画像
        max_size (int): 最大サイズ（幅または高さ）
        
    Returns:
        np.ndarray: リサイズされた画像
    """
    height, width = image.shape[:2]
    if height > width:
        new_height = max_size
        new_width = int(width * (max_size / height))
    else:
        new_width = max_size
        new_height = int(height * (max_size / width))
    
    return cv2.resize(image, (new_width, new_height))

def visualize_comparison(image1_path: str, image2_path: str, threshold: float = 0.6, output_path: str = "data/images/comparison_result.jpg"):
    """
    2つの画像の顔を比較し、結果を可視化します
    
    Args:
        image1_path (str): 1つ目の画像ファイルのパス
        image2_path (str): 2つ目の画像ファイルのパス
        threshold (float): 同一人物と判定する閾値（デフォルト: 0.6）
        output_path (str): 結果を保存するパス
    """
    # 画像を読み込む
    image1 = cv2.imread(image1_path)
    image2 = cv2.imread(image2_path)
    
    if image1 is None or image2 is None:
        raise ValueError("画像を読み込めませんでした")
    
    # 画像のサイズを調整
    image1 = resize_image(image1)
    image2 = resize_image(image2)
    
    # 顔の位置を取得
    _, locations1 = get_face_encodings(image1_path)
    _, locations2 = get_face_encodings(image2_path)
    
    # 類似度を計算
    similarity, _, _ = compare_faces(image1_path, image2_path, threshold)
    
    # 顔の周りに四角形を描画（類似度に応じて色を変更）
    color = (0, 255, 0) if similarity >= threshold else (0, 165, 255)  # 緑または橙
    
    # リサイズ後の座標に変換して四角形を描画
    for (top, right, bottom, left) in locations1:
        scale_x = image1.shape[1] / cv2.imread(image1_path).shape[1]
        scale_y = image1.shape[0] / cv2.imread(image1_path).shape[0]
        top = int(top * scale_y)
        right = int(right * scale_x)
        bottom = int(bottom * scale_y)
        left = int(left * scale_x)
        cv2.rectangle(image1, (left, top), (right, bottom), color, 2)
    
    for (top, right, bottom, left) in locations2:
        scale_x = image2.shape[1] / cv2.imread(image2_path).shape[1]
        scale_y = image2.shape[0] / cv2.imread(image2_path).shape[0]
        top = int(top * scale_y)
        right = int(right * scale_x)
        bottom = int(bottom * scale_y)
        left = int(left * scale_x)
        cv2.rectangle(image2, (left, top), (right, bottom), color, 2)
    
    # 画像を横に結合
    result = np.hstack((image1, image2))
    
    # 類似度の解釈をテキストとして追加
    interpretation = interpret_similarity(similarity, threshold)
    cv2.putText(result, f"Similarity: {similarity:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    cv2.putText(result, f"Match: {similarity >= threshold}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
    
    # 結果を保存
    cv2.imwrite(output_path, result)
    print(f"結果を保存しました: {output_path}")

if __name__ == "__main__":
    # テスト用の画像パスを指定
    image1_path = "data/images/input.jpg"
    image2_path = "data/images/person3.jpg"
    threshold = 0.6  # 同一人物と判定する閾値
    
    # 類似度を計算
    similarity, encoding1, encoding2 = compare_faces(image1_path, image2_path, threshold)
    
    # 結果を可視化
    visualize_comparison(image1_path, image2_path, threshold) 