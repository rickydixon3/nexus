import { useState } from 'react';

interface ChatInputProps {
  onSend: (query: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  }

  return (
    <form className="chat-input-row" onSubmit={handleSubmit}>
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about recent news..."
        disabled={disabled}
      />
      <button type="submit" disabled={disabled || !input.trim()} aria-label="Send">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 19V5M5 12l7-7 7 7" />
        </svg>
      </button>
    </form>
  );
}