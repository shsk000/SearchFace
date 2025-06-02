from enum import Enum
from typing import Dict, Any

class ErrorCode(str, Enum):
    # 画像関連のエラー (1000-1999)
    INVALID_IMAGE_FORMAT = "E1001"  # 画像形式が無効
    IMAGE_TOO_LARGE = "E1002"      # 画像サイズが大きすぎる
    IMAGE_TOO_SMALL = "E1003"      # 画像サイズが小さすぎる
    NO_FACE_DETECTED = "E1004"     # 顔が検出されない
    MULTIPLE_FACES = "E1005"       # 複数の顔が検出された
    IMAGE_CORRUPTED = "E1006"      # 画像が破損している

    # リクエスト関連のエラー (2000-2999)
    INVALID_REQUEST = "E2001"      # リクエストが無効
    MISSING_PARAMETER = "E2002"    # 必須パラメータが不足
    INVALID_PARAMETER = "E2003"    # パラメータが無効

    # サーバー関連のエラー (3000-3999)
    INTERNAL_ERROR = "E3001"       # 内部サーバーエラー
    DATABASE_ERROR = "E3002"       # データベースエラー
    SERVICE_UNAVAILABLE = "E3003"  # サービス利用不可

# エラーコードとメッセージのマッピング
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    ErrorCode.INVALID_IMAGE_FORMAT: {
        "ja": "画像形式が無効です。JPG、PNG、WEBP形式の画像をアップロードしてください。",
        "en": "Invalid image format. Please upload JPG, PNG, or WEBP images."
    },
    ErrorCode.IMAGE_TOO_LARGE: {
        "ja": "画像サイズが大きすぎます。5MB以下の画像をアップロードしてください。",
        "en": "Image size is too large. Please upload images under 5MB."
    },
    ErrorCode.IMAGE_TOO_SMALL: {
        "ja": "画像サイズが小さすぎます。より大きな画像をアップロードしてください。",
        "en": "Image size is too small. Please upload a larger image."
    },
    ErrorCode.NO_FACE_DETECTED: {
        "ja": "画像から顔が検出されませんでした。顔が写っている画像をアップロードしてください。",
        "en": "No face detected in the image. Please upload an image with a face."
    },
    ErrorCode.MULTIPLE_FACES: {
        "ja": "画像に複数の顔が検出されました。1つの顔が写っている画像をアップロードしてください。",
        "en": "Multiple faces detected in the image. Please upload an image with a single face."
    },
    ErrorCode.IMAGE_CORRUPTED: {
        "ja": "画像が破損しているか、読み込めません。別の画像をアップロードしてください。",
        "en": "The image is corrupted or cannot be read. Please upload a different image."
    },
    ErrorCode.INVALID_REQUEST: {
        "ja": "リクエストが無効です。",
        "en": "Invalid request."
    },
    ErrorCode.MISSING_PARAMETER: {
        "ja": "必須パラメータが不足しています。",
        "en": "Missing required parameters."
    },
    ErrorCode.INVALID_PARAMETER: {
        "ja": "パラメータが無効です。",
        "en": "Invalid parameters."
    },
    ErrorCode.INTERNAL_ERROR: {
        "ja": "サーバーでエラーが発生しました。しばらく経ってから再度お試しください。",
        "en": "An internal server error occurred. Please try again later."
    },
    ErrorCode.DATABASE_ERROR: {
        "ja": "データベースエラーが発生しました。しばらく経ってから再度お試しください。",
        "en": "A database error occurred. Please try again later."
    },
    ErrorCode.SERVICE_UNAVAILABLE: {
        "ja": "サービスが一時的に利用できません。しばらく経ってから再度お試しください。",
        "en": "Service is temporarily unavailable. Please try again later."
    }
}

def get_error_response(error_code: ErrorCode, lang: str = "ja") -> Dict[str, Any]:
    """
    エラーコードに基づいてエラーレスポンスを生成する

    Args:
        error_code (ErrorCode): エラーコード
        lang (str): 言語コード（"ja" または "en"）

    Returns:
        Dict[str, Any]: エラーレスポンス
    """
    return {
        "error": {
            "code": error_code,
            "message": ERROR_MESSAGES[error_code][lang]
        }
    } 