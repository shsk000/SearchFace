"""
画像収集機能のテストスクリプト

このスクリプトは以下の処理を行います：
1. 指定されたディレクトリ（data/images/base）内の人物ディレクトリを処理
2. 各人物ディレクトリ内のbase.jpgを基準画像として使用
3. ImageCollectorクラスを使用して画像を収集
   - Google画像検索で画像を検索
   - 基準画像との類似度を計算
   - 有効な画像を保存
4. 1人あたり3枚の画像を収集

使用方法：
- 全ディレクトリの処理: python src/image_collector.py
- 特定のディレクトリの処理: python src/image_collector.py --target "人物名"
- 初回同期（処理済みとして記録）: python src/image_collector.py --init-sync
- 新規追加ディレクトリのみ処理: python src/image_collector.py --new-only
"""

import os
import json
import argparse
from pathlib import Path
from image.collector import ImageCollector
from utils import log_utils

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

class ProcessedDirectoryManager:
    """処理済みディレクトリ管理クラス"""
    
    def __init__(self, file_path="data/processed_directories.json"):
        """処理済みディレクトリ管理クラスの初期化
        
        Args:
            file_path (str): 処理済みディレクトリ情報を保存するJSONファイルのパス
        """
        self.file_path = file_path
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        """ファイルが存在しない場合は作成"""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self.save_processed_directories([])
    
    def get_processed_directories(self):
        """処理済みディレクトリのリストを取得
        
        Returns:
            list: 処理済みディレクトリ名のリスト
        """
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"処理済みディレクトリの読み込みに失敗: {str(e)}")
            return []
    
    def save_processed_directories(self, directories):
        """処理済みディレクトリのリストを保存
        
        Args:
            directories (list): 処理済みディレクトリ名のリスト
            
        Returns:
            bool: 保存の成功/失敗
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(directories, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"処理済みディレクトリの保存に失敗: {str(e)}")
            return False
    
    def add_processed_directory(self, directory_name):
        """処理済みディレクトリを追加
        
        Args:
            directory_name (str): 追加するディレクトリ名
            
        Returns:
            bool: 追加の成功/失敗
        """
        directories = self.get_processed_directories()
        if directory_name not in directories:
            directories.append(directory_name)
            return self.save_processed_directories(directories)
        return True
    
    def get_new_directories(self, all_directories):
        """新規ディレクトリのリストを取得
        
        Args:
            all_directories (list): 全ディレクトリ名のリスト
            
        Returns:
            list: 新規ディレクトリ名のリスト（処理済みでないもの）
        """
        processed = self.get_processed_directories()
        return [d for d in all_directories if d not in processed]

def process_directory(base_dir: str, target_dir: str = None):
    """指定されたディレクトリの画像を処理

    Args:
        base_dir (str): 基準画像のディレクトリ
        target_dir (str, optional): 処理対象のディレクトリ
    """
    collector = ImageCollector()
    base_path = Path(base_dir)
    
    if not base_path.exists():
        logger.error(f"基準画像ディレクトリが存在しません: {base_dir}")
        return
    
    logger.info(f"{base_dir}ディレクトリの画像を処理中...")
    
    # 指定されたディレクトリのみを処理
    if target_dir:
        target_path = base_path / target_dir
        if not target_path.exists():
            logger.error(f"指定されたディレクトリが存在しません: {target_dir}")
            return
        process_person_directory(collector, target_path)
    else:
        # すべてのディレクトリを処理
        for person_dir in base_path.iterdir():
            if person_dir.is_dir():
                process_person_directory(collector, person_dir)

def process_person_directory(collector: ImageCollector, person_dir: Path):
    """人物ディレクトリの処理

    Args:
        collector (ImageCollector): 画像収集クラスのインスタンス
        person_dir (Path): 人物ディレクトリのパス
    """
    logger.info(f"人物ディレクトリを処理中: {person_dir.name}")
    
    # 基準画像を探す
    base_image = None
    for image_file in person_dir.glob("*.jpg"):
        if image_file.name == "base.jpg":
            base_image = image_file
            break
    
    if not base_image:
        logger.error(f"基準画像が見つかりません: {person_dir}")
        return
    
    # 画像を収集
    collected_count = collector.collect_images_for_person(
        person_dir.name,
        str(base_image)
    )
    
    logger.info(f"収集完了: {person_dir.name} - {collected_count}枚の画像を収集")

def initialize_sync(base_dir):
    """すべてのディレクトリを処理済みとして記録（初回同期）
    
    Args:
        base_dir (str): 基準画像のディレクトリ
    """
    logger.info("初回同期を実行します...")
    
    # 処理済みディレクトリマネージャーの初期化
    dir_manager = ProcessedDirectoryManager()
    
    # 全ディレクトリの取得
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.error(f"基準画像ディレクトリが存在しません: {base_dir}")
        return
    
    # 現在のディレクトリリストを取得
    all_directories = [d.name for d in base_path.iterdir() if d.is_dir()]
    
    # すべてのディレクトリを処理済みとして記録
    dir_manager.save_processed_directories(all_directories)
    
    logger.info(f"初回同期完了: {len(all_directories)}個のディレクトリを処理済みとして記録しました")
    if all_directories:
        logger.info(f"記録されたディレクトリ: {', '.join(all_directories)}")
    else:
        logger.info("記録されたディレクトリはありません")

def process_new_directories(base_dir):
    """新規追加ディレクトリのみを処理
    
    Args:
        base_dir (str): 基準画像のディレクトリ
    """
    logger.info("新規追加ディレクトリのみを処理します...")
    
    # 処理済みディレクトリマネージャーの初期化
    dir_manager = ProcessedDirectoryManager()
    
    # 処理履歴ファイルが存在しない場合の処理
    if not os.path.exists(dir_manager.file_path):
        logger.error("処理履歴ファイルが存在しません。先に --init-sync オプションで初回同期を実行してください。")
        return
    
    # 全ディレクトリの取得
    base_path = Path(base_dir)
    if not base_path.exists():
        logger.error(f"基準画像ディレクトリが存在しません: {base_dir}")
        return
    
    # 現在のディレクトリリストを取得
    all_directories = [d.name for d in base_path.iterdir() if d.is_dir()]
    
    # 新規ディレクトリを取得
    new_directories = dir_manager.get_new_directories(all_directories)
    
    if not new_directories:
        logger.info("新規追加ディレクトリはありません。")
        return
    
    logger.info(f"新規追加ディレクトリ: {', '.join(new_directories)}")
    
    # 新規ディレクトリを処理
    collector = ImageCollector()
    for dir_name in new_directories:
        person_dir = base_path / dir_name
        process_person_directory(collector, person_dir)
        # 処理済みとして記録
        dir_manager.add_processed_directory(dir_name)

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="画像収集スクリプト")
    parser.add_argument("--target", help="処理対象のディレクトリ名")
    parser.add_argument("--new-only", action="store_true", help="新規追加ディレクトリのみを処理")
    parser.add_argument("--init-sync", action="store_true", 
                        help="初回同期：すべてのディレクトリを処理済みとしてマーク（実際の処理は行わない）")
    args = parser.parse_args()
    
    base_dir = "data/images/base"
    
    if args.init_sync:
        # 初回同期（検索なし、記録のみ）
        initialize_sync(base_dir)
    elif args.new_only:
        # 新規追加ディレクトリのみを処理
        process_new_directories(base_dir)
    else:
        # 従来の処理
        process_directory(base_dir, args.target)

if __name__ == "__main__":
    main()
