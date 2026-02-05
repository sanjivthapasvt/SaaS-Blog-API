export interface Author {
  id: number;
  username: string;
  email?: string;
  profile_picture_url?: string | null;
}

export interface Blog {
  id: number;
  title: string;
  content?: string;
  created_at: string;
  updated_at?: string;
  thumbnail_url?: string | null;
  tags?: string[];
  likes_count?: number;
  comments_count?: number;
  author?: Author;
}

export interface PaginatedResponse<T> {
  total: number;
  limit: number;
  offset: number;
  data: T[];
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
