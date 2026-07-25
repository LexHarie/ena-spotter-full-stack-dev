import { describe, expect, it } from "vitest";

import { getTripStartContext } from "@/lib/time";

describe("getTripStartContext", () => {
  it("rounds to the next quarter hour and keeps the browser timezone", () => {
    const context = getTripStartContext(
      new Date("2026-07-25T13:07:22.000Z"),
      "America/Chicago",
      300,
    );

    expect(context.starts_at).toBe("2026-07-25T08:15:00-05:00");
    expect(context.home_terminal_timezone).toBe("America/Chicago");
  });
});
