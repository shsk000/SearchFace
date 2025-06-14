# SearchFace プロダクト要求仕様書 (PRD)

## 📋 プロダクト概要

### プロダクト名
**SearchFace** - AI顔画像類似検索システム

### プロダクトビジョン
「妄想が、確信に変わる。」
アップロードされた画像から高精度なAI技術を使用して類似する顔を瞬時に検索し、ユーザーの探索体験を革新する。

### ターゲットユーザー
- 18歳以上の成人ユーザー
- エンターテインメント分野での類似性検索に興味があるユーザー
- AI技術を使った画像検索サービスに関心があるユーザー

---

## 🎯 ビジネス目標

### 主要KPI
1. **ユーザーエンゲージメント**
   - 日次アクティブユーザー数（DAU）
   - 検索セッション数（1日あたり）
   - 平均検索回数/ユーザー

2. **技術パフォーマンス**
   - 検索レスポンス時間：< 500ms
   - 検索精度：類似度スコア85%以上
   - システム稼働率：99.9%以上

3. **ユーザー満足度**
   - 検索結果の満足度
   - サービス利用継続率

---

## 👥 ユーザーストーリー

### エピック1: 画像アップロードと検索
```
ユーザーとして、
画像をアップロードして類似する顔を検索したい
なぜなら、気になる人に似ている人を簡単に見つけたいから
```

**受け入れ基準:**
- [x] ドラッグ&ドロップで画像をアップロード可能
- [x] JPEG、PNG、BMP形式に対応
- [x] 画像サイズ制限：500KB以下
- [x] 単一顔のみ検出・検索
- [x] 検索結果を類似度順に表示

### エピック2: 検索結果の表示
```
ユーザーとして、
検索結果を見やすい形で確認したい
なぜなら、複数の候補を比較検討したいから
```

**受け入れ基準:**
- [x] 最大5件の検索結果を表示
- [x] 類似度スコア（パーセンテージ）表示
- [x] 人物名と画像の表示
- [x] 検索処理時間の表示

### エピック3: ランキング機能
```
ユーザーとして、
人気の検索結果ランキングを見たい
なぜなら、他のユーザーがよく検索している人物に興味があるから
```

**受け入れ基準:**
- [x] 人気ランキング表示
- [x] 検索回数ベースのランキング
- [x] リアルタイムランキング更新

---

## 🛠 機能要求仕様

### 1. 画像アップロード機能

#### 1.1 アップロード方式
- **ドラッグ&ドロップ**: メイン操作方法
- **ファイル選択**: ボタンクリックによる選択
- **ペースト機能**: クリップボードからの貼り付け

#### 1.2 対応形式と制限
| 項目 | 仕様 |
|------|------|
| ファイル形式 | JPEG, PNG, BMP |
| 最大ファイルサイズ | 500KB |
| 画像解像度 | 制限なし（自動リサイズ） |
| 顔検出要件 | 単一顔のみ（複数顔は要エラー） |

#### 1.3 バリデーション
- ファイル形式チェック
- ファイルサイズチェック
- 画像破損チェック
- 顔検出チェック（0個・複数個は要エラー）

### 2. 顔検索機能

#### 2.1 検索処理
```
入力: アップロード画像
処理: 
  1. 顔検出（face_recognition）
  2. 特徴量抽出（128次元ベクトル）
  3. FAISS類似検索
  4. 類似度計算（exponential method）
出力: 検索結果（上位5件）
```

#### 2.2 検索結果
| フィールド | 型 | 説明 |
|------------|-----|------|
| name | string | 人物名 |
| similarity | float | 類似度（0-100%） |
| distance | float | ベクトル距離 |
| image_path | string | 画像パス |

#### 2.3 パフォーマンス要件
- **応答時間**: < 500ms
- **同時検索**: 100リクエスト/秒
- **精度**: 類似度85%以上

### 3. ランキング機能

#### 3.1 ランキング集計
- **集計対象**: 検索で1位になった回数
- **更新タイミング**: リアルタイム
- **表示件数**: 上位10位まで

#### 3.2 ランキングデータ
| フィールド | 型 | 説明 |
|------------|-----|------|
| rank | integer | 順位 |
| person_name | string | 人物名 |
| win_count | integer | 1位獲得回数 |
| image_path | string | 代表画像パス |

### 4. 検索履歴機能

#### 4.1 履歴記録
- **記録内容**: 検索結果、処理時間、メタデータ
- **セッション管理**: ユニークID生成
- **保存期間**: 無期限（要検討）

#### 4.2 履歴取得API
```
GET /api/search/{session_id}
```
- 過去の検索結果を再取得可能
- セッションIDベースのアクセス

---

## 🏗 技術要求仕様

### アーキテクチャ概要
```
Frontend (Next.js 15) ←→ Backend (FastAPI) ←→ Database (SQLite + Turso)
                                     ↓
                              AI/ML (face_recognition + FAISS)
```

### 技術スタック

#### フロントエンド
| 技術 | バージョン | 用途 |
|------|------------|------|
| Next.js | 15.x | フレームワーク |
| React | 19.x | UIライブラリ |
| TypeScript | 5.x | 型安全性 |
| Tailwind CSS | 3.x | スタイリング |
| Radix UI | 1.x | UIコンポーネント |

#### バックエンド
| 技術 | バージョン | 用途 |
|------|------------|------|
| Python | 3.11+ | 実行環境 |
| FastAPI | 0.104+ | APIフレームワーク |
| face_recognition | 1.3+ | 顔検出・認識 |
| FAISS | 1.7+ | 類似検索エンジン |
| SQLite | 3.x | ローカルDB |
| Turso | - | クラウドDB |

#### インフラ・DevOps
| 技術 | 用途 |
|------|------|
| Docker | コンテナ化 |
| docker-compose | 開発環境 |
| Cloudflare R2 | 画像ストレージ |

### データベース設計

#### ローカルSQLite（顔認識コア）
```sql
-- 人物マスター
persons (person_id, name, created_at)

-- 顔画像データ
face_images (image_id, person_id, image_path, created_at)

-- FAISS インデックス
face_indexes (index_id, person_id, face_encoding, created_at)
```

#### Turso（検索履歴・ランキング）
```sql
-- 検索履歴
search_history (history_id, search_session_id, result_rank, person_id, person_name, distance, image_path, search_timestamp, metadata)

-- 人物ランキング
person_ranking (ranking_id, person_id, win_count, last_win_timestamp, created_at, updated_at)
```

### API仕様

#### 検索API
```
POST /api/search
Content-Type: multipart/form-data

Request:
- image: UploadFile (required)
- top_k: int = 5 (optional)

Response:
{
  "results": [
    {
      "name": "string",
      "similarity": "float",
      "distance": "float", 
      "image_path": "string"
    }
  ],
  "processing_time": "float",
  "search_session_id": "string"
}
```

#### ランキングAPI
```
GET /api/ranking?limit=10

Response:
{
  "ranking": [
    {
      "rank": "integer",
      "person_name": "string",
      "win_count": "integer",
      "image_path": "string"
    }
  ],
  "last_updated": "timestamp"
}
```

### セキュリティ要件

#### 画像処理セキュリティ
- ファイル形式厳密チェック
- ファイルサイズ制限（500KB）
- 画像メタデータ除去
- 一時ファイル自動削除

#### API セキュリティ
- CORS設定
- Rate Limiting
- エラーハンドリング
- ログ記録

#### データプライバシー
- 年齢制限（18歳以上）
- 著作権配慮の注意喚起
- アップロード画像の非保存

---

## 🚀 開発・運用要件

### 開発環境
```bash
# 環境構築
docker-compose up

# 開発サーバー
Frontend: http://localhost:3000
Backend: http://localhost:10000
API Docs: http://localhost:10000/docs
```

### テスト戦略

#### フロントエンド
- **Unit Tests**: vitest + React Testing Library
- **Integration Tests**: MSW (Mock Service Worker)
- **E2E Tests**: 要検討

#### バックエンド
- **Unit Tests**: pytest
- **Integration Tests**: FastAPI TestClient
- **Performance Tests**: 負荷テスト要実装

### CI/CD
- **Linting**: Biome (Frontend), flake8/black (Backend)
- **Type Checking**: TypeScript (Frontend), mypy (Backend)
- **Test Coverage**: 80%以上維持

### モニタリング
- **パフォーマンス**: 検索処理時間監視
- **エラー**: 異常系処理の監視
- **ユーザー行動**: 検索パターン分析

---

## 📅 リリース計画

### Phase 1: MVP (現在)
- [x] 基本的な顔検索機能
- [x] ランキング機能
- [x] 検索履歴記録

### Phase 2: 機能拡張
- [ ] 検索結果詳細ページ
- [ ] 個人プロフィール情報
- [ ] 検索フィルター機能

### Phase 3: 最適化
- [ ] 検索精度向上
- [ ] パフォーマンス最適化
- [ ] UI/UX改善

---

## ⚠️ リスク・制約事項

### 技術的リスク
1. **検索精度**: 顔認識の精度限界
2. **パフォーマンス**: 大規模データでの性能低下
3. **スケーラビリティ**: 同時アクセス増加への対応

### 法的・倫理的リスク
1. **著作権**: 画像の権利関係
2. **プライバシー**: 個人情報保護
3. **年齢制限**: 18歳未満アクセス防止

### 運用リスク
1. **サーバー負荷**: 急激なアクセス増加
2. **データ保護**: バックアップ・復旧
3. **セキュリティ**: 不正アクセス・攻撃

### 軽減策
- 適切な利用規約設定
- 技術的制限措置の実装
- 監視・アラート体制構築
- 定期的なセキュリティ監査

---

## 📊 成功指標

### 短期目標（3ヶ月）
- DAU: 1,000ユーザー
- 検索成功率: 95%
- 平均応答時間: 300ms以下

### 中期目標（6ヶ月）
- DAU: 10,000ユーザー
- 検索精度: 90%以上
- ユーザー満足度: 4.0/5.0以上

### 長期目標（1年）
- DAU: 50,000ユーザー
- 月間検索数: 1,000,000回
- サービス継続利用率: 60%以上

---

*このPRDは開発の進行に合わせて定期的に更新されます。*
*最終更新: 2024年12月*