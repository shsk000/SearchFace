"""
画像収集機能のテストスクリプト
"""

from image import ImageCollector
from pathlib import Path

def main():
    # 画像収集クラスのインスタンス化
    collector = ImageCollector()
    
    # 基準画像ディレクトリのパス
    base_dir = Path("data/images/base")
    
    # 基準画像ディレクトリ内の各人物ディレクトリを処理
    for person_dir in base_dir.iterdir():
        if not person_dir.is_dir():
            continue
            
        # 人物名を取得
        person_name = person_dir.name
        base_image_path = person_dir / "base.jpg"
        
        if not base_image_path.exists():
            print(f"警告: 基準画像が見つかりません: {base_image_path}")
            continue
        
        print(f"\n{person_name}の画像収集を開始します")
        
        # 画像の収集（3枚を目標）
        collected_count = collector.collect_images_for_person(
            person_name=person_name,
            base_image_path=str(base_image_path),
            target_count=3
        )
        
        print(f"{person_name}の収集完了: {collected_count}枚の画像を収集しました")

if __name__ == "__main__":
    main() 