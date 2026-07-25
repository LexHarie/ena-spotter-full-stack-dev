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
