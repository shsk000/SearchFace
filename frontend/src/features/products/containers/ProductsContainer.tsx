/**
 * 商品一覧のContainerコンポーネント
 * React Server Component - データ取得とビジネスロジックを担当
 */

import { createLogger } from "@/lib/logger";
import { getProductsByPersonId } from "../api";
import { ProductsListPresentation } from "../presentations/ProductsListPresentation";

const logger = createLogger("ProductsContainer");

interface ProductsContainerProps {
  personId: number;
  limit?: number;
  className?: string;
}

/**
 * 商品一覧のContainerコンポーネント
 * データ取得を行い、Presentationalコンポーネントに渡す
 */
export default async function ProductsContainer({
  personId,
  limit = 10,
  className,
}: ProductsContainerProps) {
  logger.info("商品一覧コンテナ開始", { personId, limit });

  try {
    // APIから商品データを取得
    const productsData = await getProductsByPersonId(personId, limit);

    logger.info("商品データ取得完了", {
      personId,
      hasData: !!productsData,
      productCount: productsData?.total_count || 0,
    });

    // Presentationalコンポーネントにデータを渡す
    return <ProductsListPresentation productsData={productsData} className={className} />;
  } catch (error) {
    logger.error("商品一覧コンテナでエラーが発生", { personId, error });

    // エラー状態をPresentationalコンポーネントに渡す
    return (
      <ProductsListPresentation
        productsData={null}
        className={className}
        error="商品情報の読み込み中にエラーが発生しました"
      />
    );
  }
}
