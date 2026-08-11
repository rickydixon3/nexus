import { useEffect, useState } from 'react';

export function useFadeIn(text: string, active: boolean, chunkMs = 200) {
  const [chunks, setChunks] = useState<string[]>(active ? [] : splitIntoChunks(text));

  useEffect(() => {
    if (!active) {
      setChunks(splitIntoChunks(text));
      return;
    }

    const allChunks = splitIntoChunks(text);
    setChunks([]);
    let i = 0;

    const interval = setInterval(() => {
      i++;
      setChunks(allChunks.slice(0, i));
      if (i >= allChunks.length) {
        clearInterval(interval);
      }
    }, chunkMs);

    return () => clearInterval(interval);
  }, [text, active, chunkMs]);

  return chunks;
}

function splitIntoChunks(text: string): string[] {
  const sentences = text.match(/[^.!?]+[.!?]+(\s|$)/g) || [text];
  return sentences.map((s) => s.trim()).filter(Boolean);
}