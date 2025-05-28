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
"""

import os
import argparse
from pathlib import Path
from image.collector import ImageCollector
from utils import log_utils

# ロギングの初期化
log_utils.setup_logging()
logger = log_utils.get_logger(__name__)

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

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="画像収集スクリプト")
    parser.add_argument("--target", help="処理対象のディレクトリ名")
    args = parser.parse_args()
    
    base_dir = "data/images/base"
    process_directory(base_dir, args.target)

if __name__ == "__main__":
    main()
