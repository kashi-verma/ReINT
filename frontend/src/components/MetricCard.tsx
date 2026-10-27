interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "positive" | "attention";
}

export function MetricCard({ label, value, detail, tone = "neutral" }: MetricCardProps) {
  return (
    <article className={`metric-card ${tone}`}>
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}
