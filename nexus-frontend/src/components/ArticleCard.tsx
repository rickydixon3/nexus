import type { Article } from '../types';

interface ArticleCardProps {
  article: Article;
}

const SOURCE_COLORS: Record<string, string> = {
  guardian: 'var(--accent)',
  nyt: '#2b3a55',
  currents: '#8a8578',
};

export function ArticleCard({ article }: ArticleCardProps) {
  const timeAgo = formatTimeAgo(article.published_at);
  const stripeColor = SOURCE_COLORS[article.source] || 'var(--text-muted)';

  return (
    <a
      className="list-row"
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: 'none', display: 'flex' }}
    >
      {article.image_url ? (
        <img
          className="list-thumb"
          src={article.image_url}
          alt=""
          loading="lazy"
        />
      ) : (
        <div
          className="list-stripe"
          style={{ background: stripeColor }}
        />
      )}

      <div className="list-body">
        <p className="list-title">{article.title}</p>
        <p className="list-meta">
          {article.source} · {timeAgo}
        </p>
      </div>
    </a>
  );
}

function formatTimeAgo(isoDate: string): string {
  const then = new Date(isoDate).getTime();
  const now = Date.now();
  const diffMinutes = Math.floor((now - then) / 60000);

  if (diffMinutes < 60) return `${diffMinutes}m ago`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}