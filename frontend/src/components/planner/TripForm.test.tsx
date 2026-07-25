import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TripForm } from "@/components/planner/TripForm";

vi.mock("@/hooks/useLocationSearch", () => ({
  useLocationSearch: () => ({
    options: [
      {
        id: "selected",
        label: "Chicago, IL, USA",
        longitude: -87.6298,
        latitude: 41.8781,
        country_code: "US",
      },
    ],
    loading: false,
    error: null,
  }),
}));

describe("TripForm", () => {
  it("shows exactly four visible inputs and submits selected locations", async () => {
    const user = userEvent.setup();
    const onPlan = vi.fn();
    render(<TripForm onPlan={onPlan} isPlanning={false} />);

    expect(screen.getAllByRole("combobox")).toHaveLength(3);
    expect(screen.getByLabelText(/current cycle used/i)).toBeInTheDocument();

    for (const name of [
      /current location/i,
      /pickup location/i,
      /drop-off location/i,
    ]) {
      const input = screen.getByRole("combobox", { name });
      await user.type(input, "Chicago");
      await user.keyboard("{ArrowDown}{Enter}");
    }
    await user.clear(screen.getByLabelText(/current cycle used/i));
    await user.type(screen.getByLabelText(/current cycle used/i), "24.25");
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(onPlan).toHaveBeenCalledWith(
      expect.objectContaining({ current_cycle_used_hours: 24.25 }),
    );
  });

  it("rejects cycle values that are not quarter hours", async () => {
    const user = userEvent.setup();
    render(<TripForm onPlan={vi.fn()} isPlanning={false} />);

    await user.clear(screen.getByLabelText(/current cycle used/i));
    await user.type(screen.getByLabelText(/current cycle used/i), "24.1");
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(await screen.findByText(/quarter-hour increments/i)).toBeInTheDocument();
  });

  it("does not coerce a cleared cycle field to zero", async () => {
    const user = userEvent.setup();
    render(<TripForm onPlan={vi.fn()} isPlanning={false} />);

    await user.clear(screen.getByLabelText(/current cycle used/i));
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(await screen.findByText(/enter current cycle usage/i)).toBeInTheDocument();
  });

  it("requires a new selection after an accepted location is edited", async () => {
    const user = userEvent.setup();
    render(<TripForm onPlan={vi.fn()} isPlanning={false} />);

    const current = screen.getByRole("combobox", {
      name: /current location/i,
    });
    await user.type(current, "Chicago");
    await user.click(screen.getByRole("option", { name: /Chicago/i }));
    await user.type(current, " altered");
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(await screen.findByText(/select a current location/i)).toBeInTheDocument();
  });
});
