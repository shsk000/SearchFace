"use server";

import { logger } from "@/lib/logger";
import {
  SearchResultError,
  SearchResultErrorCode,
  createSearchResultCustomError,
  searchResultErrorSchema,
} from "./error";
import { type SearchSuccessResponseSchema, searchSuccessResponseSchema } from "./type";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error("NEXT_PUBLIC_API_URL is not defined");
}

export async function searchImage(formData: FormData): Promise<SearchSuccessResponseSchema> {
  try {
    const image = formData.get("image") as File;
    if (!image) {
      throw new Error("画像が選択されていません");
    }

    const response = await fetch(`${API_URL}/api/search`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errorObject = searchResultErrorSchema.parse(data);
      throw createSearchResultCustomError(errorObject);
    }

    const validatedData = searchSuccessResponseSchema.parse(data);
    return validatedData;
  } catch (error) {
    logger.error("Search Result error:", error);
    if (error instanceof SearchResultError) {
      throw error;
    }
    throw new SearchResultError(SearchResultErrorCode.UNKNOWN_ERROR);
  }
}
