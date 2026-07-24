import React from 'react';
import { StationResult } from '../types';
import { DepartureRow } from './DepartureRow';

interface StationCardProps {
  stationResult: StationResult;
}

export const StationCard: React.FC<StationCardProps> = ({ stationResult }) => {
  const { station, status, departures, error } = stationResult;

  return (
    <div className={`station-card ${status === 'error' ? 'card-error' : ''}`}>
      <div className="station-card-header">
        <div className="station-title-group">
          <span className="station-icon">🚉</span>
          <h2 className="station-name">{station}</h2>
        </div>
        <div className="station-status-badge">
          {status === 'ok' ? (
            <span className="pill pill-success">Available</span>
          ) : (
            <span className="pill pill-error">Temporarily Unavailable</span>
          )}
        </div>
      </div>

      <div className="station-card-body">
        {status === 'error' ? (
          <div className="station-error-message">
            <span className="error-icon">⚠️</span>
            <span>
              Could not fetch departures for <strong>{station}</strong> ({error || 'upstream_error'}). Other matched stations are displayed below.
            </span>
          </div>
        ) : departures.length === 0 ? (
          <div className="station-empty-message">
            <span>No trains scheduled to depart from {station} in the next 15 minutes.</span>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="departures-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Train</th>
                  <th>Destination</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {departures.map((dep, idx) => (
                  <DepartureRow key={`${dep.train_number}-${dep.scheduled_time}-${idx}`} departure={dep} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
