# SearchFace API仕様

## 概要
SearchFace APIは、顔画像の類似検索を提供するRESTful APIです。FastAPIフレームワークを使用して実装されています。

## 基本情報
- ベースURL: `http://localhost:10000`
- APIバージョン: 1.0.0
- 対応形式: JSON

## エンドポイント

### ヘルスチェック
APIの稼働状態を確認します。

#### リクエスト
- メソッド: `GET`
- エンドポイント: `/`

#### レスポンス
```json
{
  "status": "ok",
  "message": "SearchFace API is running"
}
```

### 顔画像検索
顔画像をアップロードし、類似する顔を検索します。

#### リクエスト
- メソッド: `POST`
- エンドポイント: `/api/search`
- Content-Type: `multipart/form-data`
- パラメータ:
  - `image`: 画像ファイル（必須）
    - 対応形式: JPEG, PNG, BMP
    - 最大サイズ: 10MB

#### レスポンス
```json
{
  "results": [
    {
      "name": "人物名",
      "similarity": 0.95,
      "distance": 0.05,
      "image_path": "path/to/image.jpg"
    }
  ],
  "processing_time": 0.123
}
```

##### レスポンスフィールド
- `results`: 検索結果のリスト（最大3件）
  - `name`: 人物名
  - `similarity`: 類似度（0-1の範囲）
  - `distance`: 距離値
  - `image_path`: 画像パス
- `processing_time`: 処理時間（秒）

#### エラーレスポンス
- 400 Bad Request
  ```json
  {
    "detail": "無効な画像ファイル: [エラー詳細]"
  }
  ```
  ```json
  {
    "detail": "画像から顔を検出できませんでした"
  }
  ```

## 起動方法
```bash
# 基本的な使用
python src/run_api.py

# ポート指定
python src/run_api.py --port 8080

# ホスト指定
python src/run_api.py --host 127.0.0.1

# データベース同期付き
python src/run_api.py --sync-db
```

## 注意事項
1. パフォーマンス
   - 応答時間は500ms以内を目標としています
   - 画像サイズは10MB以下に制限してください

2. セキュリティ
   - 本番環境ではCORSの設定を適切に行ってください
   - 認証・認可の実装を検討してください

3. エラーハンドリング
   - 画像の読み込みに失敗した場合は400エラーを返却
   - 顔が検出できない場合は400エラーを返却

4. データベース
   - 初回起動時は`--sync-db`オプションを使用してデータベースを同期してください
   - データベースファイルは自動的にダウンロードされます 