import { createLogger } from "@/lib/logger";
import type { ActressListResponse, ActressListParams } from "./types";

const logger = createLogger("ActressList");

/**
 * 女優一覧データを取得する
 */
export async function getActressList(params: ActressListParams = {}): Promise<ActressListResponse | null> {
  try {
    const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";
    
    // クエリパラメータを構築
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.offset) searchParams.append('offset', params.offset.toString());
    if (params.search) searchParams.append('search', params.search);
    if (params.sort_by) searchParams.append('sort_by', params.sort_by);
    
    const url = `${API_BASE_URL}/api/persons${searchParams.toString() ? `?${searchParams.toString()}` : ''}`;
    
    logger.info("女優一覧データを取得中", { url, params });
    
    const response = await fetch(url, {
      cache: "no-store"
    });
    
    if (!response.ok) {
      logger.error("女優一覧取得失敗", { 
        status: response.status,
        statusText: response.statusText 
      });
      return null;
    }
    
    const data: ActressListResponse = await response.json();
    
    logger.info("女優一覧データ取得成功", { 
      count: data.persons.length,
      totalCount: data.total_count 
    });
    
    return data;
    
  } catch (error) {
    logger.error("女優一覧取得中にエラー", { error });
    return null;
  }
}