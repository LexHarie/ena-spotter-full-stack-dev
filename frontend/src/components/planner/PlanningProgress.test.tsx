import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlanningProgress } from "@/components/planner/PlanningProgress";

describe("PlanningProgress", () => {
  it("names all three meaningful planning stages", () => {
    const { rerender } = render(<PlanningProgress stage={0} />);
    expect(screen.getByText("Locating the truck route")).toBeInTheDocument();

    rerender(<PlanningProgress stage={1} />);
    expect(screen.getByText("Calculating duty limits")).toBeInTheDocument();

    rerender(<PlanningProgress stage={2} />);
    expect(screen.getByText("Building daily logs")).toBeInTheDocument();
  });
});
