import type {
  ApiErrorBody,
  LocationCandidate,
  TripPlanRequest,
  TripPlanResponse,
} from "@/lib/api/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly field: string | null,
    public readonly retryable: boolean,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ApiErrorBody;
  if (!response.ok) {
    const error = (body as ApiErrorBody).error;
    throw new ApiClientError(
      error?.message ?? "The request could not be completed.",
      error?.code ?? "INTERNAL_ERROR",
      error?.field ?? null,
      error?.retryable ?? response.status >= 500,
      response.status,
    );
  }
  return body as T;
}

export async function searchLocations(
  query: string,
  signal?: AbortSignal,
): Promise<LocationCandidate[]> {
  const response = await fetch(
    `${API_BASE}/locations/search/?q=${encodeURIComponent(query)}`,
    { signal },
  );
  const body = await parseResponse<{ locations: LocationCandidate[] }>(
    response,
  );
  return body.locations;
}

export async function planTrip(
  request: TripPlanRequest,
  signal?: AbortSignal,
): Promise<TripPlanResponse> {
  const response = await fetch(`${API_BASE}/trips/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
  return parseResponse<TripPlanResponse>(response);
}
