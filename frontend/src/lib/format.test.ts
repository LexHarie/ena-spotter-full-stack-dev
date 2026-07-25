import { describe, expect, it } from "vitest";

import { formatDateTime } from "@/lib/format";

describe("formatDateTime", () => {
  it("preserves the fixed-offset wall clock encoded by the planner", () => {
    expect(formatDateTime("2026-11-01T01:30:00-05:00")).toBe(
      "Nov 1, 1:30 AM",
    );
  });
});
