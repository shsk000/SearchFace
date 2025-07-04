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
- results: 検索結果のリスト（最大5件）
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
import os
import uvicorn
from dotenv import load_dotenv
from utils import log_utils
from utils.r2_uploader import download_database_files
from src.api.main import app

load_dotenv('/etc/secrets/.env')

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

def start_server(host: str, port: int, debug: bool = False):
    """サーバーを起動する

    Args:
        host (str): ホストアドレス
        port (int): ポート番号
        debug (bool): デバッグモード（ホットリロード）の有効/無効
    """
    logger.info(f"顔画像の類似検索APIを起動します（{host}:{port}）")

    # 開発環境の場合のみホットリロードを有効化
    reload = debug
    reload_dirs = ["src"] if debug else None

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        reload_dirs=reload_dirs,
        log_level="info"
    )

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="顔画像の類似検索API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="ホストアドレス（デフォルト: 0.0.0.0）")
    parser.add_argument("--port", type=int, default=10000, help="ポート番号（デフォルト: 10000）")
    parser.add_argument("--sync-db", type=bool, default=False, help="データベースを同期するかどうか（デフォルト: False）")

    args = parser.parse_args()

    if args.sync_db:
        logger.info("データベースを同期します")
        download_database_files()

    # 環境変数からデバッグモードを取得
    debug = os.getenv("DEBUG", "false").lower() == "true"

    # サーバーを起動
    start_server(args.host, args.port, debug)

if __name__ == "__main__":
    main()
