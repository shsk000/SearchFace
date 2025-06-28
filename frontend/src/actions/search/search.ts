"use server";

import { logger } from "@/lib/logger";
import { SearchResultError } from "./error";
import type { SearchSuccessResponse } from "./type";
import { isErrorResponse, searchSuccessResponseSchema } from "./type";

const API_BASE_URL = process.env.API_BASE_URL || "http://backend:10000";

export async function searchImage(formData: FormData): Promise<SearchSuccessResponse> {
  const image = formData.get("image") as File;

  if (!image) {
    throw new SearchResultError("INVALID_IMAGE");
  }

  try {
    logger.info("画像検索を開始", {
      fileName: image.name,
      fileSize: image.size,
      fileType: image.type,
    });

    const searchFormData = new FormData();
    searchFormData.append("image", image);

    const response = await fetch(`${API_BASE_URL}/api/search?top_k=5`, {
      method: "POST",
      body: searchFormData,
    });

    const responseText = await response.text();
    if (!responseText) {
      logger.error("APIから空のレスポンスを受信", {
        status: response.status,
        statusText: response.statusText,
      });
      throw new SearchResultError("SERVER_ERROR");
    }

    let data: SearchSuccessResponse | Record<string, unknown>;
    try {
      data = JSON.parse(responseText);
    } catch (parseError) {
      logger.error("APIレスポンスのJSONパースに失敗", {
        status: response.status,
        statusText: response.statusText,
        responseText: responseText.substring(0, 200),
        parseError,
      });
      throw new SearchResultError("SERVER_ERROR");
    }

    if (!response.ok) {
      logger.error("API検索エラー", {
        status: response.status,
        statusText: response.statusText,
        error: data,
      });

      if (isErrorResponse(data)) {
        throw new SearchResultError(data.error.code);
      }

      throw new SearchResultError("SERVER_ERROR");
    }

    // レスポンスデータの検証
    const validationResult = searchSuccessResponseSchema.safeParse(data);
    if (!validationResult.success) {
      logger.error("API レスポンスの形式が不正", {
        error: validationResult.error,
        data,
      });

      throw new SearchResultError("UNKNOWN_ERROR");
    }

    logger.info("画像検索成功", {
      resultsCount: validationResult.data.results?.length,
      processingTime: validationResult.data.processing_time,
    });

    return validationResult.data;
  } catch (error) {
    logger.error("検索処理中にエラー", { error });

    if (error instanceof Error) {
      throw error;
    }

    throw new SearchResultError("UNKNOWN_ERROR");
  }
}
