export interface DecisionPoint {
  startTime: string;
  forecastMw: number | null;
  forecastPublishTime: string | null;
  actualMw: number | null;
  actualHalfHourCount: number;
  signedErrorMw: number | null;
}

export interface DecisionMetrics {
  expectedPeriods: number;
  forecastPeriods: number;
  matchedPeriods: number;
  forecastCoverage: number;
  matchedCoverage: number;
  maeMw: number | null;
  rmseMw: number | null;
  biasMw: number | null;
}

export interface DecisionResponse {
  decisionDate: string;
  deliveryDate: string;
  cutoffLocal: string;
  timezone: string;
  cutoffUtc: string;
  units: string;
  errorDefinition: string;
  retrospective: boolean;
  metrics: DecisionMetrics;
  warnings: string[];
  points: DecisionPoint[];
}
