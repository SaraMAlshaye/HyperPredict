import type { ModelSchema, PredictionRequest, PredictionResponse } from "./types";

/** An error with a message that is safe to show to the user. */
export class ApiError extends Error {
  constructor(message: string, public readonly status: number | null = null,
              public readonly details: string[] = []) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiError(
      "Can't reach the HyperPredict server. Make sure the backend is running, then try again.",
    );
  }
  let body: unknown = null;
  try {
    body = await res.json();
  } catch {
    /* non-JSON error page */
  }
  if (!res.ok) {
    const detail = (body as { detail?: unknown } | null)?.detail;
    const details = Array.isArray(detail)
      ? detail.map((d) => (typeof d === "string" ? d : (d as { msg?: string }).msg ?? "Invalid value"))
      : typeof detail === "string" ? [detail] : [];
    const message =
      res.status === 503 ? "The prediction model is not available on the server right now."
      : res.status === 422 ? "The server could not accept these values."
      : `The server returned an error (${res.status}).`;
    throw new ApiError(message, res.status, details);
  }
  return body as T;
}

export function fetchSchema(): Promise<ModelSchema> {
  return request<ModelSchema>("/api/schema");
}

export function requestPrediction(input: PredictionRequest): Promise<PredictionResponse> {
  return request<PredictionResponse>("/api/predict", { method: "POST", body: JSON.stringify(input) });
}
