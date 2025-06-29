import { logger } from "@/lib/logger";

export interface ActressDetail {
  person_id: number;
  name: string;
  image_path: string;
  search_count: number;
  dmm_list_url_digital?: string;
}

export interface AffiliateProduct {
  id: number;
  title: string;
  image: string;
  link: string;
}

/**
 * 女優詳細情報を取得
 * @param personId - 人物ID
 * @returns 女優詳細情報
 */
export async function getActressDetail(personId: number): Promise<ActressDetail> {
  try {
    logger.info("女優詳細情報を取得中", { personId });

    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    const response = await fetch(`${API_BASE_URL}/api/persons/${personId}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      next: { revalidate: 86400 }, // 1日（24時間）キャッシュ
    });

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`女優ID ${personId} が見つかりません`);
      }
      throw new Error(`API エラー: ${response.status}`);
    }

    const data = await response.json();
    logger.info("女優詳細情報を取得しました", { data });

    return data;
  } catch (error) {
    logger.error("女優詳細情報の取得に失敗しました", { error, personId });
    throw error;
  }
}

/**
 * ダミーのアフィリエイト商品リストを生成
 * @param actressName - 女優名
 * @returns ダミー商品リスト
 */
export function getDummyAffiliateProducts(actressName: string): AffiliateProduct[] {
  return [
    {
      id: 1,
      title: `${actressName} FANZA 商品ダミー1`,
      image: "/images/dummy_product1.jpg",
      link: "#",
    },
    {
      id: 2,
      title: `${actressName} FANZA 商品ダミー2`,
      image: "/images/dummy_product2.jpg",
      link: "#",
    },
    {
      id: 3,
      title: `${actressName} FANZA 商品ダミー3`,
      image: "/images/dummy_product3.jpg",
      link: "#",
    },
  ];
}
