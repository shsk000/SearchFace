/**
 * 女優リスト機能の型定義
 */

export interface ActressListItem {
  person_id: number;
  name: string;
  image_path: string | null;
  dmm_actress_id: number | null;
}

export interface ActressListResponse {
  persons: ActressListItem[];
  total_count: number;
  has_more: boolean;
}

export interface ActressListParams {
  limit?: number;
  offset?: number;
  search?: string;
  sort_by?: 'name' | 'person_id' | 'created_at';
}

export interface ActressCardProps {
  actress: ActressListItem;
}

export interface ActressListPresentationProps {
  actresses: ActressListItem[];
  totalCount: number;
  currentPage: number;
  itemsPerPage: number;
  searchQuery: string;
  sortBy: string;
  isLoading: boolean;
  error: string | null;
}