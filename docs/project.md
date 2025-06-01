# SearchFace プロジェクト設定

## プロジェクト概要
- プロジェクト名: SearchFace
- 目的: 顔画像の類似度検索システム
- 主要技術: Python, FAISS, SQLite, face_recognition

> 注意: プロジェクトの詳細な設定は [docs/project.md](./docs/project.md) を参照してください。
> Python開発に関する詳細な設定は [docs/python.md](./docs/python.md) を参照してください。
> データベースに関する詳細な設定は [docs/db.md](./docs/db.md) を参照してください。

## ディレクトリ構成
```
SearchFace/
├── .cursorrules          # プロジェクト設定
├── requirements.txt      # 依存関係ファイル
├── data/                 # データディレクトリ
│   ├── images/          # 顔画像保存用
│   │   ├── base/       # 基準画像ディレクトリ
│   │   │   └── 人物名/  # 人物ごとのディレクトリ
│   │   │       └── base.jpg  # 基準画像
│   │   └── collected/  # 収集した画像ディレクトリ
│   │       └── 人物名/  # 人物ごとのディレクトリ
│   │           ├── 人物名_N.jpg  # 有効な画像
│   │           └── all_images/   # 無効な画像
│   ├── face_database.db # SQLiteデータベース
│   └── face.index       # FAISSインデックス
├── src/                 # ソースコード
│   ├── database/        # データベース関連
│   │   ├── __init__.py
│   │   ├── face_database.py  # 顔データベース管理
│   │   └── db_utils.py       # データベースユーティリティ
│   ├── face/           # 顔認識関連
│   │   ├── __init__.py
│   │   ├── face_comparison.py # 顔比較処理
│   │   └── face_utils.py      # 顔認識ユーティリティ
│   ├── image/          # 画像処理関連
│   │   ├── __init__.py
│   │   ├── collector.py       # 画像収集
│   │   ├── download.py        # 画像ダウンロード
│   │   ├── search.py          # 画像検索
│   │   └── storage.py         # 画像保存
│   ├── utils/          # 共通ユーティリティ
│   │   ├── __init__.py
│   │   └── similarity.py      # 類似度計算
│   ├── main.py         # メインスクリプト
│   └── test_image_collector.py # 画像収集テスト
├── tests/              # テストコード
└── docs/               # ドキュメント
    ├── design.md      # 設計資料
    └── api.md         # API仕様
```

## 顔データ管理ルール
- 1人につき複数枚の画像を登録可能
- 画像ファイル形式: .jpg, .jpeg, .png
- 画像ファイル名: 人物名.jpg
- メタデータ: JSON形式で保存
- 同一画像の重複登録は防止

## 注意事項
- 顔データの取り扱いには注意が必要
- プライバシー保護に配慮
- データベースの整合性を維持
- パフォーマンスに注意（大量データ処理時） 