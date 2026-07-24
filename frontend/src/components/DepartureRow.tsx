import React from 'react';
import { Departure } from '../types';

interface DepartureRowProps {
  departure: Departure;
}

export const DepartureRow: React.FC<DepartureRowProps> = ({ departure }) => {
  const { train_number, destination, scheduled_time, delay_minutes, cancelled } = departure;

  // Format ISO 8601 UTC timestamp to local display time (HH:mm)
  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
    } catch {
      return isoString;
    }
  };

  return (
    <tr className={`departure-row ${cancelled ? 'is-cancelled' : ''}`}>
      <td className="time-cell">
        <span className="time-text">{formatTime(scheduled_time)}</span>
      </td>
      <td className="train-cell">
        <span className="train-badge">{train_number}</span>
      </td>
      <td className="dest-cell">
        <span className="destination-name">{destination}</span>
      </td>
      <td className="status-cell">
        {cancelled ? (
          <span className="badge badge-cancelled">CANCELLED</span>
        ) : delay_minutes > 0 ? (
          <span className="badge badge-delayed">+{delay_minutes} min</span>
        ) : (
          <span className="badge badge-ontime">On time</span>
        )}
      </td>
    </tr>
  );
};
