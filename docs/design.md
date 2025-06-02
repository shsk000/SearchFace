# フロントエンド設計仕様

## ディレクトリ構造

```
frontend/
├── src/
│   ├── actions/          # サーバーアクション
│   │   └── search.ts     # 画像検索アクション
│   ├── components/       # 再利用可能なUIコンポーネント
│   │   └── ui/          # shadcn/uiコンポーネント
│   ├── features/        # 機能単位のコンポーネント
│   │   ├── image-upload/ # 画像アップロード機能
│   │   │   └── ImageUploadZone.tsx
│   │   └── background/  # 背景画像機能
│   │       └── BackgroundImages.tsx
│   └── app/            # ページコンポーネント
│       └── page.tsx    # トップページ
```

## コンポーネント設計

### 機能コンポーネント（features）

#### ImageUploadZone
- 画像のドラッグ＆ドロップ
- 画像のプレビュー表示
- 検索ボタン
- Props:
  - `onImageSelect`: 画像選択時のコールバック
  - `onSearch`: 検索実行時のコールバック
  - `selectedImage`: 選択された画像ファイル
  - `previewUrl`: プレビュー画像のURL

#### BackgroundImages
- 背景画像のグリッド表示
- レスポンシブなグリッドレイアウト
- 画像の最適化（lazy loading, blur effect）
- オーバーレイによる視認性の向上

### 再利用可能なUIコンポーネント（components）

#### Button
- shadcn/uiのボタンコンポーネント
- カスタマイズ可能なスタイル

#### Card
- shadcn/uiのカードコンポーネント
- 検索結果の表示に使用

## サーバーアクション

### searchImage
- 画像検索APIを呼び出す
- FormDataを使用して画像を送信
- 環境変数 `NEXT_PUBLIC_API_URL` でAPIエンドポイントを設定

## 環境変数

### 開発環境（.env.local）
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 本番環境（Vercel）
- Vercelのダッシュボードで環境変数を設定
- `NEXT_PUBLIC_API_URL` に本番環境のAPIエンドポイントを設定

## 注意事項

1. 環境変数
   - `.env.local` はGitにコミットしない
   - `.env.example` で必要な環境変数を共有

2. コンポーネントの責務
   - `features/`: 特定の機能を実装するコンポーネント
   - `components/`: 再利用可能なUIコンポーネント

3. 型定義
   - すべてのPropsに型を定義
   - 環境変数の型チェック 