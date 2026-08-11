import type { RagResponse } from '../types';

interface ResultsDisplayProps {
  result: RagResponse | null;
  error: string | null;
}

export function ResultsDisplay({ result, error }: ResultsDisplayProps) {
  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!result) {
    return null;
  }

  return (
    <div className="results">
      <p className="answer">{result.answer}</p>
      {result.sources.length > 0 && (
        <div className="sources">
          <h3>Sources</h3>
          <ul>
            {result.sources.map((source, i) => (
              <li key={source.url}>
                [{i + 1}]{' '}
                <a href={source.url} target="_blank" rel="noopener noreferrer">
                  {source.title}
                </a>{' '}
                — {source.source}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}