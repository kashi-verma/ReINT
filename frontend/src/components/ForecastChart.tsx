import type { DecisionPoint } from "../types";
import { formatMw, formatTime } from "../format";

interface ForecastChartProps {
  points: DecisionPoint[];
  showActual: boolean;
}

const WIDTH = 920;
const HEIGHT = 330;
const LEFT = 66;
const RIGHT = 18;
const TOP = 24;
const BOTTOM = 44;

export function ForecastChart({ points, showActual }: ForecastChartProps) {
  const values = points.flatMap((point) => [
    point.forecastMw,
    ...(showActual ? [point.actualMw] : []),
  ]).filter((value): value is number => value !== null);

  if (points.length === 0 || values.length === 0) {
    return <div className="empty-chart">No generation periods to display.</div>;
  }

  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const padding = Math.max((rawMax - rawMin) * 0.12, 500);
  const min = Math.max(0, rawMin - padding);
  const max = rawMax + padding;
  const chartWidth = WIDTH - LEFT - RIGHT;
  const chartHeight = HEIGHT - TOP - BOTTOM;
  const x = (index: number) => LEFT + (index / Math.max(points.length - 1, 1)) * chartWidth;
  const y = (value: number) => TOP + ((max - value) / (max - min)) * chartHeight;
  const line = (key: "forecastMw" | "actualMw") =>
    points
      .map((point, index) =>
        point[key] === null ? null : `${x(index)},${y(point[key] as number)}`,
      )
      .filter(Boolean)
      .join(" ");
  const gridValues = Array.from({ length: 5 }, (_, index) => min + ((max - min) * index) / 4);

  return (
    <div className="chart-wrap">
      <svg
        className="forecast-chart"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={showActual ? "Hourly forecast and actual wind generation" : "Hourly wind forecast"}
      >
        {gridValues.map((value) => (
          <g key={value}>
            <line x1={LEFT} x2={WIDTH - RIGHT} y1={y(value)} y2={y(value)} className="grid-line" />
            <text x={LEFT - 12} y={y(value) + 4} textAnchor="end" className="axis-label">
              {Math.round(value / 1000)}k
            </text>
          </g>
        ))}
        <polyline points={line("forecastMw")} className="forecast-line" />
        {showActual && <polyline points={line("actualMw")} className="actual-line" />}
        {points.map((point, index) => (
          <g key={point.startTime}>
            {index % 4 === 0 && (
              <text x={x(index)} y={HEIGHT - 14} textAnchor="middle" className="axis-label">
                {formatTime(point.startTime)}
              </text>
            )}
            {point.forecastMw !== null && (
              <circle cx={x(index)} cy={y(point.forecastMw)} r="3.5" className="forecast-dot">
                <title>{`${formatTime(point.startTime)} forecast: ${formatMw(point.forecastMw)}`}</title>
              </circle>
            )}
            {showActual && point.actualMw !== null && (
              <circle cx={x(index)} cy={y(point.actualMw)} r="3" className="actual-dot">
                <title>{`${formatTime(point.startTime)} actual: ${formatMw(point.actualMw, 1)}`}</title>
              </circle>
            )}
          </g>
        ))}
        <text x="16" y="18" className="unit-label">MW</text>
      </svg>
      <div className="legend" aria-label="Chart legend">
        <span><i className="legend-swatch forecast" />Selected forecast</span>
        {showActual && <span><i className="legend-swatch actual" />FUELHH actual</span>}
      </div>
    </div>
  );
}
