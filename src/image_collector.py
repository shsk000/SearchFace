import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from PIL import Image
from io import BytesIO
import face_recognition
import numpy as np
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pathlib import Path
from dotenv import load_dotenv
import time

# 環境変数の読み込み
load_dotenv()

class ImageCollector:
    def __init__(self):
        """画像収集クラスの初期化"""
        # 環境変数から設定を読み込み
        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not api_key or not search_engine_id:
            raise ValueError(
                "環境変数が設定されていません。"
                "GOOGLE_API_KEYとGOOGLE_SEARCH_ENGINE_IDを.envファイルに設定してください。"
            )
        
        self.service = build("customsearch", "v1", developerKey=api_key)
        self.search_engine_id = search_engine_id
        self.base_dir = Path("data/images/base")
        self.collected_dir = Path("data/images/collected")
        
        # 環境変数から閾値を読み込み（デフォルト値あり）
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))
        self.max_faces_threshold = int(os.getenv("MAX_FACES_THRESHOLD", "1"))

    def get_base_encoding(self, base_image_path: str) -> Optional[np.ndarray]:
        """基準画像の顔エンコーディングを取得

        Args:
            base_image_path (str): 基準画像のパス

        Returns:
            Optional[np.ndarray]: 顔エンコーディング
        """
        try:
            image = face_recognition.load_image_file(base_image_path)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                print(f"警告: 基準画像から顔を検出できません: {base_image_path}")
                return None
            return encodings[0]
        except Exception as e:
            print(f"エラー: 基準画像の処理に失敗: {str(e)}")
            return None

    def validate_image(self, image_data: bytes, base_encoding: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """画像の検証

        Args:
            image_data (bytes): 画像データ
            base_encoding (np.ndarray): 基準画像のエンコーディング

        Returns:
            Tuple[bool, Optional[np.ndarray]]: (検証結果, 検出された顔のエンコーディング)
        """
        try:
            # 画像を読み込み
            image = Image.open(BytesIO(image_data))
            
            # RGBA画像をRGBに変換
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # 画像を配列に変換
            image_array = np.array(image)
            
            # 顔の検出
            face_locations = face_recognition.face_locations(image_array)
            
            # 複数の顔が検出された場合は除外
            if len(face_locations) > self.max_faces_threshold:
                print(f"警告: 複数の顔が検出されました（{len(face_locations)}個）")
                return False, None
            
            # 顔が検出されない場合は除外
            if not face_locations:
                print("警告: 顔が検出されませんでした")
                return False, None
            
            # 顔のエンコーディングを取得
            face_encoding = face_recognition.face_encodings(image_array, face_locations)[0]
            
            # 類似度の計算
            distance = face_recognition.face_distance([base_encoding], face_encoding)[0]
            similarity = 1 - distance
            
            # 類似度が閾値を超える場合のみ有効
            if similarity >= self.similarity_threshold:
                print(f"類似度: {similarity:.2f}")
                return True, face_encoding
            
            print(f"警告: 類似度が低すぎます（{similarity:.2f}）")
            return False, None
            
        except Exception as e:
            print(f"エラー: 画像の検証に失敗: {str(e)}")
            return False, None

    def search_images(self, query: str, num: int = 10) -> List[str]:
        """画像検索の実行

        Args:
            query (str): 検索クエリ
            num (int): 取得する画像数

        Returns:
            List[str]: 画像URLのリスト
        """
        try:
            # 検索クエリの最適化
            optimized_query = f"{query} パッケージ"
            print(f"検索クエリ: {optimized_query}")
            
            # 画像検索の実行
            result = self.service.cse().list(
                q=optimized_query,
                cx=self.search_engine_id,
                searchType="image",
                num=num,
                safe="off"  # セーフサーチを無効化
            ).execute()
            
            # 画像情報の抽出と表示
            image_urls = []
            for item in result.get("items", []):
                url = item["link"]
                mime = item.get("mime", "不明")
                file_format = item.get("fileFormat", "不明")
                print(f"検出画像: {url}")
                print(f"  MIME: {mime}")
                print(f"  形式: {file_format}")
                image_urls.append(url)
            
            print(f"\n検索結果: {len(image_urls)}件の画像URLを取得")
            return image_urls
            
        except Exception as e:
            print(f"エラー: 画像検索に失敗: {str(e)}")
            return []

    def download_image(self, url: str, max_retries: int = 3) -> Optional[bytes]:
        """画像のダウンロード

        Args:
            url (str): 画像URL
            max_retries (int): 最大リトライ回数

        Returns:
            Optional[bytes]: 画像データ
        """
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                    'Referer': 'https://www.google.com/',
                    'sec-ch-ua': '"Google Chrome";v="119"',
                    'sec-ch-ua-platform': '"Windows"'
                }
                
                # URLがTikTokの場合はスキップ
                if "tiktok.com" in url:
                    print(f"警告: TikTok URLはスキップします: {url}")
                    return None
                    
                # URLの正規化
                url = url.split('?')[0]  # クエリパラメータを削除
                
                # セッションを使用してリクエスト
                session = requests.Session()
                response = session.get(
                    url,
                    headers=headers,
                    timeout=(5, 30),  # (接続タイムアウト, 読み取りタイムアウト)
                    verify=False
                )
                response.raise_for_status()
                
                # Content-Typeの確認
                content_type = response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    print(f"警告: 画像以外のコンテンツタイプです: {content_type}")
                    return None
                
                # 画像データの検証
                try:
                    Image.open(BytesIO(response.content))
                except Exception as e:
                    print(f"警告: 無効な画像データです: {str(e)}")
                    return None
                
                return response.content
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"警告: リトライ中... ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(1)  # リトライ前に1秒待機
                    continue
                print(f"エラー: 画像のダウンロードに失敗: {str(e)}")
                return None
            except Exception as e:
                print(f"エラー: 予期せぬエラーが発生: {str(e)}")
                return None
        
        return None

    def save_image(self, image_data: bytes, person_name: str, index: int, validation_result: str = "") -> bool:
        """画像の保存

        Args:
            image_data (bytes): 画像データ
            person_name (str): 人物名
            index (int): 画像のインデックス
            validation_result (str): 検証結果の説明

        Returns:
            bool: 保存の成功/失敗
        """
        try:
            # 保存先ディレクトリの決定
            if validation_result == "valid":
                # 有効な画像はcollectedディレクトリに保存
                person_dir = self.collected_dir / person_name
                image_path = person_dir / f"{person_name}_{index}.jpg"
            else:
                # 無効な画像はall_imagesディレクトリに保存
                person_dir = self.collected_dir / person_name / "all_images"
                result_text = validation_result.replace(" ", "_")
                image_path = person_dir / f"{person_name}_{index}_{result_text}.jpg"
            
            # ディレクトリの作成
            person_dir.mkdir(parents=True, exist_ok=True)
            
            # 画像の保存
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            print(f"画像を保存しました: {image_path}")
            return True
            
        except Exception as e:
            print(f"エラー: 画像の保存に失敗: {str(e)}")
            return False

    def collect_images_for_person(self, person_name: str, base_image_path: str, target_count: int = 3) -> int:
        """人物の画像を収集

        Args:
            person_name (str): 人物名
            base_image_path (str): 基準画像のパス
            target_count (int): 収集する画像数

        Returns:
            int: 収集した画像数
        """
        # 基準画像のエンコーディングを取得
        base_encoding = self.get_base_encoding(base_image_path)
        if base_encoding is None:
            return 0
        
        # 画像の検索
        image_urls = self.search_images(person_name)
        collected_count = 0
        download_count = 0
        
        for url in image_urls:
            if collected_count >= target_count:
                break
                
            # 画像のダウンロード
            image_data = self.download_image(url)
            if image_data is None:
                continue
            
            download_count += 1
            validation_result = ""
            
            try:
                # 画像の検証
                is_valid, _ = self.validate_image(image_data, base_encoding)
                if is_valid:
                    collected_count += 1
                    validation_result = "valid"
                else:
                    validation_result = "invalid"
            except Exception as e:
                validation_result = "error"
                print(f"エラー: 画像の検証に失敗: {str(e)}")
            
            # すべての画像を保存
            self.save_image(image_data, person_name, download_count, validation_result)
        
        print(f"\n{person_name}の結果:")
        print(f"- ダウンロードした画像数: {download_count}")
        print(f"- 有効な画像数: {collected_count}")
        return collected_count 