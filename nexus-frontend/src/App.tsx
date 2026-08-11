import { useState } from 'react';
import { ChatThread } from './components/ChatThread';
import { ChatInput } from './components/ChatInput';
import { ArticleFeed } from './components/ArticleFeed';
import { FilterBar } from './components/FilterBar';
import { queryNexus } from './api/query';
import type { ChatMessage } from './types';

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState('');
  const [category, setCategory] = useState('');

  async function handleSend(query: string) {
    setMessages((prev) => [...prev, { role: 'user', content: query }]);
    setLoading(true);

    try {
      const response = await queryNexus(query);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.answer, sources: response.sources },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong';
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: message, isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleNewConversation() {
    setMessages([]);
  }

  return (
    <div className="shell-page">
      <div className="shell-container">
        <div className="shell-topbar">
          <div className="mark">nexus<span className="dot">.</span></div>
        </div>
        <div className="shell-body">
          <div className="shell-ask">
            <div className="shell-header-row">
              <button onClick={handleNewConversation} disabled={messages.length === 0}>
                New conversation
              </button>
            </div>
            <ChatThread messages={messages} loading={loading} onSuggestionClick={handleSend} />
            <ChatInput onSend={handleSend} disabled={loading} />
          </div>
          <div className="shell-browse">
            <div className="shell-browse-header">Latest articles</div>
            <div className="shell-browse-list">
              <FilterBar
                source={source}
                category={category}
                onSourceChange={setSource}
                onCategoryChange={setCategory}
              />
              <ArticleFeed source={source || undefined} category={category || undefined} />
            </div>
          </div>
        </div>
        <div className="shell-footer">
          Powered by retrieval-augmented generation (RAG) Data from the Guardian, NYT, and Currents API
        </div>
      </div>
    </div>
  );
}

export default App;