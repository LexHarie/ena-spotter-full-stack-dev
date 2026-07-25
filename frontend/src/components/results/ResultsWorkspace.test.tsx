import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ResultsWorkspace } from "@/components/results/ResultsWorkspace";
import type { TripPlanResponse } from "@/lib/api/types";

vi.mock("@/components/results/RouteMap", () => ({
  RouteMap: ({
    plan,
    selectedEventId,
    onSelectEvent,
  }: {
    plan: TripPlanResponse;
    selectedEventId: string | null;
    onSelectEvent: (event: TripPlanResponse["events"][number]) => void;
  }) => (
    <div data-testid="route-map">
      Map data © OpenStreetMap contributors
      <button type="button" onClick={() => onSelectEvent(plan.events[0])}>
        Select map stop
      </button>
      <output data-testid="map-selection">{selectedEventId}</output>
    </div>
  ),
}));

const plan = {
  meta: {
    generated_at: "2026-07-25T13:15:00+00:00",
    rule_set_version: "property-70-8-v1",
    home_terminal_timezone: "America/Chicago",
    fixed_utc_offset_minutes: -300,
    assumptions: [],
    warnings: [],
  },
  summary: {
    starts_at: "2026-07-25T08:15:00-05:00",
    ends_at: "2026-07-26T12:15:00-05:00",
    distance_m: 1609344,
    distance_miles: "1000.00",
    driving_minutes: 900,
    on_duty_not_driving_minutes: 120,
    off_duty_minutes: 30,
    sleeper_berth_minutes: 600,
    total_duration_minutes: 1680,
    cycle_used_start_minutes: 1440,
    cycle_used_end_minutes: 2460,
    cycle_restarts: 0,
    log_days: 2,
    fuel_stops: 1,
    rest_stops: 1,
  },
  route: {
    bounds: {
      west: -112.074,
      south: 33.4484,
      east: -87.6298,
      north: 41.8781,
    },
    geometry: {
      type: "LineString",
      coordinates: [
        [-87.6298, 41.8781],
        [-112.074, 33.4484],
      ],
    },
    legs: [
      {
        from: {
          id: "current",
          label: "Chicago, IL",
          longitude: -87.6298,
          latitude: 41.8781,
          country_code: "US",
        },
        to: {
          id: "pickup",
          label: "St. Louis, MO",
          longitude: -90.1994,
          latitude: 38.627,
          country_code: "US",
        },
        distance_m: 480000,
        duration_minutes: 270,
        steps: [
          {
            instruction: "Continue southwest",
            road_name: "I-55 S",
            distance_m: 480000,
            duration_minutes: 270,
          },
        ],
      },
    ],
  },
  events: [
    {
      id: "event-001",
      kind: "pickup",
      duty_status: "on_duty_not_driving",
      start_at: "2026-07-25T12:45:00-05:00",
      end_at: "2026-07-25T13:45:00-05:00",
      duration_minutes: 60,
      route_start_m: 480000,
      route_end_m: 480000,
      location: {
        id: "pickup",
        label: "St. Louis, MO",
        longitude: -90.1994,
        latitude: 38.627,
        country_code: "US",
      },
      remark: "Pickup",
    },
  ],
  stops: [],
  daily_logs: [],
} satisfies TripPlanResponse;

describe("ResultsWorkspace", () => {
  it("renders operational results in the approved order", () => {
    render(<ResultsWorkspace plan={plan} />);

    const map = screen.getByTestId("route-map");
    const summary = screen.getByRole("region", { name: /trip summary/i });
    const itinerary = screen.getByRole("region", { name: /itinerary/i });
    const directions = screen.getByRole("region", { name: /directions/i });

    expect(map.compareDocumentPosition(summary)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(summary.compareDocumentPosition(itinerary)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(itinerary.compareDocumentPosition(directions)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(screen.getByText("1,000 mi")).toBeInTheDocument();
    expect(screen.getByText("Pickup")).toBeInTheDocument();
  });

  it("shares selection between map markers and itinerary rows", async () => {
    const user = userEvent.setup();
    render(<ResultsWorkspace plan={plan} />);

    await user.click(screen.getByRole("button", { name: "Select map stop" }));

    expect(screen.getByTestId("map-selection")).toHaveTextContent("event-001");
    expect(screen.getByRole("button", { name: /Pickup/ })).toHaveClass(
      "selected",
    );
  });
});
