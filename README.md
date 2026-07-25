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

- [Architecture](docs/architecture.md)
- [Planning assumptions](docs/assumptions.md)
- [Deployment](docs/deployment.md)
- [Loom walkthrough](docs/loom-script.md)
- [Approved design specification](docs/superpowers/specs/2026-07-25-eld-trip-planner-design.md)
