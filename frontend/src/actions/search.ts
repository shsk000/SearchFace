'use server';

import { ApiResponse } from '@/types/error'

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL is not defined');
}

export async function searchImage(formData: FormData): Promise<ApiResponse<any>> {
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
      console.error('API Error:', data);
      return {
        error: {
          code: data.error?.code || 'E3001',
          message: data.error?.message || 'サーバーでエラーが発生しました。'
        }
      };
    }

    return data;
  } catch (error) {
    console.error('Search error:', error);
    return {
      error: {
        code: 'E3001',
        message: 'サーバーでエラーが発生しました。'
      }
    };
  }
} 