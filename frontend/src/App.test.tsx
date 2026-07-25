import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "@/App";

describe("App", () => {
  it("introduces the RouteLog planning workflow", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: /a clear road ahead/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(/FMCSA-aware trip planning/i)).toBeInTheDocument();
  });
});
