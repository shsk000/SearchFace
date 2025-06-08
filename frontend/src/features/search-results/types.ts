import { z } from "zod";

// 検索セッション結果の型定義
export const searchSessionResultSchema = z.object({
  rank: z.number(),
  person_id: z.number(),
  name: z.string(),
  similarity: z.number(),
  distance: z.number(),
  image_path: z.string(),
});

export const searchSessionResponseSchema = z.object({
  session_id: z.string(),
  search_timestamp: z.string(),
  metadata: z.record(z.any()).optional(),
  results: z.array(searchSessionResultSchema),
});

export type SearchSessionResult = z.infer<typeof searchSessionResultSchema>;
export type SearchSessionResponse = z.infer<typeof searchSessionResponseSchema>;

// UI用の型定義
export interface PersonWithRank {
  id: number;
  rank: number;
  name: string;
  similarity: number;
  distance: number;
  image_path: string;
}

// アフィリエイト商品の型定義
export interface Product {
  id: number;
  title: string;
  // price: string;
  image: string;
}
