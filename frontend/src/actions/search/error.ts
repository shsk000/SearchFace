import { z } from "zod";
import type { ErrorCode } from "./type";

export function getErrorMessage(code: ErrorCode): string {
  const messages: Record<ErrorCode, string> = {
    NO_FACE_DETECTED: "画像から顔が検出できませんでした",
    MULTIPLE_FACES: "画像には1つの顔のみ含める必要があります",
    INVALID_IMAGE: "無効な画像形式です",
    SERVER_ERROR: "サーバーエラーが発生しました",
    NETWORK_ERROR: "ネットワークエラーが発生しました",
    UNKNOWN_ERROR: "予期せぬエラーが発生しました",
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
      return "error";
    default:
      return "info";
  }
}

/**
 * アプリケーション固有のエラーコード
 */
export enum SearchResultErrorCode {
  // 画像関連のエラー
  NO_FACE_DETECTED = "NO_FACE_DETECTED",
  MULTIPLE_FACES = "MULTIPLE_FACES",
  INVALID_IMAGE = "INVALID_IMAGE",

  // サーバー関連のエラー
  SERVER_ERROR = "SERVER_ERROR",
  NETWORK_ERROR = "NETWORK_ERROR",

  // その他のエラー
  UNKNOWN_ERROR = "UNKNOWN_ERROR",
}

/**
 * エラーの種類
 */
export type SearchResultErrorType = "error" | "warning" | "info";

/**
 * 検索結果に関するエラークラス
 */
export class SearchResultError extends Error {
  constructor(message: SearchResultErrorCode) {
    super(message);
    this.name = "SearchResultError";
  }
}

export const searchResultErrorSchema = z.object({
  error: z.object({
    code: z.nativeEnum(SearchResultErrorCode),
    message: z.string(),
  }),
});

export type SearchResultErrorResponseSchema = z.infer<typeof searchResultErrorSchema>;

export const createSearchResultCustomError = (data: SearchResultErrorResponseSchema) => {
  return new SearchResultError(data.error.code);
};
