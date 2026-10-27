import type { DecisionResponse } from "./types";

export async function getDecision(
  decisionDate: string,
  cutoff: string,
  signal?: AbortSignal,
): Promise<DecisionResponse> {
  const query = new URLSearchParams({
    decision_date: decisionDate,
    cutoff,
    timezone: "Europe/London",
  });
  const response = await fetch(`/api/v1/decision?${query}`, { signal });
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // Preserve the status-based fallback when an upstream response is not JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<DecisionResponse>;
}
