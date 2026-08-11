import { useState } from 'react';

interface SearchBoxProps {
  onSearch: (query: string) => void;
  disabled: boolean;
}

export function SearchBox({ onSearch, disabled }: SearchBoxProps) {
  const [input, setInput] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim()) {
      onSearch(input.trim());
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about recent news..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !input.trim()}>
        {disabled ? 'Searching...' : 'Search'}
      </button>
    </form>
  );
}