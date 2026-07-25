import { Accordion } from "@/components/ui/accordion";
import type { TripPlanResponse } from "@/lib/api/types";
import { formatDuration, formatMiles } from "@/lib/format";

export function Directions({ plan }: { plan: TripPlanResponse }) {
  let routeProgressM = 0;
  const steps = plan.route.legs.flatMap((leg) =>
    leg.steps.map((step) => {
      const routeStartM = routeProgressM;
      routeProgressM += step.distance_m;
      return { routeStartM, step };
    }),
  );
  return (
    <section aria-label="Directions" className="directions">
      <Accordion title={`${steps.length} turn-by-turn directions`}>
        <ol>
          {steps.map(({ routeStartM, step }, index) => (
            <li
              key={`${routeStartM}-${step.instruction}-${step.road_name}-${step.distance_m}-${step.duration_minutes}`}
            >
              <span>{index + 1}</span>
              <p>
                <strong>{step.instruction}</strong>
                <small>
                  {step.road_name || "Unnamed road"} ·{" "}
                  {formatMiles(step.distance_m / 1609.344)} ·{" "}
                  {formatDuration(step.duration_minutes)}
                </small>
              </p>
            </li>
          ))}
        </ol>
      </Accordion>
    </section>
  );
}
