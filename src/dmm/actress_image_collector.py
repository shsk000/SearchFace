"""
DMM API 女優画像収集クラス

DMM APIから商品画像を取得し、顔検出・類似度計算を行って
女優の顔写真を収集・保存する機能を提供します。
"""

import time
import traceback
import json
from datetime import datetime
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
from src.database.face_index_database import FaceIndexDatabase
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
        self.face_db = FaceIndexDatabase()
        self.downloader = DmmImageDownloader()
        
        # 処理済みディレクトリの管理ファイル
        self.processed_file = Path("data/processed_dmm_directories.json")
        self._processed_dirs: Optional[set] = None
        
        # エラーログファイル
        self.error_log_path = Path("data/dmm_collection_errors.log")
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 画像保存失敗ログファイル
        self.failed_save_log_path = Path("data/dmm_failed_saves.log")
        self.failed_save_log_path.parent.mkdir(parents=True, exist_ok=True)
        
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
            
            # 3. 処理済みチェック（強制実行フラグが有効でない場合のみ）
            if not self.config.force_reprocess and self._is_already_processed(actress_info.name):
                return CollectionResult(
                    status=CollectionStatus.ALREADY_PROCESSED,
                    actress_name=actress_info.name,
                    error_message="既に処理済みです",
                    processing_time=time.time() - start_time
                )
            
            # 4. 複数回検索による顔画像収集
            saved_faces, total_products_searched = self._collect_faces_with_pagination(actress_info)
            
            # 6. 処理済みマーク
            self._mark_as_processed(actress_info.name)
            
            processing_time = time.time() - start_time
            
            if saved_faces:
                logger.info(f"収集完了: {actress_info.name} - {len(saved_faces)}枚保存")
                return CollectionResult(
                    status=CollectionStatus.SUCCESS,
                    actress_name=actress_info.name,
                    total_products=total_products_searched,
                    processed_images=total_products_searched,
                    saved_faces=saved_faces,
                    processing_time=processing_time
                )
            else:
                return CollectionResult(
                    status=CollectionStatus.NO_VALID_IMAGES,
                    actress_name=actress_info.name,
                    total_products=total_products_searched,
                    processed_images=total_products_searched,
                    error_message="有効な顔画像が見つかりませんでした",
                    processing_time=processing_time
                )
        
        except Exception as e:
            logger.error(f"収集中にエラーが発生: {str(e)}")
            
            # エラーログファイルに詳細を出力
            self._log_error_to_file(
                error_type="collection_error",
                error_message=str(e),
                traceback_info=traceback.format_exc(),
                actress_info=actress_info,
                person_id=person_id
            )
            
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
            
            # 基準画像パスを取得（URL形式）
            base_image_path = self._get_base_image_path(
                person_detail['name'], 
                person_detail['base_image_path']
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
    
    def _get_base_image_path(self, actress_name: str, original_path: Optional[str] = None) -> Optional[str]:
        """基準画像パスを取得（URL形式をそのまま返す）
        
        Args:
            actress_name (str): 女優名
            original_path (Optional[str]): 元のパス（URL形式）
            
        Returns:
            Optional[str]: 基準画像パス（URL）
        """
        try:
            # URL形式の場合はそのまま返す
            if original_path and original_path.startswith(('http://', 'https://')):
                return original_path
            
            # URLでない場合はエラー
            logger.warning(f"基準画像URLが無効です: actress={actress_name}, path={original_path}")
            return None
            
        except Exception as e:
            logger.error(f"基準画像パス取得エラー: {str(e)}")
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
        
        # 基準画像がURL形式でない場合はエラー
        if not actress_info.base_image_path.startswith(('http://', 'https://')):
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
    
    def _collect_and_save_faces(self, actress_info: ActressInfo, products: List, max_collect: Optional[int] = None) -> List[SavedFaceInfo]:
        """顔画像を収集・保存
        
        Args:
            actress_info (ActressInfo): 女優情報
            products (List): 商品リスト
            max_collect (Optional[int]): 最大収集数（Noneの場合は設定値を使用）
            
        Returns:
            List[SavedFaceInfo]: 保存された顔情報リスト
        """
        saved_faces = []
        
        # 最大収集数の決定
        target_count = max_collect if max_collect is not None else self.config.max_faces_per_actress
        
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
            if len(saved_faces) >= target_count:
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
                    # 顔エンコーディングを取得（FaceExtractionResultから）
                    face_encoding = getattr(face_result, 'face_encoding', None)
                    
                    saved_info = self._save_face_image(
                        face_result.face_image_data,
                        actress_info.name,
                        face_result.similarity_score,
                        product.primary_image_url,
                        product.content_id,
                        face_encoding
                    )
                    
                    if saved_info:
                        saved_faces.append(saved_info)
                        logger.info(f"顔画像保存成功: {saved_info.file_path} (類似度: {face_result.similarity_score:.3f})")
                    else:
                        # 画像保存に失敗した場合のログ記録
                        self._log_failed_save(
                            actress_info=actress_info,
                            content_id=product.content_id,
                            image_url=product.primary_image_url,
                            similarity_score=face_result.similarity_score,
                            reason="image_save_failed"
                        )
                
            except Exception as e:
                logger.warning(f"商品画像処理エラー: {product.content_id} - {str(e)}")
                
                # 処理エラーの場合もログ記録
                self._log_failed_save(
                    actress_info=actress_info,
                    content_id=product.content_id,
                    image_url=product.primary_image_url,
                    reason="processing_error",
                    error_message=str(e)
                )
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
            
            # PIL Image に変換し、確実にRGB形式にする
            pil_image = Image.open(BytesIO(image_data))
            pil_image_rgb = pil_image.convert('RGB')
            image_array = np.array(pil_image_rgb, dtype=np.uint8)
            
            # メモリレイアウトを連続にする（face_recognitionライブラリの要件）
            image_array = np.ascontiguousarray(image_array)
            logger.debug("画像をRGB形式に変換し、C連続配列にしました")
            
            logger.debug(f"最終画像形状: {image_array.shape}, データ型: {image_array.dtype}, C連続: {image_array.flags['C_CONTIGUOUS']}")
            
            # 顔検出
            try:
                encodings, locations = face_utils.detect_faces(image_array)
            except Exception as face_detection_error:
                logger.error(f"顔検出でエラーが発生: {str(face_detection_error)}")
                logger.error(f"画像詳細: shape={image_array.shape}, dtype={image_array.dtype}, min={image_array.min()}, max={image_array.max()}")
                
                # エラーログファイルに詳細を出力
                self._log_error_to_file(
                    error_type="face_detection_error",
                    error_message=f"顔検出エラー: {str(face_detection_error)}",
                    traceback_info=traceback.format_exc(),
                    actress_name=actress_name,
                    product_id=product_id,
                    additional_info={
                        "image_url": image_url
                    }
                )
                
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
                
                # 選択された顔を切り出し（余白を追加して顎なども含める）
                top, right, bottom, left = selected_face['location']
                
                # 顔領域を拡張（設定値に基づいた余白を追加）
                face_height = bottom - top
                face_width = right - left
                
                # 拡張サイズを計算
                expand_height = int(face_height * self.config.face_expand_ratio)
                expand_width = int(face_width * self.config.face_expand_ratio)
                
                # 画像境界を考慮して拡張
                img_height, img_width = image_array.shape[:2]
                expanded_top = max(0, top - expand_height)
                expanded_bottom = min(img_height, bottom + expand_height)
                expanded_left = max(0, left - expand_width)
                expanded_right = min(img_width, right + expand_width)
                
                face_crop = image_array[expanded_top:expanded_bottom, expanded_left:expanded_right]
                
                logger.debug(f"顔切り出し - 元の領域: ({top},{left})-({bottom},{right}), "
                           f"拡張後: ({expanded_top},{expanded_left})-({expanded_bottom},{expanded_right})")
                
                # PIL Image に変換してバイトデータ化
                face_pil = Image.fromarray(face_crop)
                
                # 顔画像のサイズを確認し、小さすぎる場合はリサイズ
                min_face_size = self.config.min_face_size  # 設定値から最小サイズを取得
                face_width, face_height = face_pil.size
                
                if face_width < min_face_size or face_height < min_face_size:
                    # アスペクト比を保持してリサイズ
                    if face_width < face_height:
                        new_width = min_face_size
                        new_height = int((min_face_size / face_width) * face_height)
                    else:
                        new_height = min_face_size
                        new_width = int((min_face_size / face_height) * face_width)
                    
                    face_pil = face_pil.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.debug(f"顔画像をリサイズ: {face_width}x{face_height} -> {new_width}x{new_height}")
                
                face_bytes = BytesIO()
                face_pil.save(face_bytes, format='JPEG', quality=95)
                
                best_similarity = selected_face['similarity']
                best_face_data = face_bytes.getvalue()
                best_face_encoding = selected_face['encoding']  # 顔エンコーディングを保存
            
            if best_face_data:
                # FaceExtractionResultにface_encodingを追加
                result = FaceExtractionResult(
                    success=True,
                    face_image_data=best_face_data,
                    similarity_score=best_similarity
                )
                # 動的に属性を追加（FaceExtractionResultモデルを変更せずに済む）
                result.face_encoding = best_face_encoding
                return result
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
                        similarity_score: float, source_url: str, content_id: str,
                        face_encoding: Optional[np.ndarray] = None) -> Optional[SavedFaceInfo]:
        """顔画像を保存
        
        Args:
            face_data (bytes): 顔画像データ
            actress_name (str): 女優名
            similarity_score (float): 類似度スコア
            source_url (str): 元画像URL
            content_id (str): 商品ID
            face_encoding (Optional[np.ndarray]): 顔エンコーディング
            
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
            
            # FAISSデータベースに登録
            image_id = None
            if face_encoding is not None:
                try:
                    # 女優のperson_idを取得
                    person = self.db.get_person_by_name(actress_name)
                    if person:
                        person_id = person['person_id']
                        
                        # メタデータ作成
                        metadata = {
                            "source": "dmm_api",
                            "content_id": content_id,
                            "similarity_score": similarity_score,
                            "source_url": source_url,
                            "collection_date": time.time()
                        }
                        
                        # face_imagesテーブルとFAISSインデックスに追加
                        image_id = self.face_db.add_face_image(
                            person_id=person_id,
                            image_path=str(final_path),
                            encoding=face_encoding,
                            image_hash=hash_value,
                            metadata=metadata
                        )
                        
                        logger.info(f"FAISS登録成功: image_id={image_id}, person_id={person_id}")
                    else:
                        logger.warning(f"女優が見つかりません: {actress_name}")
                        
                except Exception as faiss_error:
                    logger.error(f"FAISS登録エラー: {str(faiss_error)}")
                    
                    # エラーログファイルに詳細を出力
                    self._log_error_to_file(
                        error_type="faiss_registration_error",
                        error_message=f"FAISS登録エラー: {str(faiss_error)}",
                        traceback_info=traceback.format_exc(),
                        actress_name=actress_name,
                        additional_info={
                            "content_id": content_id,
                            "file_path": str(final_path),
                            "hash_value": hash_value
                        }
                    )
                    # FAISS登録に失敗してもファイル保存は成功として扱う
            else:
                logger.warning("顔エンコーディングが無いためFAISS登録をスキップ")
            
            return SavedFaceInfo(
                file_path=str(final_path),
                hash_value=hash_value,
                similarity_score=similarity_score,
                source_url=source_url,
                face_encoding=face_encoding,
                image_id=image_id
            )
        
        except Exception as e:
            logger.error(f"画像保存エラー: {str(e)}")
            
            # エラーログファイルに詳細を出力
            self._log_error_to_file(
                error_type="image_save_error",
                error_message=f"画像保存エラー: {str(e)}",
                traceback_info=traceback.format_exc(),
                actress_name=actress_name,
                additional_info={
                    "content_id": content_id,
                    "source_url": source_url
                }
            )
            
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
    
    def _log_error_to_file(self, error_type: str, error_message: str, traceback_info: str,
                          actress_info: Optional[ActressInfo] = None, person_id: Optional[int] = None,
                          actress_name: Optional[str] = None, product_id: Optional[str] = None,
                          additional_info: Optional[Dict] = None):
        """エラー情報をファイルに記録
        
        Args:
            error_type (str): エラータイプ
            error_message (str): エラーメッセージ
            traceback_info (str): トレースバック情報
            actress_info (Optional[ActressInfo]): 女優情報
            person_id (Optional[int]): 人物ID
            actress_name (Optional[str]): 女優名
            product_id (Optional[str]): 商品ID
            additional_info (Optional[Dict]): 追加情報
        """
        try:
            # エラー情報をまとめる
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "error_message": error_message,
                "actress_info": {
                    "person_id": None,
                    "name": None,
                    "dmm_actress_id": None
                },
                "additional_info": additional_info or {},
                "traceback": traceback_info
            }
            
            # 女優情報を設定
            if actress_info:
                error_record["actress_info"]["person_id"] = actress_info.person_id
                error_record["actress_info"]["name"] = actress_info.name
                error_record["actress_info"]["dmm_actress_id"] = actress_info.dmm_actress_id
            elif person_id:
                error_record["actress_info"]["person_id"] = person_id
                if actress_name:
                    error_record["actress_info"]["name"] = actress_name
            elif actress_name:
                error_record["actress_info"]["name"] = actress_name
            
            # 商品IDがある場合は追加情報に含める
            if product_id:
                error_record["additional_info"]["product_id"] = product_id
            
            # ファイルに書き込み
            with open(self.error_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_record, ensure_ascii=False, indent=2))
                f.write('\n' + '='*80 + '\n')
                
            logger.debug(f"エラーログを記録: {self.error_log_path}")
            
        except Exception as log_error:
            logger.error(f"エラーログの記録に失敗: {str(log_error)}")
    
    def _log_failed_save(self, actress_info: ActressInfo, content_id: str, image_url: str,
                        reason: str, similarity_score: Optional[float] = None,
                        error_message: Optional[str] = None):
        """画像保存失敗情報をファイルに記録
        
        Args:
            actress_info (ActressInfo): 女優情報
            content_id (str): 商品ID
            image_url (str): 画像URL
            reason (str): 失敗理由
            similarity_score (Optional[float]): 類似度スコア
            error_message (Optional[str]): エラーメッセージ
        """
        try:
            # 保存失敗情報をまとめる
            failed_record = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "actress_info": {
                    "person_id": actress_info.person_id,
                    "name": actress_info.name,
                    "dmm_actress_id": actress_info.dmm_actress_id
                },
                "product_info": {
                    "content_id": content_id,
                    "image_url": image_url
                }
            }
            
            # オプション情報を追加
            if similarity_score is not None:
                failed_record["similarity_score"] = similarity_score
            
            if error_message:
                failed_record["error_message"] = error_message
            
            # ファイルに書き込み
            with open(self.failed_save_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(failed_record, ensure_ascii=False, indent=2))
                f.write('\n' + '-'*50 + '\n')
                
            logger.debug(f"保存失敗ログを記録: {self.failed_save_log_path}")
            
        except Exception as log_error:
            logger.error(f"保存失敗ログの記録に失敗: {str(log_error)}")
    
    def _collect_faces_with_pagination(self, actress_info) -> tuple[list, int]:
        """ページ分割検索による顔画像収集
        
        Args:
            actress_info: 女優情報
            
        Returns:
            tuple[list, int]: (保存された顔画像リスト, 検索した商品総数)
        """
        all_saved_faces = []
        total_products_searched = 0
        current_offset = 1
        
        logger.info(f"📄 複数回検索開始: {actress_info.name} - 目標枚数: {self.config.max_faces_per_actress}")
        
        for page in range(1, self.config.max_search_pages + 1):
            # 目標枚数に達した場合は終了
            if len(all_saved_faces) >= self.config.max_faces_per_actress:
                logger.info(f"✅ 目標枚数達成: {actress_info.name} - {len(all_saved_faces)}枚")
                break
            
            # 閾値チェック：最初のページまたは現在の枚数が閾値以下の場合のみ継続
            if page > 1 and len(all_saved_faces) > self.config.min_faces_threshold:
                logger.info(f"📊 閾値クリア: {actress_info.name} - {len(all_saved_faces)}枚収集済み、検索終了")
                break
            
            logger.info(f"📄 検索ページ {page}/{self.config.max_search_pages} - オフセット: {current_offset}")
            
            # DMM API商品検索
            api_response = self.api_client.search_actress_products(
                actress_info.dmm_actress_id,
                self.config.dmm_products_limit,
                current_offset
            )
            
            if not api_response or not api_response.has_products:
                logger.info(f"📭 商品なし: ページ{page}で商品が見つかりません")
                break
            
            total_products_searched += len(api_response.products)
            logger.info(f"🔍 検索結果: ページ{page} - {len(api_response.products)}件の商品")
            
            # このページの商品から顔画像収集
            page_saved_faces = self._collect_and_save_faces(
                actress_info, 
                api_response.products,
                max_collect=self.config.max_faces_per_actress - len(all_saved_faces)
            )
            
            if page_saved_faces:
                all_saved_faces.extend(page_saved_faces)
                logger.info(f"💾 ページ{page}収集結果: {len(page_saved_faces)}枚保存 (累計: {len(all_saved_faces)}枚)")
            else:
                logger.info(f"📭 ページ{page}: 有効な顔画像なし")
            
            # 次のページのオフセット計算
            current_offset += self.config.dmm_products_limit
            
            # APIレート制限対策
            if page < self.config.max_search_pages:
                time.sleep(0.5)
        
        logger.info(f"📊 複数回検索完了: {actress_info.name} - {len(all_saved_faces)}枚保存, {total_products_searched}商品検索")
        return all_saved_faces, total_products_searched
    
    def close(self):
        """リソースを閉じる"""
        self.db.close()
        self.face_db.close()
        logger.info("DMM女優画像収集クラスを終了しました")