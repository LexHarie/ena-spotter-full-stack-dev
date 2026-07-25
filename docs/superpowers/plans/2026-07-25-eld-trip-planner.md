# RouteLog HOS Trip Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and deploy the approved RouteLog React/Django application that turns four trip inputs into a truck route, HOS-aware itinerary, mapped stops, and original printable daily logs.

**Architecture:** A Vite React client calls a stateless Django REST API through same-origin `/api/*` paths. Django owns the OpenRouteService adapter and a pure integer-minute HOS scheduling engine; the client owns the Roadbook interface, React Leaflet map, semantic HTML/SVG daily logs, and print view.

**Tech Stack:** Python 3.12, Django 5.2 LTS, Django REST Framework, HTTPX, Pytest, Ruff, React 19, TypeScript, Vite, Tailwind CSS 4, shadcn-style source components, React Hook Form, Zod, React Leaflet, Lucide, Motion, Vitest, Testing Library, Playwright, GitHub Actions, and two Vercel projects.

## Global Constraints

- Keep the four required visible inputs exactly: current location, pickup location, drop-off location, and current cycle used hours.
- Restrict location candidates and routes to the United States.
- Use OpenRouteService `driving-hgv` for routing and OpenStreetMap tiles with visible attribution.
- Keep `ORS_API_KEY` on the Django server; the browser calls only `/api/*`.
- Model a solo property-carrying driver under 70 hours / 8 days, 11 driving hours, a 14-hour driving window, a 30-minute interruption after 8 cumulative driving hours, 10-hour daily rests, and 34-hour cycle restarts.
- Model pickup and drop-off as exactly 60 on-duty minutes each.
- Model fuel as 30 on-duty minutes before every additional 1,000 route miles.
- Treat current cycle used as aggregate on-duty usage; hours return only through a modeled 34-hour restart.
- Round the trip start and every generated transition to quarter-hour precision.
- Freeze the trip-start home-terminal UTC offset for the whole plan and warn when the IANA zone crosses a daylight-saving transition.
- Every daily log must cover exactly 1,440 minutes with no gaps or overlaps.
- Use the original RouteLog HTML/SVG sheet; do not render on `blank-paper-log.png`.
- Keep driver, carrier, vehicle, shipping-document, and signature lines writable rather than inventing values.
- Label generated logs as planning copies and state that RouteLog is not a certified ELD.
- Use the Roadbook palette: paper `#F4F0E7`, ink `#182231`, safety amber `#E59A18`, and muted green `#365C4C`.
- Self-host Satoshi Bold and Erode Regular from `FontshareKit-2607003495.zip`, retaining the Fontshare license.
- Do not add authentication, persistence, Django admin, background jobs, or a database.
- Tests must not call the live OpenRouteService API.
- Before Task 1, invoke `using-git-worktrees` and execute on an isolated feature
  branch/worktree.
- Use test-driven development for every behavior task and commit after every reviewer-sized task.
- Run `backend/.venv/bin/ruff format backend` after each Python edit, before
  the task's listed checks.
- Before frontend implementation, invoke `frontend-skill`; after React changes, invoke `react-doctor`.
- Before claiming any task complete, invoke `verification-before-completion` and run the task's fresh verification commands.

## Frontend skill direction

**Visual thesis:** A warm printed roadbook laid over live route intelligence: editorial paper and typography, an operational navy map line, and one amber signal for action or state.

**Content plan:** The first viewport is the working form and dominant map plane; successful results move through route summary, duty itinerary, turn instructions, original daily sheets, and the final Print / Save PDF action. Each section has one job and uses dividers or open layout before cards.

**Interaction thesis:** Use three restrained motions that improve orientation: blur-fade between the three planning stages, one entrance reveal when the generated workspace replaces the empty map, and one shared selection rail that moves between itinerary events while the corresponding map marker enlarges. Button hover lift remains a small affordance, not a fourth decorative system.

## Approved-spec coverage

| Approved design area | Owning tasks |
| --- | --- |
| Product, scope, and regulatory assumptions | Global constraints; Tasks 5–10 and 18 |
| Map-first Roadbook UX and visual system | Tasks 11, 13, 14, and 16 |
| Original daily-log model and print output | Tasks 8 and 15 |
| Stateless architecture and provider boundary | Tasks 1–4 and 9–12 |
| Integer-minute HOS scheduling and route positioning | Tasks 2 and 4–8 |
| API contracts, typed failures, and no fallback route | Tasks 9, 10, 12, and 16 |
| Accessibility, responsiveness, reduced motion, and printing | Tasks 11 and 13–17 |
| Unit, API, component, browser, and CI verification | Every behavior task; Task 17 |
| Vercel, GitHub, documentation, and Loom handoff | Task 18 |

## Planned file structure

```text
.github/workflows/ci.yml                    Test and build gates
.gitignore                                  Python, Node, Vercel, and local-secret exclusions
README.md                                   Setup, architecture, deployment, and demo
THIRD_PARTY_NOTICES.md                      Font and UI-source notices
backend/
  .env.example                              Backend environment contract
  .python-version                           Vercel Python selection
  manage.py                                 Django CLI and Vercel detection
  pyproject.toml                            Pytest and Ruff configuration
  requirements.txt                          Runtime dependencies
  requirements-dev.txt                      Test/lint dependencies
  routelog/
    settings.py                             Stateless Django settings
    urls.py                                 Root API routing
    wsgi.py                                 Vercel WSGI entrypoint
  trips/
    apps.py                                 Django app definition
    urls.py                                 Health, search, and plan routes
    views.py                                Thin DRF request handlers
    serializers.py                          Request validation and response contract
    errors.py                               Stable error envelope
    domain/
      types.py                              Immutable domain records and enums
      units.py                              Time/distance conversion
      scheduler.py                          Pure HOS event engine
      projector.py                          Midnight splitting and daily logs
    services/
      ors_client.py                         OpenRouteService implementation
      route_index.py                        Route-progress interpolation
      planner.py                            Provider + scheduler orchestration
      provider.py                           Runtime provider construction
  tests/
    fixtures/ors_route.json                 Reduced deterministic provider fixture
    conftest.py                             Shared test factories
    test_health.py                          Framework smoke test
    test_units.py                           Unit conversion tests
    test_ors_client.py                      Provider parsing and failure tests
    test_route_index.py                     Interpolation tests
    test_scheduler_basic.py                 Route/service scheduling tests
    test_scheduler_limits.py                Break, shift, and rest tests
    test_scheduler_cycle_fuel.py            Fuel and cycle tests
    test_projector.py                       Daily-log invariants
    test_location_api.py                    Search endpoint contract
    test_plan_api.py                        Full planning endpoint contract
frontend/
  .env.example                              Local API-base contract
  .nvmrc                                    Node 22 selection
  eslint.config.js                          TypeScript/React lint configuration
  index.html                                Vite entry document
  package.json                              Frontend scripts and dependencies
  playwright.config.ts                      Browser test configuration
  tsconfig.app.json                         Browser TypeScript settings
  tsconfig.json                             TypeScript references
  tsconfig.node.json                        Tooling TypeScript settings
  vercel.json                               API proxy and SPA fallback
  vite.config.ts                            React, Tailwind, test, and dev proxy setup
  public/
    fonts/Erode-Regular.woff2               Editorial webfont
    fonts/Satoshi-Bold.woff2                Operational webfont
    licenses/Fontshare-FFL.txt               Font license
  src/
    main.tsx                                React entrypoint
    App.tsx                                 Page state orchestration
    assets/route-planning.svg               unDraw empty-state art
    styles/globals.css                      Tokens, layout, motion, and print rules
    components/
      ui/button.tsx                         Source-owned shadcn-style button
      ui/alert.tsx                          Source-owned alert
      ui/accordion.tsx                      Source-owned accordion
      planner/TripForm.tsx                  Four-field form
      planner/LocationCombobox.tsx          Accessible search combobox
      planner/CycleMeter.tsx                70-hour capacity feedback
      planner/PlanningProgress.tsx           Three-stage progress treatment
      results/ResultsWorkspace.tsx          Results composition
      results/RouteMap.tsx                  Route and stop map
      results/TripSummary.tsx               Operational metrics
      results/Itinerary.tsx                 Duty-event timeline
      results/Directions.tsx                Collapsible route steps
      logs/DailyLogSheet.tsx                Original printable sheet
      logs/DutyGraph.tsx                    SVG duty trace
      logs/PrintToolbar.tsx                 Print / Save PDF action
      states/EmptyState.tsx                 unDraw opening state
      states/ErrorAlert.tsx                 Typed recoverable errors
    hooks/useLocationSearch.ts              Debounced cancellable search
    lib/
      api/client.ts                         Fetch wrapper
      api/types.ts                          API contract
      api/client.test.ts                    Client tests
      time.ts                               Start-time and timezone helpers
      utils.ts                              Class-name helper
  src/test/setup.ts                         DOM test setup
  src/**/*.test.tsx                         Component behavior tests
  e2e/fixtures/plan.json                    Deterministic browser fixture
  e2e/planning-flow.spec.ts                 Full user-flow test
docs/
  architecture.md                           Runtime and module boundaries
  assumptions.md                            HOS interpretations and limitations
  deployment.md                             Vercel setup and smoke test
  loom-script.md                            3–5 minute walkthrough outline
```

---

### Task 1: Bootstrap the stateless Django API

**Files:**
- Modify: `.gitignore`
- Create: `backend/.python-version`
- Create: `backend/.env.example`
- Create: `backend/requirements.txt`
- Create: `backend/requirements-dev.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/manage.py`
- Create: `backend/routelog/__init__.py`
- Create: `backend/routelog/settings.py`
- Create: `backend/routelog/urls.py`
- Create: `backend/routelog/wsgi.py`
- Create: `backend/trips/__init__.py`
- Create: `backend/trips/apps.py`
- Create: `backend/trips/urls.py`
- Create: `backend/trips/views.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Consumes: no application code.
- Produces: Django application `routelog.wsgi.application` and `GET /api/v1/health/ -> {"status": "ok"}`.

- [ ] **Step 1: Add the Python dependency and tool configuration**

Create `backend/.python-version`:

```text
3.12
```

Create `backend/requirements.txt`:

```text
Django==5.2.16
djangorestframework==3.17.1
httpx==0.28.1
```

Create `backend/requirements-dev.txt`:

```text
-r requirements.txt
pytest==9.1.1
pytest-django==4.12.0
ruff==0.16.0
```

Create `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "routelog.settings"
pythonpath = ["."]
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
```

Create `backend/.env.example`:

```dotenv
DJANGO_SECRET_KEY=
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
ORS_API_KEY=
```

Append these entries to `.gitignore`:

```gitignore
.DS_Store
.env
.env.*
!.env.example
.venv/
__pycache__/
.pytest_cache/
.ruff_cache/
*.py[cod]
node_modules/
dist/
coverage/
.vercel/
playwright-report/
test-results/
```

- [ ] **Step 2: Write the failing health-endpoint test**

Create `backend/tests/test_health.py`:

```python
from django.test import Client


def test_health_endpoint() -> None:
    response = Client().get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 3: Install dependencies and verify the test fails**

Run:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-dev.txt
backend/.venv/bin/pytest backend/tests/test_health.py -v
```

Expected: FAIL while importing `routelog.settings` because the Django project does not exist yet.

- [ ] **Step 4: Add the minimal Django project and health view**

Create `backend/manage.py`:

```python
#!/usr/bin/env python
import os
import sys


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "routelog.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

Create empty `backend/routelog/__init__.py` and `backend/trips/__init__.py`.

Create `backend/routelog/settings.py`:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "local-development-only")
DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,.vercel.app",
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = ["rest_framework", "trips"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "routelog.urls"
TEMPLATES = []
WSGI_APPLICATION = "routelog.wsgi.application"
DATABASES: dict[str, object] = {}
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
}
```

Create `backend/routelog/urls.py`:

```python
from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("trips.urls")),
]
```

Create `backend/routelog/wsgi.py`:

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "routelog.settings")
application = get_wsgi_application()
```

Create `backend/trips/apps.py`:

```python
from django.apps import AppConfig


class TripsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "trips"
```

Create `backend/trips/views.py`:

```python
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request):
        return Response({"status": "ok"})
```

Create `backend/trips/urls.py`:

```python
from django.urls import path

from trips.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
]
```

- [ ] **Step 5: Run the backend foundation checks**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_health.py -v
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/ruff check backend
```

Expected: one passing test, Django reports no issues, and Ruff reports no errors.

- [ ] **Step 6: Commit the backend foundation**

```bash
git add .gitignore backend
git commit -m "chore: bootstrap stateless Django API"
```

---

### Task 2: Define domain types and exact units

**Files:**
- Create: `backend/trips/domain/__init__.py`
- Create: `backend/trips/domain/types.py`
- Create: `backend/trips/domain/units.py`
- Create: `backend/tests/test_units.py`

**Interfaces:**
- Consumes: Python standard-library `dataclasses`, `datetime`, `decimal`, and `enum`.
- Produces: `Coordinate`, `Location`, `RouteStep`, `RouteLeg`, `NormalizedRoute`, `TripRequest`, `DutyEvent`, `DailyLogSegment`, `DailyLog`, `DutyStatus`, `EventKind`, `hours_to_minutes()`, `ceil_minutes_to_quarter()`, `ceil_datetime_to_quarter()`, and `meters_to_miles()`.

- [ ] **Step 1: Write failing conversion tests**

Create empty `backend/trips/domain/__init__.py`.

Create `backend/tests/test_units.py`:

```python
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from trips.domain.units import (
    ceil_datetime_to_quarter,
    ceil_minutes_to_quarter,
    hours_to_minutes,
    meters_to_miles,
)


def test_hours_to_minutes_accepts_quarter_hours() -> None:
    assert hours_to_minutes(Decimal("24.25")) == 1455


def test_hours_to_minutes_rejects_non_quarter_hours() -> None:
    with pytest.raises(ValueError, match="quarter-hour"):
        hours_to_minutes(Decimal("1.10"))


def test_ceil_minutes_to_quarter() -> None:
    assert ceil_minutes_to_quarter(61) == 75
    assert ceil_minutes_to_quarter(75) == 75


def test_ceil_datetime_to_quarter_preserves_offset() -> None:
    value = datetime(2026, 7, 25, 8, 7, tzinfo=timezone(timedelta(hours=-5)))

    assert ceil_datetime_to_quarter(value) == datetime(
        2026,
        7,
        25,
        8,
        15,
        tzinfo=timezone(timedelta(hours=-5)),
    )


def test_meters_to_miles_rounds_only_for_display() -> None:
    assert meters_to_miles(160934) == Decimal("100.00")
```

- [ ] **Step 2: Run the unit tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_units.py -v
```

Expected: FAIL because `trips.domain.units` does not exist.

- [ ] **Step 3: Implement exact conversion helpers**

Create `backend/trips/domain/units.py`:

```python
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

MINUTES_PER_QUARTER = 15
METERS_PER_MILE = Decimal("1609.344")


def hours_to_minutes(hours: Decimal) -> int:
    minutes = hours * Decimal(60)
    if minutes != minutes.to_integral_value() or int(minutes) % MINUTES_PER_QUARTER:
        raise ValueError("Hours must use quarter-hour increments.")
    return int(minutes)


def ceil_minutes_to_quarter(minutes: int) -> int:
    if minutes < 0:
        raise ValueError("Minutes cannot be negative.")
    return ((minutes + MINUTES_PER_QUARTER - 1) // MINUTES_PER_QUARTER) * MINUTES_PER_QUARTER


def ceil_datetime_to_quarter(value: datetime) -> datetime:
    if value.utcoffset() is None:
        raise ValueError("Start time must be timezone-aware.")
    floor = value.replace(second=0, microsecond=0)
    remainder = floor.minute % MINUTES_PER_QUARTER
    extra = 0 if remainder == 0 and value == floor else MINUTES_PER_QUARTER - remainder
    return floor + timedelta(minutes=extra)


def meters_to_miles(meters: int) -> Decimal:
    return (Decimal(meters) / METERS_PER_MILE).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
```

- [ ] **Step 4: Add immutable domain records**

Create `backend/trips/domain/types.py`:

```python
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class DutyStatus(StrEnum):
    OFF_DUTY = "off_duty"
    SLEEPER_BERTH = "sleeper_berth"
    DRIVING = "driving"
    ON_DUTY = "on_duty_not_driving"


class EventKind(StrEnum):
    PRE_TRIP_OFF_DUTY = "pre_trip_off_duty"
    DRIVING = "driving"
    PICKUP = "pickup"
    DROPOFF = "dropoff"
    FUEL = "fuel"
    BREAK = "break"
    DAILY_REST = "daily_rest"
    CYCLE_RESTART = "cycle_restart"
    POST_TRIP_OFF_DUTY = "post_trip_off_duty"


@dataclass(frozen=True)
class Coordinate:
    longitude: float
    latitude: float


@dataclass(frozen=True)
class Location:
    id: str
    label: str
    coordinate: Coordinate
    country_code: str = "US"


@dataclass(frozen=True)
class RouteStep:
    instruction: str
    road_name: str
    distance_m: int
    duration_minutes: int
    geometry_start_index: int
    geometry_end_index: int


@dataclass(frozen=True)
class RouteLeg:
    start: Location
    end: Location
    distance_m: int
    duration_minutes: int
    steps: tuple[RouteStep, ...]


@dataclass(frozen=True)
class NormalizedRoute:
    geometry: tuple[Coordinate, ...]
    legs: tuple[RouteLeg, ...]
    distance_m: int
    driving_minutes: int


@dataclass(frozen=True)
class TripRequest:
    current_location: Location
    pickup_location: Location
    dropoff_location: Location
    cycle_used_minutes: int
    starts_at: datetime
    home_terminal_timezone: str
    fixed_utc_offset_minutes: int


@dataclass(frozen=True)
class DutyEvent:
    id: str
    kind: EventKind
    duty_status: DutyStatus
    start_at: datetime
    end_at: datetime
    route_start_m: int
    route_end_m: int
    location: Location
    remark: str
    cycle_used_before_minutes: int
    cycle_used_after_minutes: int

    @property
    def duration_minutes(self) -> int:
        return int((self.end_at - self.start_at).total_seconds() // 60)


@dataclass(frozen=True)
class DailyLogSegment:
    event_id: str
    kind: EventKind
    duty_status: DutyStatus
    start_minute: int
    end_minute: int
    location: Location
    remark: str


@dataclass(frozen=True)
class DailyLog:
    date: date
    trip_day: int
    start_location: Location
    end_location: Location
    distance_m: int
    segments: tuple[DailyLogSegment, ...]
    off_duty_minutes: int
    sleeper_berth_minutes: int
    driving_minutes: int
    on_duty_minutes: int
    cycle_used_start_minutes: int
    cycle_added_minutes: int
    cycle_remaining_end_minutes: int
```

- [ ] **Step 5: Run domain checks**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_units.py -v
backend/.venv/bin/ruff check backend
```

Expected: five passing tests and no Ruff errors.

- [ ] **Step 6: Commit the domain foundation**

```bash
git add backend/trips/domain backend/tests/test_units.py
git commit -m "feat: define RouteLog domain types and units"
```

---

### Task 3: Implement the OpenRouteService adapter

**Files:**
- Create: `backend/trips/services/__init__.py`
- Create: `backend/trips/services/ors_client.py`
- Create: `backend/trips/services/provider.py`
- Create: `backend/tests/fixtures/ors_route.json`
- Create: `backend/tests/test_ors_client.py`

**Interfaces:**
- Consumes: `Coordinate`, `Location`, `NormalizedRoute`, `RouteLeg`, and `RouteStep` from `trips.domain.types`.
- Produces: `RoutingProvider` protocol, `OpenRouteServiceClient.search_locations(query)`, `OpenRouteServiceClient.build_route(waypoints)`, `OpenRouteServiceClient.reverse_geocode(coordinate)`, `ProviderError`, and `get_routing_provider()`.

- [ ] **Step 1: Save a reduced ORS response fixture**

Create `backend/tests/fixtures/ors_route.json`:

```json
{
  "features": [
    {
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [-87.6298, 41.8781],
          [-89.0000, 40.5000],
          [-90.1994, 38.6270],
          [-101.0000, 36.0000],
          [-112.0740, 33.4484]
        ]
      },
      "properties": {
        "summary": {"distance": 2816350.0, "duration": 91800.0},
        "segments": [
          {
            "distance": 478100.0,
            "duration": 16200.0,
            "steps": [
              {
                "distance": 478100.0,
                "duration": 16200.0,
                "instruction": "Continue southwest to St. Louis",
                "name": "I-55 S",
                "way_points": [0, 2]
              }
            ]
          },
          {
            "distance": 2338250.0,
            "duration": 75600.0,
            "steps": [
              {
                "distance": 2338250.0,
                "duration": 75600.0,
                "instruction": "Continue west to Phoenix",
                "name": "I-40 W",
                "way_points": [2, 4]
              }
            ]
          }
        ]
      }
    }
  ]
}
```

- [ ] **Step 2: Write failing provider tests**

Create `backend/tests/test_ors_client.py`:

```python
import json
from pathlib import Path

import httpx
import pytest

from trips.domain.types import Coordinate, Location
from trips.services.ors_client import OpenRouteServiceClient, ProviderError

FIXTURE = Path(__file__).parent / "fixtures" / "ors_route.json"


def test_build_route_normalizes_geometry_legs_and_quarter_hours() -> None:
    payload = json.loads(FIXTURE.read_text())

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "test-key"
        return httpx.Response(200, json=payload)

    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    )
    locations = (
        Location("current", "Chicago, IL", Coordinate(-87.6298, 41.8781)),
        Location("pickup", "St. Louis, MO", Coordinate(-90.1994, 38.6270)),
        Location("dropoff", "Phoenix, AZ", Coordinate(-112.0740, 33.4484)),
    )

    route = client.build_route(locations)

    assert route.distance_m == 2816350
    assert route.driving_minutes == 1530
    assert len(route.geometry) == 5
    assert [leg.duration_minutes for leg in route.legs] == [270, 1260]
    assert all(
        sum(step.distance_m for step in leg.steps) == leg.distance_m
        for leg in route.legs
    )
    assert route.legs[1].steps[0].road_name == "I-40 W"


def test_search_locations_restricts_to_us_and_caps_results() -> None:
    payload = {
        "features": [
            {
                "properties": {
                    "id": f"id-{index}",
                    "label": f"Result {index}, USA",
                    "country_a": "USA",
                },
                "geometry": {"coordinates": [-87.6 + index / 100, 41.8]},
            }
            for index in range(7)
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["boundary.country"] == "US"
        return httpx.Response(200, json=payload)

    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    assert len(client.search_locations("Chicago")) == 5


def test_provider_raises_typed_error_after_transient_failure() -> None:
    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(503, json={"error": "unavailable"})
        ),
    )

    with pytest.raises(ProviderError) as error:
        client.search_locations("Chicago")

    assert error.value.code == "PROVIDER_UNAVAILABLE"
    assert error.value.retryable is True


def test_provider_retries_a_timeout_then_raises_typed_error() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectTimeout("timed out", request=request)

    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ProviderError) as error:
        client.search_locations("Chicago")

    assert attempts == 2
    assert error.value.code == "PROVIDER_UNAVAILABLE"


def test_malformed_route_response_raises_typed_provider_error() -> None:
    client = OpenRouteServiceClient(
        "test-key",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={"features": [{"geometry": {}}]},
            )
        ),
    )
    locations = (
        Location("current", "Chicago, IL", Coordinate(-87.6298, 41.8781)),
        Location("pickup", "St. Louis, MO", Coordinate(-90.1994, 38.6270)),
        Location("dropoff", "Phoenix, AZ", Coordinate(-112.0740, 33.4484)),
    )

    with pytest.raises(ProviderError) as error:
        client.build_route(locations)

    assert error.value.code == "PROVIDER_UNAVAILABLE"
    assert error.value.retryable is True
```

- [ ] **Step 3: Run provider tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_ors_client.py -v
```

Expected: FAIL because `trips.services.ors_client` does not exist.

- [ ] **Step 4: Implement provider parsing and bounded retries**

Create empty `backend/trips/services/__init__.py`.

Create `backend/trips/services/ors_client.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from typing import Protocol

import httpx

from trips.domain.types import (
    Coordinate,
    Location,
    NormalizedRoute,
    RouteLeg,
    RouteStep,
)
from trips.domain.units import ceil_minutes_to_quarter

ORS_BASE_URL = "https://api.openrouteservice.org"


@dataclass(frozen=True)
class ProviderError(Exception):
    code: str
    message: str
    retryable: bool
    status_code: int = 503

    def __str__(self) -> str:
        return self.message


class RoutingProvider(Protocol):
    def search_locations(self, query: str) -> tuple[Location, ...]: ...

    def build_route(
        self,
        waypoints: tuple[Location, Location, Location],
    ) -> NormalizedRoute: ...

    def reverse_geocode(self, coordinate: Coordinate) -> Location: ...


def _coordinate(raw: object) -> Coordinate:
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError("Invalid coordinate.")
    longitude = float(raw[0])
    latitude = float(raw[1])
    if (
        not isfinite(longitude)
        or not isfinite(latitude)
        or not -180 <= longitude <= 180
        or not -90 <= latitude <= 90
    ):
        raise ValueError("Invalid coordinate.")
    return Coordinate(longitude, latitude)


def _nonnegative_number(value: object) -> float:
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ValueError("Expected a finite non-negative number.")
    return number


def _parse_route_payload(
    payload: dict,
    waypoints: tuple[Location, Location, Location],
) -> NormalizedRoute:
    features = payload.get("features", [])
    if features == []:
        raise ProviderError(
            "ROUTE_NOT_FOUND",
            "No truck route was found for the selected locations.",
            False,
            422,
        )
    try:
        feature = features[0]
        geometry = tuple(
            _coordinate(raw)
            for raw in feature["geometry"]["coordinates"]
        )
        segments = feature["properties"]["segments"]
        if len(geometry) < 2 or len(segments) != 2:
            raise ValueError("Unexpected route shape.")
        legs: list[RouteLeg] = []
        for index, segment in enumerate(segments):
            segment_distance_m = round(
                _nonnegative_number(segment["distance"])
            )
            raw_steps = segment["steps"]
            if not raw_steps and segment_distance_m:
                raise ValueError("A non-empty leg requires route steps.")
            remaining_distance_m = segment_distance_m
            normalized_steps: list[RouteStep] = []
            for step_index, step in enumerate(raw_steps):
                is_last = step_index == len(raw_steps) - 1
                raw_step_distance_m = round(
                    _nonnegative_number(step["distance"])
                )
                step_distance_m = (
                    remaining_distance_m
                    if is_last
                    else min(raw_step_distance_m, remaining_distance_m)
                )
                duration_minutes = ceil_minutes_to_quarter(
                    ceil(_nonnegative_number(step["duration"]) / 60)
                )
                if step_distance_m and duration_minutes == 0:
                    raise ValueError("A moving step requires duration.")
                geometry_start_index, geometry_end_index = step["way_points"]
                if not (
                    0 <= geometry_start_index <= geometry_end_index
                    < len(geometry)
                ):
                    raise ValueError("Invalid step geometry indexes.")
                normalized_steps.append(
                    RouteStep(
                        instruction=step["instruction"],
                        road_name=step.get("name", ""),
                        distance_m=step_distance_m,
                        duration_minutes=duration_minutes,
                        geometry_start_index=geometry_start_index,
                        geometry_end_index=geometry_end_index,
                    )
                )
                remaining_distance_m -= step_distance_m
            steps = tuple(normalized_steps)
            legs.append(
                RouteLeg(
                    start=waypoints[index],
                    end=waypoints[index + 1],
                    distance_m=segment_distance_m,
                    duration_minutes=sum(
                        step.duration_minutes for step in steps
                    ),
                    steps=steps,
                )
            )
    except (IndexError, KeyError, TypeError, ValueError) as exc:
        raise ProviderError(
            "PROVIDER_UNAVAILABLE",
            "The routing service returned an invalid response.",
            True,
        ) from exc
    return NormalizedRoute(
        geometry=geometry,
        legs=tuple(legs),
        distance_m=sum(leg.distance_m for leg in legs),
        driving_minutes=sum(leg.duration_minutes for leg in legs),
    )


class OpenRouteServiceClient:
    def __init__(
        self,
        api_key: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=ORS_BASE_URL,
            headers={"Authorization": api_key},
            timeout=httpx.Timeout(12.0, connect=5.0),
            transport=transport,
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        for attempt in range(2):
            try:
                response = self._client.request(method, path, **kwargs)
            except httpx.RequestError as exc:
                if attempt == 0:
                    continue
                raise ProviderError(
                    "PROVIDER_UNAVAILABLE",
                    "The routing service could not be reached.",
                    True,
                ) from exc

            if response.status_code == 429:
                raise ProviderError(
                    "PROVIDER_RATE_LIMITED",
                    "The routing service rate limit was reached.",
                    True,
                    429,
                )
            if response.status_code in {502, 503, 504} and attempt == 0:
                continue
            if response.status_code >= 500:
                raise ProviderError(
                    "PROVIDER_UNAVAILABLE",
                    "The routing service is temporarily unavailable.",
                    True,
                )
            if response.status_code >= 400:
                raise ProviderError(
                    "ROUTE_NOT_FOUND",
                    "No truck route was found for the selected locations.",
                    False,
                    422,
                )
            try:
                payload = response.json()
                if not isinstance(payload, dict):
                    raise TypeError("Provider JSON root must be an object.")
            except (TypeError, ValueError) as exc:
                raise ProviderError(
                    "PROVIDER_UNAVAILABLE",
                    "The routing service returned an invalid response.",
                    True,
                ) from exc
            return payload

        raise ProviderError(
            "PROVIDER_UNAVAILABLE",
            "The routing service is temporarily unavailable.",
            True,
        )

    def search_locations(self, query: str) -> tuple[Location, ...]:
        payload = self._request(
            "GET",
            "/geocode/search",
            params={
                "text": query,
                "boundary.country": "US",
                "size": 5,
            },
        )
        locations: list[Location] = []
        for feature in payload.get("features", [])[:5]:
            properties = feature["properties"]
            longitude, latitude = feature["geometry"]["coordinates"]
            locations.append(
                Location(
                    id=str(properties.get("id", properties["label"])),
                    label=properties["label"],
                    coordinate=Coordinate(float(longitude), float(latitude)),
                    country_code="US",
                )
            )
        return tuple(locations)

    def build_route(
        self,
        waypoints: tuple[Location, Location, Location],
    ) -> NormalizedRoute:
        payload = self._request(
            "POST",
            "/v2/directions/driving-hgv/geojson",
            json={
                "coordinates": [
                    [point.coordinate.longitude, point.coordinate.latitude]
                    for point in waypoints
                ],
                "instructions": True,
            },
        )
        return _parse_route_payload(payload, waypoints)

    def reverse_geocode(self, coordinate: Coordinate) -> Location:
        payload = self._request(
            "GET",
            "/geocode/reverse",
            params={
                "point.lon": coordinate.longitude,
                "point.lat": coordinate.latitude,
                "size": 1,
            },
        )
        features = payload.get("features", [])
        if not features:
            return Location(
                id=f"{coordinate.longitude:.5f},{coordinate.latitude:.5f}",
                label=f"{coordinate.latitude:.5f}, {coordinate.longitude:.5f}",
                coordinate=coordinate,
            )
        feature = features[0]
        properties = feature["properties"]
        return Location(
            id=str(properties.get("id", properties["label"])),
            label=properties["label"],
            coordinate=coordinate,
            country_code="US",
        )
```

Create `backend/trips/services/provider.py`:

```python
import os

from trips.services.ors_client import OpenRouteServiceClient, RoutingProvider


def get_routing_provider() -> RoutingProvider:
    api_key = os.environ.get("ORS_API_KEY", "")
    if not api_key:
        raise RuntimeError("ORS_API_KEY is required.")
    return OpenRouteServiceClient(api_key)
```

- [ ] **Step 5: Run provider tests and static checks**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_ors_client.py -v
backend/.venv/bin/ruff check backend
```

Expected: five passing tests and no Ruff errors.

- [ ] **Step 6: Commit the routing adapter**

```bash
git add backend/trips/services backend/tests/fixtures backend/tests/test_ors_client.py
git commit -m "feat: add OpenRouteService adapter"
```

---

### Task 4: Index and interpolate route progress

**Files:**
- Create: `backend/trips/services/route_index.py`
- Create: `backend/tests/test_route_index.py`

**Interfaces:**
- Consumes: `Coordinate` and `NormalizedRoute`.
- Produces: `RouteIndex(route).coordinate_at(progress_m: int) -> Coordinate`.

- [ ] **Step 1: Write failing interpolation tests**

Create `backend/tests/test_route_index.py`:

```python
import pytest

from trips.domain.types import Coordinate, NormalizedRoute
from trips.services.route_index import RouteIndex


def test_coordinate_at_scales_provider_distance_over_geometry() -> None:
    route = NormalizedRoute(
        geometry=(
            Coordinate(0.0, 0.0),
            Coordinate(0.0, 1.0),
            Coordinate(0.0, 2.0),
        ),
        legs=(),
        distance_m=200_000,
        driving_minutes=120,
    )

    coordinate = RouteIndex(route).coordinate_at(100_000)

    assert coordinate.longitude == pytest.approx(0.0)
    assert coordinate.latitude == pytest.approx(1.0, abs=0.01)


def test_coordinate_at_clamps_route_bounds() -> None:
    route = NormalizedRoute(
        geometry=(Coordinate(-1.0, 1.0), Coordinate(1.0, 2.0)),
        legs=(),
        distance_m=100,
        driving_minutes=15,
    )
    index = RouteIndex(route)

    assert index.coordinate_at(-1) == route.geometry[0]
    assert index.coordinate_at(101) == route.geometry[-1]
```

- [ ] **Step 2: Run interpolation tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_route_index.py -v
```

Expected: FAIL because `trips.services.route_index` does not exist.

- [ ] **Step 3: Implement geometry indexing**

Create `backend/trips/services/route_index.py`:

```python
from math import asin, cos, radians, sin, sqrt

from trips.domain.types import Coordinate, NormalizedRoute

EARTH_RADIUS_M = 6_371_000


def _distance_m(start: Coordinate, end: Coordinate) -> float:
    lat1 = radians(start.latitude)
    lat2 = radians(end.latitude)
    delta_lat = lat2 - lat1
    delta_lon = radians(end.longitude - start.longitude)
    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * asin(sqrt(haversine))


class RouteIndex:
    def __init__(self, route: NormalizedRoute) -> None:
        if len(route.geometry) < 2:
            raise ValueError("Route geometry requires at least two coordinates.")
        self._route = route
        cumulative = [0.0]
        for start, end in zip(
            route.geometry,
            route.geometry[1:],
            strict=False,
        ):
            cumulative.append(cumulative[-1] + _distance_m(start, end))
        self._cumulative = tuple(cumulative)
        self._geometry_distance = cumulative[-1]

    def coordinate_at(self, progress_m: int) -> Coordinate:
        if progress_m <= 0:
            return self._route.geometry[0]
        if progress_m >= self._route.distance_m:
            return self._route.geometry[-1]

        target = (
            progress_m / self._route.distance_m
        ) * self._geometry_distance
        for index in range(1, len(self._cumulative)):
            if self._cumulative[index] < target:
                continue
            start_distance = self._cumulative[index - 1]
            segment_distance = self._cumulative[index] - start_distance
            ratio = 0.0 if segment_distance == 0 else (
                target - start_distance
            ) / segment_distance
            start = self._route.geometry[index - 1]
            end = self._route.geometry[index]
            return Coordinate(
                longitude=start.longitude
                + (end.longitude - start.longitude) * ratio,
                latitude=start.latitude
                + (end.latitude - start.latitude) * ratio,
            )
        return self._route.geometry[-1]
```

- [ ] **Step 4: Run interpolation and static checks**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_route_index.py -v
backend/.venv/bin/ruff check backend
```

Expected: two passing tests and no Ruff errors.

- [ ] **Step 5: Commit route indexing**

```bash
git add backend/trips/services/route_index.py backend/tests/test_route_index.py
git commit -m "feat: interpolate stops along route geometry"
```

---

### Task 5: Schedule short routes and service events

**Files:**
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_scheduler_basic.py`
- Create: `backend/trips/domain/scheduler.py`

**Interfaces:**
- Consumes: `TripRequest`, `NormalizedRoute`, `RouteLeg`, and the duty enums.
- Produces: `build_schedule(request: TripRequest, route: NormalizedRoute) -> tuple[DutyEvent, ...]`.

- [ ] **Step 1: Add deterministic route factories**

Create `backend/tests/conftest.py`:

```python
from datetime import datetime, timedelta, timezone

import pytest

from trips.domain.types import (
    Coordinate,
    Location,
    NormalizedRoute,
    RouteLeg,
    RouteStep,
    TripRequest,
)


@pytest.fixture
def locations() -> tuple[Location, Location, Location]:
    return (
        Location("current", "Chicago, IL", Coordinate(-87.6298, 41.8781)),
        Location("pickup", "St. Louis, MO", Coordinate(-90.1994, 38.6270)),
        Location("dropoff", "Phoenix, AZ", Coordinate(-112.0740, 33.4484)),
    )


@pytest.fixture
def trip_request(locations) -> TripRequest:
    return TripRequest(
        current_location=locations[0],
        pickup_location=locations[1],
        dropoff_location=locations[2],
        cycle_used_minutes=24 * 60,
        starts_at=datetime(
            2026,
            7,
            25,
            8,
            15,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
        home_terminal_timezone="America/Chicago",
        fixed_utc_offset_minutes=-300,
    )


def make_route(
    locations: tuple[Location, Location, Location],
    *,
    first_minutes: int,
    second_minutes: int,
    first_distance_m: int = 300_000,
    second_distance_m: int = 500_000,
) -> NormalizedRoute:
    first_step = RouteStep(
        "Drive to pickup",
        "I-55 S",
        first_distance_m,
        first_minutes,
        0,
        1,
    )
    second_step = RouteStep(
        "Drive to drop-off",
        "I-40 W",
        second_distance_m,
        second_minutes,
        1,
        2,
    )
    legs = (
        RouteLeg(
            locations[0],
            locations[1],
            first_distance_m,
            first_minutes,
            (first_step,),
        ),
        RouteLeg(
            locations[1],
            locations[2],
            second_distance_m,
            second_minutes,
            (second_step,),
        ),
    )
    return NormalizedRoute(
        geometry=tuple(location.coordinate for location in locations),
        legs=legs,
        distance_m=first_distance_m + second_distance_m,
        driving_minutes=first_minutes + second_minutes,
    )
```

- [ ] **Step 2: Write the failing basic-schedule test**

Create `backend/tests/test_scheduler_basic.py`:

```python
from datetime import timedelta

from conftest import make_route
from trips.domain.scheduler import build_schedule
from trips.domain.types import DutyStatus, EventKind


def test_short_route_contains_driving_pickup_and_dropoff(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=120,
        second_minutes=180,
    )

    events = build_schedule(trip_request, route)

    assert [event.kind for event in events] == [
        EventKind.DRIVING,
        EventKind.PICKUP,
        EventKind.DRIVING,
        EventKind.DROPOFF,
    ]
    assert [event.duty_status for event in events] == [
        DutyStatus.DRIVING,
        DutyStatus.ON_DUTY,
        DutyStatus.DRIVING,
        DutyStatus.ON_DUTY,
    ]
    assert [event.duration_minutes for event in events] == [120, 60, 180, 60]
    assert events[-1].end_at == trip_request.starts_at + timedelta(hours=7)
    assert events[-1].cycle_used_after_minutes == 31 * 60
    assert events[-1].route_end_m == route.distance_m
```

- [ ] **Step 3: Run the schedule test to verify it fails**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_scheduler_basic.py -v
```

Expected: FAIL because `trips.domain.scheduler` does not exist.

- [ ] **Step 4: Implement the short-route scheduler**

Create `backend/trips/domain/scheduler.py`:

```python
from datetime import timedelta

from trips.domain.types import (
    DutyEvent,
    DutyStatus,
    EventKind,
    Location,
    NormalizedRoute,
    RouteLeg,
    TripRequest,
)

PICKUP_MINUTES = 60
DROPOFF_MINUTES = 60


class Scheduler:
    def __init__(self, request: TripRequest, route: NormalizedRoute) -> None:
        self.request = request
        self.route = route
        self.now = request.starts_at
        self.route_progress_m = 0
        self.cycle_used_minutes = request.cycle_used_minutes
        self.events: list[DutyEvent] = []

    def _append(
        self,
        kind: EventKind,
        status: DutyStatus,
        duration_minutes: int,
        route_end_m: int,
        location: Location,
        remark: str,
    ) -> None:
        start = self.now
        end = start + timedelta(minutes=duration_minutes)
        cycle_before = self.cycle_used_minutes
        if status in {DutyStatus.DRIVING, DutyStatus.ON_DUTY}:
            self.cycle_used_minutes += duration_minutes
        self.events.append(
            DutyEvent(
                id=f"event-{len(self.events) + 1:03d}",
                kind=kind,
                duty_status=status,
                start_at=start,
                end_at=end,
                route_start_m=self.route_progress_m,
                route_end_m=route_end_m,
                location=location,
                remark=remark,
                cycle_used_before_minutes=cycle_before,
                cycle_used_after_minutes=self.cycle_used_minutes,
            )
        )
        self.now = end
        self.route_progress_m = route_end_m

    def _drive_leg(self, leg: RouteLeg) -> None:
        self._append(
            EventKind.DRIVING,
            DutyStatus.DRIVING,
            leg.duration_minutes,
            self.route_progress_m + leg.distance_m,
            leg.start,
            f"Drive toward {leg.end.label}",
        )

    def _service(
        self,
        kind: EventKind,
        location: Location,
        duration_minutes: int,
        remark: str,
    ) -> None:
        self._append(
            kind,
            DutyStatus.ON_DUTY,
            duration_minutes,
            self.route_progress_m,
            location,
            remark,
        )

    def build(self) -> tuple[DutyEvent, ...]:
        first_leg, second_leg = self.route.legs
        self._drive_leg(first_leg)
        self._service(
            EventKind.PICKUP,
            self.request.pickup_location,
            PICKUP_MINUTES,
            "Pickup",
        )
        self._drive_leg(second_leg)
        self._service(
            EventKind.DROPOFF,
            self.request.dropoff_location,
            DROPOFF_MINUTES,
            "Drop-off",
        )
        return tuple(self.events)


def build_schedule(
    request: TripRequest,
    route: NormalizedRoute,
) -> tuple[DutyEvent, ...]:
    if len(route.legs) != 2:
        raise ValueError("A trip route must contain current-to-pickup and pickup-to-drop-off legs.")
    if (
        sum(leg.distance_m for leg in route.legs) != route.distance_m
        or sum(leg.duration_minutes for leg in route.legs)
        != route.driving_minutes
        or any(
            sum(step.distance_m for step in leg.steps) != leg.distance_m
            or sum(step.duration_minutes for step in leg.steps)
            != leg.duration_minutes
            for leg in route.legs
        )
    ):
        raise ValueError("Route leg and step totals must match the route.")
    return Scheduler(request, route).build()
```

- [ ] **Step 5: Run scheduler and static checks**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_scheduler_basic.py -v
backend/.venv/bin/ruff check backend
```

Expected: one passing scheduler test and no Ruff errors.

- [ ] **Step 6: Commit basic scheduling**

```bash
git add backend/trips/domain/scheduler.py backend/tests/conftest.py backend/tests/test_scheduler_basic.py
git commit -m "feat: schedule route driving and service events"
```

---

### Task 6: Enforce driving, break, and shift limits

**Files:**
- Modify: `backend/trips/domain/scheduler.py`
- Create: `backend/tests/test_scheduler_limits.py`

**Interfaces:**
- Consumes: `build_schedule()` from Task 5.
- Produces: automatic `break` events at the eight-hour boundary and `daily_rest` events before driving past the 11-hour or 14-hour limits.

- [ ] **Step 1: Write failing break and daily-rest tests**

Create `backend/tests/test_scheduler_limits.py`:

```python
from dataclasses import replace

from conftest import make_route
from trips.domain.scheduler import build_schedule
from trips.domain.types import EventKind, RouteStep


def test_break_is_inserted_after_eight_cumulative_driving_hours(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=540,
        second_minutes=60,
    )

    events = build_schedule(trip_request, route)
    kinds = [event.kind for event in events]
    break_event = events[kinds.index(EventKind.BREAK)]

    assert break_event.duration_minutes == 30
    assert sum(
        event.duration_minutes
        for event in events[: kinds.index(EventKind.BREAK)]
        if event.kind == EventKind.DRIVING
    ) == 480


def test_exactly_eight_hours_before_pickup_needs_no_extra_break(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=480,
        second_minutes=0,
        second_distance_m=0,
    )

    events = build_schedule(trip_request, route)

    assert EventKind.BREAK not in [event.kind for event in events]


def test_pickup_service_satisfies_the_non_driving_break(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=450,
        second_minutes=450,
    )

    events = build_schedule(trip_request, route)

    assert EventKind.BREAK not in [event.kind for event in events]


def test_daily_rest_is_inserted_before_twelfth_driving_hour(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=720,
        second_minutes=60,
    )

    events = build_schedule(trip_request, route)
    kinds = [event.kind for event in events]
    rest_event = events[kinds.index(EventKind.DAILY_REST)]

    assert rest_event.duration_minutes == 600
    driving_before_rest = sum(
        event.duration_minutes
        for event in events[: kinds.index(EventKind.DAILY_REST)]
        if event.kind == EventKind.DRIVING
    )
    assert driving_before_rest == 660


def test_exactly_eleven_driving_hours_needs_no_daily_rest(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=600,
        second_minutes=60,
    )

    events = build_schedule(trip_request, route)

    assert EventKind.DAILY_REST not in [event.kind for event in events]
    assert sum(
        event.duration_minutes
        for event in events
        if event.kind == EventKind.DRIVING
    ) == 660


def test_all_transitions_remain_on_quarter_hours(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=720,
        second_minutes=180,
    )

    events = build_schedule(trip_request, route)

    assert all(event.start_at.minute % 15 == 0 for event in events)
    assert all(event.end_at.minute % 15 == 0 for event in events)


def test_driving_events_stop_at_provider_route_step_boundaries(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=120,
        second_minutes=60,
    )
    first_leg = route.legs[0]
    split_first_leg = replace(
        first_leg,
        steps=(
            RouteStep(
                "Continue on I-55",
                "I-55 S",
                150_000,
                60,
                0,
                1,
            ),
            RouteStep(
                "Take the St. Louis exit",
                "I-55 S",
                150_000,
                60,
                0,
                1,
            ),
        ),
    )
    route = replace(
        route,
        legs=(split_first_leg, route.legs[1]),
    )

    events = build_schedule(trip_request, route)
    pickup_index = next(
        index for index, event in enumerate(events) if event.kind == EventKind.PICKUP
    )

    assert [
        event.duration_minutes
        for event in events[:pickup_index]
        if event.kind == EventKind.DRIVING
    ] == [60, 60]
```

- [ ] **Step 2: Run the limit tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_scheduler_limits.py -v
```

Expected: FAIL because the scheduler currently emits no break or daily-rest events.

- [ ] **Step 3: Add shift clocks and chunked driving**

In `backend/trips/domain/scheduler.py`, add these constants:

```python
BREAK_AFTER_DRIVING_MINUTES = 8 * 60
MAX_DRIVING_MINUTES = 11 * 60
MAX_SHIFT_MINUTES = 14 * 60
BREAK_MINUTES = 30
DAILY_REST_MINUTES = 10 * 60
```

Add this state in `Scheduler.__init__`:

```python
self.shift_elapsed_minutes = 0
self.shift_driving_minutes = 0
self.driving_since_break_minutes = 0
```

Replace `_drive_leg` with:

```python
def _drive_leg(self, leg: RouteLeg) -> None:
    for step in leg.steps:
        remaining_minutes = step.duration_minutes
        remaining_distance_m = step.distance_m
        while remaining_minutes:
            if (
                self.shift_driving_minutes >= MAX_DRIVING_MINUTES
                or self.shift_elapsed_minutes >= MAX_SHIFT_MINUTES
            ):
                self._take_daily_rest()
            if (
                self.driving_since_break_minutes
                >= BREAK_AFTER_DRIVING_MINUTES
            ):
                self._take_break()

            capacity = min(
                remaining_minutes,
                BREAK_AFTER_DRIVING_MINUTES
                - self.driving_since_break_minutes,
                MAX_DRIVING_MINUTES - self.shift_driving_minutes,
                MAX_SHIFT_MINUTES - self.shift_elapsed_minutes,
            )
            if capacity <= 0:
                continue
            chunk_distance_m = (
                remaining_distance_m
                if capacity == remaining_minutes
                else (remaining_distance_m * capacity) // remaining_minutes
            )
            self._append(
                EventKind.DRIVING,
                DutyStatus.DRIVING,
                capacity,
                self.route_progress_m + chunk_distance_m,
                leg.start,
                step.instruction or f"Drive toward {leg.end.label}",
            )
            self.shift_elapsed_minutes += capacity
            self.shift_driving_minutes += capacity
            self.driving_since_break_minutes += capacity
            remaining_minutes -= capacity
            remaining_distance_m -= chunk_distance_m
```

Add these methods:

```python
def _take_break(self) -> None:
    self._append(
        EventKind.BREAK,
        DutyStatus.OFF_DUTY,
        BREAK_MINUTES,
        self.route_progress_m,
        self.events[-1].location,
        "30-minute break",
    )
    self.shift_elapsed_minutes += BREAK_MINUTES
    self.driving_since_break_minutes = 0

def _take_daily_rest(self) -> None:
    self._append(
        EventKind.DAILY_REST,
        DutyStatus.SLEEPER_BERTH,
        DAILY_REST_MINUTES,
        self.route_progress_m,
        self.events[-1].location,
        "10-hour sleeper-berth rest",
    )
    self.shift_elapsed_minutes = 0
    self.shift_driving_minutes = 0
    self.driving_since_break_minutes = 0
```

At the end of `_service`, add:

```python
self.shift_elapsed_minutes += duration_minutes
if duration_minutes >= BREAK_MINUTES:
    self.driving_since_break_minutes = 0
```

This makes any pickup or drop-off lasting at least 30 minutes a qualifying
non-driving break without resetting the 11-hour or 14-hour shift clocks.

- [ ] **Step 4: Run all scheduler tests**

Run:

```bash
backend/.venv/bin/pytest \
  backend/tests/test_scheduler_basic.py \
  backend/tests/test_scheduler_limits.py \
  -v
backend/.venv/bin/ruff check backend
```

Expected: eight passing scheduler tests and no Ruff errors.

- [ ] **Step 5: Commit HOS shift limits**

```bash
git add backend/trips/domain/scheduler.py backend/tests/test_scheduler_limits.py
git commit -m "feat: enforce HOS break and shift limits"
```

---

### Task 7: Add fuel stops and 70/8 cycle restarts

**Files:**
- Modify: `backend/trips/domain/scheduler.py`
- Create: `backend/tests/test_scheduler_cycle_fuel.py`
- Create: `backend/tests/test_scheduler_invariants.py`

**Interfaces:**
- Consumes: the chunked scheduler from Task 6.
- Produces: `fuel` events before 1,000-mile intervals and `cycle_restart` events before duty would exceed 4,200 cycle minutes.

- [ ] **Step 1: Write failing fuel and cycle tests**

Create `backend/tests/test_scheduler_cycle_fuel.py`:

```python
from dataclasses import replace

from conftest import make_route
from trips.domain.scheduler import build_schedule
from trips.domain.types import EventKind

MILE_M = 1609


def test_fuel_is_scheduled_before_each_thousand_miles(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=600,
        second_minutes=1200,
        first_distance_m=900 * MILE_M,
        second_distance_m=1300 * MILE_M,
    )

    events = build_schedule(trip_request, route)
    fuel_events = [event for event in events if event.kind == EventKind.FUEL]

    assert len(fuel_events) == 2
    assert all(event.duration_minutes == 30 for event in fuel_events)
    assert fuel_events[0].route_start_m <= 1000 * MILE_M
    assert fuel_events[1].route_start_m <= 2000 * MILE_M


def test_fuel_resets_the_eight_hour_break_counter(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=0,
        second_minutes=600,
        first_distance_m=0,
        second_distance_m=1340 * MILE_M,
    )

    events = build_schedule(trip_request, route)
    kinds = [event.kind for event in events]

    assert EventKind.FUEL in kinds
    assert EventKind.BREAK not in kinds


def test_exhausted_cycle_starts_with_a_thirty_four_hour_restart(
    trip_request,
    locations,
) -> None:
    request = replace(trip_request, cycle_used_minutes=70 * 60)
    route = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )

    events = build_schedule(request, route)

    assert events[0].kind == EventKind.CYCLE_RESTART
    assert events[0].duration_minutes == 34 * 60
    assert events[0].cycle_used_after_minutes == 0


def test_service_is_not_split_when_cycle_capacity_is_too_small(
    trip_request,
    locations,
) -> None:
    request = replace(trip_request, cycle_used_minutes=69 * 60 + 30)
    route = make_route(
        locations,
        first_minutes=30,
        second_minutes=30,
    )

    events = build_schedule(request, route)
    pickup_index = next(
        index for index, event in enumerate(events) if event.kind == EventKind.PICKUP
    )

    assert events[pickup_index - 1].kind == EventKind.CYCLE_RESTART
    assert events[pickup_index].duration_minutes == 60


def test_dropoff_waits_for_restart_when_only_thirty_cycle_minutes_remain(
    trip_request,
    locations,
) -> None:
    request = replace(trip_request, cycle_used_minutes=68 * 60)
    route = make_route(
        locations,
        first_minutes=15,
        second_minutes=15,
    )

    events = build_schedule(request, route)
    dropoff_index = next(
        index
        for index, event in enumerate(events)
        if event.kind == EventKind.DROPOFF
    )

    assert events[dropoff_index - 1].kind == EventKind.CYCLE_RESTART
    assert events[dropoff_index].duration_minutes == 60
```

- [ ] **Step 2: Run cycle and fuel tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_scheduler_cycle_fuel.py -v
```

Expected: FAIL because no fuel or cycle-restart logic exists.

- [ ] **Step 3: Add cycle and fuel constants and state**

In `backend/trips/domain/scheduler.py`, add:

```python
MAX_CYCLE_MINUTES = 70 * 60
CYCLE_RESTART_MINUTES = 34 * 60
FUEL_INTERVAL_M = round(1000 * 1609.344)
FUEL_MINUTES = 30
```

Add this state in `Scheduler.__init__`:

```python
self.next_fuel_at_m = FUEL_INTERVAL_M
```

Add:

```python
def _take_cycle_restart(self) -> None:
    location = (
        self.events[-1].location
        if self.events
        else self.request.current_location
    )
    self._append(
        EventKind.CYCLE_RESTART,
        DutyStatus.OFF_DUTY,
        CYCLE_RESTART_MINUTES,
        self.route_progress_m,
        location,
        "34-hour cycle restart",
    )
    self.cycle_used_minutes = 0
    last = self.events[-1]
    self.events[-1] = DutyEvent(
        id=last.id,
        kind=last.kind,
        duty_status=last.duty_status,
        start_at=last.start_at,
        end_at=last.end_at,
        route_start_m=last.route_start_m,
        route_end_m=last.route_end_m,
        location=last.location,
        remark=last.remark,
        cycle_used_before_minutes=last.cycle_used_before_minutes,
        cycle_used_after_minutes=0,
    )
    self.shift_elapsed_minutes = 0
    self.shift_driving_minutes = 0
    self.driving_since_break_minutes = 0

def _take_fuel_stop(self) -> None:
    location = self.events[-1].location
    self._service(
        EventKind.FUEL,
        location,
        FUEL_MINUTES,
        "Fuel stop",
    )
    self.next_fuel_at_m = self.route_progress_m + FUEL_INTERVAL_M

def _ensure_cycle_capacity(self, required_minutes: int) -> None:
    if self.cycle_used_minutes + required_minutes > MAX_CYCLE_MINUTES:
        self._take_cycle_restart()
```

- [ ] **Step 4: Apply fuel and cycle boundaries while driving**

Inside `_drive_leg`, replace the boundary checks at the top of the innermost
per-step `while` loop with this explicit priority order:

```python
if self.cycle_used_minutes >= MAX_CYCLE_MINUTES:
    self._take_cycle_restart()
if (
    self.shift_driving_minutes >= MAX_DRIVING_MINUTES
    or self.shift_elapsed_minutes >= MAX_SHIFT_MINUTES
):
    self._take_daily_rest()
if (
    self.route_progress_m >= self.next_fuel_at_m
    and self.route_progress_m < self.route.distance_m
):
    self._take_fuel_stop()
if self.driving_since_break_minutes >= BREAK_AFTER_DRIVING_MINUTES:
    self._take_break()
```

Add cycle capacity to the `capacity = min(...)` calculation:

```python
MAX_CYCLE_MINUTES - self.cycle_used_minutes,
```

Immediately after calculating `capacity`—and before the existing
`if capacity <= 0` guard—constrain it to stop before the next fuel boundary:

```python
distance_until_fuel = self.next_fuel_at_m - self.route_progress_m
if 0 < distance_until_fuel < remaining_distance_m:
    minutes_until_fuel = (
        remaining_minutes * distance_until_fuel
    ) // remaining_distance_m
    quarter_minutes = (minutes_until_fuel // 15) * 15
    if quarter_minutes == 0:
        self._take_fuel_stop()
        continue
    capacity = min(capacity, quarter_minutes)
```

At the beginning of `_service`, add:

```python
self._ensure_cycle_capacity(duration_minutes)
```

Because fuel uses `_service`, the existing 30-minute non-driving reset from
Task 6 applies to fuel stops as well.

After `_append` inside `_take_daily_rest`, retain the existing cycle value; only `_take_cycle_restart` resets it.

- [ ] **Step 5: Add a 14-hour-window regression using fuel time**

Append to `backend/tests/test_scheduler_cycle_fuel.py`:

```python
def test_fuel_and_pickup_time_can_trigger_fourteen_hour_rest(
    trip_request,
    locations,
) -> None:
    route = make_route(
        locations,
        first_minutes=600,
        second_minutes=60,
        first_distance_m=5100 * MILE_M,
        second_distance_m=100 * MILE_M,
    )

    events = build_schedule(trip_request, route)
    for index, event in enumerate(events):
        if event.kind != EventKind.DAILY_REST:
            continue
        shift_elapsed = sum(
            prior.duration_minutes
            for prior in events[:index]
            if prior.kind != EventKind.CYCLE_RESTART
        )
        driving_before_rest = sum(
            prior.duration_minutes
            for prior in events[:index]
            if prior.kind == EventKind.DRIVING
        )
        assert shift_elapsed == 14 * 60
        assert driving_before_rest < 11 * 60
        break
    else:
        raise AssertionError("Expected a daily rest before additional driving.")
```

- [ ] **Step 6: Run the complete scheduler suite**

Create `backend/tests/test_scheduler_invariants.py`:

```python
from dataclasses import replace

import pytest

from conftest import make_route
from trips.domain.scheduler import FUEL_INTERVAL_M, build_schedule
from trips.domain.types import DutyStatus, EventKind


@pytest.mark.parametrize(
    (
        "cycle_used_minutes",
        "first_minutes",
        "second_minutes",
        "first_distance_m",
        "second_distance_m",
    ),
    [
        (0, 120, 180, 300_000, 500_000),
        (24 * 60, 600, 1200, 900 * 1609, 1300 * 1609),
        (70 * 60, 60, 60, 100_000, 100_000),
    ],
)
def test_generated_schedule_preserves_all_hos_and_route_invariants(
    trip_request,
    locations,
    cycle_used_minutes,
    first_minutes,
    second_minutes,
    first_distance_m,
    second_distance_m,
) -> None:
    request = replace(
        trip_request,
        cycle_used_minutes=cycle_used_minutes,
    )
    route = make_route(
        locations,
        first_minutes=first_minutes,
        second_minutes=second_minutes,
        first_distance_m=first_distance_m,
        second_distance_m=second_distance_m,
    )

    events = build_schedule(request, route)
    previous_end = request.starts_at
    previous_progress_m = 0
    previous_cycle_minutes = request.cycle_used_minutes
    shift_elapsed_minutes = 0
    shift_driving_minutes = 0
    driving_since_break_minutes = 0
    fuel_points_m = [0]

    for event in events:
        assert event.start_at == previous_end
        assert event.duration_minutes > 0
        assert event.route_start_m == previous_progress_m
        assert event.route_start_m <= event.route_end_m <= route.distance_m
        assert event.cycle_used_before_minutes == previous_cycle_minutes
        assert 0 <= event.cycle_used_after_minutes <= 70 * 60

        if event.kind == EventKind.FUEL:
            fuel_points_m.append(event.route_start_m)

        if event.kind in {
            EventKind.DAILY_REST,
            EventKind.CYCLE_RESTART,
        }:
            shift_elapsed_minutes = 0
            shift_driving_minutes = 0
            driving_since_break_minutes = 0
        elif event.duty_status == DutyStatus.DRIVING:
            assert shift_driving_minutes + event.duration_minutes <= 11 * 60
            assert shift_elapsed_minutes + event.duration_minutes <= 14 * 60
            assert (
                driving_since_break_minutes + event.duration_minutes
                <= 8 * 60
            )
            shift_elapsed_minutes += event.duration_minutes
            shift_driving_minutes += event.duration_minutes
            driving_since_break_minutes += event.duration_minutes
        else:
            shift_elapsed_minutes += event.duration_minutes
            if event.duration_minutes >= 30:
                driving_since_break_minutes = 0

        previous_end = event.end_at
        previous_progress_m = event.route_end_m
        previous_cycle_minutes = event.cycle_used_after_minutes

    fuel_points_m.append(route.distance_m)
    assert previous_progress_m == route.distance_m
    assert all(
        right - left <= FUEL_INTERVAL_M
        for left, right in zip(
            fuel_points_m,
            fuel_points_m[1:],
            strict=False,
        )
    )
    assert [
        event.duration_minutes
        for event in events
        if event.kind == EventKind.PICKUP
    ] == [60]
    assert [
        event.duration_minutes
        for event in events
        if event.kind == EventKind.DROPOFF
    ] == [60]
```

Run:

```bash
backend/.venv/bin/pytest \
  backend/tests/test_scheduler_basic.py \
  backend/tests/test_scheduler_limits.py \
  backend/tests/test_scheduler_cycle_fuel.py \
  backend/tests/test_scheduler_invariants.py \
  -v
backend/.venv/bin/ruff check backend
```

Expected: seventeen passing scheduler tests and no Ruff errors.

- [ ] **Step 7: Commit cycle and fuel scheduling**

```bash
git add \
  backend/trips/domain/scheduler.py \
  backend/tests/test_scheduler_cycle_fuel.py \
  backend/tests/test_scheduler_invariants.py
git commit -m "feat: schedule fuel stops and cycle restarts"
```

---

### Task 8: Project events into complete daily logs

**Files:**
- Create: `backend/trips/domain/projector.py`
- Create: `backend/tests/test_projector.py`

**Interfaces:**
- Consumes: `TripRequest`, `NormalizedRoute`, and ordered `DutyEvent` records.
- Produces: `build_daily_logs(request, route, events) -> tuple[DailyLog, ...]`.

- [ ] **Step 1: Write failing projection tests**

Create `backend/tests/test_projector.py`:

```python
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from conftest import make_route
from trips.domain.projector import build_daily_logs
from trips.domain.scheduler import build_schedule
from trips.domain.types import EventKind


def test_each_projected_day_has_exactly_1440_minutes(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        starts_at=datetime(
            2026,
            7,
            25,
            22,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=720,
        second_minutes=600,
    )
    events = build_schedule(request, route)

    logs = build_daily_logs(request, route, events)

    assert len(logs) >= 2
    assert logs[0].cycle_used_start_minutes == 24 * 60
    assert logs[0].cycle_added_minutes == 90
    assert logs[0].cycle_remaining_end_minutes == 70 * 60 - (24 * 60 + 90)
    assert sum(log.distance_m for log in logs) == route.distance_m
    for event in events:
        assert sum(
            segment.end_minute - segment.start_minute
            for log in logs
            for segment in log.segments
            if segment.event_id == event.id
        ) == event.duration_minutes
    for log in logs:
        assert (
            log.off_duty_minutes
            + log.sleeper_berth_minutes
            + log.driving_minutes
            + log.on_duty_minutes
        ) == 1440
        assert log.segments[0].start_minute == 0
        assert log.segments[-1].end_minute == 1440
        assert all(
            left.end_minute == right.start_minute
            for left, right in zip(
                log.segments,
                log.segments[1:],
                strict=False,
            )
        )


def test_projection_splits_an_event_at_midnight(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        starts_at=datetime(
            2026,
            7,
            25,
            23,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=120,
        second_minutes=60,
    )

    logs = build_daily_logs(request, route, build_schedule(request, route))

    assert logs[0].segments[-1].end_minute == 1440
    assert logs[1].segments[0].start_minute == 0
    assert (
        logs[0].segments[-1].event_id
        == logs[1].segments[0].event_id
    )


def test_trip_ending_at_midnight_does_not_create_an_extra_day(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        starts_at=datetime(
            2026,
            7,
            25,
            20,
            0,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )

    logs = build_daily_logs(request, route, build_schedule(request, route))

    assert len(logs) == 1
    assert logs[0].date.isoformat() == "2026-07-25"
    assert logs[0].segments[-1].end_minute == 1440


def test_thirty_four_hour_restart_is_split_across_every_midnight(
    trip_request,
    locations,
) -> None:
    request = replace(
        trip_request,
        cycle_used_minutes=70 * 60,
        starts_at=datetime(
            2026,
            7,
            25,
            23,
            30,
            tzinfo=timezone(timedelta(hours=-5)),
        ),
    )
    route = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )
    events = build_schedule(request, route)

    logs = build_daily_logs(request, route, events)
    restart = next(
        event for event in events if event.kind == EventKind.CYCLE_RESTART
    )
    restart_segments = [
        segment
        for log in logs
        for segment in log.segments
        if segment.event_id == restart.id
    ]

    assert len(restart_segments) == 3
    assert sum(
        segment.end_minute - segment.start_minute
        for segment in restart_segments
    ) == 34 * 60
```

- [ ] **Step 2: Run projector tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_projector.py -v
```

Expected: FAIL because `trips.domain.projector` does not exist.

- [ ] **Step 3: Implement fixed-offset midnight projection**

Create `backend/trips/domain/projector.py`:

```python
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone

from trips.domain.types import (
    DailyLog,
    DailyLogSegment,
    DutyEvent,
    DutyStatus,
    EventKind,
    NormalizedRoute,
    TripRequest,
)

DAY_MINUTES = 24 * 60
MAX_CYCLE_MINUTES = 70 * 60


def _minute_of_day(value: datetime) -> int:
    return value.hour * 60 + value.minute


def _segment(
    event: DutyEvent,
    start_at: datetime,
    end_at: datetime,
) -> DailyLogSegment:
    end_minute = DAY_MINUTES if end_at.date() > start_at.date() else _minute_of_day(end_at)
    return DailyLogSegment(
        event_id=event.id,
        kind=event.kind,
        duty_status=event.duty_status,
        start_minute=_minute_of_day(start_at),
        end_minute=end_minute,
        location=event.location,
        remark=event.remark,
    )


def _off_duty_event(
    event_id: str,
    kind: EventKind,
    start_at: datetime,
    end_at: datetime,
    template: DutyEvent,
    cycle_used_minutes: int,
) -> DutyEvent:
    return DutyEvent(
        id=event_id,
        kind=kind,
        duty_status=DutyStatus.OFF_DUTY,
        start_at=start_at,
        end_at=end_at,
        route_start_m=template.route_start_m,
        route_end_m=template.route_start_m,
        location=template.location,
        remark="Off duty",
        cycle_used_before_minutes=cycle_used_minutes,
        cycle_used_after_minutes=cycle_used_minutes,
    )


def _cycle_at(event: DutyEvent, moment: datetime) -> int:
    if moment <= event.start_at:
        return event.cycle_used_before_minutes
    if moment >= event.end_at:
        return event.cycle_used_after_minutes
    if event.duty_status in {DutyStatus.DRIVING, DutyStatus.ON_DUTY}:
        elapsed_minutes = int(
            (moment - event.start_at).total_seconds() // 60
        )
        return event.cycle_used_before_minutes + elapsed_minutes
    return event.cycle_used_before_minutes


def _distance_during(
    event: DutyEvent,
    overlap_start: datetime,
    overlap_end: datetime,
) -> int:
    distance_m = event.route_end_m - event.route_start_m
    if distance_m <= 0:
        return 0
    duration_seconds = (event.end_at - event.start_at).total_seconds()
    start_seconds = (overlap_start - event.start_at).total_seconds()
    end_seconds = (overlap_end - event.start_at).total_seconds()
    return round(distance_m * end_seconds / duration_seconds) - round(
        distance_m * start_seconds / duration_seconds
    )


def build_daily_logs(
    request: TripRequest,
    route: NormalizedRoute,
    events: tuple[DutyEvent, ...],
) -> tuple[DailyLog, ...]:
    if not events:
        raise ValueError("Cannot build daily logs without duty events.")
    fixed_zone = timezone(timedelta(minutes=request.fixed_utc_offset_minutes))
    normalized = tuple(
        DutyEvent(
            id=event.id,
            kind=event.kind,
            duty_status=event.duty_status,
            start_at=event.start_at.astimezone(fixed_zone),
            end_at=event.end_at.astimezone(fixed_zone),
            route_start_m=event.route_start_m,
            route_end_m=event.route_end_m,
            location=event.location,
            remark=event.remark,
            cycle_used_before_minutes=event.cycle_used_before_minutes,
            cycle_used_after_minutes=event.cycle_used_after_minutes,
        )
        for event in events
    )
    first_midnight = datetime.combine(
        normalized[0].start_at.date(),
        time.min,
        fixed_zone,
    )
    last_end = normalized[-1].end_at
    final_midnight = (
        last_end
        if last_end.time() == time.min
        else datetime.combine(
            last_end.date() + timedelta(days=1),
            time.min,
            fixed_zone,
        )
    )
    timeline = [
        _off_duty_event(
            "pre-trip-off-duty",
            EventKind.PRE_TRIP_OFF_DUTY,
            first_midnight,
            normalized[0].start_at,
            normalized[0],
            normalized[0].cycle_used_before_minutes,
        ),
        *normalized,
        _off_duty_event(
            "post-trip-off-duty",
            EventKind.POST_TRIP_OFF_DUTY,
            last_end,
            final_midnight,
            normalized[-1],
            normalized[-1].cycle_used_after_minutes,
        ),
    ]

    by_date: dict = defaultdict(list)
    for event in timeline:
        cursor = event.start_at
        while cursor < event.end_at:
            midnight = datetime.combine(
                cursor.date() + timedelta(days=1),
                time.min,
                fixed_zone,
            )
            segment_end = min(event.end_at, midnight)
            by_date[cursor.date()].append(_segment(event, cursor, segment_end))
            cursor = segment_end

    logs: list[DailyLog] = []
    for trip_day, (log_date, segments) in enumerate(sorted(by_date.items()), start=1):
        if (
            segments[0].start_minute != 0
            or segments[-1].end_minute != DAY_MINUTES
            or any(
                left.end_minute != right.start_minute
                for left, right in zip(
                    segments,
                    segments[1:],
                    strict=False,
                )
            )
        ):
            raise ValueError(f"Daily log {log_date} has a gap or overlap.")
        totals = defaultdict(int)
        for segment in segments:
            totals[segment.duty_status] += segment.end_minute - segment.start_minute
        total_minutes = sum(totals.values())
        if total_minutes != DAY_MINUTES:
            raise ValueError(f"Daily log {log_date} totals {total_minutes} minutes.")
        day_start = datetime.combine(log_date, time.min, fixed_zone)
        day_end = day_start + timedelta(days=1)
        day_events = [
            event
            for event in normalized
            if event.start_at < day_end and event.end_at > day_start
        ]
        cycle_start = (
            _cycle_at(day_events[0], day_start)
            if day_events
            else request.cycle_used_minutes
        )
        cycle_end = (
            _cycle_at(day_events[-1], day_end)
            if day_events
            else cycle_start
        )
        driving = totals[DutyStatus.DRIVING]
        on_duty = totals[DutyStatus.ON_DUTY]
        logs.append(
            DailyLog(
                date=log_date,
                trip_day=trip_day,
                start_location=segments[0].location,
                end_location=segments[-1].location,
                distance_m=sum(
                    _distance_during(
                        event,
                        max(event.start_at, day_start),
                        min(event.end_at, day_end),
                    )
                    for event in day_events
                    if event.route_end_m > event.route_start_m
                ),
                segments=tuple(segments),
                off_duty_minutes=totals[DutyStatus.OFF_DUTY],
                sleeper_berth_minutes=totals[DutyStatus.SLEEPER_BERTH],
                driving_minutes=driving,
                on_duty_minutes=on_duty,
                cycle_used_start_minutes=cycle_start,
                cycle_added_minutes=driving + on_duty,
                cycle_remaining_end_minutes=max(0, MAX_CYCLE_MINUTES - cycle_end),
            )
        )
    projected_distance_m = sum(log.distance_m for log in logs)
    if projected_distance_m != route.distance_m:
        raise ValueError(
            "Daily-log distance does not match the normalized route."
        )
    return tuple(logs)
```

- [ ] **Step 4: Run projector and scheduler regression checks**

Run:

```bash
backend/.venv/bin/pytest \
  backend/tests/test_scheduler_basic.py \
  backend/tests/test_scheduler_limits.py \
  backend/tests/test_scheduler_cycle_fuel.py \
  backend/tests/test_scheduler_invariants.py \
  backend/tests/test_projector.py \
  -v
backend/.venv/bin/ruff check backend
```

Expected: twenty-one passing tests and no Ruff errors.

- [ ] **Step 5: Commit daily-log projection**

```bash
git add backend/trips/domain/projector.py backend/tests/test_projector.py
git commit -m "feat: project schedules into complete daily logs"
```

---

### Task 9: Expose normalized location search and typed errors

**Files:**
- Create: `backend/trips/errors.py`
- Create: `backend/trips/serializers.py`
- Modify: `backend/routelog/settings.py`
- Modify: `backend/trips/urls.py`
- Modify: `backend/trips/views.py`
- Create: `backend/tests/test_location_api.py`

**Interfaces:**
- Consumes: `get_routing_provider()`, `ProviderError`, `Location`, `TripRequest`, and `hours_to_minutes()`.
- Produces: `GET /api/v1/locations/search/?q=...`, `TripPlanRequestSerializer.to_domain()`, and the stable `{"error": {...}}` envelope.

- [ ] **Step 1: Write failing location API tests**

Create `backend/tests/test_location_api.py`:

```python
from unittest.mock import Mock, patch

from django.test import Client

from trips.domain.types import Coordinate, Location
from trips.serializers import LocationSerializer
from trips.services.ors_client import ProviderError


def test_location_search_returns_normalized_us_candidates() -> None:
    provider = Mock()
    provider.search_locations.return_value = (
        Location(
            "chicago",
            "Chicago, Cook County, Illinois, USA",
            Coordinate(-87.6298, 41.8781),
        ),
    )

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().get(
            "/api/v1/locations/search/",
            {"q": "Chicago"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "locations": [
            {
                "id": "chicago",
                "label": "Chicago, Cook County, Illinois, USA",
                "longitude": -87.6298,
                "latitude": 41.8781,
                "country_code": "US",
            }
        ]
    }


def test_short_location_query_does_not_call_provider() -> None:
    provider = Mock()

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().get("/api/v1/locations/search/", {"q": "ab"})

    assert response.status_code == 200
    assert response.json() == {"locations": []}
    provider.search_locations.assert_not_called()


def test_provider_failure_uses_stable_error_envelope() -> None:
    provider = Mock()
    provider.search_locations.side_effect = ProviderError(
        "PROVIDER_RATE_LIMITED",
        "The routing service rate limit was reached.",
        True,
        429,
    )

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().get(
            "/api/v1/locations/search/",
            {"q": "Chicago"},
        )

    assert response.status_code == 429
    assert response.json()["error"] == {
        "code": "PROVIDER_RATE_LIMITED",
        "message": "The routing service rate limit was reached.",
        "field": None,
        "retryable": True,
    }


def test_location_serializer_rejects_non_finite_coordinates() -> None:
    serializer = LocationSerializer(
        data={
            "id": "invalid",
            "label": "Invalid location",
            "longitude": -87.6298,
            "latitude": float("nan"),
            "country_code": "US",
        }
    )

    assert serializer.is_valid() is False
    assert "latitude" in serializer.errors
```

- [ ] **Step 2: Run location API tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_location_api.py -v
```

Expected: FAIL because the location serializer and search route do not exist.

- [ ] **Step 3: Implement the error envelope**

Create `backend/trips/errors.py`:

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def _first_detail(value) -> str:
    if isinstance(value, dict):
        return _first_detail(next(iter(value.values()), "Invalid value."))
    if isinstance(value, list):
        return _first_detail(value[0] if value else "Invalid value.")
    return str(value)


def error_response(
    code: str,
    message: str,
    *,
    status_code: int,
    field: str | None = None,
    retryable: bool = False,
) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "field": field,
                "retryable": retryable,
            }
        },
        status=status_code,
    )


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected server error occurred.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            retryable=True,
        )
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        field = next(iter(response.data), None) if isinstance(response.data, dict) else None
        detail = response.data.get(field) if field else response.data
        return error_response(
            "VALIDATION_ERROR",
            _first_detail(detail),
            status_code=response.status_code,
            field=field,
        )
    return response
```

Add this entry inside `REST_FRAMEWORK` in `backend/routelog/settings.py`:

```python
"EXCEPTION_HANDLER": "trips.errors.api_exception_handler",
```

- [ ] **Step 4: Add request and location serializers**

Create `backend/trips/serializers.py`:

```python
from datetime import datetime
from decimal import Decimal
from math import isfinite
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from trips.domain.types import Coordinate, Location, TripRequest
from trips.domain.units import ceil_datetime_to_quarter, hours_to_minutes


class LocationSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=200)
    label = serializers.CharField(max_length=300)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    country_code = serializers.CharField(max_length=2)

    def validate_longitude(self, value: float) -> float:
        if not isfinite(value):
            raise serializers.ValidationError("Longitude must be finite.")
        return value

    def validate_latitude(self, value: float) -> float:
        if not isfinite(value):
            raise serializers.ValidationError("Latitude must be finite.")
        return value

    def validate_country_code(self, value: str) -> str:
        if value.upper() != "US":
            raise serializers.ValidationError("Select a United States location.")
        return "US"

    def to_domain(self, data: dict) -> Location:
        return Location(
            id=data["id"],
            label=data["label"],
            coordinate=Coordinate(data["longitude"], data["latitude"]),
            country_code=data["country_code"],
        )


class TripPlanRequestSerializer(serializers.Serializer):
    current_location = LocationSerializer()
    pickup_location = LocationSerializer()
    dropoff_location = LocationSerializer()
    current_cycle_used_hours = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        min_value=Decimal("0"),
        max_value=Decimal("70"),
    )
    starts_at = serializers.CharField(max_length=64)
    home_terminal_timezone = serializers.CharField(max_length=64)

    def validate_current_cycle_used_hours(self, value: Decimal) -> Decimal:
        try:
            hours_to_minutes(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def validate(self, attrs: dict) -> dict:
        try:
            starts_at = datetime.fromisoformat(attrs["starts_at"])
        except ValueError as exc:
            raise serializers.ValidationError(
                {"starts_at": "Use an ISO 8601 timestamp with a UTC offset."}
            ) from exc
        if starts_at.utcoffset() is None:
            raise serializers.ValidationError(
                {"starts_at": "Start time must include a UTC offset."}
            )
        try:
            home_zone = ZoneInfo(attrs["home_terminal_timezone"])
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError(
                {"home_terminal_timezone": "Use a valid IANA timezone."}
            ) from exc
        if starts_at.astimezone(home_zone).utcoffset() != starts_at.utcoffset():
            raise serializers.ValidationError(
                {"starts_at": "Start offset does not match the home-terminal timezone."}
            )
        attrs["parsed_starts_at"] = ceil_datetime_to_quarter(starts_at)
        return attrs

    def to_domain(self) -> TripRequest:
        data = self.validated_data
        location_serializer = LocationSerializer()
        starts_at = data["parsed_starts_at"]
        offset = starts_at.utcoffset()
        if offset is None:
            raise ValueError("Validated start time must retain its UTC offset.")
        return TripRequest(
            current_location=location_serializer.to_domain(data["current_location"]),
            pickup_location=location_serializer.to_domain(data["pickup_location"]),
            dropoff_location=location_serializer.to_domain(data["dropoff_location"]),
            cycle_used_minutes=hours_to_minutes(data["current_cycle_used_hours"]),
            starts_at=starts_at,
            home_terminal_timezone=data["home_terminal_timezone"],
            fixed_utc_offset_minutes=int(offset.total_seconds() // 60),
        )
```

- [ ] **Step 5: Add the search view and route**

Replace `backend/trips/views.py` with:

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from trips.errors import error_response
from trips.services.ors_client import ProviderError
from trips.services.provider import get_routing_provider


class HealthView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request):
        return Response({"status": "ok"})


class LocationSearchView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 3:
            return Response({"locations": []})
        if len(query) > 160:
            return error_response(
                "VALIDATION_ERROR",
                "Location search must be 160 characters or fewer.",
                status_code=status.HTTP_400_BAD_REQUEST,
                field="q",
            )
        try:
            locations = get_routing_provider().search_locations(query)
        except ProviderError as exc:
            return error_response(
                exc.code,
                exc.message,
                status_code=exc.status_code,
                retryable=exc.retryable,
            )
        return Response(
            {
                "locations": [
                    {
                        "id": location.id,
                        "label": location.label,
                        "longitude": location.coordinate.longitude,
                        "latitude": location.coordinate.latitude,
                        "country_code": location.country_code,
                    }
                    for location in locations
                ]
            }
        )
```

Replace `backend/trips/urls.py` with:

```python
from django.urls import path

from trips.views import HealthView, LocationSearchView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path(
        "locations/search/",
        LocationSearchView.as_view(),
        name="location-search",
    ),
]
```

- [ ] **Step 6: Run API validation checks**

Run:

```bash
backend/.venv/bin/pytest \
  backend/tests/test_health.py \
  backend/tests/test_location_api.py \
  -v
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/ruff check backend
```

Expected: five passing API tests, no Django issues, and no Ruff errors.

- [ ] **Step 7: Commit location search**

```bash
git add backend/routelog/settings.py backend/trips backend/tests/test_location_api.py
git commit -m "feat: expose normalized location search API"
```

---

### Task 10: Compose and serialize complete trip plans

**Files:**
- Modify: `backend/trips/domain/types.py`
- Create: `backend/trips/services/planner.py`
- Modify: `backend/trips/serializers.py`
- Modify: `backend/trips/views.py`
- Modify: `backend/trips/urls.py`
- Create: `backend/tests/test_plan_api.py`

**Interfaces:**
- Consumes: `RoutingProvider`, `RouteIndex`, `build_schedule()`, `build_daily_logs()`, and `TripPlanRequestSerializer`.
- Produces: `PlanningResult`, `TripPlanner.plan(request)`, `serialize_plan(result)`, and `POST /api/v1/trips/plan/`.

- [ ] **Step 1: Write a failing planning endpoint test**

Create `backend/tests/test_plan_api.py`:

```python
from unittest.mock import Mock, patch

from django.test import Client

from conftest import make_route
from trips.services.ors_client import ProviderError


def request_payload() -> dict:
    return {
        "current_location": {
            "id": "current",
            "label": "Chicago, IL",
            "longitude": -87.6298,
            "latitude": 41.8781,
            "country_code": "US",
        },
        "pickup_location": {
            "id": "pickup",
            "label": "St. Louis, MO",
            "longitude": -90.1994,
            "latitude": 38.6270,
            "country_code": "US",
        },
        "dropoff_location": {
            "id": "dropoff",
            "label": "Phoenix, AZ",
            "longitude": -112.0740,
            "latitude": 33.4484,
            "country_code": "US",
        },
        "current_cycle_used_hours": "24.00",
        "starts_at": "2026-07-25T08:15:00-05:00",
        "home_terminal_timezone": "America/Chicago",
    }


def test_plan_endpoint_returns_route_events_stops_and_daily_logs(
    locations,
) -> None:
    provider = Mock()
    provider.api_key = "test-provider-secret"
    provider.build_route.return_value = make_route(
        locations,
        first_minutes=180,
        second_minutes=720,
    )
    provider.reverse_geocode.side_effect = lambda coordinate: locations[0]

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().post(
            "/api/v1/trips/plan/",
            request_payload(),
            content_type="application/json",
        )

    body = response.json()
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert body["meta"]["rule_set_version"] == "property-70-8-v1"
    assert body["meta"]["generated_at"].endswith("+00:00")
    assert body["route"]["geometry"]["type"] == "LineString"
    assert body["route"]["bounds"]["west"] < body["route"]["bounds"]["east"]
    assert body["summary"]["distance_m"] == provider.build_route.return_value.distance_m
    assert body["summary"]["cycle_used_start_minutes"] == 24 * 60
    assert body["events"]
    assert body["stops"]
    assert body["daily_logs"]
    assert "test-provider-secret" not in response.content.decode()
    assert all(
        sum(log["totals_minutes"].values()) == 1440
        for log in body["daily_logs"]
    )


def test_plan_endpoint_rejects_non_quarter_cycle_value() -> None:
    payload = request_payload()
    payload["current_cycle_used_hours"] = "24.10"

    response = Client().post(
        "/api/v1/trips/plan/",
        payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"]["field"] == "current_cycle_used_hours"


def test_plan_endpoint_flattens_nested_location_validation() -> None:
    payload = request_payload()
    payload["pickup_location"]["country_code"] = "CA"

    response = Client().post(
        "/api/v1/trips/plan/",
        payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["error"] == {
        "code": "VALIDATION_ERROR",
        "message": "Select a United States location.",
        "field": "pickup_location",
        "retryable": False,
    }


def test_plan_endpoint_preserves_typed_provider_failure() -> None:
    provider = Mock()
    provider.build_route.side_effect = ProviderError(
        "PROVIDER_UNAVAILABLE",
        "Routing is temporarily unavailable.",
        True,
        503,
    )

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().post(
            "/api/v1/trips/plan/",
            request_payload(),
            content_type="application/json",
        )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "PROVIDER_UNAVAILABLE",
        "message": "Routing is temporarily unavailable.",
        "field": None,
        "retryable": True,
    }


def test_planning_invariant_failure_returns_no_partial_plan() -> None:
    with (
        patch("trips.views.get_routing_provider", return_value=Mock()),
        patch(
            "trips.views.TripPlanner.plan",
            side_effect=ValueError("broken invariant"),
        ),
    ):
        response = Client().post(
            "/api/v1/trips/plan/",
            request_payload(),
            content_type="application/json",
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "PLANNING_INFEASIBLE",
            "message": "A compliant trip plan could not be generated.",
            "field": None,
            "retryable": False,
        }
    }


def test_plan_warns_when_fixed_offset_crosses_daylight_saving(
    locations,
) -> None:
    payload = request_payload()
    payload["starts_at"] = "2026-10-31T23:00:00-05:00"
    provider = Mock()
    provider.build_route.return_value = make_route(
        locations,
        first_minutes=60,
        second_minutes=60,
    )
    provider.reverse_geocode.side_effect = lambda coordinate: locations[0]

    with patch("trips.views.get_routing_provider", return_value=provider):
        response = Client().post(
            "/api/v1/trips/plan/",
            payload,
            content_type="application/json",
        )

    assert response.status_code == 200
    assert any(
        "daylight-saving" in warning
        for warning in response.json()["meta"]["warnings"]
    )
```

- [ ] **Step 2: Run planning API tests to verify they fail**

Run:

```bash
backend/.venv/bin/pytest backend/tests/test_plan_api.py -v
```

Expected: FAIL with 404 because the trip-planning route does not exist.

- [ ] **Step 3: Add the planning result type**

Append to `backend/trips/domain/types.py`:

```python
@dataclass(frozen=True)
class PlanningResult:
    request: TripRequest
    route: NormalizedRoute
    events: tuple[DutyEvent, ...]
    daily_logs: tuple[DailyLog, ...]
    warnings: tuple[str, ...]
```

- [ ] **Step 4: Implement planning orchestration and location enrichment**

First add this read-only property to `RouteIndex` in
`backend/trips/services/route_index.py`:

```python
@property
def distance_m(self) -> int:
    return self._route.distance_m
```

Create `backend/trips/services/planner.py`:

```python
from dataclasses import replace
from zoneinfo import ZoneInfo

from trips.domain.projector import build_daily_logs
from trips.domain.scheduler import build_schedule
from trips.domain.types import (
    DutyEvent,
    EventKind,
    Location,
    PlanningResult,
    TripRequest,
)
from trips.services.ors_client import RoutingProvider
from trips.services.route_index import RouteIndex


class TripPlanner:
    def __init__(self, provider: RoutingProvider) -> None:
        self.provider = provider

    def _event_location(
        self,
        event: DutyEvent,
        request: TripRequest,
        route_index: RouteIndex,
        pickup_progress_m: int,
        cache: dict[tuple[float, float], Location],
    ) -> Location:
        if event.route_start_m == 0:
            return request.current_location
        if event.route_start_m == pickup_progress_m:
            return request.pickup_location
        if event.route_start_m == route_index.distance_m:
            return request.dropoff_location
        coordinate = route_index.coordinate_at(event.route_start_m)
        key = (round(coordinate.longitude, 4), round(coordinate.latitude, 4))
        if key not in cache:
            cache[key] = self.provider.reverse_geocode(coordinate)
        return cache[key]

    def plan(self, request: TripRequest) -> PlanningResult:
        route = self.provider.build_route(
            (
                request.current_location,
                request.pickup_location,
                request.dropoff_location,
            )
        )
        route_index = RouteIndex(route)
        raw_events = build_schedule(request, route)
        pickup_progress_m = route.legs[0].distance_m
        cache: dict[tuple[float, float], Location] = {}
        events = tuple(
            replace(
                event,
                location=self._event_location(
                    event,
                    request,
                    route_index,
                    pickup_progress_m,
                    cache,
                ),
            )
            for event in raw_events
        )
        logs = build_daily_logs(request, route, events)
        home_zone = ZoneInfo(request.home_terminal_timezone)
        ending_offset = events[-1].end_at.astimezone(home_zone).utcoffset()
        ending_offset_minutes = (
            int(ending_offset.total_seconds() // 60)
            if ending_offset is not None
            else request.fixed_utc_offset_minutes
        )
        warnings = (
            (
                "This plan crosses a daylight-saving transition and keeps "
                "the trip-start home-terminal UTC offset."
            ),
        ) if ending_offset_minutes != request.fixed_utc_offset_minutes else ()
        return PlanningResult(
            request=request,
            route=route,
            events=events,
            daily_logs=logs,
            warnings=warnings,
        )
```

- [ ] **Step 5: Serialize the complete response contract**

Change the standard-library import at the top of
`backend/trips/serializers.py` to `from datetime import UTC, datetime`. Extend
the existing `trips.domain.types` import with `DutyStatus`, `EventKind`, and
`PlanningResult`, and extend the existing `trips.domain.units` import with
`meters_to_miles`. Then append:

```python
def _location_data(location: Location) -> dict:
    return {
        "id": location.id,
        "label": location.label,
        "longitude": location.coordinate.longitude,
        "latitude": location.coordinate.latitude,
        "country_code": location.country_code,
    }


def serialize_plan(result: PlanningResult) -> dict:
    route = result.route
    total_duration = sum(event.duration_minutes for event in result.events)
    duty_totals = {
        status: sum(
            event.duration_minutes
            for event in result.events
            if event.duty_status == status
        )
        for status in DutyStatus
    }
    longitudes = [point.longitude for point in route.geometry]
    latitudes = [point.latitude for point in route.geometry]
    stop_kinds = {
        EventKind.PICKUP,
        EventKind.DROPOFF,
        EventKind.FUEL,
        EventKind.BREAK,
        EventKind.DAILY_REST,
        EventKind.CYCLE_RESTART,
    }
    events = [
        {
            "id": event.id,
            "kind": event.kind,
            "duty_status": event.duty_status,
            "start_at": event.start_at.isoformat(),
            "end_at": event.end_at.isoformat(),
            "duration_minutes": event.duration_minutes,
            "route_start_m": event.route_start_m,
            "route_end_m": event.route_end_m,
            "location": _location_data(event.location),
            "remark": event.remark,
        }
        for event in result.events
    ]
    return {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "rule_set_version": "property-70-8-v1",
            "home_terminal_timezone": result.request.home_terminal_timezone,
            "fixed_utc_offset_minutes": result.request.fixed_utc_offset_minutes,
            "assumptions": [
                "Solo property-carrying driver",
                "70 hours in 8 days",
                "Fresh 11-hour driving and 14-hour shift clocks",
                "Thirty non-driving minutes after 8 driving hours",
                "Ten consecutive sleeper-berth hours reset shift clocks",
                "Thirty-four off-duty hours reset aggregate cycle usage",
                "No adverse-condition extension",
                "One hour each for pickup and drop-off",
                "Thirty-minute fuel stop before every 1,000 miles",
                "Trip-start home-terminal UTC offset remains fixed",
            ],
            "warnings": list(result.warnings),
        },
        "summary": {
            "starts_at": result.events[0].start_at.isoformat(),
            "ends_at": result.events[-1].end_at.isoformat(),
            "distance_m": route.distance_m,
            "distance_miles": str(meters_to_miles(route.distance_m)),
            "driving_minutes": sum(
                event.duration_minutes
                for event in result.events
                if event.kind == EventKind.DRIVING
            ),
            "on_duty_not_driving_minutes": duty_totals[DutyStatus.ON_DUTY],
            "off_duty_minutes": duty_totals[DutyStatus.OFF_DUTY],
            "sleeper_berth_minutes": duty_totals[DutyStatus.SLEEPER_BERTH],
            "total_duration_minutes": total_duration,
            "cycle_used_start_minutes": result.request.cycle_used_minutes,
            "cycle_used_end_minutes": result.events[-1].cycle_used_after_minutes,
            "cycle_restarts": sum(
                event.kind == EventKind.CYCLE_RESTART
                for event in result.events
            ),
            "log_days": len(result.daily_logs),
            "fuel_stops": sum(
                event.kind == EventKind.FUEL for event in result.events
            ),
            "rest_stops": sum(
                event.kind in {EventKind.DAILY_REST, EventKind.CYCLE_RESTART}
                for event in result.events
            ),
        },
        "route": {
            "bounds": {
                "west": min(longitudes),
                "south": min(latitudes),
                "east": max(longitudes),
                "north": max(latitudes),
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    [point.longitude, point.latitude]
                    for point in route.geometry
                ],
            },
            "legs": [
                {
                    "from": _location_data(leg.start),
                    "to": _location_data(leg.end),
                    "distance_m": leg.distance_m,
                    "duration_minutes": leg.duration_minutes,
                    "steps": [
                        {
                            "instruction": step.instruction,
                            "road_name": step.road_name,
                            "distance_m": step.distance_m,
                            "duration_minutes": step.duration_minutes,
                        }
                        for step in leg.steps
                    ],
                }
                for leg in route.legs
            ],
        },
        "events": events,
        "stops": [
            event for event in events if event["kind"] in stop_kinds
        ],
        "daily_logs": [
            {
                "date": log.date.isoformat(),
                "trip_day": log.trip_day,
                "start_location": _location_data(log.start_location),
                "end_location": _location_data(log.end_location),
                "distance_m": log.distance_m,
                "totals_minutes": {
                    "off_duty": log.off_duty_minutes,
                    "sleeper_berth": log.sleeper_berth_minutes,
                    "driving": log.driving_minutes,
                    "on_duty_not_driving": log.on_duty_minutes,
                },
                "cycle": {
                    "used_at_start_minutes": log.cycle_used_start_minutes,
                    "added_minutes": log.cycle_added_minutes,
                    "remaining_at_end_minutes": log.cycle_remaining_end_minutes,
                },
                "segments": [
                    {
                        "event_id": segment.event_id,
                        "kind": segment.kind,
                        "duty_status": segment.duty_status,
                        "start_minute": segment.start_minute,
                        "end_minute": segment.end_minute,
                        "location": _location_data(segment.location),
                        "remark": segment.remark,
                    }
                    for segment in log.segments
                ],
            }
            for log in result.daily_logs
        ],
    }
```

- [ ] **Step 6: Add the planning view and URL**

Add `TripPlanRequestSerializer` and `serialize_plan` to the import block at the
top of `backend/trips/views.py`, import `logging` and `TripPlanner` there, and
define `logger = logging.getLogger(__name__)` below the imports. Then append:

```python
class TripPlanView(APIView):
    authentication_classes: list[type] = []
    permission_classes: list[type] = []

    def post(self, request):
        serializer = TripPlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = TripPlanner(get_routing_provider()).plan(
                serializer.to_domain()
            )
        except ProviderError as exc:
            return error_response(
                exc.code,
                exc.message,
                status_code=exc.status_code,
                retryable=exc.retryable,
            )
        except ValueError:
            logger.exception(
                "Trip planning invariant failed",
                extra={
                    "home_terminal_timezone": serializer.validated_data.get(
                        "home_terminal_timezone"
                    ),
                    "current_cycle_used_hours": str(
                        serializer.validated_data.get(
                            "current_cycle_used_hours"
                        )
                    ),
                },
            )
            return error_response(
                "PLANNING_INFEASIBLE",
                "A compliant trip plan could not be generated.",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                retryable=False,
            )
        response = Response(serialize_plan(result))
        response["Cache-Control"] = "no-store"
        return response
```

Add this route to `backend/trips/urls.py` and import `TripPlanView`:

```python
path("trips/plan/", TripPlanView.as_view(), name="trip-plan"),
```

- [ ] **Step 7: Run the complete backend suite**

Run:

```bash
backend/.venv/bin/pytest backend/tests -v
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/ruff check backend
```

Expected: all backend tests pass, Django reports no issues, and Ruff reports no errors.

- [ ] **Step 8: Commit the complete planning API**

```bash
git add backend/trips backend/tests/test_plan_api.py
git commit -m "feat: expose complete HOS trip plans"
```

---

### Task 11: Bootstrap the Roadbook React application

**Files:**
- Modify: `.gitignore`
- Create: `THIRD_PARTY_NOTICES.md`
- Create: `frontend/.nvmrc`
- Create: `frontend/.env.example`
- Create: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/eslint.config.js`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/public/fonts/Erode-Regular.woff2`
- Create: `frontend/public/fonts/Satoshi-Bold.woff2`
- Create: `frontend/public/licenses/Fontshare-FFL.txt`
- Create: `frontend/src/assets/route-planning.svg`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/ui/button.tsx`
- Create: `frontend/src/styles/globals.css`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/App.test.tsx`
- Create: `frontend/src/main.tsx`

**Interfaces:**
- Consumes: the approved Fontshare archive and unDraw route-planning illustration.
- Produces: `npm run dev`, `npm run build`, `npm run lint`, `npm test`, Roadbook design tokens, and reusable `Button`.

- [ ] **Step 1: Invoke the frontend design skill**

Invoke `frontend-skill` and re-read the approved visual constraints in the design specification before creating frontend files.

Expected: the implementation stays image-led, restrained, responsive, and consistent with Roadbook Editorial.

- [ ] **Step 2: Add the frontend dependency manifest**

Create `frontend/.nvmrc`:

```text
22
```

Create `frontend/.env.example`:

```dotenv
VITE_API_BASE_URL=/api/v1
```

Create `frontend/package.json`:

```json
{
  "name": "routelog-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint .",
    "test": "vitest run",
    "test:watch": "vitest",
    "e2e": "playwright test"
  },
  "dependencies": {
    "@hookform/resolvers": "5.2.2",
    "@radix-ui/react-accordion": "1.2.20",
    "@radix-ui/react-slot": "1.3.3",
    "class-variance-authority": "0.7.1",
    "clsx": "2.1.1",
    "cmdk": "1.1.1",
    "leaflet": "1.9.4",
    "lucide-react": "1.26.0",
    "motion": "12.42.2",
    "react": "19.2.8",
    "react-dom": "19.2.8",
    "react-hook-form": "7.83.0",
    "react-leaflet": "5.0.0",
    "tailwind-merge": "3.6.0",
    "zod": "4.4.3"
  },
  "devDependencies": {
    "@eslint/js": "10.0.1",
    "@playwright/test": "1.62.0",
    "@tailwindcss/vite": "4.3.3",
    "@testing-library/dom": "10.4.1",
    "@testing-library/jest-dom": "7.0.0",
    "@testing-library/react": "16.3.2",
    "@testing-library/user-event": "14.6.1",
    "@types/leaflet": "1.9.21",
    "@types/node": "22.20.1",
    "@types/react": "19.2.17",
    "@types/react-dom": "19.2.3",
    "@vitejs/plugin-react": "6.0.4",
    "eslint": "10.8.0",
    "eslint-plugin-react-hooks": "7.1.1",
    "eslint-plugin-react-refresh": "0.5.3",
    "globals": "17.7.0",
    "jsdom": "29.1.1",
    "tailwindcss": "4.3.3",
    "typescript": "6.0.3",
    "typescript-eslint": "8.65.0",
    "vite": "8.1.5",
    "vitest": "4.1.10"
  }
}
```

Run:

```bash
cd frontend
npm install
cd ..
```

Expected: `frontend/package-lock.json` is generated with no installation error.

- [ ] **Step 3: Add TypeScript, Vite, and ESLint configuration**

Create `frontend/tsconfig.json`:

```json
{
  "files": [],
  "references": [
    {"path": "./tsconfig.app.json"},
    {"path": "./tsconfig.node.json"}
  ]
}
```

Create `frontend/tsconfig.app.json`:

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.app.tsbuildinfo",
    "target": "ES2023",
    "useDefineForClassFields": true,
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "types": ["vite/client", "vitest/globals"],
    "baseUrl": ".",
    "paths": {"@/*": ["./src/*"]}
  },
  "include": ["src"]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "tsBuildInfoFile": "./node_modules/.tmp/tsconfig.node.tsbuildinfo",
    "target": "ES2023",
    "lib": ["ES2023"],
    "skipLibCheck": true,
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "verbatimModuleSyntax": true,
    "moduleDetection": "force",
    "noEmit": true,
    "types": ["node"]
  },
  "include": ["vite.config.ts", "playwright.config.ts"]
}
```

Create `frontend/vite.config.ts`:

```typescript
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    css: true,
  },
});
```

Create `frontend/eslint.config.js`:

```javascript
import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "playwright-report", "test-results"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module"
      }
    },
    rules: {
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react-refresh/only-export-components": [
        "warn",
        {
          "allowConstantExport": true,
          "allowExportNames": ["buildDutyPath"]
        }
      ]
    }
  }
);
```

Create `frontend/src/test/setup.ts`:

```typescript
import "@testing-library/jest-dom/vitest";
```

- [ ] **Step 4: Extract licensed fonts and fetch the empty-state illustration**

Run:

```bash
mkdir -p frontend/public/fonts frontend/public/licenses frontend/src/assets
unzip -p FontshareKit-2607003495.zip \
  'FontshareKit-2607003495/Erode/Fonts/WEB/fonts/Erode-Regular.woff2' \
  > frontend/public/fonts/Erode-Regular.woff2
unzip -p FontshareKit-2607003495.zip \
  'FontshareKit-2607003495/Satoshi/Fonts/WEB/fonts/Satoshi-Bold.woff2' \
  > frontend/public/fonts/Satoshi-Bold.woff2
unzip -p FontshareKit-2607003495.zip \
  'FontshareKit-2607003495/Erode/License/FFL.txt' \
  > frontend/public/licenses/Fontshare-FFL.txt
curl -fsSL \
  https://cdn.undraw.co/illustration/route-planning_2psv.svg \
  -o frontend/src/assets/route-planning.svg
test -s frontend/public/fonts/Erode-Regular.woff2
test -s frontend/public/fonts/Satoshi-Bold.woff2
test -s frontend/public/licenses/Fontshare-FFL.txt
rg -q '<svg' frontend/src/assets/route-planning.svg
```

Expected: two non-empty WOFF2 files, one license file, and one SVG exist.

Create `THIRD_PARTY_NOTICES.md`:

```markdown
# Third-party notices

- Erode Regular and Satoshi Bold are supplied under the Fontshare Free Fonts
  License. The full license is distributed at
  `frontend/public/licenses/Fontshare-FFL.txt`.
- The opening route illustration is from unDraw and is used under the unDraw
  license: https://undraw.co/license
- Roadbook visual research considered shadcn/ui, Aceternity UI, and Magic UI.
  Runtime UI dependencies and licenses are recorded by `package-lock.json`;
  RouteLog-specific component source remains local to this repository.
- Map data is © OpenStreetMap contributors. Routing and geocoding use
  OpenRouteService.
```

- [ ] **Step 5: Write the failing application-shell test**

Create `frontend/src/App.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "@/App";

describe("App", () => {
  it("introduces the RouteLog planning workflow", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { name: /a clear road ahead/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/FMCSA-aware trip planning/i),
    ).toBeInTheDocument();
  });
});
```

- [ ] **Step 6: Run the shell test to verify it fails**

Run:

```bash
cd frontend
npm test -- --run src/App.test.tsx
```

Expected: FAIL because `App.tsx` does not exist.

- [ ] **Step 7: Implement the Roadbook shell and source-owned button**

Create `frontend/src/lib/utils.ts`:

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

Create `frontend/src/components/ui/button.tsx`:

```tsx
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md font-satoshi text-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-ink px-5 py-3 text-paper shadow-roadbook hover:-translate-y-0.5",
        quiet: "border border-line bg-paper px-4 py-2 text-ink hover:bg-white",
      },
    },
    defaultVariants: { variant: "primary" },
  },
);

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export function Button({
  asChild,
  className,
  variant,
  ...props
}: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return (
    <Component
      className={cn(buttonVariants({ variant }), className)}
      {...props}
    />
  );
}
```

Create `frontend/src/App.tsx`:

```tsx
import routePlanning from "@/assets/route-planning.svg";

export function App() {
  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="flex items-center justify-between border-b border-line px-6 py-4">
        <a className="font-satoshi text-sm tracking-tight" href="/">
          <span className="mr-2 inline-block size-3 rounded-route bg-amber" />
          ROUTELOG
        </a>
        <p className="font-erode text-sm text-muted">
          FMCSA-aware trip planning
        </p>
      </header>
      <section className="opening-grid">
        <div className="opening-copy">
          <p className="eyebrow">Plan your run</p>
          <h1>A clear road ahead.</h1>
          <p>
            Build a truck route, place required stops, and generate a daily
            duty log for every day of the trip.
          </p>
        </div>
        <div className="empty-map" aria-label="Route planning preview">
          <img src={routePlanning} alt="" />
          <p>Your route and planned rests will appear here.</p>
        </div>
      </section>
    </main>
  );
}
```

Create `frontend/src/main.tsx`:

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MotionConfig } from "motion/react";

import { App } from "@/App";
import "@/styles/globals.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <App />
    </MotionConfig>
  </StrictMode>,
);
```

Create `frontend/index.html`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta
      name="description"
      content="RouteLog creates truck routes, HOS-aware stops, and printable daily logs."
    />
    <title>RouteLog · HOS Trip Planner</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

Create `frontend/src/styles/globals.css`:

```css
@import "tailwindcss";

@font-face {
  font-family: "Satoshi";
  src: url("/fonts/Satoshi-Bold.woff2") format("woff2");
  font-weight: 700;
  font-display: swap;
}

@font-face {
  font-family: "Erode";
  src: url("/fonts/Erode-Regular.woff2") format("woff2");
  font-weight: 400;
  font-display: swap;
}

@theme {
  --color-paper: #f4f0e7;
  --color-ink: #182231;
  --color-amber: #e59a18;
  --color-map-green: #365c4c;
  --color-line: #d7d0c3;
  --color-muted: #6f756c;
  --font-satoshi: "Satoshi", sans-serif;
  --font-erode: "Erode", serif;
  --shadow-roadbook: 0 18px 45px rgb(24 34 49 / 0.16);
  --radius-route: 0.2rem 0.7rem 0.2rem 0.7rem;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  min-width: 320px;
  background: var(--color-paper);
}

button,
input {
  font: inherit;
}

.opening-grid {
  display: grid;
  min-height: calc(100vh - 65px);
  grid-template-columns: minmax(22rem, 2fr) minmax(0, 3fr);
}

.opening-copy {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: clamp(2rem, 6vw, 6rem);
  border-right: 1px solid var(--color-line);
}

.opening-copy h1 {
  max-width: 9ch;
  margin: 0.5rem 0 1rem;
  font: 400 clamp(3rem, 6vw, 6.5rem) / 0.9 var(--font-erode);
  letter-spacing: -0.05em;
}

.opening-copy p:not(.eyebrow) {
  max-width: 34rem;
  color: var(--color-muted);
  font: 400 1.1rem / 1.55 var(--font-erode);
}

.eyebrow {
  color: #a76000;
  font: 700 0.72rem / 1 var(--font-satoshi);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.empty-map {
  display: grid;
  place-content: center;
  gap: 1rem;
  padding: 2rem;
  overflow: hidden;
  background:
    radial-gradient(#7e8d80 0.7px, transparent 0.7px) 0 0 / 13px 13px,
    #cad9cc;
  color: var(--color-map-green);
  text-align: center;
}

.empty-map img {
  width: min(75%, 34rem);
  margin-inline: auto;
}

@media (max-width: 800px) {
  .opening-grid {
    grid-template-columns: 1fr;
  }

  .opening-copy {
    border-right: 0;
    border-bottom: 1px solid var(--color-line);
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
  }
}
```

- [ ] **Step 8: Run frontend foundation checks**

Run:

```bash
cd frontend
npm test -- --run src/App.test.tsx
npm run lint
npm run build
```

Expected: one passing test, no lint errors, and a successful Vite production build.

- [ ] **Step 9: Run React Doctor and commit**

Invoke `react-doctor`, address every actionable error it reports, then run:

```bash
git add .gitignore THIRD_PARTY_NOTICES.md frontend
git commit -m "feat: establish Roadbook React interface"
```

---

### Task 12: Create the typed frontend API client

**Files:**
- Create: `frontend/src/lib/api/types.ts`
- Create: `frontend/src/lib/api/client.ts`
- Create: `frontend/src/lib/api/client.test.ts`

**Interfaces:**
- Consumes: `/api/v1/locations/search/` and `/api/v1/trips/plan/`.
- Produces: `searchLocations(query, signal)`, `planTrip(request, signal)`, `ApiClientError`, `LocationCandidate`, `TripPlanRequest`, and `TripPlanResponse`.

- [ ] **Step 1: Define the complete TypeScript contract**

Create `frontend/src/lib/api/types.ts`:

```typescript
export type DutyStatus =
  | "off_duty"
  | "sleeper_berth"
  | "driving"
  | "on_duty_not_driving";

export type EventKind =
  | "pre_trip_off_duty"
  | "driving"
  | "pickup"
  | "dropoff"
  | "fuel"
  | "break"
  | "daily_rest"
  | "cycle_restart"
  | "post_trip_off_duty";

export interface LocationCandidate {
  id: string;
  label: string;
  longitude: number;
  latitude: number;
  country_code: "US";
}

export interface TripPlanRequest {
  current_location: LocationCandidate;
  pickup_location: LocationCandidate;
  dropoff_location: LocationCandidate;
  current_cycle_used_hours: number;
  starts_at: string;
  home_terminal_timezone: string;
}

export interface DutyEvent {
  id: string;
  kind: EventKind;
  duty_status: DutyStatus;
  start_at: string;
  end_at: string;
  duration_minutes: number;
  route_start_m: number;
  route_end_m: number;
  location: LocationCandidate;
  remark: string;
}

export interface RouteStep {
  instruction: string;
  road_name: string;
  distance_m: number;
  duration_minutes: number;
}

export interface DailyLogSegment {
  event_id: string;
  kind: EventKind;
  duty_status: DutyStatus;
  start_minute: number;
  end_minute: number;
  location: LocationCandidate;
  remark: string;
}

export interface DailyLog {
  date: string;
  trip_day: number;
  start_location: LocationCandidate;
  end_location: LocationCandidate;
  distance_m: number;
  totals_minutes: Record<DutyStatus, number>;
  cycle: {
    used_at_start_minutes: number;
    added_minutes: number;
    remaining_at_end_minutes: number;
  };
  segments: DailyLogSegment[];
}

export interface TripPlanResponse {
  meta: {
    generated_at: string;
    rule_set_version: string;
    home_terminal_timezone: string;
    fixed_utc_offset_minutes: number;
    assumptions: string[];
    warnings: string[];
  };
  summary: {
    starts_at: string;
    ends_at: string;
    distance_m: number;
    distance_miles: string;
    driving_minutes: number;
    on_duty_not_driving_minutes: number;
    off_duty_minutes: number;
    sleeper_berth_minutes: number;
    total_duration_minutes: number;
    cycle_used_start_minutes: number;
    cycle_used_end_minutes: number;
    cycle_restarts: number;
    log_days: number;
    fuel_stops: number;
    rest_stops: number;
  };
  route: {
    bounds: {
      west: number;
      south: number;
      east: number;
      north: number;
    };
    geometry: {
      type: "LineString";
      coordinates: [number, number][];
    };
    legs: {
      from: LocationCandidate;
      to: LocationCandidate;
      distance_m: number;
      duration_minutes: number;
      steps: RouteStep[];
    }[];
  };
  events: DutyEvent[];
  stops: DutyEvent[];
  daily_logs: DailyLog[];
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field: string | null;
    retryable: boolean;
  };
}
```

- [ ] **Step 2: Write failing API-client tests**

Create `frontend/src/lib/api/client.test.ts`:

```typescript
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiClientError,
  planTrip,
  searchLocations,
} from "@/lib/api/client";
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
```

- [ ] **Step 3: Run API-client tests to verify they fail**

Run:

```bash
cd frontend
npm test -- --run src/lib/api/client.test.ts
```

Expected: FAIL because `client.ts` does not exist.

- [ ] **Step 4: Implement the same-origin API client**

Create `frontend/src/lib/api/client.ts`:

```typescript
import type {
  ApiErrorBody,
  LocationCandidate,
  TripPlanRequest,
  TripPlanResponse,
} from "@/lib/api/types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly field: string | null,
    public readonly retryable: boolean,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = (await response.json()) as T | ApiErrorBody;
  if (!response.ok) {
    const error = (body as ApiErrorBody).error;
    throw new ApiClientError(
      error?.message ?? "The request could not be completed.",
      error?.code ?? "INTERNAL_ERROR",
      error?.field ?? null,
      error?.retryable ?? response.status >= 500,
      response.status,
    );
  }
  return body as T;
}

export async function searchLocations(
  query: string,
  signal?: AbortSignal,
): Promise<LocationCandidate[]> {
  const response = await fetch(
    `${API_BASE}/locations/search/?q=${encodeURIComponent(query)}`,
    { signal },
  );
  const body = await parseResponse<{ locations: LocationCandidate[] }>(
    response,
  );
  return body.locations;
}

export async function planTrip(
  request: TripPlanRequest,
  signal?: AbortSignal,
): Promise<TripPlanResponse> {
  const response = await fetch(`${API_BASE}/trips/plan/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
  return parseResponse<TripPlanResponse>(response);
}
```

- [ ] **Step 5: Run client checks and commit**

Run:

```bash
cd frontend
npm test -- --run src/lib/api/client.test.ts
npm run lint
npm run build
```

Expected: three passing client tests, no lint errors, and a successful build.

```bash
git add frontend/src/lib/api
git commit -m "feat: add typed RouteLog API client"
```

---

### Task 13: Build the four-field trip form and autocomplete

**Files:**
- Create: `frontend/src/lib/time.ts`
- Create: `frontend/src/lib/time.test.ts`
- Create: `frontend/src/hooks/useLocationSearch.ts`
- Create: `frontend/src/hooks/useLocationSearch.test.tsx`
- Create: `frontend/src/components/planner/LocationCombobox.tsx`
- Create: `frontend/src/components/planner/CycleMeter.tsx`
- Create: `frontend/src/components/planner/TripForm.tsx`
- Create: `frontend/src/components/planner/TripForm.test.tsx`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: `searchLocations()`, `TripPlanRequest`, and `LocationCandidate`.
- Produces: `getTripStartContext()`, debounced cancellable location search, `TripForm({onPlan, isPlanning})`, and exactly four visible form fields.

- [ ] **Step 1: Write failing time-context tests**

Create `frontend/src/lib/time.test.ts`:

```typescript
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
```

- [ ] **Step 2: Run the time test to verify it fails**

Run:

```bash
cd frontend
npm test -- --run src/lib/time.test.ts
```

Expected: FAIL because `time.ts` does not exist.

- [ ] **Step 3: Implement fixed-offset start-time formatting**

Create `frontend/src/lib/time.ts`:

```typescript
function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function getTripStartContext(
  now = new Date(),
  timezone = Intl.DateTimeFormat().resolvedOptions().timeZone,
  offsetMinutesWest?: number,
): {
  starts_at: string;
  home_terminal_timezone: string;
} {
  const roundedEpoch = Math.ceil(now.getTime() / (15 * 60_000)) * 15 * 60_000;
  const rounded = new Date(roundedEpoch);
  const effectiveOffset = offsetMinutesWest ?? rounded.getTimezoneOffset();
  const local = new Date(roundedEpoch - effectiveOffset * 60_000);
  const sign = effectiveOffset <= 0 ? "+" : "-";
  const absoluteOffset = Math.abs(effectiveOffset);
  const startsAt = [
    `${local.getUTCFullYear()}-${pad(local.getUTCMonth() + 1)}-${pad(local.getUTCDate())}`,
    `T${pad(local.getUTCHours())}:${pad(local.getUTCMinutes())}:00`,
    `${sign}${pad(Math.floor(absoluteOffset / 60))}:${pad(absoluteOffset % 60)}`,
  ].join("");
  return {
    starts_at: startsAt,
    home_terminal_timezone: timezone,
  };
}
```

- [ ] **Step 4: Write failing autocomplete and form behavior tests**

Create `frontend/src/hooks/useLocationSearch.test.tsx`:

```tsx
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
```

Create `frontend/src/components/planner/TripForm.test.tsx`:

```tsx
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

    expect(screen.getAllByRole("textbox")).toHaveLength(3);
    expect(screen.getByLabelText(/current cycle used/i)).toBeInTheDocument();

    for (const name of [
      /current location/i,
      /pickup location/i,
      /drop-off location/i,
    ]) {
      const input = screen.getByRole("textbox", { name });
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

    expect(
      await screen.findByText(/quarter-hour increments/i),
    ).toBeInTheDocument();
  });

  it("does not coerce a cleared cycle field to zero", async () => {
    const user = userEvent.setup();
    render(<TripForm onPlan={vi.fn()} isPlanning={false} />);

    await user.clear(screen.getByLabelText(/current cycle used/i));
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(
      await screen.findByText(/enter current cycle usage/i),
    ).toBeInTheDocument();
  });

  it("requires a new selection after an accepted location is edited", async () => {
    const user = userEvent.setup();
    render(<TripForm onPlan={vi.fn()} isPlanning={false} />);

    const current = screen.getByRole("textbox", {
      name: /current location/i,
    });
    await user.type(current, "Chicago");
    await user.click(screen.getByRole("option", { name: /Chicago/i }));
    await user.type(current, " altered");
    await user.click(screen.getByRole("button", { name: /build trip plan/i }));

    expect(
      await screen.findByText(/select a current location/i),
    ).toBeInTheDocument();
  });
});
```

- [ ] **Step 5: Run form tests to verify they fail**

Run:

```bash
cd frontend
npm test -- --run \
  src/lib/time.test.ts \
  src/hooks/useLocationSearch.test.tsx \
  src/components/planner/TripForm.test.tsx
```

Expected: the time test passes and autocomplete/form tests FAIL because their
modules do not exist.

- [ ] **Step 6: Implement debounced location search**

Create `frontend/src/hooks/useLocationSearch.ts`:

```typescript
import { useEffect, useState } from "react";

import { ApiClientError, searchLocations } from "@/lib/api/client";
import type { LocationCandidate } from "@/lib/api/types";

export function useLocationSearch(query: string) {
  const [options, setOptions] = useState<LocationCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 3) {
      setOptions([]);
      setLoading(false);
      setError(null);
      return;
    }
    setOptions([]);
    setLoading(true);
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setError(null);
      try {
        const results = await searchLocations(trimmed, controller.signal);
        if (!controller.signal.aborted) setOptions(results);
      } catch (caught) {
        if (controller.signal.aborted) return;
        setError(
          caught instanceof ApiClientError
            ? caught.message
            : "Location search is unavailable.",
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 300);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [query]);

  return { options, loading, error };
}
```

- [ ] **Step 7: Implement the combobox, meter, and validated form**

Create `frontend/src/components/planner/LocationCombobox.tsx`:

```tsx
import { Command } from "cmdk";
import { MapPin, Search } from "lucide-react";
import { useState } from "react";

import { useLocationSearch } from "@/hooks/useLocationSearch";
import type { LocationCandidate } from "@/lib/api/types";

interface Props {
  id: string;
  label: string;
  value: LocationCandidate | null;
  onChange: (location: LocationCandidate | null) => void;
  error?: string;
}

export function LocationCombobox({
  id,
  label,
  value,
  onChange,
  error,
}: Props) {
  const [query, setQuery] = useState(value?.label ?? "");
  const { options, loading, error: searchError } = useLocationSearch(query);
  const open = query.trim().length >= 3 && query !== value?.label;

  return (
    <div className="field-group">
      <label htmlFor={id}>{label}</label>
      <Command shouldFilter={false} className="location-command">
        <div className="location-input-wrap">
          <Search aria-hidden="true" size={16} />
          <Command.Input
            id={id}
            value={query}
            onValueChange={(nextQuery) => {
              setQuery(nextQuery);
              if (nextQuery !== value?.label) onChange(null);
            }}
            aria-invalid={Boolean(error)}
            aria-describedby={
              error || searchError ? `${id}-error` : undefined
            }
            placeholder="City, state, or address"
          />
        </div>
        {open && (
          <Command.List aria-label={`${label} suggestions`}>
            {loading && <Command.Loading>Searching…</Command.Loading>}
            {!loading && options.length === 0 && (
              <Command.Empty>No United States locations found.</Command.Empty>
            )}
            {options.map((option) => (
              <Command.Item
                key={option.id}
                value={option.id}
                onSelect={() => {
                  onChange(option);
                  setQuery(option.label);
                }}
              >
                <MapPin aria-hidden="true" size={15} />
                {option.label}
              </Command.Item>
            ))}
          </Command.List>
        )}
      </Command>
      {(error || searchError) && (
        <p id={`${id}-error`} role="alert" className="field-error">
          {error ?? searchError}
        </p>
      )}
    </div>
  );
}
```

Create `frontend/src/components/planner/CycleMeter.tsx`:

```tsx
interface Props {
  usedHours: number;
}

export function CycleMeter({ usedHours }: Props) {
  const safeUsed = Number.isFinite(usedHours) ? Math.min(70, Math.max(0, usedHours)) : 0;
  const remaining = 70 - safeUsed;
  return (
    <div className="cycle-meter" aria-live="polite">
      <div>
        <span>{safeUsed.toFixed(2)} h used</span>
        <strong>{remaining.toFixed(2)} h available</strong>
      </div>
      <progress max={70} value={safeUsed} aria-label="Cycle hours used" />
    </div>
  );
}
```

Create `frontend/src/components/planner/TripForm.tsx`:

```tsx
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowRight } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { CycleMeter } from "@/components/planner/CycleMeter";
import { LocationCombobox } from "@/components/planner/LocationCombobox";
import { Button } from "@/components/ui/button";
import { getTripStartContext } from "@/lib/time";
import type { LocationCandidate, TripPlanRequest } from "@/lib/api/types";

const locationSchema = z.object({
  id: z.string().min(1),
  label: z.string().min(1),
  longitude: z.number(),
  latitude: z.number(),
  country_code: z.literal("US"),
});

const formSchema = z.object({
  current_location: locationSchema.nullable().refine(Boolean, "Select a current location."),
  pickup_location: locationSchema.nullable().refine(Boolean, "Select a pickup location."),
  dropoff_location: locationSchema.nullable().refine(Boolean, "Select a drop-off location."),
  current_cycle_used_hours: z
    .number({ error: "Enter current cycle usage." })
    .min(0, "Cycle usage cannot be negative.")
    .max(70, "Cycle usage cannot exceed 70 hours.")
    .refine(
      (value) => Number.isInteger(value * 4),
      "Use quarter-hour increments.",
    ),
});

type FormInput = z.input<typeof formSchema>;
type FormValues = z.output<typeof formSchema>;

interface Props {
  onPlan: (request: TripPlanRequest) => void;
  isPlanning: boolean;
}

export function TripForm({ onPlan, isPlanning }: Props) {
  const {
    control,
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<FormInput, unknown, FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      current_location: null,
      pickup_location: null,
      dropoff_location: null,
      current_cycle_used_hours: 0,
    },
  });
  const cycleUsed = Number(watch("current_cycle_used_hours"));

  const submit = (values: FormValues) => {
    const context = getTripStartContext();
    onPlan({
      current_location: values.current_location as LocationCandidate,
      pickup_location: values.pickup_location as LocationCandidate,
      dropoff_location: values.dropoff_location as LocationCandidate,
      current_cycle_used_hours: values.current_cycle_used_hours,
      ...context,
    });
  };

  return (
    <form
      className="trip-form"
      onSubmit={handleSubmit(submit)}
      aria-busy={isPlanning}
      noValidate
    >
      {(
        [
          ["current_location", "Current location"],
          ["pickup_location", "Pickup location"],
          ["dropoff_location", "Drop-off location"],
        ] as const
      ).map(([name, label]) => (
        <Controller
          key={name}
          name={name}
          control={control}
          render={({ field }) => (
            <LocationCombobox
              id={name}
              label={label}
              value={field.value}
              onChange={field.onChange}
              error={errors[name]?.message}
            />
          )}
        />
      ))}
      <div className="field-group">
        <label htmlFor="current_cycle_used_hours">
          Current cycle used (hours)
        </label>
        <input
          id="current_cycle_used_hours"
          type="number"
          min="0"
          max="70"
          step="0.25"
          aria-invalid={Boolean(errors.current_cycle_used_hours)}
          aria-describedby={
            errors.current_cycle_used_hours
              ? "current-cycle-used-error"
              : undefined
          }
          {...register("current_cycle_used_hours", { valueAsNumber: true })}
        />
        {errors.current_cycle_used_hours && (
          <p
            id="current-cycle-used-error"
            role="alert"
            className="field-error"
          >
            {errors.current_cycle_used_hours.message}
          </p>
        )}
      </div>
      <CycleMeter usedHours={cycleUsed} />
      <a className="assumptions-link" href="#planning-assumptions">
        Review planning assumptions
      </a>
      <Button type="submit" disabled={isPlanning}>
        {isPlanning ? "Building trip plan…" : "Build trip plan"}
        <ArrowRight aria-hidden="true" size={16} />
      </Button>
    </form>
  );
}
```

- [ ] **Step 8: Wire the form to the API in the opening panel**

In `frontend/src/App.tsx`, import `TripForm` and the API client, add working
request state, and render the form after the opening copy:

```tsx
import { useState } from "react";

import { TripForm } from "@/components/planner/TripForm";
import { ApiClientError, planTrip } from "@/lib/api/client";
import type {
  TripPlanRequest,
  TripPlanResponse,
} from "@/lib/api/types";

const [isPlanning, setIsPlanning] = useState(false);
const [plan, setPlan] = useState<TripPlanResponse | null>(null);
const [error, setError] = useState<string | null>(null);

const handlePlan = async (request: TripPlanRequest) => {
  setIsPlanning(true);
  setError(null);
  try {
    setPlan(await planTrip(request));
  } catch (caught) {
    setError(
      caught instanceof ApiClientError
        ? caught.message
        : "The trip plan could not be built.",
    );
  } finally {
    setIsPlanning(false);
  }
};

<TripForm onPlan={handlePlan} isPlanning={isPlanning} />
{error && <p role="alert">{error}</p>}
{plan && <p role="status">Trip plan ready.</p>}
```

Place the state and callback inside `App`, and place the form directly below
the introductory paragraph. Task 16 retains the same API state and expands it
with cancellation, staged progress, retry handling, and the results workspace.
Place this slim reference strip immediately after the opening grid:

```tsx
<section
  id="planning-assumptions"
  className="planning-assumptions"
  aria-labelledby="planning-assumptions-title"
>
  <h2 id="planning-assumptions-title">Planning assumptions</h2>
  <p>
    Solo property carrier · aggregate 70 / 8 cycle only · fresh shift clocks
    · no adverse or split-sleeper exceptions · fixed home-terminal UTC offset
  </p>
</section>
```

Append form styles to `frontend/src/styles/globals.css`:

```css
.trip-form,
.field-group {
  display: grid;
  gap: 0.5rem;
}

.trip-form {
  gap: 1rem;
  margin-top: 2rem;
}

.field-group label {
  color: var(--color-ink);
  font: 700 0.75rem/1 var(--font-satoshi);
}

.field-group input,
.location-input-wrap {
  width: 100%;
  border: 1px solid var(--color-line);
  border-radius: 0.5rem;
  background: #fffdf8;
}

.field-group input {
  min-height: 2.8rem;
  padding: 0 0.8rem;
  color: var(--color-ink);
}

.assumptions-link {
  width: fit-content;
  color: var(--color-map-green);
  font: 700 0.72rem/1 var(--font-satoshi);
  text-underline-offset: 0.2rem;
}

.planning-assumptions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: baseline;
  padding: 0.8rem 1.5rem;
  border-block: 1px solid var(--color-line);
}

.planning-assumptions h2,
.planning-assumptions p {
  margin: 0;
}

.planning-assumptions h2 {
  font: 700 0.68rem/1 var(--font-satoshi);
  text-transform: uppercase;
}

.planning-assumptions p {
  color: var(--color-muted);
  font: 400 0.78rem/1.4 var(--font-erode);
}

.location-input-wrap {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0 0.8rem;
}

.location-input-wrap input {
  border: 0;
  outline: 0;
}

.location-input-wrap:focus-within {
  outline: 2px solid var(--color-amber);
  outline-offset: 2px;
}

[cmdk-list] {
  position: absolute;
  z-index: 1000;
  width: 100%;
  max-height: 15rem;
  overflow: auto;
  border: 1px solid var(--color-line);
  border-radius: 0.6rem;
  background: #fffdf8;
  box-shadow: var(--shadow-roadbook);
}

.location-command {
  position: relative;
}

[cmdk-item] {
  display: flex;
  gap: 0.55rem;
  padding: 0.75rem;
  cursor: pointer;
}

[cmdk-item][data-selected="true"] {
  background: #e8eee8;
}

.field-error {
  margin: 0;
  color: #9e3425;
  font: 400 0.8rem/1.3 var(--font-erode);
}

.cycle-meter div {
  display: flex;
  justify-content: space-between;
  color: var(--color-muted);
  font: 700 0.72rem/1 var(--font-satoshi);
}

.cycle-meter progress {
  width: 100%;
  accent-color: var(--color-amber);
}
```

- [ ] **Step 9: Run form checks, React Doctor, and commit**

Run:

```bash
cd frontend
npm test -- --run \
  src/lib/time.test.ts \
  src/hooks/useLocationSearch.test.tsx \
  src/components/planner/TripForm.test.tsx
npm run lint
npm run build
```

Expected: three passing tests, no lint errors, and a successful build.

Invoke `react-doctor`, resolve actionable findings, then run:

```bash
git add frontend/src
git commit -m "feat: add validated trip planning form"
```

---

### Task 14: Render the route, summary, itinerary, and directions

**Files:**
- Create: `frontend/src/lib/format.ts`
- Create: `frontend/src/lib/format.test.ts`
- Create: `frontend/src/components/ui/accordion.tsx`
- Create: `frontend/src/components/results/RouteMap.tsx`
- Create: `frontend/src/components/results/TripSummary.tsx`
- Create: `frontend/src/components/results/Itinerary.tsx`
- Create: `frontend/src/components/results/Directions.tsx`
- Create: `frontend/src/components/results/ResultsWorkspace.tsx`
- Create: `frontend/src/components/results/ResultsWorkspace.test.tsx`
- Modify: `frontend/src/styles/globals.css`

**Interfaces:**
- Consumes: `TripPlanResponse`, its canonical `events`, `stops`, route geometry, and direction steps.
- Produces: `ResultsWorkspace({plan})` in the approved map → summary → itinerary → directions order, with synchronized stop selection.

- [ ] **Step 1: Write failing fixed-time and results-workspace tests**

Create `frontend/src/lib/format.test.ts`:

```typescript
import { describe, expect, it } from "vitest";

import { formatDateTime } from "@/lib/format";

describe("formatDateTime", () => {
  it("preserves the fixed-offset wall clock encoded by the planner", () => {
    expect(formatDateTime("2026-11-01T01:30:00-05:00")).toBe(
      "Nov 1, 1:30 AM",
    );
  });
});
```

Create `frontend/src/components/results/ResultsWorkspace.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ResultsWorkspace } from "@/components/results/ResultsWorkspace";
import type { TripPlanResponse } from "@/lib/api/types";

vi.mock("@/components/results/RouteMap", () => ({
  RouteMap: ({
    plan,
    selectedEventId,
    onSelectEvent,
  }: {
    plan: TripPlanResponse;
    selectedEventId: string | null;
    onSelectEvent: (event: TripPlanResponse["events"][number]) => void;
  }) => (
    <div data-testid="route-map">
      Map data © OpenStreetMap contributors
      <button type="button" onClick={() => onSelectEvent(plan.events[0])}>
        Select map stop
      </button>
      <output data-testid="map-selection">{selectedEventId}</output>
    </div>
  ),
}));

const plan = {
  meta: {
    generated_at: "2026-07-25T13:15:00+00:00",
    rule_set_version: "property-70-8-v1",
    home_terminal_timezone: "America/Chicago",
    fixed_utc_offset_minutes: -300,
    assumptions: [],
    warnings: [],
  },
  summary: {
    starts_at: "2026-07-25T08:15:00-05:00",
    ends_at: "2026-07-26T12:15:00-05:00",
    distance_m: 1609344,
    distance_miles: "1000.00",
    driving_minutes: 900,
    on_duty_not_driving_minutes: 120,
    off_duty_minutes: 30,
    sleeper_berth_minutes: 600,
    total_duration_minutes: 1680,
    cycle_used_start_minutes: 1440,
    cycle_used_end_minutes: 2460,
    cycle_restarts: 0,
    log_days: 2,
    fuel_stops: 1,
    rest_stops: 1,
  },
  route: {
    bounds: {
      west: -112.074,
      south: 33.4484,
      east: -87.6298,
      north: 41.8781,
    },
    geometry: {
      type: "LineString",
      coordinates: [
        [-87.6298, 41.8781],
        [-112.074, 33.4484],
      ],
    },
    legs: [
      {
        from: {
          id: "current",
          label: "Chicago, IL",
          longitude: -87.6298,
          latitude: 41.8781,
          country_code: "US",
        },
        to: {
          id: "pickup",
          label: "St. Louis, MO",
          longitude: -90.1994,
          latitude: 38.627,
          country_code: "US",
        },
        distance_m: 480000,
        duration_minutes: 270,
        steps: [
          {
            instruction: "Continue southwest",
            road_name: "I-55 S",
            distance_m: 480000,
            duration_minutes: 270,
          },
        ],
      },
    ],
  },
  events: [
    {
      id: "event-001",
      kind: "pickup",
      duty_status: "on_duty_not_driving",
      start_at: "2026-07-25T12:45:00-05:00",
      end_at: "2026-07-25T13:45:00-05:00",
      duration_minutes: 60,
      route_start_m: 480000,
      route_end_m: 480000,
      location: {
        id: "pickup",
        label: "St. Louis, MO",
        longitude: -90.1994,
        latitude: 38.627,
        country_code: "US",
      },
      remark: "Pickup",
    },
  ],
  stops: [],
  daily_logs: [],
} satisfies TripPlanResponse;

describe("ResultsWorkspace", () => {
  it("renders operational results in the approved order", () => {
    render(<ResultsWorkspace plan={plan} />);

    const map = screen.getByTestId("route-map");
    const summary = screen.getByRole("region", { name: /trip summary/i });
    const itinerary = screen.getByRole("region", { name: /itinerary/i });
    const directions = screen.getByRole("region", { name: /directions/i });

    expect(map.compareDocumentPosition(summary)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(summary.compareDocumentPosition(itinerary)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(itinerary.compareDocumentPosition(directions)).toBe(
      Node.DOCUMENT_POSITION_FOLLOWING,
    );
    expect(screen.getByText("1,000 mi")).toBeInTheDocument();
    expect(screen.getByText("Pickup")).toBeInTheDocument();
  });

  it("shares selection between map markers and itinerary rows", async () => {
    const user = userEvent.setup();
    render(<ResultsWorkspace plan={plan} />);

    await user.click(
      screen.getByRole("button", { name: "Select map stop" }),
    );

    expect(screen.getByTestId("map-selection")).toHaveTextContent("event-001");
    expect(
      screen.getByRole("button", { name: /Pickup/ }),
    ).toHaveClass("selected");
  });
});
```

- [ ] **Step 2: Run the results test to verify it fails**

Run:

```bash
cd frontend
npm test -- --run \
  src/lib/format.test.ts \
  src/components/results/ResultsWorkspace.test.tsx
```

Expected: FAIL because the formatting and results modules do not exist.

- [ ] **Step 3: Add formatting and the source-owned accordion**

Create `frontend/src/lib/format.ts`:

```typescript
export function formatDuration(minutes: number): string {
  const days = Math.floor(minutes / 1440);
  const hours = Math.floor((minutes % 1440) / 60);
  const remainder = minutes % 60;
  return [
    days ? `${days}d` : "",
    hours ? `${hours}h` : "",
    remainder ? `${remainder}m` : "",
  ].filter(Boolean).join(" ") || "0m";
}

export function formatMiles(miles: string | number): string {
  return `${Math.round(Number(miles)).toLocaleString("en-US")} mi`;
}

export function formatDateTime(value: string): string {
  const match = value.match(
    /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/,
  );
  if (!match) return value;
  const [, year, month, day, hour, minute] = match;
  const fixedWallClock = new Date(
    Date.UTC(
      Number(year),
      Number(month) - 1,
      Number(day),
      Number(hour),
      Number(minute),
    ),
  );
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: "UTC",
  }).format(fixedWallClock);
}
```

Create `frontend/src/components/ui/accordion.tsx`:

```tsx
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";

interface Props {
  title: string;
  children: ReactNode;
}

export function Accordion({ title, children }: Props) {
  return (
    <AccordionPrimitive.Root type="single" collapsible>
      <AccordionPrimitive.Item value="content" className="accordion-item">
        <AccordionPrimitive.Header>
          <AccordionPrimitive.Trigger className="accordion-trigger">
            {title}
            <ChevronDown aria-hidden="true" size={17} />
          </AccordionPrimitive.Trigger>
        </AccordionPrimitive.Header>
        <AccordionPrimitive.Content className="accordion-content">
          {children}
        </AccordionPrimitive.Content>
      </AccordionPrimitive.Item>
    </AccordionPrimitive.Root>
  );
}
```

- [ ] **Step 4: Implement map rendering and map fitting**

Create `frontend/src/components/results/RouteMap.tsx`:

```tsx
import "leaflet/dist/leaflet.css";

import { latLngBounds } from "leaflet";
import { useEffect } from "react";
import {
  CircleMarker,
  MapContainer,
  Polyline,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import { formatDateTime, formatDuration } from "@/lib/format";
import type { DutyEvent, TripPlanResponse } from "@/lib/api/types";

const STOP_COLORS: Record<string, string> = {
  current: "#7e8d80",
  pickup: "#e59a18",
  dropoff: "#365c4c",
  fuel: "#b76c19",
  break: "#58728a",
  daily_rest: "#182231",
  cycle_restart: "#7f4d82",
};

function FitRoute({
  coordinates,
}: {
  coordinates: [number, number][];
}) {
  const map = useMap();
  useEffect(() => {
    const bounds = latLngBounds(
      coordinates.map(([longitude, latitude]) => [latitude, longitude]),
    );
    map.fitBounds(bounds, { padding: [32, 32] });
  }, [coordinates, map]);
  return null;
}

interface Props {
  plan: TripPlanResponse;
  selectedEventId: string | null;
  onSelectEvent: (event: DutyEvent) => void;
}

export function RouteMap({
  plan,
  selectedEventId,
  onSelectEvent,
}: Props) {
  const positions = plan.route.geometry.coordinates.map(
    ([longitude, latitude]) => [latitude, longitude] as [number, number],
  );
  const current = plan.route.legs[0].from;
  const markers = [
    {
      id: "current-location",
      kind: "current",
      location: current,
      remark: "Current location",
      start_at: plan.summary.starts_at,
      duration_minutes: 0,
    },
    ...plan.stops,
  ];

  return (
    <section className="route-map-shell" aria-label="Planned route map">
      <MapContainer
        center={positions[0]}
        zoom={5}
        scrollWheelZoom
        className="route-map"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> · Routing by <a href="https://openrouteservice.org/">openrouteservice</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline positions={positions} pathOptions={{ color: "#182231", weight: 5 }} />
        {markers.map((marker) => (
          <CircleMarker
            key={marker.id}
            center={[
              marker.location.latitude,
              marker.location.longitude,
            ]}
            radius={selectedEventId === marker.id ? 10 : 7}
            pathOptions={{
              color: "#fffdf8",
              weight: 3,
              fillColor: STOP_COLORS[marker.kind] ?? "#182231",
              fillOpacity: 1,
            }}
            eventHandlers={{
              click: () => {
                if ("duty_status" in marker) onSelectEvent(marker);
              },
            }}
          >
            <Popup>
              <strong>{marker.remark}</strong>
              <span>{marker.location.label}</span>
              <span>
                {formatDateTime(marker.start_at)}
                {marker.duration_minutes
                  ? ` · ${formatDuration(marker.duration_minutes)}`
                  : ""}
              </span>
              {"duty_status" in marker && (
                <span>{marker.duty_status.replaceAll("_", " ")}</span>
              )}
            </Popup>
          </CircleMarker>
        ))}
        <FitRoute coordinates={plan.route.geometry.coordinates} />
      </MapContainer>
    </section>
  );
}
```

- [ ] **Step 5: Implement summary, itinerary, and directions**

Create `frontend/src/components/results/TripSummary.tsx`:

```tsx
import { formatDuration, formatMiles } from "@/lib/format";
import type { TripPlanResponse } from "@/lib/api/types";

export function TripSummary({ plan }: { plan: TripPlanResponse }) {
  const stats = [
    ["Distance", formatMiles(plan.summary.distance_miles)],
    ["Trip time", formatDuration(plan.summary.total_duration_minutes)],
    ["Driving", formatDuration(plan.summary.driving_minutes)],
    ["Daily logs", String(plan.summary.log_days)],
  ];
  return (
    <section className="trip-summary" aria-label="Trip summary">
      {stats.map(([label, value]) => (
        <div key={label}>
          <strong>{value}</strong>
          <span>{label}</span>
        </div>
      ))}
    </section>
  );
}
```

Create `frontend/src/components/results/Itinerary.tsx`:

```tsx
import {
  BedDouble,
  CircleParking,
  Clock3,
  Fuel,
  MapPin,
  PackageCheck,
  Truck,
} from "lucide-react";
import { motion } from "motion/react";

import { formatDateTime, formatDuration } from "@/lib/format";
import type { DutyEvent } from "@/lib/api/types";

const icons = {
  driving: Truck,
  pickup: PackageCheck,
  dropoff: MapPin,
  fuel: Fuel,
  break: CircleParking,
  daily_rest: BedDouble,
  cycle_restart: Clock3,
  pre_trip_off_duty: Clock3,
  post_trip_off_duty: Clock3,
};

interface Props {
  events: DutyEvent[];
  selectedEventId: string | null;
  onSelectEvent: (event: DutyEvent) => void;
}

export function Itinerary({
  events,
  selectedEventId,
  onSelectEvent,
}: Props) {
  return (
    <section className="itinerary" aria-label="Itinerary">
      <div className="section-heading">
        <p className="eyebrow">Operational timeline</p>
        <h2>Planned duty timeline.</h2>
      </div>
      <ol>
        {events.map((event) => {
          const Icon = icons[event.kind];
          return (
            <li key={event.id}>
              <button
                type="button"
                className={selectedEventId === event.id ? "selected" : ""}
                onClick={() => onSelectEvent(event)}
                onFocus={() => onSelectEvent(event)}
              >
                {selectedEventId === event.id && (
                  <motion.span
                    layoutId="itinerary-selection"
                    className="itinerary-selection"
                    transition={{ type: "spring", stiffness: 420, damping: 34 }}
                  />
                )}
                <Icon aria-hidden="true" size={17} />
                <span>
                  <strong>{event.remark}</strong>
                  <small>{event.location.label}</small>
                </span>
                <span>
                  {formatDateTime(event.start_at)}
                  <small>{formatDuration(event.duration_minutes)}</small>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
```

Create `frontend/src/components/results/Directions.tsx`:

```tsx
import { Accordion } from "@/components/ui/accordion";
import { formatDuration, formatMiles } from "@/lib/format";
import type { TripPlanResponse } from "@/lib/api/types";

export function Directions({ plan }: { plan: TripPlanResponse }) {
  const steps = plan.route.legs.flatMap((leg) => leg.steps);
  return (
    <section aria-label="Directions" className="directions">
      <Accordion title={`${steps.length} turn-by-turn directions`}>
        <ol>
          {steps.map((step, index) => (
            <li key={`${step.instruction}-${index}`}>
              <span>{index + 1}</span>
              <p>
                <strong>{step.instruction}</strong>
                <small>
                  {step.road_name || "Unnamed road"} ·{" "}
                  {formatMiles(step.distance_m / 1609.344)} ·{" "}
                  {formatDuration(step.duration_minutes)}
                </small>
              </p>
            </li>
          ))}
        </ol>
      </Accordion>
    </section>
  );
}
```

Create `frontend/src/components/results/ResultsWorkspace.tsx`:

```tsx
import { useState } from "react";
import { motion } from "motion/react";

import { Directions } from "@/components/results/Directions";
import { Itinerary } from "@/components/results/Itinerary";
import { RouteMap } from "@/components/results/RouteMap";
import { TripSummary } from "@/components/results/TripSummary";
import type { DutyEvent, TripPlanResponse } from "@/lib/api/types";

export function ResultsWorkspace({ plan }: { plan: TripPlanResponse }) {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const selectEvent = (event: DutyEvent) => setSelectedEventId(event.id);

  return (
    <motion.section
      className="results-workspace"
      aria-label="Generated trip plan"
      initial={{ opacity: 0, y: 18, filter: "blur(8px)" }}
      animate={{ opacity: 1, y: 0, filter: "blur(0)" }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
    >
      <RouteMap
        plan={plan}
        selectedEventId={selectedEventId}
        onSelectEvent={selectEvent}
      />
      <TripSummary plan={plan} />
      <Itinerary
        events={plan.events}
        selectedEventId={selectedEventId}
        onSelectEvent={selectEvent}
      />
      <Directions plan={plan} />
    </motion.section>
  );
}
```

- [ ] **Step 6: Add the results styles**

Append to `frontend/src/styles/globals.css`:

```css
.results-workspace {
  display: grid;
  gap: 0;
  border-top: 1px solid var(--color-line);
}

.route-map-shell,
.route-map {
  min-height: clamp(28rem, 65vh, 48rem);
}

.trip-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-block: 1px solid var(--color-line);
}

.trip-summary > div {
  padding: 1.5rem;
  border-right: 1px solid var(--color-line);
}

.trip-summary > div:last-child {
  border-right: 0;
}

.trip-summary strong,
.trip-summary span {
  display: block;
}

.trip-summary strong {
  font: 700 clamp(1.5rem, 3vw, 2.5rem)/1 var(--font-satoshi);
}

.trip-summary span {
  margin-top: 0.45rem;
  color: var(--color-muted);
  font: 700 0.7rem/1 var(--font-satoshi);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.itinerary,
.directions {
  padding: clamp(2rem, 6vw, 5rem);
}

.section-heading h2 {
  margin: 0.5rem 0 2rem;
  font: 400 clamp(2rem, 5vw, 4.5rem)/0.95 var(--font-erode);
}

.itinerary ol,
.directions ol {
  margin: 0;
  padding: 0;
  list-style: none;
}

.itinerary li {
  border-top: 1px solid var(--color-line);
}

.itinerary button {
  position: relative;
  display: grid;
  width: 100%;
  grid-template-columns: auto 1fr auto;
  gap: 1rem;
  align-items: center;
  padding: 1rem 0.75rem;
  border: 0;
  background: transparent;
  color: var(--color-ink);
  text-align: left;
  cursor: pointer;
}

.itinerary button.selected {
  background: #e8eee8;
}

.itinerary-selection {
  position: absolute;
  inset-block: 0.55rem;
  left: 0;
  width: 3px;
  border-radius: 999px;
  background: var(--color-amber);
}

.itinerary small {
  display: block;
  margin-top: 0.25rem;
  color: var(--color-muted);
  font: 400 0.82rem/1.3 var(--font-erode);
}

.accordion-trigger {
  display: flex;
  width: 100%;
  justify-content: space-between;
  padding: 1rem;
  border: 1px solid var(--color-line);
  border-radius: 0.7rem;
  background: #fffdf8;
  color: var(--color-ink);
  font: 700 0.9rem/1 var(--font-satoshi);
}

.accordion-content {
  overflow: hidden;
}

.directions li {
  display: grid;
  grid-template-columns: 2rem 1fr;
  gap: 0.75rem;
  padding: 1rem;
  border-bottom: 1px solid var(--color-line);
}

.directions p {
  margin: 0;
}

.directions small {
  display: block;
  margin-top: 0.35rem;
  color: var(--color-muted);
}

@media (max-width: 700px) {
  .trip-summary {
    grid-template-columns: 1fr 1fr;
  }

  .trip-summary > div:nth-child(2) {
    border-right: 0;
  }

  .trip-summary > div:nth-child(-n + 2) {
    border-bottom: 1px solid var(--color-line);
  }
}
```

- [ ] **Step 7: Run result checks, React Doctor, and commit**

Run:

```bash
cd frontend
npm test -- --run \
  src/lib/format.test.ts \
  src/components/results/ResultsWorkspace.test.tsx
npm run lint
npm run build
```

Expected: three passing formatting/results tests, no lint errors, and a
successful build.

Invoke `react-doctor`, resolve actionable findings, then run:

```bash
git add frontend/src
git commit -m "feat: render map-first trip results"
```

---

### Task 15: Render the original daily logs and print view

**Files:**
- Create: `frontend/src/components/logs/DutyGraph.tsx`
- Create: `frontend/src/components/logs/DailyLogSheet.tsx`
- Create: `frontend/src/components/logs/PrintToolbar.tsx`
- Create: `frontend/src/components/logs/DailyLogSheet.test.tsx`
- Modify: `frontend/src/components/results/ResultsWorkspace.tsx`
- Modify: `frontend/src/styles/globals.css`

**Interfaces:**
- Consumes: `DailyLog`, `DailyLogSegment`, plan timezone, and summary.
- Produces: `buildDutyPath(segments)`, `DutyGraph`, `DailyLogSheet`, one print page per daily log, and `window.print()` control.

- [ ] **Step 1: Write failing duty-path and sheet tests**

Create `frontend/src/components/logs/DailyLogSheet.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import {
  DailyLogSheet,
} from "@/components/logs/DailyLogSheet";
import { buildDutyPath } from "@/components/logs/DutyGraph";
import type { DailyLog } from "@/lib/api/types";

const location = {
  id: "omaha",
  label: "Omaha, NE",
  longitude: -95.9345,
  latitude: 41.2565,
  country_code: "US" as const,
};

const log = {
  date: "2026-07-25",
  trip_day: 1,
  start_location: location,
  end_location: location,
  distance_m: 1030000,
  totals_minutes: {
    off_duty: 420,
    sleeper_berth: 300,
    driving: 660,
    on_duty_not_driving: 60,
  },
  cycle: {
    used_at_start_minutes: 1440,
    added_minutes: 750,
    remaining_at_end_minutes: 2010,
  },
  segments: [
    {
      event_id: "off",
      kind: "pre_trip_off_duty",
      duty_status: "off_duty",
      start_minute: 0,
      end_minute: 360,
      location,
      remark: "Off duty",
    },
    {
      event_id: "pickup",
      kind: "pickup",
      duty_status: "on_duty_not_driving",
      start_minute: 360,
      end_minute: 420,
      location,
      remark: "Pickup",
    },
    {
      event_id: "drive",
      kind: "driving",
      duty_status: "driving",
      start_minute: 420,
      end_minute: 1080,
      location,
      remark: "Drive",
    },
    {
      event_id: "rest",
      kind: "daily_rest",
      duty_status: "sleeper_berth",
      start_minute: 1080,
      end_minute: 1380,
      location,
      remark: "Daily rest",
    },
    {
      event_id: "post",
      kind: "post_trip_off_duty",
      duty_status: "off_duty",
      start_minute: 1380,
      end_minute: 1440,
      location,
      remark: "Off duty",
    },
  ],
} satisfies DailyLog;

describe("DailyLogSheet", () => {
  it("draws horizontal duty lines and vertical transitions", () => {
    expect(buildDutyPath(log.segments)).toContain("H");
    expect(buildDutyPath(log.segments)).toContain("V");
  });

  it("renders an original complete 24-hour planning sheet", () => {
    render(
      <DailyLogSheet
        log={log}
        totalLogs={2}
        homeTimezone="America/Chicago"
      />,
    );

    expect(
      screen.getByRole("heading", { name: /driver's daily log/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("24.0 h")).toBeInTheDocument();
    expect(screen.getByText(/not a certified ELD/i)).toBeInTheDocument();
    expect(screen.getByText("Driver")).toBeInTheDocument();
    expect(screen.getByText("Carrier")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run log tests to verify they fail**

Run:

```bash
cd frontend
npm test -- --run src/components/logs/DailyLogSheet.test.tsx
```

Expected: FAIL because the log components do not exist.

- [ ] **Step 3: Implement the SVG duty graph**

Create `frontend/src/components/logs/DutyGraph.tsx`:

```tsx
import type {
  DailyLogSegment,
  DutyStatus,
} from "@/lib/api/types";

const X_START = 118;
const X_WIDTH = 650;
const STATUS_Y: Record<DutyStatus, number> = {
  off_duty: 52,
  sleeper_berth: 91,
  driving: 130,
  on_duty_not_driving: 169,
};

function xForMinute(minute: number): number {
  return X_START + (minute / 1440) * X_WIDTH;
}

export function buildDutyPath(segments: DailyLogSegment[]): string {
  if (segments.length === 0) return "";
  const commands = [
    `M ${xForMinute(segments[0].start_minute)} ${STATUS_Y[segments[0].duty_status]}`,
  ];
  segments.forEach((segment, index) => {
    commands.push(`H ${xForMinute(segment.end_minute)}`);
    const next = segments[index + 1];
    if (next) commands.push(`V ${STATUS_Y[next.duty_status]}`);
  });
  return commands.join(" ");
}

export function DutyGraph({
  segments,
  totals,
}: {
  segments: DailyLogSegment[];
  totals: Record<DutyStatus, number>;
}) {
  const statuses: [DutyStatus, string][] = [
    ["off_duty", "OFF DUTY"],
    ["sleeper_berth", "SLEEPER BERTH"],
    ["driving", "DRIVING"],
    ["on_duty_not_driving", "ON DUTY"],
  ];
  return (
    <svg
      className="duty-graph"
      viewBox="0 0 860 205"
      role="img"
      aria-label="Twenty-four hour duty status graph"
    >
      {Array.from({ length: 25 }, (_, hour) => {
        const x = xForMinute(hour * 60);
        return (
          <g key={hour}>
            <line x1={x} x2={x} y1="33" y2="188" className="hour-line" />
            {hour % 2 === 0 && (
              <text x={x} y="18" textAnchor="middle" className="hour-label">
                {String(hour).padStart(2, "0")}
              </text>
            )}
          </g>
        );
      })}
      {Array.from({ length: 96 }, (_, quarter) => {
        const x = xForMinute(quarter * 15);
        return (
          <line
            key={quarter}
            x1={x}
            x2={x}
            y1="33"
            y2="188"
            className="quarter-line"
          />
        );
      })}
      {statuses.map(([status, label]) => (
        <g key={status}>
          <line
            x1={X_START}
            x2={X_START + X_WIDTH}
            y1={STATUS_Y[status] + 19.5}
            y2={STATUS_Y[status] + 19.5}
            className="row-line"
          />
          <text x="4" y={STATUS_Y[status] + 3} className="status-label">
            {label}
          </text>
          <text x="820" y={STATUS_Y[status] + 3} className="status-total">
            {(totals[status] / 60).toFixed(1)}
          </text>
        </g>
      ))}
      <path d={buildDutyPath(segments)} className="duty-path-halo" />
      <path d={buildDutyPath(segments)} className="duty-path" />
    </svg>
  );
}
```

- [ ] **Step 4: Implement the original RouteLog sheet**

Create `frontend/src/components/logs/DailyLogSheet.tsx`:

```tsx
import { DutyGraph } from "@/components/logs/DutyGraph";
import { formatMiles } from "@/lib/format";
import type { DailyLog } from "@/lib/api/types";

function minutesAsHours(minutes: number): string {
  return `${(minutes / 60).toFixed(1)} h`;
}

export function DailyLogSheet({
  log,
  totalLogs,
  homeTimezone,
}: {
  log: DailyLog;
  totalLogs: number;
  homeTimezone: string;
}) {
  const totalMinutes = Object.values(log.totals_minutes).reduce(
    (sum, value) => sum + value,
    0,
  );
  const remarks = log.segments.filter(
    (segment) =>
      !["pre_trip_off_duty", "post_trip_off_duty"].includes(segment.kind),
  );

  return (
    <article className="daily-log-sheet">
      <header className="log-header">
        <div className="log-brand">
          <span className="sheet-mark" />
          <div>
            <h2>ROUTELOG · DRIVER'S DAILY LOG</h2>
            <p>Planned record of duty status</p>
          </div>
        </div>
        <dl>
          <div>
            <dt>Date</dt>
            <dd>{log.date}</dd>
          </div>
          <div>
            <dt>Trip day</dt>
            <dd>{String(log.trip_day).padStart(2, "0")} / {String(totalLogs).padStart(2, "0")}</dd>
          </div>
        </dl>
      </header>

      <section className="log-route">
        <div>
          <span>{log.start_location.label}</span>
          <i />
          <span>{log.end_location.label}</span>
        </div>
        <dl>
          <div><dt>Distance</dt><dd>{formatMiles(log.distance_m / 1609.344)}</dd></div>
          <div><dt>Driving</dt><dd>{minutesAsHours(log.totals_minutes.driving)}</dd></div>
          <div><dt>Rule set</dt><dd>70 / 8</dd></div>
        </dl>
      </section>

      <section className="identity-fields" aria-label="Writable driver details">
        {["Driver", "Carrier", "Vehicle / unit", "Shipping document"].map((label) => (
          <div key={label}><span>{label}</span><i /></div>
        ))}
      </section>

      <section className="log-graph">
        <div className="log-section-heading">
          <strong>24-HOUR DUTY STATUS</strong>
          <span>{homeTimezone} · fixed trip-start offset</span>
        </div>
        <DutyGraph segments={log.segments} totals={log.totals_minutes} />
      </section>

      <section className="log-remarks">
        <div className="remarks-header">
          <span>Time</span><span>Duty change / reason</span><span>Location</span>
        </div>
        {remarks.map((segment) => (
          <div className="remark-entry" key={`${segment.event_id}-${segment.start_minute}`}>
            <time>
              {String(Math.floor(segment.start_minute / 60)).padStart(2, "0")}:
              {String(segment.start_minute % 60).padStart(2, "0")}
            </time>
            <span>{segment.remark}</span>
            <span>{segment.location.label}</span>
          </div>
        ))}
      </section>

      <section className="log-recap">
        <div>
          <strong>8-DAY CYCLE RECAP</strong>
          <dl>
            <div><dt>Used before day</dt><dd>{minutesAsHours(log.cycle.used_at_start_minutes)}</dd></div>
            <div><dt>On duty today</dt><dd>{minutesAsHours(log.cycle.added_minutes)}</dd></div>
            <div><dt>Remaining</dt><dd>{minutesAsHours(log.cycle.remaining_at_end_minutes)}</dd></div>
          </dl>
        </div>
        <div className="driver-review">
          <strong>DRIVER REVIEW</strong>
          <i />
          <span>Signature / date</span>
        </div>
      </section>

      <footer>
        <span>{minutesAsHours(totalMinutes)} balanced</span>
        Planning copy generated from a proposed route. Review before use.
        RouteLog is not a certified ELD.
      </footer>
    </article>
  );
}
```

Create `frontend/src/components/logs/PrintToolbar.tsx`:

```tsx
import { Printer } from "lucide-react";

import { Button } from "@/components/ui/button";

export function PrintToolbar() {
  return (
    <div className="print-toolbar">
      <div>
        <p className="eyebrow">Daily records</p>
        <h2>Review every day, then print or save as PDF.</h2>
      </div>
      <Button type="button" onClick={() => window.print()}>
        <Printer aria-hidden="true" size={16} />
        Print / Save PDF
      </Button>
    </div>
  );
}
```

- [ ] **Step 5: Add logs after directions**

In `frontend/src/components/results/ResultsWorkspace.tsx`, import `DailyLogSheet` and `PrintToolbar`, then add this after `<Directions>`:

```tsx
<section className="daily-logs" aria-label="Daily log sheets">
  <PrintToolbar />
  {plan.daily_logs.map((log) => (
    <DailyLogSheet
      key={log.date}
      log={log}
      totalLogs={plan.daily_logs.length}
      homeTimezone={plan.meta.home_terminal_timezone}
    />
  ))}
</section>
```

- [ ] **Step 6: Add screen and print styling**

Append to `frontend/src/styles/globals.css`:

```css
.daily-logs {
  display: grid;
  gap: 2rem;
  padding: clamp(1rem, 4vw, 4rem);
  background: var(--color-ink);
}

.print-toolbar {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 2rem;
  color: var(--color-paper);
}

.print-toolbar h2 {
  max-width: 18ch;
  margin: 0.5rem 0 0;
  font: 400 clamp(2rem, 4vw, 3.5rem)/0.95 var(--font-erode);
}

.daily-log-sheet {
  width: min(100%, 850px);
  margin-inline: auto;
  overflow: hidden;
  background: #fbf8ef;
  color: var(--color-ink);
  box-shadow: 0 18px 48px rgb(0 0 0 / 0.28);
}

.log-header,
.log-route,
.identity-fields,
.log-recap {
  display: grid;
}

.log-header {
  grid-template-columns: 1.35fr 0.65fr;
  border-bottom: 2px solid var(--color-ink);
}

.log-brand {
  display: flex;
  gap: 0.8rem;
  align-items: center;
  padding: 1.2rem;
  border-right: 1px solid var(--color-line);
}

.log-brand h2,
.log-brand p {
  margin: 0;
}

.log-brand h2 {
  font: 700 0.9rem/1 var(--font-satoshi);
}

.log-brand p {
  margin-top: 0.35rem;
  color: var(--color-muted);
  font: 400 0.72rem/1 var(--font-erode);
}

.sheet-mark {
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-route);
  background: var(--color-amber);
}

.log-header dl,
.log-route dl,
.log-recap dl {
  display: grid;
  margin: 0;
}

.log-header dl {
  grid-template-columns: 1fr 1fr;
}

.log-header dl > div,
.log-route dl > div {
  padding: 0.8rem;
  border-left: 1px solid var(--color-line);
}

.daily-log-sheet dt {
  color: var(--color-muted);
  font: 700 0.58rem/1 var(--font-satoshi);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.daily-log-sheet dd {
  margin: 0.4rem 0 0;
  font: 700 0.8rem/1 var(--font-satoshi);
}

.log-route {
  grid-template-columns: 1.5fr 1fr;
  border-bottom: 1px solid var(--color-line);
}

.log-route > div:first-child {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 1rem;
}

.log-route i {
  flex: 1;
  height: 2px;
  background: var(--color-map-green);
}

.log-route dl {
  grid-template-columns: repeat(3, 1fr);
}

.identity-fields {
  grid-template-columns: repeat(4, 1fr);
  border-bottom: 1px solid var(--color-line);
}

.identity-fields > div {
  min-height: 3.2rem;
  padding: 0.65rem;
  border-right: 1px solid var(--color-line);
  font: 700 0.58rem/1 var(--font-satoshi);
  text-transform: uppercase;
}

.identity-fields i,
.driver-review i {
  display: block;
  margin-top: 1rem;
  border-bottom: 1px dotted var(--color-muted);
}

.log-graph {
  padding: 1rem;
}

.log-section-heading {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font: 700 0.62rem/1 var(--font-satoshi);
}

.duty-graph {
  width: 100%;
}

.hour-line,
.row-line {
  stroke: #a8aaa3;
  stroke-width: 1;
}

.quarter-line {
  stroke: #dcd6ca;
  stroke-width: 0.5;
}

.hour-label,
.status-label,
.status-total {
  fill: #667067;
  font: 700 8px var(--font-satoshi);
}

.status-total {
  fill: var(--color-ink);
}

.duty-path-halo,
.duty-path {
  fill: none;
  stroke-linejoin: round;
}

.duty-path-halo {
  stroke: #fbf8ef;
  stroke-width: 7;
}

.duty-path {
  stroke: var(--color-ink);
  stroke-width: 3;
}

.log-remarks {
  margin: 0 1rem 1rem;
  border: 1px solid var(--color-line);
}

.remarks-header,
.remark-entry {
  display: grid;
  grid-template-columns: 5rem 1fr 11rem;
}

.remarks-header {
  padding: 0.55rem;
  background: var(--color-ink);
  color: var(--color-paper);
  font: 700 0.55rem/1 var(--font-satoshi);
  text-transform: uppercase;
}

.remark-entry > * {
  padding: 0.55rem;
  border-right: 1px solid var(--color-line);
  border-bottom: 1px solid var(--color-line);
  font: 700 0.62rem/1.2 var(--font-satoshi);
}

.log-recap {
  grid-template-columns: 1.2fr 0.8fr;
  border-top: 1px solid var(--color-line);
}

.log-recap > div {
  padding: 1rem;
}

.log-recap > div:first-child {
  border-right: 1px solid var(--color-line);
}

.log-recap dl {
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  margin-top: 0.8rem;
}

.log-recap dl > div {
  padding: 0.6rem;
  background: #eee8dc;
}

.driver-review span {
  color: var(--color-muted);
  font: 400 0.6rem/1 var(--font-erode);
}

.daily-log-sheet footer {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.6rem 1rem;
  border-top: 1px solid var(--color-line);
  color: var(--color-muted);
  font: 400 0.58rem/1.3 var(--font-erode);
}

.daily-log-sheet footer span {
  color: var(--color-map-green);
  font-family: var(--font-satoshi);
}

@media print {
  @page {
    size: letter portrait;
    margin: 0.35in;
  }

  body {
    background: white;
  }

  body > #root > main > *:not(.results-workspace),
  .route-map-shell,
  .trip-summary,
  .itinerary,
  .directions,
  .print-toolbar {
    display: none !important;
  }

  .daily-logs {
    display: block;
    padding: 0;
    background: white;
  }

  .daily-log-sheet {
    width: 100%;
    min-height: 10in;
    break-after: page;
    break-inside: avoid;
    page-break-after: always;
    page-break-inside: avoid;
    box-shadow: none;
    print-color-adjust: exact;
  }

  .daily-log-sheet:last-child {
    break-after: auto;
    page-break-after: auto;
  }
}
```

- [ ] **Step 7: Run log checks, React Doctor, and commit**

Run:

```bash
cd frontend
npm test -- --run src/components/logs/DailyLogSheet.test.tsx
npm run lint
npm run build
```

Expected: two passing log tests, no lint errors, and a successful build.

Invoke `react-doctor`, resolve actionable findings, then run:

```bash
git add frontend/src
git commit -m "feat: add original printable daily logs"
```

---

### Task 16: Integrate loading, success, warning, and error states

**Files:**
- Create: `frontend/src/components/ui/alert.tsx`
- Create: `frontend/src/components/planner/PlanningProgress.tsx`
- Create: `frontend/src/components/planner/PlanningProgress.test.tsx`
- Create: `frontend/src/components/states/EmptyState.tsx`
- Create: `frontend/src/components/states/ErrorAlert.tsx`
- Create: `frontend/src/App.integration.test.tsx`
- Modify: `frontend/src/components/planner/TripForm.tsx`
- Modify: `frontend/src/components/planner/TripForm.test.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles/globals.css`

**Interfaces:**
- Consumes: `TripForm`, `planTrip()`, `ApiClientError`, `ResultsWorkspace`, and the empty-state illustration.
- Produces: the complete idle → planning → success/error flow, three planning stages, retry, warnings, and edit/regenerate-in-place behavior.

- [ ] **Step 1: Write the failing application integration test**

Create `frontend/src/App.integration.test.tsx`:

```tsx
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
```

Create `frontend/src/components/planner/PlanningProgress.test.tsx`:

```tsx
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
```

In `frontend/src/components/planner/TripForm.test.tsx`, import
`ApiClientError` from `@/lib/api/client` and append:

```tsx
it("places a server validation error beside its matching field", () => {
  render(
    <TripForm
      onPlan={vi.fn()}
      isPlanning={false}
      serverError={
        new ApiClientError(
          "Select a United States location.",
          "VALIDATION_ERROR",
          "pickup_location",
          false,
          400,
        )
      }
    />,
  );

  expect(
    screen.getByText("Select a United States location."),
  ).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the integration test to verify it fails**

Run:

```bash
cd frontend
npm test -- --run \
  src/App.integration.test.tsx \
  src/components/planner/PlanningProgress.test.tsx \
  src/components/planner/TripForm.test.tsx
```

Expected: FAIL because `App` does not render the typed flow, the progress
component does not exist, and `TripForm` does not yet place server errors.

- [ ] **Step 3: Add alert and state components**

Create `frontend/src/components/ui/alert.tsx`:

```tsx
import type { ReactNode } from "react";

export function Alert({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="alert" role="alert">
      <strong>{title}</strong>
      <div>{children}</div>
    </div>
  );
}
```

Create `frontend/src/components/states/EmptyState.tsx`:

```tsx
import routePlanning from "@/assets/route-planning.svg";

export function EmptyState() {
  return (
    <div className="empty-map" aria-label="Route planning preview">
      <img src={routePlanning} alt="" />
      <p>Your route and planned rests will appear here.</p>
    </div>
  );
}
```

Create `frontend/src/components/states/ErrorAlert.tsx`:

```tsx
import { RotateCcw } from "lucide-react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { ApiClientError } from "@/lib/api/client";

export function ErrorAlert({
  error,
  onRetry,
}: {
  error: ApiClientError;
  onRetry: () => void;
}) {
  return (
    <Alert title="We could not build this route.">
      <p>{error.message}</p>
      {error.retryable && (
        <Button type="button" variant="quiet" onClick={onRetry}>
          <RotateCcw aria-hidden="true" size={15} />
          Retry
        </Button>
      )}
    </Alert>
  );
}
```

Create `frontend/src/components/planner/PlanningProgress.tsx`:

```tsx
import { AnimatePresence, motion } from "motion/react";

const stages = [
  "Locating the truck route",
  "Calculating duty limits",
  "Building daily logs",
] as const;

export function PlanningProgress({ stage }: { stage: number }) {
  return (
    <div className="planning-progress" role="status" aria-live="polite">
      <AnimatePresence mode="wait">
        <motion.div
          key={stage}
          initial={{ opacity: 0, filter: "blur(6px)", y: 4 }}
          animate={{ opacity: 1, filter: "blur(0)", y: 0 }}
          exit={{ opacity: 0, filter: "blur(6px)", y: -4 }}
          transition={{ duration: 0.2 }}
        >
          <span>{String(stage + 1).padStart(2, "0")} / 03</span>
          <strong>{stages[stage]}</strong>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
```

- [ ] **Step 4: Replace temporary App wiring with real plan state**

First update `frontend/src/components/planner/TripForm.tsx` so server validation
errors appear beside the corresponding visible input. Add this type-only
import:

```tsx
import type { ApiClientError } from "@/lib/api/client";
```

Replace the existing `Props` interface and function signature with:

```tsx
interface Props {
  onPlan: (request: TripPlanRequest) => void;
  isPlanning: boolean;
  serverError?: ApiClientError | null;
}

export function TripForm({
  onPlan,
  isPlanning,
  serverError,
}: Props) {
```

Immediately after the existing `cycleUsed` declaration, add:

```tsx
const fieldError = (name: keyof FormValues) =>
  errors[name]?.message ??
  (serverError?.field === name ? serverError.message : undefined);
const cycleError = fieldError("current_cycle_used_hours");
```

In each `LocationCombobox`, replace `error={errors[name]?.message}` with
`error={fieldError(name)}`. On the cycle input, replace the old
`aria-invalid` expression with `aria-invalid={Boolean(cycleError)}` and set
`aria-describedby` to `"current-cycle-used-error"` when `cycleError` exists.
Replace the local-only cycle error paragraph with:

```tsx
{cycleError && (
  <p
    id="current-cycle-used-error"
    role="alert"
    className="field-error"
  >
    {cycleError}
  </p>
)}
```

Replace `frontend/src/App.tsx` with:

```tsx
import { useEffect, useRef, useState } from "react";

import { TripForm } from "@/components/planner/TripForm";
import { PlanningProgress } from "@/components/planner/PlanningProgress";
import { ResultsWorkspace } from "@/components/results/ResultsWorkspace";
import { EmptyState } from "@/components/states/EmptyState";
import { ErrorAlert } from "@/components/states/ErrorAlert";
import { Alert } from "@/components/ui/alert";
import {
  ApiClientError,
  planTrip,
} from "@/lib/api/client";
import type {
  TripPlanRequest,
  TripPlanResponse,
} from "@/lib/api/types";

const VISIBLE_FORM_FIELDS = new Set([
  "current_location",
  "pickup_location",
  "dropoff_location",
  "current_cycle_used_hours",
]);

export function App() {
  const [plan, setPlan] = useState<TripPlanResponse | null>(null);
  const [error, setError] = useState<ApiClientError | null>(null);
  const [isPlanning, setIsPlanning] = useState(false);
  const [stage, setStage] = useState(0);
  const lastRequest = useRef<TripPlanRequest | null>(null);
  const activeController = useRef<AbortController | null>(null);

  useEffect(
    () => () => activeController.current?.abort(),
    [],
  );

  const runPlan = async (request: TripPlanRequest) => {
    activeController.current?.abort();
    const controller = new AbortController();
    activeController.current = controller;
    lastRequest.current = request;
    setIsPlanning(true);
    setPlan(null);
    setError(null);
    setStage(0);
    const stageTimer = window.setInterval(
      () => setStage((current) => Math.min(2, current + 1)),
      650,
    );
    try {
      const result = await planTrip(request, controller.signal);
      setPlan(result);
      window.requestAnimationFrame(() => {
        document
          .querySelector<HTMLElement>(".results-workspace")
          ?.focus({ preventScroll: true });
        document
          .querySelector(".results-workspace")
          ?.scrollIntoView?.({ behavior: "smooth", block: "start" });
      });
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError(
        caught instanceof ApiClientError
          ? caught
          : new ApiClientError(
              "An unexpected error occurred.",
              "INTERNAL_ERROR",
              null,
              true,
              500,
            ),
      );
    } finally {
      window.clearInterval(stageTimer);
      if (!controller.signal.aborted) setIsPlanning(false);
    }
  };
  const hasInlineFieldError = VISIBLE_FORM_FIELDS.has(error?.field ?? "");

  return (
    <main className="min-h-screen bg-paper text-ink">
      <header className="app-header">
        <a className="brand" href="/">
          <span />
          ROUTELOG
        </a>
        <p>FMCSA-aware trip planning</p>
      </header>
      <section className={`opening-grid${plan ? " plan-complete" : ""}`}>
        <div className="opening-copy">
          <p className="eyebrow">Plan your run</p>
          <h1>A clear road ahead.</h1>
          <p>
            Build a truck route, place required stops, and generate a daily
            duty log for every day of the trip.
          </p>
          <TripForm
            onPlan={runPlan}
            isPlanning={isPlanning}
            serverError={error}
          />
          {error && !hasInlineFieldError && (
            <ErrorAlert
              error={error}
              onRetry={() => {
                if (lastRequest.current) void runPlan(lastRequest.current);
              }}
            />
          )}
        </div>
        {!plan && (
          isPlanning ? <PlanningProgress stage={stage} /> : <EmptyState />
        )}
      </section>
      <section
        id="planning-assumptions"
        className="planning-assumptions"
        aria-labelledby="planning-assumptions-title"
      >
        <h2 id="planning-assumptions-title">Planning assumptions</h2>
        <p>
          Solo property carrier · aggregate 70 / 8 cycle only · fresh shift
          clocks · no adverse or split-sleeper exceptions · fixed
          home-terminal UTC offset
        </p>
      </section>
      {plan?.meta.warnings.map((warning) => (
        <Alert key={warning} title="Planning assumption">
          <p>{warning}</p>
        </Alert>
      ))}
      {plan && <ResultsWorkspace plan={plan} />}
      <footer className="app-footer">
        Route and timing data are estimates. Public provider quotas may
        interrupt planning. RouteLog creates advisory planning copies, not
        certified ELD records.
      </footer>
    </main>
  );
}
```

Add `tabIndex={-1}` to the root `<section className="results-workspace">` in `ResultsWorkspace.tsx`.

- [ ] **Step 5: Add integrated state styling**

Append to `frontend/src/styles/globals.css`:

```css
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-line);
}

.opening-grid.plan-complete {
  grid-template-columns: minmax(0, 42rem);
}

.app-header p {
  margin: 0;
  color: var(--color-muted);
  font: 400 0.85rem/1 var(--font-erode);
}

.brand {
  color: var(--color-ink);
  font: 700 0.85rem/1 var(--font-satoshi);
  text-decoration: none;
}

.brand span {
  display: inline-block;
  width: 0.75rem;
  height: 0.75rem;
  margin-right: 0.5rem;
  border-radius: var(--radius-route);
  background: var(--color-amber);
}

.planning-progress {
  display: grid;
  min-height: 28rem;
  place-content: center;
  background:
    radial-gradient(#7e8d80 0.7px, transparent 0.7px) 0 0 / 13px 13px,
    #cad9cc;
}

.planning-progress div {
  min-width: min(80vw, 22rem);
  padding: 1.5rem;
  border: 1px solid rgb(24 34 49 / 0.14);
  border-radius: 0.8rem;
  background: rgb(255 253 248 / 0.9);
  box-shadow: var(--shadow-roadbook);
}

.planning-progress span,
.planning-progress strong {
  display: block;
}

.planning-progress span {
  color: #a76000;
  font: 700 0.65rem/1 var(--font-satoshi);
  letter-spacing: 0.1em;
}

.planning-progress strong {
  margin-top: 0.6rem;
  font: 400 1.5rem/1.1 var(--font-erode);
}

.alert {
  margin: 1rem;
  padding: 1rem;
  border: 1px solid #cbd8cd;
  border-radius: 0.7rem;
  background: #e8eee8;
}

.alert p {
  margin: 0.4rem 0 0.8rem;
  font: 400 0.9rem/1.4 var(--font-erode);
}

.results-workspace:focus {
  outline: none;
}

.app-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-line);
  color: var(--color-muted);
  font: 400 0.72rem/1.4 var(--font-erode);
}

@media (max-width: 600px) {
  .app-header p {
    display: none;
  }

  .opening-copy {
    padding: 2rem 1rem;
  }

  .itinerary,
  .directions,
  .daily-logs {
    padding-inline: 1rem;
  }

  .remarks-header,
  .remark-entry {
    grid-template-columns: 3.8rem 1fr;
  }

  .remarks-header span:last-child,
  .remark-entry span:last-child {
    display: none;
  }
}
```

- [ ] **Step 6: Run the complete frontend suite**

Run:

```bash
cd frontend
npm test
npm run lint
npm run build
```

Expected: all frontend tests pass, lint reports no errors, and the production build succeeds.

- [ ] **Step 7: Run React Doctor and commit the integrated flow**

Invoke `react-doctor`, address every actionable error, then run:

```bash
git add frontend/src
git commit -m "feat: integrate RouteLog planning states"
```

---

### Task 17: Add deterministic browser coverage and continuous integration

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/fixtures/plan.json`
- Create: `frontend/e2e/planning-flow.spec.ts`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the full browser interface and its `/api/v1/*` requests.
- Produces: deterministic Playwright coverage without provider traffic and GitHub Actions gates for backend, frontend, and browser checks.

- [ ] **Step 1: Add a deterministic browser fixture**

Create `frontend/e2e/fixtures/plan.json`:

```json
{
  "meta": {
    "generated_at": "2026-07-25T11:00:00+00:00",
    "rule_set_version": "property-70-8-v1",
    "home_terminal_timezone": "America/Chicago",
    "fixed_utc_offset_minutes": -300,
    "assumptions": [
      "Solo property-carrying driver",
      "70 hours in 8 days"
    ],
    "warnings": []
  },
  "summary": {
    "starts_at": "2026-07-25T06:00:00-05:00",
    "ends_at": "2026-07-25T19:30:00-05:00",
    "distance_m": 1030000,
    "distance_miles": "640.00",
    "driving_minutes": 660,
    "on_duty_not_driving_minutes": 120,
    "off_duty_minutes": 30,
    "sleeper_berth_minutes": 0,
    "total_duration_minutes": 810,
    "cycle_used_start_minutes": 1440,
    "cycle_used_end_minutes": 2220,
    "cycle_restarts": 0,
    "log_days": 1,
    "fuel_stops": 0,
    "rest_stops": 0
  },
  "route": {
    "bounds": {
      "west": -95.9345,
      "south": 38.627,
      "east": -87.6298,
      "north": 41.8781
    },
    "geometry": {
      "type": "LineString",
      "coordinates": [
        [-87.6298, 41.8781],
        [-90.1994, 38.627],
        [-95.9345, 41.2565]
      ]
    },
    "legs": [
      {
        "from": {
          "id": "current",
          "label": "Chicago, IL, USA",
          "longitude": -87.6298,
          "latitude": 41.8781,
          "country_code": "US"
        },
        "to": {
          "id": "pickup",
          "label": "St. Louis, MO, USA",
          "longitude": -90.1994,
          "latitude": 38.627,
          "country_code": "US"
        },
        "distance_m": 480000,
        "duration_minutes": 240,
        "steps": [
          {
            "instruction": "Continue southwest toward St. Louis",
            "road_name": "I-55 S",
            "distance_m": 480000,
            "duration_minutes": 240
          }
        ]
      },
      {
        "from": {
          "id": "pickup",
          "label": "St. Louis, MO, USA",
          "longitude": -90.1994,
          "latitude": 38.627,
          "country_code": "US"
        },
        "to": {
          "id": "dropoff",
          "label": "Omaha, NE, USA",
          "longitude": -95.9345,
          "latitude": 41.2565,
          "country_code": "US"
        },
        "distance_m": 550000,
        "duration_minutes": 420,
        "steps": [
          {
            "instruction": "Continue northwest toward Omaha",
            "road_name": "I-29 N",
            "distance_m": 550000,
            "duration_minutes": 420
          }
        ]
      }
    ]
  },
  "events": [
    {
      "id": "drive-1",
      "kind": "driving",
      "duty_status": "driving",
      "start_at": "2026-07-25T06:00:00-05:00",
      "end_at": "2026-07-25T10:00:00-05:00",
      "duration_minutes": 240,
      "route_start_m": 0,
      "route_end_m": 480000,
      "location": {
        "id": "current",
        "label": "Chicago, IL, USA",
        "longitude": -87.6298,
        "latitude": 41.8781,
        "country_code": "US"
      },
      "remark": "Drive toward St. Louis"
    },
    {
      "id": "pickup",
      "kind": "pickup",
      "duty_status": "on_duty_not_driving",
      "start_at": "2026-07-25T10:00:00-05:00",
      "end_at": "2026-07-25T11:00:00-05:00",
      "duration_minutes": 60,
      "route_start_m": 480000,
      "route_end_m": 480000,
      "location": {
        "id": "pickup",
        "label": "St. Louis, MO, USA",
        "longitude": -90.1994,
        "latitude": 38.627,
        "country_code": "US"
      },
      "remark": "Pickup"
    },
    {
      "id": "drive-2",
      "kind": "driving",
      "duty_status": "driving",
      "start_at": "2026-07-25T11:00:00-05:00",
      "end_at": "2026-07-25T17:00:00-05:00",
      "duration_minutes": 360,
      "route_start_m": 480000,
      "route_end_m": 960000,
      "location": {
        "id": "pickup",
        "label": "St. Louis, MO, USA",
        "longitude": -90.1994,
        "latitude": 38.627,
        "country_code": "US"
      },
      "remark": "Drive toward Omaha"
    },
    {
      "id": "break",
      "kind": "break",
      "duty_status": "off_duty",
      "start_at": "2026-07-25T17:00:00-05:00",
      "end_at": "2026-07-25T17:30:00-05:00",
      "duration_minutes": 30,
      "route_start_m": 960000,
      "route_end_m": 960000,
      "location": {
        "id": "break-location",
        "label": "Council Bluffs, IA, USA",
        "longitude": -95.8608,
        "latitude": 41.2619,
        "country_code": "US"
      },
      "remark": "30-minute break"
    },
    {
      "id": "drive-3",
      "kind": "driving",
      "duty_status": "driving",
      "start_at": "2026-07-25T17:30:00-05:00",
      "end_at": "2026-07-25T18:30:00-05:00",
      "duration_minutes": 60,
      "route_start_m": 960000,
      "route_end_m": 1030000,
      "location": {
        "id": "break-location",
        "label": "Council Bluffs, IA, USA",
        "longitude": -95.8608,
        "latitude": 41.2619,
        "country_code": "US"
      },
      "remark": "Drive toward Omaha"
    },
    {
      "id": "dropoff",
      "kind": "dropoff",
      "duty_status": "on_duty_not_driving",
      "start_at": "2026-07-25T18:30:00-05:00",
      "end_at": "2026-07-25T19:30:00-05:00",
      "duration_minutes": 60,
      "route_start_m": 1030000,
      "route_end_m": 1030000,
      "location": {
        "id": "dropoff",
        "label": "Omaha, NE, USA",
        "longitude": -95.9345,
        "latitude": 41.2565,
        "country_code": "US"
      },
      "remark": "Drop-off"
    }
  ],
  "stops": [
    {
      "id": "pickup",
      "kind": "pickup",
      "duty_status": "on_duty_not_driving",
      "start_at": "2026-07-25T10:00:00-05:00",
      "end_at": "2026-07-25T11:00:00-05:00",
      "duration_minutes": 60,
      "route_start_m": 480000,
      "route_end_m": 480000,
      "location": {
        "id": "pickup",
        "label": "St. Louis, MO, USA",
        "longitude": -90.1994,
        "latitude": 38.627,
        "country_code": "US"
      },
      "remark": "Pickup"
    },
    {
      "id": "break",
      "kind": "break",
      "duty_status": "off_duty",
      "start_at": "2026-07-25T17:00:00-05:00",
      "end_at": "2026-07-25T17:30:00-05:00",
      "duration_minutes": 30,
      "route_start_m": 960000,
      "route_end_m": 960000,
      "location": {
        "id": "break-location",
        "label": "Council Bluffs, IA, USA",
        "longitude": -95.8608,
        "latitude": 41.2619,
        "country_code": "US"
      },
      "remark": "30-minute break"
    },
    {
      "id": "dropoff",
      "kind": "dropoff",
      "duty_status": "on_duty_not_driving",
      "start_at": "2026-07-25T18:30:00-05:00",
      "end_at": "2026-07-25T19:30:00-05:00",
      "duration_minutes": 60,
      "route_start_m": 1030000,
      "route_end_m": 1030000,
      "location": {
        "id": "dropoff",
        "label": "Omaha, NE, USA",
        "longitude": -95.9345,
        "latitude": 41.2565,
        "country_code": "US"
      },
      "remark": "Drop-off"
    }
  ],
  "daily_logs": [
    {
      "date": "2026-07-25",
      "trip_day": 1,
      "start_location": {
        "id": "current",
        "label": "Chicago, IL, USA",
        "longitude": -87.6298,
        "latitude": 41.8781,
        "country_code": "US"
      },
      "end_location": {
        "id": "dropoff",
        "label": "Omaha, NE, USA",
        "longitude": -95.9345,
        "latitude": 41.2565,
        "country_code": "US"
      },
      "distance_m": 1030000,
      "totals_minutes": {
        "off_duty": 660,
        "sleeper_berth": 0,
        "driving": 660,
        "on_duty_not_driving": 120
      },
      "cycle": {
        "used_at_start_minutes": 1440,
        "added_minutes": 780,
        "remaining_at_end_minutes": 1980
      },
      "segments": [
        {
          "event_id": "pre",
          "kind": "pre_trip_off_duty",
          "duty_status": "off_duty",
          "start_minute": 0,
          "end_minute": 360,
          "location": {
            "id": "current",
            "label": "Chicago, IL, USA",
            "longitude": -87.6298,
            "latitude": 41.8781,
            "country_code": "US"
          },
          "remark": "Off duty"
        },
        {
          "event_id": "drive-1",
          "kind": "driving",
          "duty_status": "driving",
          "start_minute": 360,
          "end_minute": 600,
          "location": {
            "id": "current",
            "label": "Chicago, IL, USA",
            "longitude": -87.6298,
            "latitude": 41.8781,
            "country_code": "US"
          },
          "remark": "Drive toward St. Louis"
        },
        {
          "event_id": "pickup",
          "kind": "pickup",
          "duty_status": "on_duty_not_driving",
          "start_minute": 600,
          "end_minute": 660,
          "location": {
            "id": "pickup",
            "label": "St. Louis, MO, USA",
            "longitude": -90.1994,
            "latitude": 38.627,
            "country_code": "US"
          },
          "remark": "Pickup"
        },
        {
          "event_id": "drive-2",
          "kind": "driving",
          "duty_status": "driving",
          "start_minute": 660,
          "end_minute": 1020,
          "location": {
            "id": "pickup",
            "label": "St. Louis, MO, USA",
            "longitude": -90.1994,
            "latitude": 38.627,
            "country_code": "US"
          },
          "remark": "Drive toward Omaha"
        },
        {
          "event_id": "break",
          "kind": "break",
          "duty_status": "off_duty",
          "start_minute": 1020,
          "end_minute": 1050,
          "location": {
            "id": "break-location",
            "label": "Council Bluffs, IA, USA",
            "longitude": -95.8608,
            "latitude": 41.2619,
            "country_code": "US"
          },
          "remark": "30-minute break"
        },
        {
          "event_id": "drive-3",
          "kind": "driving",
          "duty_status": "driving",
          "start_minute": 1050,
          "end_minute": 1110,
          "location": {
            "id": "break-location",
            "label": "Council Bluffs, IA, USA",
            "longitude": -95.8608,
            "latitude": 41.2619,
            "country_code": "US"
          },
          "remark": "Drive toward Omaha"
        },
        {
          "event_id": "dropoff",
          "kind": "dropoff",
          "duty_status": "on_duty_not_driving",
          "start_minute": 1110,
          "end_minute": 1170,
          "location": {
            "id": "dropoff",
            "label": "Omaha, NE, USA",
            "longitude": -95.9345,
            "latitude": 41.2565,
            "country_code": "US"
          },
          "remark": "Drop-off"
        },
        {
          "event_id": "post",
          "kind": "post_trip_off_duty",
          "duty_status": "off_duty",
          "start_minute": 1170,
          "end_minute": 1440,
          "location": {
            "id": "dropoff",
            "label": "Omaha, NE, USA",
            "longitude": -95.9345,
            "latitude": 41.2565,
            "country_code": "US"
          },
          "remark": "Off duty"
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Configure Playwright and write the user-flow test**

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
  },
});
```

Create `frontend/e2e/planning-flow.spec.ts`:

```typescript
import { expect, test } from "@playwright/test";

import plan from "./fixtures/plan.json";

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
    await page.getByRole("textbox", { name: label }).fill(query);
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
```

- [ ] **Step 3: Run the browser test**

Run:

```bash
cd frontend
npx playwright install chromium
npm run e2e
```

Expected: one passing Chromium flow with no live map, geocoder, or directions request.

- [ ] **Step 4: Add GitHub Actions**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: backend/requirements-dev.txt
      - run: pip install -r requirements-dev.txt
      - run: ruff format --check .
      - run: ruff check .
      - run: python manage.py check
      - run: pytest -v

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build

  browser:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run e2e
```

- [ ] **Step 5: Run all local gates and commit**

Run:

```bash
backend/.venv/bin/ruff format --check backend
backend/.venv/bin/ruff check backend
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/pytest backend/tests -v
cd frontend
npm run lint
npm test
npm run build
npm run e2e
```

Expected: every backend, frontend, build, and browser gate passes.

```bash
git add .github frontend/e2e frontend/playwright.config.ts
git commit -m "test: add RouteLog CI and browser coverage"
```

---

### Task 18: Document, deploy, and smoke-test the deliverable

**Files:**
- Create: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/assumptions.md`
- Create: `docs/deployment.md`
- Create: `docs/loom-script.md`
- Create: `frontend/vercel.json`

**Interfaces:**
- Consumes: a passing repository, an OpenRouteService key, authenticated GitHub access, and authenticated Vercel access.
- Produces: one GitHub repository, two linked Vercel projects, one public frontend URL, production smoke evidence, and a 3–5 minute Loom recording script.

- [ ] **Step 1: Write the project README**

Create `README.md`:

````markdown
# RouteLog

RouteLog turns a current location, pickup, drop-off, and current 70/8 cycle
usage into a truck route, planned HOS stops, turn-by-turn instructions, and an
original printable daily log for every trip day.

> RouteLog generates planning copies. It is not a certified ELD and does not
> replace a driver's or carrier's official record of duty status.

## Stack

- React 19, TypeScript, Vite, React Leaflet
- Django 5.2 LTS, Django REST Framework, HTTPX
- OpenRouteService `driving-hgv`
- OpenStreetMap tiles
- Pytest, Vitest, Playwright, GitHub Actions
- Vercel frontend and Django projects

## Prerequisites

- Python 3.12
- Node.js 22 and npm
- `jq` for deployment scripting
- An OpenRouteService API key

## Local setup

```bash
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements-dev.txt
cp backend/.env.example backend/.env
cd frontend
npm install
cp .env.example .env
cd ..
```

Set `ORS_API_KEY` and a local `DJANGO_SECRET_KEY` in `backend/.env`, then run:

```bash
set -a
source backend/.env
set +a
backend/.venv/bin/python backend/manage.py runserver 127.0.0.1:8000
```

In a second terminal:

```bash
cd frontend
npm run dev
```

Open `http://127.0.0.1:5173`.

## Important limitations

- Route and duration data are provider estimates; free quotas can temporarily
  prevent new plans.
- Public OpenStreetMap tiles are suitable only while traffic remains within
  the tile usage policy.
- Aggregate cycle usage cannot reconstruct rolling hours that return naturally.
- The plan freezes the trip-start home-terminal UTC offset and warns on a
  daylight-saving transition.
- Vercel's Python runtime is Beta.
- RouteLog is advisory planning software, not a certified ELD.

## Verification

```bash
backend/.venv/bin/ruff format --check backend
backend/.venv/bin/ruff check backend
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/pytest backend/tests -v
cd frontend
npm run lint
npm test
npm run build
npm run e2e
```

## Documentation

- `docs/architecture.md`
- `docs/assumptions.md`
- `docs/deployment.md`
- `docs/loom-script.md`
- `docs/superpowers/specs/2026-07-25-eld-trip-planner-design.md`
````

- [ ] **Step 2: Document architecture and assumptions**

Create `docs/architecture.md`:

````markdown
# Architecture

```text
React form
  -> same-origin /api/v1
  -> Django serializers
  -> OpenRouteService adapter
  -> normalized route
  -> pure integer-minute HOS scheduler
  -> midnight daily-log projector
  -> route, events, stops, logs
  -> React map, itinerary, SVG logs, print
```

The frontend never receives the OpenRouteService key. The backend is stateless
and has no database, authentication, admin, session, upload, or worker
dependency. Canonical duty events feed both map stops and daily remarks so the
two views cannot diverge.

Production uses two Vercel projects from this monorepo. The frontend proxies
`/api/*` to the Django production deployment and serves all other paths through
the Vite SPA.
````

Create `docs/assumptions.md`:

```markdown
# Planning assumptions

- Solo property-carrying driver.
- 70 hours on duty in eight days.
- 11 driving hours after 10 consecutive off-duty hours.
- No driving after the 14th consecutive on-duty hour.
- 30 consecutive non-driving minutes after eight cumulative driving hours.
- 34 consecutive off-duty hours reset modeled aggregate cycle usage.
- No adverse, split-sleeper, team-driver, short-haul, or state exceptions.
- Pickup and drop-off each take 60 on-duty minutes.
- Fuel takes 30 on-duty minutes before every additional 1,000 route miles.
- The driver starts with fresh shift and break clocks.
- Current cycle used is aggregate; rolling hours do not return at midnight.
- The browser timezone is the home-terminal timezone.
- The trip-start UTC offset remains fixed throughout the generated plan.
- RouteLog is advisory planning software, not a certified ELD.
```

- [ ] **Step 3: Write deployment and Loom instructions**

Create `docs/deployment.md`:

```markdown
# Deployment

## Backend project

1. Link `backend/` to a Vercel project.
2. Add `ORS_API_KEY`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and
   `DJANGO_ALLOWED_HOSTS=.vercel.app` for Production.
3. Deploy `backend/` first and retain the production deployment URL.
4. Confirm `/api/v1/health/` returns `{"status":"ok"}`.

Vercel detects `backend/manage.py` and deploys Django through its Python
runtime. No backend `vercel.json` is required.

## Frontend project

1. Generate `frontend/vercel.json` with the current backend production URL.
2. Link `frontend/` to a second Vercel project.
3. Deploy and treat that frontend URL as the public application.
4. Confirm `/api/v1/health/` works through the frontend origin.

Because the generated rewrite contains a concrete backend deployment URL,
regenerate it after intentionally changing the production backend target.

## Smoke test

- Health endpoint succeeds through the frontend origin.
- Three United States locations autocomplete.
- A live route returns map geometry and directions.
- Pickup, drop-off, breaks, fuel, daily rests, and restarts match the itinerary.
- Every displayed log totals 24 hours.
- Print Preview creates one complete sheet per page.
- Browser source contains no OpenRouteService key.
```

Create `docs/loom-script.md`:

```markdown
# Loom walkthrough — 3 to 5 minutes

## 0:00–0:35 · Product and inputs

Open the production URL. Explain the four required inputs and the cycle meter.

## 0:35–1:35 · Generate a multi-day route

Choose three United States locations, submit, and call out the locating,
calculating, and log-building states.

## 1:35–2:25 · Map and itinerary

Show the HGV route, pickup, drop-off, break, fuel, sleeper, or restart markers.
Open one marker, then show the matching itinerary event and route directions.

## 2:25–3:20 · Original daily logs

Show multiple RouteLog sheets, explain the four duty rows and 24-hour total,
then open Print Preview. State clearly that these are planning copies and not a
certified ELD.

## 3:20–4:30 · Code and verification

Show the OpenRouteService adapter, pure scheduler, midnight projector, React
map/log components, and representative boundary tests. Finish with CI and the
deployed architecture.
```

- [ ] **Step 4: Run the pre-deployment verification gate**

Invoke `verification-before-completion`, then run:

```bash
backend/.venv/bin/ruff format --check backend
backend/.venv/bin/ruff check backend
backend/.venv/bin/python backend/manage.py check
backend/.venv/bin/pytest backend/tests -v
cd frontend
npm run lint
npm test
npm run build
npm run e2e
```

Expected: every command exits successfully before any deployment begins.

- [ ] **Step 5: Commit documentation before account-bound actions**

```bash
git add README.md docs THIRD_PARTY_NOTICES.md
git commit -m "docs: add RouteLog setup and delivery guide"
```

- [ ] **Step 6: Link and configure the Django Vercel project**

Confirm `ORS_API_KEY` exists in the current shell without printing it:

```bash
test -n "${ORS_API_KEY:-}"
```

Authenticate and link:

```bash
npx vercel@latest login
npx vercel@latest link --cwd backend
```

Add production environment variables without echoing their values:

```bash
printf '%s' "$ORS_API_KEY" |
  npx vercel@latest env add ORS_API_KEY production --sensitive --cwd backend
backend/.venv/bin/python -c \
  'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' |
  npx vercel@latest env add DJANGO_SECRET_KEY production --sensitive --cwd backend
printf '%s' 'false' |
  npx vercel@latest env add DJANGO_DEBUG production --cwd backend
printf '%s' '.vercel.app' |
  npx vercel@latest env add DJANGO_ALLOWED_HOSTS production --cwd backend
```

If Vercel or OpenRouteService credentials are unavailable, stop here and ask the user to connect or supply the required account access.

- [ ] **Step 7: Deploy Django and generate the concrete frontend proxy**

Deploy Django and capture its URL:

```bash
backend_origin=$(npx vercel@latest deploy --prod --cwd backend)
test -n "$backend_origin"
curl -fsS "$backend_origin/api/v1/health/" |
  jq -e '.status == "ok"'
```

Generate `frontend/vercel.json` mechanically from that verified origin:

```bash
jq -n --arg origin "${backend_origin%/}" '{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": ($origin + "/api/:path*")
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}' > frontend/vercel.json
jq -e '.rewrites | length == 2' frontend/vercel.json
```

- [ ] **Step 8: Deploy the frontend and verify same-origin API routing**

Authenticate/link the frontend project and deploy:

```bash
npx vercel@latest link --cwd frontend
frontend_origin=$(npx vercel@latest deploy --prod --cwd frontend)
test -n "$frontend_origin"
curl -fsS "$frontend_origin/api/v1/health/" |
  jq -e '.status == "ok"'
curl -fsS \
  "$frontend_origin/api/v1/locations/search/?q=Chicago" |
  jq -e '.locations | length > 0'
```

Confirm the key was not bundled:

```bash
if rg -l -F "$ORS_API_KEY" frontend/dist; then
  exit 1
fi
```

Expected: frontend and proxied health/search requests succeed, and no built file contains the provider key.

- [ ] **Step 9: Perform the live product smoke test**

Open the production frontend URL and exercise:

```text
Current: Chicago, IL
Pickup: St. Louis, MO
Drop-off: Phoenix, AZ
Current cycle used: 24.00
```

Verify map geometry, directions, stop chronology, exact pickup/drop-off hours,
fuel and HOS rests, log totals, mobile layout, and one log per Print Preview
page. Record the verified URL and UTC timestamp in `docs/deployment.md`.

Expected: every item in the documented smoke checklist passes. If one fails,
capture the exact failure and return to the owning task before publishing.

- [ ] **Step 10: Commit the verified production routing**

```bash
git add frontend/vercel.json docs/deployment.md
git commit -m "chore: configure verified Vercel deployment"
```

- [ ] **Step 11: Publish the repository and record the Loom**

Push the focused branch to the intended GitHub repository, confirm GitHub
Actions passes, and record the 3–5 minute walkthrough using
`docs/loom-script.md`. Add the final GitHub, Vercel, and Loom links to the
submission message without committing account tokens or private URLs.

Expected: the evaluator receives one public frontend URL, one GitHub repository
URL, and one Loom URL.
