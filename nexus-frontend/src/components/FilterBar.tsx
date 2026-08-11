import { useEffect, useState } from 'react';
import { fetchCategories } from '../api/articles';

interface FilterBarProps {
  source: string;
  category: string;
  onSourceChange: (source: string) => void;
  onCategoryChange: (category: string) => void;
}

const SOURCES = ['guardian', 'nyt', 'currents'];

function formatCategory(cat: string): string {
  return cat
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function FilterBar({ source, category, onSourceChange, onCategoryChange }: FilterBarProps) {
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    fetchCategories()
      .then(setCategories)
      .catch((err) => console.error('Failed to load categories', err));
  }, []);

  return (
    <div className="filter-row">
      <select value={source} onChange={(e) => onSourceChange(e.target.value)}>
        <option value="">All sources</option>
        {SOURCES.map((s) => (
          <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
        ))}
      </select>

      <select value={category} onChange={(e) => onCategoryChange(e.target.value)}>
        <option value="">All categories</option>
        {categories.map((c) => (
          <option key={c} value={c}>{formatCategory(c)}</option>
        ))}
      </select>

      {source && (
        <div className="chip">
          {source.charAt(0).toUpperCase() + source.slice(1)}
          <button onClick={() => onSourceChange('')}>&times;</button>
        </div>
      )}

      {category && (
        <div className="chip">
          {category}
          <button onClick={() => onCategoryChange('')}>&times;</button>
        </div>
      )}
    </div>
  );
}