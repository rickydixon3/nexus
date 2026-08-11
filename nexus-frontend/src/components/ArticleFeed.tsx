import { useEffect, useRef, useState, useCallback } from 'react';
import { ArticleCard } from './ArticleCard';
import { fetchArticles } from '../api/articles';
import type { Article } from '../types';

interface ArticleFeedProps {
  source?: string;
  category?: string;
}

const PAGE_SIZE = 20;

function markDuplicateImages(articles: Article[]): Article[] {
  const counts = new Map<string, number>();
  for (const a of articles) {
    if (a.image_url) {
      counts.set(a.image_url, (counts.get(a.image_url) || 0) + 1);
    }
  }
  return articles.map((a) =>
    a.image_url && (counts.get(a.image_url) || 0) > 1
      ? { ...a, image_url: null }
      : a
  );
}

export function ArticleFeed({ source, category }: ArticleFeedProps) {
  const [articles, setArticles] = useState<Article[]>([]);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const loadMore = useCallback(async () => {
    if (loading || !hasMore) return;
    setLoading(true);
    try {
      const data = await fetchArticles({ source, category, limit: PAGE_SIZE, offset });
      setArticles((prev) => markDuplicateImages([...prev, ...data.articles]));
      setOffset((prev) => prev + data.articles.length);
      setHasMore(data.articles.length === PAGE_SIZE);
    } catch (err) {
      console.error('Failed to load articles', err);
    } finally {
      setLoading(false);
    }
  }, [source, category, offset, loading, hasMore]);

  // Reset and reload whenever filters change
  useEffect(() => {
    setArticles([]);
    setOffset(0);
    setHasMore(true);
  }, [source, category]);

  useEffect(() => {
    if (offset === 0 && articles.length === 0 && hasMore) {
      loadMore();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [offset, articles.length]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadMore();
        }
      },
      { rootMargin: '400px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  return (
    <div>
      <div className="list">
        {articles.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>
      {loading && <p style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>Loading more articles...</p>}
      <div ref={sentinelRef} style={{ height: '1px' }} />
    </div>
  );
}