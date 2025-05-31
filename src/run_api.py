"""
顔画像の類似検索API起動スクリプト

このスクリプトは以下の機能を提供します：
1. FastAPIベースの顔画像類似検索APIを起動
2. 画像アップロードによる顔検索機能の提供
3. 検索結果をJSON形式で返却

使用方法：
- 基本的な使用: python src/run_api.py
- ポート指定: python src/run_api.py --port 8080
- ホスト指定: python src/run_api.py --host 127.0.0.1

APIエンドポイント：
- POST /api/search: 画像をアップロードして類似顔を検索

レスポンス形式：
- results: 検索結果のリスト（最大3件）
  - name: 人物名
  - similarity: 類似度（0-1の範囲）
  - image_path: 画像パス
  - metadata: メタデータ（存在する場合）
- processing_time: 処理時間（秒）

注意事項：
- 入力画像から顔が検出できない場合はエラーを返却
- 応答時間は500ms以内を目標
"""

import argparse
from api.main import start as start_api
from utils import log_utils

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="顔画像の類似検索API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="ホストアドレス（デフォルト: 0.0.0.0）")
    parser.add_argument("--port", type=int, default=8000, help="ポート番号（デフォルト: 8000）")
    
    args = parser.parse_args()
    
    logger.info(f"顔画像の類似検索APIを起動します（{args.host}:{args.port}）")
    
    # APIの起動
    start_api(host=args.host, port=args.port)

if __name__ == "__main__":
    main()
