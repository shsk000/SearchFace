// エラーコードの定義
export type ErrorCode =
  | "NO_FACE_DETECTED"
  | "MULTIPLE_FACES"
  | "INVALID_IMAGE"
  | "SERVER_ERROR"
  | "NETWORK_ERROR"
  | "UNKNOWN_ERROR"

// エラーレスポンスの型定義
export interface ErrorResponse {
  code: ErrorCode
  message: string
}

import { z } from "zod"

export const searchResultSchema = z.object({
  name: z.string(),
  similarity: z.number(),
  distance: z.number(),
  image_path: z.string(),
})

export const searchSuccessResponseSchema = z.object({
  results: z.array(searchResultSchema),
  processing_time: z.number()
})

export type SearchSuccessResponseSchema = z.infer<typeof searchSuccessResponseSchema>
