/**
 * 商品関連の型定義
 * バックエンドのAPI仕様に対応
 */

export interface DmmDelivery {
  type: string; // 配信タイプ (stream, download等)
  price: string; // 配信価格
}

export interface DmmPrices {
  price?: string; // 金額 (300～)
  list_price?: string; // 定価
  deliveries?: DmmDelivery[]; // 配信リスト
}

export interface DmmImageUrl {
  list: string; // リストページ用画像URL
  small: string; // 小サイズ画像URL
  large: string; // 大サイズ画像URL（メイン使用）
}

export interface DmmProduct {
  imageURL: DmmImageUrl;
  title: string;
  productURL: string; // アフィリエイトURL
  prices: DmmPrices;
}

// 人物別商品取得APIのレスポンス
export interface PersonProductsResponse {
  person_id: number;
  person_name: string;
  dmm_actress_id: number;
  products: DmmProduct[];
  total_count: number;
}

// DMM女優ID別商品取得APIのレスポンス
export interface DmmProductsResponse {
  dmm_actress_id: number;
  products: DmmProduct[];
  total_count: number;
}

// API状態確認のレスポンス
export interface ProductApiStatusResponse {
  api_configured: boolean;
  api_accessible: boolean;
  test_message: string;
}
