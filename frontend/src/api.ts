import { ApiErrorResponse, DeparturesResponse } from './types';

export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export async function fetchDepartures(query: string): Promise<DeparturesResponse> {
  const url = `/departures?q=${encodeURIComponent(query.trim())}`;
  const response = await fetch(url, {
    headers: {
      Accept: 'application/json',
    },
  });

  if (!response.ok) {
    let errorData: ApiErrorResponse | null = null;
    try {
      errorData = await response.json();
    } catch {
      // JSON parse error on non-ok response
    }

    const code = errorData?.error || 'unknown_error';
    const message = errorData?.message || `Server returned HTTP ${response.status}`;
    throw new ApiError(response.status, code, message);
  }

  return response.json();
}
