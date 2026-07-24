import { useState } from 'react';
import { fetchDepartures } from './api';
import { SearchForm } from './components/SearchForm';
import { StationCard } from './components/StationCard';
import { DeparturesResponse } from './types';

export default function App() {
  const [data, setData] = useState<DeparturesResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentQuery, setCurrentQuery] = useState('');

  const handleSearch = async (query: string) => {
    setIsLoading(true);
    setError(null);
    setCurrentQuery(query);

    try {
      const result = await fetchDepartures(query);
      setData(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred while fetching departures.');
      }
      setData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePresetClick = (preset: string) => {
    handleSearch(preset);
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-badge">Lagovia Transit Network</div>
        <h1 className="app-title">Train Departure Tracker</h1>
        <p className="app-subtitle">
          Real-time Belgian train departures in the next 15-minute window.
        </p>
      </header>

      <main className="app-main">
        <section className="search-section">
          <SearchForm onSearch={handleSearch} isLoading={isLoading} initialQuery={currentQuery} />
          
          <div className="preset-suggestions">
            <span className="preset-label">Try searching:</span>
            <button className="preset-btn" onClick={() => handlePresetClick('Bru')} disabled={isLoading}>
              "Bru" (Brussels / Bruges)
            </button>
            <button className="preset-btn" onClick={() => handlePresetClick('Gent')} disabled={isLoading}>
              "Gent"
            </button>
            <button className="preset-btn" onClick={() => handlePresetClick('Aac')} disabled={isLoading}>
              "Aac" (Aachen)
            </button>
          </div>
        </section>

        {/* State 1: Loading State */}
        {isLoading && (
          <div className="state-container state-loading">
            <div className="spinner"></div>
            <p>Fetching liveboard departures from iRail API...</p>
          </div>
        )}

        {/* State 2: Global API / Server Error State */}
        {!isLoading && error && (
          <div className="state-container state-error">
            <span className="error-badge-icon">❌</span>
            <h3>Unable to complete search</h3>
            <p>{error}</p>
            <button className="retry-btn" onClick={() => handleSearch(currentQuery)}>
              Try Again
            </button>
          </div>
        )}

        {/* State 3: Empty Result State (Valid query, 0 stations matched) */}
        {!isLoading && !error && data && data.stations.length === 0 && (
          <div className="state-container state-empty">
            <span className="empty-icon">🔍</span>
            <h3>No stations match "{data.query}"</h3>
            <p>No Belgian train stations match your query substring. Please try a different name.</p>
          </div>
        )}

        {/* State 4: Success Results State */}
        {!isLoading && !error && data && data.stations.length > 0 && (
          <section className="results-section">
            <div className="results-meta">
              <span>
                Found <strong>{data.stations.length}</strong> matching station{data.stations.length > 1 ? 's' : ''} for "{data.query}"
              </span>
              <span className="meta-time">
                Window: Next {data.window_minutes} min • Generated at{' '}
                {new Date(data.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
            </div>

            <div className="stations-list">
              {data.stations.map((stationResult) => (
                <StationCard key={stationResult.station} stationResult={stationResult} />
              ))}
            </div>
          </section>
        )}
      </main>

      <footer className="app-footer">
        <p>Lagovia Train Tracker • Powered by iRail Belgium API</p>
      </footer>
    </div>
  );
}
