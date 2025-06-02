'use server';

import { createSearchResultCustomError, SearchResultError, SearchResultErrorCode, searchResultErrorSchema } from './error';
import { searchSuccessResponseSchema, type SearchSuccessResponseSchema } from './type';

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL is not defined');
}

export async function searchImage(formData: FormData): Promise<SearchSuccessResponseSchema> {
  try {
    const image = formData.get('image') as File;
    if (!image) {
      throw new Error('画像が選択されていません');
    }

    const response = await fetch(`${API_URL}/api/search`, {
      method: 'POST',
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
    if (error instanceof SearchResultError) {
      throw error;
    }
    console.error('Search error:', error);
    throw new SearchResultError(SearchResultErrorCode.UNKNOWN_ERROR, "原因不明のエラーが発生しました");
  }
}