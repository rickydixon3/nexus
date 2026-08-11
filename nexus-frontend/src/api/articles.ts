import type { Article } from '../types';

const API_URL = import.meta.env.VITE_API_URL;

interface ArticlesResponse {
  articles: Article[];
  limit: number;
  offset: number;
}

interface FetchArticlesParams {
  source?: string;
  category?: string;
  limit?: number;
  offset?: number;
}

export async function fetchCategories(): Promise<string[]> {
  const response = await fetch(`${API_URL}/articles?meta=categories`);
  if (!response.ok) {
    throw new Error(`Failed to fetch categories: ${response.status}`);
  }
  const data = await response.json();
  return data.categories;
}

export async function fetchArticles({
  source,
  category,
  limit = 20,
  offset = 0,
}: FetchArticlesParams): Promise<ArticlesResponse> {
  const params = new URLSearchParams();
  if (source) params.set('source', source);
  if (category) params.set('category', category);
  params.set('limit', String(limit));
  params.set('offset', String(offset));

  const response = await fetch(`${API_URL}/articles?${params.toString()}`);

  if (!response.ok) {
    throw new Error(`Failed to fetch articles: ${response.status}`);
  }

  return response.json();
}