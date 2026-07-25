# RouteLog HOS Trip Planner and Daily Log Generator

**Status:** Approved design

**Date:** 2026-07-25

**Primary brief:** `deliverables.md`

## 1. Product definition

RouteLog is a single-page trip-planning application for a solo, property-carrying commercial driver. The driver supplies a current location, pickup location, drop-off location, and current 70-hour/8-day cycle usage. The application retrieves a truck route, applies the agreed hours-of-service assumptions, places required work and rest events along that route, and produces:

- A map containing the route, pickup, drop-off, fuel, break, sleeper, and restart markers.
- A concise trip summary.
- A chronological itinerary and collapsible turn-by-turn directions.
- One original RouteLog Driver's Daily Log for every home-terminal calendar day touched by the plan.
- Print-ready output that can be saved as a PDF.

The generated logs are planning worksheets. RouteLog is not a certified electronic logging device, does not replace a carrier's official record-of-duty-status process, and must not present itself as doing either.

## 2. Success criteria

The product is successful when:

1. A user can submit all four required inputs without needing an account.
2. Locations are resolved to United States coordinates and the route passes through current location, pickup, and drop-off in that order.
3. The displayed route, distance, directions, and stop markers come from OpenRouteService data rather than guessed straight-line calculations.
4. The schedule never plans driving beyond the agreed 11-hour, 14-hour, 8-hour-break, or 70-hour/8-day limits.
5. Pickup and drop-off each contribute exactly 60 minutes of on-duty, not-driving time.
6. A 30-minute on-duty fuel stop occurs before each additional 1,000 route miles and can satisfy the 30-minute non-driving break requirement.
7. The planner inserts 10 consecutive sleeper-berth hours when a new driving shift is required and a 34-hour restart when the supplied cycle capacity is insufficient.
8. Every generated daily log covers midnight to midnight in the home-terminal timezone and its four duty totals equal exactly 24 hours.
9. Multi-day routes show every log sheet in the page and print one log sheet per page.
10. The deployed application is responsive, keyboard accessible, visually polished, and does not expose the routing API key.

## 3. Scope

### Included

- React, TypeScript, and Vite frontend.
- Django and Django REST Framework backend.
- OpenRouteService geocoding and `driving-hgv` directions.
- OpenStreetMap tiles rendered with React Leaflet and visible attribution.
- Deterministic hours-of-service scheduling.
- Original HTML/SVG daily logs.
- In-browser results, print layout, and browser Save as PDF.
- Two Vercel projects connected to one GitHub monorepo.
- Automated tests and deployment documentation.

### Excluded

- Authentication, driver accounts, saved trip history, or a database.
- Carrier administration, dispatch collaboration, or fleet management.
- Live traffic, weather, toll, fuel-price, or parking-availability data.
- Team drivers, passenger-carrying rules, split sleeper-berth rules, adverse-driving extensions, short-haul exceptions, or state-specific rules.
- Editing official ELD records, ELD hardware integration, certification, or FMCSA file transfer.
- Automatic driver, carrier, vehicle, shipping-document, or signature data that the required inputs do not provide.
- A custom navigation engine or a fallback route fabricated from straight-line distance.

## 4. Regulatory and planning assumptions

The scheduling model uses the assessment assumptions plus the current federal property-carrier limits documented by FMCSA:

- Solo property-carrying driver.
- 70 hours on duty in eight consecutive days.
- Maximum 11 hours of driving after 10 consecutive hours off duty.
- No driving after the 14th consecutive hour after coming on duty.
- A qualifying interruption of at least 30 consecutive non-driving minutes after eight cumulative driving hours.
- A 34-consecutive-hour restart resets the modeled cycle usage to zero.
- No adverse conditions, exceptions, or split sleeper periods.
- Fuel at least once per 1,000 miles.
- Pickup and drop-off service each take one hour.

Because the brief supplies only an aggregate current-cycle-used value and not eight days of duty history, RouteLog cannot calculate rolling daily recaps or hours that naturally return at midnight. V1 therefore treats the supplied value as the driver's on-duty total at trip start, subtracts all planned driving and on-duty time from the remaining `70 - used` hours, and only restores capacity through a modeled 34-hour restart.

The user is assumed to begin after at least 10 consecutive hours off duty, with fresh 11-hour driving, 14-hour shift, and eight-hour break clocks. Pre-trip off-duty time may have begun on the preceding day.

The browser's IANA timezone and UTC offset at submission are treated as the home-terminal log clock. V1 freezes that starting offset for the generated plan, so it does not change clocks as the truck crosses geographic time zones or a daylight-saving transition. This keeps every modeled log day at exactly 1,440 elapsed minutes. The IANA name is retained to detect a daylight-saving transition and display a warning that the plan uses the starting offset throughout.

The trip begins at the next quarter-hour boundary after submission. All generated transitions use quarter-hour precision.

## 5. User experience

### 5.1 Page structure

RouteLog is a focused single-page operations desk without dashboard navigation.

Before planning, the opening viewport uses an approximately 40/60 split:

- Left: the four-field trip form, cycle-capacity meter, assumptions link, and primary action.
- Right: an empty map state with a restrained route-planning illustration.

The four primary fields are:

1. Current location.
2. Pickup location.
3. Drop-off location.
4. Current cycle used, from 0 to 70 hours in quarter-hour increments.

Location inputs become debounced, cancellable United States autocomplete comboboxes after three characters. A typed value must be selected from the results before submission. Validation remains adjacent to its field.

Submission communicates three meaningful stages: locating the route, calculating the schedule, and building daily logs.

After success, the page presents:

1. Route map and stop markers.
2. Trip summary.
3. Chronological itinerary.
4. Collapsible turn-by-turn instructions.
5. Every daily log, stacked and visible.
6. Print / Save PDF action.

Editing an input and regenerating replaces the result in place. Mobile keeps the same order in one column rather than creating a separate interaction model.

### 5.2 Visual system

The approved visual direction is **Map-first operations desk / Roadbook Editorial**.

- Paper: `#F4F0E7`
- Ink navy: `#182231`
- Safety amber: `#E59A18`
- Muted map green: approximately `#365C4C`
- Operational type: Satoshi Bold
- Editorial type: Erode Regular

The supplied Fontshare kit is self-hosted. Its EULA and required notices must be retained in the repository. Satoshi is used for metrics, labels, controls, and wayfinding; Erode is used for editorial headings and supporting copy.

UI sources are intentionally limited:

- shadcn/ui for accessible form, dialog, alert, accordion, and command primitives.
- Lucide for the icon system.
- Aceternity patterns only where they improve the stateful planning button or itinerary.
- Magic UI only for restrained Blur Fade, Number Ticker, Animated List, or Dot Pattern treatments.
- unDraw only for the initial empty state.

Motion must clarify state changes, respect `prefers-reduced-motion`, and never delay access to results. The interface must avoid a collage of unrelated component-library styles, excessive cards, gratuitous gradients, and decorative dashboard chrome.

### 5.3 Map behavior

The map:

- Fits the full route after a plan succeeds.
- Draws one route line through current location, pickup, and drop-off.
- Uses distinct markers for current location, pickup, drop-off, fuel, 30-minute break, 10-hour sleeper rest, and 34-hour restart.
- Opens a compact marker detail containing time, duty status, location, duration, and reason.
- Keeps required OpenStreetMap attribution visible.
- Mirrors the itinerary selection when a marker or itinerary event is focused.

Turn-by-turn instructions are available but collapsed by default so the map and operational stops remain primary.

## 6. Original RouteLog Driver's Daily Log

The final product does not draw on top of `blank-paper-log.png`. That asset and the supplied FMCSA PDF are reference material only.

Each log is an original semantic HTML/SVG sheet using the Roadbook visual system. It contains:

- RouteLog mark and "Driver's Daily Log" title.
- "Planned record of duty status" and "Planning copy" language.
- Date and trip-day number.
- Day-start and day-end locations.
- Route distance, driving total, and 70/8 rule-set label.
- Writable driver, carrier, vehicle/unit, shipping-document, and signature fields.
- A midnight-to-midnight graph with Off Duty, Sleeper Berth, Driving, and On Duty rows.
- Hour divisions and quarter-hour transition precision.
- A vector duty-status line.
- Per-status totals.
- Time, reason, and location remarks for every duty transition.
- Cycle used before the day, cycle added that day, and modeled remaining capacity.
- A visible planning/certification disclaimer.

The app auto-fills only facts available from the four inputs, the route response, or the deterministic scheduler. It must not invent administrative identity data.

Events spanning midnight are split into two daily segments without changing their elapsed duration. The first sheet begins at midnight with Off Duty until the trip start; the final sheet ends with Off Duty after drop-off service. Every sheet asserts:

```text
off_duty + sleeper_berth + driving + on_duty_not_driving = 1,440 minutes
```

Screen presentation may scale responsively, but printing fixes each log to its own letter-size page with no clipped graph, remarks, or disclaimer.

## 7. System architecture

The repository is a monorepo:

```text
frontend/                   React, TypeScript, Vite
backend/                    Django, Django REST Framework
docs/                       design, architecture, setup, assumptions
```

The runtime flow is:

```text
React form
  -> Django validation
  -> OpenRouteService adapter
  -> normalized route model
  -> pure HOS scheduler
  -> route + stops + events + daily logs
  -> React map, itinerary, and print views
```

### 7.1 Frontend responsibilities

- Render the form, accessible location comboboxes, progress states, map, itinerary, logs, and print view.
- Keep the selected normalized locations and generated plan in memory.
- Submit the rounded start timestamp, its UTC offset, and browser IANA timezone as hidden context.
- Call only same-origin `/api/*` URLs.
- Never receive or bundle the OpenRouteService API key.
- Cancel stale autocomplete requests and cache recent normalized results in memory.

### 7.2 Backend responsibilities

- Validate and normalize the request.
- Restrict geocoding to United States candidates.
- Keep the OpenRouteService key server-side.
- Translate provider responses into provider-neutral route models.
- Calculate all duty events through a pure, deterministic scheduler.
- Split events into calendar-day log models.
- Return typed, stable JSON and typed errors.
- Emit no guessed route or schedule when routing fails.

The backend is stateless. Django admin, authentication, sessions, persistence, uploads, and background workers are omitted.

### 7.3 Provider boundary

The routing layer exposes a small internal interface:

```text
search_locations(query) -> LocationCandidate[]
build_route(current, pickup, dropoff) -> NormalizedRoute
reverse_geocode(coordinate) -> NormalizedLocation
```

The OpenRouteService implementation uses:

- Geocoding with a United States boundary.
- Directions with the `driving-hgv` profile.
- GeoJSON route geometry.
- Leg and step distances, durations, instructions, and waypoint indexes.

The adapter validates that required route fields are present and finite. It uses a bounded timeout and at most one retry for transient network or 5xx failures. It does not retry invalid requests or route-not-found responses. A provider rate limit is surfaced with a retryable typed error and any safe retry timing rather than hidden by a loop.

## 8. Scheduling engine

The scheduling engine is independent of Django, HTTP, React, and OpenRouteService. It accepts a normalized route and planning assumptions and returns immutable duty events.

### 8.1 Internal units

- Duration: integer minutes.
- Distance: integer meters.
- Timestamps: timezone-aware instants plus the home-terminal IANA name and fixed starting UTC offset.
- Coordinates: GeoJSON order, `[longitude, latitude]`.
- Display hours and miles: derived only at serialization/render time.

These choices prevent fractional-hour accumulation and daily-total drift.

### 8.2 Duty statuses and event kinds

Duty statuses:

- `off_duty`
- `sleeper_berth`
- `driving`
- `on_duty_not_driving`

Event kinds:

- `pre_trip_off_duty`
- `driving`
- `pickup`
- `dropoff`
- `fuel`
- `break`
- `daily_rest`
- `cycle_restart`
- `post_trip_off_duty`

Every event has a stable ID, kind, duty status, start and end time, integer duration, route-progress position, normalized location, and human-readable remark.

### 8.3 Scheduling sequence

1. Begin with fresh shift and break clocks and `70 hours - current cycle used` available.
2. Drive from current location toward pickup while monitoring the nearest driving, shift, break, cycle, fuel, route-step, and leg boundary.
3. At pickup, add 60 minutes of on-duty, not-driving service.
4. Continue toward drop-off under the same constraint model.
5. Before each additional 1,000 route miles, add a 30-minute on-duty, not-driving fuel stop.
6. At drop-off, add 60 minutes of on-duty, not-driving service.
7. Fill the remaining final calendar day with Off Duty.

At each advancement, the scheduler consumes only the duration and distance available before the nearest boundary:

- Before exceeding eight cumulative driving hours without a qualifying interruption, add 30 minutes Off Duty unless an already scheduled pickup, drop-off, or fuel interval of at least 30 minutes qualifies first.
- Before exceeding 11 driving hours or the 14-hour driving window, add 10 consecutive hours in Sleeper Berth and reset the shift-driving and break clocks.
- Before driving or performing on-duty service beyond the available 70/8 capacity, add 34 consecutive hours Off Duty and reset the modeled cycle usage.

Pickup, drop-off, and fuel consume cycle and 14-hour-window time. Because each lasts at least 30 consecutive minutes without driving, each also resets the eight-hour driving-break counter. Ordinary 30-minute Off Duty breaks do not extend the 14-hour window.

### 8.4 Route positioning

The normalized route maintains cumulative distance and duration across legs and steps. When the scheduler creates an en-route stop, it locates the event at the current route-progress position, interpolates a coordinate within the relevant geometry section, and reverse-geocodes that coordinate for the remark and marker.

The map and logs use the same event objects, preventing disagreement between the displayed stop, timestamp, and written remark.

### 8.5 Daily-log projection

After scheduling, a projector:

1. Finds each midnight boundary using the fixed home-terminal offset captured at submission.
2. Clips events at those boundaries.
3. Adds pre-trip and post-trip Off Duty coverage where needed.
4. Groups segments by date.
5. Computes four status totals and the day's cycle contribution.
6. Rejects any day whose coverage overlaps, contains a gap, or does not total 1,440 minutes.

## 9. API contract

All JSON uses `snake_case`. Django REST Framework serializers are the canonical contract; frontend TypeScript types mirror that contract and are exercised by shared response fixtures.

### 9.1 Location search

```http
GET /api/v1/locations/search/?q=chicago
```

Successful response:

```json
{
  "locations": [
    {
      "id": "provider-stable-id",
      "label": "Chicago, Cook County, Illinois, USA",
      "longitude": -87.6298,
      "latitude": 41.8781,
      "country_code": "US"
    }
  ]
}
```

The query is trimmed and length-bounded. Fewer than three characters returns no provider request. Results are capped at five.

### 9.2 Trip planning

```http
POST /api/v1/trips/plan/
Content-Type: application/json
```

Request:

```json
{
  "current_location": {
    "id": "ors:current-location",
    "label": "Chicago, Illinois, USA",
    "longitude": -87.6298,
    "latitude": 41.8781,
    "country_code": "US"
  },
  "pickup_location": {
    "id": "ors:pickup-location",
    "label": "St. Louis, Missouri, USA",
    "longitude": -90.1994,
    "latitude": 38.6270,
    "country_code": "US"
  },
  "dropoff_location": {
    "id": "ors:dropoff-location",
    "label": "Phoenix, Arizona, USA",
    "longitude": -112.0740,
    "latitude": 33.4484,
    "country_code": "US"
  },
  "current_cycle_used_hours": 24.0,
  "starts_at": "2026-07-25T08:15:00-05:00",
  "home_terminal_timezone": "America/Chicago"
}
```

Validation requires three selected United States location candidates, finite valid coordinates, cycle usage from 0 through 70 in quarter-hour increments, an offset-aware start timestamp, and a valid IANA timezone whose offset matches the timestamp at trip start.

The response contains:

- `meta`: generation time, rule-set version, explicit assumptions, and warnings.
- `summary`: trip start/end, distance, duration, duty totals, stop counts, log-day count, and cycle impact.
- `route`: GeoJSON geometry, bounds, legs, and turn steps.
- `stops`: ordered pickup, drop-off, fuel, break, sleeper, and restart markers.
- `events`: the canonical chronological duty-event list.
- `daily_logs`: date-grouped, midnight-clipped segments, totals, remarks, and cycle recap.

The planning response sends `Cache-Control: no-store`.

### 9.3 Error envelope

```json
{
  "error": {
    "code": "ROUTE_NOT_FOUND",
    "message": "No truck route was found between the selected locations.",
    "field": null,
    "retryable": false
  }
}
```

Stable codes include:

- `VALIDATION_ERROR`
- `LOCATION_NOT_FOUND`
- `ROUTE_NOT_FOUND`
- `PROVIDER_RATE_LIMITED`
- `PROVIDER_UNAVAILABLE`
- `PLANNING_INFEASIBLE`
- `INTERNAL_ERROR`

Validation and location errors return to the relevant field. Provider errors preserve all inputs and expose a retry action. The application never replaces a failed route with an invented schedule.

## 10. Failure and empty states

- Before input: route-planning empty state and a short explanation of the four required fields.
- No autocomplete matches: prompt the user to refine the city, state, or address.
- Stale autocomplete response: discard it using request cancellation or request identity.
- Invalid cycle value: inline range and quarter-hour message.
- Route not found: retain the form and explain that a truck route could not be built.
- Rate limited or transient provider failure: retain inputs, show a non-alarming service message, and offer Retry.
- Scheduling invariant failure: do not render partial logs; show a recoverable planning error and record diagnostic context server-side.
- Print failure is left to the browser, but print CSS must provide a normal HTML fallback rather than requiring image generation.

## 11. Accessibility, responsiveness, and printing

- Every control has a programmatic label and visible focus state.
- Autocomplete follows combobox/listbox keyboard behavior.
- Loading updates are announced without repeatedly stealing focus.
- Errors are associated with the relevant field and summarized near the action.
- Map information is duplicated in the textual itinerary; the map is not the only source of meaning.
- Color is never the only distinction between stop or duty types.
- Motion is disabled or reduced under `prefers-reduced-motion`.
- Mobile preserves the desktop reading order.
- Screen logs may scroll horizontally only at the graph level if unavoidable; the primary page must not.
- Print CSS hides form chrome, map controls, animations, and interactive-only controls.
- Each daily log uses `break-after: page` and retains colors legibly in grayscale.

## 12. Testing strategy

### 12.1 Backend unit tests

The pure scheduler receives deterministic normalized-route fixtures. Parameterized boundary tests cover:

- Short trip requiring no break.
- Exactly eight driving hours and the first minute beyond eight.
- Pickup or fuel satisfying the 30-minute interruption.
- Exactly 11 driving hours and a trip requiring another driving shift.
- A 14-hour limit reached before the 11-hour driving limit.
- Fuel placement before 1,000 and 2,000 route miles.
- Zero, partial, and fully exhausted cycle capacity.
- A 34-hour restart spanning one or more midnights.
- Pickup or drop-off service when remaining cycle capacity is insufficient.
- Events and rests spanning midnight.
- Multi-day trips and trips ending exactly at midnight.

Every schedule test asserts:

- No driving interval violates the 8-, 11-, 14-, or 70-hour rules.
- Events are ordered, non-overlapping, and positive in duration.
- Fuel gaps never exceed 1,000 planned route miles.
- Pickup and drop-off each total 60 minutes.
- Event route progress never decreases or exceeds route distance.
- Every daily log contains exactly 1,440 minutes.
- The sum of daily segments equals the sum of canonical events after boundary clipping.

Provider-adapter tests use recorded, reduced fixtures and never call the live free API.

### 12.2 Backend API tests

- Request validation and normalization.
- Stable success serialization.
- Typed provider and planning errors.
- API-key absence from responses and logs.
- `no-store` behavior for generated plans.
- OpenRouteService timeouts and response-shape failures.

### 12.3 Frontend tests

Vitest and Testing Library cover:

- Required fields and cycle validation.
- Debounced, keyboard-operable autocomplete.
- Cancellation of stale search results.
- Progress stages.
- Field, route, provider, and retry states.
- Map marker and itinerary synchronization.
- Summary and daily-log rendering.
- Editing and regenerating in place.
- Print-control behavior.

### 12.4 End-to-end and build checks

Playwright uses a deterministic route fixture to verify:

```text
fill form -> select locations -> generate -> inspect map and stops
-> inspect every daily log -> open print view
```

Continuous integration runs without external network dependency:

- Python formatting/linting.
- Django system checks.
- Pytest.
- TypeScript checking.
- ESLint.
- Vitest.
- Production frontend build.
- Playwright's primary planning flow.

One controlled post-deployment smoke test uses the live provider to verify environment configuration, routing, map tiles, and same-origin API proxying.

## 13. Deployment

One GitHub monorepo connects to two Vercel projects:

```text
RouteLog Frontend
  root directory: frontend/
  output: Vite static application

RouteLog Backend
  root directory: backend/
  output: Django on Vercel Python Functions
```

Deployment order:

1. Deploy the backend and assign its stable production domain.
2. Configure backend secrets:
   - `ORS_API_KEY`
   - `DJANGO_SECRET_KEY`
   - `DJANGO_ALLOWED_HOSTS`
   - production debug setting
3. Configure the frontend's `vercel.json` so `/api/:path*` rewrites to the backend production domain before the SPA fallback.
4. Deploy the frontend and treat its domain as the single public application URL.
5. Run the production smoke test.

The browser calls `/api/*`; Vercel proxies those requests without changing the visible URL. Django does not enable broad cross-origin access.

The Python runtime is currently Beta. This is acceptable for a small stateless assessment application, but it is an explicit hosting risk. If the product later needs durable data, queues, long-running work, or stricter runtime guarantees, the Django project should move to a conventional Python service or VPS without changing the frontend contract.

## 14. Repository and handoff deliverables

The completed repository includes:

- Frontend and backend source.
- Tests and continuous-integration workflow.
- `.env.example` files with no secret values.
- Setup and local-development commands.
- Architecture, HOS assumptions, provider limits, and disclaimer documentation.
- Font and third-party license notices.
- Production frontend URL.
- A concise deployment verification record.
- A 3–5 minute Loom outline covering the user flow, architecture, scheduling engine, custom daily log, tests, and deployed application.

The actual Loom recording and any account-bound Vercel or GitHub publication require access to the user's accounts if they are not already available in the environment.

## 15. Risks and accepted limitations

- OpenRouteService duration, geometry, and instructions are estimates and can change with provider data.
- Free-provider quotas may temporarily prevent new plans.
- Public OpenStreetMap tiles are appropriate only while usage remains within the tile policy; heavier production use requires a dedicated tile provider.
- Aggregate cycle usage cannot reconstruct rolling hours that return during the trip.
- The home-terminal timezone is inferred from the browser rather than supplied as a visible field.
- The log clock freezes the trip-start UTC offset; a plan crossing a daylight-saving transition is warned and does not switch offsets mid-plan.
- Administrative identity fields remain writable because the brief does not collect those values.
- The generated schedule is an advisory plan, not evidence of actual duty activity.
- Vercel's Python runtime is Beta.

These limitations are disclosed in the interface and README rather than hidden behind fabricated precision.

## 16. References

- Local assessment brief: `deliverables.md`
- Local FMCSA reference: `fmcsa-hos-395-drivers-guide-to-hos-2022-04-28-0-1-.pdf`
- [FMCSA summary of hours-of-service regulations](https://www.fmcsa.dot.gov/regulations/hours-service/summary-hours-service-regulations)
- [FMCSA ELD technical specifications FAQ](https://eld.fmcsa.dot.gov/FAQ/Topics?name=ELD_Technical_Specifications)
- [OpenRouteService directions and routing options](https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/routing-options)
- [OpenRouteService geocoder](https://giscience.github.io/openrouteservice/api-reference/endpoints/geocoder/)
- [OpenRouteService public API restrictions](https://openrouteservice.org/restrictions/)
- [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/)
- [Vercel monorepo projects](https://vercel.com/docs/monorepos)
- [Vercel external rewrites](https://vercel.com/docs/routing/rewrites)
- [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python)
- [unDraw license](https://undraw.co/license)
- [Aceternity UI license](https://ui.aceternity.com/licence)
- [Magic UI source and MIT license](https://github.com/magicuidesign/magicui)
- [Lucide source and ISC license](https://github.com/lucide-icons/lucide)

## 17. Resolved decisions

- Product layout: Map-first operations desk.
- Visual direction: Roadbook Editorial.
- Fonts: Satoshi Bold and Erode Regular from the supplied Fontshare kit.
- Map and routing: OpenRouteService plus OpenStreetMap tiles.
- Daily logs: original RouteLog HTML/SVG design, not the supplied PNG.
- Frontend and backend hosting: two Vercel projects in one monorepo.
- Persistence: none in v1.
- Rule interpretation: aggregate cycle consumption with modeled 34-hour restarts.
- Design approval: complete; no open product-design decisions remain.
