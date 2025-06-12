"""
DMM API関連のデータモデル定義

このモジュールは、DMM APIのレスポンスデータや
女優画像収集に関連するデータモデルを定義します。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np


class CollectionStatus(Enum):
    """収集ステータス"""
    SUCCESS = "success"
    ALREADY_PROCESSED = "already_processed"
    NO_DMM_ID = "no_dmm_id"
    NO_BASE_IMAGE = "no_base_image"
    API_ERROR = "api_error"
    NO_VALID_IMAGES = "no_valid_images"
    ERROR = "error"


@dataclass
class ActressInfo:
    """女優情報"""
    person_id: int
    name: str
    dmm_actress_id: Optional[int]
    base_image_path: Optional[str]
    
    @property
    def has_dmm_id(self) -> bool:
        """DMM女優IDが設定されているかチェック"""
        return self.dmm_actress_id is not None
    
    @property
    def has_base_image(self) -> bool:
        """基準画像パスが設定されているかチェック"""
        return self.base_image_path is not None and self.base_image_path.strip() != ""


@dataclass
class DmmImageInfo:
    """DMM商品画像情報"""
    list_url: str       # リストページ用画像URL
    small_url: str      # 小サイズ画像URL  
    large_url: str      # 大サイズ画像URL（メイン使用）


@dataclass
class DmmProduct:
    """DMM商品情報"""
    content_id: str
    title: str
    image_info: DmmImageInfo
    actress_count: int = 1  # 出演女優数
    
    @property
    def primary_image_url(self) -> str:
        """メイン画像URLを取得（大サイズを優先）"""
        return self.image_info.large_url
    
    @property
    def is_single_actress(self) -> bool:
        """単一女優の商品かチェック"""
        return self.actress_count == 1


@dataclass
class DmmApiResponse:
    """DMM APIレスポンス"""
    status: int
    result_count: int
    total_count: int
    products: List[DmmProduct]
    
    @property
    def has_products(self) -> bool:
        """商品が存在するかチェック"""
        return len(self.products) > 0


@dataclass
class FaceExtractionResult:
    """顔抽出結果"""
    success: bool
    face_image_data: Optional[bytes]
    similarity_score: float
    error_message: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """有効な顔画像かチェック"""
        return self.success and self.face_image_data is not None


@dataclass
class SavedFaceInfo:
    """保存された顔画像情報"""
    file_path: str
    hash_value: str
    similarity_score: float
    source_url: str
    face_encoding: Optional[np.ndarray] = None  # 顔エンコーディング（FAISS登録用）
    image_id: Optional[int] = None  # face_imagesテーブルのimage_id


@dataclass
class CollectionResult:
    """収集結果"""
    status: CollectionStatus
    actress_name: str
    total_products: int = 0
    processed_images: int = 0
    saved_faces: List[SavedFaceInfo] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        """初期化後処理"""
        if self.saved_faces is None:
            self.saved_faces = []
    
    @property
    def success_count(self) -> int:
        """成功した保存数"""
        return len(self.saved_faces)
    
    @property
    def is_success(self) -> bool:
        """収集が成功したかチェック"""
        return self.status == CollectionStatus.SUCCESS and self.success_count > 0
    
    def add_saved_face(self, face_info: SavedFaceInfo):
        """保存された顔情報を追加"""
        self.saved_faces.append(face_info)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "status": self.status.value,
            "actress_name": self.actress_name,
            "total_products": self.total_products,
            "processed_images": self.processed_images,
            "success_count": self.success_count,
            "saved_faces": [
                {
                    "file_path": face.file_path,
                    "hash_value": face.hash_value,
                    "similarity_score": face.similarity_score,
                    "source_url": face.source_url
                }
                for face in self.saved_faces
            ],
            "error_message": self.error_message,
            "processing_time": self.processing_time
        }


@dataclass
class CollectionConfig:
    """収集設定"""
    # 類似度閾値（既存ImageCollectorの設定を活用）
    similarity_threshold: float = 0.55
    
    # 最大収集数
    max_faces_per_actress: int = 3
    
    # DMM API設定
    dmm_products_limit: int = 10
    
    # タイムアウト設定
    request_timeout: int = 30
    retry_count: int = 3
    retry_delay: int = 1
    
    # 保存設定
    save_directory_template: str = "data/images/dmm/{actress_name}"
    filename_template: str = "search-dmm-{content_id}-{hash}.{extension}"
    
    # 商品画像保存設定
    save_product_images: bool = False
    product_images_subdir: str = "products"
    
    # 画像処理設定
    prioritize_right_faces: bool = True  # 右側の顔を優先的に選択する
    
    def get_save_directory(self, actress_name: str) -> str:
        """保存ディレクトリパスを取得"""
        return self.save_directory_template.format(actress_name=actress_name)
    
    def get_filename(self, content_id: str, hash_value: str, extension: str) -> str:
        """ファイル名を取得"""
        return self.filename_template.format(content_id=content_id, hash=hash_value, extension=extension)
    
    def get_product_images_directory(self, actress_name: str) -> str:
        """商品画像保存ディレクトリパスを取得"""
        base_dir = self.get_save_directory(actress_name)
        return f"{base_dir}/{self.product_images_subdir}"