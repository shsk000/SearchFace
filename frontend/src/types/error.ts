export type ErrorCode =
  | "E1001" // 画像形式が無効
  | "E1002" // 画像サイズが大きすぎる
  | "E1003" // 画像サイズが小さすぎる
  | "E1004" // 顔が検出されない
  | "E1005" // 複数の顔が検出された
  | "E1006" // 画像が破損している
  | "E2001" // リクエストが無効
  | "E2002" // 必須パラメータが不足
  | "E2003" // パラメータが無効
  | "E3001" // 内部サーバーエラー
  | "E3002" // データベースエラー
  | "E3003"; // サービス利用不可

export interface ErrorResponse {
  error: {
    code: ErrorCode;
    message: string;
  };
}

export interface ApiResponse<T> {
  results?: T;
  error?: {
    code: ErrorCode;
    message: string;
  };
} 