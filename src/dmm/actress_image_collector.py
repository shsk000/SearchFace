"""
DMM API 女優画像収集クラス

DMM APIから商品画像を取得し、顔検出・類似度計算を行って
女優の顔写真を収集・保存する機能を提供します。
"""

import time
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from PIL import Image
from io import BytesIO

# プロジェクト内のモジュール
from .dmm_api_client import DmmApiClient
from .models import (
    ActressInfo, CollectionResult, CollectionStatus, CollectionConfig,
    FaceExtractionResult, SavedFaceInfo
)
from src.database.person_database import PersonDatabase
from src.face import face_utils
from src.utils import image_utils, similarity, log_utils
from .image_downloader import DmmImageDownloader

# ログ設定
logger = log_utils.get_logger(__name__)


class DmmActressImageCollector:
    """DMM API 女優画像収集クラス"""
    
    def __init__(self, config: Optional[CollectionConfig] = None):
        """初期化
        
        Args:
            config (Optional[CollectionConfig]): 収集設定
        """
        self.config = config or CollectionConfig()
        self.api_client = DmmApiClient()
        self.db = PersonDatabase()
        self.downloader = DmmImageDownloader()
        
        # 処理済みディレクトリの管理ファイル
        self.processed_file = Path("data/processed_dmm_directories.json")
        self._processed_dirs: Optional[set] = None
        
        logger.info("DMM女優画像収集クラスを初期化しました")
    
    def collect_actress_images(self, person_id: int) -> CollectionResult:
        """女優の顔画像を収集
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            CollectionResult: 収集結果
        """
        start_time = time.time()
        
        try:
            # 1. 女優情報取得
            actress_info = self._get_actress_info(person_id)
            if not actress_info:
                return CollectionResult(
                    status=CollectionStatus.ERROR,
                    actress_name=f"person_id_{person_id}",
                    error_message="女優情報が見つかりません",
                    processing_time=time.time() - start_time
                )
            
            logger.info(f"女優画像収集開始: {actress_info.name} (ID: {person_id})")
            
            # 2. 前提条件チェック
            status_check = self._check_prerequisites(actress_info)
            if status_check != CollectionStatus.SUCCESS:
                return CollectionResult(
                    status=status_check,
                    actress_name=actress_info.name,
                    error_message=self._get_status_message(status_check),
                    processing_time=time.time() - start_time
                )
            
            # 3. 処理済みチェック
            if self._is_already_processed(actress_info.name):
                return CollectionResult(
                    status=CollectionStatus.ALREADY_PROCESSED,
                    actress_name=actress_info.name,
                    error_message="既に処理済みです",
                    processing_time=time.time() - start_time
                )
            
            # 4. DMM API商品検索
            api_response = self.api_client.search_actress_products(
                actress_info.dmm_actress_id,
                self.config.dmm_products_limit
            )
            
            if not api_response or not api_response.has_products:
                return CollectionResult(
                    status=CollectionStatus.NO_VALID_IMAGES,
                    actress_name=actress_info.name,
                    error_message="商品が見つかりません",
                    processing_time=time.time() - start_time
                )
            
            # 5. 顔画像収集・保存
            saved_faces = self._collect_and_save_faces(actress_info, api_response.products)
            
            # 6. 処理済みマーク
            self._mark_as_processed(actress_info.name)
            
            processing_time = time.time() - start_time
            
            if saved_faces:
                logger.info(f"収集完了: {actress_info.name} - {len(saved_faces)}枚保存")
                return CollectionResult(
                    status=CollectionStatus.SUCCESS,
                    actress_name=actress_info.name,
                    total_products=len(api_response.products),
                    processed_images=len(api_response.products),
                    saved_faces=saved_faces,
                    processing_time=processing_time
                )
            else:
                return CollectionResult(
                    status=CollectionStatus.NO_VALID_IMAGES,
                    actress_name=actress_info.name,
                    total_products=len(api_response.products),
                    processed_images=len(api_response.products),
                    error_message="有効な顔画像が見つかりませんでした",
                    processing_time=processing_time
                )
        
        except Exception as e:
            logger.error(f"収集中にエラーが発生: {str(e)}")
            return CollectionResult(
                status=CollectionStatus.ERROR,
                actress_name=getattr(actress_info, 'name', f"person_id_{person_id}"),
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _get_actress_info(self, person_id: int) -> Optional[ActressInfo]:
        """女優情報を取得
        
        Args:
            person_id (int): 人物ID
            
        Returns:
            Optional[ActressInfo]: 女優情報
        """
        try:
            person_detail = self.db.get_person_detail(person_id)
            if not person_detail:
                return None
            
            # 基準画像パスをローカルパスに変換
            base_image_path = self._convert_to_local_path(
                person_detail['name'], 
                person_detail['image_path']
            )
            
            return ActressInfo(
                person_id=person_detail['person_id'],
                name=person_detail['name'],
                dmm_actress_id=person_detail['dmm_actress_id'],
                base_image_path=base_image_path
            )
        except Exception as e:
            logger.error(f"女優情報取得エラー: {str(e)}")
            return None
    
    def _convert_to_local_path(self, actress_name: str, original_path: Optional[str] = None) -> Optional[str]:
        """基準画像パスをローカルパスに変換
        
        Args:
            actress_name (str): 女優名
            original_path (Optional[str]): 元のパス（URL形式の可能性あり）
            
        Returns:
            Optional[str]: ローカルファイルパス
        """
        try:
            # original_pathは将来の拡張用に残すが、現在は使用しない
            _ = original_path  # 未使用変数警告を回避
            
            # ローカルパスを構築
            local_path = Path(f"data/images/base/{actress_name}/base.jpg")
            
            # ファイル存在確認
            if local_path.exists():
                return str(local_path)
            
            # ファイルが存在しない場合はNone
            logger.warning(f"基準画像ファイルが存在しません: {local_path}")
            return None
            
        except Exception as e:
            logger.error(f"ローカルパス変換エラー: {str(e)}")
            return None
    
    def _check_prerequisites(self, actress_info: ActressInfo) -> CollectionStatus:
        """前提条件をチェック
        
        Args:
            actress_info (ActressInfo): 女優情報
            
        Returns:
            CollectionStatus: チェック結果
        """
        if not actress_info.has_dmm_id:
            return CollectionStatus.NO_DMM_ID
        
        if not actress_info.has_base_image:
            return CollectionStatus.NO_BASE_IMAGE
        
        # 基準画像ファイルの存在確認
        if not Path(actress_info.base_image_path).exists():
            return CollectionStatus.NO_BASE_IMAGE
        
        return CollectionStatus.SUCCESS
    
    def _get_status_message(self, status: CollectionStatus) -> str:
        """ステータスメッセージを取得"""
        messages = {
            CollectionStatus.NO_DMM_ID: "DMM女優IDが設定されていません",
            CollectionStatus.NO_BASE_IMAGE: "基準画像が設定されていないか、ファイルが存在しません",
            CollectionStatus.API_ERROR: "DMM API エラーが発生しました"
        }
        return messages.get(status, "不明なエラー")
    
    def _is_already_processed(self, actress_name: str) -> bool:
        """処理済みかチェック
        
        Args:
            actress_name (str): 女優名
            
        Returns:
            bool: 処理済みの場合True
        """
        save_dir = Path(self.config.get_save_directory(actress_name))
        
        # ディレクトリ存在チェック
        if not save_dir.exists():
            return False
        
        # search-dmm-* ファイルの存在チェック
        dmm_files = list(save_dir.glob("search-dmm-*"))
        return len(dmm_files) > 0
    
    def _mark_as_processed(self, actress_name: str):
        """処理済みマークを設定"""
        # 実際の処理は _is_already_processed でファイル存在を確認するため
        # このメソッドでは特別な処理は不要
        logger.debug(f"処理済みマーク: {actress_name}")
    
    def _collect_and_save_faces(self, actress_info: ActressInfo, products: List) -> List[SavedFaceInfo]:
        """顔画像を収集・保存
        
        Args:
            actress_info (ActressInfo): 女優情報
            products (List): 商品リスト
            
        Returns:
            List[SavedFaceInfo]: 保存された顔情報リスト
        """
        saved_faces = []
        
        # 基準顔エンコーディング取得
        base_encoding = self._get_base_encoding(actress_info.base_image_path)
        if base_encoding is None:
            logger.error(f"基準画像のエンコーディング取得に失敗: {actress_info.base_image_path}")
            return saved_faces
        
        # 保存ディレクトリ作成
        save_dir = Path(self.config.get_save_directory(actress_info.name))
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 商品画像を順次処理
        for product in products:
            if len(saved_faces) >= self.config.max_faces_per_actress:
                break
            
            # 複数女優商品はスキップ
            if not product.is_single_actress:
                logger.info(f"複数女優商品のためスキップ: {product.content_id} (女優数: {product.actress_count})")
                continue
            
            try:
                face_result = self._extract_actress_face(
                    product.primary_image_url,
                    base_encoding,
                    actress_info.name,
                    product.content_id
                )
                
                if face_result.is_valid:
                    saved_info = self._save_face_image(
                        face_result.face_image_data,
                        actress_info.name,
                        face_result.similarity_score,
                        product.primary_image_url,
                        product.content_id
                    )
                    
                    if saved_info:
                        saved_faces.append(saved_info)
                        logger.info(f"顔画像保存成功: {saved_info.file_path} (類似度: {face_result.similarity_score:.3f})")
                
            except Exception as e:
                logger.warning(f"商品画像処理エラー: {product.content_id} - {str(e)}")
                continue
        
        return saved_faces
    
    def _get_base_encoding(self, base_image_path: str) -> Optional[np.ndarray]:
        """基準画像のエンコーディングを取得
        
        Args:
            base_image_path (str): 基準画像パス
            
        Returns:
            Optional[np.ndarray]: 顔エンコーディング
        """
        try:
            image = face_utils.load_image(base_image_path)
            if image is None:
                return None
            
            encodings, _ = face_utils.detect_faces(image)
            if len(encodings) != 1:
                logger.error(f"基準画像に1つの顔が必要です: {len(encodings)}個検出")
                return None
            
            return encodings[0]
        
        except Exception as e:
            logger.error(f"基準画像エンコーディング取得エラー: {str(e)}")
            return None
    
    def _extract_actress_face(self, image_url: str, base_encoding: np.ndarray, 
                             actress_name: str = "", product_id: str = "") -> FaceExtractionResult:
        """商品画像から女優の顔を抽出
        
        Args:
            image_url (str): 商品画像URL
            base_encoding (np.ndarray): 基準顔エンコーディング
            actress_name (str): 女優名（商品画像保存用）
            product_id (str): 商品ID（商品画像保存用）
            
        Returns:
            FaceExtractionResult: 抽出結果
        """
        try:
            # 画像ダウンロード
            image_data = self.downloader.download_image(image_url)
            if not image_data:
                return FaceExtractionResult(
                    success=False,
                    face_image_data=None,
                    similarity_score=0.0,
                    error_message="画像ダウンロードに失敗"
                )
            
            # 商品画像を保存（設定で有効な場合）
            if self.config.save_product_images and actress_name and product_id:
                self._save_product_image(image_data, actress_name, product_id, image_url)
            
            # PIL Image に変換
            pil_image = Image.open(BytesIO(image_data))
            image_array = np.array(pil_image)
            original_width = image_array.shape[1]  # 元の画像幅を保存
            
            # face_recognitionライブラリはRGB uint8画像を期待するため、形状とデータ型を確認
            if len(image_array.shape) == 2:
                # グレースケール画像の場合はRGBに変換
                image_array = np.stack([image_array] * 3, axis=-1)
                logger.debug("グレースケール画像をRGBに変換しました")
            elif len(image_array.shape) == 3 and image_array.shape[2] == 4:
                # RGBA画像の場合はRGBに変換
                image_array = image_array[:, :, :3]
                logger.debug("RGBA画像をRGBに変換しました")
            
            # データ型をuint8に確実に変換
            if image_array.dtype != np.uint8:
                # float型の場合は0-1範囲を0-255範囲に変換
                if image_array.dtype in [np.float32, np.float64]:
                    if image_array.max() <= 1.0:
                        image_array = (image_array * 255).astype(np.uint8)
                    else:
                        image_array = image_array.astype(np.uint8)
                else:
                    image_array = image_array.astype(np.uint8)
                logger.debug(f"画像データ型をuint8に変換しました")
            
            # 3次元RGB形状を確認
            if len(image_array.shape) != 3 or image_array.shape[2] != 3:
                logger.error(f"画像形状が不正です: {image_array.shape}")
                return FaceExtractionResult(
                    success=False,
                    face_image_data=None,
                    similarity_score=0.0,
                    error_message=f"画像形状が不正です: {image_array.shape}"
                )
            
            # メモリレイアウトを連続にする（face_recognitionライブラリの要件）
            if not image_array.flags['C_CONTIGUOUS']:
                image_array = np.ascontiguousarray(image_array)
                logger.debug("画像配列をC連続にしました")
            
            logger.debug(f"最終画像形状: {image_array.shape}, データ型: {image_array.dtype}, C連続: {image_array.flags['C_CONTIGUOUS']}")
            
            # 顔検出（エラーハンドリング強化）
            try:
                encodings, locations = face_utils.detect_faces(image_array)
            except Exception as face_detection_error:
                logger.error(f"顔検出でエラーが発生: {str(face_detection_error)}")
                logger.error(f"画像詳細: shape={image_array.shape}, dtype={image_array.dtype}, min={image_array.min()}, max={image_array.max()}")
                
                # 代替手段: PIL経由で再読み込みしてRGBに確実に変換
                try:
                    pil_image_rgb = pil_image.convert('RGB')
                    image_array = np.array(pil_image_rgb)
                    original_width = image_array.shape[1]  # 元の画像幅を再保存
                    
                    # C連続配列に変換
                    image_array = np.ascontiguousarray(image_array, dtype=np.uint8)
                    logger.info("PIL RGB変換による修復を試行中...")
                    
                    encodings, locations = face_utils.detect_faces(image_array)
                    logger.info("PIL RGB変換による修復が成功しました")
                    
                except Exception as retry_error:
                    logger.error(f"PIL RGB変換による修復も失敗: {str(retry_error)}")
                    return FaceExtractionResult(
                        success=False,
                        face_image_data=None,
                        similarity_score=0.0,
                        error_message=f"顔検出エラー: {str(face_detection_error)}"
                    )
            
            if not encodings:
                return FaceExtractionResult(
                    success=False,
                    face_image_data=None,
                    similarity_score=0.0,
                    error_message="顔が検出されませんでした"
                )
            
            # 類似度による顔選択（右側の顔を優先）
            best_similarity = 0.0
            best_face_data = None
            
            # 各顔の類似度と位置を記録
            face_candidates = []
            
            for encoding, location in zip(encodings, locations):
                # 類似度計算
                distance = np.linalg.norm(base_encoding - encoding)
                similarity_score = similarity.sigmoid_similarity(distance)
                
                if similarity_score >= self.config.similarity_threshold:
                    top, right, bottom, left = location
                    face_center_x = (left + right) / 2  # 顔の中心X座標
                    
                    face_candidates.append({
                        'similarity': similarity_score,
                        'location': location,
                        'center_x': face_center_x,
                        'encoding': encoding
                    })
            
            # 右側の顔を優先的に選択
            if face_candidates:
                if self.config.prioritize_right_faces:
                    # 右側の顔を優先: 類似度0.1以上の差がない場合は右側を選択
                    face_candidates.sort(key=lambda x: (-x['center_x'], -x['similarity']))
                    logger.debug(f"右側優先モード: {len(face_candidates)}個の顔候補から選択")
                    
                    # 最も右側の顔を基準に、類似度が大きく劣らないものを選択
                    rightmost_face = face_candidates[0]
                    
                    for candidate in face_candidates:
                        # 類似度の差が0.1以下なら右側を優先
                        if rightmost_face['similarity'] - candidate['similarity'] <= 0.1:
                            if candidate['center_x'] >= rightmost_face['center_x']:
                                rightmost_face = candidate
                    
                    selected_face = rightmost_face
                    logger.debug(f"選択された顔: 中心X={selected_face['center_x']:.1f}, 類似度={selected_face['similarity']:.3f}")
                else:
                    # 類似度のみで選択
                    selected_face = max(face_candidates, key=lambda x: x['similarity'])
                    logger.debug(f"類似度優先モード: 類似度={selected_face['similarity']:.3f}")
                
                # 選択された顔を切り出し
                top, right, bottom, left = selected_face['location']
                face_crop = image_array[top:bottom, left:right]
                
                # PIL Image に変換してバイトデータ化
                face_pil = Image.fromarray(face_crop)
                face_bytes = BytesIO()
                face_pil.save(face_bytes, format='JPEG', quality=95)
                
                best_similarity = selected_face['similarity']
                best_face_data = face_bytes.getvalue()
            
            if best_face_data:
                return FaceExtractionResult(
                    success=True,
                    face_image_data=best_face_data,
                    similarity_score=best_similarity
                )
            else:
                return FaceExtractionResult(
                    success=False,
                    face_image_data=None,
                    similarity_score=best_similarity,
                    error_message=f"類似度が閾値({self.config.similarity_threshold})を下回りました"
                )
        
        except Exception as e:
            logger.error(f"顔抽出エラー: {str(e)}")
            return FaceExtractionResult(
                success=False,
                face_image_data=None,
                similarity_score=0.0,
                error_message=str(e)
            )
    
    def _save_face_image(self, face_data: bytes, actress_name: str, 
                        similarity_score: float, source_url: str, content_id: str) -> Optional[SavedFaceInfo]:
        """顔画像を保存
        
        Args:
            face_data (bytes): 顔画像データ
            actress_name (str): 女優名
            similarity_score (float): 類似度スコア
            source_url (str): 元画像URL
            content_id (str): 商品ID
            
        Returns:
            Optional[SavedFaceInfo]: 保存情報
        """
        try:
            # 保存ディレクトリ
            save_dir = Path(self.config.get_save_directory(actress_name))
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 一時ファイルに保存してハッシュ計算
            temp_path = save_dir / "temp_face.jpg"
            with open(temp_path, 'wb') as f:
                f.write(face_data)
            
            # ハッシュ計算
            hash_value = image_utils.calculate_image_hash(str(temp_path))
            if not hash_value:
                temp_path.unlink(missing_ok=True)
                return None
            
            # 最終ファイル名
            filename = self.config.get_filename(content_id, hash_value[:12], "jpg")
            final_path = save_dir / filename
            
            # 重複チェック
            if final_path.exists():
                temp_path.unlink(missing_ok=True)
                logger.info(f"重複画像のためスキップ: {final_path}")
                return None
            
            # ファイル名変更
            temp_path.rename(final_path)
            
            return SavedFaceInfo(
                file_path=str(final_path),
                hash_value=hash_value,
                similarity_score=similarity_score,
                source_url=source_url
            )
        
        except Exception as e:
            logger.error(f"画像保存エラー: {str(e)}")
            return None
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """収集統計を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        stats = {
            "total_actresses": 0,
            "processed_actresses": 0,
            "total_images": 0,
            "config": self.config.__dict__
        }
        
        try:
            # 全女優数取得
            all_persons = self.db.get_all_persons()
            stats["total_actresses"] = len(all_persons)
            
            # 処理済み女優数とファイル数カウント
            processed_count = 0
            total_images = 0
            
            for person in all_persons:
                if person['dmm_actress_id']:
                    actress_name = person['name']
                    save_dir = Path(self.config.get_save_directory(actress_name))
                    
                    if save_dir.exists():
                        dmm_files = list(save_dir.glob("search-dmm-*"))
                        if dmm_files:
                            processed_count += 1
                            total_images += len(dmm_files)
            
            stats["processed_actresses"] = processed_count
            stats["total_images"] = total_images
            
        except Exception as e:
            logger.error(f"統計取得エラー: {str(e)}")
        
        return stats
    
    def _save_product_image(self, image_data: bytes, actress_name: str, 
                           product_id: str, source_url: str = ""):
        """商品画像を保存
        
        Args:
            image_data (bytes): 画像データ
            actress_name (str): 女優名
            product_id (str): 商品ID
            source_url (str): 元URL
        """
        try:
            # source_urlは現在使用していないが、将来の拡張のために残す
            _ = source_url  # 未使用変数警告を回避
            
            # 商品画像保存ディレクトリ作成
            product_dir = Path(self.config.get_product_images_directory(actress_name))
            product_dir.mkdir(parents=True, exist_ok=True)
            
            # ファイル名生成（商品IDベース）
            filename = f"product-{product_id}.jpg"
            file_path = product_dir / filename
            
            # 重複チェック
            if file_path.exists():
                logger.debug(f"商品画像は既に存在します: {file_path}")
                return
            
            # 画像保存
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"商品画像保存成功: {file_path}")
            
        except Exception as e:
            logger.error(f"商品画像保存エラー: {str(e)}")
    
    def close(self):
        """リソースを閉じる"""
        self.db.close()
        logger.info("DMM女優画像収集クラスを終了しました")