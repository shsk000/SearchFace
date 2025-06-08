import { z } from "zod";

// エラーコードの定義
export const errorCodeSchema = z.enum([
  "NO_FACE_DETECTED",
  "MULTIPLE_FACES",
  "INVALID_IMAGE",
  "SERVER_ERROR",
  "NETWORK_ERROR",
  "UNKNOWN_ERROR",
  "SESSION_NOT_FOUND",
]);

export type ErrorCode = z.infer<typeof errorCodeSchema>;

// エラーレスポンスの型定義
export const errorResponseSchema = z.object({
  error: z.object({
    code: errorCodeSchema,
    message: z.string(),
  }),
});

export type ErrorResponse = z.infer<typeof errorResponseSchema>;

// 検索結果のスキーマ
export const searchResultSchema = z.object({
  name: z.string(),
  similarity: z.number(),
  distance: z.number(),
  image_path: z.string(),
});

export const searchSuccessResponseSchema = z.object({
  results: z.array(searchResultSchema),
  processing_time: z.number(),
  search_session_id: z.string(),
});

// セッション結果用のスキーマ
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

export type SearchResult = z.infer<typeof searchResultSchema>;
export type SearchSuccessResponse = z.infer<typeof searchSuccessResponseSchema>;
export type SearchSessionResult = z.infer<typeof searchSessionResultSchema>;
export type SearchSessionResponse = z.infer<typeof searchSessionResponseSchema>;

// 型ガード関数
export const isErrorCode = (code: unknown): code is ErrorCode =>
  errorCodeSchema.safeParse(code).success;

export const isErrorResponse = (response: unknown): response is ErrorResponse =>
  errorResponseSchema.safeParse(response).success;
