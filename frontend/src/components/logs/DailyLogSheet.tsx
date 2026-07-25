import { DutyGraph } from "@/components/logs/DutyGraph";
import type { DailyLog } from "@/lib/api/types";
import { formatMiles } from "@/lib/format";

function minutesAsHours(minutes: number): string {
  return `${(minutes / 60).toFixed(1)} h`;
}

export function DailyLogSheet({
  log,
  totalLogs,
  homeTimezone,
}: {
  log: DailyLog;
  totalLogs: number;
  homeTimezone: string;
}) {
  const totalMinutes = Object.values(log.totals_minutes).reduce(
    (sum, value) => sum + value,
    0,
  );
  const remarks = log.segments.filter(
    (segment) =>
      !["pre_trip_off_duty", "post_trip_off_duty"].includes(segment.kind),
  );

  return (
    <article className="daily-log-sheet">
      <header className="log-header">
        <div className="log-brand">
          <span className="sheet-mark" />
          <div>
            <h2>ROUTELOG · DRIVER'S DAILY LOG</h2>
            <p>Planned record of duty status</p>
          </div>
        </div>
        <dl>
          <div>
            <dt>Date</dt>
            <dd>{log.date}</dd>
          </div>
          <div>
            <dt>Trip day</dt>
            <dd>
              {String(log.trip_day).padStart(2, "0")} /{" "}
              {String(totalLogs).padStart(2, "0")}
            </dd>
          </div>
        </dl>
      </header>

      <section className="log-route">
        <div>
          <span>{log.start_location.label}</span>
          <i />
          <span>{log.end_location.label}</span>
        </div>
        <dl>
          <div>
            <dt>Distance</dt>
            <dd>{formatMiles(log.distance_m / 1609.344)}</dd>
          </div>
          <div>
            <dt>Driving</dt>
            <dd>{minutesAsHours(log.totals_minutes.driving)}</dd>
          </div>
          <div>
            <dt>Rule set</dt>
            <dd>70 / 8</dd>
          </div>
        </dl>
      </section>

      <section className="identity-fields" aria-label="Writable driver details">
        {["Driver", "Carrier", "Vehicle / unit", "Shipping document"].map(
          (label) => (
            <div key={label}>
              <span>{label}</span>
              <i />
            </div>
          ),
        )}
      </section>

      <section className="log-graph">
        <div className="log-section-heading">
          <strong>24-HOUR DUTY STATUS</strong>
          <span>{homeTimezone} · fixed trip-start offset</span>
        </div>
        <DutyGraph segments={log.segments} totals={log.totals_minutes} />
      </section>

      <section className="log-remarks">
        <div className="remarks-header">
          <span>Time</span>
          <span>Duty change / reason</span>
          <span>Location</span>
        </div>
        {remarks.map((segment) => (
          <div
            className="remark-entry"
            key={`${segment.event_id}-${segment.start_minute}`}
          >
            <time>
              {String(Math.floor(segment.start_minute / 60)).padStart(2, "0")}:
              {String(segment.start_minute % 60).padStart(2, "0")}
            </time>
            <span>{segment.remark}</span>
            <span>{segment.location.label}</span>
          </div>
        ))}
      </section>

      <section className="log-recap">
        <div>
          <strong>8-DAY CYCLE RECAP</strong>
          <dl>
            <div>
              <dt>Used before day</dt>
              <dd>{minutesAsHours(log.cycle.used_at_start_minutes)}</dd>
            </div>
            <div>
              <dt>On duty today</dt>
              <dd>{minutesAsHours(log.cycle.added_minutes)}</dd>
            </div>
            <div>
              <dt>Remaining</dt>
              <dd>{minutesAsHours(log.cycle.remaining_at_end_minutes)}</dd>
            </div>
          </dl>
        </div>
        <div className="driver-review">
          <strong>DRIVER REVIEW</strong>
          <i />
          <span>Signature / date</span>
        </div>
      </section>

      <footer>
        <span>{minutesAsHours(totalMinutes)} balanced</span>
        Planning copy generated from a proposed route. Review before use.
        RouteLog is not a certified ELD.
      </footer>
    </article>
  );
}
