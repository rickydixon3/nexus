import type { RagResponse, RagError } from '../types';

const API_URL = import.meta.env.VITE_API_URL;

export async function queryNexus(query: string): Promise<RagResponse> {
  const response = await fetch(`${API_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const errorData: RagError = await response.json().catch(() => ({
      error: `Request failed with status ${response.status}`,
    }));
    throw new Error(errorData.error);
  }

  console.log(import.meta.env.VITE_API_URL)

  return response.json();
}