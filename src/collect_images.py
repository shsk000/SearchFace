import os
from pathlib import Path
from image_collector import ImageCollector

def main():
    """メイン処理"""
    # 基準画像のディレクトリ
    base_dir = Path("data/images/base")
    if not base_dir.exists():
        print(f"エラー: 基準画像ディレクトリが存在しません: {base_dir}")
        return

    # 画像収集クラスの初期化
    collector = ImageCollector()
    
    # 基準画像ディレクトリ内の人物ディレクトリを処理
    total_collected = 0
    for person_dir in base_dir.iterdir():
        if not person_dir.is_dir():
            continue
            
        person_name = person_dir.name
        print(f"\n{person_name}の画像収集を開始します...")
        
        # 基準画像を探す（base.jpg, base.jpeg, base.png）
        base_images = []
        for ext in ['.jpg', '.jpeg', '.png']:
            base_image = person_dir / f"base{ext}"
            if base_image.exists():
                base_images.append(base_image)
        
        if not base_images:
            print(f"警告: {person_name}の基準画像が見つかりません")
            continue
            
        # 最初の基準画像を使用
        base_image_path = str(base_images[0])
        print(f"基準画像: {base_image_path}")
        
        # 画像の収集
        collected_count = collector.collect_images_for_person(person_name, base_image_path)
        total_collected += collected_count
        
        print(f"{person_name}の画像収集が完了しました")
        print(f"収集した画像数: {collected_count}")
    
    print(f"\n全体の結果:")
    print(f"収集した画像数: {total_collected}")

if __name__ == "__main__":
    main() 