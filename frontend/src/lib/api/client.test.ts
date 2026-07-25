import { afterEach, describe, expect, it, vi } from "vitest";

import { planTrip, searchLocations } from "@/lib/api/client";
import type { TripPlanRequest } from "@/lib/api/types";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("API client", () => {
  it("encodes location search and returns normalized candidates", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          locations: [
            {
              id: "chicago",
              label: "Chicago, IL",
              longitude: -87.6298,
              latitude: 41.8781,
              country_code: "US",
            },
          ],
        }),
        { status: 200 },
      ),
    );

    const results = await searchLocations("Chicago & nearby");

    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/locations/search/?q=Chicago%20%26%20nearby",
      expect.objectContaining({ signal: undefined }),
    );
    expect(results[0].id).toBe("chicago");
  });

  it("throws typed API errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "PROVIDER_UNAVAILABLE",
            message: "Routing is unavailable.",
            field: null,
            retryable: true,
          },
        }),
        { status: 503 },
      ),
    );

    await expect(searchLocations("Chicago")).rejects.toMatchObject({
      code: "PROVIDER_UNAVAILABLE",
      retryable: true,
    });
  });

  it("posts the complete trip request", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ daily_logs: [] }), { status: 200 }),
    );
    const request = {
      current_cycle_used_hours: 24,
    } as TripPlanRequest;

    await planTrip(request);

    expect(fetch).toHaveBeenCalledWith(
      "/api/v1/trips/plan/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
  });
});
