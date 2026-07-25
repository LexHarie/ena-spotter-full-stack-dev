import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DailyLogSheet } from "@/components/logs/DailyLogSheet";
import { buildDutyPath } from "@/components/logs/dutyGraphPath";
import type { DailyLog } from "@/lib/api/types";

const location = {
  id: "omaha",
  label: "Omaha, NE",
  longitude: -95.9345,
  latitude: 41.2565,
  country_code: "US" as const,
};

const log = {
  date: "2026-07-25",
  trip_day: 1,
  start_location: location,
  end_location: location,
  distance_m: 1030000,
  totals_minutes: {
    off_duty: 420,
    sleeper_berth: 300,
    driving: 660,
    on_duty_not_driving: 60,
  },
  cycle: {
    used_at_start_minutes: 1440,
    added_minutes: 750,
    remaining_at_end_minutes: 2010,
  },
  segments: [
    {
      event_id: "off",
      kind: "pre_trip_off_duty",
      duty_status: "off_duty",
      start_minute: 0,
      end_minute: 360,
      location,
      remark: "Off duty",
    },
    {
      event_id: "pickup",
      kind: "pickup",
      duty_status: "on_duty_not_driving",
      start_minute: 360,
      end_minute: 420,
      location,
      remark: "Pickup",
    },
    {
      event_id: "drive",
      kind: "driving",
      duty_status: "driving",
      start_minute: 420,
      end_minute: 1080,
      location,
      remark: "Drive",
    },
    {
      event_id: "rest",
      kind: "daily_rest",
      duty_status: "sleeper_berth",
      start_minute: 1080,
      end_minute: 1380,
      location,
      remark: "Daily rest",
    },
    {
      event_id: "post",
      kind: "post_trip_off_duty",
      duty_status: "off_duty",
      start_minute: 1380,
      end_minute: 1440,
      location,
      remark: "Off duty",
    },
  ],
} satisfies DailyLog;

describe("DailyLogSheet", () => {
  it("draws horizontal duty lines and vertical transitions", () => {
    expect(buildDutyPath(log.segments)).toContain("H");
    expect(buildDutyPath(log.segments)).toContain("V");
  });

  it("renders an original complete 24-hour planning sheet", () => {
    render(
      <DailyLogSheet
        log={log}
        totalLogs={2}
        homeTimezone="America/Chicago"
      />,
    );

    expect(
      screen.getByRole("heading", { name: /driver's daily log/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("24.0 h")).toBeInTheDocument();
    expect(screen.getByText(/not a certified ELD/i)).toBeInTheDocument();
    expect(screen.getByText("Driver")).toBeInTheDocument();
    expect(screen.getByText("Carrier")).toBeInTheDocument();
  });
});
