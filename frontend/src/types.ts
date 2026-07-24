export interface Departure {
  train_number: string;
  destination: string;
  scheduled_time: string; // ISO 8601 UTC string (e.g., "2026-07-24T10:22:00Z")
  delay_minutes: number;
  cancelled: boolean;
}

export interface StationResult {
  station: string;
  status: 'ok' | 'error';
  departures: Departure[];
  error?: string;
}

export interface DeparturesResponse {
  query: string;
  generated_at: string;
  window_minutes: number;
  stations: StationResult[];
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  min_length?: number;
}
