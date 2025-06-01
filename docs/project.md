# SearchFace プロジェクト設定

## プロジェクト概要
- プロジェクト名: SearchFace
- 目的: 顔画像の類似度検索システム
- 主要技術: Python, FAISS, SQLite, face_recognition

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
  - `face_database.py`の`add_face`メソッドで実装
- 画像ファイル形式: .jpg, .jpeg, .png
  - `storage.py`で.jpg形式で保存
- 画像ファイル名: 人物名.jpg
  - `storage.py`の`save_image`メソッドで`{person_name}_{content_hash}.jpg`形式で保存
- メタデータ: JSON形式で保存
  - `face_database.py`の`add_face`メソッドでJSON形式で保存
- 同一画像の重複登録は防止
  - `face_database.py`の`face_images`テーブルで`image_hash`にUNIQUE制約
  - `storage.py`の`save_image`メソッドでハッシュ値による重複チェック

## 類似度検索設定
- 検索結果数: デフォルト5件
  - `face_database.py`の`search_similar_faces`メソッドで`top_k=5`をデフォルト値として設定
- 類似度計算方法: 距離ベース
  - FAISSの`IndexFlatL2`を使用してL2距離で計算
- 閾値設定:
  - 距離0.4以上: 異なる人物の可能性が高い（50%未満）
  - 距離0.6以上: ほぼ確実に異なる人物（0%）

## 画像収集設定
### 検索設定
- 検索エンジン: Google Custom Search API
  - `search.py`の`ImageSearcher`クラスで実装
- 検索クエリ: 人物名 + "av女優"
  - `search.py`の`search_images`メソッドで実装
- セーフサーチ: 無効（safe="off"）
  - `search.py`の`search_images`メソッドで設定
- 検索結果数: 10件
  - `search.py`の`search_images`メソッドで`num=10`をデフォルト値として設定

### 画像検証
- 類似度閾値: 0.55
  - `collector.py`の`ImageCollector`クラスで`self.similarity_threshold = 0.55`として設定
- 最大顔検出数: 1
  - `collector.py`の`ImageCollector`クラスで`self.max_faces_threshold = 1`として設定
- 検証項目:
  - 顔の検出: `face_utils.py`の`detect_faces`関数
  - 類似度の計算: `collector.py`の`validate_image`メソッド
  - 複数顔のチェック: `collector.py`の`validate_image`メソッド

### 画像保存
- 有効な画像: collected/人物名/人物名_N.jpg
- 無効な画像: collected/人物名/all_images/人物名_N_invalid.jpg
- 保存形式: JPEG
  - `storage.py`の`save_image`メソッドで実装

### エラーハンドリング
- タイムアウト設定:
  - 接続タイムアウト: 5秒
  - 読み取りタイムアウト: 30秒
  - `download.py`の`download_image`メソッドで`timeout=30`として設定
- リトライ設定:
  - 最大リトライ回数: 3回
  - リトライ間隔: 1秒
  - `download.py`の`download_image`メソッドで`max_retries=3`と`time.sleep(1)`として設定

## 注意事項
- 顔データの取り扱いには注意が必要
- プライバシー保護に配慮
- データベースの整合性を維持
- パフォーマンスに注意（大量データ処理時） 