/**
 * 商品関連のAPI取得関数
 * React Server Componentで使用される取得系API
 */

import { createLogger } from "@/lib/logger";
import type {
  DmmProductsResponse,
  PersonProductsResponse,
  ProductApiStatusResponse,
} from "./types";

const logger = createLogger("Products");

/**
 * 人物IDから関連商品を取得
 * React Server Componentで使用
 *
 * @param personId - 人物ID
 * @param limit - 取得件数（1-20、デフォルト10）
 * @returns 商品情報またはnull
 */
export async function getProductsByPersonId(
  personId: number,
  limit = 10,
): Promise<PersonProductsResponse | null> {
  try {
    logger.info("商品取得開始", { personId, limit });

    // Docker内部ネットワークを使用
    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const url = `${API_BASE_URL}/api/products/${personId}?limit=${Math.min(limit, 20)}`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      next: { revalidate: 86400 }, // 1日（24時間）キャッシュ
    });

    if (!response.ok) {
      if (response.status === 404) {
        logger.warn("人物が見つかりません", { personId });
        return null;
      }
      if (response.status === 400) {
        logger.warn("DMM女優IDが設定されていません", { personId });
        return null;
      }

      logger.error("商品取得APIリクエストが失敗", {
        personId,
        status: response.status,
        statusText: response.statusText,
      });
      return null;
    }

    const data: PersonProductsResponse = await response.json();
    logger.info("商品取得成功", {
      personId,
      personName: data.person_name,
      productCount: data.total_count,
    });

    return data;
  } catch (error) {
    logger.error("商品取得中にエラーが発生", { personId, limit, error });
    return null;
  }
}

/**
 * DMM女優IDから関連商品を直接取得
 * React Server Componentで使用
 *
 * @param dmmActressId - DMM女優ID
 * @param limit - 取得件数（1-20、デフォルト10）
 * @returns 商品情報またはnull
 */
export async function getProductsByDmmId(
  dmmActressId: number,
  limit = 10,
): Promise<DmmProductsResponse | null> {
  try {
    logger.info("DMM商品取得開始", { dmmActressId, limit });

    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const url = `${API_BASE_URL}/api/products/by-dmm-id/${dmmActressId}?limit=${Math.min(limit, 20)}`;

    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      logger.error("DMM商品取得APIリクエストが失敗", {
        dmmActressId,
        status: response.status,
        statusText: response.statusText,
      });
      return null;
    }

    const data: DmmProductsResponse = await response.json();
    logger.info("DMM商品取得成功", {
      dmmActressId,
      productCount: data.total_count,
    });

    return data;
  } catch (error) {
    logger.error("DMM商品取得中にエラーが発生", { dmmActressId, limit, error });
    return null;
  }
}

/**
 * 商品取得APIの状態を確認
 * React Server Componentで使用
 *
 * @returns API状態情報またはnull
 */
export async function getProductApiStatus(): Promise<ProductApiStatusResponse | null> {
  try {
    logger.info("商品取得API状態確認開始");

    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const url = `${API_BASE_URL}/api/products/status`;

    const response = await fetch(url, {
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      logger.error("商品API状態確認リクエストが失敗", {
        status: response.status,
        statusText: response.statusText,
      });
      return null;
    }

    const data: ProductApiStatusResponse = await response.json();
    logger.info("商品API状態確認完了", {
      apiConfigured: data.api_configured,
      apiAccessible: data.api_accessible,
      testMessage: data.test_message,
    });

    return data;
  } catch (error) {
    logger.error("商品API状態確認中にエラーが発生", { error });
    return null;
  }
}
