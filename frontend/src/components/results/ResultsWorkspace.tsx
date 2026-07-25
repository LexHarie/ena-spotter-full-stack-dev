import { domMax, LazyMotion, m } from "motion/react";
import { useState } from "react";

import { DailyLogSheet } from "@/components/logs/DailyLogSheet";
import { PrintToolbar } from "@/components/logs/PrintToolbar";
import { Directions } from "@/components/results/Directions";
import { Itinerary } from "@/components/results/Itinerary";
import { RouteMap } from "@/components/results/RouteMap";
import { TripSummary } from "@/components/results/TripSummary";
import type { DutyEvent, TripPlanResponse } from "@/lib/api/types";

export function ResultsWorkspace({ plan }: { plan: TripPlanResponse }) {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const selectEvent = (event: DutyEvent) => setSelectedEventId(event.id);

  return (
    <LazyMotion features={domMax} strict>
      <m.section
        className="results-workspace"
        aria-label="Generated trip plan"
        initial={{ opacity: 0, y: 18, filter: "blur(8px)" }}
        animate={{ opacity: 1, y: 0, filter: "blur(0)" }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      >
        <RouteMap
          plan={plan}
          selectedEventId={selectedEventId}
          onSelectEvent={selectEvent}
        />
        <TripSummary plan={plan} />
        <Itinerary
          events={plan.events}
          selectedEventId={selectedEventId}
          onSelectEvent={selectEvent}
        />
        <Directions plan={plan} />
        <section className="daily-logs" aria-label="Daily log sheets">
          <PrintToolbar />
          {plan.daily_logs.map((log) => (
            <DailyLogSheet
              key={log.date}
              log={log}
              totalLogs={plan.daily_logs.length}
              homeTimezone={plan.meta.home_terminal_timezone}
            />
          ))}
        </section>
      </m.section>
    </LazyMotion>
  );
}
