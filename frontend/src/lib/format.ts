const wallClockFormatter = new Intl.DateTimeFormat("en-US", {
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
  timeZone: "UTC",
});

export function formatDuration(minutes: number): string {
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const remainder = minutes % 60;
  return (
    [
      days ? `${days}d` : "",
      hours ? `${hours}h` : "",
      remainder ? `${remainder}m` : "",
    ]
      .filter(Boolean)
      .join(" ") || "0m"
  );
}

export function formatMiles(miles: string | number): string {
  return `${Math.round(Number(miles)).toLocaleString("en-US")} mi`;
}

export function formatDateTime(value: string): string {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
  if (!match) return value;
  const [, year, month, day, hour, minute] = match;
  const fixedWallClock = new Date(
    Date.UTC(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour),
      Number(minute),
    ),
  );
  return wallClockFormatter.format(fixedWallClock);
}
