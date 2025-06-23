/**
 * 商品一覧のPresentationalコンポーネント
 * UIの表示のみを担当
 */

import { ProductCard } from "@/components/search/ProductCard";
import type { DmmProduct, PersonProductsResponse } from "../types";

interface ProductsListPresentationProps {
  productsData: PersonProductsResponse | null;
  className?: string;
  error?: string;
}

/**
 * 商品が存在しない場合のフォールバックUI
 */
function NoProductsMessage() {
  return (
    <div className="text-center py-8">
      <p className="text-zinc-400 text-sm">この女優の関連商品は現在取得できません</p>
    </div>
  );
}

/**
 * エラー状態のUI
 */
function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="text-center py-8">
      <p className="text-red-400 text-sm">{message}</p>
    </div>
  );
}

/**
 * 商品一覧のタイトル
 */
function ProductsTitle({
  personName,
  productCount,
}: {
  personName: string;
  productCount: number;
}) {
  return (
    <div className="mb-6">
      <h3 className="text-xl font-bold text-white mb-2">{personName}さんの関連商品</h3>
      <p className="text-zinc-400 text-sm">{productCount}件の商品が見つかりました</p>
    </div>
  );
}

/**
 * 商品カードリスト
 */
function ProductCardList({ products }: { products: DmmProduct[] }) {
  return (
    <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-zinc-600 scrollbar-track-zinc-800">
      {products.map((product, index) => (
        <ProductCard
          key={`${product.title}-${index}`}
          product={product}
          className="flex-shrink-0"
        />
      ))}
    </div>
  );
}

/**
 * 商品一覧のPresentationalコンポーネント（メイン）
 */
export function ProductsListPresentation({
  productsData,
  className,
  error,
}: ProductsListPresentationProps) {
  // エラーが発生している場合
  if (error) {
    return (
      <div className={className}>
        <ErrorMessage message={error} />
      </div>
    );
  }

  // データが取得できない場合
  if (!productsData) {
    return (
      <div className={className}>
        <NoProductsMessage />
      </div>
    );
  }

  // 商品が存在しない場合
  if (productsData.total_count === 0) {
    return (
      <div className={className}>
        <ProductsTitle personName={productsData.person_name} productCount={0} />
        <NoProductsMessage />
      </div>
    );
  }

  // 商品リストを表示
  return (
    <div className={className}>
      <ProductsTitle
        personName={productsData.person_name}
        productCount={productsData.total_count}
      />
      <ProductCardList products={productsData.products} />
    </div>
  );
}
