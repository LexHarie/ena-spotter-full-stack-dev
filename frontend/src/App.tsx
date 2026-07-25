import { useState } from "react";

import routePlanning from "@/assets/route-planning.svg";
import { TripForm } from "@/components/planner/TripForm";
import { ApiClientError, planTrip } from "@/lib/api/client";
import type { TripPlanRequest, TripPlanResponse } from "@/lib/api/types";

export function App() {
  const [isPlanning, setIsPlanning] = useState(false);
  const [plan, setPlan] = useState<TripPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePlan = async (request: TripPlanRequest) => {
    setIsPlanning(true);
    setError(null);
    try {
      setPlan(await planTrip(request));
    } catch (caught) {
      setError(
        caught instanceof ApiClientError
          ? caught.message
          : "The trip plan could not be built.",
      );
    } finally {
      setIsPlanning(false);
    }
  };

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="flex items-center justify-between border-b border-line px-6 py-4">
        <a className="font-satoshi text-sm tracking-tight" href="/">
          <span className="mr-2 inline-block size-3 rounded-route bg-amber" />
          ROUTELOG
        </a>
        <p className="font-erode text-sm text-muted">
          FMCSA-aware trip planning
        </p>
      </header>
      <section className="opening-grid">
        <div className="opening-copy">
          <p className="eyebrow">Plan your run</p>
          <h1>A clear road ahead.</h1>
          <p>
            Build a truck route, place required stops, and generate a daily duty
            log for every day of the trip.
          </p>
          <TripForm onPlan={handlePlan} isPlanning={isPlanning} />
          {error && <p role="alert">{error}</p>}
          {plan && <p role="status">Trip plan ready.</p>}
        </div>
        <div className="empty-map" aria-label="Route planning preview">
          <img src={routePlanning} alt="" />
          <p>Your route and planned rests will appear here.</p>
        </div>
      </section>
      <section
        id="planning-assumptions"
        className="planning-assumptions"
        aria-labelledby="planning-assumptions-title"
      >
        <h2 id="planning-assumptions-title">Planning assumptions</h2>
        <p>
          Solo property carrier · aggregate 70 / 8 cycle only · fresh shift
          clocks · no adverse or split-sleeper exceptions · fixed home-terminal
          UTC offset
        </p>
      </section>
    </main>
  );
}
