import React, { useState } from 'react';

interface SearchFormProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
  initialQuery?: string;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, isLoading, initialQuery = '' }) => {
  const [query, setQuery] = useState(initialQuery);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = query.trim();

    // Client-side minimum 3-character validation (mirrors backend rule)
    if (trimmed.length < 3) {
      setValidationError('Please enter at least 3 characters to search stations.');
      return;
    }

    setValidationError(null);
    onSearch(trimmed);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setQuery(val);
    if (validationError && val.trim().length >= 3) {
      setValidationError(null);
    }
  };

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <div className="search-input-group">
        <label htmlFor="station-search" className="sr-only">
          Station Name
        </label>
        <div className="input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            id="station-search"
            type="text"
            className={`search-input ${validationError ? 'input-invalid' : ''}`}
            placeholder="Search stations (e.g. Bru, Gent, Aac)..."
            value={query}
            onChange={handleInputChange}
            disabled={isLoading}
            autoFocus
          />
        </div>
        <button type="submit" className="search-button" disabled={isLoading}>
          {isLoading ? 'Searching...' : 'Search Departures'}
        </button>
      </div>

      {validationError && (
        <div className="validation-error" role="alert">
          <span>⚠️ {validationError}</span>
        </div>
      )}
    </form>
  );
};
