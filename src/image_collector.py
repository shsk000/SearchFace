"""
画像収集機能のテストスクリプト
"""

from image import ImageCollector
from pathlib import Path
import sys

def main():
    try:
        # 画像収集クラスのインスタンス化
        collector = ImageCollector()
        
        # 基準画像ディレクトリのパス
        base_dir = Path("data/images/base")
        
        if not base_dir.exists():
            print(f"エラー: 基準画像ディレクトリが見つかりません: {base_dir}")
            sys.exit(1)
        
        # 処理対象のディレクトリ一覧を表示
        person_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
        print(f"\n処理対象の人物数: {len(person_dirs)}")
        for d in person_dirs:
            print(f"- {d.name}")
        
        # 基準画像ディレクトリ内の各人物ディレクトリを処理
        for person_dir in person_dirs:
            try:
                # 人物名を取得
                person_name = person_dir.name
                base_image_path = person_dir / "base.jpg"
                
                if not base_image_path.exists():
                    print(f"警告: 基準画像が見つかりません: {base_image_path}")
                    continue
                
                print(f"\n{'='*50}")
                print(f"{person_name}の画像収集を開始します")
                print(f"基準画像: {base_image_path}")
                
                # 画像の収集（3枚を目標）
                collected_count = collector.collect_images_for_person(
                    person_name=person_name,
                    base_image_path=str(base_image_path),
                    target_count=3
                )
                
                print(f"{person_name}の収集完了: {collected_count}枚の画像を収集しました")
                print(f"{'='*50}\n")
                
            except Exception as e:
                print(f"エラー: {person_name}の処理中にエラーが発生しました: {str(e)}")
                continue

    except Exception as e:
        print(f"エラー: プログラムの実行中にエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 