export interface Source {
  title: string;
  source: string;
  url: string;
  published_at: string;
}

export interface RagResponse {
  answer: string;
  sources: Source[];
}

export interface RagError {
  error: string;
}

export interface Article {
  id: string;
  title: string;
  source: string;
  url: string;
  published_at: string;
  category: string | null;
  image_url: string | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
  isError?: boolean;
}