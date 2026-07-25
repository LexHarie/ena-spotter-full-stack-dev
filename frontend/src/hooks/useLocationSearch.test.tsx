import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useLocationSearch } from "@/hooks/useLocationSearch";
import { searchLocations } from "@/lib/api/client";
import type { LocationCandidate } from "@/lib/api/types";

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>(
    "@/lib/api/client",
  );
  return { ...actual, searchLocations: vi.fn() };
});

const chicago = {
  id: "chicago",
  label: "Chicago, IL, USA",
  longitude: -87.6298,
  latitude: 41.8781,
  country_code: "US" as const,
};
const dallas = {
  id: "dallas",
  label: "Dallas, TX, USA",
  longitude: -96.797,
  latitude: 32.7767,
  country_code: "US" as const,
};

beforeEach(() => {
  vi.useFakeTimers();
  vi.mocked(searchLocations).mockReset();
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useLocationSearch", () => {
  it("waits 300 milliseconds before searching", async () => {
    vi.mocked(searchLocations).mockResolvedValue([chicago]);
    const { result } = renderHook(() => useLocationSearch("Chicago"));

    act(() => {
      vi.advanceTimersByTime(299);
    });
    expect(searchLocations).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(1);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(searchLocations).toHaveBeenCalledWith(
      "Chicago",
      expect.any(AbortSignal),
    );
    expect(result.current.options).toEqual([chicago]);
  });

  it("discards a stale response even when its transport ignores abort", async () => {
    let resolveChicago!: (value: LocationCandidate[]) => void;
    let resolveDallas!: (value: LocationCandidate[]) => void;
    vi.mocked(searchLocations).mockImplementation(
      (query) =>
        new Promise((resolve) => {
          if (query === "Chicago") resolveChicago = resolve;
          if (query === "Dallas") resolveDallas = resolve;
        }),
    );
    const { result, rerender } = renderHook(
      ({ query }) => useLocationSearch(query),
      { initialProps: { query: "Chicago" } },
    );

    act(() => {
      vi.advanceTimersByTime(300);
    });
    rerender({ query: "Dallas" });
    act(() => {
      vi.advanceTimersByTime(300);
    });
    await act(async () => {
      resolveDallas([dallas]);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.options).toEqual([dallas]);

    await act(async () => {
      resolveChicago([chicago]);
      await Promise.resolve();
      await Promise.resolve();
    });
    expect(result.current.options).toEqual([dallas]);
  });
});
