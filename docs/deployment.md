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
