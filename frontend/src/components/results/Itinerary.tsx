import {
  BedDouble,
  CircleParking,
  Clock3,
  Fuel,
  MapPin,
  PackageCheck,
  Truck,
} from "lucide-react";
import { m } from "motion/react";

import type { DutyEvent } from "@/lib/api/types";
import { formatDateTime, formatDuration } from "@/lib/format";

const icons = {
  driving: Truck,
  pickup: PackageCheck,
  dropoff: MapPin,
  fuel: Fuel,
  break: CircleParking,
  daily_rest: BedDouble,
  cycle_restart: Clock3,
  pre_trip_off_duty: Clock3,
  post_trip_off_duty: Clock3,
};

interface Props {
  events: DutyEvent[];
  selectedEventId: string | null;
  onSelectEvent: (event: DutyEvent) => void;
}

export function Itinerary({
  events,
  selectedEventId,
  onSelectEvent,
}: Props) {
  return (
    <section className="itinerary" aria-label="Itinerary">
      <div className="section-heading">
        <p className="eyebrow">Operational timeline</p>
        <h2>Planned duty timeline.</h2>
      </div>
      <ol>
        {events.map((event) => {
          const Icon = icons[event.kind];
          return (
            <li key={event.id}>
              <button
                type="button"
                className={selectedEventId === event.id ? "selected" : ""}
                onClick={() => onSelectEvent(event)}
                onFocus={() => onSelectEvent(event)}
              >
                {selectedEventId === event.id && (
                  <m.span
                    layoutId="itinerary-selection"
                    className="itinerary-selection"
                    transition={{
                      type: "spring",
                      stiffness: 420,
                      damping: 34,
                    }}
                  />
                )}
                <Icon aria-hidden="true" size={17} />
                <span>
                  <strong>{event.remark}</strong>
                  <small>{event.location.label}</small>
                </span>
                <span>
                  {formatDateTime(event.start_at)}
                  <small>{formatDuration(event.duration_minutes)}</small>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
