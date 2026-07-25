import type { DailyLogSegment, DutyStatus } from "@/lib/api/types";

const X_START = 118;
const X_WIDTH = 650;

export const STATUS_Y: Record<DutyStatus, number> = {
  off_duty: 52,
  sleeper_berth: 91,
  driving: 130,
  on_duty_not_driving: 169,
};

export function xForMinute(minute: number): number {
  return X_START + (minute / 1440) * X_WIDTH;
}

export function buildDutyPath(segments: DailyLogSegment[]): string {
  if (segments.length === 0) return "";
  const commands = [
    `M ${xForMinute(segments[0].start_minute)} ${STATUS_Y[segments[0].duty_status]}`,
  ];
  segments.forEach((segment, index) => {
    commands.push(`H ${xForMinute(segment.end_minute)}`);
    const next = segments[index + 1];
    if (next) commands.push(`V ${STATUS_Y[next.duty_status]}`);
  });
  return commands.join(" ");
}
