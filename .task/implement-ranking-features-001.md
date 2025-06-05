# 検索結果のランキング機能実装

Date: 2024-12-19
Status: In-Progress

## Request
検索APIを実行して1位になった女優のランキング機能を実装する

## Objective
- 検索API実行時に自動的に1位結果を記録
- ランキングAPI実装（勝利回数順）
- ルートページフッターにランキング表示（名前、サムネイル、回数）

## Action Plan
- [x] データベース設計と実装
  - [x] `search_history`テーブル（検索履歴記録）
  - [x] `person_ranking`テーブル（ランキング集計）
- [x] ファイル分離による責任分離
  - [x] `search_database.py`（検索履歴管理）
  - [x] `ranking_database.py`（ランキング集計管理）
- [x] 検索API修正
  - [x] 検索完了後、`search_database`に直接記録
  - [x] 1位結果を`ranking_database`に反映
- [x] ランキングAPI実装
  - [x] GET /api/ranking（ランキング取得）
  - [x] GET /api/ranking/stats（統計情報）
  - [x] GET /api/ranking/history（検索履歴）
- [x] person_idベースに修正
  - [x] actress_name → person_id変更
  - [x] personsテーブルとのJOIN実装
- [x] 類似度関連フィールドの削除
  - [x] total_similarity, average_similarity削除
  - [x] 勝利回数のみでランキング管理
- [ ] フロントエンド実装
  - [ ] ルートページフッターでのランキング表示
  - [ ] 名前、サムネイル、勝利回数の表示

## Execution Log

### 2024-12-19 15:30:00
- 初期設計：検索結果表示のUI カスタマイズ機能として誤解していたが、ユーザー要求はAPIの1位結果記録によるランキング機能だった

### 2024-12-19 15:45:00
- データベース設計：`ranking_database.py`に検索履歴とランキング集計を含む構造で実装
- 検索API修正：`/api/search`実行時にランキングデータベースに自動記録する仕組み実装
- 拡張要求：1-3位全てを記録する仕様に変更

### 2024-12-19 16:15:00
- ファイル分離リファクタリング実施
  - `search_database.py`：検索履歴専用（search_historyテーブル管理）
  - `ranking_database.py`：ランキング集計専用（person_rankingテーブル管理）
- `routes/search.py`修正：直接データベースクラスを呼び出すクリーンな構造に変更
- `routes/ranking.py`修正：分離されたデータベース構造に対応

### 2024-12-19 16:30:00
- person_idベースへの全面的な修正実施
  - `actress_name` → `person_id`への変更
  - `actress_ranking` → `person_ranking`テーブル名変更
  - personsテーブルとのJOINによる名前取得
  - 外部キー制約の追加（データ整合性向上）
  - Pydanticモデルの適切な修正

### 2024-12-19 16:45:00
- 不要な類似度関連フィールドの削除
  - `total_similarity`, `average_similarity`カラム削除
  - シンプルに勝利回数（`win_count`）のみでランキング管理
  - `update_ranking()`メソッドからsimilarityパラメータ削除
  - 統計情報からaverage_similarity関連削除

### 実装完了項目
- [x] データベース層の責任分離
- [x] 検索API自動記録機能（1-3位全記録、1位のみランキング反映）
- [x] ランキングAPI実装（3エンドポイント）
- [x] エラーハンドリング強化（データベースエラーが検索結果を阻害しない設計）
- [x] 既存データベース設計との整合性確保（person_idベース）
- [x] 人物の代表画像取得機能（ランキング表示用）
- [x] シンプルな勝利回数ベースのランキング（類似度計算不要）

### 次のステップ
- フロントエンド実装（ルートページフッター）
- 画像パスの表示機能（ランキングでのサムネイル表示）
