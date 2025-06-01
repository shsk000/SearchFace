"""
Cloudflare R2を使用したデータベースファイルのアップロード/ダウンロードスクリプト

環境変数の設定:
.envファイルに以下の環境変数を設定してください：

R2_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_access_key_id
R2_SECRET_ACCESS_KEY=your_secret_access_key
R2_BUCKET_NAME=your_bucket_name

実行例:
1. 環境変数の設定
   $ cp .env.example .env
   $ vim .env  # 環境変数を編集

2. データベースファイルのアップロード
   $ python src/utils/r2_uploader.py --action upload

3. データベースファイルのダウンロード
   $ python src/utils/r2_uploader.py --action download

注意事項:
- アップロード前にファイルの存在確認を行います
- ダウンロード時に必要なディレクトリは自動的に作成されます
- エラー発生時はログに詳細が出力されます
"""

import os
import boto3
from botocore.config import Config
import logging

# ロギングの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class R2Uploader:
    def __init__(self):
        """R2Uploaderの初期化"""
        logger.debug(f"R2_BUCKET_NAME: {os.getenv('R2_BUCKET_NAME')}")
        logger.debug(f"R2_ENDPOINT_URL: {os.getenv('R2_ENDPOINT_URL')}")
        logger.debug(f"R2_ACCESS_KEY_ID: {os.getenv('R2_ACCESS_KEY_ID')}")
        logger.debug(f"R2_SECRET_ACCESS_KEY: {os.getenv('R2_SECRET_ACCESS_KEY')}")
        
        self.s3 = boto3.client(
            's3',
            endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            config=Config(signature_version='s3v4'),
            region_name='auto'
        )
        self.bucket_name = os.getenv('R2_BUCKET_NAME')

    def upload_file(self, file_path: str, object_name: str = None) -> bool:
        """
        ファイルをR2にアップロードする
        
        Args:
            file_path: アップロードするファイルのパス
            object_name: R2上のオブジェクト名（指定しない場合はファイル名を使用）
            
        Returns:
            bool: アップロードが成功したかどうか
        """
        if not object_name:
            object_name = os.path.basename(file_path)

        try:
            logger.info(f"ファイルをアップロード中: {file_path} -> {object_name}")
            self.s3.upload_file(file_path, self.bucket_name, object_name)
            logger.info(f"アップロード成功: {object_name}")
            return True
        except Exception as e:
            logger.error(f"アップロード失敗: {str(e)}")
            return False

    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        R2からファイルをダウンロードする
        
        Args:
            object_name: R2上のオブジェクト名
            file_path: ダウンロード先のファイルパス
            
        Returns:
            bool: ダウンロードが成功したかどうか
        """
        try:
            logger.info(f"ファイルをダウンロード中: {object_name} -> {file_path}")
            logger.debug(f"バケット名: {self.bucket_name}")
            logger.debug(f"オブジェクト名: {object_name}")
            logger.debug(f"ファイルパス: {file_path}")
            self.s3.download_file(self.bucket_name, object_name, file_path)
            logger.info(f"ダウンロード成功: {file_path}")
            return True
        except Exception as e:
            logger.error(f"ダウンロード失敗: {str(e)}")
            return False

def upload_database_files():
    """データベースファイルをR2にアップロードする"""
    uploader = R2Uploader()
    
    # アップロードするファイルのリスト
    files_to_upload = [
        ('data/face_database.db', 'face_database.db'),
        ('data/face.index', 'face.index')
    ]
    
    # 各ファイルをアップロード
    for local_path, object_name in files_to_upload:
        if os.path.exists(local_path):
            uploader.upload_file(local_path, object_name)
        else:
            logger.error(f"ファイルが存在しません: {local_path}")

def download_database_files():
    """データベースファイルをR2からダウンロードする"""
    uploader = R2Uploader()
    
    # ダウンロードするファイルのリスト
    files_to_download = [
        ('face_database.db', 'data/face_database.db'),
        ('face.index', 'data/face.index')
    ]
    
    # 各ファイルをダウンロード
    for object_name, local_path in files_to_download:
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        uploader.download_file(object_name, local_path)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='R2データベースファイル管理')
    parser.add_argument('--action', choices=['upload', 'download'], required=True,
                      help='実行するアクション（upload: アップロード, download: ダウンロード）')
    
    args = parser.parse_args()
    
    if args.action == 'upload':
        upload_database_files()
    else:
        download_database_files() 