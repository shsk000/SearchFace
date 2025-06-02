'use server';

const API_URL = process.env.NEXT_PUBLIC_API_URL;
if (!API_URL) {
  throw new Error('NEXT_PUBLIC_API_URL is not defined');
}

export async function searchImage(formData: FormData) {
  try {
    const image = formData.get('image') as File;
    if (!image) {
      throw new Error('画像が選択されていません');
    }

    const response = await fetch(`${API_URL}/api/search`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('検索に失敗しました');
    }

    const data = await response.json();
    console.log('検索結果:', data);
    return data;
  } catch (error) {
    console.error('エラー:', error);
    throw error;
  }
} 