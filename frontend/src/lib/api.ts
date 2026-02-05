import { Blog, PaginatedResponse, TokenResponse } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function fetchBlogs(params?: {
  search?: string;
  limit?: number;
  offset?: number;
}): Promise<PaginatedResponse<Blog>> {
  const query = new URLSearchParams();

  if (params?.search) query.set('search', params.search);
  if (params?.limit) query.set('limit', String(params.limit));
  if (params?.offset) query.set('offset', String(params.offset));

  const response = await fetch(`${API_BASE}/api/blogs?${query.toString()}`, {
    next: { revalidate: 60 }
  });

  if (!response.ok) {
    throw new Error('Failed to fetch blogs');
  }

  return response.json();
}

export async function fetchBlogById(id: string): Promise<Blog> {
  const response = await fetch(`${API_BASE}/api/blogs/${id}`, { cache: 'no-store' });

  if (!response.ok) {
    throw new Error('Blog not found');
  }

  return response.json();
}

export async function login(username: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ username, password })
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail ?? 'Login failed');
  }

  return response.json();
}
