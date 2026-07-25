import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "@/App";
import { ApiClientError, planTrip } from "@/lib/api/client";

vi.mock("@/components/planner/TripForm", () => ({
  TripForm: ({ onPlan }: { onPlan: (value: object) => void }) => (
    <button type="button" onClick={() => onPlan({})}>
      Build trip plan
    </button>
  ),
}));

vi.mock("@/components/results/ResultsWorkspace", () => ({
  ResultsWorkspace: ({ plan }: { plan: { label?: string } }) => (
    <section aria-label="Generated trip plan">{plan.label ?? "Plan"}</section>
  ),
}));

vi.mock("@/lib/api/client", async () => {
  const actual = await vi.importActual<typeof import("@/lib/api/client")>(
    "@/lib/api/client",
  );
  return { ...actual, planTrip: vi.fn() };
});

beforeEach(() => {
  vi.mocked(planTrip).mockReset();
});

describe("App planning flow", () => {
  it("replaces the empty state with generated results", async () => {
    vi.mocked(planTrip).mockResolvedValue({
      meta: { warnings: ["Fixed-offset daylight-saving warning."] },
    } as never);
    const user = userEvent.setup();
    render(<App />);

    expect(screen.getByText(/route and planned rests/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(
      await screen.findByRole("region", { name: /generated trip plan/i }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/route and planned rests/i),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Fixed-offset daylight-saving warning.",
    );
  });

  it("preserves a retry action for recoverable provider failures", async () => {
    vi.mocked(planTrip)
      .mockRejectedValueOnce(
        new ApiClientError(
          "Routing is unavailable.",
          "PROVIDER_UNAVAILABLE",
          null,
          true,
          503,
        ),
      )
      .mockResolvedValueOnce({ meta: { warnings: [] } } as never);
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Routing is unavailable.",
    );
    await user.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => expect(planTrip).toHaveBeenCalledTimes(2));
    expect(
      await screen.findByRole("region", { name: /generated trip plan/i }),
    ).toBeInTheDocument();
  });

  it("does not offer retry for a route that cannot be built", async () => {
    vi.mocked(planTrip).mockRejectedValue(
      new ApiClientError(
        "No truck route was found.",
        "ROUTE_NOT_FOUND",
        null,
        false,
        422,
      ),
    );
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No truck route was found.",
    );
    expect(
      screen.queryByRole("button", { name: /retry/i }),
    ).not.toBeInTheDocument();
  });

  it("replaces an earlier plan when the form is regenerated", async () => {
    vi.mocked(planTrip)
      .mockResolvedValueOnce({
        label: "First plan",
        meta: { warnings: [] },
      } as never)
      .mockResolvedValueOnce({
        label: "Second plan",
        meta: { warnings: [] },
      } as never);
    const user = userEvent.setup();
    render(<App />);

    await user.click(screen.getByRole("button", { name: /build trip plan/i }));
    expect(await screen.findByText("First plan")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /build trip plan/i }));
    expect(await screen.findByText("Second plan")).toBeInTheDocument();
    expect(screen.queryByText("First plan")).not.toBeInTheDocument();
  });
});
