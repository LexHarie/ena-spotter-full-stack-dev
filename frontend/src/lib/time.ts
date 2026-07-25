function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function getTripStartContext(
  now = new Date(),
  timezone = Intl.DateTimeFormat().resolvedOptions().timeZone,
  offsetMinutesWest?: number,
): {
  starts_at: string;
  home_terminal_timezone: string;
} {
  const roundedEpoch = Math.ceil(now.getTime() / (15 * 60_000)) * 15 * 60_000;
  const rounded = new Date(roundedEpoch);
  const effectiveOffset = offsetMinutesWest ?? rounded.getTimezoneOffset();
  const local = new Date(roundedEpoch - effectiveOffset * 60_000);
  const sign = effectiveOffset <= 0 ? "+" : "-";
  const absoluteOffset = Math.abs(effectiveOffset);
  const startsAt = [
    `${local.getUTCFullYear()}-${pad(local.getUTCMonth() + 1)}-${pad(local.getUTCDate())}`,
    `T${pad(local.getUTCHours())}:${pad(local.getUTCMinutes())}:00`,
    `${sign}${pad(Math.floor(absoluteOffset / 60))}:${pad(absoluteOffset % 60)}`,
  ].join("");
  return {
    starts_at: startsAt,
    home_terminal_timezone: timezone,
  };
}
