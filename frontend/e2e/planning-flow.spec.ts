import { expect, test } from "@playwright/test";

import plan from "./fixtures/plan.json" with { type: "json" };

const locations = {
  Chicago: {
    id: "current",
    label: "Chicago, IL, USA",
    longitude: -87.6298,
    latitude: 41.8781,
    country_code: "US",
  },
  "St. Louis": {
    id: "pickup",
    label: "St. Louis, MO, USA",
    longitude: -90.1994,
    latitude: 38.627,
    country_code: "US",
  },
  Omaha: {
    id: "dropoff",
    label: "Omaha, NE, USA",
    longitude: -95.9345,
    latitude: 41.2565,
    country_code: "US",
  },
};

test("plans a route and exposes every required output", async ({ page }) => {
  await page.route("**tile.openstreetmap.org/**", (route) => route.abort());
  await page.route("**/api/v1/locations/search/**", async (route) => {
    const query = new URL(route.request().url()).searchParams.get("q") ?? "";
    const key = Object.keys(locations).find((name) => query.includes(name));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        locations: key ? [locations[key as keyof typeof locations]] : [],
      }),
    });
  });
  await page.route("**/api/v1/trips/plan/", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(plan),
    }),
  );
  await page.goto("/");

  for (const [label, query] of [
    ["Current location", "Chicago"],
    ["Pickup location", "St. Louis"],
    ["Drop-off location", "Omaha"],
  ] as const) {
    await page.getByRole("combobox", { name: label }).fill(query);
    await page.getByRole("option").click();
  }
  await page.getByLabel("Current cycle used (hours)").fill("24");
  await page.getByRole("button", { name: "Build trip plan" }).click();

  await expect(
    page.getByRole("region", { name: "Planned route map" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Trip summary" }),
  ).toContainText("640 mi");
  await expect(
    page.getByRole("region", { name: "Itinerary" }),
  ).toContainText("Pickup");
  await expect(
    page.getByRole("region", { name: "Directions" }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: "Daily log sheets" }),
  ).toContainText("DRIVER'S DAILY LOG");

  await page.evaluate(() => {
    window.print = () => {
      document.body.dataset.printInvoked = "true";
    };
  });
  await page.getByRole("button", { name: "Print / Save PDF" }).click();
  await expect(page.locator("body")).toHaveAttribute(
    "data-print-invoked",
    "true",
  );

  await page.emulateMedia({ media: "print" });
  await expect(page.locator(".print-toolbar")).toBeHidden();
  await expect
    .poll(() =>
      page
        .locator(".daily-log-sheet")
        .first()
        .evaluate((element) => getComputedStyle(element).breakInside),
    )
    .toBe("avoid");
});
