import { z } from "zod";
import { type ErrorCode, errorCodeSchema } from "./type";

export function getErrorMessage(code: ErrorCode): string {
  const messages: Record<ErrorCode, string> = {
    NO_FACE_DETECTED: "画像から顔が検出できませんでした",
    MULTIPLE_FACES: "画像には1つの顔のみ含める必要があります",
    INVALID_IMAGE: "無効な画像形式です",
    SERVER_ERROR: "サーバーエラーが発生しました",
    NETWORK_ERROR: "ネットワークエラーが発生しました",
    UNKNOWN_ERROR: "予期せぬエラーが発生しました",
    SESSION_NOT_FOUND: "検索結果が見つかりません",
  };
  return messages[code];
}

// エラーコードに基づいてエラーの種類を判定する関数
export function getErrorType(code: ErrorCode): "error" | "warning" | "info" {
  switch (code) {
    case "NO_FACE_DETECTED":
    case "MULTIPLE_FACES":
    case "INVALID_IMAGE":
      return "warning";
    case "SERVER_ERROR":
    case "NETWORK_ERROR":
    case "UNKNOWN_ERROR":
    case "SESSION_NOT_FOUND":
      return "error";
    default:
      return "info";
  }
}

/**
 * エラーの種類
 */
export type SearchResultErrorType = "error" | "warning" | "info";

/**
 * 検索結果に関するエラークラス
 */
export class SearchResultError extends Error {
  constructor(message: ErrorCode) {
    super(message);
    this.name = "SearchResultError";
  }
}

export const searchResultErrorSchema = z.object({
  error: z.object({
    code: errorCodeSchema,
    message: z.string(),
  }),
});

export type SearchResultErrorResponseSchema = z.infer<typeof searchResultErrorSchema>;

export const createSearchResultCustomError = (data: SearchResultErrorResponseSchema) => {
  return new SearchResultError(data.error.code);
};
