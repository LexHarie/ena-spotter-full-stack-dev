import type { DailyLogSegment, DutyStatus } from "@/lib/api/types";
import {
  buildDutyPath,
  STATUS_Y,
  xForMinute,
} from "@/components/logs/dutyGraphPath";

const X_START = 118;
const X_WIDTH = 650;
const STATUSES: [DutyStatus, string][] = [
  ["off_duty", "OFF DUTY"],
  ["sleeper_berth", "SLEEPER BERTH"],
  ["driving", "DRIVING"],
  ["on_duty_not_driving", "ON DUTY"],
];

export function DutyGraph({
  segments,
  totals,
}: {
  segments: DailyLogSegment[];
  totals: Record<DutyStatus, number>;
}) {
  return (
    <svg
      className="duty-graph"
      viewBox="0 0 860 205"
      role="img"
      aria-label="Twenty-four hour duty status graph"
    >
      {Array.from({ length: 25 }, (_, hour) => {
        const x = xForMinute(hour * 60);
        return (
          <g key={`hour-${hour}`}>
            <line x1={x} x2={x} y1="33" y2="188" className="hour-line" />
            {hour % 2 === 0 && (
              <text x={x} y="18" textAnchor="middle" className="hour-label">
                {String(hour).padStart(2, "0")}
              </text>
            )}
          </g>
        );
      })}
      {Array.from({ length: 96 }, (_, quarter) => {
        const x = xForMinute(quarter * 15);
        return (
          <line
            key={`quarter-${quarter}`}
            x1={x}
            x2={x}
            y1="33"
            y2="188"
            className="quarter-line"
          />
        );
      })}
      {STATUSES.map(([status, label]) => (
        <g key={status}>
          <line
            x1={X_START}
            x2={X_START + X_WIDTH}
            y1={STATUS_Y[status] + 19.5}
            y2={STATUS_Y[status] + 19.5}
            className="row-line"
          />
          <text x="4" y={STATUS_Y[status] + 3} className="status-label">
            {label}
          </text>
          <text x="820" y={STATUS_Y[status] + 3} className="status-total">
            {(totals[status] / 60).toFixed(1)}
          </text>
        </g>
      ))}
      <path d={buildDutyPath(segments)} className="duty-path-halo" />
      <path d={buildDutyPath(segments)} className="duty-path" />
    </svg>
  );
}
