import { useEffect, useRef, useState } from "react";

import { PlanningProgress } from "@/components/planner/PlanningProgress";
import { TripForm } from "@/components/planner/TripForm";
import { ResultsWorkspace } from "@/components/results/ResultsWorkspace";
import { EmptyState } from "@/components/states/EmptyState";
import { ErrorAlert } from "@/components/states/ErrorAlert";
import { Alert } from "@/components/ui/alert";
import { ApiClientError, planTrip } from "@/lib/api/client";
import type { TripPlanRequest, TripPlanResponse } from "@/lib/api/types";

const VISIBLE_FORM_FIELDS = new Set([
  "current_location",
  "pickup_location",
  "dropoff_location",
  "current_cycle_used_hours",
]);

export function App() {
  const [plan, setPlan] = useState<TripPlanResponse | null>(null);
  const [error, setError] = useState<ApiClientError | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [stage, setStage] = useState(0);
  const lastRequest = useRef<TripPlanRequest | null>(null);
  const activeController = useRef<AbortController | null>(null);

  useEffect(() => () => activeController.current?.abort(), []);

  const runPlan = async (request: TripPlanRequest) => {
    activeController.current?.abort();
    const controller = new AbortController();
    activeController.current = controller;
    lastRequest.current = request;
    setIsPlanning(true);
    setPlan(null);
    setError(null);
    setStage(0);
    const stageTimer = window.setInterval(
      () => setStage((current) => Math.min(2, current + 1)),
      650,
    );
    try {
      const result = await planTrip(request, controller.signal);
      setPlan(result);
      window.requestAnimationFrame(() => {
        document
          .querySelector<HTMLElement>(".results-workspace")
          ?.focus({ preventScroll: true });
        document
          .querySelector(".results-workspace")
          ?.scrollIntoView?.({ behavior: "smooth", block: "start" });
      });
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError(
        caught instanceof ApiClientError
          ? caught
          : new ApiClientError(
              "An unexpected error occurred.",
              "INTERNAL_ERROR",
              null,
              true,
              500,
            ),
      );
    } finally {
      window.clearInterval(stageTimer);
      if (!controller.signal.aborted) setIsPlanning(false);
    }
  };
  const hasInlineFieldError = VISIBLE_FORM_FIELDS.has(error?.field ?? "");

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="app-header">
        <a className="brand" href="/">
          <span />
          ROUTELOG
        </a>
        <p>FMCSA-aware trip planning</p>
      </header>
      <section className={`opening-grid${plan ? " plan-complete" : ""}`}>
        <div className="opening-copy">
          <p className="eyebrow">Plan your run</p>
          <h1>A clear road ahead.</h1>
          <p>
            Build a truck route, place required stops, and generate a daily
            duty log for every day of the trip.
          </p>
          <TripForm
            onPlan={runPlan}
            isPlanning={isPlanning}
            serverError={error}
          />
          {error && !hasInlineFieldError && (
            <ErrorAlert
              error={error}
              onRetry={() => {
                if (lastRequest.current) void runPlan(lastRequest.current);
              }}
            />
          )}
        </div>
        {!plan &&
          (isPlanning ? <PlanningProgress stage={stage} /> : <EmptyState />)}
      </section>
      <section
        id="planning-assumptions"
        className="planning-assumptions"
        aria-labelledby="planning-assumptions-title"
      >
        <h2 id="planning-assumptions-title">Planning assumptions</h2>
        <p>
          Solo property carrier · aggregate 70 / 8 cycle only · fresh shift
          clocks · no adverse or split-sleeper exceptions · fixed
          home-terminal UTC offset
        </p>
      </section>
      {plan?.meta.warnings.map((warning) => (
        <Alert key={warning} title="Planning assumption">
          <p>{warning}</p>
        </Alert>
      ))}
      {plan && <ResultsWorkspace plan={plan} />}
      <footer className="app-footer">
        Route and timing data are estimates. Public provider quotas may
        interrupt planning. RouteLog creates advisory planning copies, not
        certified ELD records.
      </footer>
    </main>
  );
}
