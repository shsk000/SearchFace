import { z } from "zod";

// セッション結果用のスキーマ（Server Components用）
export const searchSessionResultSchema = z.object({
  rank: z.number(),
  person_id: z.number(),
  name: z.string(),
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