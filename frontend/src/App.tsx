import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { getDecision } from "./api";
import { ForecastChart } from "./components/ForecastChart";
import { MetricCard } from "./components/MetricCard";
import { formatDate, formatMw, formatPercent, formatTime } from "./format";
import type { DecisionResponse } from "./types";

type View = "decision" | "accuracy";

export default function App() {
  const [view, setView] = useState<View>("decision");
  const [decisionDate, setDecisionDate] = useState("2026-01-05");
  const [cutoff, setCutoff] = useState("09:20");
  const [data, setData] = useState<DecisionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDecision(decisionDate, cutoff, signal);
      setData(result);
    } catch (requestError) {
      if (requestError instanceof DOMException && requestError.name === "AbortError") return;
      setData(null);
      setError(requestError instanceof Error ? requestError.message : "Unable to load decision data.");
    } finally {
      if (!signal?.aborted) setLoading(false);
    }
  }, [decisionDate, cutoff]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const overestimates = useMemo(
    () =>
      [...(data?.points ?? [])]
        .filter((point) => point.signedErrorMw !== null && point.signedErrorMw > 0)
        .sort((a, b) => (b.signedErrorMw ?? 0) - (a.signedErrorMw ?? 0))
        .slice(0, 5),
    [data],
  );

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void load();
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="WindSight home">
          <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
          <span>WindSight</span>
        </a>
        <div className="source-badge"><span />Elexon data snapshot</div>
      </header>

      <main id="top">
        <section className="hero">
          <div>
            <p className="eyebrow">GB day-ahead decision support</p>
            <h1>Wind confidence,<br /><em>before the market moves.</em></h1>
            <p className="hero-copy">
              Replay exactly what was known at the purchasing cutoff, then assess the forecast against national wind outturn.
            </p>
          </div>
          <aside className="scope-note">
            <span>Scope</span>
            <p>National GB wind only. This is not the utility’s contracted supply and does not calculate required purchases.</p>
          </aside>
        </section>

        <section className="control-panel" aria-label="Decision controls">
          <form onSubmit={submit}>
            <label>
              Decision date
              <input
                type="date"
                min="2026-01-05"
                max="2026-01-05"
                value={decisionDate}
                onChange={(event) => setDecisionDate(event.target.value)}
              />
              <small>Sample slice: 5 January only</small>
            </label>
            <label>
              Decision cutoff
              <input type="time" value={cutoff} onChange={(event) => setCutoff(event.target.value)} />
              <small>Europe/London · configurable assumption</small>
            </label>
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "Loading…" : "Replay decision"}<span aria-hidden="true">→</span>
            </button>
          </form>
          <div className="cutoff-context">
            <strong>Why 09:20?</strong>
            <span>Default based on the EPEX GB hourly day-ahead auction close. Confirm the team’s internal cutoff before operational use.</span>
          </div>
        </section>

        <nav className="view-tabs" aria-label="Analysis views">
          <button className={view === "decision" ? "active" : ""} onClick={() => setView("decision")}>
            <span>01</span> Decision replay
          </button>
          <button className={view === "accuracy" ? "active" : ""} onClick={() => setView("accuracy")}>
            <span>02</span> Retrospective accuracy
          </button>
        </nav>

        {loading && <section className="state-card" role="status"><div className="spinner" />Loading Elexon decision data…</section>}
        {error && (
          <section className="state-card error-state" role="alert">
            <strong>We couldn’t load this decision.</strong><p>{error}</p><button onClick={() => void load()}>Try again</button>
          </section>
        )}
        {!loading && !error && data && data.points.length === 0 && (
          <section className="state-card">No forecast periods were returned for this decision.</section>
        )}

        {!loading && !error && data && data.points.length > 0 && (
          <>
            {data.warnings.length > 0 && (
              <section className="warning-banner" role="status">
                <strong>Coverage warning</strong>{data.warnings.map((warning) => <span key={warning}>{warning}</span>)}
              </section>
            )}

            {view === "decision" ? (
              <section className="view-section">
                <div className="section-heading">
                  <div><p className="eyebrow">Available by {data.cutoffLocal.slice(0, 5)}</p><h2>{formatDate(data.deliveryDate)} forecast</h2></div>
                  <div className="coverage-pill"><span>{data.metrics.forecastPeriods}/{data.metrics.expectedPeriods}</span> hourly targets covered</div>
                </div>
                <div className="chart-card">
                  <div className="chart-title"><div><h3>Selected wind forecast</h3><p>Latest eligible publication for each delivery hour</p></div><span className="unit-chip">MW</span></div>
                  <ForecastChart points={data.points} showActual={false} />
                </div>
                <div className="decision-grid">
                  <article className="publication-card">
                    <p className="eyebrow">Audit trail</p><h3>Publication coverage</h3>
                    <div className="publication-stat"><strong>{formatPercent(data.metrics.forecastCoverage)}</strong><span>of delivery hours have an eligible forecast</span></div>
                    <p>Every visible value was published at or before <strong>{formatTime(data.cutoffUtc)} UTC</strong>. Later updates remain excluded.</p>
                  </article>
                  <article className="period-table-card">
                    <div className="table-heading"><h3>Hourly selections</h3><span>UTC</span></div>
                    <div className="table-scroll">
                      <table><thead><tr><th>Delivery</th><th>Forecast</th><th>Published</th></tr></thead>
                        <tbody>{data.points.map((point) => <tr key={point.startTime}><td>{formatTime(point.startTime)}</td><td>{formatMw(point.forecastMw)}</td><td>{formatTime(point.forecastPublishTime)}</td></tr>)}</tbody>
                      </table>
                    </div>
                  </article>
                </div>
              </section>
            ) : (
              <section className="view-section">
                <div className="section-heading">
                  <div><p className="eyebrow retrospective-label">Retrospective analysis</p><h2>How the forecast performed</h2></div>
                  <p className="heading-note">Uses actual generation that was not available at decision time.</p>
                </div>
                <div className="metric-grid">
                  <MetricCard label="Mean absolute error" value={formatMw(data.metrics.maeMw, 0)} detail="Typical absolute miss" />
                  <MetricCard label="Root mean square error" value={formatMw(data.metrics.rmseMw, 0)} detail="Penalises larger misses" tone="attention" />
                  <MetricCard label="Bias" value={formatMw(data.metrics.biasMw, 0)} detail="Positive = over-forecast" tone={data.metrics.biasMw !== null && data.metrics.biasMw > 0 ? "attention" : "positive"} />
                  <MetricCard label="Matched coverage" value={formatPercent(data.metrics.matchedCoverage)} detail={`${data.metrics.matchedPeriods} of ${data.metrics.expectedPeriods} hours`} tone="positive" />
                </div>
                <div className="chart-card">
                  <div className="chart-title"><div><h3>Forecast versus actual</h3><p>FUELHH half-hours averaged to match hourly WINDFOR targets</p></div><span className="unit-chip">MW</span></div>
                  <ForecastChart points={data.points} showActual />
                </div>
                <article className="overestimate-card">
                  <div><p className="eyebrow">Largest misses</p><h3>Overestimation periods</h3><p>Signed error is forecast minus actual.</p></div>
                  <ol>{overestimates.map((point) => <li key={point.startTime}><span>{formatTime(point.startTime)}</span><div><i style={{ width: `${Math.min(((point.signedErrorMw ?? 0) / (overestimates[0]?.signedErrorMw ?? 1)) * 100, 100)}%` }} /></div><strong>+{formatMw(point.signedErrorMw)}</strong></li>)}</ol>
                </article>
              </section>
            )}
          </>
        )}
      </main>

      <footer><span>WindSight pilot · Elexon WINDFOR + FUELHH</span><span>Times shown in UTC · Generation shown in MW</span></footer>
    </div>
  );
}
