import type { TripPlanResponse } from "@/lib/api/types";
import { formatDuration, formatMiles } from "@/lib/format";

export function TripSummary({ plan }: { plan: TripPlanResponse }) {
  const stats = [
    ["Distance", formatMiles(plan.summary.distance_miles)],
    ["Trip time", formatDuration(plan.summary.total_duration_minutes)],
    ["Driving", formatDuration(plan.summary.driving_minutes)],
    ["Daily logs", String(plan.summary.log_days)],
  ];
  return (
    <section className="trip-summary" aria-label="Trip summary">
      {stats.map(([label, value]) => (
        <div key={label}>
          <strong>{value}</strong>
          <span>{label}</span>
        </div>
      ))}
    </section>
  );
}
