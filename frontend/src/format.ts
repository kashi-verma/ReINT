export const formatMw = (value: number | null, digits = 0): string =>
  value === null
    ? "—"
    : `${new Intl.NumberFormat("en-GB", {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(value)} MW`;

export const formatPercent = (value: number): string =>
  new Intl.NumberFormat("en-GB", {
    style: "percent",
    maximumFractionDigits: 0,
  }).format(value);

export const formatDate = (value: string): string =>
  new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));

export const formatTime = (value: string | null): string =>
  value === null
    ? "Not available"
    : new Intl.DateTimeFormat("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "UTC",
        hour12: false,
      }).format(new Date(value));
