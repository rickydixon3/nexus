import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types';

interface ChatThreadProps {
  messages: ChatMessage[];
  loading: boolean;
  onSuggestionClick: (query: string) => void;
}

const SUGGESTIONS = [
  'What major events have happened recently?',
  'What is happening in the Middle East?',
  'Any updates on the Commonwealth Games?',
];

export function ChatThread({
  messages,
  loading,
  onSuggestionClick,
}: ChatThreadProps) {
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = threadRef.current;

    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, loading]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="chat-thread chat-empty" ref={threadRef}>
        <div className="chat-empty-inner">
          <p className="chat-empty-title">Ask about the news</p>

          <p className="chat-empty-subtitle">Nexus answers questions using recent articles, with sources cited.</p>

          <div className="chat-suggestions">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className="chat-suggestion"
                onClick={() => onSuggestionClick(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-thread" ref={threadRef}>
      {messages.map((msg, i) =>
        msg.role === 'user' ? (
          <div key={i} className="chat-user-msg">
            {msg.content}
          </div>
        ) : (
          <div key={i} className="chat-assistant-msg fade-in">
            <p
              className="chat-answer"
              style={
                msg.isError
                  ? {
                      color: 'var(--text-muted)',
                      fontStyle: 'italic',
                    }
                  : undefined
              }
            >
              {msg.content}
            </p>

            {msg.sources && msg.sources.length > 0 && (
              <div className="chat-sources">
                {msg.sources.map((source) => (
                  <a
                    key={source.url}
                    className="chat-source-link"
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {source.title} — {source.source}
                  </a>
                ))}
              </div>
            )}
          </div>
        )
      )}

      {loading && (
        <div className="chat-assistant-msg">
          <div className="chat-typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      )}
    </div>
  );
}