import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import type { DecisionResponse } from "./types";

const response: DecisionResponse = {
  decisionDate: "2026-01-05",
  deliveryDate: "2026-01-06",
  cutoffLocal: "09:20:00",
  timezone: "Europe/London",
  cutoffUtc: "2026-01-05T09:20:00Z",
  units: "MW",
  errorDefinition: "forecast minus actual",
  retrospective: true,
  warnings: [],
  metrics: {
    expectedPeriods: 1,
    forecastPeriods: 1,
    matchedPeriods: 1,
    forecastCoverage: 1,
    matchedCoverage: 1,
    maeMw: 100,
    rmseMw: 100,
    biasMw: 100,
  },
  points: [{
    startTime: "2026-01-06T00:00:00Z",
    forecastMw: 6000,
    forecastPublishTime: "2026-01-05T07:30:00Z",
    actualMw: 5900,
    actualHalfHourCount: 2,
    signedErrorMw: 100,
  }],
};

afterEach(() => vi.unstubAllGlobals());

describe("decision and accuracy separation", () => {
  it("keeps retrospective results out of the decision view", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      json: async () => response,
    }));

    render(<App />);
    expect(await screen.findByText("Selected wind forecast")).toBeInTheDocument();
    expect(screen.queryByText("Mean absolute error")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Retrospective accuracy/i }));
    expect(screen.getByText("Mean absolute error")).toBeInTheDocument();
    expect(screen.getByText(/not available at decision time/i)).toBeInTheDocument();
  });
});
